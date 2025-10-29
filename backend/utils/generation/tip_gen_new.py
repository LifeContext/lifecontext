"""
智能提示生成模块
分析用户行为并提供智能建议，通过语义搜索检索相关历史上下文
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import config
from utils.helpers import (
    get_logger, 
    estimate_tokens, 
    truncate_web_data_by_tokens, 
    calculate_available_context_tokens
)
from utils.db import get_web_data, get_activities, get_todos, insert_tip, get_tips
from utils.llm import get_openai_client
from utils.vectorstore import search_similar_content

logger = get_logger(__name__)

# LLM客户端缓存
_llm = None


def _get_client():
    """获取LLM客户端"""
    global _llm
    if _llm is None:
        _llm = get_openai_client()
    return _llm


async def generate_smart_tips(history_mins: int = 60) -> Dict[str, Any]:
    """
    生成智能提示（主入口）
    
    Args:
        history_mins: 历史回溯分钟数
    
    Returns:
        提示数据字典
    """
    try:
        current_time = datetime.now()
        past_time = current_time - timedelta(minutes=history_mins)
        
        # 收集上下文
        context_info = _assemble_context(past_time, current_time)
        
        if not context_info['has_data']:
            logger.warning(f"No data for tip generation in last {history_mins} minutes")
            return {"success": False, "message": "数据不足"}
        
        # 生成提示
        tips_list = await _produce_tips(context_info, history_mins)
        
        if not tips_list:
            return {"success": False, "message": "提示生成失败"}
        
        # 保存提示
        tip_ids = []
        for tip_item in tips_list:
            tid = insert_tip(
                title=tip_item['title'],
                content=tip_item['content'],
                tip_type=tip_item.get('type', 'smart')
            )
            tip_ids.append(tid)
        
        logger.info(f"Generated {len(tip_ids)} tips")
        
        return {
            "success": True,
            "tip_ids": tip_ids,
            "tips": tips_list
        }
    except Exception as e:
        logger.exception(f"Tip generation error: {e}")
        return {"success": False, "message": str(e)}


def _assemble_context(start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """组装上下文数据"""
    try:
        context = {
            "has_data": False,
            "activity_records": [],
            "web_history": [],
            "pending_tasks": [],
            "existing_tips": [],
            "relevant_history": [],  # 新增：语义搜索的相关历史
            "timeframe": {
                "from": start_dt.isoformat(),
                "to": end_dt.isoformat()
            }
        }
        
        # 获取活动
        try:
            acts = get_activities(
                start_time=start_dt,
                end_time=end_dt,
                limit=10
            )
            context["activity_records"] = acts
            if acts:
                context["has_data"] = True
        except Exception as e:
            logger.debug(f"Activity fetch error: {e}")
        
        # 获取网页数据
        try:
            web_items = get_web_data(
                start_time=start_dt,
                end_time=end_dt,
                limit=20
            )
            logger.info(f"Found {len(web_items)} web records for tips")
            context["web_history"] = web_items
            if web_items:
                context["has_data"] = True
        except Exception as e:
            logger.warning(f"Web data error: {e}")
        
        # 获取待办
        try:
            todos = get_todos(status=0, limit=10)  # 未完成
            context["pending_tasks"] = todos
            if todos:
                context["has_data"] = True
        except Exception as e:
            logger.debug(f"Todo fetch error: {e}")
        
        # 获取已有提示（最近24小时内的提示，用于避免重复）
        try:
            existing_tips = get_tips(limit=20)  # 获取最近20条提示
            # 过滤出最近24小时内的提示
            recent_tips = []
            for tip in existing_tips:
                if 'create_time' in tip:
                    tip_time = datetime.fromisoformat(tip['create_time'].replace('Z', '+00:00'))
                    if (datetime.now() - tip_time).total_seconds() <= 24 * 3600:  # 24小时内
                        recent_tips.append({
                            'title': tip.get('title', ''),
                            'content': tip.get('content', ''),
                            'type': tip.get('tip_type', 'general')
                        })
            
            context["existing_tips"] = recent_tips[:10]  # 限制为最近10条
            logger.info(f"Found {len(recent_tips)} existing tips for reference")
        except Exception as e:
            logger.debug(f"Existing tips fetch error: {e}")
        
        # 语义搜索：检索相关历史上下文
        try:
            relevant_contexts = _retrieve_relevant_history(context)
            context["relevant_history"] = relevant_contexts
            if relevant_contexts:
                logger.info(f"Retrieved {len(relevant_contexts)} relevant historical contexts")
        except Exception as e:
            logger.warning(f"Failed to retrieve relevant history: {e}")
        
        return context
    except Exception as e:
        logger.exception(f"Context assembly error: {e}")
        return {"has_data": False}


def _retrieve_relevant_history(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    通过语义搜索检索相关历史上下文
    参考 MineContext 的实现思路
    
    Args:
        context: 当前上下文信息
    
    Returns:
        相关历史上下文列表
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage disabled, skipping semantic search")
            return []
        
        # 1. 生成查询文本：从当前活动和网页浏览中提取关键信息
        query_texts = _build_query_texts(context)
        
        if not query_texts:
            logger.info("No query text generated from current context")
            return []
        
        # 2. 对每个查询执行语义搜索
        all_results = []
        for query_text in query_texts:
            try:
                # 使用向量数据库进行语义搜索
                search_results = search_similar_content(
                    query=query_text,
                    limit=5  # 每个查询返回5个相关结果
                )
                
                for result in search_results:
                    # 添加查询来源标识
                    result['query_source'] = query_text[:50] + "..." if len(query_text) > 50 else query_text
                    all_results.append(result)
                    
            except Exception as e:
                logger.warning(f"Search failed for query '{query_text[:50]}...': {e}")
                continue
        
        # 3. 去重和排序（按相似度分数）
        unique_results = _deduplicate_results(all_results)
        
        # 4. 格式化结果供 LLM 使用
        formatted_results = _format_historical_contexts(unique_results[:10])  # 最多10条
        
        return formatted_results
        
    except Exception as e:
        logger.exception(f"Error retrieving relevant history: {e}")
        return []


def _build_query_texts(context: Dict[str, Any]) -> List[str]:
    """
    从当前上下文构建查询文本
    参考 MineContext 的策略：根据用户活动提取核心主题
    
    Args:
        context: 当前上下文
    
    Returns:
        查询文本列表
    """
    query_texts = []
    
    try:
        # 策略1：从网页浏览历史提取查询（最重要的信息源）
        web_history = context.get("web_history", [])
        if web_history:
            # 聚合最近的网页标题和内容
            web_topics = []
            for item in web_history[:5]:  # 只取最近5条
                title = item.get('title', '')
                url = item.get('url', '')
                
                # 优先使用标题
                if title and len(title) > 10:
                    web_topics.append(title)
                elif url:
                    # 从 URL 提取信息
                    web_topics.append(url)
            
            if web_topics:
                # 组合成一个综合查询
                combined_query = " ".join(web_topics[:3])  # 最多组合3个
                if combined_query:
                    query_texts.append(combined_query)
        
        # 策略2：从活动记录提取（作为补充）
        activities = context.get("activity_records", [])
        if activities:
            activity_texts = []
            for act in activities[:3]:
                app_name = act.get('app_name', '')
                window_title = act.get('window_title', '')
                
                if window_title and len(window_title) > 5:
                    activity_texts.append(window_title)
                elif app_name:
                    activity_texts.append(app_name)
            
            if activity_texts:
                # 如果活动内容与网页内容不重复，添加为单独查询
                activity_query = " ".join(activity_texts[:2])
                if activity_query and activity_query not in str(query_texts):
                    query_texts.append(activity_query)
        
        # 策略3：从待办任务提取（可能的任务关联）
        todos = context.get("pending_tasks", [])
        if todos and len(query_texts) < 2:  # 如果前面查询不足，补充待办相关
            todo_texts = []
            for todo in todos[:2]:
                content = todo.get('content', '')
                if content and len(content) > 10:
                    todo_texts.append(content)
            
            if todo_texts:
                todo_query = " ".join(todo_texts)
                if todo_query:
                    query_texts.append(todo_query)
        
        logger.info(f"Built {len(query_texts)} query texts for semantic search")
        return query_texts
        
    except Exception as e:
        logger.exception(f"Error building query texts: {e}")
        return []


def _deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    去重搜索结果（基于内容相似性和 metadata）
    
    Args:
        results: 搜索结果列表
    
    Returns:
        去重后的结果
    """
    seen_ids = set()
    unique_results = []
    
    for result in results:
        metadata = result.get('metadata', {})
        web_data_id = metadata.get('web_data_id')
        
        # 使用 web_data_id 去重
        if web_data_id and web_data_id not in seen_ids:
            seen_ids.add(web_data_id)
            unique_results.append(result)
        elif not web_data_id:
            # 没有 ID 的也保留
            unique_results.append(result)
    
    # 按距离（相似度）排序
    unique_results.sort(key=lambda x: x.get('distance', 1.0))
    
    return unique_results


def _format_historical_contexts(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    格式化历史上下文供 LLM 使用
    
    Args:
        results: 搜索结果
    
    Returns:
        格式化的上下文列表
    """
    formatted = []
    
    for idx, result in enumerate(results):
        metadata = result.get('metadata', {})
        content = result.get('content', '')
        similarity_score = 1.0 - result.get('distance', 1.0)  # 转换为相似度分数
        
        # 提取关键信息
        formatted_context = {
            'index': idx + 1,
            'title': metadata.get('title', '未知标题'),
            'url': metadata.get('url', ''),
            'source': metadata.get('source', 'web_crawler'),
            'content_preview': content[:300] + "..." if len(content) > 300 else content,
            'similarity_score': round(similarity_score, 3),
            'tags': metadata.get('tags', '[]')
        }
        
        formatted.append(formatted_context)
    
    return formatted


async def _produce_tips(context: Dict, history_mins: int) -> List[Dict[str, Any]]:
    """生成提示列表（增强版：包含语义搜索的相关历史）"""
    client = _get_client()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        logger.warning("LLM not available")
        return []
    
    try:
        # 动态计算可用于上下文数据的 token 数
        # 先估算其他数据的 token 数
        activities = context.get("activity_records", [])[:5]
        todos = context.get("pending_tasks", [])[:5]
        existing_tips = context.get("existing_tips", [])[:5]
        relevant_history = context.get("relevant_history", [])[:8]
        
        # 估算这些数据的 token
        other_data_json = json.dumps({
            "activities": activities,
            "todos": todos,
            "existing_tips": existing_tips,
            "relevant_history": relevant_history
        }, ensure_ascii=False)
        other_data_tokens = estimate_tokens(other_data_json)
        
        # 计算可用于 web_data 的 token 数
        available_tokens = calculate_available_context_tokens('tip', other_data_tokens)
        
        # 使用动态截取函数处理 web_data
        web_data_trimmed = truncate_web_data_by_tokens(
            context.get("web_history", []),
            max_tokens=available_tokens
        )
        
        context_data = {
            "activities": activities,
            "web_data": web_data_trimmed,
            "todos": todos,
            "existing_tips": existing_tips,
            "relevant_history": relevant_history
        }
        
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
        
        system_prompt = """你是一位专业的**网页洞察分析师 (Web Insight Analyst)**，具备**历史上下文感知能力**。

你的核心职责是：深度分析用户的**当前网页浏览活动**和**相关历史上下文**，主动发现并提供用户在当前任务中可能需要但尚未知晓的补充信息、知识或资源。你的目标是通过提供**信息增益 (Information Gain)** 来扩展用户的知识边界。

#### **增强分析策略 (Enhanced Analysis Strategy)**

1.  **聚合主题 (Synthesize Theme)**: 分析当前时间段内的浏览记录，**聚合出一个或两个核心的活动主题**。
2.  **历史关联 (Historical Correlation)**: **重点利用 `relevant_history` 字段**，这是通过语义搜索检索到的用户历史相关上下文。分析当前活动与历史记录的关联性，发现用户的长期兴趣、重复遇到的问题、或之前未解决的疑问。
3.  **评估深度 (Assess Depth)**: 结合当前浏览和历史记录，判断用户对当前主题的了解深度和学习进度。
4.  **预测下一步 (Predict Next Step)**: 基于当前主题、历史轨迹和用户深度，预测他们最有可能需要的下一步知识或遇到的问题。

#### **相关历史上下文的使用 (How to Use Relevant History)**

- `relevant_history` 包含通过**语义搜索**检索到的与当前活动相关的历史网页记录
- 每条历史记录包含：标题、URL、内容预览、相似度分数
- **关键用途**：
  1. 识别用户的**持续关注点**（多次出现的主题）
  2. 发现用户的**知识盲点**（反复查询但未深入的领域）
  3. 联系用户的**学习路径**（从历史到现在的知识演进）
  4. 提供**个性化建议**（基于用户特定的历史兴趣）

#### **内容维度 (Content Dimensions)**

你生成的内容 `type` 必须属于以下类别之一：

* **`DEEP_DIVE`**: 对用户正在关注的核心概念，提供更深层次的解读。
* **`RESOURCE_RECOMMENDATION`**: 推荐相关的工具、开源库、优质文章或数据集。
* **`RISK_ANALYSIS`**: 预见用户当前方案可能遇到的技术陷阱、局限性或风险。
* **`KNOWLEDGE_EXPANSION`**: 将当前主题与相关联的新领域或更高阶的知识联系起来。
* **`ALTERNATIVE_PERSPECTIVE`**: 提供与用户当前思路不同的备选方案或反向观点。
* **`HISTORICAL_CONNECTION`**: **新增**：基于历史上下文，指出用户之前关注但未深入的相关话题，或之前遇到的问题的新解决方案。

#### **质量与输出要求 (Strictly Enforced)**

* **高信息增益**: 必须提供用户大概率不知道的新信息。禁止常识。
* **强相关性**: 所有内容必须与聚合出的核心主题紧密相关。
* **历史感知**: 优先利用 `relevant_history` 生成个性化、有延续性的建议。
* **具体可用**: 提供的信息应具体、清晰，包含链接、名称或关键术语。
* **避免重复**: 绝不重复用户已浏览页面或历史记录的核心内容。
* **质量优先**: 若无高价值内容，必须返回空数组 `[]`。
* **输出格式**: 严格的 JSON 数组。
    ```json
    [
      {
        "title": "对补充内容的高度概括",
        "content": "详细、具体的补充信息、知识或资源说明。必须使用 markdown 格式，段落分明，必须正确转义 JSON 字符串中的特殊字符（换行用 \\n，引号用 \\\"）。",
        "type": "从`内容维度`中选择一个最合适的类型"
      }
    ]
    ```

**JSON 格式要求（严格遵守）：**
1. 必须返回有效的 JSON 数组
2. content 字段中的换行符必须使用 `\\n` 转义
3. content 字段中的引号必须使用 `\\\"` 转义
4. 不要在 JSON 外添加任何解释性文字
5. 如果使用代码块包裹，使用 ```json ... ``` 格式"""
        
        user_prompt = f"""作为网页洞察分析师，请分析用户最近{history_mins}分钟的活动数据，**特别注意利用语义搜索检索到的相关历史上下文**。

**分析指令：**

1. **聚合主题优先**: 分析当前网页和活动，找出用户当前的核心研究主题。
2. **深度利用历史上下文**: **重点关注 `relevant_history` 字段**，这些是通过语义搜索找到的与当前主题相关的历史记录。分析用户的长期兴趣、学习路径和知识演进。
3. **识别信息缺口与机会**: 
   - 基于当前主题和历史轨迹，发现用户的知识盲点
   - 识别用户之前关注但未深入的话题
   - 发现用户重复遇到但未解决的问题
4. **生成个性化建议**: 结合当前活动和历史上下文，提供有延续性、个性化的高价值建议。
5. **避免重复**: 绝不重复当前浏览内容或历史记录的核心内容。
6. **质量优先**: 如果没有真正高价值、高信息增益的内容，严格返回空数组 []。

**数据上下文：**
{context_json}

**特别说明：**
- `web_data`: 当前时间段的网页浏览记录
- `activities`: 当前时间段的应用活动
- `todos`: 待办任务
- `existing_tips`: 已有提示（避免重复）
- `relevant_history`: **核心数据** - 通过语义搜索检索到的相关历史上下文（包含标题、URL、内容预览、相似度分数）

请按照指定的JSON格式输出分析结果："""
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.info("LLM tip generation completed")
        
        # 解析结果
        tips = _parse_tips_json(result_text)
        return tips
    except Exception as e:
        logger.exception(f"Tip production error: {e}")
        return []


def _parse_tips_json(text: str) -> List[Dict[str, Any]]:
    """解析提示JSON（增强容错）"""
    try:
        # 记录原始返回（用于调试）
        logger.debug(f"Raw LLM response (first 500 chars): {text[:500]}")
        
        # 提取JSON
        json_text = text
        if "```json" in text:
            json_text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            json_text = text.split("```")[1].split("```")[0]
        
        # 清理文本
        json_text = json_text.strip()
        
        # 尝试解析
        try:
            tips = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}")
            # 尝试修复常见问题
            json_text = _fix_json_string(json_text)
            tips = json.loads(json_text)
        
        # 验证结果
        if isinstance(tips, list):
            return tips
        elif isinstance(tips, dict) and 'tips' in tips:
            return tips['tips']
        else:
            logger.warning(f"Unexpected JSON structure: {type(tips)}")
            return []
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.error(f"Failed JSON text (first 1000 chars): {text[:1000]}")
        
        # 保存失败的响应到文件用于调试
        try:
            import os
            debug_file = os.path.join(config.DATA_DIR, "failed_tip_response.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write("=== Failed LLM Response ===\n")
                f.write(f"Error: {e}\n")
                f.write("=== Full Response ===\n")
                f.write(text)
            logger.info(f"Failed response saved to: {debug_file}")
        except Exception as save_error:
            logger.warning(f"Could not save failed response: {save_error}")
        
        return []
    except Exception as e:
        logger.exception(f"Unexpected error parsing tips: {e}")
        return []


def _fix_json_string(text: str) -> str:
    """
    尝试修复常见的JSON格式问题
    
    Args:
        text: 原始JSON文本
    
    Returns:
        修复后的JSON文本
    """
    try:
        import re
        
        # 移除可能的 BOM 标记
        text = text.replace('\ufeff', '')
        
        # 替换全角引号为半角引号
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # 移除控制字符（保留换行符和制表符）
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # 尝试找到数组的开始和结束
        if '[' in text and ']' in text:
            start = text.find('[')
            end = text.rfind(']') + 1
            text = text[start:end]
        
        # 修复策略：逐个对象处理
        fixed_objects = []
        
        # 分割成独立的对象（简单的基于 { } 的分割）
        objects = _extract_json_objects(text)
        
        for obj_text in objects:
            try:
                # 尝试修复单个对象
                fixed_obj = _fix_single_object(obj_text)
                fixed_objects.append(fixed_obj)
            except Exception as e:
                logger.warning(f"Failed to fix object: {e}")
                continue
        
        if fixed_objects:
            result = '[' + ','.join(fixed_objects) + ']'
            logger.info(f"Applied JSON fixes, recovered {len(fixed_objects)} objects")
            return result
        else:
            logger.warning("No objects could be recovered")
            return text
        
    except Exception as e:
        logger.warning(f"Error fixing JSON: {e}")
        return text


def _extract_json_objects(text: str) -> List[str]:
    """
    从 JSON 数组文本中提取独立的对象
    
    Args:
        text: JSON 数组文本
    
    Returns:
        对象文本列表
    """
    import re
    
    objects = []
    depth = 0
    current_obj = []
    in_string = False
    escape_next = False
    
    for i, char in enumerate(text):
        if escape_next:
            current_obj.append(char)
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            current_obj.append(char)
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            current_obj.append(char)
            continue
        
        if not in_string:
            if char == '{':
                if depth == 0:
                    current_obj = [char]
                else:
                    current_obj.append(char)
                depth += 1
            elif char == '}':
                depth -= 1
                current_obj.append(char)
                if depth == 0 and current_obj:
                    objects.append(''.join(current_obj))
                    current_obj = []
            elif depth > 0:
                current_obj.append(char)
        else:
            current_obj.append(char)
    
    return objects


def _fix_single_object(obj_text: str) -> str:
    """
    修复单个 JSON 对象
    
    Args:
        obj_text: 对象文本
    
    Returns:
        修复后的对象文本
    """
    import re
    import json
    
    # 尝试直接解析
    try:
        json.loads(obj_text)
        return obj_text  # 已经是有效的 JSON
    except:
        pass
    
    # 提取字段
    title_match = re.search(r'"title"\s*:\s*"([^"]*)"', obj_text)
    type_match = re.search(r'"type"\s*:\s*"([^"]*)"', obj_text)
    
    # 提取 content（可能包含换行和引号）
    content_match = re.search(r'"content"\s*:\s*"(.*?)"\s*,?\s*"type"', obj_text, re.DOTALL)
    if not content_match:
        # 尝试匹配到对象结尾
        content_match = re.search(r'"content"\s*:\s*"(.*?)"\s*}', obj_text, re.DOTALL)
    
    if title_match and content_match:
        title = title_match.group(1)
        content = content_match.group(1)
        type_val = type_match.group(1) if type_match else "RESOURCE_RECOMMENDATION"
        
        # 清理和转义 content
        # 将 \" 替换为实际引号，然后统一转义
        content = content.replace('\\"', '"')  # 先去掉 LLM 的转义
        content = content.replace('\\n', '\n')  # 将 \n 转为实际换行
        
        # 使用 json.dumps 自动处理所有转义
        content_escaped = json.dumps(content)[1:-1]  # 移除首尾引号
        
        # 重构对象
        fixed = f'{{"title": "{title}", "content": "{content_escaped}", "type": "{type_val}"}}'
        
        # 验证
        try:
            json.loads(fixed)
            return fixed
        except:
            logger.warning(f"Fixed object still invalid: {fixed[:100]}...")
            return obj_text
    
    return obj_text

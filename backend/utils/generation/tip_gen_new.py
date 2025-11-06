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
    calculate_available_context_tokens,
    parse_llm_json_response
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
        logger.info("🚀" * 30)
        logger.info(f"开始生成智能提示 - 回溯 {history_mins} 分钟")
        
        current_time = datetime.now()
        past_time = current_time - timedelta(minutes=history_mins)
        
        # 收集上下文
        logger.info("第一步：收集上下文数据...")
        context_info = _assemble_context(past_time, current_time)
        
        if not context_info['has_data']:
            logger.warning(f"❌ 数据不足：最近 {history_mins} 分钟内没有足够的数据生成提示")
            return {"success": False, "message": "数据不足"}
        
        logger.info("✅ 上下文数据收集完成")
        
        # 生成提示
        logger.info("第二步：调用 LLM 生成提示...")
        tips_list = await _produce_tips(context_info, history_mins)
        
        if not tips_list:
            logger.error("❌ 提示生成失败：LLM 未返回有效的提示")
            return {"success": False, "message": "提示生成失败"}
        
        logger.info(f"✅ LLM 生成了 {len(tips_list)} 个提示")
        
        # 保存提示
        logger.info("第三步：保存提示到数据库...")
        tip_ids = []
        for idx, tip_item in enumerate(tips_list):
            try:
                tid = insert_tip(
                    title=tip_item['title'],
                    content=tip_item['content'],
                    tip_type=tip_item.get('type', 'smart')
                )
                tip_ids.append(tid)
                logger.info(f"  ✅ Tip {idx + 1} 保存成功，ID: {tid}")
            except Exception as e:
                logger.error(f"  ❌ Tip {idx + 1} 保存失败: {e}")
        
        logger.info(f"✅ 成功保存 {len(tip_ids)} 个提示")
        logger.info("🎉" * 30)
        
        return {
            "success": True,
            "tip_ids": tip_ids,
            "tips": tips_list
        }
    except Exception as e:
        logger.error("💥" * 30)
        logger.error("❌ 智能提示生成过程中发生严重错误")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误信息: {e}")
        logger.exception("完整堆栈追踪:")
        logger.error("💥" * 30)
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
        
        # 使用动态截取函数处理 web_data，使用 metadata 替代 content
        web_data_trimmed = truncate_web_data_by_tokens(
            context.get("web_history", []),
            max_tokens=available_tokens,
            use_metadata=True
        )
        
        context_data = {
            "activities": activities,
            "web_data": web_data_trimmed,
            "todos": todos,
            "existing_tips": existing_tips,
            "relevant_history": relevant_history
        }
        
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
        
        # 打印上下文数据统计
        logger.info("=" * 60)
        logger.info("开始生成 Tips")
        logger.info(f"上下文数据统计:")
        logger.info(f"  - activities: {len(activities)} 条")
        logger.info(f"  - web_data: {len(web_data_trimmed)} 条")
        logger.info(f"  - todos: {len(todos)} 条")
        logger.info(f"  - existing_tips: {len(existing_tips)} 条")
        logger.info(f"  - relevant_history: {len(relevant_history)} 条")
        logger.info(f"上下文 JSON 长度: {len(context_json)} 字符")
        logger.info(f"估算输入 tokens: ~{estimate_tokens(context_json)}")
        logger.info("=" * 60)
        
        system_prompt = """你是一个智能提示生成助手，任务是生成1-3个有价值的Tips（建议）。

## 核心任务
分析用户的网页浏览记录、活动记录和待办事项，识别用户的兴趣主题和知识缺口，生成有价值的建议。

## 输入数据说明
你会收到JSON对象，包含：
- `activities`: 用户活动记录
- `web_data`: 网页分析报告（包含metadata_analysis、detailed_summary等字段）
- `todos`: 待办事项
- `existing_tips`: 已生成的提示（避免重复）
- `relevant_history`: 相关的历史上下文

## Tips类型
每个tip的`type`必须是以下之一：
- `DEEP_DIVE`: 深入解析核心概念
- `RESOURCE_RECOMMENDATION`: 推荐工具、文章、教程等资源
- `RISK_ANALYSIS`: 指出潜在风险或陷阱
- `KNOWLEDGE_EXPANSION`: 关联新知识领域
- `ALTERNATIVE_PERSPECTIVE`: 提供替代方案或不同视角

## 内容要求
- `title`: 简短精炼的标题（10-30字）
- `content`: 使用Markdown格式的详细内容，包含标题、列表、代码块等
- 内容应深入、有价值，避免泛泛而谈
- 避免与existing_tips重复
- ⚠️ 数学公式使用普通文本或代码块，不要使用LaTeX语法（如\\[、\\frac等）

## ⚠️ 输出格式（极其重要）
直接返回JSON对象，包含一个tips数组。

✅ 正确格式：
{
  "tips": [
    {
      "title": "React Hooks性能优化关键技巧",
      "content": "## 核心优化策略\n\n### 1. 使用useMemo和useCallback\n\n这两个Hook可以避免不必要的重新计算和重新渲染...\n\n```javascript\nconst memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);\n```",
      "type": "DEEP_DIVE"
    }
  ]
}

❌ 错误格式（千万不要这样）：
- 不要用```json包裹JSON
- 不要添加任何解释文字
- 不要返回Markdown分析文章
- 不要返回技术报告

如果没有合适的提示，返回空tips数组: {"tips": []}

记住：返回JSON对象，包含tips数组！"""
        
        user_prompt = f"""请分析以下用户行为数据，生成1-3个有价值的Tips。

**上下文数据:**

{context_json}

⚠️ 重要提醒：直接返回JSON对象，格式为 {{"tips": [{{"title": "...", "content": "...", "type": "..."}}]}}，不要添加任何其他文字或代码块标记。"""
        
        logger.info("正在调用 LLM API...")
        logger.info(f"模型: {config.LLM_MODEL}, 温度: 0.3, max_tokens: 8196")
        
        # 构建请求参数
        request_params = {
            "model": config.LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,  # 降低温度以获得更稳定的JSON输出
            "max_tokens": 8196
        }
        
        # 尝试启用JSON mode（如果模型支持）
        try:
            # OpenAI的gpt-4-turbo-preview和gpt-3.5-turbo-1106及以后版本支持JSON mode
            if config.LLM_MODEL and ('gpt-4' in config.LLM_MODEL or 'gpt-3.5' in config.LLM_MODEL):
                request_params["response_format"] = {"type": "json_object"}
                logger.info("✅ 已启用JSON mode")
        except Exception as e:
            logger.debug(f"JSON mode不可用: {e}")
        
        response = client.chat.completions.create(**request_params)
        
        result_text = response.choices[0].message.content.strip()
        
        # 详细打印 LLM 返回信息
        logger.info("=" * 60)
        logger.info("LLM 返回完成")
        logger.info(f"返回长度: {len(result_text)} 字符")
        logger.info(f"开始字符: {result_text[:100] if len(result_text) > 100 else result_text}")
        logger.info(f"结束字符: {result_text[-100:] if len(result_text) > 100 else result_text}")
        logger.info(f"是否以 {{ 开头: {result_text.startswith('{')}")
        logger.info(f"是否以 }} 结尾: {result_text.endswith('}')}")
        logger.info(f"是否包含代码块: {'```' in result_text}")
        logger.info("=" * 60)
        
        # 使用通用 JSON 解析工具
        logger.info("开始解析 JSON...")
        result = parse_llm_json_response(
            result_text,
            expected_type='object',  # 现在期望返回对象
            save_on_error=True,
            error_file_prefix='failed_tip_response'
        )
        
        # 提取tips数组
        if result is not None:
            tips = result.get('tips', [])
            logger.info("=" * 60)
            logger.info(f"✅ JSON 解析成功！生成了 {len(tips)} 个 tips")
            for idx, tip in enumerate(tips):
                logger.info(f"  Tip {idx + 1}:")
                logger.info(f"    - title: {tip.get('title', 'N/A')[:50]}...")
                logger.info(f"    - type: {tip.get('type', 'N/A')}")
                logger.info(f"    - content 长度: {len(tip.get('content', ''))} 字符")
            logger.info("=" * 60)
            return tips
        else:
            logger.error("=" * 60)
            logger.error("❌ JSON 解析失败，返回 None")
            logger.error("请检查以上日志中的 LLM 返回内容")
            logger.error("=" * 60)
            return []
    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ Tip 生成过程中发生错误")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误信息: {e}")
        logger.exception("完整堆栈追踪:")
        logger.error("=" * 60)
        return []

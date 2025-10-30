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
        
        system_prompt = """你是一位顶级的网络洞察策略师 (Principal Web Insight Strategist)。你的专长是从一系列零散的用户行为数据中，精准地聚合出核心意图，并预测用户在知识探索路径上的下一个关键"信息缺口"。

## 任务目标 (Task Goal)

你的核心目标是分析一个时间窗口内、一系列由上一节点预处理过的网页分析报告，识别出用户在当前探索主题下的核心"信息缺口"，并生成少量（1-3个）极具价值的"Tips"。每一个Tip都必须是用户大概率不知道的、经过深度拓展的、能直接启发下一步思考或行动的增量信息。

## 输入数据说明 (Input Data Description)

你将收到一个名为`context_data`的单一JSON对象，它包含以下四个关键字段：

1. **`activities`**: 一个JSON数组，记录了用户一段时间内的活动记录。
2. **`web_data`**: 一个JSON数组，包含对每个网页的独立分析报告，这是最主要的信息来源。
3. **`todos`**: 一个JSON数组，包含用户当前未完成的待办事项列表。
4. **`existing_tips`**: 一个JSON数组，包含已经为用户生成过的、仍然有效的Tips列表。你的核心任务之一就是避免生成与此列表内容重复的新Tips。

其中**`web_data`**是一个JSON数组。数组中的每一个对象，都是对用户单个浏览网页的预分析报告，其结构如下：

```json
{
  "metadata_analysis": {
    "category": "内容分类",
    "keywords": ["关键词1", "关键词2"],
    "topics": ["主题1"]
  },
  "detailed_summary": "该网页的详细摘要",
  "potential_insights": [ { "insight_title": "一个初步的、未经拓展的洞察点" } ],
  "actionable_tasks": [ { "task_title": "一个初步的、未经拓展的待办项" } ]
}
```

你的任务是基于这个**分析报告的集合**进行更高层次的综合分析，而不是重新分析网页原始内容。

## 执行步骤 (Execution Steps)

你必须严格遵循以下五个步骤来完成任务：

1. **第一步：主题聚合与意图识别。** 快速浏览所有输入报告的`metadata_analysis.keywords`, `metadata_analysis.topics`和`detailed_summary`字段，精准地识别并总结出用户在此时间段内的**核心探索主题**（例如："研究React Hooks的性能优化与最佳实践"）。

2. **第二步：洞察聚类与信息缺口定位。** 收集所有报告中的`potential_insights`。将内容相似或指向同一知识点的洞察进行分组、合并。然后，基于你识别出的核心主题，判断这些聚类后的洞察点中，哪些构成了用户知识体系中最关键的**"信息缺口"**。

3. **第三步：核心Tips筛选。** 从你定位出的"信息缺口"中，**精选出1到3个**对用户当前探索路径最有价值、最能推动其前进的核心点，作为你将要详细拓展的最终Tips。

4. **第四步：深度内容拓展。** 针对每一个选定的Tip，参考下方的`## 内容维度`，为其选择一个最合适的`type`。然后，撰写其`content`部分。

**核心要求：** `content`必须是**详细、深入、结构清晰**的。你必须使用**GitHub Flavored Markdown**来格式化内容，使其像一篇高质量的README文档。有效利用以下元素：
    - **标题:** 使用 `##` 或 `###` 来创建内容的内部结构。
    - **列表:** 使用 `-` 或 `1.` 来罗列要点、资源或步骤。
    - **代码块:** 使用 \`\`\` 来展示代码示例或配置。
    - **重点突出:** 使用 `**文字**` (加粗) 或 `*文字*` (斜体) 来强调关键概念。
    - **链接:** 使用 `[链接文本](URL)` 来引用外部资源。

5. **第五步：质量审查与格式化输出。** 对生成的所有Tips进行严格的自我审查，剔除任何与用户已浏览内容重复、宽泛或价值不高的部分。**如果经过审查后，没有任何一个Tip能达到高质量标准，你必须返回一个空数组`[]`**。最后，将所有通过审查的Tips按照`## 输出要求`中定义的JSON格式进行封装。

## 内容维度 (Content Dimensions)

你生成的每个Tip的`type`必须属于以下类别之一：

- **`DEEP_DIVE`**: 对用户正在关注的核心概念，提供更深层次的解读（例如：解释其背后的工作原理或设计模式）。
- **`RESOURCE_RECOMMENDATION`**: 推荐相关的工具、高质量文章、开源库或权威教程。
- **`RISK_ANALYSIS`**: 预见用户当前方案可能遇到的技术陷阱、局限性或风险。
- **`KNOWLEDGE_EXPANSION`**: 将当前主题与相关联的新领域或更高阶的知识联系起来（例如：学习完A，下一步可以探索B）。
- **`ALTERNATIVE_PERSPECTIVE`**: 提供与用户当前思路不同的备选方案或反向观点，并对比优缺点。

## 输出要求 (Output Requirements)

你必须返回一个**纯 JSON 数组**，不要使用 markdown 代码块包裹，不要添加任何解释性文字。

### JSON 结构示例:

```json
[
  {
    "title": "对这个Tip核心价值的高度概括，应简洁且引人注目",
    "content": "这是Tip的详细主体内容。必须使用GitHub Flavored Markdown编写，结构清晰、内容详实，就像一篇高质量的README文档。\n\n## 二级标题\n- 列表项\n\n```python\ncode here\n```",
    "type": "从`## 内容维度`中选择一个最合适的类型"
  }
]
```

### 关键要求:

1. **输出格式**: 直接输出 JSON 数组，以 `[` 开始，以 `]` 结束
2. **不要包裹**: 不要用 \`\`\`json 或 \`\`\` 包裹 JSON
3. **不要注释**: JSON 外不要有任何解释文字
4. **content 字段**: 是一个 JSON 字符串，包含 markdown 格式的内容
   - markdown 中的换行用 `\n` 表示（例如：`"第一行\n第二行"`）
   - markdown 中的引号用 `\"` 转义（例如：`"他说\"你好\""`）
   - markdown 中的反引号（用于代码块）无需转义（例如：`"\`\`\`python\ncode\n\`\`\`"`）
5. **空结果**: 如果没有高质量内容，返回 `[]`
6. **数量控制**: 返回 1-3 个高质量的 tips，不要贪多"""
        
        user_prompt = f"""作为网络洞察策略师，请严格按照你的角色、目标和要求，分析以下由上一节点生成的网页浏览分析报告集合。

**数据上下文 (预分析报告集合):**

{context_json}

请输出你的洞察分析结果。"""
        
        logger.info("正在调用 LLM API...")
        logger.info(f"模型: {config.LLM_MODEL}, 温度: 0.8, max_tokens: 3000")
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=3000  # 增大到 3000，确保返回完整的 JSON
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 详细打印 LLM 返回信息
        logger.info("=" * 60)
        logger.info("LLM 返回完成")
        logger.info(f"返回长度: {len(result_text)} 字符")
        logger.info(f"开始字符: {result_text[:100] if len(result_text) > 100 else result_text}")
        logger.info(f"结束字符: {result_text[-100:] if len(result_text) > 100 else result_text}")
        logger.info(f"是否以 [ 开头: {result_text.startswith('[')}")
        logger.info(f"是否以 ] 结尾: {result_text.endswith(']')}")
        logger.info(f"是否包含代码块: {'```' in result_text}")
        logger.info("=" * 60)
        
        # 使用通用 JSON 解析工具
        logger.info("开始解析 JSON...")
        tips = parse_llm_json_response(
            result_text,
            expected_type='array',
            save_on_error=True,
            error_file_prefix='failed_tip_response'
        )
        
        # 打印解析结果
        if tips is not None:
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

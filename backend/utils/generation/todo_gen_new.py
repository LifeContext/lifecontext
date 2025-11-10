"""
待办事项智能生成模块
分析用户数据并提取可执行的待办任务
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from string import Template
import config
from utils.helpers import (
    get_logger,
    estimate_tokens,
    truncate_web_data_by_tokens,
    calculate_available_context_tokens
)
from utils.json_utils import parse_llm_json_response
from utils.db import (
    get_todos,
    get_web_data,
    get_activities,
    insert_todo
)
from utils.llm import get_openai_client
from utils.prompt_config import get_prompt_set
from utils.vectorstore import search_similar_content

logger = get_logger(__name__)

# 全局客户端
_llm_instance = None

PROMPTS = get_prompt_set(config.PROMPT_LANGUAGE)


def _get_llm():
    """获取LLM实例"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = get_openai_client()
    return _llm_instance


async def generate_task_list(lookback_mins: int = 30) -> Dict[str, Any]:
    """
    生成待办任务列表（主入口）
    
    Args:
        lookback_mins: 向前回溯的分钟数
    
    Returns:
        包含任务列表的字典
    """
    try:
        now = datetime.now()
        past = now - timedelta(minutes=lookback_mins)
        
        # 收集数据
        context = _gather_context(past, now)
        
        if not context['has_content']:
            logger.warning(f"Insufficient data in last {lookback_mins} minutes")
            return {"success": False, "message": "数据不足，无法生成待办"}
        
        # 生成任务
        tasks = await _create_tasks_from_context(context, lookback_mins)
        
        if not tasks:
            return {"success": False, "message": "任务生成失败"}
        
        # 保存到数据库
        task_ids = []
        for task in tasks:
            tid = insert_todo(
                title=task['title'],
                description=task.get('description', ''),
                priority=task.get('priority', 1)
            )
            task_ids.append(tid)
        
        logger.info(f"Generated {len(task_ids)} tasks")
        
        return {
            "success": True,
            "todo_ids": task_ids,
            "todos": tasks
        }
    except Exception as e:
        logger.exception(f"Task generation error: {e}")
        return {"success": False, "message": str(e)}


def _gather_context(start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """收集上下文数据"""
    try:
        logger.info(f"Gathering context: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        context = {
            "has_content": False,
            "activities": [],
            "web_items": [],
            "existing_todos": [],
            "relevant_history": [],
            "time_span": {
                "begin": start_dt.isoformat(),
                "finish": end_dt.isoformat()
            }
        }
        
        # 获取活动记录
        try:
            acts = get_activities(
                start_time=start_dt,
                end_time=end_dt,
                limit=10
            )
            logger.info(f"Found {len(acts)} activities")
            context["activities"] = acts
            if acts:
                context["has_content"] = True
        except Exception as e:
            logger.warning(f"Activity fetch error: {e}")
        
        # 获取网页数据
        try:
            web_items = get_web_data(
                start_time=start_dt,
                end_time=end_dt,
                limit=20
            )
            logger.info(f"Found {len(web_items)} web records")
            context["web_items"] = web_items
            if web_items:
                context["has_content"] = True
        except Exception as e:
            logger.warning(f"Web data fetch error: {e}")
        
        # 获取已有待办事项（最近24小时内的）
        try:
            # 获取最近20条待办事项
            all_todos = get_todos(limit=20)
            
            # 过滤出最近24小时内的待办事项
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_todos = []
            
            for todo in all_todos:
                create_time_str = todo.get('create_time')
                if create_time_str:
                    try:
                        todo_time = datetime.strptime(create_time_str, '%Y-%m-%d %H:%M:%S')
                        if todo_time >= cutoff_time:
                            # 只保留关键信息，避免上下文过大
                            recent_todos.append({
                                'title': todo.get('title', ''),
                                'description': todo.get('description', ''),
                                'priority': todo.get('priority', 0),
                                'status': todo.get('status', 0),
                                'create_time': create_time_str
                            })
                    except Exception as time_err:
                        logger.debug(f"Time parse error for todo {todo.get('id')}: {time_err}")
            
            # 限制为最近10条
            context["existing_todos"] = recent_todos[:10]
            logger.info(f"Found {len(recent_todos)} recent todos, using {len(context['existing_todos'])}")
            
            if recent_todos:
                context["has_content"] = True
                
        except Exception as e:
            logger.warning(f"Todo fetch error: {e}")
 
        # 语义搜索相关历史
        try:
            relevant_contexts = _retrieve_relevant_history(context)
            context["relevant_history"] = relevant_contexts
            if relevant_contexts:
                logger.info(f"Retrieved {len(relevant_contexts)} relevant historical contexts")
                context["has_content"] = True
        except Exception as e:
            logger.warning(f"Failed to retrieve relevant history: {e}")
        
        logger.info(f"Context has_content: {context['has_content']}")
        return context
    except Exception as e:
        logger.exception(f"Context gathering error: {e}")
        return {"has_content": False}


async def _create_tasks_from_context(context: Dict, lookback_mins: int) -> List[Dict[str, Any]]:
    """从上下文数据生成任务"""
    client = _get_llm()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        logger.warning("LLM not available")
        return []
    
    try:
        # 准备上下文数据，包含已有todos
        existing_todos = context.get("existing_todos", [])
        activities = context.get("activities", [])
        relevant_history = context.get("relevant_history", [])[:8]
        
        # 估算其他数据的 token
        other_data_json = json.dumps({
            "activities": activities,
            "existing_todos": existing_todos,
            "relevant_history": relevant_history
        }, ensure_ascii=False)
        other_data_tokens = estimate_tokens(other_data_json)
        
        # 计算可用于 web_data 的 token 数
        available_tokens = calculate_available_context_tokens('todo', other_data_tokens)
        
        # 使用动态截取函数处理 web_data，使用 metadata 替代 content
        web_data_trimmed = truncate_web_data_by_tokens(
            context.get("web_items", []),
            max_tokens=available_tokens,
            use_metadata=True
        )
        
        context_data = {
            "activities": activities,
            "web_data": web_data_trimmed,
            "existing_todos": existing_todos,
            "relevant_history": relevant_history
        }
        
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
         
        system_msg = PROMPTS["todo"]["system"]

        user_template = Template(PROMPTS["todo"]["user_template"])
        user_msg = user_template.safe_substitute(context_json=context_json)
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.8,
            max_tokens=1000
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
        tasks = parse_llm_json_response(
            result_text,
            expected_type='array',
            save_on_error=True,
            error_file_prefix='failed_todo_response'
        )
        
        # 打印解析结果
        if tasks is not None:
            logger.info("=" * 60)
            logger.info(f"✅ JSON 解析成功！生成了 {len(tasks)} 个待办任务")
            for idx, task in enumerate(tasks):
                logger.info(f"  任务 {idx + 1}:")
                logger.info(f"    - title: {task.get('title', 'N/A')}")
                logger.info(f"    - priority: {task.get('priority', 'N/A')}")
                logger.info(f"    - description 长度: {len(task.get('description', ''))} 字符")
            logger.info("=" * 60)
            return tasks if isinstance(tasks, list) else []
        else:
            logger.warning("=" * 60)
            logger.warning("⚠️ JSON 解析失败，返回空列表")
            logger.warning("=" * 60)
            return []
    except Exception as e:
        logger.exception(f"LLM task creation error: {e}")
        return []


# 语义搜索相关辅助函数
def _retrieve_relevant_history(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """通过语义搜索检索与当前待办推断相关的历史上下文"""
    if not config.ENABLE_VECTOR_STORAGE:
        logger.info("Vector storage disabled, skip semantic retrieval for todos")
        return []

    try:
        query_texts = _build_query_texts(context)
        if not query_texts:
            return []

        all_results: List[Dict[str, Any]] = []
        for query_text in query_texts:
            try:
                results = search_similar_content(query=query_text, limit=5)
                for item in results:
                    item['query_source'] = query_text[:50] + "..." if len(query_text) > 50 else query_text
                    all_results.append(item)
            except Exception as exc:
                logger.warning(f"Semantic search failed for todo query '{query_text[:50]}...': {exc}")

        unique = _deduplicate_results(all_results)
        return _format_historical_contexts(unique[:10])
    except Exception as exc:
        logger.exception(f"Todo semantic retrieval error: {exc}")
        return []


def _build_query_texts(context: Dict[str, Any]) -> List[str]:
    """根据当前上下文构建语义检索用的查询文本"""
    query_texts: List[str] = []
    try:
        web_items = context.get("web_items", [])
        if web_items:
            web_topics = []
            for item in web_items[:5]:
                title = item.get('title') or ''
                url = item.get('url') or ''
                if title and len(title) > 10:
                    web_topics.append(title)
                elif url:
                    web_topics.append(url)
            if web_topics:
                combined = " ".join(web_topics[:3])
                if combined:
                    query_texts.append(combined)

        activities = context.get("activities", [])
        if activities:
            activity_parts = []
            for act in activities[:3]:
                window_title = act.get('window_title') or ''
                app_name = act.get('app_name') or ''
                if window_title and len(window_title) > 5:
                    activity_parts.append(window_title)
                elif app_name:
                    activity_parts.append(app_name)
            if activity_parts:
                query = " ".join(activity_parts[:2])
                if query and query not in query_texts:
                    query_texts.append(query)

        existing_todos = context.get("existing_todos", [])
        if existing_todos and len(query_texts) < 2:
            todo_parts = []
            for todo in existing_todos[:2]:
                title = todo.get('title') or ''
                description = todo.get('description') or ''
                content = title if len(title) > 10 else description
                if content:
                    todo_parts.append(content)
            if todo_parts:
                query_texts.append(" ".join(todo_parts))

        return query_texts
    except Exception as exc:
        logger.exception(f"Todo query text build error: {exc}")
        return []


def _deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """根据 web_data_id 去重搜索结果"""
    seen = set()
    unique: List[Dict[str, Any]] = []
    for item in results:
        metadata = item.get('metadata', {})
        web_id = metadata.get('web_data_id')
        if web_id:
            if web_id in seen:
                continue
            seen.add(web_id)
        unique.append(item)

    unique.sort(key=lambda x: x.get('distance', 1.0))
    return unique


def _format_historical_contexts(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """格式化语义搜索结果，供待办提示使用"""
    formatted: List[Dict[str, Any]] = []
    for idx, item in enumerate(results):
        metadata = item.get('metadata', {})
        content = item.get('content', '')
        similarity = 1.0 - item.get('distance', 1.0)
        formatted.append({
            'index': idx + 1,
            'title': metadata.get('title', 'Unknown Title'),
            'url': metadata.get('url', ''),
            'source': metadata.get('source', 'web_crawler'),
            'content_preview': content[:300] + "..." if len(content) > 300 else content,
            'similarity_score': round(similarity, 3),
            'tags': metadata.get('tags', [])
        })
    return formatted


# 移除旧的 _parse_task_json 函数，改用统一的 parse_llm_json_response

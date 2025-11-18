"""
智能对话接口路由
"""
import sys
from pathlib import Path

from numpy import True_
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from flask import Blueprint, request, Response, stream_with_context
import config
from utils.helpers import convert_resp, auth_required, get_logger
from utils.llm import get_openai_client
from typing import Dict, Any, List, Optional

# 导入 llm_strategy 相关类
from routes.llm_strategy import (
    LLMContextStrategy,
    Intent,
    ContextCollection,
    ContextItem,
    ContextSufficiency
)
from utils.db import get_todos
from utils.prompt_config import get_current_prompts
from string import Template

logger = get_logger(__name__)

agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')

# 工作流状态存储（简化实现，实际应该使用数据库或 Redis）
workflows = {}

# 全局策略实例（单例模式）
_strategy_instance = None

def get_strategy() -> LLMContextStrategy:
    """获取策略实例（单例）"""
    global _strategy_instance
    if _strategy_instance is None:
        _strategy_instance = LLMContextStrategy()
    return _strategy_instance


def run_async(coro):
    """在 Flask 中运行异步函数"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # 如果事件循环已经在运行，创建新任务
        import nest_asyncio
        nest_asyncio.apply()
    
    return loop.run_until_complete(coro)


async def process_query_with_strategy(
    query: str,
    session_id: str,
    use_tools: bool = True,
    max_iterations: int = 3,
    stream_final_response: bool = True,
    page_context: Optional[Dict[str, Any]] = None,  # 当前页面上下文
    optimize_prompt: bool = False  # 是否优化用户提示词
) -> dict:
    """
    使用策略处理查询（智能工具调用和上下文管理）
    
    Args:
        query: 用户查询
        session_id: 会话ID
        use_tools: 是否使用工具
        max_iterations: 最大迭代次数
        stream_final_response: 是否流式输出最终回答
        page_context: 当前页面上下文，包含 url、title 和 content
        optimize_prompt: 是否优化用户提示词
        
    Returns:
        处理结果字典
    """ 
    strategy = get_strategy()
    context = ContextCollection()
    intent = Intent(query=query, type="general")
    
    # ========== 步骤 0.5: 处理当前页面上下文（新增） ==========
    current_page_url = None
    if page_context:
        page_url = page_context.get("url")
        page_content = page_context.get("content")
        
        if page_url:
            current_page_url = page_url.rstrip('/')  # 规范化URL
            strategy.current_page_url = current_page_url
            logger.info(f"Current page URL set: {current_page_url}")
            
            # 如果提供了页面内容，存储到向量数据库
            if page_content and page_content.strip() and config.ENABLE_VECTOR_STORAGE:
                try:
                    from utils.db import insert_web_data
                    from utils.vectorstore import add_web_data_to_vectorstore
                    from utils.llm import generate_embeddings
                    
                    # 存储到SQLite
                    web_data_id = insert_web_data(
                        title=page_context.get("title", page_url),
                        url=page_url,
                        content=page_content,
                        source="chat_context"
                    )
                    
                    logger.info(f"Stored page content to SQLite: web_data_id={web_data_id}, url={page_url}")
                    
                    # 存储到向量数据库，传递 session_id
                    def embedding_fn(texts):
                        return generate_embeddings(texts)
                    
                    success = add_web_data_to_vectorstore(
                        web_data_id=web_data_id,
                        title=page_context.get("title", page_url),
                        url=page_url,
                        content=page_content,
                        source="chat_context",
                        embedding_function=embedding_fn,
                        session_id=session_id  # 传递 session_id
                    )
                    
                    if success:
                        logger.info(f"Stored current page content to vectorstore: {page_url}")
                    else:
                        logger.warning(f"Failed to store page content to vectorstore: {page_url}")
                except Exception as e:
                    logger.warning(f"Failed to store page content: {e}", exc_info=True)
    
    # ========== 步骤 0: 从会话记忆检索相关上下文（补充） ==========
    if use_tools:
        logger.info(f"Retrieving session memory for session: {session_id}")
        memory_items = await strategy.retrieve_session_memory(session_id, query)
        if memory_items:
            logger.info(f"Retrieved {len(memory_items)} items from session memory")
            for item in memory_items:
                context.add(item)
    
    # 构建消息历史（用于最终生成回答）
    messages = [
        {
            "role": "system",
            "content": "你是一个智能助手，能够帮助用户解答问题、分析信息和提供建议。请主动使用上下文信息回答问题，如果上下文信息不够完整，可以基于常识和最佳实践给出合理的建议。用简洁、清晰、直接的方式回答，避免过度保守。"
        }
    ]
    
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Processing query iteration {iteration}/{max_iterations}")
        
        # 1. 评估上下文充分性（跳过第一轮，因为第一轮强制调用user_profile）
        if iteration > 1 and context.items:
            sufficiency = await strategy.evaluate_sufficiency(context, intent)
            logger.info(f"Context sufficiency: {sufficiency}")
            
            if sufficiency == ContextSufficiency.SUFFICIENT:
                logger.info("Context is sufficient, proceeding to generate response")
                break
        
        # 2. 如果需要工具且未达到最大迭代次数，规划工具调用
        if use_tools and iteration < max_iterations:
            # 第一轮总是强制调用 get_user_profile（修改：无论上下文是否为空）
            if iteration == 1:
                logger.info("First iteration: forcing get_user_profile to retrieve local context")
                # 强制先调用 get_user_profile，传入当前页面URL
                tool_calls = [{
                    "id": "force_user_profile",
                    "function_name": "get_user_profile",
                    "arguments": {
                        "query": query,
                        "session_id": session_id,
                        "context_type": "all",
                        "limit": 10,
                        "current_page_url": current_page_url or ""  # 传递当前页面URL
                    }
                }]
                analysis_msg = {"content": "First iteration: retrieving local user context (todos, tips, pages, and session memory)"}
            else:
                # 后续迭代，正常规划工具调用
                tool_calls, analysis_msg = await strategy.analyze_and_plan_tools(
                    intent, context, iteration
                )
            
            if analysis_msg.get("content"):
                logger.info(f"Analysis: {analysis_msg['content']}")
            
        # 3. 执行工具调用
            if tool_calls:
                logger.info(f"Executing {len(tool_calls)} tool calls")
                
                # 为 get_user_profile 工具自动添加 session_id 和 current_page_url
                for tool_call in tool_calls:
                    if tool_call.get("function_name") == "get_user_profile":
                        if "session_id" not in tool_call.get("arguments", {}):
                            tool_call["arguments"]["session_id"] = session_id
                        # 如果有当前页面URL，传递给工具
                        if current_page_url and "current_page_url" not in tool_call.get("arguments", {}):
                            tool_call["arguments"]["current_page_url"] = current_page_url
                
                tool_results = await strategy.execute_tool_calls_parallel(tool_calls)
                
                # 4. 验证和过滤工具结果
                relevant_items, validation_msg = await strategy.validate_and_filter_tool_results(
                    tool_calls, tool_results, intent, context
                )
                
                # 5. 添加到上下文
                for item in relevant_items:
                    context.add(item)
                
                logger.info(f"Added {len(relevant_items)} relevant context items")
                
                # 每一轮迭代后，将对话内容存储到向量数据库（新增）
                if relevant_items:
                    await store_iteration_context_to_vectorstore(
                        session_id=session_id,
                        iteration=iteration,
                        query=query,
                        context_items=relevant_items
                    )
                
                # 如果第一次迭代获取到了上下文，继续下一次迭代（可能还需要其他工具）
                if iteration == 1 and relevant_items:
                    logger.info("First iteration retrieved context, continuing to next iteration for potential additional tools")
                    continue  # 继续下一次迭代，而不是 break
            else:
                # 没有工具调用，退出循环
                logger.info("No tool calls planned, exiting loop")
                break
        else:
            # use_tools 为 False 或达到最大迭代次数，退出循环
            logger.info(f"Exiting loop: use_tools={use_tools}, iteration={iteration}")
            break
    
    # ========== 步骤 6: 将关键信息存储到会话记忆（补充） ==========
    if use_tools and context.items:
        logger.info(f"Storing context to session memory for session: {session_id}")
        await strategy.store_to_session_memory(session_id, context, query)
    
    # ========== 步骤 6.3: 优化用户提示词（新增） ==========
    optimized_query = query  # 默认使用原查询
    optimization_result = None
    
    if optimize_prompt and context.items:
        logger.info(f"Optimizing user prompt based on context")
        optimization_result = await optimize_user_prompt(query, context, session_id)
        
        if optimization_result.get("success"):
            optimized_query = optimization_result.get("optimized_query", query)
            logger.info(f"Prompt optimization successful: confidence={optimization_result.get('confidence', 0)}")
        else:
            logger.warning(f"Prompt optimization failed: {optimization_result.get('error', 'unknown error')}")
    
    # ========== 步骤 6.5: 检查时间冲突（新增） ==========
    # 从上下文中提取todo信息，检查是否有时间冲突
    conflict_check_result = check_schedule_conflict(context, query)
    if conflict_check_result.get("has_conflict"):
        # 发现冲突，直接返回提醒，不生成回答
        return {
            "success": True,
            "response": conflict_check_result.get("warning_message", "检测到时间冲突，请检查您的日程安排。"),
            "context_items_count": len(context.items),
            "iterations": iteration,
            "has_schedule_conflict": True,
            "conflict_details": conflict_check_result.get("conflict_details", []),
            "context_summary": [
                {
                    "source": item.source,
                    "content_preview": item.content[:200]
                }
                for item in context.items[:5]
            ]
        }
    
    # 7. 构建最终响应
    # 构建上下文摘要
    if context.items:
        context_summary = "\n\n".join([
            f"[{item.source}] {item.content[:500]}"
            for item in context.items[:10]  # 最多10个上下文项
        ])
        # 使用优化后的查询（如果启用了优化）
        final_query = optimized_query if optimize_prompt else query
        user_message = f"""用户问题: {final_query}

相关上下文信息:
{context_summary}

请基于以上上下文信息直接回答用户的问题。如果上下文信息不够完整，可以结合常识和最佳实践给出合理的建议。"""
    else:
        user_message = optimized_query if optimize_prompt else query
    
    messages.append({"role": "user", "content": user_message})
    
    # 8. 调用 LLM 生成最终回答
    client = get_openai_client()
    if not client:
        return {
            "success": False,
            "error": "LLM 服务不可用"
        }
    
    # 根据 stream_final_response 参数决定是否使用流式
    if stream_final_response:
        # 使用流式 API
        stream = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=config.LLM_MAX_TOKENS,
            stream=True
        )
        
        # 收集流式响应
        final_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                final_response += chunk.choices[0].delta.content
        
        final_response = final_response.strip()
    else:
        # 非流式 API
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=config.LLM_MAX_TOKENS,
            stream=False
        )
        final_response = response.choices[0].message.content.strip()
    
    # ========== 步骤 9: 将最终对话内容存储到向量数据库（新增） ==========
    if use_tools and final_response:
        await store_conversation_to_vectorstore(
            session_id=session_id,
            query=query,
            response=final_response,
            context_items=context.items
        )
    
    result = {
        "success": True,
        "response": final_response,
        "context_items_count": len(context.items),
        "iterations": iteration,
        "context_summary": [
            {
                "source": item.source,
                "content_preview": item.content[:200]
            }
            for item in context.items[:5]
        ]
    }
    
    # 如果进行了提示词优化，添加优化信息
    if optimize_prompt and optimization_result:
        result["prompt_optimization"] = {
            "enabled": True,
            "original_query": optimization_result.get("original_query", query),
            "optimized_query": optimization_result.get("optimized_query", query),
            "optimization_reason": optimization_result.get("optimization_reason", ""),
            "confidence": optimization_result.get("confidence", 0.0)
        }
    
    return result


# ========== 新增：存储迭代上下文到向量数据库 ==========
async def store_iteration_context_to_vectorstore(
    session_id: str,
    iteration: int,
    query: str,
    context_items: List[ContextItem]
):
    """
    将每一轮迭代获取的上下文存储到向量数据库
    
    Args:
        session_id: 会话ID
        iteration: 迭代轮次
        query: 用户查询
        context_items: 本轮获取的上下文项
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            return
        
        if not context_items:
            return
        
        from utils.vectorstore import add_session_memory_to_vectorstore
        from utils.llm import generate_embedding
        
        # 将本轮上下文合并为一个文本
        context_texts = []
        for item in context_items:
            source = item.source
            content = item.content
            if source == "user_profile":
                ctx_type = item.metadata.get("context_type", "unknown")
                context_texts.append(f"[{ctx_type}] {content}")
            elif source in ["current_page", "web_page"]:
                context_texts.append(f"[页面内容] {content}")
            elif source == "session_memory":
                context_texts.append(f"[会话记忆] {content}")
            else:
                context_texts.append(f"[{source}] {content}")
        
        combined_context = "\n\n".join(context_texts)
        
        # 构建记忆内容：用户查询 + 检索到的上下文
        memory_content = f"用户查询: {query}\n\n检索到的上下文（第{iteration}轮）:\n{combined_context}"
        
        # 存储到向量数据库
        success = add_session_memory_to_vectorstore(
            session_id=session_id,
            content=memory_content,
            content_type="iteration_context",
            metadata={
                "iteration": iteration,
                "query": query,
                "context_count": len(context_items)
            }
        )
        
        if success:
            logger.info(f"Stored iteration {iteration} context to vectorstore: {len(context_items)} items")
        
    except Exception as e:
        logger.warning(f"Failed to store iteration context to vectorstore: {e}", exc_info=True)


# ========== 新增：存储完整对话到向量数据库 ==========
async def store_conversation_to_vectorstore(
    session_id: str,
    query: str,
    response: str,
    context_items: List[ContextItem]
):
    """
    将完整的对话（用户查询 + AI回答）存储到向量数据库
    
    Args:
        session_id: 会话ID
        query: 用户查询
        response: AI回答
        context_items: 使用的上下文项
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            return
        
        if not query or not response:
            return
        
        from utils.vectorstore import add_session_memory_to_vectorstore
        from utils.db import insert_web_data
        from utils.llm import generate_embeddings
        
        # 构建对话内容
        conversation_text = f"用户: {query}\n\n助手: {response}"
        
        # 如果有上下文，也包含进去
        if context_items:
            context_summary = "\n\n参考上下文:\n" + "\n".join([
                f"- [{item.source}] {item.content[:200]}"
                for item in context_items[:5]
            ])
            conversation_text += context_summary
        
        # 方法1: 存储到会话记忆（向量数据库）
        success = add_session_memory_to_vectorstore(
            session_id=session_id,
            content=conversation_text,
            content_type="conversation",
            metadata={
                "query": query,
                "response_length": len(response),
                "context_count": len(context_items)
            }
        )
        
        if success:
            logger.info(f"Stored conversation to session memory vectorstore")
        
        # 方法2: 也可以存储到web_data（SQLite + 向量数据库）
        try:
            web_data_id = insert_web_data(
                title=f"对话记录 - {query[:50]}",
                url="",  # 对话没有URL
                content=conversation_text,
                source="chat_conversation",
                metadata={
                    "session_id": session_id,
                    "query": query,
                    "response_length": len(response)
                }
            )
            
            # 存储到向量数据库，传递 session_id
            if web_data_id:
                def embedding_fn(texts):
                    return generate_embeddings(texts)
                
                from utils.vectorstore import add_web_data_to_vectorstore
                add_web_data_to_vectorstore(
                    web_data_id=web_data_id,
                    title=f"对话记录 - {query[:50]}",
                    url="",
                    content=conversation_text,
                    source="chat_conversation",
                    embedding_function=embedding_fn,
                    session_id=session_id  # 传递 session_id
                )
                
                logger.info(f"Stored conversation to web_data vectorstore: web_data_id={web_data_id}")
        except Exception as e:
            logger.warning(f"Failed to store conversation to web_data: {e}")
        
    except Exception as e:
        logger.warning(f"Failed to store conversation to vectorstore: {e}", exc_info=True)


async def optimize_user_prompt(
    original_query: str,
    context: ContextCollection,
    session_id: str
) -> Dict[str, Any]:
    """
    基于上下文和大模型优化用户提示词
    
    Args:
        original_query: 用户原始查询
        context: 已收集的上下文信息
        session_id: 会话ID
    
    Returns:
        {
            "success": bool,
            "original_query": str,
            "optimized_query": str,
            "optimization_reason": str  # 优化说明
        }
    """
    try:
        client = get_openai_client()
        if not client:
            logger.warning("LLM unavailable for prompt optimization")
            return {
                "success": False,
                "original_query": original_query,
                "optimized_query": original_query,
                "error": "LLM服务不可用"
            }
        
        # 构建上下文摘要（限制长度，突出关键信息）
        context_summary_parts = []
        
        # 提取用户待办事项
        task_items = [item for item in context.items if item.source == "user_profile" and item.metadata.get("context_type") == "task"]
        if task_items:
            task_summary = "用户待办事项：\n" + "\n".join([f"- {item.content[:100]}" for item in task_items[:5]])
            context_summary_parts.append(task_summary)
        
        # 提取智能提示
        tip_items = [item for item in context.items if item.source == "user_profile" and item.metadata.get("context_type") == "tip"]
        if tip_items:
            tip_summary = "智能提示：\n" + "\n".join([f"- {item.content[:100]}" for item in tip_items[:3]])
            context_summary_parts.append(tip_summary)
        
        # 提取会话记忆
        memory_items = [item for item in context.items if item.source == "session_memory"]
        if memory_items:
            memory_summary = "会话记忆：\n" + "\n".join([f"- {item.content[:100]}" for item in memory_items[:5]])
            context_summary_parts.append(memory_summary)
        
        # 提取页面上下文
        page_items = [item for item in context.items if item.source in ["current_page", "web_page"]]
        if page_items:
            page_summary = "相关页面：\n" + "\n".join([
                f"- {item.metadata.get('url', 'unknown')}: {item.content[:80]}" 
                for item in page_items[:3]
            ])
            context_summary_parts.append(page_summary)
        
        context_summary = "\n\n".join(context_summary_parts) if context_summary_parts else "暂无上下文信息"
        
        # 动态获取当前配置的提示词
        prompts = get_current_prompts()
        optimization_prompts = prompts.get("prompt_optimization", {})
        
        # 构建优化提示词
        system_prompt = optimization_prompts.get("system", "")
        user_template = optimization_prompts.get("user_template", "")
        
        # 使用 Template 替换变量
        user_prompt = Template(user_template).safe_substitute(
            original_query=original_query,
            context_summary=context_summary,
            session_id=session_id
        )
        
        # 调用 LLM 优化
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # 较低温度以保持稳定
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        # 解析结果
        result_text = response.choices[0].message.content.strip()
        result_json = json.loads(result_text)
        
        optimized_query = result_json.get("optimized_query", original_query)
        optimization_reason = result_json.get("optimization_reason", "")
        confidence = result_json.get("confidence", 0.5)
        
        
        logger.info(f"Prompt optimized: '{original_query}' -> '{optimized_query}' (confidence: {confidence})")
        
        return {
            "success": True,
            "original_query": original_query,
            "optimized_query": optimized_query,
            "optimization_reason": optimization_reason,
            "confidence": confidence
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse optimization result: {e}")
        return {
            "success": False,
            "original_query": original_query,
            "optimized_query": original_query,
            "error": "优化结果解析失败"
        }
    except Exception as e:
        logger.exception(f"Error optimizing prompt: {e}")
        return {
            "success": False,
            "original_query": original_query,
            "optimized_query": original_query,
            "error": str(e)
        }


def check_schedule_conflict(context: ContextCollection, user_query: str) -> Dict[str, Any]:
    """
    检查用户的查询是否与现有日程安排有冲突
    只检查用户查询中提到的模糊时间概念（如"明天"、"后天"），不与todo的时间戳对比
    
    Args:
        context: 上下文集合
        user_query: 用户查询
    
    Returns:
        {
            "has_conflict": bool,
            "warning_message": str,
            "conflict_details": List[Dict]
        }
    """
    try:
        # 快速检查：如果查询不包含时间相关关键词，直接返回
        time_keywords = ['明天', '后天', '今天', '下周一', '下周二', '下周三', '下周四', '下周五', 
                        '下周', '下个月', '周末', '计划', '出行', '去', '玩', '旅行', '活动', 
                        '安排', '时间', '几点', '什么时候', '何时', '日期', '行程']
        query_lower = user_query.lower()
        if not any(keyword in query_lower for keyword in time_keywords):
            # 不涉及时间，跳过检查
            return {"has_conflict": False}
        
        # 从上下文中提取所有task类型的项
        task_items = [
            item for item in context.items
            if item.source == "user_profile" and item.metadata.get("context_type") == "task"
        ]
        
        if not task_items:
            # 没有任务信息，无需检查
            return {"has_conflict": False}
        
        # 提取所有todo_id
        todo_ids = []
        for item in task_items:
            todo_id = item.metadata.get("todo_id")
            if todo_id:
                todo_ids.append(int(todo_id))
        
        if not todo_ids:
            # 没有todo_id，无法检查
            return {"has_conflict": False}
        
        # 从数据库获取todo信息（只需要标题和描述，不需要时间戳）
        all_todos = get_todos(limit=100)
        relevant_todos = []
        for todo in all_todos:
            if todo.get("id") in todo_ids:
                relevant_todos.append({
                    "id": todo.get("id"),
                    "title": todo.get("title", ""),
                    "description": todo.get("description", ""),
                    "status": todo.get("status", 0)
                })
        
        if not relevant_todos:
            return {"has_conflict": False}
        
        # 使用LLM提取用户查询中的时间概念，并检查是否与todo冲突
        client = get_openai_client()
        if not client:
            return {"has_conflict": False}
        
        # 构建待办事项摘要（只包含标题和描述）
        todos_summary = "\n".join([
            f"- {todo['title']}"
            + (f" ({todo['description']})" if todo.get('description') else "")
            for todo in relevant_todos[:10]  # 最多10个todo
        ])
        
        # 优化的提示词：要求更精确的时间段判断
        analysis_prompt = f"""用户查询: {user_query}

用户的待办事项列表:
{todos_summary}

请精确分析时间冲突：

1. **提取时间概念**：从用户查询和待办事项中提取完整的时间概念，包括：
   - 日期概念：如"明天"、"后天"、"下周"
   - 时间段：如"早上"、"上午"、"中午"、"下午"、"晚上"、"九点"、"十点"等
   - 完整时间：如"明天下午"、"明天早上九点"

2. **判断冲突**：只有当以下条件**同时满足**时才认为冲突：
   - 日期概念相同（如都是"明天"）
   - **并且**时间段重叠或无法确定时间段（如"明天下午"与"明天早上九点"不冲突，因为时间段不重叠）
   - **或者**待办事项没有明确时间段，但用户查询需要长时间（如"明天出去玩一整天"）

3. **特殊情况**：
   - "明天记得买XX"这类没有具体时间段的待办事项，如果用户查询是"明天下午"，通常不冲突（可以下午出去前买）
   - "明天早上九点"和"明天下午"不冲突
   - "明天"和"明天下午"不冲突（后者更具体，可以安排）

请返回JSON格式：
{{
    "query_time": {{
        "date": "明天",
        "time_period": "下午",  // 可能为空
        "is_flexible": false  // 是否时间灵活
    }},
    "has_conflict": true/false,
    "conflict_todos": ["待办事项标题"],  // 只包含真正冲突的
    "conflict_reason": "详细说明为什么冲突（包括时间段对比）"
}}"""
        
        try:
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "你是日程冲突检测助手。必须精确判断时间段是否重叠。只有日期相同且时间段重叠时才认为冲突。返回JSON。"},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=400
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            import json
            import re
            # 提取JSON部分
            json_match = re.search(r'\{[^{}]*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis_result = json.loads(json_match.group())
            else:
                analysis_result = json.loads(analysis_text)
            
            if analysis_result.get("has_conflict"):
                # 发现冲突
                conflict_todos = analysis_result.get("conflict_todos", [])
                query_time = analysis_result.get("query_time", {})
                conflict_reason = analysis_result.get("conflict_reason", "检测到时间冲突")
                
                # 构建警告消息
                warning_message = f"⚠️ 时间冲突提醒：\n\n"
                
                date_concept = query_time.get("date", "")
                time_period = query_time.get("time_period", "")
                if date_concept:
                    if time_period:
                        warning_message += f"您提到的「{date_concept}{time_period}」可能与以下待办事项冲突：\n\n"
                    else:
                        warning_message += f"您提到的「{date_concept}」可能与以下待办事项冲突：\n\n"
                
                warning_message += f"{conflict_reason}\n\n"
                
                if conflict_todos:
                    warning_message += "冲突的待办事项：\n"
                    for todo_title in conflict_todos:
                        warning_message += f"- {todo_title}\n"
                    warning_message += "\n"
                
                warning_message += "请调整您的计划，避免时间冲突。"
                
                return {
                    "has_conflict": True,
                    "warning_message": warning_message,
                    "conflict_details": [
                        {
                            "todo_title": title,
                            "query_date": date_concept,
                            "query_time_period": time_period,
                            "reason": conflict_reason
                        }
                        for title in conflict_todos
                    ]
                }
            
        except Exception as e:
            logger.warning(f"Error analyzing schedule conflict: {e}")
            # 如果分析失败，不阻止正常流程
            return {"has_conflict": False}
        
        return {"has_conflict": False}
        
    except Exception as e:
        logger.exception(f"Error checking schedule conflict: {e}")
        # 出错时不阻止正常流程
        return {"has_conflict": False}


def call_llm(query: str, temperature: float = 0.7) -> str:
    """调用大模型生成响应（简单版本，不使用工具）"""
    try:
        client = get_openai_client()
        if not client:
            return "抱歉，LLM 服务暂时不可用，请检查 API Key 配置。"
        
        # 直接调用大模型
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个智能助手，能够帮助用户解答问题、分析信息和提供建议。请用简洁、清晰的方式回答。"},
                {"role": "user", "content": query}
            ],
            temperature=temperature,
            max_tokens=config.LLM_MAX_TOKENS
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.exception(f"Error calling LLM: {e}")
        return f"抱歉，处理您的请求时出现错误：{str(e)}"


@agent_bp.route('/chat', methods=['POST'])
@auth_required
def chat():
    """智能对话接口（非流式）- 支持工具调用和上下文管理"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return convert_resp(code=400, status=400, message="缺少 query 参数")
        
        query = data['query']
        session_id = data.get('session_id') or str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())
        temperature = data.get('temperature', 0.7)
        use_tools = data.get('use_tools', True)  # 默认启用工具
        max_iterations = data.get('max_iterations', 3)
        optimize_prompt = data.get('optimize_prompt', False)  # 新增：提示词优化开关
        
        # 获取当前页面上下文（新增）
        page_context = data.get('context', {}).get('page')
        if page_context:
            logger.info(f"Received page context: url={page_context.get('url')}")
        
        logger.info(f"Processing chat query: {query}, session: {session_id}, use_tools: {use_tools}, optimize_prompt: {optimize_prompt}")
        
        # 根据配置选择处理方式
        if use_tools:
            # 使用智能策略（工具调用 + 上下文管理）
            result = run_async(
                process_query_with_strategy(
                    query, 
                    session_id, 
                    use_tools, 
                    max_iterations,
                    page_context=page_context,  # 传递页面上下文
                    optimize_prompt=optimize_prompt  # 传递优化开关
                )
            )
            
            if not result.get("success"):
                return convert_resp(
                    code=500,
                    status=500,
                    message=result.get("error", "处理失败")
                )
            
            llm_response = result["response"]
            context_info = {
                "context_items_count": result.get("context_items_count", 0),
                "iterations": result.get("iterations", 0),
                "context_summary": result.get("context_summary", [])
            }
        else:
            # 简单调用（不使用工具）
            llm_response = call_llm(query, temperature)
            context_info = {}
        
        # 构建响应
        response = {
            "success": True,
            "workflow_id": workflow_id,
            "session_id": session_id,
            "query": query,
            "response": llm_response,
            "timestamp": datetime.now().isoformat(),
            "model": config.LLM_MODEL,
            "context_info": context_info
        }
        
        # 保存工作流状态
        workflows[workflow_id] = {
            "query": query,
            "session_id": session_id,
            "status": "completed",
            "result": response,
            "created_at": datetime.now().isoformat(),
            "use_tools": use_tools
        }
        
        return convert_resp(data=response)
        
    except Exception as e:
        logger.exception(f"Error in chat: {e}")
        return convert_resp(code=500, status=500, message=f"对话失败: {str(e)}")


@agent_bp.route('/chat/stream', methods=['POST'])
@auth_required
def chat_stream():
    """智能对话接口（流式）- 支持工具调用"""
    
    def generate():
        try:
            data = request.get_json()
            
            if not data or 'query' not in data:
                yield f"data: {json.dumps({'type': 'error', 'content': '缺少 query 参数'}, ensure_ascii=False)}\n\n"
                return
            
            query = data['query']
            session_id = data.get('session_id') or str(uuid.uuid4())
            workflow_id = str(uuid.uuid4())
            temperature = data.get('temperature', 0.7)
            use_tools = data.get('use_tools', True)
            max_iterations = data.get('max_iterations', 3)
            optimize_prompt = data.get('optimize_prompt', False)  # 新增：提示词优化开关
            
            # 获取当前页面上下文（新增）
            page_context = data.get('context', {}).get('page')
            if page_context:
                logger.info(f"Received page context: url={page_context.get('url')}")
            
            logger.info(f"Processing stream chat query: {query}, session: {session_id}, use_tools: {use_tools}, optimize_prompt: {optimize_prompt}")
            
            # 发送会话开始事件（立即发送）
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'workflow_id': workflow_id, 'model': config.LLM_MODEL}, ensure_ascii=False)}\n\n"
            
            if use_tools:
                # 使用智能策略（工具调用 + 上下文管理）
                # 工具调用阶段：非流式执行，获取上下文
                strategy_result = run_async(
                    process_query_with_strategy(
                        query, 
                        session_id, 
                        use_tools, 
                        max_iterations, 
                        stream_final_response=False,
                        page_context=page_context,  # 传递页面上下文
                        optimize_prompt=optimize_prompt  # 传递优化开关
                    )
                )
                
                if not strategy_result.get("success"):
                    yield f"data: {json.dumps({'type': 'error', 'content': strategy_result.get('error', '处理失败')}, ensure_ascii=False)}\n\n"
                    return
                
                # 检查时间冲突（新增）
                # 构建ContextCollection用于冲突检查
                from routes.llm_strategy import ContextCollection
                context = ContextCollection()
                # 从strategy_result中重建context（如果需要）
                # 或者直接从context_summary中获取信息
                
                # 简化的冲突检查：直接使用strategy_result中的context信息
                # 这里我们需要从strategy_result中提取todo信息
                # 为了简化，我们可以直接在process_query_with_strategy中检查
                # 或者在这里重新构建context
                
                # 发送工具调用完成事件
                if strategy_result.get("context_items_count", 0) > 0:
                    yield f"data: {json.dumps({'type': 'tool_complete', 'context_items': strategy_result.get('context_items_count', 0), 'iterations': strategy_result.get('iterations', 0)}, ensure_ascii=False)}\n\n"
                
                # 发送提示词优化事件（如果启用了优化）
                if optimize_prompt and strategy_result.get("prompt_optimization"):
                    opt_info = strategy_result["prompt_optimization"]
                    optimization_event = {
                        "type": "prompt_optimized",
                        "original_query": opt_info.get("original_query", query),
                        "optimized_query": opt_info.get("optimized_query", query),
                        "optimization_reason": opt_info.get("optimization_reason", ""),
                        "confidence": opt_info.get("confidence", 0.0),
                        "workflow_id": workflow_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(optimization_event, ensure_ascii=False)}\n\n"
                    logger.info(f"Sent prompt optimization event: {opt_info.get('optimized_query', query)[:50]}...")
                
                # 检查是否有时间冲突（在流式输出前检查）
                # 注意：这里需要从strategy_result中提取context信息
                # 为了简化，我们可以在process_query_with_strategy中添加一个标志
                # 或者创建一个辅助函数来检查
                
                # 如果检测到冲突，直接发送警告消息
                if strategy_result.get("has_schedule_conflict"):
                    warning_message = strategy_result.get("response", "检测到时间冲突，请检查您的日程安排。")
                    # 流式输出警告消息
                    for char in warning_message:
                        yield f"data: {json.dumps({'type': 'content', 'content': char, 'workflow_id': workflow_id}, ensure_ascii=False)}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'workflow_id': workflow_id, 'full_response': warning_message}, ensure_ascii=False)}\n\n"
                    return
                
                # 使用流式 API 生成最终回答
                client = get_openai_client()
                if not client:
                    yield f"data: {json.dumps({'type': 'error', 'content': 'LLM 服务不可用'}, ensure_ascii=False)}\n\n"
                    return
                
                # 构建最终回答的消息（使用工具调用获取的上下文）
                messages = [
                    {
                        "role": "system",
                        "content": "你是一个智能助手，能够帮助用户解答问题、分析信息和提供建议。请基于提供的上下文信息，用简洁、清晰的方式回答。"
                    }
                ]
                
                # 构建上下文摘要
                context_summary = strategy_result.get("context_summary", [])
                if context_summary:
                    context_text = "\n\n".join([
                        f"[{item.get('source', 'unknown')}] {item.get('content_preview', '')}"
                        for item in context_summary
                    ])
                    user_message = f"""用户问题: {query}

相关上下文信息:
{context_text}

请基于以上上下文信息直接回答用户的问题。如果上下文信息不够完整，可以结合常识和最佳实践给出合理的建议。"""
                else:
                    user_message = query
                
                messages.append({"role": "user", "content": user_message})
                
                # 流式调用 LLM
                logger.info("Starting LLM stream generation")
                stream = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=config.LLM_MAX_TOKENS,
                    stream=True
                )
                
                # 流式输出每个 token（立即发送，不缓冲）
                full_response = ""
                chunk_count = 0
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            content = delta.content
                            full_response += content
                            chunk_count += 1
                            
                            # 立即发送每个 chunk
                            event = {
                                "type": "content",
                                "content": content,
                                "workflow_id": workflow_id,
                                "timestamp": datetime.now().isoformat()
                            }
                            # 确保每个 chunk 都立即发送
                            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                            
                            # 每10个chunk记录一次日志（避免日志过多）
                            if chunk_count % 10 == 0:
                                logger.debug(f"Streamed {chunk_count} chunks, current length: {len(full_response)}")
                
                logger.info(f"Stream generation completed, total chunks: {chunk_count}, total length: {len(full_response)}")
                
                # 发送完成事件
                yield f"data: {json.dumps({'type': 'done', 'workflow_id': workflow_id, 'full_response': full_response}, ensure_ascii=False)}\n\n"
                
                # 保存工作流状态
                workflows[workflow_id] = {
                    "query": query,
                    "session_id": session_id,
                    "status": "completed",
                    "response": full_response,
                    "created_at": datetime.now().isoformat(),
                    "use_tools": use_tools
                }
            else:
                # 简单流式调用（不使用工具）
                client = get_openai_client()
                if not client:
                    yield f"data: {json.dumps({'type': 'error', 'content': 'LLM 服务不可用'}, ensure_ascii=False)}\n\n"
                    return
                
                # 流式调用
                stream = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": "你是一个智能助手，能够帮助用户解答问题、分析信息和提供建议。请用简洁、清晰的方式回答。"},
                        {"role": "user", "content": query}
                    ],
                    temperature=temperature,
                    max_tokens=config.LLM_MAX_TOKENS,
                    stream=True
                )
                
                # 流式输出每个 token（立即发送，不缓冲）
                full_response = ""
                chunk_count = 0
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            content = delta.content
                            full_response += content
                            chunk_count += 1
                            
                            # 立即发送每个 chunk
                            event = {
                                "type": "content",
                                "content": content,
                                "workflow_id": workflow_id,
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                
                # 发送完成事件
                yield f"data: {json.dumps({'type': 'done', 'workflow_id': workflow_id, 'full_response': full_response}, ensure_ascii=False)}\n\n"
                
                # 保存工作流状态
                workflows[workflow_id] = {
                    "query": query,
                    "session_id": session_id,
                    "status": "completed",
                    "response": full_response,
                    "created_at": datetime.now().isoformat(),
                    "use_tools": use_tools
                }
            
        except Exception as e:
            logger.exception(f"Error in stream chat: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache, no-transform',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'Content-Type': 'text/event-stream; charset=utf-8'
        }
    )


@agent_bp.route('/resume/<workflow_id>', methods=['POST'])
@auth_required
def resume_workflow(workflow_id):
    """恢复工作流"""
    try:
        data = request.get_json() or {}
        user_input = data.get('user_input')
        
        # 检查工作流是否存在
        if workflow_id not in workflows:
            return convert_resp(code=404, status=404, message="工作流不存在")
        
        workflow = workflows[workflow_id]
        
        logger.info(f"Resuming workflow: {workflow_id}, input: {user_input}")
        
        # 更新工作流状态
        workflow['status'] = 'resumed'
        workflow['resumed_at'] = datetime.now().isoformat()
        workflow['user_input'] = user_input
        
        # 生成新的响应 - 使用实际的 LLM 调用
        query = workflow.get('query', '')
        session_id = workflow.get('session_id', '')
        
        # 组合原查询和用户输入
        combined_query = f"{query}\n\n用户补充信息: {user_input}"
        
        # 根据工作流配置决定是否使用工具
        use_tools = workflow.get('use_tools', True)
        
        if use_tools:
            # 使用策略处理
            result = run_async(
                process_query_with_strategy(combined_query, session_id, use_tools)
            )
            if result.get("success"):
                response = result["response"]
            else:
                response = call_llm(combined_query)
        else:
            # 简单 LLM 调用
            response = call_llm(combined_query)
        
        workflow['result'] = response
        workflow['status'] = 'completed'
        
        return convert_resp(data={
            "success": True,
            "workflow_id": workflow_id,
            "session_id": session_id,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.exception(f"Error resuming workflow: {e}")
        return convert_resp(code=500, status=500, message=f"恢复工作流失败: {str(e)}")


@agent_bp.route('/state/<workflow_id>', methods=['GET'])
@auth_required
def get_workflow_state(workflow_id):
    """获取工作流状态"""
    try:
        if workflow_id not in workflows:
            return convert_resp(
                code=404,
                status=404,
                message="工作流不存在",
                data={"success": False}
            )
        
        workflow = workflows[workflow_id]
        
        return convert_resp(
            data={
                "success": True,
                "state": workflow
            }
        )
        
    except Exception as e:
        logger.exception(f"Error getting workflow state: {e}")
        return convert_resp(code=500, status=500, message=f"获取工作流状态失败: {str(e)}")


@agent_bp.route('/cancel/<workflow_id>', methods=['DELETE'])
@auth_required
def cancel_workflow(workflow_id):
    """取消工作流"""
    try:
        if workflow_id not in workflows:
            return convert_resp(
                code=404,
                status=404,
                message="工作流不存在",
                data={"success": False}
            )
        
        # 更新工作流状态
        workflows[workflow_id]['status'] = 'cancelled'
        workflows[workflow_id]['cancelled_at'] = datetime.now().isoformat()
        
        logger.info(f"Cancelled workflow: {workflow_id}")
        
        return convert_resp(
            data={
                "success": True,
                "message": f"工作流 {workflow_id} 已取消"
            }
        )
        
    except Exception as e:
        logger.exception(f"Error cancelling workflow: {e}")
        return convert_resp(code=500, status=500, message=f"取消工作流失败: {str(e)}")


@agent_bp.route('/optimize_prompt', methods=['POST'])
@auth_required
def optimize_prompt_api():
    """
    基于页面上下文优化用户提示词的独立接口
    
    适用场景：在第三方大模型网页（如 ChatGPT、Claude）中，
            系统已通过爬虫获取当前页面数据，调用此接口优化用户输入
    
    请求参数：
    - prompt (必填): 原始提示词
    - url (必填): 当前页面 URL（用于检索已爬取的页面数据）
    
    返回：
    {
        "success": true,
        "optimized_prompt": "优化后的提示词"
    }
    """
    try:
        data = request.get_json()
        
        # 参数验证
        if not data or 'prompt' not in data:
            return convert_resp(code=400, status=400, message="缺少 prompt 参数")
        
        if 'url' not in data:
            return convert_resp(code=400, status=400, message="缺少 url 参数")
        
        prompt = data['prompt'].strip()
        url = data['url'].strip()
        
        # 快速检查：问候语或过短直接返回
        if len(prompt) < 3 or prompt.lower() in ['你好', '在吗', 'hello', 'hi', 'hey']:
            return convert_resp(data={
                "success": True,
                "optimized_prompt": prompt
            })
        
        logger.info(f"Optimizing prompt for URL: {url}, prompt: '{prompt[:50]}...'")
        
        # 执行优化
        result = run_async(optimize_prompt_simple(prompt, url))
        
        return convert_resp(data=result)
        
    except Exception as e:
        logger.exception(f"Error in optimize_prompt_api: {e}")
        return convert_resp(code=500, status=500, message=f"优化失败: {str(e)}")


async def optimize_prompt_simple(prompt: str, url: str) -> Dict[str, Any]:
    """
    简化版提示词优化（基于页面上下文）
    
    Args:
        prompt: 原始提示词
        url: 当前页面 URL（用于检索已爬取的页面内容）
    
    Returns:
        {
            "success": true/false,
            "optimized_prompt": "优化后的提示词",
            "error": "错误信息（仅失败时）"
        }
    """
    try:
        client = get_openai_client()
        if not client:
            return {"success": False, "error": "LLM服务不可用"}
        
        # ========== 步骤 1: 检索页面上下文 ==========
        page_content = ""
        if config.ENABLE_VECTOR_STORAGE:
            try:
                from utils.vectorstore import search_user_context
                
                # 使用 URL 精确检索当前页面数据
                results = search_user_context(
                    query=prompt,
                    context_type="all",
                    limit=3,
                    include_page_content=True,
                    current_page_url=url
                )
                
                # 提取页面内容
                for result in results:
                    if result.get("metadata", {}).get("url") == url:
                        page_content = result.get("content", "")
                        break
                
                logger.info(f"Retrieved page content length: {len(page_content)}")
            except Exception as e:
                logger.warning(f"Failed to retrieve page context: {e}")
        
        # 如果没有页面内容，直接返回原提示词
        if not page_content:
            logger.info("No page content found, returning original prompt")
            return {
                "success": True,
                "optimized_prompt": prompt
            }
        
        # 截断过长内容（保留前2000字符）
        if len(page_content) > 2000:
            page_content = page_content[:2000] + "..."
        
        # ========== 步骤 2: 构建优化提示词 ==========
        # 动态获取当前配置的提示词
        prompts = get_current_prompts()
        base_optimization = prompts.get("prompt_optimization", {})
        
        system_prompt = base_optimization.get("system", "") + """

**针对当前场景的额外要求**:
1. 仅基于提供的页面内容优化提示词
2. 如果提示词与页面内容高度相关，补充具体细节
3. 如果提示词与页面内容关联不强，保持原样
4. 返回的 optimized_query 应该是可以直接使用的提示词

**返回JSON格式**:
{
    "optimized_query": "优化后的提示词",
    "confidence": 0.85
}"""
        
        user_prompt = f"""原始提示词：{prompt}

当前页面内容：
{page_content}

请基于页面内容优化这个提示词。如果提示词与页面内容无关，或页面内容不足以优化，请返回原提示词。"""
        
        # ========== 步骤 3: 调用 LLM 优化 ==========
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        # 解析结果
        result_text = response.choices[0].message.content.strip()
        result_json = json.loads(result_text)
        
        optimized_prompt = result_json.get("optimized_query", prompt)
        confidence = result_json.get("confidence", 0.5)
        
        # 置信度过低，使用原提示词
        if confidence < 0.5:
            optimized_prompt = prompt
        
        logger.info(f"Prompt optimization completed: confidence={confidence}")
        
        return {
            "success": True,
            "optimized_prompt": optimized_prompt
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse optimization result: {e}")
        return {"success": False, "optimized_prompt": prompt, "error": "优化结果解析失败"}
    except Exception as e:
        logger.exception(f"Error in optimize_prompt_simple: {e}")
        return {"success": False, "optimized_prompt": prompt, "error": str(e)}


@agent_bp.route('/test', methods=['GET'])
@auth_required
def test_agent():
    """测试智能代理"""
    try:
        # 执行简单的测试查询
        test_query = "Hello, test the system"
        session_id = str(uuid.uuid4())
        
        # 使用实际的 LLM 调用进行测试
        response = call_llm(test_query)
        
        logger.info("Agent test successful")
        
        return convert_resp(
            data={
                "success": True,
                "message": "智能代理运行正常",
                "test_response": response,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.exception(f"Error testing agent: {e}")
        return convert_resp(
            code=500,
            status=500,
            message=f"测试失败: {str(e)}",
            data={"success": False}
        )

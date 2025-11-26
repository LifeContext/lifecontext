"""
智能对话接口路由
"""
from __future__ import annotations
import asyncio
import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, Response, request, stream_with_context

import config
from routes.llm_strategy import (
    ContextCollection,
    ContextItem,
    ContextSufficiency,
    Intent,
    LlamaIndexContextStrategy,
)
from utils.helpers import auth_required, convert_resp, get_logger
from utils.llm import get_openai_client

_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

logger = get_logger(__name__)

agent_bp = Blueprint("agent", __name__, url_prefix="/api/agent")

# 工作流状态存储（简化实现，实际应该使用数据库或 Redis）
workflows: Dict[str, Dict[str, Any]] = {}

# 全局策略实例（单例模式）
_strategy_instance: Optional[LlamaIndexContextStrategy] = None


def get_strategy() -> LlamaIndexContextStrategy:
    """获取策略实例（单例）"""
    global _strategy_instance
    if _strategy_instance is None:
        _strategy_instance = LlamaIndexContextStrategy()
    return _strategy_instance


def run_async(coro):
    """在 Flask 中运行异步函数"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
    return loop.run_until_complete(coro)


@dataclass
class WorkflowConfig:
    query: str
    session_id: str
    use_tools: bool = True
    max_iterations: int = 2
    stream_final_response: bool = True
    temperature: float = 0.7
    page_context: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowResult:
    success: bool
    response: str
    context: ContextCollection
    iterations: int
    context_summary: List[Dict[str, str]] = field(default_factory=list)
    has_conflict: bool = False
    conflict_details: List[Dict[str, Any]] = field(default_factory=list)

    def to_payload(self) ->  Dict[str, Any]:
        payload: Dict[str, Any] = {
            "success": self.success,
            "response": self.response,
            "context_items_count": len(self.context.items),
            "iterations": self.iterations,
            "context_summary": self.context_summary,
        }
        if self.has_conflict:
            payload["has_schedule_conflict"] = True
            payload["conflict_details"] = self.conflict_details
        return payload


class AgentWorkflow:
    """封装 agent 工具调用与回复生成流程"""

    def __init__(self, config: WorkflowConfig) -> None:
        self.config = config
        self.strategy = get_strategy()
        self.context = ContextCollection()
        self.intent = Intent(query=config.query, type="general")
        self.iteration = 0
        self.analysis_logs: List[str] = []
        self.current_page_url: Optional[str] = None
        self.messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "你是一个智能助手，能够帮助用户解答问题、分析信息和提供建议。"
                    "请主动使用上下文信息回答问题，如果上下文信息不够完整，"
                    "可以基于常识和最佳实践给出合理的建议。用简洁、清晰、直接的方式回答，避免过度保守。"
                ),
            }
        ]

    async def run(self) -> WorkflowResult:
        try:
            await self._ingest_page_context()
            conflict_result = await self._check_schedule_conflict()
            context_summary = self._build_context_summary()
            if conflict_result.get("has_conflict"):
                warning = conflict_result.get(
                    "warning_message", "检测到时间冲突，请检查您的日程安排。"
                )
                return WorkflowResult(
                    success=True,
                    response=warning,
                    context=self.context,
                    iterations=self.iteration,
                    context_summary=context_summary,
                    has_conflict=True,
                    conflict_details=conflict_result.get("conflict_details", []),
                )
            if self.config.use_tools:
                await self._load_session_memory()
                await self._run_tool_iterations()
                await self._store_session_memory()

            final_response = await self._generate_final_response()
            if self.config.use_tools and final_response:
                await store_conversation_to_vectorstore(
                    session_id=self.config.session_id,
                    query=self.config.query,
                    response=final_response,
                    context_items=self.context.items,
                )

            return WorkflowResult(
                success=True,
                response=final_response,
                context=self.context,
                iterations=self.iteration,
                context_summary=context_summary,
            )
        except Exception as exc:
            logger.exception("Agent workflow failed: %s", exc)
            return WorkflowResult(
                success=False,
                response=f"处理失败: {exc}",
                context=self.context,
                iterations=self.iteration,
                context_summary=self._build_context_summary(),
            )

    async def _ingest_page_context(self) -> None:
        page_context = self.config.page_context or {}
        page_url = page_context.get("url")
        page_content = page_context.get("content")

        if not page_url:
            return

        self.current_page_url = page_url.rstrip("/")
        self.strategy.current_page_url = self.current_page_url
        logger.info("Current page URL set: %s, session_id: %s", self.current_page_url, self.config.session_id)

        if not config.ENABLE_VECTOR_STORAGE:
            logger.warning("Vector storage is disabled, skipping page content storage")
            return
            
        if not page_content or not page_content.strip():
            logger.warning("Page content is empty, skipping storage")
            return

        try:
            from utils.db import insert_web_data
            from utils.llm import generate_embeddings
            from utils.vectorstore import add_web_data_to_vectorstore

            web_data_id = insert_web_data(
                title=page_context.get("title", page_url),
                url=page_url,
                content=page_content,
                source="chat_context",
            )
            logger.info(
                "Stored page content to SQLite: web_data_id=%s, url=%s, title=%s",
                web_data_id,
                page_url,
                page_context.get("title", "N/A"),
            )

            success = add_web_data_to_vectorstore(
                web_data_id=web_data_id,
                title=page_context.get("title", page_url),
                url=page_url,
                content=page_content,
                source="chat_context",
                embedding_function=generate_embeddings,
                session_id=self.config.session_id,
            )
            if success:
                logger.info(
                    "Stored current page content to vectorstore: url=%s, session_id=%s, web_data_id=%s",
                    page_url,
                    self.config.session_id,
                    web_data_id
                )
            else:
                logger.warning(
                    "Failed to store page content to vectorstore: url=%s, session_id=%s, web_data_id=%s",
                    page_url,
                    self.config.session_id,
                    web_data_id
                )
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to store page content: %s", exc, exc_info=True)

    async def _load_session_memory(self) -> None:
        logger.info(
            "Retrieving session memory for session: %s", self.config.session_id
        )
        memory_items = await self.strategy.retrieve_session_memory(
            self.config.session_id, self.config.query
        )
        for item in memory_items:
            self.context.add(item)
        if memory_items:
            logger.info(
                "Retrieved %d items from session memory", len(memory_items)
            )

    async def _run_tool_iterations(self) -> None:
        while self.iteration < self.config.max_iterations:
            self.iteration += 1
            logger.info(
                "Processing query iteration %d/%d",
                self.iteration,
                self.config.max_iterations,
            )

            if self.iteration > 1 and self.context.items:
                sufficiency, filtered_context = await self.strategy.evaluate_and_filter_context(  # noqa: E501
                    self.intent, self.context.get_all()
                )
                self.context.items = filtered_context
                logger.info("Context sufficiency: %s", sufficiency)
                if sufficiency == ContextSufficiency.SUFFICIENT:
                    logger.info(
                        "Context is sufficient, proceeding to generate response"
                    )
                    break

            tool_calls = await self._plan_tool_calls()
            if not tool_calls:
                logger.info("No tool calls planned, exiting loop")
                break

            tool_sufficiency, relevant_items = await self._execute_tool_calls(
                tool_calls
            )

            if self.iteration == 1 and relevant_items:
                logger.info(
                    "First iteration retrieved context, continuing to next iteration"
                )
                continue

            if tool_sufficiency == ContextSufficiency.SUFFICIENT:
                logger.info("Tool results are sufficient, stopping iterations")
                break

    async def _plan_tool_calls(self) -> List[Dict[str, Any]]:
        if self.iteration == 1:
            logger.info(
                "First iteration: forcing get_user_profile to retrieve local context"
            )
            analysis_message = (
                "First iteration: retrieving local user context (todos, tips, pages, and session memory)"
            )
            self.analysis_logs.append(analysis_message)
            return [
                {
                    "id": "force_user_profile",
                    "function_name": "get_user_profile",
                    "arguments": {
                        "query": self.config.query,
                        "session_id": self.config.session_id,
                        "context_type": "all",
                        "limit": 10,
                        "current_page_url": self.current_page_url or "",
                    },
                }
            ]

        tool_calls, analysis_msg = await self.strategy.analyze_and_plan_tools(
            self.intent, self.context, self.iteration
        )
        if analysis_msg and analysis_msg.get("content"):
            self.analysis_logs.append(analysis_msg["content"])
            logger.info("Analysis: %s", analysis_msg["content"])
        return tool_calls

    async def _execute_tool_calls(
        self, tool_calls: List[Dict[str, Any]]
    ) -> Tuple[ContextSufficiency, List[ContextItem]]:
        for call in tool_calls:
            if call.get("function_name") == "get_user_profile":
                call.setdefault("arguments", {})
                call["arguments"].setdefault("session_id", self.config.session_id)
                if self.current_page_url:
                    call["arguments"].setdefault(
                        "current_page_url", self.current_page_url
                    )

        tool_results = await self.strategy.execute_tool_calls_parallel(tool_calls)
        sufficiency, relevant_items = await self.strategy.evaluate_and_filter_context(
            self.intent, tool_results
        )
        logger.info(
            "Tool context sufficiency: %s, relevant items: %d",
            sufficiency,
            len(relevant_items),
        )

        for item in relevant_items:
            self.context.add(item)

        if relevant_items:
            await store_iteration_context_to_vectorstore(
                session_id=self.config.session_id,
                iteration=self.iteration,
                query=self.config.query,
                context_items=relevant_items,
            )

        return sufficiency, relevant_items

    async def _store_session_memory(self) -> None:
        if not self.config.use_tools or not self.context.items:
            return
        logger.info(
            "Storing context to session memory for session: %s", self.config.session_id
        )
        await self.strategy.store_to_session_memory(
            self.config.session_id, self.context, self.config.query
        )

    async def _check_schedule_conflict(self) -> Dict[str, Any]:
        if not self.config.use_tools:
            return {"has_conflict": False}
        return await self.strategy.check_schedule_conflict(
            self.context, self.config.query
        )

    async def _generate_final_response(self) -> str:
        client = get_openai_client()
        if not client:
            raise RuntimeError("LLM 服务不可用")
        user_prompt = self._build_user_message()
        messages = self.messages + [{"role": "user", "content": user_prompt}]
        if self.config.stream_final_response:
            stream = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=config.LLM_MAX_TOKENS,
                stream=True,
            )
            final_response = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    final_response += chunk.choices[0].delta.content
            return final_response.strip()

        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=config.LLM_MAX_TOKENS,
            stream=False,
        )
        return response.choices[0].message.content.strip()

    def _build_user_message(self) -> str:
        if not self.context.items:
            return self.config.query

        context_text = "\n\n".join(
            [
                f"[{item.source}] {item.content[:500]}"
                for item in self.context.items[:10]
            ]
        )
        return (
            f"用户问题: {self.config.query}\n\n"
            f"相关上下文信息:\n{context_text}\n\n"
            "请基于以上上下文信息直接回答用户的问题。如果上下文信息不够完整，"
            "可以结合常识和最佳实践给出合理的建议。"
        )

    def _build_context_summary(self, limit: int = 5) -> List[Dict[str, str]]:
        return [
            {
                "source": item.source,
                "content_preview": item.content[:200],
            }
            for item in self.context.items[:limit]
        ]


async def process_query_with_strategy(
    query: str,
    session_id: str,
    use_tools: bool = True,
    max_iterations: int = 2,  # 默认改为2轮迭代
    stream_final_response: bool = True,
    page_context: Optional[Dict[str, Any]] = None,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """使用策略处理查询（智能工具调用和上下文管理）"""
    workflow = AgentWorkflow(
        WorkflowConfig(
            query=query,
            session_id=session_id,
            use_tools=use_tools,
            max_iterations=max_iterations,
            stream_final_response=stream_final_response,
            temperature=temperature,
            page_context=page_context,
        )
    )
    result = await workflow.run()

    if not result.success:
        return {"success": False, "error": result.response}

    return result.to_payload()


async def store_iteration_context_to_vectorstore(
    session_id: str,
    iteration: int,
    query: str,
    context_items: List[ContextItem],
) -> None:
    """将每一轮迭代获取的上下文存储到向量数据库"""
    if not config.ENABLE_VECTOR_STORAGE or not context_items:
        return

    try:
        from utils.vectorstore import add_session_memory_to_vectorstore

        context_texts = []
        for item in context_items:
            source = item.source
            content = item.content
            if source == "user_profile":
                ctx_type = item.metadata.get("context_type", "unknown")
                context_texts.append(f"[{ctx_type}] {content}")
            elif source in {"current_page", "web_page"}:
                context_texts.append(f"[页面内容] {content}")
            elif source == "session_memory":
                context_texts.append(f"[会话记忆] {content}")
            else:
                context_texts.append(f"[{source}] {content}")

        combined_context = "\n\n".join(context_texts)
        memory_content = (
            f"用户查询: {query}\n\n检索到的上下文（第{iteration}轮）:\n{combined_context}"
        )

        success = add_session_memory_to_vectorstore(
            session_id=session_id,
            content=memory_content,
            content_type="iteration_context",
            metadata={
                "iteration": iteration,
                "query": query,
                "context_count": len(context_items),
            },
        )
        if success:
            logger.info(
                "Stored iteration %d context to vectorstore: %d items",
                iteration,
                len(context_items),
            )
    except Exception as exc:  # pragma: no cover
        logger.warning(
            "Failed to store iteration context to vectorstore: %s", exc, exc_info=True
        )


async def store_conversation_to_vectorstore(
    session_id: str,
    query: str,
    response: str,
    context_items: List[ContextItem],
) -> None:
    """将完整的对话（用户查询 + AI 回答）存储到向量数据库"""
    if not config.ENABLE_VECTOR_STORAGE or not query or not response:
        return

    try:
        from utils.db import insert_web_data
        from utils.llm import generate_embeddings
        from utils.vectorstore import (
            add_session_memory_to_vectorstore,
            add_web_data_to_vectorstore,
        )

        conversation_text = f"用户: {query}\n\n助手: {response}"
        if context_items:
            context_summary = "\n\n参考上下文:\n" + "\n".join(
                [
                    f"- [{item.source}] {item.content[:200]}"
                    for item in context_items[:5]
                ]
            )
            conversation_text += context_summary

        success = add_session_memory_to_vectorstore(
            session_id=session_id,
            content=conversation_text,
            content_type="conversation",
            metadata={
                "query": query,
                "response_length": len(response),
                "context_count": len(context_items),
            },
        )
        if success:
            logger.info("Stored conversation to session memory vectorstore")

        web_data_id = insert_web_data(
            title=f"对话记录 - {query[:50]}",
            url="",
            content=conversation_text,
            source="chat_conversation",
            metadata={
                "session_id": session_id,
                "query": query,
                "response_length": len(response),
            },
        )
        if web_data_id:
            add_web_data_to_vectorstore(
                web_data_id=web_data_id,
                title=f"对话记录 - {query[:50]}",
                url="",
                content=conversation_text,
                source="chat_conversation",
                embedding_function=generate_embeddings,
                session_id=session_id,
            )
            logger.info(
                "Stored conversation to web_data vectorstore: web_data_id=%s",
                web_data_id,
            )
    except Exception as exc:  # pragma: no cover
        logger.warning(
            "Failed to store conversation to vectorstore: %s", exc, exc_info=True
        )


def call_llm(query: str, temperature: float = 0.7) -> str:
    """调用大模型生成响应（简单版本，不使用工具）"""
    try:
        client = get_openai_client()
        if not client:
            return "抱歉，LLM 服务暂时不可用，请检查 API Key 配置。"

        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个智能助手，能够帮助用户解答问题、分析信息和提供建议。"
                        "请用简洁、清晰的方式回答。"
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=temperature,
            max_tokens=config.LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.exception("Error calling LLM: %s", exc)
        return f"抱歉，处理您的请求时出现错误：{exc}"


@agent_bp.route("/chat", methods=["POST"])
@auth_required
def chat():
    """智能对话接口（非流式）- 支持工具调用和上下文管理"""
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return convert_resp(code=400, status=400, message="缺少 query 参数")

        query = data["query"]
        session_id = data.get("session_id") or str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())
        temperature = data.get("temperature", 0.7)
        use_tools = data.get("use_tools", True)
        max_iterations = data.get("max_iterations", 2)  # 默认改为2轮迭代
        page_context = data.get("context", {}).get("page")

        if page_context:
            logger.info("Received page context: url=%s", page_context.get("url"))

        logger.info(
            "Processing chat query: %s, session: %s, use_tools: %s",
            query,
            session_id,
            use_tools,
        )

        if use_tools:
            result = run_async(
                process_query_with_strategy(
                    query=query,
                    session_id=session_id,
                    use_tools=use_tools,
                    max_iterations=max_iterations,
                    stream_final_response=True,
                    page_context=page_context,
                    temperature=temperature,
                )
            )
            if not result.get("success"):
                return convert_resp(
                    code=500,
                    status=500,
                    message=result.get("error", "处理失败"),
                )
            llm_response = result["response"]
            context_info = {
                "context_items_count": result.get("context_items_count", 0),
                "iterations": result.get("iterations", 0),
                "context_summary": result.get("context_summary", []),
            }
        else:
            llm_response = call_llm(query, temperature)
            context_info = {}

        response_payload = {
            "success": True,
            "workflow_id": workflow_id,
            "session_id": session_id,
            "query": query,
            "response": llm_response,
            "timestamp": datetime.now().isoformat(),
            "model": config.LLM_MODEL,
            "context_info": context_info,
        }

        workflows[workflow_id] = {
            "query": query,
            "session_id": session_id,
            "status": "completed",
            "result": response_payload,
            "created_at": datetime.now().isoformat(),
            "use_tools": use_tools,
        }

        return convert_resp(data=response_payload)
    except Exception as exc:
        logger.exception("Error in chat: %s", exc)
        return convert_resp(code=500, status=500, message=f"对话失败: {exc}")


@agent_bp.route("/chat/stream", methods=["POST"])
@auth_required
def chat_stream():
    """智能对话接口（流式）- 支持工具调用"""

    def generate():
        try:
            data = request.get_json()
            if not data or "query" not in data:
                yield "data: {}\n\n".format(
                    json.dumps(
                        {"type": "error", "content": "缺少 query 参数"},
                        ensure_ascii=False,
                    )
                )
                return

            query = data["query"]
            session_id = data.get("session_id") or str(uuid.uuid4())
            workflow_id = str(uuid.uuid4())
            temperature = data.get("temperature", 0.7)
            use_tools = data.get("use_tools", True)
            max_iterations = data.get("max_iterations", 2)  # 默认改为2轮迭代
            page_context = data.get("context", {}).get("page")

            if page_context:
                logger.info("Received page context: url=%s", page_context.get("url"))

            logger.info(
                "Processing stream chat query: %s, session: %s, use_tools: %s",
                query,
                session_id,
                use_tools,
            )

            yield "data: {}\n\n".format(
                json.dumps(
                    {
                        "type": "start",
                        "session_id": session_id,
                        "workflow_id": workflow_id,
                        "model": config.LLM_MODEL,
                    },
                    ensure_ascii=False,
                )
            )

            if use_tools:
                strategy_result = run_async(
                    process_query_with_strategy(
                        query=query,
                        session_id=session_id,
                        use_tools=use_tools,
                        max_iterations=max_iterations,
                        stream_final_response=False,
                        page_context=page_context,
                        temperature=temperature,
                    )
                )

                if not strategy_result.get("success"):
                    yield "data: {}\n\n".format(
                        json.dumps(
                            {
                                "type": "error",
                                "content": strategy_result.get("error", "处理失败"),
                            },
                            ensure_ascii=False,
                        )
                    )
                    return

                if strategy_result.get("context_items_count", 0) > 0:
                    yield "data: {}\n\n".format(
                        json.dumps(
                            {
                                "type": "tool_complete",
                                "context_items": strategy_result.get(
                                    "context_items_count", 0
                                ),
                                "iterations": strategy_result.get("iterations", 0),
                            },
                            ensure_ascii=False,
                        )
                    )

                if strategy_result.get("has_schedule_conflict"):
                    warning_message = strategy_result.get(
                        "response", "检测到时间冲突，请检查您的日程安排。"
                    )
                    for char in warning_message:
                        yield "data: {}\n\n".format(
                            json.dumps(
                                {
                                    "type": "content",
                                    "content": char,
                                    "workflow_id": workflow_id,
                                },
                                ensure_ascii=False,
                            )
                        )
                    yield "data: {}\n\n".format(
                        json.dumps(
                            {
                                "type": "done",
                                "workflow_id": workflow_id,
                                "full_response": warning_message,
                            },
                            ensure_ascii=False,
                        )
                    )
                    return

                client = get_openai_client()
                if not client:
                    yield "data: {}\n\n".format(
                        json.dumps(
                            {
                                "type": "error",
                                "content": "LLM 服务不可用",
                            },
                            ensure_ascii=False,
                        )
                    )
                    return

                context_summary = strategy_result.get("context_summary", [])
                if context_summary:
                    context_text = "\n\n".join(
                        [
                            f"[{item.get('source', 'unknown')}] {item.get('content_preview', '')}"
                            for item in context_summary
                        ]
                    )
                    user_message = (
                        f"用户问题: {query}\n\n"
                        f"相关上下文信息:\n{context_text}\n\n"
                        "请基于以上上下文信息直接回答用户的问题。如果上下文信息不够完整，"
                        "可以结合常识和最佳实践给出合理的建议。"
                    )
                else:
                    user_message = query

                messages = [
                    {
                        "role": "system",
                        "content": (
                            "你是一个智能助手，能够帮助用户解答问题、分析信息和提供建议。"
                            "请基于提供的上下文信息，用简洁、清晰的方式回答。"
                        ),
                    },
                    {"role": "user", "content": user_message},
                ]

                logger.info("Starting LLM stream generation")
                stream = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=config.LLM_MAX_TOKENS,
                    stream=True,
                )

                full_response = ""
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        event = {
                            "type": "content",
                            "content": content,
                            "workflow_id": workflow_id,
                            "timestamp": datetime.now().isoformat(),
                        }
                        yield "data: {}\n\n".format(
                            json.dumps(event, ensure_ascii=False)
                        )

                yield "data: {}\n\n".format(
                    json.dumps(
                        {
                            "type": "done",
                            "workflow_id": workflow_id,
                            "full_response": full_response,
                        },
                        ensure_ascii=False,
                    )
                )

                workflows[workflow_id] = {
                    "query": query,
                    "session_id": session_id,
                    "status": "completed",
                    "response": full_response,
                    "created_at": datetime.now().isoformat(),
                    "use_tools": use_tools,
                }
            else:
                client = get_openai_client()
                if not client:
                    yield "data: {}\n\n".format(
                        json.dumps(
                            {
                                "type": "error",
                                "content": "LLM 服务不可用",
                            },
                            ensure_ascii=False,
                        )
                    )
                    return

                stream = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "你是一个智能助手，能够帮助用户解答问题、分析信息和提供建议。"
                                "请用简洁、清晰的方式回答。"
                            ),
                        },
                        {"role": "user", "content": query},
                    ],
                    temperature=temperature,
                    max_tokens=config.LLM_MAX_TOKENS,
                    stream=True,
                )

                full_response = ""
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        event = {
                            "type": "content",
                            "content": content,
                            "workflow_id": workflow_id,
                            "timestamp": datetime.now().isoformat(),
                        }
                        yield "data: {}\n\n".format(
                            json.dumps(event, ensure_ascii=False)
                        )

                yield "data: {}\n\n".format(
                    json.dumps(
                        {
                            "type": "done",
                            "workflow_id": workflow_id,
                            "full_response": full_response,
                        },
                        ensure_ascii=False,
                    )
                )

                workflows[workflow_id] = {
                    "query": query,
                    "session_id": session_id,
                    "status": "completed",
                    "response": full_response,
                    "created_at": datetime.now().isoformat(),
                    "use_tools": use_tools,
                }
        except Exception as exc:
            logger.exception("Error in stream chat: %s", exc)
            yield "data: {}\n\n".format(
                json.dumps({"type": "error", "content": str(exc)}, ensure_ascii=False)
            )

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
    )


@agent_bp.route("/resume/<workflow_id>", methods=["POST"])
@auth_required
def resume_workflow(workflow_id):
    """恢复工作流"""
    try:
        data = request.get_json() or {}
        user_input = data.get("user_input")

        if workflow_id not in workflows:
            return convert_resp(code=404, status=404, message="工作流不存在")

        workflow = workflows[workflow_id]
        workflow["status"] = "resumed"
        workflow["resumed_at"] = datetime.now().isoformat()
        workflow["user_input"] = user_input

        query = workflow.get("query", "")
        session_id = workflow.get("session_id", "")
        combined_query = f"{query}\n\n用户补充信息: {user_input}"
        use_tools = workflow.get("use_tools", True)

        if use_tools:
            result = run_async(
                process_query_with_strategy(
                    query=combined_query,
                    session_id=session_id,
                    use_tools=True,
                )
            )
            response_text = (
                result["response"]
                if result.get("success")
                else call_llm(combined_query)
            )
        else:
            response_text = call_llm(combined_query)

        workflow["result"] = response_text
        workflow["status"] = "completed"

        return convert_resp(
            data={
                "success": True,
                "workflow_id": workflow_id,
                "session_id": session_id,
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as exc:
        logger.exception("Error resuming workflow: %s", exc)
        return convert_resp(code=500, status=500, message=f"恢复工作流失败: {exc}")


@agent_bp.route("/state/<workflow_id>", methods=["GET"])
@auth_required
def get_workflow_state(workflow_id):
    """获取工作流状态"""
    try:
        if workflow_id not in workflows:
            return convert_resp(
                code=404,
                status=404,
                message="工作流不存在",
                data={"success": False},
            )

        return convert_resp(data={"success": True, "state": workflows[workflow_id]})
    except Exception as exc:
        logger.exception("Error getting workflow state: %s", exc)
        return convert_resp(code=500, status=500, message=f"获取工作流状态失败: {exc}")


@agent_bp.route("/cancel/<workflow_id>", methods=["DELETE"])
@auth_required
def cancel_workflow(workflow_id):
    """取消工作流"""
    try:
        if workflow_id not in workflows:
            return convert_resp(
                code=404,
                status=404,
                message="工作流不存在",
                data={"success": False},
            )

        workflows[workflow_id]["status"] = "cancelled"
        workflows[workflow_id]["cancelled_at"] = datetime.now().isoformat()
        logger.info("Cancelled workflow: %s", workflow_id)

        return convert_resp(
            data={"success": True, "message": f"工作流 {workflow_id} 已取消"}
        )
    except Exception as exc:
        logger.exception("Error cancelling workflow: %s", exc)
        return convert_resp(code=500, status=500, message=f"取消工作流失败: {exc}")


@agent_bp.route("/test", methods=["GET"])
@auth_required
def test_agent():
    """测试智能代理"""
    try:
        test_query = "Hello, test the system"
        response_text = call_llm(test_query)
        logger.info("Agent test successful")
        return convert_resp(
            data={
                "success": True,
                "message": "智能代理运行正常",
                "test_response": response_text,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as exc:
        logger.exception("Error testing agent: %s", exc)
        return convert_resp(
            code=500,
            status=500,
            message=f"测试失败: {exc}",
            data={"success": False},
        )
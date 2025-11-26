"""
LLM 策略模块 - 智能上下文管理和工具调用策略
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
_backend_dir = Path(__file__).parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
from utils.helpers import get_logger
from utils.db import get_todos
import config
from tools.base import ToolsExecutor
logger = get_logger(__name__)

@dataclass
class Intent:
    """用户意图"""
    query: str
    type: str = "general"  # general, question, task, search, etc.
    metadata: Dict[str, Any] = None
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
@dataclass
class ContextItem:
    """上下文项"""
    id: str
    content: str
    source: str  # retrieval, entity, web_search, etc.
    metadata: Dict[str, Any] = None
    relevance_score: float = 0.0
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
class ContextCollection:
    """上下文集合"""
    def __init__(self):
        self.items: List[ContextItem] = []
    
    def add(self, item: ContextItem):
        self.items.append(item)
    
    def get_all(self) -> List[ContextItem]:
        return self.items
    
    def get_by_source(self, source: str) -> List[ContextItem]:
        return [item for item in self.items if item.source == source]
    
    def clear(self):
        self.items.clear()
class ContextSufficiency(str, Enum):
    """上下文充分性评估结果"""
    SUFFICIENT = "sufficient"  # 足够回答
    INSUFFICIENT = "insufficient"  # 不够，需要更多工具调用
    UNKNOWN = "unknown"  # 无法确定

# ✅ 核心配置
from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    VectorStoreIndex,
)

# ✅ OpenAI 兼容模型（官方OpenAI 或 OpenAI-like接口）
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.storage import StorageContext
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.storage.index_store import SimpleIndexStore
# ✅ 向量与图存储
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.graph_stores import SimpleGraphStore
# ✅ 评估与后处理
from llama_index.core.evaluation import RelevancyEvaluator
from llama_index.core.postprocessor import SimilarityPostprocessor
class LlamaIndexContextStrategy:
    """
    复用 LLMContextStrategy 的方法签名，但内部换成 LlamaIndex。
    外部（agent.py）仍然通过 analyze_and_plan_tools / evaluate_sufficiency 等接口使用。
    """
    
    def __init__(self):
        # 1. 初始化 LlamaIndex 全局设置
        Settings.llm = OpenAILike(
            model=config.LLM_MODEL,                  # 例如豆包模型
            api_base=config.LLM_BASE_URL,            # OpenAI 兼容地址
            api_key=config.LLM_API_KEY,
            is_chat_model=True,  # 确保使用 chat completions 端点
        )
        Settings.embed_model = OpenAIEmbedding(
            model_name=config.EMBEDDING_MODEL,
            api_base=config.EMBEDDING_BASE_URL,
            api_key=config.EMBEDDING_API_KEY,
            embed_batch_size=32 
        )
        # 2. 准备持久化存储（向量库 / Memory）
        self.storage_context = self._build_storage_context(
            config.CHROMA_PERSIST_DIR
        )
        # 3. 构建全局索引（可按需加载已有文档）
        self.global_index = self._load_global_index()
        # 4. 构建自己的工具类型供模型使用
        self.tools_executor = ToolsExecutor()
        # 从工具执行器获取所有工具定义
        self.all_tools = self.tools_executor.get_function_definitions()
        self.profile_tools = [
            tool.get_function_definition() 
            for tool in self.tools_executor.get_all_tools()
            if tool.get_metadata().get("category") == "profile_tools"
        ]
        self.operation_tools = [
            tool.get_function_definition() 
            for tool in self.tools_executor.get_all_tools()
            if tool.get_metadata().get("category") == "operation_tools"
        ]
        self.context_evaluator = RelevancyEvaluator(llm=Settings.llm)
        self.similarity_filter = SimilarityPostprocessor(
            threshold=0.4,          # 相似度阈值，可按需要调整
            top_k=6,                # 最多保留多少条
        )
        self.session_indices: dict[str, VectorStoreIndex] = {}
        self.session_root = Path(config.CHROMA_PERSIST_DIR)
        self.session_root.mkdir(parents=True, exist_ok=True)
    def _load_global_index(self) -> VectorStoreIndex:
        """从磁盘加载或初始化一个 VectorStoreIndex"""
        try:
            # 尝试从文档创建
            try:
                if config.CHROMA_PERSIST_DIR.exists():
                    docs = SimpleDirectoryReader(config.CHROMA_PERSIST_DIR).load_data()
                    if docs:
                        return VectorStoreIndex.from_documents(
                            docs,
                            storage_context=self.storage_context,
                        )
            except Exception as e:
                logger.debug(f"Failed to load documents: {e}")
            
            # 如果都失败了，创建一个空的索引
            from llama_index.core.schema import Document
            empty_doc = Document(text="", metadata={})
            return VectorStoreIndex.from_documents(
                [empty_doc],
                storage_context=self.storage_context,
            )
        except ValueError as exc:
            message = str(exc)
            if "No existing llama_index.core.vector_stores" in message or "One of nodes, objects, or index_struct must be provided" in message:
                logger.info("No persisted global index found, creating fresh one")
                fresh_context = StorageContext.from_defaults(
                    persist_dir=config.CHROMA_PERSIST_DIR
                )
                # 创建一个空的索引
                from llama_index.core.schema import Document
                empty_doc = Document(text="", metadata={})
                return VectorStoreIndex.from_documents(
                    [empty_doc],
                    storage_context=fresh_context,
                )
            raise

    def _get_context_summary(self, context: ContextCollection) -> str:
        """
        生成上下文摘要，用于工具调用或agent规划
        
        Args:
            context: 上下文集合
            
        Returns:
            上下文摘要字符串
        """
        if not context or not context.items:
            return "无历史上下文。"
        
        try:
            # 简单汇总：按来源分组，显示关键信息
            summary_parts = []
            by_source = {}
            
            for item in context.items:
                source = item.source or "unknown"
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(item)
            
            for source, items in by_source.items():
                summary_parts.append(f"\n[{source}] ({len(items)} 项):")
                for item in items[:3]:  # 只显示前3项
                    content_preview = item.content[:100] + "..." if len(item.content) > 100 else item.content
                    summary_parts.append(f"  - {content_preview}")
                if len(items) > 3:
                    summary_parts.append(f"  ... 还有 {len(items) - 3} 项")
            
            return "\n".join(summary_parts) if summary_parts else "无有效上下文内容。"
        except Exception as e:
            logger.warning(f"Failed to generate context summary: {e}")
            return f"无法生成摘要: {e}"

    async def analyze_and_plan_tools(
        self,
        intent,
        existing_context,
        iteration: int = 1,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        使用 OpenAI function calling 来分析和规划工具调用
        不依赖 LlamaIndex Agent，直接使用 OpenAI API，避免事件循环问题
        """
        try:
            from utils.llm import get_openai_client
            import json
            
            client = get_openai_client()
            if not client:
                raise RuntimeError("LLM 客户端不可用")
            
            # 1. 获取所有可用工具的函数定义
            available_tools = self.tools_executor.get_function_definitions()
            
            # 2. 整理已有上下文
            context_summary = self._get_context_summary(existing_context)
            
            # 3. 构建系统提示词
            system_prompt = (
                "你是一个智能助手，负责分析用户查询并决定需要调用哪些工具来获取信息。\n"
                "根据用户的问题，选择合适的工具来检索相关信息。\n"
                "如果用户的问题涉及时间、计划、待办事项、任务等，应该调用 get_user_profile 工具来检索相关的待办事项。\n"
                "如果用户的问题涉及提示、建议等，应该调用 get_user_profile 工具来检索相关的提示信息。\n"
                "如果用户的问题需要搜索网络信息，应该调用 web_search 工具。\n"
                "只有在确实需要额外信息时才调用工具，如果已有上下文足够回答问题，则不需要调用工具。"
            )
            
            # 4. 构建用户提示词
            user_prompt = f"用户问题: {intent.query}\n\n"
            
            if context_summary:
                user_prompt += f"已有上下文信息:\n{context_summary}\n\n"
            
            user_prompt += (
                f"这是第 {iteration} 轮分析。请根据用户问题，判断是否需要调用工具来获取更多信息。\n"
                "如果需要调用工具，请使用 function calling 功能。"
            )
            
            # 5. 调用 LLM，启用 function calling
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            logger.info(f"Analyzing query for tool planning: {intent.query[:100]}...")
            logger.debug(f"Available tools: {[t['function']['name'] for t in available_tools]}")
            
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                tools=available_tools if available_tools else None,
                tool_choice="auto",  # 让模型自动决定是否调用工具
                temperature=0.3,  # 降低温度以获得更稳定的工具调用决策
            )
            
            # 6. 提取工具调用和响应消息
            tool_calls: List[Dict[str, Any]] = []
            analysis_message = {"content": ""}
            
            message = response.choices[0].message
            
            # 提取文本响应
            if message.content:
                analysis_message["content"] = message.content
            
            # 提取工具调用
            if message.tool_calls:
                for idx, tool_call in enumerate(message.tool_calls):
                    function_name = tool_call.function.name
                    try:
                        # 解析参数
                        arguments = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse tool arguments for {function_name}: {tool_call.function.arguments}")
                        arguments = {}
                    
                    tool_calls.append({
                        "id": tool_call.id or f"call-{idx}",
                        "function_name": function_name,
                        "arguments": arguments,
                    })
                    logger.info(f"Tool call planned: {function_name} with args: {arguments}")
            
            # 7. 如果没有工具调用，记录分析结果
            if not tool_calls:
                analysis_content = analysis_message.get("content", "")
                if not analysis_content:
                    analysis_message["content"] = "分析完成，当前上下文信息足够回答问题，无需调用工具。"
                logger.info("No tool calls planned. Analysis: %s", analysis_message["content"][:200])
            
            logger.info(f"Tool planning completed: {len(tool_calls)} tool calls planned")
            return tool_calls, analysis_message
            
        except Exception as e:
            logger.exception(f"analyze_and_plan_tools error: {e}")
            return [], {"content": f"工具规划失败: {e}"}
    async def execute_tool_calls_parallel(
        self,
        tool_calls: list[dict[str, Any]]
    ) -> list[ContextItem]:
        """
        并发执行工具调用（复用现有 ToolsExecutor）
        tool_calls 结构与之前保持一致：
        [
            {
                "id": "...",
                "function_name": "get_user_profile",
                "arguments": {...}
            },
            ...
        ]
        """
        if not tool_calls:
            return []
        tasks: list[tuple[str, str, asyncio.Task]] = []
        for call in tool_calls:
            fn = call["function_name"]
            args = call.get("arguments", {})
            task = self.tools_executor.run_async(fn, **args)
            tasks.append((fn, call.get("id", ""), asyncio.create_task(task)))
        results = await asyncio.gather(
            *[t for _, _, t in tasks],
            return_exceptions=True
        )
        context_items: list[ContextItem] = []
        for (fn, call_id, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"Tool {fn} failed: {result}")
                continue
            items = self._convert_tool_result_to_context_items(fn, result, call_id)
            context_items.extend(items)
        logger.info(f"Executed {len(tool_calls)} tool calls, got {len(context_items)} context items")
        
        # 输出转换后的 context items 的详细信息
        for idx, item in enumerate(context_items):
            logger.info(
                f"  Converted item {idx+1}: id={item.id}, source={item.source}, "
                f"relevance_score={item.relevance_score:.4f}, "
                f"metadata={item.metadata}, content_preview={item.content[:60]}..."
            )
        
        return context_items

    def _convert_tool_result_to_context_items(
        self,
        tool_name: str,
        result: Any,
        call_id: str,
    ) -> List[ContextItem]:
        """将工具返回结果统一转换为 ContextItem 列表。"""
        if tool_name == "get_user_profile" and isinstance(result, dict):
            context_items: List[ContextItem] = []
            context_search = result.get("context_search", {}) or {}
            for section in ["todos","tasks", "tips", "memories", "pages"]:
                entries = context_search.get(section, []) or []
                for idx, entry in enumerate(entries):
                    if isinstance(entry, dict):
                        raw_metadata = entry.get("metadata") or {}
                        metadata = dict(raw_metadata) if isinstance(raw_metadata, dict) else {}
                        metadata["context_type"] = section
                        content = entry.get("content") or ""
                        relevance = float(entry.get("relevance_score", 0.0))
                    else:
                        metadata = {"context_type": section}
                        content = str(entry)
                        relevance = 0.0

                    context_items.append(
                        ContextItem(
                            id=f"{call_id or tool_name}_{section}_{idx}",
                            content=content,
                            source="user_profile",
                            metadata=metadata,
                            relevance_score=relevance,
                        )
                    )

            # 如果有上下文条目则直接返回
            if context_items:
                return context_items
        items: List[ContextItem] = []
        if isinstance(result, list):
            for idx, entry in enumerate(result):
                if isinstance(entry, dict):
                    items.append(
                        ContextItem(
                            id=f"{call_id or tool_name}_{idx}",
                            content=str(entry.get("content", "")),
                            source=str(entry.get("source", tool_name)),
                            metadata=entry.get("metadata"),
                            relevance_score=float(entry.get("relevance_score", 0.0)),
                        )
                    )
                else:
                    items.append(
                        ContextItem(
                            id=f"{call_id or tool_name}_{idx}",
                            content=str(entry),
                            source=tool_name,
                        )
                    )
            return items
        if isinstance(result, dict):
            items.append(
                ContextItem(
                    id=call_id or f"{tool_name}_0",
                    content=str(result.get("content", result)),
                    source=str(result.get("source", tool_name)),
                    metadata=result.get("metadata"),
                    relevance_score=float(result.get("relevance_score", 0.0)),
                )
            )
            return items
        items.append(
            ContextItem(
                id=call_id or f"{tool_name}_0",
                content=str(result),
                source=tool_name,
            )
        )
        return items
    async def evaluate_and_filter_context(
    self,
    intent,
    context_items: List,
) -> Tuple[ContextSufficiency, List]:
        """
        改进版上下文评估函数：
        - 动态阈值适配问句
        - 支持 LLM 语义补偿
        - 输出详细日志
        """
        import re
        if not context_items:
            return ContextSufficiency.INSUFFICIENT, []

        query = intent.query.strip()
        is_question = query.endswith("?") or "？" in query
        base_threshold = 0.15
        threshold = 0.15 if is_question else base_threshold

        logger.info(f"Evaluating {len(context_items)} context items for query: '{query}' (threshold={threshold:.2f})")

        surviving_items = []
        high_score_count = 0

        for idx, item in enumerate(context_items):
            raw_score = item.relevance_score or 0.0
            item.metadata = item.metadata or {}

            # --- Step 1: 判断是否需要语义补偿 ---
            semantic_boost = 0.0
            if raw_score < threshold:
                # 调用 LLM 检查语义相关性（轻量方式）
                prompt = (
                    f"判断以下两句话是否语义相关。只输出一个0到1之间的数字。\n"
                    f"句子1: {query}\n句子2: {item.content[:200]}"
                )
                try:
                    # 直接使用 OpenAI 客户端，避免 LlamaIndex 的返回格式问题
                    from utils.llm import get_openai_client
                    client = get_openai_client()
                    if client:
                        response = await asyncio.to_thread(
                            client.chat.completions.create,
                            model=config.LLM_MODEL,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.3,
                            max_tokens=50
                        )
                        llm_text = response.choices[0].message.content.strip()
                        match = re.search(r"([0-1](?:\.\d+)?)", llm_text)
                        if match:
                            semantic_score = float(match.group(1))
                            # 动态计算 boost：根据 LLM 的语义相关性分数来调整
                            # semantic_score 越高，boost 越大，但不超过 0.3
                            # 例如：0.6 -> 0.1, 0.7 -> 0.15, 0.8 -> 0.2, 0.9 -> 0.25, 1.0 -> 0.3
                            if semantic_score > 0.6:
                                # 线性映射：0.6 -> 0.1, 1.0 -> 0.3
                                semantic_boost = 0.1 + (semantic_score - 0.6) * 0.5  # (1.0-0.6) * 0.5 = 0.2, 所以 1.0 -> 0.3
                                semantic_boost = min(0.3, semantic_boost)  # 限制最大 boost 为 0.3
                                logger.info(f"🔁 LLM semantic boost applied: semantic_score={semantic_score:.2f}, boost={semantic_boost:.2f} for {item.source}")
                except Exception as e:
                    logger.warning(f"LLM relevance check failed for {item.source}: {e}")

            # --- Step 2: 综合分数 ---
            final_score = min(1.0, raw_score + semantic_boost)
            item.metadata["final_relevance_score"] = final_score

            logger.info(
                f"  Item {idx+1}: source={item.source}, "
                f"raw={raw_score:.4f}, boost={semantic_boost:.2f}, "
                f"final={final_score:.4f}, "
                f"content_preview={item.content[:60]}..."
            )

            # --- Step 3: 过滤逻辑 ---
            if final_score >= threshold:
                surviving_items.append(item)
                if final_score >= 0.6:
                    high_score_count += 1
                logger.info(f"✓ Passed: {item.source}, score={final_score:.4f}")
            else:
                logger.warning(f"✗ Filtered: {item.source}, score={final_score:.4f} < {threshold:.2f}")
        # --- Step 4: 判断充分性 ---
        if not surviving_items:
            suff = ContextSufficiency.INSUFFICIENT
            logger.info(f"Context evaluation: INSUFFICIENT (no items passed filter)")
        else:
            # 获取最高分数
            max_score = max((i.metadata.get("final_relevance_score", 0.0) for i in surviving_items), default=0.0)
            
            # 判断条件：
            # 1. 有 2 个或更多高分项（score >= 0.6）-> SUFFICIENT
            # 2. 或者有 1 个高分项（score >= 0.6）-> SUFFICIENT（降低要求，只要有 1 个高分项就足够）
            # 3. 或者最高分数 >= 0.5 -> SUFFICIENT（进一步降低要求，只要有中等相关度就足够）
            # 4. 否则 -> UNKNOWN
            if high_score_count >= 2:
                suff = ContextSufficiency.SUFFICIENT
                logger.info(f"Context evaluation: SUFFICIENT ({high_score_count} high-score items >= 0.6)")
            elif high_score_count >= 1:
                suff = ContextSufficiency.SUFFICIENT
                logger.info(f"Context evaluation: SUFFICIENT (1 high-score item >= 0.6, max_score={max_score:.4f})")
            elif max_score >= 0.5:
                suff = ContextSufficiency.SUFFICIENT
                logger.info(f"Context evaluation: SUFFICIENT (max_score={max_score:.4f} >= 0.5, {len(surviving_items)} items)")
            else:
                suff = ContextSufficiency.UNKNOWN
                logger.info(f"Context evaluation: UNKNOWN ({len(surviving_items)} surviving items, max_score={max_score:.4f} < 0.5)")
        return suff, surviving_items
    def _create_session_index(self, session_id: str) -> VectorStoreIndex:
        """首次遇到某个会话时创建专属索引（持久化到 session_root/session_id）"""
        persist_dir = self.session_root / session_id
        storage = self._build_storage_context(persist_dir)
        # 创建一个空的索引，后续可以通过 insert_documents 添加文档
        from llama_index.core.schema import Document
        empty_doc = Document(text="", metadata={})
        return VectorStoreIndex.from_documents(
            [empty_doc],
            storage_context=storage,
        )

    def _get_session_index(self, session_id: str) -> VectorStoreIndex:
        index = self.session_indices.get(session_id)
        if index is None:
            index = self._create_session_index(session_id)
            self.session_indices[session_id] = index
        return index
    
    async def store_to_session_memory(
        self,
        session_id: str,
        context: ContextCollection,
        query: str
    ) -> None:
        """
        将本轮 context.items 写入当前会话的向量数据库（ChromaDB），供后续检索使用。
        统一使用 ChromaDB 存储，确保与检索一致。
        """
        if not context.items:
            return
        try:
            from utils.vectorstore import add_session_memory_to_vectorstore
            
            # 将每个 context item 存储到 ChromaDB
            stored_count = 0
            for item in context.items:
                # 构建存储内容
                content = item.content
                
                # 准备元数据
                metadata = {
                    "session_id": session_id,
                    "source": item.source,
                    "relevance_score": item.relevance_score,
                    "query": query,
                    **(item.metadata or {}),
                }
                
                # 确定内容类型
                content_type = item.metadata.get("context_type", "general") if item.metadata else "general"
                
                # 存储到 ChromaDB
                success = add_session_memory_to_vectorstore(
                    session_id=session_id,
                    content=content,
                    content_type=content_type,
                    metadata=metadata
                )
                
                if success:
                    stored_count += 1
                else:
                    logger.warning(f"Failed to store item to session memory: {item.source}, content={content[:50]}...")
            
            logger.info(f"Stored {stored_count}/{len(context.items)} items to session {session_id} memory (ChromaDB)")
        except Exception as e:
            logger.warning(f"Failed to store session memory: {e}", exc_info=True)
            
    async def retrieve_session_memory(
        self,
        session_id: str,
        query: str,
        top_k: int = 6,
    ) -> list[ContextItem]:
        """从当前会话专属索引里检索与 query 相关的记忆"""
        try:
            from functools import partial
            session_index = self._get_session_index(session_id)
            retriever = session_index.as_retriever(similarity_top_k=top_k)
            # LlamaIndex 的 retrieve 是同步调用，放到线程池里跑
            loop = asyncio.get_event_loop()
            nodes = await loop.run_in_executor(
                None,
                partial(retriever.retrieve, query),
            )
            items: list[ContextItem] = []
            for idx, node in enumerate(nodes):
                # node 是 NodeWithScore，需要通过 node.node 访问实际节点
                node_content = node.node.get_content() if hasattr(node.node, 'get_content') else node.node.text
                node_metadata = node.node.metadata if hasattr(node.node, 'metadata') else {}
                items.append(
                    ContextItem(
                        id=f"{session_id}_memory_{idx}",
                        content=node_content,
                        source=node_metadata.get("source", "session_memory"),
                        metadata={
                            **node_metadata,
                            "similarity": node.score,
                            "query": query,
                        },
                        relevance_score=node.score or 0.8,
                    )
                )
            return items
        except Exception as e:
            logger.warning(f"retrieve_session_memory failed for {session_id}: {e}", exc_info=True)
            return []

    async def check_schedule_conflict(
        self,
        context: ContextCollection,
        user_query: str,
    ) -> Dict[str, Any]:
        """
        检查用户查询与待办事项之间是否存在时间冲突。
        返回结构:
        {
            "has_conflict": bool,
            "warning_message": str,
            "conflict_details": List[Dict[str, Any]]
        }
        """
        try:
            time_keywords = [
                "明天",
                "后天",
                "今天",
                "下周一",
                "下周二",
                "下周三",
                "下周四",
                "下周五",
                "下周",
                "下个月",
                "周末",
                "计划",
                "出行",
                "去",
                "玩",
                "旅行",
                "活动",
                "安排",
                "时间",
                "几点",
                "什么时候",
                "何时",
                "日期",
                "行程",
            ]
            query_lower = user_query.lower()
            if not any(keyword in query_lower for keyword in time_keywords):
                return {"has_conflict": False}

            task_items = [
                item
                for item in context.items
                if item.source == "user_profile"
                and item.metadata.get("context_type") == "task"
            ]
            if not task_items:
                return {"has_conflict": False}

            todo_ids = [
                int(todo_id)
                for item in task_items
                for todo_id in [item.metadata.get("todo_id")]
                if todo_id
            ]
            if not todo_ids:
                return {"has_conflict": False}

            all_todos = get_todos(limit=100)
            relevant_todos = []
            for todo in all_todos:
                if todo.get("id") in todo_ids:
                    relevant_todos.append(
                        {
                            "id": todo.get("id"),
                            "title": todo.get("title", ""),
                            "description": todo.get("description", ""),
                            "status": todo.get("status", 0),
                        }
                    )
            if not relevant_todos:
                return {"has_conflict": False}
            result = await self.tools_executor.run_async(
                "schedule_conflict_check",
                user_query=user_query,
                todos=[
                    {
                        "title": todo.get("title", ""),
                        "description": todo.get("description", ""),
                    }
                    for todo in relevant_todos
                ],
            )

            if isinstance(result, dict):
                return result

        except Exception as e:
            logger.exception(f"Error checking schedule conflict: {e}")

        return {"has_conflict": False}

    # ------------------------------------------------------------------
    # 辅助方法

    def _build_storage_context(self, persist_dir: Path | str) -> StorageContext:
        """构建 StorageContext，若持久化数据缺失则自动引导创建。"""
        target = Path(persist_dir)
        target.mkdir(parents=True, exist_ok=True)
        try:
            return StorageContext.from_defaults(persist_dir=str(target))
        except (ValueError, FileNotFoundError) as exc:
            message = str(exc)
            if (
                "No existing llama_index.core.vector_stores.simple" not in message
                and "docstore.json" not in message
            ):
                raise

            logger.info(
                "Persisted storage not found at %s, initializing fresh store",
                target,
            )

            fresh_context = StorageContext.from_defaults(
                docstore=SimpleDocumentStore(),
                index_store=SimpleIndexStore(),
                vector_store=SimpleVectorStore(),
                graph_store=SimpleGraphStore(),
            )
            fresh_context.persist(persist_dir=str(target))
            return StorageContext.from_defaults(persist_dir=str(target))
        
        


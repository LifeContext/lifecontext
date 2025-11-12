"""
LLM 策略模块 - 智能上下文管理和工具调用策略
"""
import json
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
from utils.llm import get_openai_client
from utils.helpers import get_logger
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



# ============================================================================
# LLMContextStrategy 主类
# ============================================================================

class LLMContextStrategy:
    def __init__(self):
        self.tools_executor = ToolsExecutor()
        # 从工具执行器获取所有工具定义
        self.all_tools = self.tools_executor.get_function_definitions()
        
        # 按类别分类工具（可选）
        # 删除 retrieval_tools 分类
        # self.retrieval_tools = [
        #     tool.get_function_definition() 
        #     for tool in self.tools_executor.get_all_tools()
        #     if tool.get_metadata().get("category") == "retrieval_tools"
        # ]
        
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
    
    def _get_context_summary(self, context: ContextCollection) -> str:
        """构建上下文摘要"""
        if not context.items:
            return "暂无上下文信息。"
        
        summary_parts = []
        for item in context.items[:10]:  # 最多10个项
            summary_parts.append(f"- [{item.source}] {item.content[:200]}...")
        
        return "\n".join(summary_parts)
    
    def _get_detailed_context_summary(self, contexts: ContextCollection) -> str:
        """构建详细上下文摘要（用于充分性评估）"""
        summary = f"当前上下文包含 {len(contexts.items)} 个上下文项：\n\n"
        
        for i, item in enumerate(contexts.items, 1):
            summary += f"{i}. [来源: {item.source}] (相关性: {item.relevance_score:.2f})\n"
            summary += f"   内容: {item.content[:300]}...\n\n"
        
        return summary
    
    async def analyze_and_plan_tools(
        self,
        intent: Intent,
        existing_context: ContextCollection,
        iteration: int = 1
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        核心功能：分析用户意图，决定需要调用哪些工具
        """
        try:
            client = get_openai_client()
            if not client:
                logger.error("OpenAI client not available")
                return [], {"error": "LLM服务不可用"}
            
            # 1. 构建上下文摘要
            context_summary = self._get_context_summary(existing_context)
            
            # 调试：打印可用工具和上下文
            logger.info(f"Available tools count: {len(self.all_tools)}")
            logger.info(f"Tool names: {[tool.get('function', {}).get('name', 'unknown') for tool in self.all_tools]}")
            logger.info(f"Existing context items: {len(existing_context.items)}")
            logger.info(f"Context summary: {context_summary[:200]}...")
            
            # 2. 构建系统提示词
            system_prompt = """你是一个智能上下文分析助手。你的任务是分析用户意图，决定需要调用哪些工具来获取更多上下文信息。

**重要规则**：
1. 如果用户明确询问邮件/邮箱/email相关问题，必须调用 email_reader 工具
2. 即使已有一些本地上下文（如todos、tips），也要调用相应的专门工具来获取最新的邮件/日历/文档信息

请根据用户意图和已有上下文，决定需要调用哪些工具。可用工具将通过 Function Calling 提供给你。"""
            
            # 3. 构建用户提示词
            user_prompt = f"""用户查询: {intent.query}

已有上下文:
{context_summary}

当前迭代: {iteration}

请分析这个查询，决定需要调用哪些工具来获取更多信息。"""
            
            # 4. 调用 LLM (Function Calling)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 调试：如果没有工具，记录警告
            if not self.all_tools:
                logger.warning("No tools available for LLM to call!")
            
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                tools=self.all_tools if self.all_tools else None,  # 如果没有工具，传 None
                tool_choice="auto",
                temperature=0.3,
                max_tokens=config.LLM_MAX_TOKENS
            )
            
            # 5. 提取工具调用
            tool_calls = []
            analysis_message = {"content": ""}
            
            message = response.choices[0].message
            
            if message.content:
                analysis_message["content"] = message.content
                logger.debug(f"LLM analysis message: {message.content}")
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                        tool_calls.append({
                            "id": tool_call.id,
                            "function_name": function_name,
                            "arguments": function_args
                        })
                        logger.info(f"Tool call planned: {function_name} with args: {function_args}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse tool call arguments: {e}")
            else:
                logger.info("LLM decided not to call any tools")
                if message.content:
                    logger.info(f"LLM reasoning: {message.content}")
            
            logger.info(f"Planned {len(tool_calls)} tool calls for iteration {iteration}")
            return tool_calls, analysis_message
            
        except Exception as e:
            logger.exception(f"Error in analyze_and_plan_tools: {e}")
            return [], {"error": str(e)}
    
    async def evaluate_sufficiency(
        self, 
        contexts: ContextCollection, 
        intent: Intent
    ) -> ContextSufficiency:
        """
        核心功能：评估已有上下文是否足够回答问题
        
        特别处理：如果用户明确询问需要外部数据源的问题（邮件/日程/文档），
        直接返回 INSUFFICIENT，强制调用对应的工具。
        """
        try:
            # 【关键修复】检查是否明确需要调用特定工具
            query_lower = intent.query.lower()
            
            # 定义需要强制调用工具的关键词
            email_keywords = ['邮件', '邮箱', '收件箱', 'email', 'mail', 'inbox', '未读邮件', '新邮件']
            
            # 如果包含这些关键词，强制返回 INSUFFICIENT，让系统调用工具
            if any(kw in query_lower for kw in email_keywords):
                logger.info(f"检测到邮件相关关键词，强制返回 INSUFFICIENT 以调用 email_reader")
                return ContextSufficiency.INSUFFICIENT
            
            # 如果没有特殊关键词，按正常流程评估
            client = get_openai_client()
            if not client:
                logger.warning("LLM unavailable, defaulting to INSUFFICIENT")
                return ContextSufficiency.UNKNOWN
            
            # 1. 构建详细上下文摘要
            context_summary = self._get_detailed_context_summary(contexts)
            
            # 2. 构建评估提示词
            system_prompt = """你是一个上下文充分性评估专家。评估已有上下文是否足够回答用户的问题。

请返回以下三种结果之一：
- SUFFICIENT: 如果已有上下文足够回答问题
- INSUFFICIENT: 如果还需要更多信息
- UNKNOWN: 如果无法确定

只返回结果单词，不要其他解释。"""
            
            user_prompt = f"""用户查询: {intent.query}

已有上下文:
{context_summary}

评估结果:"""
            
            # 3. 调用 LLM
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            # 4. 解析结果
            result_text = response.choices[0].message.content.strip().upper()
            
            if "SUFFICIENT" in result_text:
                return ContextSufficiency.SUFFICIENT
            elif "INSUFFICIENT" in result_text:
                return ContextSufficiency.INSUFFICIENT
            else:
                return ContextSufficiency.UNKNOWN
                
        except Exception as e:
            logger.exception(f"Error in evaluate_sufficiency: {e}")
            return ContextSufficiency.UNKNOWN
    
    async def execute_tool_calls_parallel(
        self, 
        tool_calls: List[Dict[str, Any]]
    ) -> List[ContextItem]:
        """
        核心功能：并发执行工具调用，并转换为 ContextItem
        """
        if not tool_calls:
            return []
        
        try:
            # 1. 创建异步任务列表
            tasks = []
            for call in tool_calls:
                function_name = call["function_name"]
                function_args = call.get("arguments", {})
                
                task = self.tools_executor.run_async(
                    function_name,
                    **function_args
                )
                tasks.append((function_name, call.get("id", ""), task))
            
            # 2. 并发执行
            results = await asyncio.gather(
                *[task for _, _, task in tasks],
                return_exceptions=True
            )
            
            # 3. 处理结果并转换
            all_items = []
            for (function_name, call_id, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"Tool {function_name} failed: {result}")
                    continue
                
                context_items = self._convert_tool_result_to_context_items(
                    function_name,
                    result,
                    call_id
                )
                all_items.extend(context_items)
            
            logger.info(f"Executed {len(tool_calls)} tool calls, got {len(all_items)} context items")
            return all_items
            
        except Exception as e:
            logger.exception(f"Error in execute_tool_calls_parallel: {e}")
            return []
    
    def _convert_tool_result_to_context_items(
        self,
        function_name: str,
        result: Any,
        call_id: str = ""
    ) -> List[ContextItem]:
        """将工具结果转换为 ContextItem"""
        items = []
        
        if function_name == "web_search":
            # web_search 返回的是字典格式，包含 results 字段
            if isinstance(result, dict):
                # 检查是否成功
                if result.get("success", False):
                    search_results = result.get("results", [])
                    engine = result.get("engine", "unknown")
                    query = result.get("query", "")
                    
                    # 转换每个搜索结果
                    for i, search_item in enumerate(search_results):
                        title = search_item.get("title", "")
                        url = search_item.get("url", "")
                        snippet = search_item.get("snippet", "")
                        
                        # 构建内容摘要
                        content_text = f"标题: {title}\nURL: {url}\n摘要: {snippet}"
                        
                        context_item = ContextItem(
                            id=f"{call_id}_search_{i}",
                            content=content_text,
                            source="web_search",
                            metadata={
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "engine": engine,
                                "query": query
                            },
                            relevance_score=0.9  # 网络搜索结果相关性较高
                        )
                        items.append(context_item)
                else:
                    # 搜索失败，记录错误但不添加上下文项
                    error_msg = result.get("error", "Unknown error")
                    logger.warning(f"Web search failed: {error_msg}")
            elif isinstance(result, list):
                # 兼容旧格式：如果直接返回列表（异常情况）
                logger.warning("Web search returned list format, converting...")
                for i, search_item in enumerate(result):
                    if isinstance(search_item, dict):
                        title = search_item.get("title", "")
                        url = search_item.get("url", "")
                        snippet = search_item.get("snippet", "")
                        
                        content_text = f"标题: {title}\nURL: {url}\n摘要: {snippet}"
                        
                        context_item = ContextItem(
                            id=f"{call_id}_search_{i}",
                            content=content_text,
                            source="web_search",
                            metadata={
                                "title": title,
                                "url": url,
                                "snippet": snippet
                            },
                            relevance_score=0.9
                        )
                        items.append(context_item)
        
        elif function_name == "get_user_profile":
            # 用户待办事项、提示信息和会话记忆
            if isinstance(result, dict):
                # 检查是否有 context_search 字段
                if "context_search" in result:
                    context_search = result["context_search"]
                    # 从 context_search 中提取 tasks、tips、memories 和 pages
                    tasks = context_search.get("tasks", [])
                    tips = context_search.get("tips", [])
                    memories = context_search.get("memories", [])
                    pages = context_search.get("pages", [])  # 新增：提取pages
                    
                    # 处理 tasks
                    for i, task in enumerate(tasks):
                        context_item = ContextItem(
                            id=f"{call_id}_task_{i}",
                            content=task.get("content", ""),
                            source="user_profile",
                            metadata={
                                **task.get("metadata", {}),
                                "context_type": "task"
                            },
                            relevance_score=task.get("relevance_score", 0.8)
                        )
                        items.append(context_item)
                    
                    # 处理 tips
                    for i, tip in enumerate(tips):
                        context_item = ContextItem(
                            id=f"{call_id}_tip_{i}",
                            content=tip.get("content", ""),
                            source="user_profile",
                            metadata={
                                **tip.get("metadata", {}),
                                "context_type": "tip"
                            },
                            relevance_score=tip.get("relevance_score", 0.8)
                        )
                        items.append(context_item)
                    
                    # 处理 memories（会话记忆）
                    for i, memory in enumerate(memories):
                        context_item = ContextItem(
                            id=f"{call_id}_memory_{i}",
                            content=memory.get("content", ""),
                            source="session_memory",
                            metadata={
                                **memory.get("metadata", {}),
                                "context_type": memory.get("content_type", "general"),
                                "timestamp": memory.get("timestamp", "")
                            },
                            relevance_score=memory.get("relevance_score", 0.9)
                        )
                        items.append(context_item)
                    
                    # 处理 pages（页面内容）（新增）
                    for i, page in enumerate(pages):
                        metadata = page.get("metadata", {})
                        url = metadata.get("url", "")
                        source = metadata.get("source", "web_page")
                        
                        # 根据source确定最终的source标识
                        if source == "chat_context":
                            final_source = "current_page"
                        elif source in ["web_crawler", "web-crawler-initial"]:
                            final_source = "web_page"
                        else:
                            final_source = "page"
                        
                        context_item = ContextItem(
                            id=f"{call_id}_page_{i}",
                            content=page.get("content", ""),
                            source=final_source,  # 使用确定的source
                            metadata={
                                **metadata,
                                "context_type": "page",
                                "url": url
                            },
                            relevance_score=page.get("relevance_score", 0.9)
                        )
                        items.append(context_item)
                    
                    logger.info(f"Extracted {len(tasks)} tasks, {len(tips)} tips, {len(memories)} memories, and {len(pages)} pages from context_search")
                else:
                    # 如果没有 context_search，尝试从顶层获取（兼容旧格式）
                    tasks = result.get("tasks", [])
                    tips = result.get("tips", [])
                    
                    if tasks or tips:
                        logger.warning("Found tasks/tips at top level, but expected in context_search")
                        # 处理逻辑同上
                        for i, task in enumerate(tasks):
                            context_item = ContextItem(
                                id=f"{call_id}_task_{i}",
                                content=task.get("content", ""),
                                source="user_profile",
                                metadata={
                                    **task.get("metadata", {}),
                                    "context_type": "task"
                                },
                                relevance_score=task.get("relevance_score", 0.8)
                            )
                            items.append(context_item)
                        
                        for i, tip in enumerate(tips):
                            context_item = ContextItem(
                                id=f"{call_id}_tip_{i}",
                                content=tip.get("content", ""),
                                source="user_profile",
                                metadata={
                                    **tip.get("metadata", {}),
                                    "context_type": "tip"
                                },
                                relevance_score=tip.get("relevance_score", 0.8)
                            )
                            items.append(context_item)
        
        # 处理 email_reader 工具结果
        elif function_name == "email_reader":
            if result.get("status") == "success":
                emails = result.get("emails", [])
                for i, email in enumerate(emails):
                    email_content = f"""邮件主题: {email.get('subject', '无主题')}
发件人: {email.get('from', '未知')}
收件人: {email.get('to', '未知')}
日期: {email.get('date', '未知')}
摘要: {email.get('snippet', '无内容')}
{'🔴 未读' if email.get('is_unread') else ''}"""
                    
                    context_item = ContextItem(
                        id=f"{call_id}_email_{i}",
                        content=email_content,
                        source="email",
                        metadata={
                            "email_id": email.get("id", ""),
                            "subject": email.get("subject", ""),
                            "from": email.get("from", ""),
                            "date": email.get("date", ""),
                            "is_unread": email.get("is_unread", False),
                            "context_type": "email"
                        },
                        relevance_score=1.0 if email.get("is_unread") else 0.8
                    )
                    items.append(context_item)
                logger.info(f"Converted {len(emails)} emails from email_reader")
            else:
                # 如果获取邮件失败，也要告诉 LLM
                error_content = f"邮箱状态: {result.get('status', 'unknown')}\n"
                error_content += f"信息: {result.get('message', '')}\n"
                if result.get('authorization_url'):
                    error_content += f"授权链接: {result.get('authorization_url')}"
                
                context_item = ContextItem(
                    id=f"{call_id}_email_status",
                    content=error_content,
                    source="email_status",
                    metadata={"status": result.get("status"), "context_type": "email_error"},
                    relevance_score=1.0
                )
                items.append(context_item)

        else:
            logger.warning(f"No conversion logic for tool: {function_name}")
            logger.warning(f"Tool result: {result}")
        logger.error(f"tool result: {result}")
        logger.error(f"items {items}")
        return items
    
    async def validate_and_filter_tool_results(
        self,
        tool_calls: List[Dict[str, Any]],
        tool_results: List[ContextItem],
        intent: Intent,
        existing_context: ContextCollection,
    ) -> Tuple[List[ContextItem], Dict[str, str]]:
        """
        核心功能：使用 LLM 验证工具结果的相关性，过滤低相关性项
        """
        if not tool_results:
            return [], {"message": "没有工具结果需要验证"}
        
        # 临时调试：如果结果数量很少（<=5），直接返回所有结果
        if len(tool_results) <= 5:
            logger.info(f"Tool results count ({len(tool_results)}) is small, skipping validation")
            return tool_results, {"message": "结果数量较少，跳过验证"}
        
        try:
            client = get_openai_client()
            if not client:
                logger.warning("LLM unavailable, returning all results")
                return tool_results, {"message": "验证服务不可用，返回所有结果"}
            
            # 1. 构建结果摘要
            results_summary = []
            for item in tool_results:
                results_summary.append({
                    "result_id": item.id,
                    "content": item.content[:500],  # 限制长度
                    "source": item.source,
                    "relevance_score": item.relevance_score
                })
            
            # 2. 构建验证提示词
            system_prompt = """你是一个上下文相关性验证专家。评估工具结果与用户查询的相关性。

请返回一个JSON对象，包含以下字段：
- relevant_result_ids: 相关结果ID列表
- validation_message: 验证说明

只返回JSON，不要其他文字。"""
            
            user_prompt = f"""用户查询: {intent.query}

工具结果列表:
{json.dumps(results_summary, ensure_ascii=False, indent=2)}

请评估每个结果的相关性，返回相关结果ID列表。"""
            
            # 3. 调用 LLM 验证
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # 4. 解析验证结果
            validation_json = json.loads(response.choices[0].message.content)
            relevant_ids = set(validation_json.get("relevant_result_ids", []))
            validation_message = validation_json.get("validation_message", "")
            
            # 5. 过滤相关项
            relevant_items = [
                item for item in tool_results 
                if item.id in relevant_ids
            ]
            
            # 6. 容错处理（如果验证失败，返回所有结果）
            if not relevant_ids:
                logger.warning("Validation returned no relevant IDs, returning all results")
                return tool_results, {"message": "验证未识别到相关结果，返回所有结果"}
            
            logger.info(f"Validated {len(tool_results)} results, kept {len(relevant_items)} relevant items")
            return relevant_items, validation_message
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse validation JSON: {e}")
            return tool_results, {"message": "验证结果解析失败，返回所有结果"}
        except Exception as e:
            logger.exception(f"Error in validate_and_filter_tool_results: {e}")
            return tool_results, {"message": f"验证过程出错: {str(e)}"}

    async def retrieve_session_memory(
        self,
        session_id: str,
        query: str
    ) -> List[ContextItem]:
        """
        从会话记忆检索相关上下文信息
        
        Args:
            session_id: 会话ID
            query: 用户查询，用于检索相关记忆
        
        Returns:
            检索到的上下文项列表
        """
        try:
            memory_tool = self.tools_executor.get_tool("session_memory")
            if not memory_tool:
                logger.debug("Session memory tool not available")
                return []
            
            # 检索会话记忆
            result = memory_tool.execute(
                action="retrieve",
                session_id=session_id,
                query=query,
                limit=10
            )
            
            if not result.get("success", False):
                return []
            
            # 转换为 ContextItem
            items = []
            memory_items = result.get("items", [])
            
            for i, memory_item in enumerate(memory_items):
                content = memory_item.get("content", "")
                content_type = memory_item.get("type", "general")
                
                context_item = ContextItem(
                    id=f"session_memory_{session_id}_{i}",
                    content=content,
                    source="session_memory",
                    metadata={
                        "content_type": content_type,
                        "timestamp": memory_item.get("timestamp", ""),
                        **memory_item.get("metadata", {})
                    },
                    relevance_score=0.95  # 会话记忆相关性很高
                )
                items.append(context_item)
            
            logger.info(f"Retrieved {len(items)} items from session memory")
            return items
            
        except Exception as e:
            logger.exception(f"Error retrieving session memory: {e}")
            return []

    async def store_to_session_memory(
        self,
        session_id: str,
        context: ContextCollection,
        query: str
    ):
        """
        将上下文中的关键信息存储到会话记忆
        
        Args:
            session_id: 会话ID
            context: 上下文集合
            query: 用户查询
        """
        try:
            memory_tool = self.tools_executor.get_tool("session_memory")
            if not memory_tool:
                logger.debug("Session memory tool not available")
                return
            
            # 从上下文中提取关键信息
            # 优先提取用户待办事项中的信息
            user_profile_items = [
                item for item in context.items
                if item.source == "user_profile" and item.metadata.get("context_type") == "task"
            ]
            
            stored_count = 0
            for item in user_profile_items:
                content = item.content.strip()
                if content and len(content) > 0:
                    # 存储到会话记忆
                    result = memory_tool.execute(
                        action="store",
                        session_id=session_id,
                        content=content,
                        content_type="task"
                    )
                    if result.get("success", False):
                        stored_count += 1
            
            if stored_count > 0:
                logger.info(f"Stored {stored_count} items to session memory")
            
        except Exception as e:
            logger.exception(f"Error storing to session memory: {e}")
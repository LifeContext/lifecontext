"""
会话记忆工具 - 通用的上下文记忆管理（使用向量数据库）
"""
from typing import Dict, Any, List, Optional
from tools.base import BaseTool
from utils.helpers import get_logger
from utils.vectorstore import add_session_memory_to_vectorstore, search_session_memory
from datetime import datetime

logger = get_logger(__name__)


class SessionMemoryTool(BaseTool):
    """会话记忆工具 - 通用的上下文记忆管理（向量数据库持久化）"""
    
    def __init__(self):
        super().__init__(
            name="session_memory",
            description="存储和检索当前会话中的关键上下文信息。这是一个通用的记忆工具，可以存储任何类型的上下文信息（如用户提到的计划、任务、物品、地点、时间等），并在后续查询中检索这些信息。当用户的查询是之前对话的延续（如'推荐品牌'、'给几个选择'、'给出出行计划'等）时，应该先使用此工具检索相关的上下文信息。数据会持久化存储到向量数据库中，支持语义搜索，即使服务重启也能保留。",
            is_async=False
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "操作类型：store（存储信息）或 retrieve（检索信息）",
                    "enum": ["store", "retrieve"],
                    "default": "retrieve"
                },
                "session_id": {
                    "type": "string",
                    "description": "会话ID，用于区分不同的会话"
                },
                "content": {
                    "type": "string",
                    "description": "要存储的信息内容（仅在action为store时使用）"
                },
                "content_type": {
                    "type": "string",
                    "description": "内容类型（可选），如 'task'、'product'、'plan'、'location'、'time' 等，用于分类存储",
                    "default": "general"
                },
                "query": {
                    "type": "string",
                    "description": "检索查询文本（仅在action为retrieve时使用），用于搜索相关的记忆内容。应该使用用户查询中的关键词或相关概念。"
                },
                "limit": {
                    "type": "integer",
                    "description": "检索结果数量限制（仅在action为retrieve时使用）",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["action", "session_id"]
        }
    
    def execute(
        self,
        action: str,
        session_id: str,
        content: Optional[str] = None,
        content_type: str = "general",
        query: Optional[str] = None,
        limit: int = 10,
        **kwargs
    ) -> Any:
        """
        执行会话记忆操作
        
        Args:
            action: 操作类型（store 或 retrieve）
            session_id: 会话ID
            content: 要存储的信息内容
            content_type: 内容类型
            query: 检索查询文本
            limit: 检索结果数量限制
        
        Returns:
            操作结果
        """
        try:
            if action == "store":
                return self._store_memory(session_id, content, content_type)
            elif action == "retrieve":
                return self._retrieve_memory(session_id, query, limit)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            logger.exception(f"Error in session_memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _store_memory(self, session_id: str, content: str, content_type: str) -> Dict[str, Any]:
        """存储信息到向量数据库"""
        if not content or not content.strip():
            return {
                "success": False,
                "error": "Content cannot be empty"
            }
        
        success = add_session_memory_to_vectorstore(
            session_id=session_id,
            content=content.strip(),
            content_type=content_type,
            metadata={
                "timestamp": datetime.now().isoformat()
            }
        )
        
        if success:
            logger.info(f"Stored session memory to vectorstore: session_id={session_id}, content_type={content_type}, content={content[:50]}...")
            return {
                "success": True,
                "message": f"已存储信息到向量数据库",
                "session_id": session_id,
                "stored_content": content[:100],
                "content_type": content_type
            }
        else:
            return {
                "success": False,
                "error": "存储到向量数据库失败",
                "session_id": session_id
            }
    
    def _retrieve_memory(self, session_id: str, query: Optional[str], limit: int) -> Dict[str, Any]:
        """从向量数据库检索信息（语义搜索）"""
        # 如果没有查询，使用空查询（会返回最近的记录）
        search_query = query if query and query.strip() else ""
        
        memory_items = search_session_memory(
            session_id=session_id,
            query=search_query,
            limit=limit
        )
        
        if not memory_items:
            return {
                "success": True,
                "items": [],
                "count": 0,
                "message": "该会话暂无记忆"
            }
        
        # 转换为工具返回格式
        formatted_items = []
        for item in memory_items:
            formatted_items.append({
                "content": item.get("content", ""),
                "type": item.get("context_type", "general"),
                "timestamp": item.get("timestamp", ""),
                "metadata": item.get("metadata", {}),
                "relevance_score": 1.0 - min(item.get("distance", 1.0), 1.0)  # 距离越小，相关性越高
            })
        
        logger.info(f"Retrieved {len(formatted_items)} memory items from vectorstore for session {session_id}")
        
        return {
            "success": True,
            "items": formatted_items,
            "count": len(formatted_items),
            "query": query,
            "session_id": session_id
        }
    
    @staticmethod
    def get_session_memory(session_id: str) -> List[Dict[str, Any]]:
        """获取会话的所有记忆（用于内部使用）"""
        # This function is no longer needed as memory is stored in vectorstore
        # and can be retrieved via search_session_memory.
        # Keeping it for now, but it will return an empty list.
        return []
    
    @staticmethod
    def clear_session_memory(session_id: str) -> bool:
        """清除会话记忆（用于测试或清理）"""
        # This function is no longer needed as memory is stored in vectorstore
        # and can be cleared via vectorstore.clear_collection().
        # Keeping it for now, but it will return False.
        return False


def get_operation_tools() -> List[BaseTool]:
    """获取所有操作工具实例"""
    from tools.operation_tools.web_search_tool import WebSearchTool
    return [
        WebSearchTool(),
        SessionMemoryTool(),  # 添加会话记忆工具
    ]

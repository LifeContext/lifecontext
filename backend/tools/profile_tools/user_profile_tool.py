"""
用户配置工具
支持检索用户实体、兴趣、偏好等上下文信息
"""

from typing import Dict, Any, List, Optional
from tools.base import BaseTool
from utils.vectorstore import search_user_context, search_session_memory
from utils.helpers import get_logger
import config

logger = get_logger(__name__)


class UserProfileTool(BaseTool):
    """获取用户配置和上下文信息工具"""
    
    def __init__(self):
        super().__init__(
            name="get_user_profile",
            description="搜索用户的待办事项（todo）、智能提示（tips）以及会话记忆（session_memory）。仅用于检索用户个人计划、任务、提示信息和对话上下文，不用于获取外部信息或市场数据。",
            is_async=False
        )
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询文本，用于检索相关的待办事项（todo）、提示（tips）和会话记忆。应该使用用户查询中的关键词，例如：如果用户问'明天的计划'，应该使用'明天'作为查询词。"
                },
                "context_type": {
                    "type": "string",
                    "description": "上下文类型过滤。可选值: task（待办事项）、tip（提示）、memory（会话记忆）、all（全部）。",
                    "enum": ["task", "tip", "memory", "all"],
                    "default": "all"
                },
                "session_id": {
                    "type": "string",
                    "description": "会话ID（可选），如果提供且 context_type 包含 memory，会从该会话的记忆中检索信息"
                },
                "current_page_url": {  # 新增参数
                    "type": "string",
                    "description": "当前页面URL（可选），如果提供，将只返回该页面的内容，过滤掉其他历史页面的内容"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        }
    
    def execute(
        self, 
        query: Optional[str] = None, 
        context_type: str = "all", 
        session_id: Optional[str] = None,
        current_page_url: Optional[str] = None,  # 新增参数
        limit: int = 10, 
        **kwargs
    ) -> Any:
        """
        获取用户配置和上下文信息
        
        Args:
            query: 搜索查询
            context_type: 上下文类型过滤
            session_id: 会话ID（用于检索会话记忆）
            current_page_url: 当前页面URL（如果提供，只返回该页面的内容）
            limit: 返回结果数量
        
        Returns:
            用户配置字典，包含偏好设置和上下文信息
        """
        try:
            # 基础配置信息
            base_profile = {
                "preferences": {
                    "language": "zh-CN",
                    "timezone": "Asia/Shanghai"
                },
                "interests": [],
                "settings": {}
            }
            
            # 如果提供了查询，从向量数据库检索相关上下文
            if query:
                logger.info(f"Searching user context for query: {query}, current_page_url: {current_page_url}")
                
                tasks = []
                tips = []
                memories = []
                pages = []
                
                # 1. 如果提供了 current_page_url，只检索当前页面的内容
                if current_page_url:
                    # 规范化 URL（移除尾随斜杠，确保匹配）
                    normalized_url = current_page_url.rstrip('/')
                    logger.info(f"Searching only current page content for URL: {normalized_url}")
                    from utils.vectorstore import search_similar_content
                    
                    # 尝试两种 URL 格式（带斜杠和不带斜杠）
                    url_variants = [normalized_url, normalized_url + '/']
                    
                    # 先尝试精确匹配
                    current_page_results = search_similar_content(
                        query=query,
                        limit=limit,
                        filter_metadata={
                            "$and": [
                                {
                                    "$or": [
                                        {"url": normalized_url},
                                        {"url": normalized_url + '/'}
                                    ]
                                },
                                {
                                    "$or": [
                                        {"source": "chat_context"},
                                        {"source": "web_crawler"},
                                        {"source": "web-crawler-initial"}
                                    ]
                                }
                            ]
                        }
                    )
                    
                    # 将当前页面内容添加到 pages 列表
                    for result in current_page_results:
                        metadata = result.get('metadata', {})
                        result_url = metadata.get("url", "").rstrip('/')
                        
                        # 规范化比较
                        if result_url.rstrip('/') != normalized_url:
                            logger.warning(f"Skipping non-matching URL: {result_url} != {normalized_url}")
                            continue
                        
                        item = {
                            "content": result.get('content', ''),
                            "metadata": metadata,
                            "relevance_score": 1.0 - min(result.get('distance', 1.0), 1.0),
                            "title": metadata.get("title", ""),
                            "url": result_url,
                            "is_current_page": True
                        }
                        pages.append(item)
                    
                    logger.info(f"Found {len(pages)} chunks from current page only (URL: {normalized_url})")
                    
                    # 如果检索结果为空，尝试直接查询该 URL 的所有内容（不依赖语义搜索）
                    if len(pages) == 0:
                        logger.warning(f"No semantic search results for URL: {normalized_url}, trying direct query")
                        try:
                            from utils.vectorstore import get_collection
                            collection = get_collection()
                            
                            # 直接根据 URL 查询（不依赖语义相似度）
                            direct_results = collection.get(
                                where={
                                    "$and": [
                                        {
                                            "$or": [
                                                {"url": normalized_url},
                                                {"url": normalized_url + '/'}
                                            ]
                                        },
                                        {
                                            "$or": [
                                                {"source": "chat_context"},
                                                {"source": "web_crawler"},
                                                {"source": "web-crawler-initial"}
                                            ]
                                        }
                                    ]
                                },
                                limit=limit
                            )
                            
                            if direct_results and direct_results.get('documents'):
                                logger.info(f"Found {len(direct_results['documents'])} chunks via direct query")
                                for i, doc in enumerate(direct_results['documents']):
                                    metadata = direct_results['metadatas'][i] if direct_results.get('metadatas') else {}
                                    item = {
                                        "content": doc,
                                        "metadata": metadata,
                                        "relevance_score": 0.9,  # 直接查询的结果相关性较高
                                        "title": metadata.get("title", ""),
                                        "url": metadata.get("url", "").rstrip('/'),
                                        "is_current_page": True
                                    }
                                    pages.append(item)
                        except Exception as e:
                            logger.exception(f"Error in direct query: {e}")
                
                # 2. 检索待办事项和提示（不包含其他页面内容）
                if context_type in ["all", "task", "tip"]:
                    # 如果有 current_page_url，不检索其他页面内容
                    include_page = True # 默认包含其他页面内容
                    if current_page_url:
                        include_page = False # 如果提供了 current_page_url，则不包含其他页面内容
                    
                    context_results = search_user_context(
                        query=query,
                        context_type=context_type,
                        limit=limit,
                        include_todos=True,
                        include_tips=True,
                        include_page_content=include_page  # 如果有当前页面URL，不包含其他页面
                    )
                    
                    for result in context_results:
                        ctx_type = result.get("context_type", "unknown")
                        source = result.get("source", "")
                        content = result.get("content", "")
                        metadata = result.get("metadata", {})
                        
                        item = {
                            "content": content,
                            "metadata": metadata,
                            "relevance_score": 1.0 - min(result.get("distance", 1.0), 1.0)
                        }
                        
                        if ctx_type == "task":
                            tasks.append(item)
                        elif ctx_type == "tip":
                            tips.append(item)
                        # 如果有 current_page_url，不添加其他页面内容
                        # 如果没有 current_page_url，才添加网页内容
                        elif source in ["web_crawler", "chat_context", "web-crawler-initial"] and not current_page_url:
                            item["title"] = metadata.get("title", "")
                            item["url"] = metadata.get("url", "")
                            pages.append(item)
                
                # 3. 检索会话记忆（如果提供了 session_id）
                if context_type in ["all", "memory"] and session_id:
                    logger.info(f"Searching session memory for session: {session_id}")
                    memory_results = search_session_memory(
                        session_id=session_id,
                        query=query,
                        limit=limit
                    )
                    
                    for result in memory_results:
                        content = result.get("content", "")
                        metadata = result.get("metadata", {})
                        content_type = result.get("context_type", "general")
                        
                        item = {
                            "content": content,
                            "metadata": metadata,
                            "content_type": content_type,
                            "relevance_score": 1.0 - min(result.get("distance", 1.0), 1.0),
                            "timestamp": result.get("timestamp", "")
                        }
                        memories.append(item)
                
                base_profile["context_search"] = {
                    "query": query,
                    "results_count": len(tasks) + len(tips) + len(memories) + len(pages),
                    "tasks": tasks,
                    "tips": tips,
                    "memories": memories,
                    "pages": pages  # 只包含当前页面内容（如果有 current_page_url）
                }
            else:
                # 如果没有查询，返回一个通用的上下文摘要
                logger.info("No query provided, generating user context summary")
                
                # 尝试搜索一些常见的上下文类型来构建摘要
                all_entities = search_user_context("", context_type="entity", limit=10)
                all_interests = search_user_context("", context_type="interest", limit=10)
                
                # 提取去重后的关键词和主题
                unique_keywords = set()
                unique_topics = set()
                categories = set()
                
                for item in all_entities:
                    content = item.get("content", "")
                    if "关键词:" in content:
                        keyword = content.replace("关键词:", "").strip()
                        unique_keywords.add(keyword)
                    elif "主题:" in content:
                        topic = content.replace("主题:", "").strip()
                        unique_topics.add(topic)
                
                for item in all_interests:
                    content = item.get("content", "")
                    if "用户关注领域:" in content:
                        category = content.replace("用户关注领域:", "").strip()
                        categories.add(category)
                
                base_profile["context_summary"] = {
                    "keywords": list(unique_keywords)[:10],
                    "topics": list(unique_topics)[:10],
                    "categories": list(categories)[:5],
                    "total_entities": len(all_entities),
                    "total_interests": len(all_interests)
                }
                
                base_profile["interests"] = list(categories)
            
            return base_profile
            
        except Exception as e:
            logger.exception(f"Error getting user profile: {e}")
            # 返回基础配置，即使检索失败
            return {
                "preferences": {
                    "language": "zh-CN",
                    "timezone": "Asia/Shanghai"
                },
                "interests": [],
                "settings": {},
                "error": f"Failed to retrieve context: {str(e)}"
            }


def get_profile_tools() -> list:
    """获取所有配置工具实例"""
    return [
        UserProfileTool(),
        # 可以添加更多配置工具
    ]

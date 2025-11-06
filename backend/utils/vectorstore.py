"""
向量数据库操作模块 - ChromaDB
"""

import json
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import config
from utils.helpers import get_logger

logger = get_logger(__name__)

# 全局 ChromaDB 客户端
_chroma_client = None
_collection = None


def get_chroma_client():
    """获取或创建 ChromaDB 客户端"""
    global _chroma_client
    if _chroma_client is None:
        try:
            _chroma_client = chromadb.PersistentClient(
                path=str(config.CHROMA_PERSIST_DIR),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"ChromaDB client initialized at {config.CHROMA_PERSIST_DIR}")
        except Exception as e:
            logger.exception(f"Failed to initialize ChromaDB client: {e}")
            raise
    return _chroma_client


def get_collection():
    """获取或创建集合（仅用于存储，不处理embedding）"""
    global _collection
    if _collection is None:
        try:
            client = get_chroma_client()
            # ChromaDB 仅用于存储向量，不使用其默认的 sentence-transformers
            # 所有 embedding 由配置的向量模型生成
            _collection = client.get_or_create_collection(
                name=config.CHROMA_COLLECTION_NAME,
                metadata={
                    "description": "Web data collection",
                    "embedding_provider": "external"  # 标记使用外部embedding
                }
            )
            logger.info(f"ChromaDB collection '{config.CHROMA_COLLECTION_NAME}' ready (external embedding only)")
        except Exception as e:
            logger.exception(f"Failed to get/create collection: {e}")
            raise
    return _collection


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """
    将文本分块
    
    Args:
        text: 要分块的文本
        chunk_size: 每块的大小（字符数）
        overlap: 重叠部分的大小
    
    Returns:
        文本块列表
    """
    if chunk_size is None:
        chunk_size = config.CHUNK_SIZE
    if overlap is None:
        overlap = config.CHUNK_OVERLAP
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def add_web_data_to_vectorstore(
    web_data_id: int,
    title: str,
    url: str,
    content: str,
    source: str = "web_crawler",
    tags: List[str] = None,
    metadata: Dict[str, Any] = None,
    embedding_function=None,
    session_id: Optional[str] = None  # 新增：会话ID
) -> bool:
    """
    将网页数据添加到向量数据库
    
    Args:
        web_data_id: 网页数据ID
        title: 标题
        url: URL
        content: 内容（JSON 或文本）
        source: 来源
        tags: 标签列表
        metadata: 额外元数据
        embedding_function: 自定义嵌入函数
        session_id: 会话ID（新增，用于过滤页面内容）
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled, skipping")
            return True
        
        # 检查是否有 embedding 函数，必须使用配置的向量模型
        if not embedding_function:
            logger.error("No embedding function provided. Vector storage requires external embedding model.")
            return False
        
        # 如果 content 是字典，转换为字符串
        if isinstance(content, dict):
            content_text = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            content_text = str(content)
        
        # 将内容分块
        chunks = chunk_text(content_text)
        logger.info(f"Split content into {len(chunks)} chunks")
        
        # 准备向量数据库文档
        collection = get_collection()
        
        documents = []
        metadatas = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            doc_id = f"web_{web_data_id}_chunk_{i}"
            
            chunk_metadata = {
                "web_data_id": web_data_id,
                "title": title,
                "url": url or "",
                "source": source,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "tags": json.dumps(tags or [], ensure_ascii=False),
            }
            
            # 添加 session_id（如果是 chat_context、chat_conversation 或 web_crawler 来源）
            # 抓取的页面内容应该作为"上文"关联到当前session
            if session_id and source in ["chat_context", "chat_conversation", "web_crawler", "web-crawler-initial", "web-crawler-incremental"]:
                chunk_metadata["session_id"] = session_id
            
            # 添加自定义元数据
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        chunk_metadata[f"meta_{key}"] = value
            
            documents.append(chunk)
            metadatas.append(chunk_metadata)
            ids.append(doc_id)
        
        # 使用配置的向量模型生成 embeddings
        try:
            embeddings = embedding_function(documents)
            if not embeddings:
                logger.error("Embedding function returned None or empty. Cannot store without embeddings.")
                return False
            
            # 验证 embeddings 数量与文档数量一致
            if len(embeddings) != len(documents):
                logger.error(f"Embedding count mismatch: {len(embeddings)} embeddings for {len(documents)} documents")
                return False
            
            # 存储到 ChromaDB（仅存储，不生成 embedding）
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            logger.info(f"Added {len(chunks)} chunks to vectorstore for web_data_id={web_data_id}, session_id={session_id}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to generate or store embeddings: {e}")
            return False
        
    except Exception as e:
        logger.exception(f"Error adding web data to vectorstore: {e}")
        return False


def search_similar_content(
    query: str,
    limit: int = 5,
    filter_metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    搜索相似内容（必须使用配置的向量模型）
    
    Args:
        query: 查询文本
        limit: 返回结果数量
        filter_metadata: 元数据过滤条件
    
    Returns:
        相似内容列表
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled")
            return []
        
        # 生成查询向量（必须使用配置的嵌入模型）
        try:
            from utils.llm import generate_embedding
            query_embedding = generate_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding. Cannot search without embedding model.")
                return []
            
            logger.info(f"Generated query embedding (dim: {len(query_embedding)})")
            
        except Exception as e:
            logger.exception(f"Failed to generate query embedding: {e}")
            return []
        
        # 执行查询（使用嵌入向量）
        collection = get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=filter_metadata
        )
        
        # 格式化结果
        formatted_results = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
        
        logger.info(f"Found {len(formatted_results)} similar results for query")
        return formatted_results
        
    except Exception as e:
        logger.exception(f"Error searching similar content: {e}")
        return []


def delete_web_data_from_vectorstore(web_data_id: int) -> bool:
    """
    从向量数据库删除网页数据
    
    Args:
        web_data_id: 网页数据ID
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            return True
        
        collection = get_collection()
        
        # 查找所有相关文档
        results = collection.get(
            where={"web_data_id": web_data_id}
        )
        
        if results and results['ids']:
            collection.delete(ids=results['ids'])
            logger.info(f"Deleted {len(results['ids'])} chunks for web_data_id={web_data_id}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error deleting web data from vectorstore: {e}")
        return False


def search_user_context(
    query: str,
    context_type: str = "all",
    limit: int = 10,
    include_todos: bool = False,
    include_tips: bool = False,
    include_page_content: bool = False,
    current_page_url: Optional[str] = None,
    session_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    搜索用户上下文信息（todos, tips, 页面内容等）
    
    Args:
        query: 搜索查询文本
        context_type: 上下文类型过滤（task, tip, entity, interest, all）
        limit: 返回结果数量
        include_todos: 是否包含待办事项
        include_tips: 是否包含提示
        include_page_content: 是否包含页面内容
        current_page_url: 当前页面URL（如果提供，只搜索该页面的内容）
        session_id: 会话ID（用于过滤对话内容，只返回该会话的对话记录）
    
    Returns:
        搜索结果列表，每个结果包含 content, metadata, distance, context_type
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled")
            return []
        
        results = []
        
        # 构建过滤条件
        where_filters = []
        
        # 根据 context_type 和 include 参数构建过滤条件
        source_filters = []
        
        # 1. 待办事项（todo/task）- 不受 session_id 限制
        if include_todos or context_type in ["all", "task"]:
            source_filters.append("todo")
        
        # 2. 提示（tips）- 不受 session_id 限制
        if include_tips or context_type in ["all", "tip"]:
            source_filters.append("tip")
        
        # 3. 页面内容和对话记录
        if include_page_content or context_type in ["all"]:
            # 如果提供了 session_id，只包含该会话的对话内容和页面内容（包括抓取的页面内容）
            if session_id:
                # 当前会话的对话内容和页面内容（包括抓取的页面内容）
                source_filters.extend(["chat_conversation", "chat_context", "web_crawler", "web-crawler-initial", "web-crawler-incremental"])
                # 抓取的页面内容作为"上文"关联到当前session，可以被当前session检索到
            else:
                # 没有 session_id，包含所有来源
                source_filters.extend(["chat_context", "web_crawler", "web-crawler-initial", "chat_conversation"])
        
        if source_filters:
            if len(source_filters) == 1:
                where_filters.append({"source": source_filters[0]})
            else:
                where_filters.append({"$or": [{"source": s} for s in source_filters]})
        
        # 如果指定了当前页面URL，添加URL过滤
        if current_page_url and include_page_content:
            normalized_url = current_page_url.rstrip('/')
            url_filter = {"url": normalized_url}
            if where_filters:
                combined_filter = {"$and": where_filters + [url_filter]}
                where_filters = [combined_filter]
            else:
                where_filters = [url_filter]
        
        # 如果提供了 session_id，添加会话过滤（只过滤对话相关的内容）
        if session_id and include_page_content:
            # 构建会话过滤：
            # - todo 和 tip 不受 session_id 限制（总是包含）
            # - chat_conversation、chat_context、web_crawler 等必须匹配 session_id（抓取的页面内容也关联到当前session）
            session_filter = {
                "$or": [
                    # 待办事项和提示不受限制
                    {"source": "todo"},
                    {"source": "tip"},
                    # 当前会话的对话内容和页面内容（包括抓取的页面内容）
                    {"$and": [{"source": "chat_conversation"}, {"session_id": session_id}]},
                    {"$and": [{"source": "chat_context"}, {"session_id": session_id}]},
                    {"$and": [{"source": "web_crawler"}, {"session_id": session_id}]},
                    {"$and": [{"source": "web-crawler-initial"}, {"session_id": session_id}]},
                    {"$and": [{"source": "web-crawler-incremental"}, {"session_id": session_id}]}
                ]
            }
            
            if where_filters:
                if len(where_filters) == 1 and isinstance(where_filters[0], dict) and "$and" in where_filters[0]:
                    where_filters[0]["$and"].append(session_filter)
                else:
                    combined_filter = {"$and": where_filters + [session_filter]}
                    where_filters = [combined_filter]
            else:
                where_filters = [session_filter]
        
        # 如果没有查询文本，使用空字符串（会返回最近的记录）
        search_query = query if query and query.strip() else ""
        
        # 如果查询为空，需要从数据库获取所有相关记录
        if not search_query:
            # 从SQLite获取todos和tips
            if include_todos or context_type in ["all", "task"]:
                from utils.db import get_todos
                todos = get_todos(status=0, limit=limit)
                for todo in todos:
                    content = f"待办事项: {todo.get('title', '')}"
                    if todo.get('description'):
                        content += f"\n描述: {todo.get('description', '')}"
                    results.append({
                        "content": content,
                        "metadata": {
                            "todo_id": todo.get('id'),
                            "title": todo.get('title'),
                            "status": todo.get('status'),
                            "priority": todo.get('priority'),
                            "start_time": todo.get('start_time'),
                            "end_time": todo.get('end_time')
                        },
                        "distance": 0.0,
                        "context_type": "task"
                    })
            
            if include_tips or context_type in ["all", "tip"]:
                from utils.db import get_tips
                tips = get_tips(limit=limit)
                for tip in tips:
                    results.append({
                        "content": f"提示: {tip.get('title', '')}\n{tip.get('content', '')}",
                        "metadata": {
                            "tip_id": tip.get('id'),
                            "title": tip.get('title'),
                            "tip_type": tip.get('tip_type'),
                            "source_urls": tip.get('source_urls')
                        },
                        "distance": 0.0,
                        "context_type": "tip"
                    })
            
            # 如果提供了 session_id，也获取该会话的对话记录
            if session_id and include_page_content:
                try:
                    collection = get_collection()
                    # 获取当前会话的对话记录
                    conversation_results = collection.get(
                        where={
                            "$and": [
                                {"source": "chat_conversation"},
                                {"session_id": session_id}
                            ]
                        },
                        limit=limit
                    )
                    
                    if conversation_results and conversation_results.get('ids'):
                        for i in range(len(conversation_results['ids'])):
                            metadata = conversation_results['metadatas'][i] if conversation_results.get('metadatas') else {}
                            content = conversation_results['documents'][i] if conversation_results.get('documents') else ""
                            results.append({
                                "content": content,
                                "metadata": metadata,
                                "distance": 0.0,
                                "context_type": "conversation"  # 标记为对话类型
                            })
                except Exception as e:
                    logger.debug(f"Failed to get conversation history: {e}")
            
            # 限制返回数量
            return results[:limit]
        
        # 使用语义搜索
        where_filter = where_filters[0] if where_filters else None
        
        # 如果指定了当前页面URL，先尝试直接查询
        if current_page_url and include_page_content:
            normalized_url = current_page_url.rstrip('/')
            
            # 提取基础URL（去除查询参数），用于更灵活的匹配
            try:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(normalized_url)
                base_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', '')).rstrip('/')
            except:
                base_url = normalized_url
            
            try:
                collection = get_collection()
                
                # 构建查询条件：优先检索当前会话的内容
                if session_id:
                    # 策略1: 先尝试检索当前会话的页面内容（chat_context）
                    current_session_query = {
                        "$and": [
                            {"url": normalized_url},  # 精确匹配
                            {"source": "chat_context"},
                            {"session_id": session_id}
                        ]
                    }
                    
                    current_session_results = collection.get(
                        where=current_session_query,
                        limit=limit
                    )
                    
                    if current_session_results and current_session_results.get('ids'):
                        # 如果找到当前会话的内容，优先使用
                        from utils.llm import generate_embedding
                        query_embedding = generate_embedding(search_query) if search_query else None
                        
                        if query_embedding:
                            semantic_results = collection.query(
                                query_embeddings=[query_embedding],
                                n_results=limit,
                                where=current_session_query
                            )
                            
                            if semantic_results and semantic_results.get('documents'):
                                for i in range(len(semantic_results['documents'][0])):
                                    results.append({
                                        "content": semantic_results['documents'][0][i],
                                        "metadata": semantic_results['metadatas'][0][i] if semantic_results.get('metadatas') else {},
                                        "distance": semantic_results['distances'][0][i] if semantic_results.get('distances') else 1.0,
                                        "context_type": "page"
                                    })
                                logger.info(f"Found {len(results)} pages from current session (chat_context) for URL: {normalized_url}")
                                found_current_page = True
                            else:
                                found_current_page = False
                        else:
                            # 即使没有查询文本，也返回找到的结果
                            for i in range(len(current_session_results['ids'])):
                                results.append({
                                    "content": current_session_results['documents'][i] if current_session_results.get('documents') else "",
                                    "metadata": current_session_results['metadatas'][i] if current_session_results.get('metadatas') else {},
                                    "distance": 0.0,
                                    "context_type": "page"
                                })
                            logger.info(f"Found {len(results)} pages from current session (chat_context) for URL: {normalized_url} (no query text)")
                            found_current_page = True
                    else:
                        found_current_page = False
                    
                    # 策略2: 如果当前会话没有内容，再检索其他来源（web_crawler等）
                    if not found_current_page:
                        # 先尝试精确匹配URL
                        other_sources_query_exact = {
                            "$and": [
                                {"url": normalized_url},
                                {
                                    "$or": [
                                        {"source": "web_crawler"},
                                        {"source": "web-crawler-initial"},
                                        {"source": "web-crawler-incremental"}
                                    ]
                                }
                            ]
                        }
                        
                        # 如果精确匹配失败，尝试基础URL匹配（忽略查询参数）
                        other_sources_query_base = {
                            "$and": [
                                {
                                    "$or": [
                                        {"url": base_url},  # 基础URL匹配
                                        {"url": {"$regex": f"^{base_url}(\\?|$)"}}  # 正则匹配：基础URL开头
                                    ]
                                },
                                {
                                    "$or": [
                                        {"source": "web_crawler"},
                                        {"source": "web-crawler-initial"},
                                        {"source": "web-crawler-incremental"}
                                    ]
                                }
                            ]
                        }
                        
                        from utils.llm import generate_embedding
                        query_embedding = generate_embedding(search_query) if search_query else None
                        
                        # 先尝试精确匹配
                        if query_embedding:
                            semantic_results = collection.query(
                                query_embeddings=[query_embedding],
                                n_results=limit,
                                where=other_sources_query_exact
                            )
                            
                            if semantic_results and semantic_results.get('documents'):
                                for i in range(len(semantic_results['documents'][0])):
                                    results.append({
                                        "content": semantic_results['documents'][0][i],
                                        "metadata": semantic_results['metadatas'][0][i] if semantic_results.get('metadatas') else {},
                                        "distance": semantic_results['distances'][0][i] if semantic_results.get('distances') else 1.0,
                                        "context_type": "page"
                                    })
                                logger.info(f"Found {len([r for r in results if r.get('context_type') == 'page'])} pages from other sources (exact URL match) for URL: {normalized_url}")
                            else:
                                # 精确匹配失败，尝试基础URL匹配
                                semantic_results = collection.query(
                                    query_embeddings=[query_embedding],
                                    n_results=limit,
                                    where=other_sources_query_base
                                )
                                
                                if semantic_results and semantic_results.get('documents'):
                                    for i in range(len(semantic_results['documents'][0])):
                                        results.append({
                                            "content": semantic_results['documents'][0][i],
                                            "metadata": semantic_results['metadatas'][0][i] if semantic_results.get('metadatas') else {},
                                            "distance": semantic_results['distances'][0][i] if semantic_results.get('distances') else 1.0,
                                            "context_type": "page"
                                        })
                                    logger.info(f"Found {len([r for r in results if r.get('context_type') == 'page'])} pages from other sources (base URL match) for URL: {base_url}")
                        else:
                            # 没有查询文本，直接查询
                            direct_results = collection.get(
                                where=other_sources_query_exact,
                                limit=limit
                            )
                            
                            if direct_results and direct_results.get('ids'):
                                for i in range(len(direct_results['ids'])):
                                    results.append({
                                        "content": direct_results['documents'][i] if direct_results.get('documents') else "",
                                        "metadata": direct_results['metadatas'][i] if direct_results.get('metadatas') else {},
                                        "distance": 0.0,
                                        "context_type": "page"
                                    })
                                logger.info(f"Found {len([r for r in results if r.get('context_type') == 'page'])} pages from other sources (exact URL, no query) for URL: {normalized_url}")
                            else:
                                # 精确匹配失败，尝试基础URL匹配
                                direct_results = collection.get(
                                    where=other_sources_query_base,
                                    limit=limit
                                )
                                
                                if direct_results and direct_results.get('ids'):
                                    for i in range(len(direct_results['ids'])):
                                        results.append({
                                            "content": direct_results['documents'][i] if direct_results.get('documents') else "",
                                            "metadata": direct_results['metadatas'][i] if direct_results.get('metadatas') else {},
                                            "distance": 0.0,
                                            "context_type": "page"
                                        })
                                    logger.info(f"Found {len([r for r in results if r.get('context_type') == 'page'])} pages from other sources (base URL, no query) for URL: {base_url}")
                else:
                    # 没有 session_id，检索所有来源
                    query_where = {"url": normalized_url}
                    
                    from utils.llm import generate_embedding
                    query_embedding = generate_embedding(search_query) if search_query else None
                    
                    if query_embedding:
                        semantic_results = collection.query(
                            query_embeddings=[query_embedding],
                            n_results=limit,
                            where=query_where
                        )
                        
                        if semantic_results and semantic_results.get('documents'):
                            for i in range(len(semantic_results['documents'][0])):
                                results.append({
                                    "content": semantic_results['documents'][0][i],
                                    "metadata": semantic_results['metadatas'][0][i] if semantic_results.get('metadatas') else {},
                                    "distance": semantic_results['distances'][0][i] if semantic_results.get('distances') else 1.0,
                                    "context_type": "page"
                                })
                    else:
                        # 没有查询文本，直接查询
                        direct_results = collection.get(
                            where=query_where,
                            limit=limit
                        )
                        
                        if direct_results and direct_results.get('ids'):
                            for i in range(len(direct_results['ids'])):
                                results.append({
                                    "content": direct_results['documents'][i] if direct_results.get('documents') else "",
                                    "metadata": direct_results['metadatas'][i] if direct_results.get('metadatas') else {},
                                    "distance": 0.0,
                                    "context_type": "page"
                                })
                        
            except Exception as e:
                logger.debug(f"Direct URL query failed, falling back to semantic search: {e}")
        
        # 如果还没有结果，使用通用语义搜索
        if not results:
            similar_results = search_similar_content(
                query=search_query,
                limit=limit,
                filter_metadata=where_filter
            )
            
            for result in similar_results:
                metadata = result.get("metadata", {})
                source = metadata.get("source", "")
                
                # 确定context_type
                if source == "todo":
                    ctx_type = "task"
                elif source == "tip":
                    ctx_type = "tip"
                elif source == "chat_conversation":
                    ctx_type = "conversation"  # 对话记录
                elif source in ["chat_context", "web_crawler", "web-crawler-initial", "web-crawler-incremental"]:
                    ctx_type = "page"
                # 确定context_type时，添加 web-crawler-incremental
                elif source in ["web-crawler-incremental"]:
                    ctx_type = "page"
                else:
                    ctx_type = "unknown"
                
                # 如果指定了当前页面URL，只返回匹配的页面内容
                if current_page_url and ctx_type in ["page", "conversation"]:
                    url = metadata.get("url", "")
                    normalized_current = current_page_url.rstrip('/')
                    normalized_result = url.rstrip('/') if url else ""
                    # 对话记录没有URL，所以不跳过
                    if ctx_type == "page" and normalized_result != normalized_current:
                        continue
                
                # 如果提供了 session_id，过滤对话内容（只返回该会话的内容）
                if session_id:
                    if source in ["chat_conversation", "chat_context", "web_crawler", "web-crawler-initial", "web-crawler-incremental"]:
                        result_session_id = metadata.get("session_id", "")
                        if result_session_id != session_id:
                            continue  # 跳过不同会话的内容
                    # todo 和 tip 不受 session_id 限制，总是包含
                
                results.append({
                    "content": result.get("content", ""),
                    "metadata": metadata,
                    "distance": result.get("distance", 1.0),
                    "context_type": ctx_type
                })
        
        logger.info(f"Found {len(results)} user context results for query: {search_query}, session_id: {session_id}")
        logger.info(f"Results breakdown: {len([r for r in results if r.get('context_type') == 'task'])} tasks, "
                   f"{len([r for r in results if r.get('context_type') == 'conversation'])} conversations, "
                   f"{len([r for r in results if r.get('context_type') == 'page'])} pages")
        return results[:limit]
        
    except Exception as e:
        logger.exception(f"Error searching user context: {e}")
        return []


def add_session_memory_to_vectorstore(
    session_id: str,
    content: str,
    content_type: str = "general",
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    添加会话记忆到向量数据库
    
    Args:
        session_id: 会话ID
        content: 要存储的内容
        content_type: 内容类型（如 task, product, plan, location, time 等）
        metadata: 额外元数据
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled, skipping")
            return True
        
        if not content or not content.strip():
            logger.warning("Empty content, skipping")
            return False
        
        # 生成embedding
        from utils.llm import generate_embedding
        embedding = generate_embedding(content.strip())
        
        if not embedding:
            logger.error("Failed to generate embedding for session memory")
            return False
        
        # 准备元数据
        memory_metadata = {
            "session_id": session_id,
            "content_type": content_type,
            "source": "session_memory"
        }
        
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    memory_metadata[key] = value
        
        # 生成唯一ID
        import uuid
        memory_id = f"memory_{session_id}_{uuid.uuid4().hex[:8]}"
        
        # 存储到ChromaDB
        collection = get_collection()
        collection.add(
            documents=[content.strip()],
            metadatas=[memory_metadata],
            ids=[memory_id],
            embeddings=[embedding]
        )
        
        logger.info(f"Added session memory to vectorstore: session_id={session_id}, content_type={content_type}, id={memory_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Error adding session memory to vectorstore: {e}")
        return False


def search_session_memory(
    session_id: str,
    query: str = "",
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    搜索会话记忆
    
    Args:
        session_id: 会话ID
        query: 搜索查询文本（如果为空，返回最近的记录）
        limit: 返回结果数量
    
    Returns:
        搜索结果列表，每个结果包含 content, metadata, distance, context_type, timestamp
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled")
            return []
        
        collection = get_collection()
        
        # 构建过滤条件
        filter_metadata = {
            "$and": [
                {"source": "session_memory"},
                {"session_id": session_id}
            ]
        }
        
        # 如果没有查询文本，返回最近的记录
        if not query or not query.strip():
            # 获取所有该会话的记忆
            results = collection.get(
                where=filter_metadata,
                limit=limit
            )
            
            formatted_results = []
            if results and results.get('ids'):
                for i in range(len(results['ids'])):
                    metadata = results['metadatas'][i] if results.get('metadatas') else {}
                    formatted_results.append({
                        "content": results['documents'][i] if results.get('documents') else "",
                        "metadata": metadata,
                        "distance": 0.0,  # 无查询时，距离为0
                        "context_type": metadata.get("content_type", "general"),
                        "timestamp": metadata.get("timestamp", "")
                    })
            
            return formatted_results
        
        # 使用语义搜索
        from utils.llm import generate_embedding
        query_embedding = generate_embedding(query)
        
        if not query_embedding:
            logger.error("Failed to generate query embedding for session memory search")
            return []
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=filter_metadata
        )
        
        formatted_results = []
        if results and results.get('documents'):
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": metadata,
                    "distance": results['distances'][0][i] if results.get('distances') else 1.0,
                    "context_type": metadata.get("content_type", "general"),
                    "timestamp": metadata.get("timestamp", "")
                })
        
        logger.info(f"Found {len(formatted_results)} session memory results for session {session_id}")
        return formatted_results
        
    except Exception as e:
        logger.exception(f"Error searching session memory: {e}")
        return []


def clear_vectorstore() -> bool:
    """
    清空向量数据库中的所有文档（保留集合）
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled")
            return True
        
        collection = get_collection()
        
        # 获取所有文档ID
        all_results = collection.get()
        
        if all_results and all_results.get('ids'):
            # 删除所有文档
            collection.delete(ids=all_results['ids'])
            logger.info(f"Cleared {len(all_results['ids'])} documents from vectorstore")
        else:
            logger.info("Vectorstore is already empty")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error clearing vectorstore: {e}")
        return False


def reset_vectorstore() -> bool:
    """
    重置向量数据库（删除集合并重建）
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled")
            return True
        
        client = get_chroma_client()
        collection_name = config.CHROMA_COLLECTION_NAME
        
        # 删除现有集合
        try:
            client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Collection may not exist: {e}")
        
        # 重置全局集合变量，强制重新创建
        global _collection
        _collection = None
        
        # 重新创建集合
        collection = get_collection()
        logger.info(f"Reset vectorstore: collection '{collection_name}' recreated")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error resetting vectorstore: {e}")
        return False


def add_todo_to_vectorstore(
    todo_id: int,
    title: str,
    description: str = "",
    priority: int = 0,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    status: int = 0
) -> bool:
    """
    将待办事项添加到向量数据库
    
    Args:
        todo_id: 待办事项ID
        title: 标题
        description: 描述
        priority: 优先级
        start_time: 开始时间
        end_time: 结束时间
        status: 状态（0=未完成，1=已完成）
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            return True
        
        # 构建待办事项的文本内容
        content_parts = [f"待办事项: {title}"]
        if description:
            content_parts.append(f"描述: {description}")
        if start_time:
            content_parts.append(f"开始时间: {start_time}")
        if end_time:
            content_parts.append(f"结束时间: {end_time}")
        if priority:
            content_parts.append(f"优先级: {priority}")
        
        content = "\n".join(content_parts)
        
        # 生成embedding
        from utils.llm import generate_embedding
        embedding = generate_embedding(content)
        
        if not embedding:
            logger.error(f"Failed to generate embedding for todo {todo_id}")
            return False
        
        # 准备元数据
        metadata = {
            "todo_id": todo_id,
            "title": title,
            "description": description or "",
            "priority": priority,
            "status": status,
            "source": "todo"
        }
        
        if start_time:
            metadata["start_time"] = start_time
        if end_time:
            metadata["end_time"] = end_time
        
        # 生成唯一ID
        todo_doc_id = f"todo_{todo_id}"
        
        # 存储到ChromaDB
        collection = get_collection()
        
        # 先删除旧的文档（如果存在）
        try:
            collection.delete(ids=[todo_doc_id])
        except:
            pass  # 如果不存在，忽略错误
        
        # 添加新文档
        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[todo_doc_id],
            embeddings=[embedding]
        )
        
        logger.info(f"Added todo to vectorstore: todo_id={todo_id}, title={title}")
        return True
        
    except Exception as e:
        logger.exception(f"Error adding todo to vectorstore: {e}")
        return False


def add_tip_to_vectorstore(
    tip_id: int,
    title: str,
    content: str,
    tip_type: str = "general",
    source_urls: Optional[List[str]] = None
) -> bool:
    """
    将提示添加到向量数据库
    
    Args:
        tip_id: 提示ID
        title: 标题
        content: 内容
        tip_type: 提示类型
        source_urls: 来源URL列表
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            return True
        
        # 构建提示的文本内容
        tip_content = f"提示: {title}\n{content}"
        
        # 生成embedding
        from utils.llm import generate_embedding
        embedding = generate_embedding(tip_content)
        
        if not embedding:
            logger.error(f"Failed to generate embedding for tip {tip_id}")
            return False
        
        # 准备元数据
        metadata = {
            "tip_id": tip_id,
            "title": title,
            "tip_type": tip_type,
            "source": "tip"
        }
        
        if source_urls:
            import json
            metadata["source_urls"] = json.dumps(source_urls, ensure_ascii=False)
        
        # 生成唯一ID
        tip_doc_id = f"tip_{tip_id}"
        
        # 存储到ChromaDB
        collection = get_collection()
        
        # 先删除旧的文档（如果存在）
        try:
            collection.delete(ids=[tip_doc_id])
        except:
            pass  # 如果不存在，忽略错误
        
        # 添加新文档
        collection.add(
            documents=[tip_content],
            metadatas=[metadata],
            ids=[tip_doc_id],
            embeddings=[embedding]
        )
        
        logger.info(f"Added tip to vectorstore: tip_id={tip_id}, title={title}")
        return True
        
    except Exception as e:
        logger.exception(f"Error adding tip to vectorstore: {e}")
        return False


def delete_todo_from_vectorstore(todo_id: int) -> bool:
    """
    从向量数据库删除待办事项
    
    Args:
        todo_id: 待办事项ID
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            return True
        
        collection = get_collection()
        todo_doc_id = f"todo_{todo_id}"
        
        try:
            collection.delete(ids=[todo_doc_id])
            logger.info(f"Deleted todo from vectorstore: todo_id={todo_id}")
        except Exception as e:
            logger.debug(f"Todo {todo_id} may not exist in vectorstore: {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error deleting todo from vectorstore: {e}")
        return False


def delete_tip_from_vectorstore(tip_id: int) -> bool:
    """
    从向量数据库删除提示
    
    Args:
        tip_id: 提示ID
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            return True
        
        collection = get_collection()
        tip_doc_id = f"tip_{tip_id}"
        
        try:
            collection.delete(ids=[tip_doc_id])
            logger.info(f"Deleted tip from vectorstore: tip_id={tip_id}")
        except Exception as e:
            logger.debug(f"Tip {tip_id} may not exist in vectorstore: {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Error deleting tip from vectorstore: {e}")
        return False

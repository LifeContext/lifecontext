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
    embedding_function=None
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
            
            logger.info(f"Added {len(chunks)} chunks to vectorstore for web_data_id={web_data_id}")
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


def add_user_context_to_vectorstore(
    context_id: str,
    context_type: str,  # "entity", "interest", "preference", "skill", etc.
    content: str,
    metadata: Dict[str, Any] = None,
    embedding_function=None
) -> bool:
    """
    将用户上下文信息添加到向量数据库（专用于 profile/entity 检索）
    
    Args:
        context_id: 上下文ID（唯一标识）
        context_type: 上下文类型（entity, interest, preference, skill, topic等）
        content: 上下文内容文本
        metadata: 额外元数据
        embedding_function: 嵌入函数
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled, skipping")
            return True
        
        if not embedding_function:
            logger.error("No embedding function provided")
            return False
        
        collection = get_collection()
        
        # 生成嵌入向量
        embeddings = embedding_function([content])
        if not embeddings or len(embeddings) == 0:
            logger.error("Failed to generate embedding")
            return False
        
        embedding = embeddings[0]
        
        # 构建元数据
        context_metadata = {
            "context_type": context_type,
            "context_id": context_id,
            "source": "user_context",
        }
        
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    context_metadata[f"meta_{key}"] = value
        
        # 存储到向量数据库
        collection.add(
            documents=[content],
            metadatas=[context_metadata],
            ids=[context_id],
            embeddings=[embedding]
        )
        
        logger.info(f"Added user context to vectorstore: {context_id} (type: {context_type})")
        return True
        
    except Exception as e:
        logger.exception(f"Error adding user context to vectorstore: {e}")
        return False


def extract_and_store_user_context_from_analysis(
    web_data_id: int,
    llm_analysis: Dict[str, Any],
    embedding_function=None
) -> bool:
    """
    从 LLM 分析结果中提取用户上下文信息并存储到向量数据库
    
    Args:
        web_data_id: 网页数据ID
        llm_analysis: LLM分析结果（来自 analyze_web_content）
        embedding_function: 嵌入函数
    
    Returns:
        是否成功
    """
    try:
        if not llm_analysis:
            return False
        
        success_count = 0
        
        # 1. 提取实体（从 keywords 和 topics）
        metadata_analysis = llm_analysis.get("metadata_analysis", {})
        keywords = metadata_analysis.get("keywords", [])
        topics = metadata_analysis.get("topics", [])
        category = metadata_analysis.get("category", "")
        
        # 存储关键词作为实体
        for i, keyword in enumerate(keywords):
            context_id = f"entity_{web_data_id}_kw_{i}"
            content = f"关键词: {keyword}"
            metadata = {
                "web_data_id": web_data_id,
                "entity_type": "keyword",
                "category": category
            }
            if add_user_context_to_vectorstore(
                context_id=context_id,
                context_type="entity",
                content=content,
                metadata=metadata,
                embedding_function=embedding_function
            ):
                success_count += 1
        
        # 存储主题作为实体
        for i, topic in enumerate(topics):
            context_id = f"entity_{web_data_id}_topic_{i}"
            content = f"主题: {topic}"
            metadata = {
                "web_data_id": web_data_id,
                "entity_type": "topic",
                "category": category
            }
            if add_user_context_to_vectorstore(
                context_id=context_id,
                context_type="entity",
                content=content,
                metadata=metadata,
                embedding_function=embedding_function
            ):
                success_count += 1
        
        # 2. 提取兴趣（从 category 和 topics）
        if category:
            context_id = f"interest_{web_data_id}_cat"
            content = f"用户关注领域: {category}"
            metadata = {
                "web_data_id": web_data_id,
                "interest_type": "category"
            }
            if add_user_context_to_vectorstore(
                context_id=context_id,
                context_type="interest",
                content=content,
                metadata=metadata,
                embedding_function=embedding_function
            ):
                success_count += 1
        
        # 3. 提取潜在兴趣（从 potential_insights）
        potential_insights = llm_analysis.get("potential_insights", [])
        for i, insight in enumerate(potential_insights):
            insight_title = insight.get("insight_title", "")
            insight_desc = insight.get("description", "")
            if insight_title:
                context_id = f"interest_{web_data_id}_insight_{i}"
                content = f"潜在兴趣: {insight_title}\n描述: {insight_desc}"
                metadata = {
                    "web_data_id": web_data_id,
                    "interest_type": "potential_insight"
                }
                if add_user_context_to_vectorstore(
                    context_id=context_id,
                    context_type="interest",
                    content=content,
                    metadata=metadata,
                    embedding_function=embedding_function
                ):
                    success_count += 1
        
        logger.info(f"Extracted and stored {success_count} user context items from web_data_id={web_data_id}")
        return success_count > 0
        
    except Exception as e:
        logger.exception(f"Error extracting user context from analysis: {e}")
        return False


def search_user_context(
    query: str,
    context_type: str = "all",
    limit: int = 5,
    include_todos: bool = True,
    include_tips: bool = True,
    include_page_content: bool = False  # 新增参数
) -> List[Dict[str, Any]]:
    """
    搜索用户上下文信息（包括 todo、tips、用户上下文、网页内容）
    
    Args:
        query: 搜索查询
        context_type: 上下文类型过滤（entity, interest, preference, skill, topic, task, tip, all）
        limit: 返回结果数量
        include_todos: 是否包含 todo
        include_tips: 是否包含 tips
        include_page_content: 是否包含网页内容（新增）
    
    Returns:
        搜索结果列表
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled")
            return []
        
        # 检查查询是否为空
        if not query or not query.strip():
            logger.warning("Empty query provided to search_user_context")
            # 如果查询为空，可以返回所有数据（使用大 limit）
            query = " "  # 使用空格作为查询，或者可以改为返回最近的记录
        
        from utils.llm import generate_embedding
        
        # 生成查询向量
        query_embedding = generate_embedding(query)
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        logger.info(f"Generated embedding for query: '{query}' (dim: {len(query_embedding)})")
        
        # 构建过滤条件
        where_filter = None
        
        if context_type == "all":
            # 搜索所有类型：user_context、todo、tip、网页内容
            or_conditions = []
            
            if include_todos:
                or_conditions.append({"source": "todo"})
            if include_tips:
                or_conditions.append({"source": "tip"})
            if include_page_content:
                # 添加网页内容来源
                or_conditions.append({"source": "web_crawler"})
                or_conditions.append({"source": "chat_context"})
                or_conditions.append({"source": "web-crawler-initial"})
            
            # 总是包含 user_context
            or_conditions.append({"source": "user_context"})
            
            if or_conditions:
                where_filter = {"$or": or_conditions}
            else:
                where_filter = {"source": "user_context"}
        elif context_type in ["task", "todo"]:
            where_filter = {"source": "todo"}
        elif context_type == "tip":
            where_filter = {"source": "tip"}
        elif context_type == "page":  # 新增：专门用于搜索页面内容
            or_conditions = [
                {"source": "web_crawler"},
                {"source": "chat_context"},
                {"source": "web-crawler-initial"}
            ]
            where_filter = {"$or": or_conditions}
        else:
            # entity, interest, topic 等用户上下文类型
            or_conditions = []
            
            # 添加 user_context 的特定类型
            or_conditions.append({
                "$and": [
                    {"source": "user_context"},
                    {"context_type": context_type}
                ]
            })
            
            # 总是包含 todo 和 tips（如果启用）
            if include_todos:
                or_conditions.append({"source": "todo"})
            if include_tips:
                or_conditions.append({"source": "tip"})
            if include_page_content:
                or_conditions.append({"source": "web_crawler"})
                or_conditions.append({"source": "chat_context"})
                or_conditions.append({"source": "web-crawler-initial"})
            
            where_filter = {"$or": or_conditions}
        
        logger.info(f"Using where filter: {where_filter}")
        
        # 执行查询
        collection = get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter
        )
        
        logger.info(f"ChromaDB query returned {len(results.get('documents', [[]])[0]) if results and results.get('documents') else 0} documents")
        
        # 格式化结果
        formatted_results = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                source = metadata.get('source', 'unknown')
                
                # 根据来源确定 context_type
                if source == "todo":
                    ctx_type = "task"
                elif source == "tip":
                    ctx_type = "tip"
                else:
                    ctx_type = metadata.get('context_type', 'unknown')
                
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": metadata,
                    "distance": results['distances'][0][i] if results['distances'] else None,
                    "context_type": ctx_type,
                    "source": source
                })
        
        logger.info(f"Found {len(formatted_results)} user context results for query: {query}")
        return formatted_results
        
    except Exception as e:
        logger.exception(f"Error searching user context: {e}")
        return []


def add_todo_to_vectorstore(
    todo_id: int,
    title: str,
    description: str = "",
    priority: int = 0,
    embedding_function=None
) -> bool:
    """
    将待办事项添加到向量数据库
    
    Args:
        todo_id: 待办事项ID
        title: 标题
        description: 描述
        priority: 优先级
        embedding_function: 嵌入函数
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled, skipping")
            return True
        
        if not embedding_function:
            logger.error("No embedding function provided")
            return False
        
        collection = get_collection()
        
        # 构建内容文本
        content = f"待办事项: {title}"
        if description:
            content += f"\n描述: {description}"
        content += f"\n优先级: {priority}"
        
        # 生成嵌入向量
        embeddings = embedding_function([content])
        if not embeddings or len(embeddings) == 0:
            logger.error("Failed to generate embedding")
            return False
        
        embedding = embeddings[0]
        
        # 构建元数据
        metadata = {
            "todo_id": todo_id,
            "title": title,
            "priority": priority,
            "source": "todo",
            "context_type": "task"
        }
        
        # 存储到向量数据库
        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[f"todo_{todo_id}"],
            embeddings=[embedding]
        )
        
        logger.info(f"Added todo to vectorstore: todo_id={todo_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Error adding todo to vectorstore: {e}")
        return False


def add_tip_to_vectorstore(
    tip_id: int,
    title: str,
    content: str,
    tip_type: str = "general",
    embedding_function=None
) -> bool:
    """
    将提示添加到向量数据库
    
    Args:
        tip_id: 提示ID
        title: 标题
        content: 内容
        tip_type: 提示类型
        embedding_function: 嵌入函数
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled, skipping")
            return True
        
        if not embedding_function:
            logger.error("No embedding function provided")
            return False
        
        collection = get_collection()
        
        # 构建内容文本
        content_text = f"提示: {title}\n内容: {content}"
        
        # 生成嵌入向量
        embeddings = embedding_function([content_text])
        if not embeddings or len(embeddings) == 0:
            logger.error("Failed to generate embedding")
            return False
        
        embedding = embeddings[0]
        
        # 构建元数据
        metadata = {
            "tip_id": tip_id,
            "title": title,
            "tip_type": tip_type,
            "source": "tip",
            "context_type": "tip"
        }
        
        # 存储到向量数据库
        collection.add(
            documents=[content_text],
            metadatas=[metadata],
            ids=[f"tip_{tip_id}"],
            embeddings=[embedding]
        )
        
        logger.info(f"Added tip to vectorstore: tip_id={tip_id}")
        return True
        
    except Exception as e:
        logger.exception(f"Error adding tip to vectorstore: {e}")
        return False


def delete_todo_from_vectorstore(todo_id: int) -> bool:
    """从向量数据库删除待办事项"""
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            return True
        
        collection = get_collection()
        collection.delete(ids=[f"todo_{todo_id}"])
        logger.info(f"Deleted todo from vectorstore: todo_id={todo_id}")
        return True
    except Exception as e:
        logger.exception(f"Error deleting todo from vectorstore: {e}")
        return False


def delete_tip_from_vectorstore(tip_id: int) -> bool:
    """从向量数据库删除提示"""
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            return True
        
        collection = get_collection()
        collection.delete(ids=[f"tip_{tip_id}"])
        logger.info(f"Deleted tip from vectorstore: tip_id={tip_id}")
        return True
    except Exception as e:
        logger.exception(f"Error deleting tip from vectorstore: {e}")
        return False


def clear_vectorstore() -> bool:
    """
    清空向量数据库中的所有数据
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled")
            return True
        
        collection = get_collection()
        
        # 方法1：获取所有文档ID并删除
        try:
            # 先获取所有数据
            all_data = collection.get()
            if all_data and all_data.get('ids'):
                ids = all_data['ids']
                logger.info(f"Found {len(ids)} documents to delete")
                
                # 删除所有文档
                collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents from vectorstore")
            else:
                logger.info("Vectorstore is already empty")
            
            return True
            
        except Exception as e:
            logger.exception(f"Error deleting documents: {e}")
            return False
            
    except Exception as e:
        logger.exception(f"Error clearing vectorstore: {e}")
        return False


def reset_vectorstore() -> bool:
    """
    重置向量数据库（删除集合并重新创建）
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled")
            return True
        
        client = get_chroma_client()
        
        # 删除现有集合
        try:
            client.delete_collection(name=config.CHROMA_COLLECTION_NAME)
            logger.info(f"Deleted collection: {config.CHROMA_COLLECTION_NAME}")
        except Exception as e:
            # 集合可能不存在，继续执行
            logger.debug(f"Collection may not exist: {e}")
        
        # 重置全局集合变量，下次调用 get_collection() 时会重新创建
        global _collection
        _collection = None
        
        logger.info("Vectorstore reset successfully")
        return True
        
    except Exception as e:
        logger.exception(f"Error resetting vectorstore: {e}")
        return False


def add_session_memory_to_vectorstore(
    session_id: str,
    content: str,
    content_type: str = "general",
    metadata: Dict[str, Any] = None,
    embedding_function=None
) -> bool:
    """
    将会话记忆添加到向量数据库
    
    Args:
        session_id: 会话ID
        content: 内容
        content_type: 内容类型（如 task, location, time, product 等）
        metadata: 额外的元数据
        embedding_function: 嵌入函数
    
    Returns:
        是否成功
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled, skipping")
            return True
        
        if not embedding_function:
            from utils.llm import generate_embedding
            # 生成嵌入向量
            embeddings = generate_embedding(content)
            if not embeddings:
                logger.error("Failed to generate embedding")
                return False
            embedding = embeddings
        else:
            embeddings = embedding_function([content])
            if not embeddings or len(embeddings) == 0:
                logger.error("Failed to generate embedding")
                return False
            embedding = embeddings[0]
        
        collection = get_collection()
        
        # 构建唯一ID（使用 session_id 和内容哈希）
        import hashlib
        content_hash = hashlib.md5(f"{session_id}_{content}".encode()).hexdigest()[:8]
        memory_id = f"session_memory_{session_id}_{content_hash}"
        
        # 检查是否已存在（避免重复）
        try:
            existing = collection.get(ids=[memory_id])
            if existing and existing.get('ids'):
                logger.debug(f"Session memory already exists: {memory_id}")
                return True  # 已存在，返回成功
        except:
            pass  # 不存在，继续添加
        
        # 构建元数据
        full_metadata = {
            "session_id": session_id,
            "content_type": content_type,
            "source": "session_memory",
            **(metadata or {})
        }
        
        # 存储到向量数据库
        collection.add(
            documents=[content],
            metadatas=[full_metadata],
            ids=[memory_id],
            embeddings=[embedding]
        )
        
        logger.info(f"Added session memory to vectorstore: session_id={session_id}, content_type={content_type}, content={content[:50]}...")
        return True
        
    except Exception as e:
        logger.exception(f"Error adding session memory to vectorstore: {e}")
        return False


def search_session_memory(
    session_id: str,
    query: str,
    limit: int = 10,
    content_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    从向量数据库搜索会话记忆（语义搜索）
    
    Args:
        session_id: 会话ID
        query: 搜索查询
        limit: 返回结果数量
        content_type: 内容类型过滤（可选）
    
    Returns:
        搜索结果列表
    """
    try:
        if not config.ENABLE_VECTOR_STORAGE:
            logger.info("Vector storage is disabled")
            return []
        
        if not query or not query.strip():
            logger.warning("Empty query provided to search_session_memory")
            query = " "  # 使用空格作为查询
        
        from utils.llm import generate_embedding
        
        # 生成查询向量
        query_embedding = generate_embedding(query)
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        # 构建过滤条件
        where_filter = {
            "$and": [
                {"source": "session_memory"},
                {"session_id": session_id}
            ]
        }
        
        # 如果指定了内容类型，添加过滤
        if content_type:
            where_filter["$and"].append({"content_type": content_type})
        
        logger.info(f"Searching session memory with filter: {where_filter}")
        
        # 执行查询
        collection = get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter
        )
        
        logger.info(f"ChromaDB query returned {len(results.get('documents', [[]])[0]) if results and results.get('documents') else 0} documents")
        
        # 格式化结果
        formatted_results = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": metadata,
                    "distance": results['distances'][0][i] if results['distances'] else None,
                    "context_type": metadata.get('content_type', 'general'),
                    "source": "session_memory",
                    "timestamp": metadata.get('timestamp', ''),
                    "session_id": session_id
                })
        
        return formatted_results
        
    except Exception as e:
        logger.exception(f"Error searching session memory: {e}")
        return []

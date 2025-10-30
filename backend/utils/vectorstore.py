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

"""
查看向量数据库内容的工具脚本
"""

import sys
from pathlib import Path

# 添加项目路径
_backend_dir = Path(__file__).parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

import json
from utils.vectorstore import get_collection, get_chroma_client
from utils.helpers import get_logger
import config

logger = get_logger(__name__)


def view_vectorstore(limit: int = None, show_content: bool = True):
    """
    查看向量数据库中的所有内容
    
    Args:
        limit: 限制显示的数量，None 表示显示全部
        show_content: 是否显示文档内容（内容可能很长）
    """
    try:
        collection = get_collection()
        
        # 获取总数
        count = collection.count()
        print(f"\n{'='*60}")
        print(f"向量数据库统计信息")
        print(f"{'='*60}")
        print(f"集合名称: {config.CHROMA_COLLECTION_NAME}")
        print(f"总文档数: {count}")
        print(f"{'='*60}\n")
        
        if count == 0:
            print("向量数据库为空，没有存储任何内容。")
            return
        
        # 获取所有数据
        if limit:
            # 使用 peek 查看前 N 条
            results = collection.peek(limit=limit)
            print(f"显示前 {limit} 条记录:\n")
        else:
            # 获取所有数据
            results = collection.get()
            print(f"显示所有 {count} 条记录:\n")
        
        # 解析结果
        ids = results.get('ids', [])
        documents = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        if not ids:
            print("没有找到任何记录。")
            return
        
        # 按 web_data_id 分组统计
        web_data_stats = {}
        for i, metadata in enumerate(metadatas):
            web_data_id = metadata.get('web_data_id')
            if web_data_id:
                if web_data_id not in web_data_stats:
                    web_data_stats[web_data_id] = {
                        'title': metadata.get('title', 'Unknown'),
                        'url': metadata.get('url', ''),
                        'chunks_count': 0,
                        'chunks': []
                    }
                web_data_stats[web_data_id]['chunks_count'] += 1
                web_data_stats[web_data_id]['chunks'].append({
                    'id': ids[i],
                    'chunk_index': metadata.get('chunk_index'),
                    'content_preview': documents[i][:100] if documents[i] else ''
                })
        
        # 显示统计信息
        print(f"\n{'='*60}")
        print(f"按网页数据分组统计")
        print(f"{'='*60}")
        for web_data_id, stats in sorted(web_data_stats.items()):
            print(f"\n📄 Web Data ID: {web_data_id}")
            print(f"   标题: {stats['title']}")
            print(f"   URL: {stats['url']}")
            print(f"   分块数量: {stats['chunks_count']}")
        
        # 显示详细信息
        if show_content:
            print(f"\n{'='*60}")
            print(f"详细信息")
            print(f"{'='*60}")
            
            for i, doc_id in enumerate(ids):
                print(f"\n--- 记录 {i+1}/{len(ids)} ---")
                print(f"ID: {doc_id}")
                
                if i < len(metadatas):
                    metadata = metadatas[i]
                    print(f"元数据:")
                    for key, value in metadata.items():
                        if key not in ['tags']:  # tags 是 JSON 字符串，稍后单独处理
                            print(f"  {key}: {value}")
                    
                    # 处理 tags
                    if 'tags' in metadata:
                        try:
                            tags = json.loads(metadata['tags'])
                            print(f"  tags: {tags}")
                        except:
                            print(f"  tags: {metadata['tags']}")
                
                if i < len(documents) and documents[i]:
                    content = documents[i]
                    if show_content:
                        print(f"内容预览 (前200字符):")
                        print(f"  {content[:200]}...")
                        if len(content) > 200:
                            print(f"  ... (总长度: {len(content)} 字符)")
                    else:
                        print(f"内容长度: {len(content)} 字符")
        
    except Exception as e:
        logger.exception(f"查看向量数据库时出错: {e}")
        print(f"\n错误: {e}")


def view_by_web_data_id(web_data_id: int):
    """
    查看特定 web_data_id 的所有分块
    
    Args:
        web_data_id: 网页数据ID
    """
    try:
        collection = get_collection()
        
        # 根据 web_data_id 过滤
        results = collection.get(
            where={"web_data_id": web_data_id}
        )
        
        ids = results.get('ids', [])
        documents = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        if not ids:
            print(f"\n未找到 web_data_id={web_data_id} 的任何记录。")
            return
        
        print(f"\n{'='*60}")
        print(f"Web Data ID: {web_data_id}")
        print(f"找到 {len(ids)} 个分块")
        print(f"{'='*60}\n")
        
        # 显示标题和URL（从第一个分块的元数据中获取）
        if metadatas:
            first_meta = metadatas[0]
            print(f"标题: {first_meta.get('title', 'Unknown')}")
            print(f"URL: {first_meta.get('url', '')}")
            print()
        
        # 按 chunk_index 排序显示
        indexed_chunks = []
        for i, metadata in enumerate(metadatas):
            chunk_index = metadata.get('chunk_index', i)
            indexed_chunks.append({
                'index': chunk_index,
                'id': ids[i],
                'content': documents[i] if i < len(documents) else '',
                'metadata': metadata
            })
        
        indexed_chunks.sort(key=lambda x: x['index'])
        
        for chunk in indexed_chunks:
            print(f"\n--- 分块 {chunk['index']} ---")
            print(f"ID: {chunk['id']}")
            print(f"内容 (前300字符):")
            print(f"{chunk['content'][:300]}...")
            if len(chunk['content']) > 300:
                print(f"... (总长度: {len(chunk['content'])} 字符)")
        
    except Exception as e:
        logger.exception(f"查看特定 web_data_id 时出错: {e}")
        print(f"\n错误: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="查看向量数据库内容")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制显示的数量（默认显示全部）"
    )
    parser.add_argument(
        "--no-content",
        action="store_true",
        help="不显示文档内容（只显示元数据）"
    )
    parser.add_argument(
        "--web-data-id",
        type=int,
        default=None,
        help="查看特定 web_data_id 的所有分块"
    )
    
    args = parser.parse_args()
    
    if args.web_data_id:
        view_by_web_data_id(args.web_data_id)
    else:
        view_vectorstore(limit=args.limit, show_content=not args.no_content)

"""
上传接口路由
"""

import os
import json
import tempfile
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request
from werkzeug.utils import secure_filename
import config
from utils.helpers import convert_resp, auth_required, allowed_file, get_logger
from utils.db import insert_screenshot, insert_web_data
from utils.llm import analyze_web_content, summarize_content, extract_keywords, generate_embeddings
from utils.vectorstore import add_web_data_to_vectorstore, chunk_text

logger = get_logger(__name__)

upload_bp = Blueprint('upload', __name__, url_prefix='/api')


@upload_bp.route('/upload_screenshot', methods=['POST'])
@auth_required
def upload_screenshot():
    """
    上传截图
    接收图片文件并保存
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return convert_resp(code=400, status=400, message="未找到上传文件")
        
        file = request.files['file']
        if file.filename == '':
            return convert_resp(code=400, status=400, message="未选择文件")
        
        # 验证文件类型
        if not allowed_file(file.filename, config.ALLOWED_IMAGE_EXTENSIONS):
            return convert_resp(code=400, status=400, message="只支持图片文件")
        
        # 获取其他参数
        window = request.form.get('window', 'unknown')
        source = request.form.get('source', 'upload')
        
        # 生成安全的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{original_filename}"
        
        # 保存文件
        file_path = config.SCREENSHOT_DIR / filename
        file.save(str(file_path))
        
        # 记录到数据库
        screenshot_id = insert_screenshot(
            path=str(file_path),
            window=window,
            source=source,
            create_time=datetime.now()
        )
        
        logger.info(f"Screenshot uploaded successfully: {filename}, id: {screenshot_id}")
        
        return convert_resp(
            message="图片上传成功",
            data={
                "screenshot_id": screenshot_id,
                "filename": filename,
                "path": str(file_path)
            }
        )
        
    except Exception as e:
        logger.exception(f"Error uploading screenshot: {e}")
        return convert_resp(code=500, status=500, message=f"上传失败: {str(e)}")


@upload_bp.route('/upload_web_data', methods=['POST'])
@auth_required
def upload_web_data():
    """
    上传网页数据（带 LLM 分析和向量存储）
    接收 JSON 格式的网页数据，进行智能处理
    
    处理流程：
    1. 验证数据
    2. 创建临时文件
    3. LLM 分析内容（可选）
    4. 存入 SQLite 数据库
    5. 存入向量数据库（可选）
    """
    temp_file_path = None
    
    try:
        # 获取 JSON 数据
        data = request.get_json()
        
        if not data:
            return convert_resp(code=400, status=400, message="请求体不能为空")
        
        # 验证必需字段
        title = data.get('title')
        url = data.get('url')
        content = data.get('content')
        
        if not title:
            return convert_resp(code=400, status=400, message="标题不能为空")
        
        if not content:
            return convert_resp(code=400, status=400, message="内容不能为空")
        
        # 获取可选字段
        source = data.get('source', 'web_crawler')
        tags = data.get('tags', [])
        metadata = data.get('metadata', {})
        
        logger.info(f"[upload_web_data] Processing: title={title}, url={url}")
        
        # 1. 将内容转换为字符串（用于 LLM 处理）
        if isinstance(content, dict):
            content_str = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            content_str = str(content)
        
        # 2. 创建临时文件保存内容
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
            temp_file.write(content_str)
            temp_file_path = temp_file.name
        
        logger.info(f"[upload_web_data] Created temp file: {temp_file_path}")
        
        # 3. LLM 分析内容（如果启用）
        llm_analysis = None
        if config.ENABLE_LLM_PROCESSING:
            try:
                logger.info("[upload_web_data] Starting LLM analysis...")
                llm_analysis = analyze_web_content(
                    title=title,
                    url=url or "",
                    content=content_str
                )
                
                if llm_analysis:
                    logger.info(f"[upload_web_data] LLM analysis completed: {llm_analysis}")
                    
                    # 将 LLM 分析结果添加到元数据
                    metadata['llm_analysis'] = llm_analysis
                    
                    # 从分析结果中提取标签（如果没有提供标签）
                    if not tags and llm_analysis.get('keywords'):
                        tags = llm_analysis['keywords']
                else:
                    logger.info("[upload_web_data] LLM analysis returned no results")
                    
            except Exception as e:
                logger.warning(f"[upload_web_data] LLM analysis failed: {e}, continuing without it")
        
        # 4. 构建完整的元数据
        full_metadata = {
            "url": url,
            "source": source,
            "tags": tags,
            "content_type": "web_data",
            "crawled_at": datetime.now().isoformat(),
            "temp_file_path": temp_file_path,
        }
        full_metadata.update(metadata)
        
        # 5. 存入 SQLite 数据库
        web_data_id = insert_web_data(
            title=title,
            url=url,
            content=content,
            source=source,
            tags=tags,
            metadata=full_metadata
        )
        
        logger.info(f"[upload_web_data] Saved to database: web_data_id={web_data_id}")
        
        # 6. 存入向量数据库（如果启用）
        vector_success = False
        if config.ENABLE_VECTOR_STORAGE:
            try:
                logger.info("[upload_web_data] Adding to vector store...")
                
                # 准备嵌入函数（仅当有 EMBEDDING_API_KEY 时使用 OpenAI Embeddings）
                embedding_function = None
                if config.EMBEDDING_API_KEY:
                    def embedding_function(texts):
                        embeddings = generate_embeddings(texts)
                        return embeddings if embeddings else None
                    logger.info("[upload_web_data] Using OpenAI embeddings")
                else:
                    logger.info("[upload_web_data] Using ChromaDB default embeddings (sentence-transformers)")
                
                vector_success = add_web_data_to_vectorstore(
                    web_data_id=web_data_id,
                    title=title,
                    url=url or "",
                    content=content_str,
                    source=source,
                    tags=tags,
                    metadata=metadata,
                    embedding_function=embedding_function
                )
                
                if vector_success:
                    logger.info(f"[upload_web_data] Added to vector store successfully")
                else:
                    logger.warning(f"[upload_web_data] Failed to add to vector store")
                    
            except Exception as e:
                logger.warning(f"[upload_web_data] Vector storage failed: {e}, continuing without it")
        
        # 7. 构建响应数据
        response_data = {
            "web_data_id": web_data_id,
            "title": title,
            "url": url,
            "processed": {
                "llm_analysis": llm_analysis is not None,
                "vector_storage": vector_success,
                "temp_file": temp_file_path
            }
        }
        
        # 如果有 LLM 分析结果，也返回
        if llm_analysis:
            response_data["analysis"] = llm_analysis
        
        logger.info(f"[upload_web_data] Processing completed for: {title}")
        
        return convert_resp(
            message=f"网页数据上传并处理成功: {title}",
            data=response_data
        )
        
    except Exception as e:
        logger.exception(f"Error uploading web data: {e}")
        
        # 清理临时文件
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
                logger.info(f"Cleaned up temp file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temp file: {cleanup_error}")
        
        return convert_resp(code=500, status=500, message=f"上传失败: {str(e)}")

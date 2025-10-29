"""
辅助工具函数
"""

import json
import logging
from functools import wraps
from typing import List, Dict, Any
from flask import request, jsonify
import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_logger(name):
    """获取日志记录器"""
    return logging.getLogger(name)


def convert_resp(code=200, status=200, message="success", data=None):
    """
    统一响应格式
    
    Args:
        code: 业务代码
        status: HTTP状态码
        message: 消息
        data: 数据
    """
    response = {
        "code": code,
        "message": message
    }
    if data is not None:
        response["data"] = data
    
    return jsonify(response), status


def auth_required(f):
    """
    认证装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果未配置 AUTH_TOKEN，则跳过认证
        if not config.AUTH_TOKEN:
            return f(*args, **kwargs)
        
        # 从请求头获取 token
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return convert_resp(code=401, status=401, message="Missing authorization token")
        
        # 验证 token
        try:
            token = auth_header.replace('Bearer ', '')
            if token != config.AUTH_TOKEN:
                return convert_resp(code=401, status=401, message="Invalid token")
        except Exception as e:
            return convert_resp(code=401, status=401, message=f"Authorization failed: {str(e)}")
        
        return f(*args, **kwargs)
    
    return decorated_function


def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量
    
    简单估算规则：
    - 英文：约 4 个字符 = 1 token
    - 中文：约 1.5 个字符 = 1 token
    - 这是一个粗略估算，实际值可能有±20%的误差
    
    Args:
        text: 要估算的文本
    
    Returns:
        估算的 token 数量
    """
    if not text:
        return 0
    
    # 统计中文字符数量
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    # 统计其他字符数量
    other_chars = len(text) - chinese_chars
    
    # 估算 token：中文按 1.5 字/token，英文按 4 字/token
    estimated_tokens = int(chinese_chars / 1.5 + other_chars / 4)
    
    return estimated_tokens


def truncate_web_data_by_tokens(
    web_data: List[Dict[str, Any]], 
    max_tokens: int,
    content_field: str = 'content'
) -> List[Dict[str, Any]]:
    """
    根据 token 限制动态截取 web_data 列表
    
    策略：
    1. 优先保留更多条目（降低每条内容长度）
    2. 为每条数据的元数据（title, url, tags 等）预留 token
    3. 剩余 token 平均分配给内容字段
    
    Args:
        web_data: 网页数据列表
        max_tokens: 最大允许的 token 数
        content_field: 内容字段名称（默认 'content'）
    
    Returns:
        截取后的网页数据列表
    """
    if not web_data:
        return []
    
    logger = get_logger(__name__)
    
    # 1. 为每条数据的元数据预留 token（title、url、tags 等）
    METADATA_TOKENS_PER_ITEM = 100  # 每条数据的元数据约占 100 tokens
    
    # 2. 计算可用于内容的 token 数
    num_items = len(web_data)
    metadata_total_tokens = num_items * METADATA_TOKENS_PER_ITEM
    
    if metadata_total_tokens >= max_tokens:
        # 如果元数据就超过限制，减少条目数量
        max_items = max(1, max_tokens // METADATA_TOKENS_PER_ITEM)
        web_data = web_data[:max_items]
        num_items = len(web_data)
        metadata_total_tokens = num_items * METADATA_TOKENS_PER_ITEM
        logger.warning(f"Too many items, reduced to {num_items} items")
    
    content_tokens_available = max_tokens - metadata_total_tokens
    
    # 3. 平均分配给每条内容
    tokens_per_content = max(50, content_tokens_available // num_items)  # 每条内容至少 50 tokens
    
    # 4. Token 转换为字符数（保守估计：1 token ≈ 2 字符）
    max_chars_per_content = tokens_per_content * 2
    
    logger.info(f"Truncating {num_items} web_data items, max {max_chars_per_content} chars per content")
    
    # 5. 截取每条数据
    truncated_data = []
    for item in web_data:
        truncated_item = {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "source": item.get("source", ""),
            "tags": item.get("tags", []),
            "create_time": item.get("create_time", "")
        }
        
        # 如果有 id 字段，保留它
        if "id" in item:
            truncated_item["id"] = item["id"]
        
        # 截取内容
        content = item.get(content_field, "")
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        
        if len(content) > max_chars_per_content:
            truncated_item[content_field] = content[:max_chars_per_content] + "..."
        else:
            truncated_item[content_field] = content
        
        truncated_data.append(truncated_item)
    
    return truncated_data


def calculate_available_context_tokens(
    prompt_type: str,
    additional_data_tokens: int = 0
) -> int:
    """
    计算可用于上下文数据的 token 数量
    
    Args:
        prompt_type: prompt 类型 ('tip', 'todo', 'activity', 'report')
        additional_data_tokens: 额外数据占用的 token（如 tips、todos 列表）
    
    Returns:
        可用于上下文数据的 token 数量
    """
    # 从配置获取总限制
    max_input_tokens = config.LLM_MAX_INPUT_TOKENS
    
    # 获取 system prompt 占用的 token
    system_tokens = config.SYSTEM_PROMPT_TOKENS.get(prompt_type, 2000)
    
    # 用户消息保留的 token
    user_reserve_tokens = config.USER_MESSAGE_RESERVE_TOKENS
    
    # 计算可用 token
    available_tokens = max_input_tokens - system_tokens - user_reserve_tokens - additional_data_tokens
    
    # 确保至少有 500 tokens
    available_tokens = max(500, available_tokens)
    
    logger = get_logger(__name__)
    logger.info(
        f"Token allocation for '{prompt_type}': "
        f"max={max_input_tokens}, system={system_tokens}, "
        f"reserve={user_reserve_tokens}, additional={additional_data_tokens}, "
        f"available={available_tokens}"
    )
    
    return available_tokens

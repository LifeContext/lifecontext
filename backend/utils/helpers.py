"""
辅助工具函数
"""

import logging
from functools import wraps
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

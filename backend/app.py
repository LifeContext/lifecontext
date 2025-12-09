"""
LifeContext Flask 应用主入口
"""

import os
import sys
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import config
from utils.db import init_db
from utils.helpers import get_logger
from routes.upload import upload_bp
from routes.generation import generation_bp
from routes.agent import agent_bp
from routes.events import events_bp
from routes.settings import settings_bp
from routes.url_blacklist import url_blacklist_bp

logger = get_logger(__name__)

# 获取前端静态文件目录
def get_frontend_dist_path():
    """获取前端 dist 目录路径，兼容开发模式和打包模式"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后：可执行文件在 backend/ 子目录，需要向上一级
        # 目录结构: LifeContext-Portable/backend/LifeContextBackend.exe
        #          LifeContext-Portable/frontend/dist/
        base_dir = Path(sys.executable).parent.parent
    else:
        # 开发模式：backend 目录的父目录（项目根目录）
        base_dir = Path(__file__).parent.parent
    
    # 前端 dist 目录路径
    frontend_dist = base_dir / "frontend" / "dist"
    
    if frontend_dist.exists():
        logger.info(f"✅ Frontend dist found: {frontend_dist}")
        return str(frontend_dist)
    else:
        logger.warning(f"⚠️ Frontend dist not found: {frontend_dist}")
        return None

FRONTEND_DIST_PATH = get_frontend_dist_path()

# 调度器实例（延迟导入避免循环依赖）
_scheduler = None


def create_app():
    """创建 Flask 应用"""
    app = Flask(__name__)
    
    # 加载配置
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    
    # 启用 CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 初始化数据库
    init_db()
    
    # 初始化定时任务（如果启用）
    if config.ENABLE_SCHEDULER:
        try:
            from scheduler import init_scheduler
            global _scheduler
            _scheduler = init_scheduler()
            logger.info("✅ Scheduler enabled and started")
        except Exception as e:
            logger.error(f"⚠️ Failed to start scheduler: {e}")
    else:
        logger.info("ℹ️ Scheduler disabled in config")
    
    # 注册蓝图
    app.register_blueprint(upload_bp)
    app.register_blueprint(generation_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(url_blacklist_bp)
    
    # 健康检查端点
    @app.route('/health', methods=['GET'])
    def health_check():
        scheduler_status = "enabled" if config.ENABLE_SCHEDULER else "disabled"
        return jsonify({
            "status": "healthy",
            "service": "lifecontext-api",
            "version": "1.0.0",
            "scheduler": scheduler_status
        })
    
    # 调度器状态查看
    @app.route('/api/scheduler/status', methods=['GET'])
    def scheduler_status():
        if not config.ENABLE_SCHEDULER:
            return jsonify({
                "enabled": False,
                "message": "调度器未启用"
            })
        
        try:
            from scheduler import get_scheduled_jobs
            jobs = get_scheduled_jobs()
            return jsonify({
                "enabled": True,
                "jobs_count": len(jobs),
                "jobs": jobs
            })
        except Exception as e:
            return jsonify({
                "enabled": False,
                "error": str(e)
            }), 500
    
    # ========== 前端静态文件服务 ==========
    # 注意：静态文件路由必须在最后注册，避免拦截 API 路由
    if FRONTEND_DIST_PATH:
        # 根路径 - 提供前端首页
        @app.route('/', methods=['GET'])
        def index():
            index_path = os.path.join(FRONTEND_DIST_PATH, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(FRONTEND_DIST_PATH, 'index.html')
            else:
                logger.error(f"❌ index.html not found at: {index_path}")
                return jsonify({
                    "error": "Frontend index.html not found",
                    "path": index_path
                }), 500
        
        # SPA 路由支持：对于前端路由（如 /chat, /timeline 等），返回 index.html
        # 这个路由必须在最后注册，避免拦截 API 路由
        @app.route('/<path:path>')
        def serve_spa(path):
            # 确保不会拦截 API 路径和特殊端点
            if path.startswith('api/') or path == 'health':
                # 如果走到这里，说明 API 路由没有匹配，返回 404
                return jsonify({"code": 404, "message": "接口不存在"}), 404
            
            # 检查是否是静态文件（如 assets/*, index.css 等）
            file_path = os.path.join(FRONTEND_DIST_PATH, path)
            if os.path.isfile(file_path):
                return send_from_directory(FRONTEND_DIST_PATH, path)
            
            # 对于 SPA 路由（如 /chat, /timeline 等），返回 index.html
            index_path = os.path.join(FRONTEND_DIST_PATH, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(FRONTEND_DIST_PATH, 'index.html')
            else:
                logger.error(f"❌ index.html not found at: {index_path}")
                return jsonify({
                    "error": "Frontend index.html not found",
                    "path": index_path
                }), 500
        
        logger.info(f"✅ Frontend static file serving enabled at: {FRONTEND_DIST_PATH}")
    else:
        # 没有前端文件时，显示 API 信息
        @app.route('/', methods=['GET'])
        def index():
            return jsonify({
                "service": "LifeContext API",
                "version": "1.0.0",
                "message": "Frontend not found. Please ensure frontend/dist exists.",
                "endpoints": {
                    "upload": [
                        "POST /api/upload_web_data",
                        "POST /api/upload_screenshot"
                    ],
                    "generation": [
                        "GET /api/generation/reports",
                        "GET /api/generation/todos",
                        "POST /api/generation/todos",
                        "GET /api/generation/activities",
                        "GET /api/generation/tips",
                        "PATCH /api/generation/todos/{todo_id}",
                        "DELETE /api/generation/todos/{todo_id}",
                        "POST /api/generation/generate/report",
                        "POST /api/generation/generate/activity",
                        "POST /api/generation/generate/tips",
                        "POST /api/generation/generate/todos"
                    ],
                    "agent": [
                        "POST /api/agent/chat",
                        "POST /api/agent/chat/stream",
                        "POST /api/agent/resume/{workflow_id}",
                        "GET /api/agent/state/{workflow_id}",
                        "DELETE /api/agent/cancel/{workflow_id}",
                        "POST /api/agent/optimize_prompt",
                        "GET /api/agent/test"
                    ],
                    "events": [
                        "GET /api/events/fetch",
                        "GET /api/events/status",
                        "POST /api/events/publish"
                    ],
                    "url_blacklist": [
                        "GET /api/url-blacklist",
                        "POST /api/url-blacklist",
                        "DELETE /api/url-blacklist/{id}"
                    ]
                }
            })
    
    # 错误处理
    # 注意：404 处理器应该在静态文件路由之后注册
    @app.errorhandler(404)
    def not_found(error):
        # 如果是 API 路径，返回 JSON 错误
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({
                "code": 404,
                "message": "接口不存在"
            }), 404
        
        # 对于非 API 路径，如果有前端文件，尝试返回 index.html（SPA 路由）
        if FRONTEND_DIST_PATH:
            try:
                return send_from_directory(FRONTEND_DIST_PATH, 'index.html')
            except Exception:
                pass
        
        # 否则返回 JSON 错误
        return jsonify({
            "code": 404,
            "message": "资源不存在"
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.exception(f"Internal server error: {error}")
        return jsonify({
            "code": 500,
            "message": "服务器内部错误"
        }), 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            "code": 413,
            "message": "上传文件过大"
        }), 413
    
    logger.info("Flask application created successfully")
    return app


if __name__ == '__main__':
    app = create_app()
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )

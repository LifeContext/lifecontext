"""
LifeContext Flask 应用主入口
"""

from flask import Flask, jsonify
from flask_cors import CORS
import config
from utils.db import init_db
from utils.helpers import get_logger
from routes.upload import upload_bp
from routes.generation import generation_bp
from routes.agent import agent_bp
from routes.events import events_bp

logger = get_logger(__name__)

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
    
    # 根路径
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            "service": "LifeContext API",
            "version": "1.0.0",
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
                    "GET /api/agent/test"
                ],
                "events": [
                    "GET /api/events/fetch",
                    "GET /api/events/status",
                    "POST /api/events/publish"
                ]
            }
        })
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "code": 404,
            "message": "接口不存在"
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

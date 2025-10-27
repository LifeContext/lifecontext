"""
事件推送路由 - 缓存版本，支持获取和清除机制
"""

from flask import Blueprint, jsonify, request
from utils.event_manager import get_event_manager, EventType
from utils.helpers import get_logger

logger = get_logger(__name__)

events_bp = Blueprint('events', __name__, url_prefix='/api/events')


@events_bp.route('/fetch', methods=['GET'])
def fetch_and_clear_events():
    """
    获取并清空缓存事件 - 核心API
    
    返回所有缓存事件并清空缓存。
    前端应该定期调用此接口以获取新事件。
    """
    try:
        event_manager = get_event_manager()
        events = event_manager.fetch_and_clear_events()

        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "events": events,
                "count": len(events)
            }
        })

    except Exception as e:
        logger.exception(f"Failed to fetch events: {e}")
        return jsonify({
            "code": 500,
            "message": f"Failed to fetch events: {str(e)}"
        }), 500


@events_bp.route('/status', methods=['GET'])
def get_event_status():
    """获取事件缓存状态"""
    try:
        event_manager = get_event_manager()
        status = event_manager.get_cache_status()

        return jsonify({
            "code": 200,
            "message": "success",
            "data": {
                "event_system_status": "active",
                **status
            }
        })

    except Exception as e:
        logger.exception(f"Failed to get event status: {e}")
        return jsonify({
            "code": 500,
            "message": f"Failed to get event status: {str(e)}"
        }), 500


@events_bp.route('/publish', methods=['POST'])
def publish_event():
    """
    发布事件（主要用于测试）
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "code": 400,
                "message": "Request body is required"
            }), 400
        
        event_type_str = data.get('event_type')
        event_data = data.get('data', {})
        
        if not event_type_str:
            return jsonify({
                "code": 400,
                "message": "event_type is required"
            }), 400
        
        # 验证事件类型
        try:
            event_type = EventType(event_type_str)
        except ValueError:
            return jsonify({
                "code": 400,
                "message": f"Invalid event type: {event_type_str}",
                "supported_types": [t.value for t in EventType]
            }), 400

        # 发布事件
        event_manager = get_event_manager()
        event_id = event_manager.publish_event(
            event_type=event_type,
            data=event_data
        )

        return jsonify({
            "code": 200,
            "message": "Event published successfully",
            "data": {
                "event_id": event_id,
                "event_type": event_type_str
            }
        })

    except Exception as e:
        logger.exception(f"Failed to publish event: {e}")
        return jsonify({
            "code": 500,
            "message": f"Failed to publish event: {str(e)}"
        }), 500

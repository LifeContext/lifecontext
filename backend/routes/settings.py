"""
设置路由
提供获取和更新系统设置的API
"""

from flask import Blueprint, jsonify, request
from utils.db import get_setting, set_setting, get_all_settings
import config
from utils.helpers import get_logger

logger = get_logger(__name__)

settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')


@settings_bp.route('', methods=['GET'])
def get_settings():
    """获取所有设置"""
    try:
        settings = get_all_settings()
        
        # 格式化返回
        result = {
            'tips_interval_minutes': int(settings.get('tips_interval_minutes', {}).get('value', '60')),
            'todo_interval_minutes': int(settings.get('todo_interval_minutes', {}).get('value', '30')),
            'daily_report_hour': int(settings.get('daily_report_hour', {}).get('value', '8')),
            'daily_report_minute': int(settings.get('daily_report_minute', {}).get('value', '0')),
            'prompt_language': settings.get('prompt_language', {}).get('value', config.PROMPT_LANGUAGE)
        }
        
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Error getting settings: {e}")
        return jsonify({
            'error': '获取设置失败',
            'message': str(e)
        }), 500


@settings_bp.route('', methods=['PUT'])
def update_settings():
    """更新设置"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': '请求体不能为空'
            }), 400
        
        # 验证并更新 tips_interval_minutes
        if 'tips_interval_minutes' in data:
            tips_interval = data['tips_interval_minutes']
            if not isinstance(tips_interval, int):
                return jsonify({
                    'error': 'tips_interval_minutes 必须是整数'
                }), 400
            # 限制只能是15、30或60分钟
            if tips_interval not in [15, 30, 60]:
                return jsonify({
                    'error': 'tips_interval_minutes 只能是15、30或60分钟'
                }), 400
            set_setting('tips_interval_minutes', str(tips_interval), 'Tips生成间隔（分钟）')
        
        # 验证并更新 todo_interval_minutes
        if 'todo_interval_minutes' in data:
            todo_interval = data['todo_interval_minutes']
            if not isinstance(todo_interval, int) or todo_interval < 1:
                return jsonify({
                    'error': 'todo_interval_minutes 必须是大于0的整数'
                }), 400
            set_setting('todo_interval_minutes', str(todo_interval), 'Todo生成间隔（分钟）')
        
        # 验证并更新 daily_report_hour
        if 'daily_report_hour' in data:
            hour = data['daily_report_hour']
            if not isinstance(hour, int) or hour < 0 or hour > 23:
                return jsonify({
                    'error': 'daily_report_hour 必须是0-23之间的整数'
                }), 400
            set_setting('daily_report_hour', str(hour), 'Daily Report生成时间（小时，0-23）')
        
        # 验证并更新 daily_report_minute
        if 'daily_report_minute' in data:
            minute = data['daily_report_minute']
            if not isinstance(minute, int) or minute < 0 or minute > 59:
                return jsonify({
                    'error': 'daily_report_minute 必须是0-59之间的整数'
                }), 400
            set_setting('daily_report_minute', str(minute), 'Daily Report生成时间（分钟，0-59）')

        # 验证并更新 prompt_language
        if 'prompt_language' in data:
            language = data['prompt_language']
            if not isinstance(language, str):
                return jsonify({
                    'error': 'prompt_language 必须是字符串'
                }), 400
            normalized = language.lower()
            if normalized not in {'zh', 'en'}:
                return jsonify({
                    'error': 'prompt_language 只支持 zh 或 en'
                }), 400
            set_setting('prompt_language', normalized, '提示词语言 (zh/en)')
        
        # 更新调度器（延迟导入避免循环依赖）
        try:
            from scheduler import update_scheduler_settings
            update_scheduler_settings()
        except Exception as e:
            logger.warning(f"Failed to update scheduler settings: {e}")
        
        # 返回更新后的设置
        settings = get_all_settings()
        result = {
            'tips_interval_minutes': int(settings.get('tips_interval_minutes', {}).get('value', '60')),
            'todo_interval_minutes': int(settings.get('todo_interval_minutes', {}).get('value', '30')),
            'daily_report_hour': int(settings.get('daily_report_hour', {}).get('value', '8')),
            'daily_report_minute': int(settings.get('daily_report_minute', {}).get('value', '0')),
            'prompt_language': settings.get('prompt_language', {}).get('value', config.PROMPT_LANGUAGE)
        }
        
        return jsonify(result)
    except Exception as e:
        logger.exception(f"Error updating settings: {e}")
        return jsonify({
            'error': '更新设置失败',
            'message': str(e)
        }), 500


"""
内容生成接口路由
"""

import asyncio
import json
from datetime import datetime, timedelta
from flask import Blueprint, request
import config
from utils.helpers import convert_resp, auth_required, get_logger
from utils.db import (
    get_reports, get_todos, get_activities, get_tips,
    update_todo_status, insert_report, insert_activity, insert_tip, insert_todo
)
from utils.generation import (
    create_activity_report,
    create_activity_record,
    generate_smart_tips,
    generate_task_list
)
from utils.event_manager import EventType, publish_event

logger = get_logger(__name__)

generation_bp = Blueprint('generation', __name__, url_prefix='/api/generation')


@generation_bp.route('/reports', methods=['GET'])
@auth_required
def get_debug_reports():
    """获取报告数据"""
    try:
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        is_deleted = request.args.get('is_deleted', 'false').lower() == 'true'
        
        reports = get_reports(limit=limit, offset=offset, is_deleted=is_deleted)
        
        logger.info(f"Retrieved {len(reports)} reports")
        
        return convert_resp(
            data={
                "reports": reports,
                "total": len(reports)
            }
        )
        
    except Exception as e:
        logger.exception(f"Error getting reports: {e}")
        return convert_resp(code=500, status=500, message=f"获取报告失败: {str(e)}")


@generation_bp.route('/todos', methods=['GET'])
@auth_required
def get_debug_todos():
    """获取待办事项数据"""
    try:
        status = request.args.get('status', type=int)
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        todos = get_todos(status=status, limit=limit, offset=offset)
        
        logger.info(f"Retrieved {len(todos)} todos")
        
        return convert_resp(
            data={
                "todos": todos,
                "total": len(todos)
            }
        )
        
    except Exception as e:
        logger.exception(f"Error getting todos: {e}")
        return convert_resp(code=500, status=500, message=f"获取待办事项失败: {str(e)}")


@generation_bp.route('/activities', methods=['GET'])
@auth_required
def get_debug_activities():
    """获取活动记录数据"""
    try:
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        start_time = datetime.fromisoformat(start_time_str) if start_time_str else None
        end_time = datetime.fromisoformat(end_time_str) if end_time_str else None
        
        activities = get_activities(
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        
        # 为每个活动记录添加 url 和 keywords 字段
        for activity in activities:
            # 从 resources 字段中提取 URL 和关键词（如果存在）
            resources = activity.get('resources')
            url = None
            urls = []
            keywords = []
            
            if resources:
                try:
                    if isinstance(resources, str):
                        resources_data = json.loads(resources)
                    else:
                        resources_data = resources
                    
                    # 处理新的 resources 格式：{"urls": [...], "keywords": [...]}
                    if isinstance(resources_data, dict):
                        # 提取 URLs
                        if 'urls' in resources_data and isinstance(resources_data['urls'], list):
                            urls = resources_data['urls']
                            url = urls[0] if urls else None
                        # 兼容旧格式的单个 URL 字段
                        else:
                            url = (resources_data.get('url') or 
                                   resources_data.get('link') or 
                                   resources_data.get('source_url'))
                            if url:
                                urls = [url]
                        
                        # 提取关键词
                        if 'keywords' in resources_data and isinstance(resources_data['keywords'], list):
                            keywords = resources_data['keywords']
                    
                    elif isinstance(resources_data, list) and len(resources_data) > 0:
                        # 如果是列表，取第一个元素的 URL
                        first_item = resources_data[0]
                        if isinstance(first_item, dict):
                            url = (first_item.get('url') or 
                                   first_item.get('link') or 
                                   first_item.get('source_url'))
                            if url:
                                urls = [url]
                except (json.JSONDecodeError, TypeError, KeyError):
                    # 如果解析失败，保持字段为默认值
                    pass
            
            # 添加字段到活动记录
            activity['url'] = url
            activity['urls'] = urls
            activity['keywords'] = keywords
        
        logger.info(f"Retrieved {len(activities)} activities")
        
        return convert_resp(
            data={
                "activities": activities,
                "total": len(activities)
            }
        )
        
    except Exception as e:
        logger.exception(f"Error getting activities: {e}")
        return convert_resp(code=500, status=500, message=f"获取活动记录失败: {str(e)}")


@generation_bp.route('/tips', methods=['GET'])
@auth_required
def get_debug_tips():
    """获取提示数据"""
    try:
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        tips = get_tips(limit=limit, offset=offset)
        
        logger.info(f"Retrieved {len(tips)} tips")
        
        return convert_resp(
            data={
                "tips": tips,
                "total": len(tips)
            }
        )
        
    except Exception as e:
        logger.exception(f"Error getting tips: {e}")
        return convert_resp(code=500, status=500, message=f"获取提示失败: {str(e)}")


@generation_bp.route('/todos/<int:todo_id>', methods=['PATCH'])
@auth_required
def update_debug_todo_status(todo_id):
    """更新待办事项状态"""
    try:
        data = request.get_json(silent=True)
        
        if not data or 'status' not in data:
            return convert_resp(code=400, status=400, message="缺少 status 参数")
        
        status = data['status']
        end_time = datetime.now() if status == 1 else None
        
        success = update_todo_status(todo_id, status, end_time)
        
        if success:
            logger.info(f"Updated todo {todo_id} status to {status}")
            return convert_resp(message="待办事项状态更新成功")
        else:
            return convert_resp(code=404, status=404, message="待办事项不存在")
        
    except Exception as e:
        logger.exception(f"Error updating todo status: {e}")
        return convert_resp(code=500, status=500, message=f"更新失败: {str(e)}")


@generation_bp.route('/generate/report', methods=['POST'])
@auth_required
def manual_generate_report():
    """手动生成报告（智能生成）"""
    try:
        data = request.get_json(silent=True) or {}
        
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not start_time or not end_time:
            now = datetime.now()
            end_time = int(now.timestamp())
            start_time = int((now - timedelta(days=1)).timestamp())
        
        # 使用函数式接口生成报告
        result = asyncio.run(create_activity_report(start_time, end_time))
        
        if result.get('success'):
            report_id = result.get('report_id')
            logger.info(f"Generated report {report_id}")
            
            # 发布事件
            publish_event(
                event_type=EventType.REPORT_GENERATED,
                data={
                    "report_id": str(report_id),
                    "title": "报告已生成",
                    "message": "手动生成的报告已完成",
                    "content": result.get('content', '')[:200],
                    "generated_by": "manual"
                }
            )
            
            return convert_resp(
                message="报告生成成功",
                data=result
            )
        else:
            return convert_resp(
                code=500,
                status=500,
                message=result.get('message', '生成报告失败')
            )
        
    except Exception as e:
        logger.exception(f"Error generating report: {e}")
        return convert_resp(code=500, status=500, message=f"生成报告失败: {str(e)}")


@generation_bp.route('/generate/activity', methods=['POST'])
@auth_required
def manual_generate_activity():
    """手动生成活动记录（智能生成）"""
    try:
        data = request.get_json(silent=True) or {}
        minutes = data.get('minutes', 15)
        
        # 使用函数式接口生成活动记录
        result = asyncio.run(create_activity_record(minutes))
        
        if result.get('success'):
            activity_id = result.get('activity_id')
            logger.info(f"Generated activity {activity_id}")
            
            # 发布事件
            publish_event(
                event_type=EventType.ACTIVITY_GENERATED,
                data={
                    "activity_id": str(activity_id),
                    "title": "活动记录已生成",
                    "message": "手动生成的活动记录已完成",
                    "content": result.get('content', '')[:200],
                    "generated_by": "manual"
                }
            )
            
            return convert_resp(
                message="活动记录生成成功",
                data=result
            )
        else:
            return convert_resp(
                code=500,
                status=500,
                message=result.get('message', '生成活动记录失败')
            )
        
    except Exception as e:
        logger.exception(f"Error generating activity: {e}")
        return convert_resp(code=500, status=500, message=f"生成活动记录失败: {str(e)}")


@generation_bp.route('/generate/tips', methods=['POST'])
@auth_required
def manual_generate_tips():
    """手动生成提示（智能生成）"""
    try:
        data = request.get_json(silent=True) or {}
        lookback_minutes = data.get('lookback_minutes', 60)
        
        # 使用函数式接口生成提示
        result = asyncio.run(generate_smart_tips(lookback_minutes))
        
        if result.get('success'):
            tip_ids = result.get('tip_ids', [])
            tip_count = len(tip_ids)
            logger.info(f"Generated {tip_count} tips")
            
            # 发布事件
            if tip_count > 0:
                publish_event(
                    event_type=EventType.TIP_GENERATED,
                    data={
                        "tip_ids": [str(tid) for tid in tip_ids],
                        "count": tip_count,
                        "title": "智能提示已生成",
                        "message": f"手动生成了 {tip_count} 条智能提示",
                        "generated_by": "manual"
                    }
                )
            
            return convert_resp(
                message="提示生成成功",
                data=result
            )
        else:
            return convert_resp(
                code=500,
                status=500,
                message=result.get('message', '生成提示失败')
            )
        
    except Exception as e:
        logger.exception(f"Error generating tip: {e}")
        return convert_resp(code=500, status=500, message=f"生成提示失败: {str(e)}")


@generation_bp.route('/generate/todos', methods=['POST'])
@auth_required
def manual_generate_todos():
    """手动生成待办事项（智能生成）"""
    try:
        data = request.get_json(silent=True) or {}
        lookback_minutes = data.get('lookback_minutes', 30)
        
        # 使用函数式接口生成待办事项
        result = asyncio.run(generate_task_list(lookback_minutes))
        
        if result.get('success'):
            todo_ids = result.get('todo_ids', [])
            todo_count = len(todo_ids)
            logger.info(f"Generated {todo_count} todos")
            
            # 发布事件
            if todo_count > 0:
                publish_event(
                    event_type=EventType.TODO_GENERATED,
                    data={
                        "todo_ids": [str(tid) for tid in todo_ids],
                        "count": todo_count,
                        "title": "待办任务已生成",
                        "message": f"手动生成了 {todo_count} 个待办任务",
                        "generated_by": "manual"
                    }
                )
            
            return convert_resp(
                message="待办事项生成成功",
                data=result
            )
        else:
            return convert_resp(
                code=500,
                status=500,
                message=result.get('message', '生成待办事项失败')
            )
        
    except Exception as e:
        logger.exception(f"Error generating todo: {e}")
        return convert_resp(code=500, status=500, message=f"生成待办事项失败: {str(e)}")

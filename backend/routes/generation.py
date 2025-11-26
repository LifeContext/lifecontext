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
    update_todo_status, update_todo, delete_todo,
    insert_report, insert_activity, insert_tip, insert_todo,
    get_daily_feeds, get_setting
)
from utils.generation import (
    create_activity_report,
    create_activity_record,
    generate_smart_tips,
    generate_task_list
)
from utils.event_manager import EventType, publish_event

logger = get_logger(__name__)


def _assign_sequential_ids(cards: list) -> list:
    """为 cards 列表按顺序添加或覆盖 id 字段（从1开始）。

    目的：在返回给前端之前统一为每张卡片提供稳定的顺序 id，
    避免在生成端引入复杂的 id 生成或匹配逻辑。
    """
    if not isinstance(cards, list):
        return cards
    for idx, card in enumerate(cards, start=1):
        try:
            if isinstance(card, dict):
                card['id'] = idx
        except Exception:
            # 保持容错，不阻塞整个返回流程
            continue
    return cards

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


@generation_bp.route('/todos', methods=['POST'])
@auth_required
def create_todo():
    """手动创建待办事项"""
    try:
        data = request.get_json()
        
        if not data or 'title' not in data:
            return convert_resp(code=400, status=400, message="缺少必填参数: title")
        
        title = data['title']
        description = data.get('description', '')
        priority = data.get('priority', 0)
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        
        # 验证优先级
        if not isinstance(priority, int) or priority < 0 or priority > 3:
            return convert_resp(code=400, status=400, message="优先级必须是0-3之间的整数")
        
        # 验证标题长度
        if len(title.strip()) < 2:
            return convert_resp(code=400, status=400, message="标题至少需要2个字符")
        
        if len(title) > 200:
            return convert_resp(code=400, status=400, message="标题不能超过200个字符")
        
        # 解析和验证时间
        start_time = None
        end_time = None
        
        if start_time_str:
            try:
                # 支持多种时间格式
                # ISO格式: 2025-10-31T12:00:00
                # 标准格式: 2025-10-31 12:00:00
                if 'T' in start_time_str:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                else:
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return convert_resp(code=400, status=400, message="开始时间格式错误，请使用 'YYYY-MM-DD HH:MM:SS' 或 ISO 格式")
        
        if end_time_str:
            try:
                if 'T' in end_time_str:
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                else:
                    end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return convert_resp(code=400, status=400, message="结束时间格式错误，请使用 'YYYY-MM-DD HH:MM:SS' 或 ISO 格式")
        
        # 验证时间逻辑
        if start_time and end_time:
            if end_time <= start_time:
                return convert_resp(code=400, status=400, message="结束时间必须晚于开始时间")
        
        # 插入待办事项
        todo_id = insert_todo(
            title=title.strip(),
            description=description.strip() if description else "",
            priority=priority,
            start_time=start_time,
            end_time=end_time
        )
        
        logger.info(f"Created todo: ID={todo_id}, title={title}, start_time={start_time}, end_time={end_time}")
        
        # 获取完整的待办信息
        todos = get_todos(limit=1, offset=0)
        created_todo = None
        for todo in todos:
            if todo.get('id') == todo_id:
                created_todo = todo
                break
        
        # 发布事件
        publish_event(
            event_type=EventType.TODO_GENERATED,
            data={
                "todo_ids": [str(todo_id)],
                "count": 1,
                "title": title,
                "message": f"手动创建待办任务: {title}",
                "todos": [created_todo] if created_todo else []
            }
        )
        
        return convert_resp(
            data={
                "todo_id": todo_id,
                "todo": created_todo
            },
            message="待办事项创建成功"
        )
        
    except Exception as e:
        logger.exception(f"Error creating todo: {e}")
        return convert_resp(code=500, status=500, message=f"创建待办事项失败: {str(e)}")


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
    """获取提示数据（按日期分类）"""
    try:
        limit = request.args.get('limit', 100, type=int)  # 默认获取更多，以便按日期分类
        
        # 获取所有tips
        tips = get_tips(limit=limit, offset=0)
        
        # 按日期分类
        tips_by_date = {}
        for tip in tips:
            create_time = tip.get('create_time', '')
            if create_time:
                # 提取日期部分（YYYY-MM-DD）
                try:
                    # 处理不同格式的时间字符串
                    if 'T' in create_time:
                        date_str = create_time.split('T')[0]
                    else:
                        date_str = create_time.split(' ')[0]
                    
                    if date_str not in tips_by_date:
                        tips_by_date[date_str] = []
                    tips_by_date[date_str].append(tip)
                except Exception as e:
                    logger.warning(f"Failed to parse date from create_time '{create_time}': {e}")
                    # 如果解析失败，放到"未知日期"分类
                    if 'unknown' not in tips_by_date:
                        tips_by_date['unknown'] = []
                    tips_by_date['unknown'].append(tip)
            else:
                # 没有时间戳的放到"未知日期"
                if 'unknown' not in tips_by_date:
                    tips_by_date['unknown'] = []
                tips_by_date['unknown'].append(tip)
        
        # 按日期倒序排序（最新的在前）
        sorted_dates = sorted(tips_by_date.keys(), reverse=True)
        if 'unknown' in sorted_dates:
            sorted_dates.remove('unknown')
            sorted_dates.append('unknown')  # 未知日期放到最后
        
        # 构建按日期分类的结果
        grouped_tips = {}
        for date_str in sorted_dates:
            grouped_tips[date_str] = tips_by_date[date_str]
        
        logger.info(f"Retrieved {len(tips)} tips, grouped into {len(grouped_tips)} dates")
        
        return convert_resp(
            data={
                "tips_by_date": grouped_tips,
                "total": len(tips),
                "date_count": len(grouped_tips)
            }
        )
        
    except Exception as e:
        logger.exception(f"Error getting tips: {e}")
        return convert_resp(code=500, status=500, message=f"获取提示失败: {str(e)}")


@generation_bp.route('/todos/<int:todo_id>', methods=['PATCH'])
@auth_required
def update_debug_todo_status(todo_id):
    """更新待办事项（支持更新 title、description、status 等字段）"""
    try:
        data = request.get_json(silent=True)
        
        if not data:
            return convert_resp(code=400, status=400, message="请求体不能为空")
        
        # 提取可更新的字段
        update_fields = {}
        
        if 'title' in data:
            update_fields['title'] = data['title']
        
        if 'description' in data:
            update_fields['description'] = data['description']
        
        if 'status' in data:
            update_fields['status'] = data['status']
            # 如果状态改为完成(1)，自动设置完成时间
            if data['status'] == 1:
                update_fields['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # 如果状态改为未完成(0)，清除完成时间
            elif data['status'] == 0:
                update_fields['end_time'] = None
        
        if 'priority' in data:
            update_fields['priority'] = data['priority']
        
        if not update_fields:
            return convert_resp(code=400, status=400, message="没有可更新的字段")
        
        # 使用通用更新函数
        success = update_todo(todo_id, **update_fields)
        
        if success:
            logger.info(f"Updated todo {todo_id}: {update_fields}")
            return convert_resp(message="待办事项更新成功")
        else:
            return convert_resp(code=404, status=404, message="待办事项不存在")
        
    except Exception as e:
        logger.exception(f"Error updating todo: {e}")
        return convert_resp(code=500, status=500, message=f"更新失败: {str(e)}")


@generation_bp.route('/todos/<int:todo_id>', methods=['DELETE'])
@auth_required
def delete_debug_todo(todo_id):
    """删除待办事项"""
    try:
        success = delete_todo(todo_id)
        
        if success:
            logger.info(f"Deleted todo {todo_id}")
            return convert_resp(message="待办事项删除成功")
        else:
            return convert_resp(code=404, status=404, message="待办事项不存在")
        
    except Exception as e:
        logger.exception(f"Error deleting todo: {e}")
        return convert_resp(code=500, status=500, message=f"删除失败: {str(e)}")


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
            
            # 从数据库获取报告的实际 title
            report_title = "活动报告"
            try:
                reports = get_reports(limit=1, offset=0)
                if reports and len(reports) > 0 and reports[0].get('id') == report_id:
                    report_title = reports[0].get('title', report_title)
            except Exception as e:
                logger.warning(f"Failed to get report title: {e}, using default")
            
            # 发布事件
            publish_event(
                event_type=EventType.REPORT_GENERATED,
                data={
                    "report_id": str(report_id),
                    "title": report_title,  # 使用实际的 title
                    "message": f"手动生成的报告已完成: {report_title}",
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
            activity_title = result.get('title', '活动记录')  # 使用实际的 title
            logger.info(f"Generated activity {activity_id}: {activity_title}")
            
            # 发布事件
            publish_event(
                event_type=EventType.ACTIVITY_GENERATED,
                data={
                    "activity_id": str(activity_id),
                    "title": activity_title,  # 使用实际的 title
                    "message": f"手动生成的活动记录已完成: {activity_title}",
                    "description": result.get('description', '')[:200],
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
            tips = result.get('tips', [])
            tip_count = len(tip_ids)
            logger.info(f"Generated {tip_count} tips")
            
            # 发布事件
            if tip_count > 0:
                # 使用第一个 tip 的 title
                first_tip_title = tips[0].get('title', '智能提示') if tips else '智能提示'
                
                publish_event(
                    event_type=EventType.TIP_GENERATED,
                    data={
                        "tip_ids": [str(tid) for tid in tip_ids],
                        "count": tip_count,
                        "title": first_tip_title if tip_count == 1 else f"{first_tip_title} 等{tip_count}条提示",
                        "message": f"手动生成了 {tip_count} 条智能提示",
                        "tips": tips,  # 包含所有 tips 的完整信息
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
            todos = result.get('todos', [])
            todo_count = len(todo_ids)
            logger.info(f"Generated {todo_count} todos")
            
            # 发布事件
            if todo_count > 0:
                # 使用第一个 todo 的 title
                first_todo_title = todos[0].get('title', '待办任务') if todos else '待办任务'
                
                publish_event(
                    event_type=EventType.TODO_GENERATED,
                    data={
                        "todo_ids": [str(tid) for tid in todo_ids],
                        "count": todo_count,
                        "title": first_todo_title if todo_count == 1 else f"{first_todo_title} 等{todo_count}项任务",
                        "message": f"手动生成了 {todo_count} 个待办任务",
                        "todos": todos,  # 包含所有 todos 的完整信息
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


@generation_bp.route('/daily-feed', methods=['GET'])
@auth_required
def get_daily_feed():
    """
    GET - 获取已生成的Feed数据（从数据库）
    """
    try:
        # 获取查询参数
        date_param = request.args.get('date')  # 可选的日期参数，格式：YYYY-MM-DD
        list_mode = request.args.get('list', 'false').lower() == 'true'  # 是否列表模式
        
        if list_mode:
            # 列表模式：获取最近的Feed列表
            limit = request.args.get('limit', 10, type=int)
            offset = request.args.get('offset', 0, type=int)
            feeds = get_daily_feeds(limit=limit, offset=offset)
            # 为返回的每个 feed 中的 cards 添加顺序 id
            try:
                for f in feeds:
                    if isinstance(f, dict) and 'cards' in f:
                        f['cards'] = _assign_sequential_ids(f.get('cards', []))
                        f['total_count'] = len(f.get('cards', []))
            except Exception:
                # 不阻塞，继续返回原始数据
                pass

            return convert_resp(
                message="Daily feeds retrieved successfully",
                data={
                    "feeds": feeds,
                    "total": len(feeds)
                }
            )
        else:
            # 单个Feed模式：默认获取当天的Feed
            if not date_param:
                date_param = datetime.now().strftime('%Y-%m-%d')
            
            # 获取指定日期的Feed
            from utils.db import get_daily_feed as db_get_daily_feed
            feed_data = db_get_daily_feed(date_param)
            
            # 如果是当天且没有数据，检查是否已过生成时间点，若已过则立即生成
            if not feed_data and date_param == datetime.now().strftime('%Y-%m-%d'):
                # 获取配置的生成时间点
                from config import ENABLE_SCHEDULER_DAILY_FEED
                if ENABLE_SCHEDULER_DAILY_FEED:
                    feed_hour = int(get_setting('daily_feed_hour', '8'))
                    feed_minute = int(get_setting('daily_feed_minute', '0'))
                    
                    # 检查当前时间是否已过生成时间点
                    now = datetime.now()
                    generation_time = now.replace(hour=feed_hour, minute=feed_minute, second=0, microsecond=0)
                    
                    if now >= generation_time:
                        # 已过生成时间点，立即生成
                        logger.info(f"Current time ({now.strftime('%H:%M')}) is past generation time ({feed_hour:02d}:{feed_minute:02d}), generating daily feed now")
                        try:
                            from utils.generation.daily_feed_gen import generate_daily_feed
                            result = asyncio.run(generate_daily_feed(lookback_hours=24))
                            
                            if result.get('success'):
                                # 生成成功，再从数据库获取
                                feed_data = db_get_daily_feed(date_param)
                                logger.info(f"Daily feed generated successfully on-demand")
                            else:
                                logger.warning(f"Failed to generate daily feed on-demand: {result.get('message')}")
                        except Exception as e:
                            logger.exception(f"Error generating daily feed on-demand: {e}")
            
            if feed_data:
                # 为返回的 cards 添加顺序 id（覆盖或新增 id 字段）
                try:
                    feed_data['cards'] = _assign_sequential_ids(feed_data.get('cards', []))
                    feed_data['total_count'] = len(feed_data.get('cards', []))
                except Exception:
                    pass

                return convert_resp(
                    message="Daily feed retrieved successfully",
                    data=feed_data  # 直接返回feed数据，不包装
                )
            else:
                # 没有生成的feed时，返回空对象，状态码200
                return convert_resp(
                    message="No feed generated yet",
                    data={"cards":[],"date":date_param,"total_count":0}
                )
        
    
    except Exception as e:
        logger.exception(f"Error retrieving daily feed: {e}")
        return convert_resp(code=500, status=500, message=f"Failed to retrieve daily feed: {str(e)}")


@generation_bp.route('/daily-feed', methods=['POST'])
@auth_required
def manual_generate_daily_feed():
    """
    POST - 生成新的Feed并存储到数据库
    """
    try:
        # 获取查询参数
        lookback_hours = request.args.get('lookback_hours', 24, type=int)
        date_param = request.args.get('date')  # 可选的日期参数，格式：YYYY-MM-DD
        
        # 如果指定了日期，计算该日期的时间范围
        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d')
                # 设置为当天的开始和结束
                from datetime import time
                start_dt = datetime.combine(target_date.date(), time.min)
                end_dt = datetime.combine(target_date.date(), time.max)
                
                # 计算lookback_hours（用于兼容现有逻辑）
                lookback_hours = int((end_dt - start_dt).total_seconds() / 3600)
            except ValueError:
                return convert_resp(
                    code=400,
                    status=400,
                    message="日期格式错误，请使用 YYYY-MM-DD 格式"
                )
        
        # 导入daily feed生成函数
        from utils.generation.daily_feed_gen import generate_daily_feed
        
        # 生成每日Feed（会自动存储到数据库）
        result = asyncio.run(generate_daily_feed(lookback_hours))
        
        if result.get('success'):
            cards = result.get('cards', [])
            # 为生成结果的 cards 添加顺序 id（仅用于返回给前端）
            try:
                cards = _assign_sequential_ids(cards)
            except Exception:
                pass

            logger.info(f"Generated and saved daily feed with {len(cards)} cards")
            
            return convert_resp(
                message="Daily feed generated and saved successfully",
                data={
                    "date": result.get('date'),
                    "cards": cards,
                    "total_count": result.get('total_count', len(cards))
                }
            )
        else:
            return convert_resp(
                code=500,
                status=500,
                message=result.get('message', 'Daily feed generation failed')
            )
        
    except Exception as e:
        logger.exception(f"Error generating daily feed: {e}")
        return convert_resp(code=500, status=500, message=f"Daily feed generation failed: {str(e)}")

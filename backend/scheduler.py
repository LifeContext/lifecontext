"""
定时任务调度器
使用 APScheduler 实现自动生成功能
"""

import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from utils.helpers import get_logger
from utils.generation import (
    create_activity_report,
    create_activity_record,
    generate_smart_tips,
    generate_task_list
)
from utils.event_manager import EventType, publish_event
from utils.db import get_reports, get_setting
from config import (
    ENABLE_SCHEDULER_ACTIVITY,
    ENABLE_SCHEDULER_TODO,
    ENABLE_SCHEDULER_TIP,
    ENABLE_SCHEDULER_REPORT
)

logger = get_logger(__name__)

# 全局调度器实例
scheduler = None


def init_scheduler():
    """初始化调度器"""
    global scheduler
    if scheduler is not None:
        return scheduler
    
    scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
    
    # 1. 每15分钟生成活动记录
    if ENABLE_SCHEDULER_ACTIVITY:
        scheduler.add_job(
            func=job_generate_activity,
            trigger=CronTrigger(minute='*/15'),  # 每15分钟
            id='activity_15min',
            name='每15分钟生成活动记录',
            replace_existing=True
        )
        logger.info("✅ Activity scheduler enabled")
    else:
        logger.info("⏸️ Activity scheduler disabled")
    
    # 2. 每30分钟生成待办任务
    if ENABLE_SCHEDULER_TODO:
        scheduler.add_job(
            func=job_generate_todos,
            trigger=CronTrigger(minute='*/30'),  # 每30分钟
            id='todos_30min',
            name='每30分钟生成待办',
            replace_existing=True
        )
        logger.info("✅ Todo scheduler enabled")
    else:
        logger.info("⏸️ Todo scheduler disabled")
    
    # 3. 生成智能提示（支持任意时间间隔）
    if ENABLE_SCHEDULER_TIP:
        tips_interval_minutes = int(get_setting('tips_interval_minutes', '60'))
        scheduler.add_job(
            func=job_generate_tips,
            trigger=IntervalTrigger(minutes=tips_interval_minutes),
            id='tips_interval',
            name=f'每{tips_interval_minutes}分钟生成智能提示',
            replace_existing=True
        )
        logger.info(f"✅ Tip scheduler enabled (interval: {tips_interval_minutes} minutes)")
    else:
        logger.info("⏸️ Tip scheduler disabled")
    
    # 4. 生成日报（支持自定义时间）
    if ENABLE_SCHEDULER_REPORT:
        report_hour = int(get_setting('daily_report_hour', '8'))
        report_minute = int(get_setting('daily_report_minute', '0'))
        scheduler.add_job(
            func=job_generate_daily_report,
            trigger=CronTrigger(hour=report_hour, minute=report_minute),
            id='daily_report',
            name=f'每日{report_hour:02d}:{report_minute:02d}生成报告',
            replace_existing=True
        )
        logger.info(f"✅ Report scheduler enabled (time: {report_hour:02d}:{report_minute:02d})")
    else:
        logger.info("⏸️ Report scheduler disabled")
    
    scheduler.start()
    logger.info("Scheduler initialized and started")
    
    return scheduler


def job_generate_activity():
    """定时任务：生成活动记录（每15分钟）"""
    try:
        logger.info("Starting scheduled activity generation (15min interval)")
        result = asyncio.run(create_activity_record(time_span_mins=15))
        
        if result.get('success'):
            activity_id = result.get('activity_id')
            activity_title = result.get('title', '活动记录')  # 使用实际的 title
            logger.info(f"✅ Activity generated: ID={activity_id}, Title={activity_title}")
            
            # 发布事件
            publish_event(
                event_type=EventType.ACTIVITY_GENERATED,
                data={
                    "activity_id": str(activity_id),
                    "title": activity_title,  # 使用实际的 title
                    "message": f"新的活动记录已生成: {activity_title}",
                    "description": result.get('description', '')[:200]
                }
            )
        else:
            logger.warning(f"⚠️ Activity generation failed: {result.get('message')}")
    except Exception as e:
        logger.exception(f"❌ Error in activity generation job: {e}")


def job_generate_todos():
    """定时任务：生成待办事项（每30分钟）"""
    try:
        logger.info("Starting scheduled todo generation (30min interval)")
        result = asyncio.run(generate_task_list(lookback_mins=30))
        
        if result.get('success'):
            todo_ids = result.get('todo_ids', [])
            todos = result.get('todos', [])
            todo_count = len(todo_ids)
            logger.info(f"✅ Generated {todo_count} todos")
            
            # 发布事件
            if todo_count > 0:
                # 使用第一个 todo 的 title，如果有多个则在 message 中说明
                first_todo_title = todos[0].get('title', '待办任务') if todos else '待办任务'
                
                publish_event(
                    event_type=EventType.TODO_GENERATED,
                    data={
                        "todo_ids": [str(tid) for tid in todo_ids],
                        "count": todo_count,
                        "title": first_todo_title if todo_count == 1 else f"{first_todo_title} 等{todo_count}项任务",
                        "message": f"生成了 {todo_count} 个新待办任务",
                        "todos": todos  # 包含所有 todos 的完整信息
                    }
                )
        else:
            logger.warning(f"⚠️ Todo generation failed: {result.get('message')}")
    except Exception as e:
        logger.exception(f"❌ Error in todo generation job: {e}")


def job_generate_tips():
    """定时任务：生成智能提示（可配置间隔）"""
    try:
        tips_interval_minutes = int(get_setting('tips_interval_minutes', '60'))
        logger.info(f"Starting scheduled tip generation (interval: {tips_interval_minutes} minutes)")
        result = asyncio.run(generate_smart_tips(history_mins=tips_interval_minutes))
        
        if result.get('success'):
            tip_ids = result.get('tip_ids', [])
            tips = result.get('tips', [])
            tip_count = len(tip_ids)
            logger.info(f"✅ Generated {tip_count} tips")
            
            # 发布事件
            if tip_count > 0:
                # 使用第一个 tip 的 title，如果有多个则在 message 中说明
                first_tip_title = tips[0].get('title', '智能提示') if tips else '智能提示'
                
                publish_event(
                    event_type=EventType.TIP_GENERATED,
                    data={
                        "tip_ids": [str(tid) for tid in tip_ids],
                        "count": tip_count,
                        "title": first_tip_title if tip_count == 1 else f"{first_tip_title} 等{tip_count}条提示",
                        "message": f"生成了 {tip_count} 条新的智能提示",
                        "tips": tips  # 包含所有 tips 的完整信息
                    }
                )
        else:
            logger.warning(f"⚠️ Tip generation failed: {result.get('message')}")
    except Exception as e:
        logger.exception(f"❌ Error in tip generation job: {e}")


def job_generate_daily_report():
    """定时任务：生成日报（每天早上8点）"""
    try:
        logger.info("Starting scheduled daily report generation (8:00 AM)")
        
        # 生成昨天的报告（从昨天早上8点到今天早上8点）
        now = datetime.now()
        start_time = (now - timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        
        result = asyncio.run(create_activity_report(
            int(start_time.timestamp()),
            int(now.timestamp())
        ))
        
        if result.get('success'):
            report_id = result.get('report_id')
            logger.info(f"✅ Daily report generated: ID={report_id}")
            
            # 从数据库获取报告的实际 title
            report_title = "每日报告"
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
                    "message": f"报告已生成: {report_title}",
                    "content": result.get('content', '')[:200],
                    "date": start_time.strftime("%Y-%m-%d")
                }
            )
        else:
            logger.warning(f"⚠️ Report generation failed: {result.get('message')}")
    except Exception as e:
        logger.exception(f"❌ Error in report generation job: {e}")


def stop_scheduler():
    """停止调度器"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def get_scheduled_jobs():
    """获取所有定时任务信息"""
    if scheduler is None:
        return []
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger)
        })
    
    return jobs


def update_scheduler_settings():
    """更新调度器设置（当设置改变时调用）"""
    global scheduler
    if scheduler is None:
        return
    
    try:
        # 更新 tips 生成间隔
        if ENABLE_SCHEDULER_TIP:
            tips_interval_minutes = int(get_setting('tips_interval_minutes', '60'))
            try:
                scheduler.remove_job('tips_interval')
            except:
                pass  # 任务可能不存在，忽略错误
            scheduler.add_job(
                func=job_generate_tips,
                trigger=IntervalTrigger(minutes=tips_interval_minutes),
                id='tips_interval',
                name=f'每{tips_interval_minutes}分钟生成智能提示',
                replace_existing=True
            )
            logger.info(f"✅ Updated tip scheduler interval to {tips_interval_minutes} minutes")
        
        # 更新 daily report 生成时间
        if ENABLE_SCHEDULER_REPORT:
            report_hour = int(get_setting('daily_report_hour', '8'))
            report_minute = int(get_setting('daily_report_minute', '0'))
            try:
                scheduler.remove_job('daily_report')
            except:
                pass  # 任务可能不存在，忽略错误
            scheduler.add_job(
                func=job_generate_daily_report,
                trigger=CronTrigger(hour=report_hour, minute=report_minute),
                id='daily_report',
                name=f'每日{report_hour:02d}:{report_minute:02d}生成报告',
                replace_existing=True
            )
            logger.info(f"✅ Updated report scheduler time to {report_hour:02d}:{report_minute:02d}")
    except Exception as e:
        logger.exception(f"Error updating scheduler settings: {e}")

"""
定时任务调度器
使用 APScheduler 实现自动生成功能
"""

import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.helpers import get_logger
from utils.generation import (
    create_activity_report,
    create_activity_record,
    generate_smart_tips,
    generate_task_list
)
from utils.event_manager import EventType, publish_event

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
    scheduler.add_job(
        func=job_generate_activity,
        trigger=CronTrigger(minute='*/15'),  # 每15分钟
        id='activity_15min',
        name='每15分钟生成活动记录',
        replace_existing=True
    )
    
    # 2. 每30分钟生成待办任务
    scheduler.add_job(
        func=job_generate_todos,
        trigger=CronTrigger(minute='*/30'),  # 每30分钟
        id='todos_30min',
        name='每30分钟生成待办',
        replace_existing=True
    )
    
    # 3. 每60分钟（1小时）生成智能提示
    scheduler.add_job(
        func=job_generate_tips,
        trigger=CronTrigger(minute=0),  # 每小时整点
        id='tips_hourly',
        name='每小时生成智能提示',
        replace_existing=True
    )
    
    # 4. 每天早上8点生成日报
    scheduler.add_job(
        func=job_generate_daily_report,
        trigger=CronTrigger(hour=8, minute=0),
        id='daily_report',
        name='每日8点生成报告',
        replace_existing=True
    )
    
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
            logger.info(f"✅ Activity generated: ID={activity_id}")
            
            # 发布事件
            publish_event(
                event_type=EventType.ACTIVITY_GENERATED,
                data={
                    "activity_id": str(activity_id),
                    "title": "活动记录",
                    "message": "新的活动记录已生成",
                    "content": result.get('content', '')[:200]
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
            todo_count = len(todo_ids)
            logger.info(f"✅ Generated {todo_count} todos")
            
            # 发布事件
            if todo_count > 0:
                publish_event(
                    event_type=EventType.TODO_GENERATED,
                    data={
                        "todo_ids": [str(tid) for tid in todo_ids],
                        "count": todo_count,
                        "title": "待办任务",
                        "message": f"生成了 {todo_count} 个新待办任务"
                    }
                )
        else:
            logger.warning(f"⚠️ Todo generation failed: {result.get('message')}")
    except Exception as e:
        logger.exception(f"❌ Error in todo generation job: {e}")


def job_generate_tips():
    """定时任务：生成智能提示（每小时）"""
    try:
        logger.info("Starting scheduled tip generation (hourly)")
        result = asyncio.run(generate_smart_tips(history_mins=60))  # 1小时
        
        if result.get('success'):
            tip_ids = result.get('tip_ids', [])
            tip_count = len(tip_ids)
            logger.info(f"✅ Generated {tip_count} tips")
            
            # 发布事件
            if tip_count > 0:
                publish_event(
                    event_type=EventType.TIP_GENERATED,
                    data={
                        "tip_ids": [str(tid) for tid in tip_ids],
                        "count": tip_count,
                        "title": "智能提示",
                        "message": f"生成了 {tip_count} 条新的智能提示"
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
            
            # 发布事件
            publish_event(
                event_type=EventType.REPORT_GENERATED,
                data={
                    "report_id": str(report_id),
                    "title": "每日报告",
                    "message": "每日报告已生成完成",
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

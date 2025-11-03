"""
数据库操作模块
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import config
from utils.helpers import get_logger

logger = get_logger(__name__)


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建报告表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT,
            content TEXT NOT NULL,
            document_type TEXT,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_deleted INTEGER DEFAULT 0
        )
    """)
    
    # 创建待办事项表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status INTEGER DEFAULT 0,
            priority INTEGER DEFAULT 0,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建活动记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            resources TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建提示表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tip_type TEXT,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建截图表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            window TEXT,
            source TEXT,
            create_time TIMESTAMP,
            processed INTEGER DEFAULT 0
        )
    """)
    
    # 创建网页数据表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS web_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT,
            content TEXT NOT NULL,
            source TEXT,
            tags TEXT,
            metadata TEXT,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")


# 报告相关操作
def get_reports(limit=10, offset=0, is_deleted=False):
    """获取报告列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM reports WHERE is_deleted = ? ORDER BY create_time DESC LIMIT ? OFFSET ?"
    cursor.execute(query, (1 if is_deleted else 0, limit, offset))
    
    reports = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return reports


def insert_report(title, content, summary="", document_type="daily_report"):
    """插入报告"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        "INSERT INTO reports (title, summary, content, document_type, create_time) VALUES (?, ?, ?, ?, ?)",
        (title, summary, content, document_type, create_time)
    )
    
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


# 待办事项相关操作
def get_todos(status=None, limit=10, offset=0):
    """获取待办事项列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status is not None:
        query = "SELECT * FROM todos WHERE status = ? ORDER BY create_time DESC LIMIT ? OFFSET ?"
        cursor.execute(query, (status, limit, offset))
    else:
        query = "SELECT * FROM todos ORDER BY create_time DESC LIMIT ? OFFSET ?"
        cursor.execute(query, (limit, offset))
    
    todos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return todos


def update_todo_status(todo_id, status, end_time=None):
    """更新待办事项状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if end_time:
        cursor.execute(
            "UPDATE todos SET status = ?, end_time = ? WHERE id = ?",
            (status, end_time, todo_id)
        )
    else:
        cursor.execute(
            "UPDATE todos SET status = ? WHERE id = ?",
            (status, todo_id)
        )
    
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0


def update_todo(todo_id, **kwargs):
    """更新待办事项（支持更新多个字段）
    
    Args:
        todo_id: 待办事项ID
        **kwargs: 可更新的字段，包括 title, description, status, priority, end_time 等
    
    Returns:
        bool: 是否更新成功
    """
    if not kwargs:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 允许更新的字段
    allowed_fields = {'title', 'description', 'status', 'priority', 'end_time', 'start_time'}
    
    # 过滤出允许更新的字段
    update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not update_fields:
        conn.close()
        return False
    
    # 构建 SQL 更新语句
    set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
    values = list(update_fields.values())
    values.append(todo_id)
    
    sql = f"UPDATE todos SET {set_clause} WHERE id = ?"
    cursor.execute(sql, values)
    
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0


def insert_todo(title, description="", priority=0, start_time=None, end_time=None):
    """插入待办事项
    
    Args:
        title: 标题
        description: 描述
        priority: 优先级 (0-3)
        start_time: 开始时间（字符串格式 'YYYY-MM-DD HH:MM:SS' 或 datetime 对象）
        end_time: 结束时间（字符串格式 'YYYY-MM-DD HH:MM:SS' 或 datetime 对象）
    
    Returns:
        int: 新插入的待办事项ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 处理开始时间
    if start_time is None:
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(start_time, datetime):
        start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # 处理结束时间
    if end_time is not None and isinstance(end_time, datetime):
        end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        "INSERT INTO todos (title, description, priority, start_time, end_time, create_time) VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, priority, start_time, end_time, create_time)
    )
    
    todo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return todo_id


def delete_todo(todo_id):
    """删除待办事项
    
    Args:
        todo_id: 待办事项ID
    
    Returns:
        bool: 是否删除成功
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    
    affected_rows = cursor.rowcount
    conn.commit()
    conn.close()
    return affected_rows > 0


# 活动记录相关操作
def get_activities(start_time=None, end_time=None, limit=10, offset=0):
    """获取活动记录列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM activities WHERE 1=1"
    params = []
    
    if start_time:
        query += " AND start_time >= ?"
        # 转换为字符串格式
        if isinstance(start_time, datetime):
            params.append(start_time.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            params.append(start_time)
    
    if end_time:
        query += " AND end_time <= ?"
        # 转换为字符串格式
        if isinstance(end_time, datetime):
            params.append(end_time.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            params.append(end_time)
    
    query += " ORDER BY create_time DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    activities = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return activities


def insert_activity(title, description="", resources=None, start_time=None, end_time=None):
    """插入活动记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    resources_json = json.dumps(resources) if resources else None
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        "INSERT INTO activities (title, description, resources, start_time, end_time, create_time) VALUES (?, ?, ?, ?, ?, ?)",
        (title, description, resources_json, start_time, end_time, create_time)
    )
    
    activity_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return activity_id


# 提示相关操作
def get_tips(limit=10, offset=0):
    """获取提示列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tips ORDER BY create_time DESC LIMIT ? OFFSET ?"
    cursor.execute(query, (limit, offset))
    
    tips = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tips


def insert_tip(title, content, tip_type="general"):
    """插入提示"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        "INSERT INTO tips (title, content, tip_type, create_time) VALUES (?, ?, ?, ?)",
        (title, content, tip_type, create_time)
    )
    
    tip_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tip_id


# 截图相关操作
def insert_screenshot(path, window="unknown", source="upload", create_time=None):
    """插入截图记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not create_time:
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(create_time, datetime):
        create_time = create_time.strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        "INSERT INTO screenshots (path, window, source, create_time) VALUES (?, ?, ?, ?)",
        (path, window, source, create_time)
    )
    
    screenshot_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return screenshot_id


# 网页数据相关操作
def get_web_data(start_time=None, end_time=None, limit=50, offset=0):
    """获取网页数据列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM web_data WHERE 1=1"
    params = []
    
    if start_time:
        query += " AND create_time >= ?"
        # 转换为字符串格式
        if isinstance(start_time, datetime):
            params.append(start_time.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            params.append(start_time)
    
    if end_time:
        query += " AND create_time <= ?"
        # 转换为字符串格式
        if isinstance(end_time, datetime):
            params.append(end_time.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            params.append(end_time)
    
    query += " ORDER BY create_time DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    web_data_list = []
    for row in rows:
        item = dict(row)
        # 解析 JSON 字段
        if item.get('tags'):
            try:
                item['tags'] = json.loads(item['tags'])
            except:
                item['tags'] = []
        else:
            item['tags'] = []
        
        if item.get('metadata'):
            try:
                item['metadata'] = json.loads(item['metadata'])
            except:
                item['metadata'] = {}
        else:
            item['metadata'] = {}
        
        if item.get('content'):
            try:
                item['content'] = json.loads(item['content'])
            except:
                pass  # 保持原样
        
        web_data_list.append(item)
    
    conn.close()
    return web_data_list


def insert_web_data(title, url, content, source="web_crawler", tags=None, metadata=None):
    """插入网页数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tags_json = json.dumps(tags) if tags else None
    metadata_json = json.dumps(metadata) if metadata else None
    content_json = json.dumps(content) if isinstance(content, dict) else content
    
    # 使用本地时间而不是 CURRENT_TIMESTAMP（UTC）
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        "INSERT INTO web_data (title, url, content, source, tags, metadata, create_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, url, content_json, source, tags_json, metadata_json, create_time)
    )
    
    web_data_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return web_data_id


def get_screenshots(start_time=None, end_time=None, limit=10, offset=0):
    """获取截图列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM screenshots WHERE 1=1"
    params = []
    
    if start_time:
        query += " AND create_time >= ?"
        # 转换为字符串格式
        if isinstance(start_time, datetime):
            params.append(start_time.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            params.append(start_time)
    
    if end_time:
        query += " AND create_time <= ?"
        # 转换为字符串格式
        if isinstance(end_time, datetime):
            params.append(end_time.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            params.append(end_time)
    
    query += " ORDER BY create_time DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    screenshots = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return screenshots

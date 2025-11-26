"""
数据库操作模块
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import config
from utils.helpers import get_logger
from typing import Optional, List

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
            source_urls TEXT,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 如果表已存在但没有 source_urls 字段，添加该字段
    try:
        cursor.execute("ALTER TABLE tips ADD COLUMN source_urls TEXT")
        logger.info("Added source_urls column to tips table")
    except sqlite3.OperationalError:
        # 字段已存在，忽略错误
        pass
    
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
    
    # 创建设置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 初始化默认设置
    default_settings = [
        ('tips_interval_minutes', '60', 'Tips生成间隔（分钟）'),
        ('daily_report_hour', '8', 'Daily Report生成时间（小时，0-23）'),
        ('daily_report_minute', '0', 'Daily Report生成时间（分钟，0-59）')
    ]
    
    for key, value, description in default_settings:
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value, description) 
            VALUES (?, ?, ?)
        """, (key, value, description))
    
    # 创建 URL 黑名单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS url_blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建每日Feed表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            cards TEXT NOT NULL,
            total_count INTEGER DEFAULT 0,
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
    
    # 如果更新成功，同步到向量数据库（不改变原有逻辑，失败不影响返回值）
    if affected_rows > 0:
        try:
            # 检查是否更新了 status 字段，如果 status 变为 1（完成），则从向量数据库删除
            if 'status' in update_fields and update_fields['status'] == 1:
                # todo 完成，从向量数据库删除
                from utils.vectorstore import delete_todo_from_vectorstore
                delete_todo_from_vectorstore(todo_id)
                logger.info(f"Deleted completed todo {todo_id} from vectorstore")
            else:
                # 其他更新，同步更新向量数据库
                # 获取更新后的完整todo信息
                todos = get_todos(limit=1000)  # 获取所有todos
                updated_todo = None
                for todo in todos:
                    if todo.get('id') == todo_id:
                        updated_todo = todo
                        break
                
                if updated_todo:
                    from utils.vectorstore import add_todo_to_vectorstore
                    add_todo_to_vectorstore(
                        todo_id=todo_id,
                        title=updated_todo.get('title', ''),
                        description=updated_todo.get('description', ''),
                        priority=updated_todo.get('priority', 0),
                        start_time=updated_todo.get('start_time'),
                        end_time=updated_todo.get('end_time'),
                        status=updated_todo.get('status', 0)
                    )
        except Exception as e:
            logger.warning(f"Failed to sync todo to vectorstore: {e}")
    
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
    
    # 添加到向量数据库（不改变原有逻辑，失败不影响返回值）
    try:
        from utils.vectorstore import add_todo_to_vectorstore
        add_todo_to_vectorstore(
            todo_id=todo_id,
            title=title,
            description=description,
            priority=priority,
            start_time=start_time,
            end_time=end_time,
            status=0  # 新创建的待办事项状态为0（未完成）
        )
    except Exception as e:
        logger.warning(f"Failed to add todo to vectorstore: {e}")
    
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
    
    # 从向量数据库删除（不改变原有逻辑，失败不影响返回值）
    if affected_rows > 0:
        try:
            from utils.vectorstore import delete_todo_from_vectorstore
            delete_todo_from_vectorstore(todo_id)
            logger.info(f"Deleted todo {todo_id} from vectorstore")
        except Exception as e:
            logger.warning(f"Failed to delete todo from vectorstore: {e}")
    
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
    
    tips = []
    for row in cursor.fetchall():
        tip = dict(row)
        # 解析 source_urls JSON 字符串为列表
        if tip.get('source_urls'):
            try:
                tip['source_urls'] = json.loads(tip['source_urls'])
            except (json.JSONDecodeError, TypeError):
                # 如果解析失败，尝试作为单个 URL 处理
                tip['source_urls'] = [tip['source_urls']] if tip['source_urls'] else []
        else:
            tip['source_urls'] = []
        tips.append(tip)
    
    conn.close()
    return tips


def insert_tip(title, content, tip_type="general", source_urls=None):
    """插入提示"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 将 source_urls 转换为 JSON 字符串
    source_urls_json = None
    if source_urls:
        if isinstance(source_urls, list):
            source_urls_json = json.dumps(source_urls, ensure_ascii=False)
        else:
            source_urls_json = str(source_urls)
    
    cursor.execute(
        "INSERT INTO tips (title, content, tip_type, source_urls, create_time) VALUES (?, ?, ?, ?, ?)",
        (title, content, tip_type, source_urls_json, create_time)
    )
    
    tip_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # 添加到向量数据库（不改变原有逻辑，失败不影响返回值）
    try:
        from utils.vectorstore import add_tip_to_vectorstore
        add_tip_to_vectorstore(
            tip_id=tip_id,
            title=title,
            content=content,
            tip_type=tip_type,
            source_urls=source_urls if isinstance(source_urls, list) else [source_urls] if source_urls else None
        )
    except Exception as e:
        logger.warning(f"Failed to add tip to vectorstore: {e}")
    
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


# URL 黑名单相关操作
def get_url_blacklist(limit=1000, offset=0):
    """获取 URL 黑名单列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, url, create_time FROM url_blacklist ORDER BY create_time DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
    
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def add_url_to_blacklist(url: str):
    """添加 URL 到黑名单"""
    if not url or not isinstance(url, str):
        raise ValueError("url 必须是非空字符串")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        cursor.execute(
            "INSERT INTO url_blacklist (url, create_time) VALUES (?, ?)",
            (url.strip(), create_time)
        )
        conn.commit()
        new_id = cursor.lastrowid
        return new_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError("该 URL 已存在于黑名单中") from e
    finally:
        conn.close()


def delete_url_from_blacklist(entry_id: int):
    """从黑名单中删除指定记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM url_blacklist WHERE id = ?", (entry_id,))
    affected_rows = cursor.rowcount
    
    conn.commit()
    conn.close()
    return affected_rows > 0


# 设置相关操作
def get_setting(key, default_value=None):
    """获取设置值
    
    Args:
        key: 设置键名
        default_value: 如果不存在时返回的默认值
    
    Returns:
        str: 设置值，如果不存在则返回 default_value
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row['value']
    return default_value


def set_setting(key, value, description=None):
    """设置配置值
    
    Args:
        key: 设置键名
        value: 设置值（字符串）
        description: 设置描述（可选）
    
    Returns:
        bool: 是否设置成功
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if description:
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value, description, update_time)
            VALUES (?, ?, ?, ?)
        """, (key, str(value), description, update_time))
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value, update_time)
            VALUES (?, ?, ?)
        """, (key, str(value), update_time))
    
    conn.commit()
    conn.close()
    return True


def get_all_settings():
    """获取所有设置
    
    Returns:
        dict: 所有设置的键值对
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT key, value, description FROM settings")
    rows = cursor.fetchall()
    conn.close()
    
    settings = {}
    for row in rows:
        row_dict = dict(row)  # 转换为字典
        settings[row_dict['key']] = {
            'value': row_dict['value'],
            'description': row_dict.get('description', '')  # 现在可以使用 .get() 了
        }
    
    return settings


# ============================================================================
# Daily Feed 相关函数
# ============================================================================

def insert_daily_feed(date: str, cards: List[dict], total_count: int) -> Optional[int]:
    """插入或更新每日Feed
    
    Args:
        date: 日期字符串 (YYYY-MM-DD)
        cards: 卡片列表
        total_count: 卡片总数
    
    Returns:
        int: feed ID，失败返回 None
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 将cards列表转换为JSON字符串
        cards_json = json.dumps(cards, ensure_ascii=False)
        
        # 使用 INSERT OR REPLACE 实现 upsert
        cursor.execute("""
            INSERT OR REPLACE INTO daily_feeds (date, cards, total_count, create_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (date, cards_json, total_count))
        
        feed_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Inserted/Updated daily feed for date {date} with {total_count} cards")
        return feed_id
        
    except Exception as e:
        logger.exception(f"Error inserting daily feed: {e}")
        return None


def get_daily_feed(date: str) -> Optional[dict]:
    """获取指定日期的Feed
    
    Args:
        date: 日期字符串 (YYYY-MM-DD)
    
    Returns:
        dict: Feed数据，包含 date, cards, total_count, create_time
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, date, cards, total_count, create_time
            FROM daily_feeds
            WHERE date = ?
        """, (date,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            row_dict = dict(row)
            # 解析JSON字符串为列表
            row_dict['cards'] = json.loads(row_dict['cards'])
            return row_dict
        
        return None
        
    except Exception as e:
        logger.exception(f"Error getting daily feed: {e}")
        return None


def get_daily_feeds(limit: int = 10, offset: int = 0) -> List[dict]:
    """获取多个Feed（按日期倒序）
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
    
    Returns:
        List[dict]: Feed列表
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, date, cards, total_count, create_time
            FROM daily_feeds
            ORDER BY date DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        feeds = []
        for row in rows:
            row_dict = dict(row)
            # 解析JSON字符串为列表
            row_dict['cards'] = json.loads(row_dict['cards'])
            feeds.append(row_dict)
        
        return feeds
        
    except Exception as e:
        logger.exception(f"Error getting daily feeds: {e}")
        return []


def delete_daily_feed(date: str) -> bool:
    """删除指定日期的Feed
    
    Args:
        date: 日期字符串 (YYYY-MM-DD)
    
    Returns:
        bool: 是否成功
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM daily_feeds WHERE date = ?", (date,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted daily feed for date {date}")
        return True
        
    except Exception as e:
        logger.exception(f"Error deleting daily feed: {e}")
        return False


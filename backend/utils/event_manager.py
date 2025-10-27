"""
事件管理器 - 缓存版本，支持获取和清除机制
"""

import json
import time
import uuid
import threading
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .helpers import get_logger

logger = get_logger(__name__)


class EventType(str, Enum):
    """事件类型枚举"""
    TIP_GENERATED = "tip"
    TODO_GENERATED = "todo"
    ACTIVITY_GENERATED = "activity"
    REPORT_GENERATED = "report"
    SYSTEM_STATUS = "system_status"


@dataclass
class Event:
    """事件数据结构"""
    id: str
    type: EventType
    data: Dict[str, Any]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        }


class EventManager:
    """缓存式事件管理器"""
    
    def __init__(self):
        self.event_cache: deque[Event] = deque()
        self.max_cache_size = 1000
        self._lock = threading.Lock()  # 确保线程安全
        logger.info("Event Manager initialized")
    
    def publish_event(
        self, 
        event_type: EventType, 
        data: Dict[str, Any]
    ) -> str:
        """发布事件到缓存"""
        event_id = str(uuid.uuid4())
        event = Event(
            id=event_id,
            type=event_type,
            data=data,
            timestamp=time.time()
        )
        
        with self._lock:
            self.event_cache.append(event)
            
            # 限制缓存大小，避免内存溢出
            while len(self.event_cache) > self.max_cache_size:
                removed_event = self.event_cache.popleft()
                logger.warning(f"缓存溢出，移除旧事件: {removed_event.id}")
        
        logger.info(f"发布事件到缓存: {event_type.value}, ID: {event_id}, 数据: {data.get('title', 'N/A')}")
        return event_id
    
    def fetch_and_clear_events(self) -> List[Dict[str, Any]]:
        """获取所有缓存事件并清空缓存"""
        with self._lock:
            # 获取当前所有事件
            events = [event.to_dict() for event in self.event_cache]
            # 清空缓存
            self.event_cache.clear()
        
        if events:
            logger.info(f"返回并清空了 {len(events)} 个缓存事件")
        return events
    
    def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        with self._lock:
            cache_size = len(self.event_cache)
            oldest_event_time = None
            if self.event_cache:
                oldest_event_time = datetime.fromtimestamp(
                    self.event_cache[0].timestamp
                ).strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "cache_size": cache_size,
            "max_cache_size": self.max_cache_size,
            "oldest_event_time": oldest_event_time,
            "supported_event_types": [t.value for t in EventType]
        }


# 全局事件管理器实例
_event_manager = None


def get_event_manager() -> EventManager:
    """获取全局事件管理器实例"""
    global _event_manager
    if _event_manager is None:
        _event_manager = EventManager()
    return _event_manager


def publish_event(
    event_type: EventType, 
    data: Dict[str, Any]
) -> str:
    """发布事件到缓存（便捷函数）"""
    return get_event_manager().publish_event(event_type, data)

"""
操作工具模块
提供各种操作相关的工具
"""

from tools.operation_tools.web_search_tool import WebSearchTool
from tools.operation_tools.schedule_conflict_tool import ScheduleConflictCheckTool


def get_operation_tools() -> list:
    """获取所有操作工具实例"""
    return [
        WebSearchTool(),
        ScheduleConflictCheckTool(),
    ]


__all__ = ["get_operation_tools"]
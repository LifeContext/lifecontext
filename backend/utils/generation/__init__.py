"""
智能内容生成模块 - 函数式接口
提供报告、任务、活动和提示的智能生成功能
"""

from .report_gen_new import create_activity_report
from .activity_gen_new import create_activity_record
from .tip_gen_new import generate_smart_tips
from .todo_gen_new import generate_task_list

# 导出公共接口
__all__ = [
    'create_activity_report',
    'create_activity_record',
    'generate_smart_tips',
    'generate_task_list',
]

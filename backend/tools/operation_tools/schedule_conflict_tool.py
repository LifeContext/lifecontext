"""
日程冲突检测工具
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import config
from tools.base import BaseTool
from utils.helpers import get_logger
from utils.llm import get_openai_client

logger = get_logger(__name__)


class ScheduleConflictCheckTool(BaseTool):
    """检测用户计划与待办事项是否存在时间冲突"""

    def __init__(self) -> None:
        super().__init__(
            name="schedule_conflict_check",
            description=(
                "根据用户查询和待办事项列表，判断是否存在时间冲突，"
                "当用户计划与已有任务在同一日期/时间段冲突时提醒用户。"
            ),
            is_async=False,
        )

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "用户的自然语言查询，包含计划时间信息",
                },
                "todos": {
                    "type": "array",
                    "description": "待办事项列表，仅包含与当前上下文相关的任务",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                        },
                        "required": ["title"],
                    },
                },
            },
            "required": ["user_query", "todos"],
        }

    def execute(self, user_query: str, todos: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        if not todos:
            return {"has_conflict": False}

        client = get_openai_client()
        if not client:
            logger.warning("LLM client not available, skip conflict check")
            return {"has_conflict": False}

        todos_summary = "\n".join(
            [
                f"- {todo.get('title', '')}"
                + (
                    f" ({todo.get('description', '')})"
                    if todo.get("description")
                    else ""
                )
                for todo in todos[:10]
            ]
        )

        analysis_prompt = f"""用户查询: {user_query}

用户的待办事项列表:
{todos_summary}

请精确分析时间冲突：

1. **提取时间概念**：从用户查询和待办事项中提取完整的时间概念，包括：
   - 日期概念：如"明天"、"后天"、"下周"
   - 时间段：如"早上"、"上午"、"中午"、"下午"、"晚上"、"九点"、"十点"等
   - 完整时间：如"明天下午"、"明天早上九点"

2. **判断冲突**：只有当以下条件**同时满足**时才认为冲突：
   - 日期概念相同（如都是"明天"）
   - **并且**时间段重叠或无法确定时间段（如"明天下午"与"明天早上九点"不冲突，因为时间段不重叠）
   - **或者**待办事项没有明确时间段，但用户查询需要长时间（如"明天出去玩一整天"）

3. **特殊情况**：
   - "明天记得买XX"这类没有具体时间段的待办事项，如果用户查询是"明天下午"，通常不冲突（可以下午出去前买）
   - "明天早上九点"和"明天下午"不冲突
   - "明天"和"明天下午"不冲突（后者更具体，可以安排）

请返回JSON格式：
{{
    "query_time": {{
        "date": "明天",
        "time_period": "下午",  // 可能为空
        "is_flexible": false  // 是否时间灵活
    }},
    "has_conflict": true/false,
    "conflict_todos": ["待办事项标题"],  // 只包含真正冲突的
    "conflict_reason": "详细说明为什么冲突（包括时间段对比）"
}}"""

        try:
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是日程冲突检测助手。必须精确判断时间段是否重叠。"
                            "只有日期相同且时间段重叠时才认为冲突。返回JSON。"
                        ),
                    },
                    {"role": "user", "content": analysis_prompt},
                ],
                temperature=0.1,
                max_tokens=400,
            )

            analysis_text = response.choices[0].message.content.strip()
            json_match = re.search(r"\{[^{}]*\}", analysis_text, re.DOTALL)
            if json_match:
                analysis_result = json.loads(json_match.group())
            else:
                analysis_result = json.loads(analysis_text)

            if analysis_result.get("has_conflict"):
                conflict_todos = analysis_result.get("conflict_todos", [])
                query_time = analysis_result.get("query_time", {})
                conflict_reason = analysis_result.get(
                    "conflict_reason", "检测到时间冲突"
                )

                warning_message = "⚠️ 时间冲突提醒：\n\n"
                date_concept = query_time.get("date", "")
                time_period = query_time.get("time_period", "")
                if date_concept:
                    if time_period:
                        warning_message += (
                            f"您提到的「{date_concept}{time_period}」可能与以下待办事项冲突：\n\n"
                        )
                    else:
                        warning_message += (
                            f"您提到的「{date_concept}」可能与以下待办事项冲突：\n\n"
                        )

                warning_message += f"{conflict_reason}\n\n"

                if conflict_todos:
                    warning_message += "冲突的待办事项：\n"
                    for todo_title in conflict_todos:
                        warning_message += f"- {todo_title}\n"
                    warning_message += "\n"

                warning_message += "请调整您的计划，避免时间冲突。"

                return {
                    "has_conflict": True,
                    "warning_message": warning_message,
                    "conflict_details": [
                        {
                            "todo_title": title,
                            "query_date": date_concept,
                            "query_time_period": time_period,
                            "reason": conflict_reason,
                        }
                        for title in conflict_todos
                    ],
                }

        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to analyze schedule conflict: %s", exc, exc_info=True)
            return {"has_conflict": False}

        return {"has_conflict": False}

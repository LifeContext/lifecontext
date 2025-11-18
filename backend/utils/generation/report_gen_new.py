"""
智能报告生成模块
基于时间范围和用户数据生成活动分析报告
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from string import Template
import asyncio
import config
from utils.helpers import (
    get_logger,
    estimate_tokens,
    truncate_web_data_by_tokens,
    calculate_available_context_tokens
)
from utils.json_utils import parse_llm_json_response
from utils.db import get_tips, get_todos, get_web_data, get_reports, insert_report
from utils.llm import get_openai_client
from utils.vectorstore import search_similar_content
from utils.prompt_config import get_current_prompts

logger = get_logger(__name__)

_llm = None

# 全局LLM客户端
_client_cache = None


def _init_llm():
    """初始化LLM客户端"""
    global _client_cache
    if _client_cache is None:
        _client_cache = get_openai_client()
    return _client_cache


async def create_activity_report(start_ts: int, end_ts: int) -> Dict[str, Any]:
    """
    生成活动报告（主入口）
    
    Args:
        start_ts: 起始Unix时间戳
        end_ts: 结束Unix时间戳
    
    Returns:
        包含报告数据的字典
    """
    try:
        hours = (end_ts - start_ts) / 3600
        
        # 根据时间跨度选择策略
        if hours > 1:
            report_text = await _generate_segmented_report(start_ts, end_ts)
        else:
            report_text = await _generate_direct_report(start_ts, end_ts)
        
        if not report_text:
            return {"success": False, "message": "缺少数据无法生成"}
        
        # 格式化时间
        dt_start = datetime.fromtimestamp(start_ts)
        dt_end = datetime.fromtimestamp(end_ts)
        
        # 保存到数据库
        title = f"活动报告 {dt_end.strftime('%Y-%m-%d %H:%M')}"
        brief = _extract_brief(report_text)
        
        rid = insert_report(
            title=title,
            content=report_text,
            summary=brief,
            document_type="activity_report"
        )
        
        logger.info(f"Report created: ID={rid}")
        
        return {
            "success": True,
            "report_id": rid,
            "content": report_text,
            "time_range": {
                "start": dt_start.isoformat(),
                "end": dt_end.isoformat()
            }
        }
    except Exception as e:
        logger.exception(f"Failed to create report: {e}")
        return {"success": False, "message": str(e)}


async def _generate_direct_report(start_ts: int, end_ts: int) -> Optional[str]:
    """直接生成报告（短时间段）"""
    data_dict = _fetch_time_range_data(start_ts, end_ts)
    
    if not data_dict.get("has_data"):
        logger.warning("No data for report")
        return None
    
    return await _ask_llm_for_report(data_dict, start_ts, end_ts)


async def _generate_segmented_report(start_ts: int, end_ts: int) -> Optional[str]:
    """分段生成报告（长时间段）"""
    logger.info("Using segmented generation for long time range")
    
    # 按小时切分
    segments = []
    current = start_ts
    
    while current < end_ts:
        next_point = min(current + 3600, end_ts)
        segments.append((current, next_point))
        current = next_point
    
    # 生成各段摘要
    summaries = []
    for seg_start, seg_end in segments:
        data = _fetch_time_range_data(seg_start, seg_end)
        if data:
            summary = await _make_segment_summary(data, seg_start, seg_end)
            if summary:
                summaries.append({
                    'time_start': seg_start,
                    'time_end': seg_end,
                    'text': summary
                })
    
    if not summaries:
        return None
    
    # 汇总成完整报告
    return await _combine_summaries(summaries, start_ts, end_ts)


def _fetch_time_range_data(start_ts: int, end_ts: int) -> Dict[str, Any]:
    """
    获取时间范围内的所有数据（网页、Tips、Todos）
    
    Returns:
        {
            "web_data": [...],
            "tips": [...],
            "todos": [...],
            "has_data": True/False
        }
    """
    try:
        dt_start = datetime.fromtimestamp(start_ts)
        dt_end = datetime.fromtimestamp(end_ts)
        
        logger.info(f"Fetching data: {dt_start.strftime('%Y-%m-%d %H:%M:%S')} to {dt_end.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 获取网页数据
        raw_web_data = get_web_data(
            start_time=dt_start,
            end_time=dt_end,
            limit=100
        )
        
        web_data_list = []
        for item in raw_web_data:
            web_data_list.append({
                "id": item["id"],
                "title": item["title"],
                "url": item.get("url", ""),
                "metadata": item.get("metadata", {}),
                "source": item.get("source", "unknown"),
                "tags": item.get("tags", []),
                "create_time": item.get("create_time", "")
            })
        
        logger.info(f"Found {len(web_data_list)} web records")
        
        # 2. 获取Tips（智能提示）
        tips_list = []
        try:
            all_tips = get_tips(limit=100)
            for tip in all_tips:
                tip_time_str = tip.get('create_time', '')
                if tip_time_str:
                    try:
                        tip_time = datetime.strptime(tip_time_str, '%Y-%m-%d %H:%M:%S')
                        if dt_start <= tip_time <= dt_end:
                            tips_list.append({
                                "id": tip.get("id"),
                                "title": tip.get("title", ""),
                                "content": tip.get("content", ""),
                                "type": tip.get("tip_type", "general"),
                                "create_time": tip_time_str
                            })
                    except Exception as e:
                        logger.debug(f"Failed to parse tip time: {e}")
            
            logger.info(f"Found {len(tips_list)} tips")
        except Exception as e:
            logger.warning(f"Failed to fetch tips: {e}")
        
        # 3. 获取Todos（待办事项）
        todos_list = []
        try:
            all_todos = get_todos(limit=200)
            for todo in all_todos:
                todo_time_str = todo.get('create_time', '')
                if todo_time_str:
                    try:
                        todo_time = datetime.strptime(todo_time_str, '%Y-%m-%d %H:%M:%S')
                        if dt_start <= todo_time <= dt_end:
                            todos_list.append({
                                "id": todo.get("id"),
                                "title": todo.get("title", ""),
                                "description": todo.get("description", ""),
                                "status": todo.get("status", 0),  # 0=未完成, 1=已完成
                                "priority": todo.get("priority", 0),
                                "create_time": todo_time_str,
                                "end_time": todo.get("end_time", "")
                            })
                    except Exception as e:
                        logger.debug(f"Failed to parse todo time: {e}")
            
            logger.info(f"Found {len(todos_list)} todos")
        except Exception as e:
            logger.warning(f"Failed to fetch todos: {e}")
        
        # 组装结果
        result = {
            "web_data": web_data_list,
            "tips": tips_list,
            "todos": todos_list,
            "has_data": bool(web_data_list or tips_list or todos_list)
        }
        
        if not result["has_data"]:
            # 调试信息
            all_records = get_web_data(limit=5)
            logger.info(f"Latest 5 web records in DB: {len(all_records)}")
            for rec in all_records:
                logger.info(f"  ID={rec['id']}, Title={rec['title']}, Time={rec.get('create_time')}")
        
        return result
    except Exception as e:
        logger.exception(f"Error fetching data: {e}")
        return {
            "web_data": [],
            "tips": [],
            "todos": [],
            "has_data": False
        }


async def _ask_llm_for_report(data_dict: Dict[str, Any], start_ts: int, end_ts: int) -> Optional[str]:
    """调用LLM生成报告"""
    client = _init_llm()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        logger.warning("LLM unavailable, using fallback")
        return _create_plain_report(data_dict, start_ts, end_ts)
    
    try:
        dt_start = datetime.fromtimestamp(start_ts)
        dt_end = datetime.fromtimestamp(end_ts)
        
        # 限制数据量避免Token超限
        tips = data_dict.get("tips", [])[:20]    # 最多20条提示
        todos = data_dict.get("todos", [])[:30]  # 最多30条待办
        
        # 估算 tips 和 todos 的 token
        other_data_json = json.dumps({
            "tips": tips,
            "todos": todos
        }, ensure_ascii=False)
        other_data_tokens = estimate_tokens(other_data_json)
        
        # 计算可用于 web_data 的 token 数
        available_tokens = calculate_available_context_tokens('report', other_data_tokens)
        
        # 使用动态截取函数处理 web_data，使用 metadata 替代 content
        web_data_trimmed = truncate_web_data_by_tokens(
            data_dict.get("web_data", []),
            max_tokens=available_tokens,
            use_metadata=True
        )
        
        report_data = {
            "web_data": web_data_trimmed,
            "tips": tips,
            "todos": todos
        }
        
        data_json = json.dumps(report_data, ensure_ascii=False, indent=2)
         
        # 动态获取当前配置的提示词
        prompts = get_current_prompts()
        sys_msg = prompts["report"]["main_system"]
        
        # 准备数据集JSON
        web_data_json = json.dumps(report_data.get('web_data', []), ensure_ascii=False, indent=2)
        tips_json = json.dumps(report_data.get('tips', []), ensure_ascii=False, indent=2)
        todos_json = json.dumps(report_data.get('todos', []), ensure_ascii=False, indent=2)
        
        user_template = Template(prompts["report"]["main_user_template"])
        user_msg = user_template.safe_substitute(
            start_time=dt_start.strftime('%Y-%m-%d %H:%M:%S'),
            end_time=dt_end.strftime('%Y-%m-%d %H:%M:%S'),
            web_data_json=web_data_json,
            tips_json=tips_json,
            todos_json=todos_json
        )
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=2500
        )
        
        result = response.choices[0].message.content
        logger.info("LLM report generated successfully")
        return result
    except Exception as e:
        logger.exception(f"LLM error: {e}")
        return _create_plain_report(data_dict, start_ts, end_ts)


async def _make_segment_summary(data_list: List[Dict], start_ts: int, end_ts: int) -> Optional[str]:
    """生成时段摘要"""
    client = _init_llm()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        return _simple_summary(data_list)
    
    try:
        data_json = json.dumps(data_list, ensure_ascii=False, indent=2)
        dt_start = datetime.fromtimestamp(start_ts)
        dt_end = datetime.fromtimestamp(end_ts)
        
        # 动态获取当前配置的提示词
        prompts = get_current_prompts()
        system_msg = prompts["report"]["segment_system"]

        user_template = Template(prompts["report"]["segment_user_template"])
        user_msg = user_template.safe_substitute(
            start_time=dt_start.strftime('%H:%M'),
            end_time=dt_end.strftime('%H:%M'),
            data_json=data_json
        )
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.5,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Summary error: {e}")
        return _simple_summary(data_list)


async def _combine_summaries(summaries: List[Dict], start_ts: int, end_ts: int) -> str:
    """合并时段摘要为完整报告"""
    client = _init_llm()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        return _merge_text(summaries, start_ts, end_ts)
    
    try:
        # 格式化时段摘要
        summary_text = "\n\n".join([
            f"**{datetime.fromtimestamp(s['time_start']).strftime('%H:%M')} - {datetime.fromtimestamp(s['time_end']).strftime('%H:%M')}:**\n{s['text']}"
            for s in summaries
        ])
        
        dt_start = datetime.fromtimestamp(start_ts)
        dt_end = datetime.fromtimestamp(end_ts)
        
        # 动态获取当前配置的提示词
        prompts = get_current_prompts()
        system_msg = prompts["report"]["combine_system"]

        user_template = Template(prompts["report"]["combine_user_template"])
        user_msg = user_template.safe_substitute(
            start_time=dt_start.strftime('%Y-%m-%d %H:%M'),
            end_time=dt_end.strftime('%H:%M'),
            summary_text=summary_text
        )
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Combine error: {e}")
        return _merge_text(summaries, start_ts, end_ts)


def _create_plain_report(data_dict: Dict[str, Any], start_ts: int, end_ts: int) -> str:
    """创建简单报告（无LLM）"""
    dt_start = datetime.fromtimestamp(start_ts)
    dt_end = datetime.fromtimestamp(end_ts)
    
    web_data = data_dict.get("web_data", [])
    tips = data_dict.get("tips", [])
    todos = data_dict.get("todos", [])
    
    lines = [
        f"# 活动报告",
        "",
        f"**时间：** {dt_start.strftime('%Y-%m-%d %H:%M')} 至 {dt_end.strftime('%H:%M')}",
        "",
        f"## 📊 概览",
        "",
        f"- 网页浏览：{len(web_data)} 条",
        f"- 智能提示：{len(tips)} 条",
        f"- 待办事项：{len(todos)} 条",
        ""
    ]
    
    # 网页活动列表
    if web_data:
        lines.extend([
            "## 🌐 网页浏览活动",
            ""
        ])
        for idx, item in enumerate(web_data[:20], 1):
            lines.extend([
                f"### {idx}. {item.get('title', '未命名')}",
                "",
                f"- **来源:** {item.get('source', 'unknown')}",
                f"- **时间:** {item.get('create_time', 'unknown')}",
                f"- **链接:** {item.get('url', 'N/A')}",
                f"- **标签:** {', '.join(item.get('tags', []))}",
                ""
            ])
    
    # 智能提示列表
    if tips:
        lines.extend([
            "## 💡 智能提示",
            ""
        ])
        for idx, tip in enumerate(tips, 1):
            lines.extend([
                f"### {idx}. {tip.get('title', '未命名提示')}",
                "",
                f"**类型:** {tip.get('type', 'general')}",
                "",
                tip.get('content', ''),
                "",
                f"*生成时间: {tip.get('create_time', 'unknown')}*",
                ""
            ])
    else:
        lines.extend([
            "## 💡 智能提示",
            "",
            "本时段未生成智能提示。",
            ""
        ])
    
    # 待办事项列表
    if todos:
        lines.extend([
            "## ✅ 待办事项",
            ""
        ])
        completed = [t for t in todos if t.get('status') == 1]
        pending = [t for t in todos if t.get('status') == 0]
        
        lines.extend([
            f"**统计:** 共 {len(todos)} 项，已完成 {len(completed)} 项，待完成 {len(pending)} 项",
            ""
        ])
        
        if pending:
            lines.extend([
                "### 待完成任务",
                ""
            ])
            for todo in pending:
                priority_str = "⭐" * todo.get('priority', 0) if todo.get('priority', 0) > 0 else ""
                lines.extend([
                    f"- [ ] {todo.get('title', '未命名任务')} {priority_str}",
                    f"  - {todo.get('description', '')}",
                    ""
                ])
        
        if completed:
            lines.extend([
                "### 已完成任务",
                ""
            ])
            for todo in completed:
                lines.extend([
                    f"- [x] {todo.get('title', '未命名任务')}",
                    f"  - {todo.get('description', '')}",
                    f"  - 完成时间: {todo.get('end_time', 'unknown')}",
                    ""
                ])
    else:
        lines.extend([
            "## ✅ 待办事项",
            "",
            "本时段未生成待办事项。",
            ""
        ])
    
    lines.extend([
        "## 📈 总结",
        "",
        "本报告基于原始数据自动生成。",
        ""
    ])
    
    return "\n".join(lines)


def _simple_summary(data_list: List[Dict]) -> str:
    """生成简单摘要"""
    if not data_list:
        return "无活动"
    
    titles = [d.get('title', '未命名') for d in data_list[:3]]
    text = f"共 {len(data_list)} 条：" + "、".join(titles)
    
    if len(data_list) > 3:
        text += " 等"
    
    return text


def _merge_text(summaries: List[Dict], start_ts: int, end_ts: int) -> str:
    """合并摘要文本"""
    dt_start = datetime.fromtimestamp(start_ts)
    dt_end = datetime.fromtimestamp(end_ts)
    
    lines = [
        "# 活动报告",
        "",
        f"**时间：** {dt_start.strftime('%Y-%m-%d %H:%M')} 至 {dt_end.strftime('%H:%M')}",
        "",
        "## 分时段活动",
        ""
    ]
    
    for seg in summaries:
        s_dt = datetime.fromtimestamp(seg['time_start'])
        e_dt = datetime.fromtimestamp(seg['time_end'])
        lines.extend([
            f"### {s_dt.strftime('%H:%M')} - {e_dt.strftime('%H:%M')}",
            "",
            seg['text'],
            ""
        ])
    
    lines.extend(["## 总结", "", "汇总各时段活动。"])
    
    return "\n".join(lines)


def _extract_brief(text: str) -> str:
    """提取简要摘要"""
    lines = text.split('\n')
    non_empty = [l.strip() for l in lines if l.strip() and not l.startswith('#')]
    brief_lines = non_empty[:3]
    return ' '.join(brief_lines)[:200]

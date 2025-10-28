"""
智能报告生成模块
基于时间范围和用户数据生成活动分析报告
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import config
from utils.helpers import get_logger
from utils.db import get_web_data, insert_report
from utils.llm import get_openai_client

logger = get_logger(__name__)

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
        title = f"活动报告 {dt_start.strftime('%Y-%m-%d %H:%M')} 至 {dt_end.strftime('%H:%M')}"
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
    data_list = _fetch_time_range_data(start_ts, end_ts)
    
    if not data_list:
        logger.warning("No data for report")
        return None
    
    return await _ask_llm_for_report(data_list, start_ts, end_ts)


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


def _fetch_time_range_data(start_ts: int, end_ts: int) -> List[Dict[str, Any]]:
    """获取时间范围内的数据"""
    try:
        dt_start = datetime.fromtimestamp(start_ts)
        dt_end = datetime.fromtimestamp(end_ts)
        
        logger.info(f"Fetching data: {dt_start.strftime('%Y-%m-%d %H:%M:%S')} to {dt_end.strftime('%Y-%m-%d %H:%M:%S')}")
        
        raw_data = get_web_data(
            start_time=dt_start,
            end_time=dt_end,
            limit=100
        )
        
        logger.info(f"Found {len(raw_data)} records")
        
        # 转换格式
        result = []
        for item in raw_data:
            result.append({
                "id": item["id"],
                "title": item["title"],
                "url": item.get("url", ""),
                "content": item["content"],
                "source": item.get("source", "unknown"),
                "tags": item.get("tags", []),
                "create_time": item.get("create_time", "")
            })
        
        if not result:
            # 调试信息
            all_records = get_web_data(limit=5)
            logger.info(f"Latest 5 records in DB: {len(all_records)}")
            for rec in all_records:
                logger.info(f"  ID={rec['id']}, Title={rec['title']}, Time={rec.get('create_time')}")
        
        return result
    except Exception as e:
        logger.exception(f"Error fetching data: {e}")
        return []


async def _ask_llm_for_report(data_list: List[Dict], start_ts: int, end_ts: int) -> Optional[str]:
    """调用LLM生成报告"""
    client = _init_llm()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        logger.warning("LLM unavailable, using fallback")
        return _create_plain_report(data_list, start_ts, end_ts)
    
    try:
        dt_start = datetime.fromtimestamp(start_ts)
        dt_end = datetime.fromtimestamp(end_ts)
        
        data_json = json.dumps(data_list, ensure_ascii=False, indent=2)
        
        sys_msg = """你是活动分析助手。根据用户数据生成Markdown格式的报告。

报告应包括：
1. 时间段总结
2. 主要活动（按重要性）
3. 发现与洞察
4. 数据统计
5. 结论建议

使用清晰的Markdown格式。"""
        
        user_msg = f"""请分析以下活动数据并生成报告。

时间段：{dt_start.strftime('%Y-%m-%d %H:%M:%S')} - {dt_end.strftime('%Y-%m-%d %H:%M:%S')}

数据：
{data_json}

生成详细报告："""
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        logger.info("LLM report generated successfully")
        return result
    except Exception as e:
        logger.exception(f"LLM error: {e}")
        return _create_plain_report(data_list, start_ts, end_ts)


async def _make_segment_summary(data_list: List[Dict], start_ts: int, end_ts: int) -> Optional[str]:
    """生成时段摘要"""
    client = _init_llm()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        return _simple_summary(data_list)
    
    try:
        data_json = json.dumps(data_list, ensure_ascii=False, indent=2)
        dt_start = datetime.fromtimestamp(start_ts)
        dt_end = datetime.fromtimestamp(end_ts)
        
        prompt = f"""简要总结以下时段活动（不超过100字）：

时段：{dt_start.strftime('%H:%M')} - {dt_end.strftime('%H:%M')}
数据：
{data_json}

摘要："""
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Summary error: {e}")
        return _simple_summary(data_list)


async def _combine_summaries(summaries: List[Dict], start_ts: int, end_ts: int) -> str:
    """合并时段摘要为完整报告"""
    client = _init_llm()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        return _merge_text(summaries, start_ts, end_ts)
    
    try:
        summary_text = "\n\n".join([
            f"**{datetime.fromtimestamp(s['time_start']).strftime('%H:%M')} - {datetime.fromtimestamp(s['time_end']).strftime('%H:%M')}:**\n{s['text']}"
            for s in summaries
        ])
        
        dt_start = datetime.fromtimestamp(start_ts)
        dt_end = datetime.fromtimestamp(end_ts)
        
        prompt = f"""基于以下各时段摘要，生成完整日报。

时间：{dt_start.strftime('%Y-%m-%d %H:%M')} 至 {dt_end.strftime('%H:%M')}

时段摘要：
{summary_text}

生成Markdown格式的完整报告，包含：
1. 整体概述
2. 各时段详情
3. 关键发现
4. 总结建议"""
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Combine error: {e}")
        return _merge_text(summaries, start_ts, end_ts)


def _create_plain_report(data_list: List[Dict], start_ts: int, end_ts: int) -> str:
    """创建简单报告（无LLM）"""
    dt_start = datetime.fromtimestamp(start_ts)
    dt_end = datetime.fromtimestamp(end_ts)
    
    lines = [
        f"# 活动报告",
        "",
        f"**时间：** {dt_start.strftime('%Y-%m-%d %H:%M')} 至 {dt_end.strftime('%H:%M')}",
        "",
        f"## 概览",
        "",
        f"记录 {len(data_list)} 条活动。",
        "",
        "## 活动列表",
        ""
    ]
    
    for idx, item in enumerate(data_list, 1):
        lines.extend([
            f"### {idx}. {item.get('title', '未命名')}",
            "",
            f"- **来源:** {item.get('source', 'unknown')}",
            f"- **时间:** {item.get('create_time', 'unknown')}",
            f"- **标签:** {', '.join(item.get('tags', []))}",
            ""
        ])
    
    lines.extend(["## 总结", "", "基于数据自动生成。"])
    
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

"""
智能报告生成模块
基于时间范围和用户数据生成活动分析报告
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import config
from utils.helpers import get_logger
from utils.db import get_web_data, get_tips, get_todos, insert_report
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
                "content": item["content"],
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
        report_data = {
            "web_data": data_dict.get("web_data", [])[:50],  # 最多50条网页数据
            "tips": data_dict.get("tips", [])[:20],           # 最多20条提示
            "todos": data_dict.get("todos", [])[:30]          # 最多30条待办
        }
        
        data_json = json.dumps(report_data, ensure_ascii=False, indent=2)
        
        sys_msg = """你是一位专业的 AI 个人分析师与策略师。

你的核心任务是整合用户在特定时间段内的活动数据、待办事项列表以及接收到的智能提醒，不仅要生成一份精准的活动总结报告，还要提供具有前瞻性的优化建议。你必须严格依据所提供的全部上下文信息，进行深度聚合、分析与呈现。

---

#### **输入数据说明**

1. **web_data（网页数据）**: 用户浏览的网页记录
   - title: 网页标题
   - url: 网页链接
   - content: 网页内容
   - tags: 标签
   - create_time: 浏览时间

2. **tips（智能提示）**: AI生成的智能建议和洞察
   - title: 提示标题
   - content: 提示内容
   - type: 提示类型（DEEP_DIVE/RESOURCE_RECOMMENDATION/RISK_ANALYSIS等）
   - create_time: 生成时间

3. **todos（待办事项）**: AI提取或用户创建的任务
   - title: 任务标题
   - description: 任务描述
   - status: 状态（0=未完成, 1=已完成）
   - priority: 优先级
   - create_time: 创建时间
   - end_time: 完成时间

---

#### **指导原则 (Guiding Principles)**

1.  **数据保真 (Data Fidelity)**: 你的所有分析、报告和建议，都必须严格源于提供的 `web_data`（活动上下文）、`todos`（待办列表）和 `tips`（智能提醒）数据。严禁任何形式的猜测或信息捏造。

2.  **洞察提炼 (Insight Extraction)**: 你的核心价值在于从原始活动数据 (`web_data`) 中提炼出真正的成就和模式，而不仅仅是罗列。你需要识别因果、总结进展。

3.  **价值导向 (Value-Oriented)**: 报告的重点是影响和成长。优先突出关键成果、学习收获以及能够帮助用户改进的 actionable 建议。

---

#### **报告结构与格式 (Report Structure & Formatting)**

你必须严格遵循以下 Markdown 结构输出报告：

# 每日洞察：{YYYY-MM-DD}

## 概览 (Overview)
* *用2-3句话，结合我的**主要活动**和收到的**关键提醒 (tips)**，高度概括这段时间的核心焦点与节奏。*

## 核心成就 (Key Achievements)
* *你的任务是**从 `web_data` 的活动描述中主动识别并提炼出**重要的成果、完成的阶段性工作或解决的关键问题。例如："我完成了XX项目原型设计"、"我解决了一个困扰已久的Bug"、"我输出了一份深度的市场分析报告"等。*
* **[成就1]**: 我完成了...（描述一项从上下文中分析出的关键成果）
* **[成就2]**: 我解决了...

## 学习与成长 (Learning & Growth)
* *整合 `web_data` 中的学习探索行为和 `tips` 中获得的启发性知识。*
* **[新知识/技能1]**: 我学习了...（记录通过研究、实践或提醒获得的新知识点或技能）
* **[新知识/技能2]**: 我掌握了...

## 待办与计划 (Action Items & Plans)
* *综合以下两个来源，生成待办列表：1. `todos` 中所有未完成的任务（status=0）。2. `web_data` 中明确提及的未来计划或下一步行动。*
* **[任务1]**: 我计划...（清晰列出识别出的、计划在未来进行的任务）
* **[任务2]**: 我需要...

## 优化建议 (Suggestions for Improvement)
* *基于对今天所有活动的整体分析，提出1-2条具体、可行的建议，旨在提高效率、规避风险或开拓思路。*
* **[建议1]**: 例如：“鉴于今天在调试XX上花费了较多时间，未来可以考虑引入自动化测试框架来提高效率。”

## 详细足迹 (Detailed Timeline)
* *按时间顺序，仅整合 `web_data` 中的具体活动记录。*
* **[HH:MM]**: 我浏览了...（描述一项具体的活动，附上关键细节）
* **[HH:MM]**: 我研究了...
```

---

"""
        
        # 计算待办统计
        todos_list = data_dict.get('todos', [])
        todos_pending = [t for t in todos_list if t.get('status') == 0]
        todos_completed = [t for t in todos_list if t.get('status') == 1]
        
        user_msg = f"""**请求 (REQUEST):**
请为我生成一份个人活动报告及优化建议，时间范围从 **{dt_start.strftime('%Y-%m-%d %H:%M:%S')}** 到 **{dt_end.strftime('%Y-%m-%d %H:%M:%S')}**。

---

**数据集 (DATASET):**

* **分析时间戳范围**: `{int(start_ts)}` 至 `{int(end_ts)}`

* **活动数据记录 (Activity Contexts / web_data)**:
```json
{json.dumps(report_data.get('web_data', []), ensure_ascii=False, indent=2)}
```

* **待办事项列表 (Todo List / todos)**:
```json
{json.dumps(report_data.get('todos', []), ensure_ascii=False, indent=2)}
```
*注：此列表用于补充"待办与计划"，但不作为判断"核心成就"的依据。*

* **此期间生成的提醒 (Generated Tips / tips)**:
```json
{json.dumps(report_data.get('tips', []), ensure_ascii=False, indent=2)}
```
*注：请将这些提醒作为归纳"概览"和"学习与成长"时的重要参考。*

---

**数据统计摘要：**
- 活动记录（web_data）：{len(data_dict.get('web_data', []))} 条
- 智能提醒（tips）：{len(data_dict.get('tips', []))} 条
- 待办事项（todos）：{len(todos_list)} 条
  - 未完成：{len(todos_pending)} 项
  - 已完成：{len(todos_completed)} 项

---

**关键指令 (CRITICAL INSTRUCTIONS):**

1. **成就推断**: 你必须从 `web_data` 数据中**分析并推断**出我的核心成就。这是对你分析能力的核心考验。

2. **计划整合**: 在构建"待办与计划"部分时，务必**结合** `todos` 的未完成项和 `web_data` 中隐含的未来意图。

3. **建议生成**: "优化建议"部分必须是**原创的、建设性的**，且紧密关联当天活动中发现的模式或挑战。

4. **信息源分离**: 严格遵守每个板块的数据来源指示，确保报告的准确性和逻辑性。

5. **第一人称视角**: 使用"我"进行叙述，增强报告的代入感。

---

请严格按照系统指令中定义的报告结构生成完整的个人活动洞察报告。"""
        
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
        
        prompt = f"""请用第一人称（"我"）简要总结以下时段的活动（不超过100字）。

**时段**: {dt_start.strftime('%H:%M')} - {dt_end.strftime('%H:%M')}

**活动数据**:
{data_json}

**要求**:
- 使用第一人称叙述（例如："我浏览了..."、"我研究了..."）
- 提炼关键活动，而非简单罗列
- 突出成果和重点

**摘要**:"""
        
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
        
        prompt = f"""你是一位专业的 AI 个人分析师与策略师。

**任务**: 基于以下各时段摘要，为我生成一份完整的个人活动洞察报告。

**时间范围**: {dt_start.strftime('%Y-%m-%d %H:%M')} 至 {dt_end.strftime('%H:%M')}

**时段摘要数据**:
{summary_text}

**输出要求**:

请严格按照以下 Markdown 结构生成报告（使用第一人称"我"）：

# 每日洞察：{dt_start.strftime('%Y-%m-%d')}

## 概览 (Overview)
* 用2-3句话，高度概括我这一天的核心焦点与节奏。

## 核心成就 (Key Achievements)
* **[成就1]**: 我完成了...（从各时段摘要中提炼出关键成果）
* **[成就2]**: 我解决了...

## 学习与成长 (Learning & Growth)
* **[新知识/技能1]**: 我学习了...
* **[新知识/技能2]**: 我掌握了...

## 待办与计划 (Action Items & Plans)
* **[任务1]**: 我计划...（从摘要中识别的未来行动）
* **[任务2]**: 我需要...

## 优化建议 (Suggestions for Improvement)
* **[建议1]**: 基于今天的活动模式，提出具体、可行的优化建议。

## 详细足迹 (Detailed Timeline)
* 按时间顺序整理各时段的活动要点。

**关键要求**:
1. 使用第一人称（"我"）进行叙述
2. 从时段摘要中提炼真正的成就，而非简单罗列
3. 提供原创的、建设性的优化建议
4. 保持报告的洞察力和价值导向
5. 段落分明，每段标题前面要有图标，类似 github 的 readme 格式"""
        
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

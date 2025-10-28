"""
活动记录生成模块
基于数据源智能总结用户活动
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import config
from utils.helpers import get_logger
from utils.db import get_web_data, get_screenshots, insert_activity
from utils.llm import get_openai_client

logger = get_logger(__name__)

# 客户端缓存
_client = None


def _init_client():
    """初始化客户端"""
    global _client
    if _client is None:
        _client = get_openai_client()
    return _client


async def create_activity_record(time_span_mins: int = 15) -> Dict[str, Any]:
    """
    创建活动记录（主函数）
    
    Args:
        time_span_mins: 时间跨度（分钟）
    
    Returns:
        活动数据字典
    """
    try:
        finish_time = datetime.now()
        begin_time = finish_time - timedelta(minutes=time_span_mins)
        
        # 收集数据
        data_items = _collect_data_sources(begin_time, finish_time)
        
        if not data_items:
            logger.warning(f"No data in last {time_span_mins} minutes")
            return {"success": False, "message": f"过去{time_span_mins}分钟无数据"}
        
        # 生成活动记录
        activity_info = await _analyze_and_summarize(data_items, begin_time, finish_time)
        
        if not activity_info:
            return {"success": False, "message": "活动分析失败"}
        
        # 存储
        record_id = insert_activity(
            title=activity_info['title'],
            description=activity_info['description'],
            resources=activity_info.get('resources', {}),
            start_time=begin_time,
            end_time=finish_time
        )
        
        logger.info(f"Activity record created: ID={record_id}, Title={activity_info['title']}")
        
        return {
            "success": True,
            "activity_id": record_id,
            **activity_info
        }
    except Exception as e:
        logger.exception(f"Activity creation error: {e}")
        return {"success": False, "message": str(e)}


def _collect_data_sources(start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
    """收集数据源"""
    try:
        logger.info(f"Collecting data: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        items = []
        
        # 获取网页数据
        web_records = get_web_data(
            start_time=start_dt,
            end_time=end_dt,
            limit=50
        )
        logger.info(f"Found {len(web_records)} web records")
        
        for record in web_records:
            items.append({
                "type": "web",
                "title": record["title"],
                "url": record.get("url", ""),
                "content": record["content"],
                "source": record.get("source", "unknown"),
                "tags": record.get("tags", []),
                "create_time": record.get("create_time", "")
            })
        
        # 获取截图（如果有）
        try:
            screenshots = get_screenshots(
                start_time=start_dt,
                end_time=end_dt,
                limit=10
            )
            
            for shot in screenshots:
                items.append({
                    "type": "screenshot",
                    "path": shot["path"],
                    "window": shot.get("window", ""),
                    "create_time": shot.get("create_time", "")
                })
            
            logger.info(f"Found {len(screenshots)} screenshots")
        except Exception as e:
            logger.debug(f"Screenshot fetch failed: {e}")
        
        return items
    except Exception as e:
        logger.exception(f"Data collection error: {e}")
        return []


async def _analyze_and_summarize(data_items: List[Dict], start_dt: datetime, end_dt: datetime) -> Optional[Dict[str, Any]]:
    """分析数据并生成摘要"""
    client = _init_client()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        logger.warning("LLM unavailable, using basic summary")
        return _create_basic_summary(data_items, start_dt, end_dt)
    
    try:
        # 准备数据（限制大小）
        limited_data = data_items[:20]
        data_json = json.dumps(limited_data, ensure_ascii=False, indent=2)
        
        system_msg = """你是一位专业的**网页活动分析师 (Web Activity Analyst)**。

你的核心任务是将用户在一段时间内的原始网页浏览数据，转化为一份简洁、结构化且富有洞察力的活动摘要。你的目标是帮助用户一目了然地理解他们最近在网上做什么、关注什么以及潜在的目标是什么。

---

#### **核心能力 (Core Competencies)**

1.  **主题识别 (Topic Recognition)**: 从 URL、网页标题和内容片段中精准识别出核心活动主题。
2.  **行为聚合 (Behavior Aggregation)**: 将围绕同一目标的多次浏览行为（例如，为了解决一个问题而查阅的多个标签页）智能地聚合成一个连贯的活动。
3.  **意图推断 (Intent Inference)**: 基于浏览模式，推断用户当前的主要意图（如：研究、学习、规划、编码、娱乐等）。
4.  **简洁总结 (Concise Summarization)**: 用最精炼的语言概括复杂的浏览活动。

---

#### **分析维度 (Dimensions of Analysis)**

* **网站与应用 (Website & Web App)**: 用户主要在哪几个网站或在线工具上活动？（例如：GitHub, Kimi Chat, Google Docs, 飞书）。
* **内容主题 (Content Topic)**: 用户正在阅读、编辑或互动的内容是关于什么的？（例如："Python 性能优化"、"Q4 市场营销计划"）。
* **用户意图 (User Intent)**: 用户浏览这些网页似乎是为了达成什么目标？（例如："解决一个技术难题"、"撰写一份项目文档"、"学习一门新技能"）。
* **浏览模式 (Browsing Pattern)**: 用户的浏览行为呈现什么模式？（例如："围绕单一主题的深度钻研"、"在多个不同主题的项目间频繁切换"）。

---

#### **输出要求 (Output Requirements)**

1.  **标题 (`title`) 要求**:
    * 不超过30个字符，高度概括核心活动。
    * 应体现出用户的**动作**和**对象**，例如"研究并实现Docker部署方案"、"规划Q4市场营销活动"。
    * 避免泛泛而谈，如"浏览了多个网页"或"查看了一些文档"。

2.  **描述 (`description`) 要求**:
    * 150-200个字符，对活动进行生动具体的描述。
    * 遵循**"主要活动 → 具体操作 → 目标/结果"**的逻辑层次。
    * 示例："正在深入研究如何使用Docker部署Node.js应用，查阅了官方文档和多篇技术博客，目标是搭建一个可行的本地开发环境。🚀"

3.  **分类分布 (`category_distribution`) 要求**:
    * 基于网站的域名和内容进行分类估算（例如: `github.com` -> work, `youtube.com` -> learning/entertainment, `notion.so` -> work/life）。

4.  **洞察提取 (`extracted_insights`) 要求**:
    * **`potential_todos`**: 严格按照**用户中心原则**，从网页内容中识别潜在待办。重点关注任务管理网站（Jira, 飞书）、代码协作平台（GitHub）、在线文档（Notion, 语雀）和AI对话中的行动意图。
    * **`tip_suggestions`**: 提出与浏览活动相关的具体建议。例如，若用户在多个技术博客间切换，可建议"使用稍后读工具（如 Instapaper）来组织阅读列表"。
    * **`key_entities`**: 从网页标题和内容中提取的关键实体（如：项目名 "Project Phoenix"、技术栈 "React"、人名）。
    * **`focus_areas`**: 对 `key_entities` 进行归纳，形成更高层次的关注领域（如："前端开发"、"项目管理"）。
    * **`work_patterns`**:
        * `continuous_work_time`: 估算围绕同一主题连续浏览的时间。
        * `task_switching_count`: 估算在多个不相关主题之间切换的次数。

5.  **JSON格式**:
```json
{
  "title": "活动标题（简短）",
  "description": "详细描述（50-200字）",
  "activity_type": "类型标签",
  "key_points": ["要点1", "要点2"],
  "resources": {
    "urls": ["相关URL"],
    "keywords": ["关键词"]
  },
  "category_distribution": {
        "work": 0.7,
        "learning": 0.2,
        "entertainment": 0.05,
        "life": 0.05,
        "other": 0.0
      },
      "extracted_insights": {
        "potential_todos": [
          {"content": "任务描述", "description": "相关背景"}
        ],
        "tip_suggestions": [
          {"topic": "主题", "reason": "原因", "suggestion": "建议"}
        ],
        "key_entities": ["实体1", "实体2"],
        "focus_areas": ["领域1", "领域2"],
        "work_patterns": {
          "continuous_work_time": 45,
          "task_switching_count": 3
        }
      }
}
```"""
        
        user_msg = f"""分析以下时段的活动数据。

时间：{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}

数据：
{data_json}

请严格根据你的系统规则，仅分析以下**网页浏览上下文**数据，并以指定的 JSON 格式返回一份简洁的实时活动总结"""
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.info("LLM analysis completed")
        
        # 解析结果
        activity_data = _parse_activity_json(result_text)
        return activity_data if activity_data else _create_basic_summary(data_items, start_dt, end_dt)
    except Exception as e:
        logger.exception(f"LLM analysis error: {e}")
        return _create_basic_summary(data_items, start_dt, end_dt)


def _parse_activity_json(text: str) -> Optional[Dict[str, Any]]:
    """解析活动JSON"""
    try:
        # 提取JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        data = json.loads(text.strip())
        
        # 验证必需字段
        if 'title' in data and 'description' in data:
            return data
        return None
    except Exception as e:
        logger.error(f"JSON parse error: {e}")
        return None


def _create_basic_summary(data_items: List[Dict], start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """创建基础摘要（无LLM）"""
    web_items = [d for d in data_items if d.get('type') == 'web']
    
    if not web_items:
        title = f"活动记录 {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
        desc = "本时段无明显活动记录。"
    else:
        titles = [item['title'] for item in web_items[:3]]
        title = f"浏览活动 {start_dt.strftime('%H:%M')}"
        desc = f"浏览了 {len(web_items)} 个页面，包括：" + "、".join(titles)
        if len(web_items) > 3:
            desc += " 等"
    
    urls = [item.get('url', '') for item in web_items if item.get('url')]
    keywords = []
    for item in web_items:
        keywords.extend(item.get('tags', []))
    
    return {
        "title": title,
        "description": desc,
        "activity_type": "web_browsing",
        "key_points": titles[:5] if web_items else [],
        "resources": {
            "urls": urls[:10],
            "keywords": list(set(keywords))[:10]
        }
    }

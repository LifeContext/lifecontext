"""
活动记录生成模块
基于数据源智能总结用户活动
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import config
from utils.helpers import (
    get_logger,
    estimate_tokens,
    truncate_web_data_by_tokens,
    calculate_available_context_tokens
)
from utils.json_utils import parse_llm_json_response
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
        
        # 先收集所有 web 数据
        for record in web_records:
            items.append({
                "type": "web",
                "title": record["title"],
                "url": record.get("url", ""),
                "content": record.get("content", ""),
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
        # 分离 web 数据和其他数据
        web_items = [item for item in data_items if item.get('type') == 'web']
        other_items = [item for item in data_items if item.get('type') != 'web']
        
        # 估算其他数据的 token
        other_data_tokens = estimate_tokens(json.dumps(other_items, ensure_ascii=False))
        
        # 计算可用于 web_data 的 token 数
        available_tokens = calculate_available_context_tokens('activity', other_data_tokens)
        
        # 使用动态截取函数处理 web_data，使用 metadata 替代 content
        web_items_trimmed = truncate_web_data_by_tokens(web_items, max_tokens=available_tokens, use_metadata=True)
        
        # 合并数据
        limited_data = other_items + web_items_trimmed
        data_json = json.dumps(limited_data, ensure_ascii=False, indent=2)
        
        system_msg = """你是一位顶级的用户行为分析师与数据叙事专家 (Principal User Behavior Analyst & Data Storyteller)。你的核心能力是从一系列独立的分析报告中，精准地聚合出连贯的活动主题，并以富有洞察力的方式总结用户的行为模式。

## 任务目标 (Task Goal)

你的核心目标是将一段时间内、一系列零散的网页分析报告，转化为一份简洁、连贯、结构化的活动总结。这份总结必须清晰地概括出用户的核心活动、关注领域和工作模式，帮助用户一目了然地回顾自己的行为。**你的任务是总结和分析，而不是生成新的待办事项或建议。**

## 输入数据说明 (Input Data Description)

你将收到一个名为`web_analysis_reports`的JSON数组。数组中的每一个对象，都是由第一节点生成的、对用户单个浏览网页的预分析报告。

## 执行步骤 (Execution Steps)

你必须严格遵循以下五个步骤来完成任务：

1. **第一步：主题聚合与意图推断。** 遍历所有输入的`web_analysis_reports`，综合分析其`metadata_analysis`（特别是`topics`, `keywords`, `category`字段）和`detailed_summary`，以识别出贯穿整个时间段的**1-2个核心活动主题**，并推断用户的主要意图（例如：研究技术、撰写文档、项目规划、学习新知等）。
2. **第二步：生成叙事性摘要。** 基于你在上一步聚合出的主题和意图，撰写`title`和`description`。
    - **`title`**：必须简短有力（不超过30字符），并采用“动词+宾语”的格式来概括核心行动。例如：“研究并实现Docker部署方案”。
    - **`description`**：必须生动具体（150-200字符），并遵循**“主要活动 → 具体操作 → 潜在目标”**的逻辑层次来描述。
3. **第三步：进行模式与分布分析。**
    - **分类估算 (`category_distribution`)**: 统计所有报告中`category`字段的分布情况，并计算出各类别的百分比。
    - **工作节律分析 (`work_patterns`)**: 基于报告的时间戳和主题连贯性，估算出`continuous_work_time`（围绕同一主题连续工作的大致分钟数）和`task_switching_count`（在多个不相关主题之间切换的大致次数）。
4. **第四步：提取核心实体与领域。**
    - **实体提取 (`key_entities`)**: 遍历所有报告的`keywords`和`topics`，将它们整合、去重，形成一份关键实体列表。
    - **领域归纳 (`focus_areas`)**: 对`key_entities`列表进行更高层次的归纳，总结出用户关注的1-3个核心领域（例如：“前端开发”、“项目管理”）。
5. **第五步：格式化封装输出。** 将以上所有分析结果，严格按照下方`## 输出要求`中定义的JSON格式进行封装。确保所有字段都已填充，且JSON格式合法。

## 输出要求 (Output Requirements)

你必须返回一个**纯 JSON 对象**，不要使用 markdown 代码块包裹，不要添加任何解释性文字。**你的输出严禁包含任何`potential_todos`或`tip_suggestions`字段。**

### JSON 结构示例:

```json
{
  "title": "活动标题，简短、行动导向",
  "description": "详细的活动描述，遵循"主要活动 → 具体操作 → 潜在目标"的逻辑",
  "activity_type": "一个最能概括意图的类型标签，例如：Researching, Writing, Planning, Learning, Coding, Entertainment",
  "category_distribution": {
    "work": 0.7,
    "learning": 0.2,
    "entertainment": 0.05,
    "life": 0.05,
    "other": 0.0
  },
  "extracted_insights": {
    "key_entities": [
      "从所有报告中提取的关键实体，如技术名、项目名等"
    ],
    "focus_areas": [
      "对关键实体进行归纳后的核心关注领域"
    ],
    "work_patterns": {
      "continuous_work_time": 45,
      "task_switching_count": 3
    }
  },
  "resources": {
    "urls": [
      "本次活动中涉及到的最关键的1-3个URL"
    ],
    "keywords": [
      "本次活动最核心的3-5个关键词"
    ]
  }
}
```

### 关键要求:

1. **输出格式**: 直接输出 JSON 对象，以 `{` 开始，以 `}` 结束
2. **不要包裹**: 不要用 \`\`\`json 或 \`\`\` 包裹 JSON
3. **不要注释**: JSON 外不要有任何解释文字
4. **所有字段必填**: 确保上述所有字段都有值
5. **数值格式**: category_distribution 中的比例相加应为 1.0
"""
        
        user_msg = f"""作为用户行为分析师与数据叙事专家，请严格按照你的角色、目标和要求，仅分析以下网页浏览分析报告集合，并返回一份简洁的实时活动总结。

**网页分析报告集合 (web_analysis_reports):**
{data_json}

请输出你的活动总结报告。"""
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 详细打印 LLM 返回信息
        logger.info("=" * 60)
        logger.info("LLM 返回完成")
        logger.info(f"返回长度: {len(result_text)} 字符")
        logger.info(f"开始字符: {result_text[:100] if len(result_text) > 100 else result_text}")
        logger.info(f"结束字符: {result_text[-100:] if len(result_text) > 100 else result_text}")
        logger.info(f"是否以 {{ 开头: {result_text.startswith('{')}")
        logger.info(f"是否以 }} 结尾: {result_text.endswith('}')}")
        logger.info(f"是否包含代码块: {'```' in result_text}")
        logger.info("=" * 60)
        
        # 使用通用 JSON 解析工具
        logger.info("开始解析 JSON...")
        activity_data = parse_llm_json_response(
            result_text,
            expected_type='object',
            save_on_error=True,
            error_file_prefix='failed_activity_response'
        )
        
        # 打印解析结果
        if activity_data is not None:
            logger.info("=" * 60)
            logger.info("✅ JSON 解析成功！")
            logger.info(f"  - title: {activity_data.get('title', 'N/A')}")
            logger.info(f"  - activity_type: {activity_data.get('activity_type', 'N/A')}")
            logger.info(f"  - description 长度: {len(activity_data.get('description', ''))} 字符")
            logger.info("=" * 60)
            return activity_data
        else:
            logger.warning("=" * 60)
            logger.warning("⚠️ JSON 解析失败，使用基础摘要作为备选")
            logger.warning("=" * 60)
            return _create_basic_summary(data_items, start_dt, end_dt)
    except Exception as e:
        logger.exception(f"LLM analysis error: {e}")
        return _create_basic_summary(data_items, start_dt, end_dt)


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

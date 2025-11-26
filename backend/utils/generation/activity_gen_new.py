"""
活动记录生成模块
基于数据源智能总结用户活动
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from string import Template
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
from utils.prompt_config import get_current_prompts

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
        
        # 动态获取当前配置的提示词
        prompts = get_current_prompts()
        system_msg = prompts["activity"]["system"]

        user_template = Template(prompts["activity"]["user_template"])
        user_msg = user_template.safe_substitute(data_json=data_json)
        
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

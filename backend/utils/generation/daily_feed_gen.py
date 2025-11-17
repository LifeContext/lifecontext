"""
每日Feed卡片生成模块
生成包含 Summary、Todo、News、Knowledge 等类型的每日推荐卡片
"""

import json
import hashlib
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
from utils.db import get_web_data, get_todos, get_activities
from utils.llm import get_openai_client
from utils.vectorstore import search_similar_content
from utils.prompt_config import get_current_prompts
from utils.db import insert_daily_feed, get_daily_feed

logger = get_logger(__name__)

# 全局LLM客户端缓存
_client_cache = None


def _init_llm():
    """初始化LLM客户端"""
    global _client_cache
    if _client_cache is None:
        _client_cache = get_openai_client()
    return _client_cache


def _generate_cover_url(card_type: str, title: str, date_str: str) -> str:
    """
    生成封面图片URL
    使用卡片类型+标题+日期作为seed，确保同一天同一卡片的封面一致
    
    Args:
        card_type: 卡片类型 (summary/todo/news/knowledge)
        title: 卡片标题
        date_str: 日期字符串 (YYYY-MM-DD)
    
    Returns:
        封面图片URL
    """
    # 生成稳定的seed
    seed_string = f"{card_type}_{title}_{date_str}"
    safe_seed = hashlib.md5(seed_string.encode()).hexdigest()[:16]
    
    return f"https://picsum.photos/seed/{safe_seed}/800/420"


def _assign_sequential_ids(cards: List[dict], start: int = 1) -> List[dict]:
    """为 cards 列表按顺序添加或覆盖 id 字段
    """
    if not isinstance(cards, list):
        return cards
    for idx, card in enumerate(cards, start=start):
        try:
            if isinstance(card, dict):
                card['id'] = idx
        except Exception:
            continue
    return cards


async def generate_daily_feed(lookback_hours: int = 24) -> Dict[str, Any]:
    """
    生成每日Feed卡片（主入口）
    
    Args:
        lookback_hours: 向前回溯的小时数，默认24小时
    
    Returns:
        包含卡片列表的字典
    """
    try:
        now = datetime.now()
        past = now - timedelta(hours=lookback_hours)
        date_str = now.strftime('%Y-%m-%d')
        
        logger.info(f"Generating daily feed for {date_str}, lookback: {lookback_hours}h")
        
        # 收集上下文数据
        context = _gather_feed_context(past, now)
        
        if not context['has_content']:
            logger.warning(f"Insufficient data for daily feed generation")
            return {
                "success": False,
                "message": "insufficient data for daily feed generation"
            }
        
        # 生成各类卡片
        cards = []
        
        # 1. 生成Summary卡片（1张）
        summary_card = await _generate_summary_card(context, date_str)
        if summary_card:
            cards.append(summary_card)
        
        # 2. 生成Todo卡片（1张）
        todo_card = await _generate_todo_card(context, date_str)
        if todo_card:
            cards.append(todo_card)
        
        # 3. 生成News推荐卡片（3-5张）
        news_cards = await _generate_news_cards(context, date_str, count=4)
        cards.extend(news_cards)
        
        # 4. 生成Knowledge推荐卡片（3-5张）
        knowledge_cards = await _generate_knowledge_cards(context, date_str, count=4)
        cards.extend(knowledge_cards)
        
        logger.info(f"Generated {len(cards)} feed cards")

        # 为 cards 按顺序分配 id（从1开始），然后保存到数据库
        try:
            cards = _assign_sequential_ids(cards, start=1)
        except Exception:
            # 若出错则继续使用原始 cards
            pass

        # 将生成的Feed存储到数据库
        feed_id = insert_daily_feed(date_str, cards, len(cards))
        if feed_id:
            logger.info(f"Daily feed saved to database with ID {feed_id}")
        else:
            logger.warning("Failed to save daily feed to database")
        
        return {
            "success": True,
            "date": date_str,
            "cards": cards,
            "total_count": len(cards),
            "feed_id": feed_id
        }
        
    except Exception as e:
        logger.exception(f"Failed to generate daily feed: {e}")
        return {
            "success": False,
            "message": str(e)
        }


def _gather_feed_context(start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """收集Feed生成所需的上下文数据"""
    try:
        logger.info(f"Gathering feed context: {start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}")
        
        context = {
            "has_content": False,
            "web_data": [],
            "activities": [],
            "todos": [],
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat()
        }
        
        # 获取网页数据
        web_data = get_web_data(
            start_time=start_dt,
            end_time=end_dt,
            limit=100
        )
        
        if web_data and len(web_data) > 0:
            context['web_data'] = web_data
            context['has_content'] = True
            logger.info(f"Found {len(web_data)} web data entries")
        
        # 获取活动记录
        activities = get_activities(
            start_time=start_dt,
            end_time=end_dt,
            limit=50
        )
        
        if activities and len(activities) > 0:
            context['activities'] = activities
            context['has_content'] = True
            logger.info(f"Found {len(activities)} activities")
        
        # 获取待办事项（未完成的）
        todos = get_todos(status=0, limit=20)  # status=0表示未完成
        
        if todos and len(todos) > 0:
            context['todos'] = todos
            logger.info(f"Found {len(todos)} pending todos")
        
        return context
        
    except Exception as e:
        logger.exception(f"Error gathering feed context: {e}")
        return {
            "has_content": False,
            "web_data": [],
            "activities": [],
            "todos": []
        }


async def _generate_summary_card(context: Dict[str, Any], date_str: str) -> Optional[Dict[str, Any]]:
    """
    生成Summary总结卡片
    使用完整的report生成逻辑，返回Markdown格式的报告
    """
    try:
        logger.info("Generating summary card...")
        
        # 导入report生成函数
        from utils.generation.report_gen_new import create_activity_report
        from datetime import datetime
        
        # 将时间范围转换为时间戳
        start_dt = datetime.fromisoformat(context['start_time'])
        end_dt = datetime.fromisoformat(context['end_time'])
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())
        
        # 使用现有的report生成逻辑
        result = await create_activity_report(start_ts, end_ts)
        
        if not result.get('success'):
            logger.warning(f"Failed to generate report: {result.get('message')}")
            return None
        
        # 获取报告内容（Markdown格式）
        report_content = result.get('content', '')
        
        if not report_content:
            logger.warning("Failed to generate summary card content")
            return None
        
        # 构建卡片
        card = {
            "type": "summary",
            "title": f"今日总结 - {date_str}",
            "content": report_content,  # Markdown格式的完整报告
            "cover": _generate_cover_url("summary", "daily_summary", date_str),
            "source_url": None  # 总结卡片没有特定来源URL
        }
        
        logger.info("Summary card generated successfully")
        return card
        
    except Exception as e:
        logger.exception(f"Error generating summary card: {e}")
        return None


async def _generate_todo_card(context: Dict[str, Any], date_str: str) -> Optional[Dict[str, Any]]:
    """
    生成Todo待办卡片
    使用LLM分析待办事项，生成结构化的Markdown清单
    """
    try:
        logger.info("Generating todo card...")
        
        todos = context.get('todos', [])
        
        if not todos or len(todos) == 0:
            logger.info("No pending todos, skipping todo card")
            return None
        
        client = _init_llm()
        
        # 准备待办数据JSON
        todos_json = json.dumps(todos, ensure_ascii=False, indent=2)
        
        # 获取prompt
        todo_prompt = PROMPTS.get("todo_summary", {})
        system_prompt = todo_prompt.get("system", "")
        user_template = todo_prompt.get("user_template", "")
        
        # 添加日志检查prompt是否被正确加载
        if system_prompt:
            logger.info(f"Using configured todo_summary prompt (length: {len(system_prompt)})")
        else:
            logger.warning("todo_summary prompt not found in PROMPTS, using fallback")
        
        # 如果没有配置prompt，使用默认的（保留向后兼容）
        if not system_prompt:
            system_prompt = """你是一个智能待办事项管理助手。请将待办事项按优先级整理成结构化的Markdown清单。

输出Markdown格式，包含：
- 概览（统计和优先级分布）
- 高优先级任务（🔴）
- 中优先级任务（🟡）
- 低优先级任务（🟢）
- 执行建议"""
        
        if not user_template:
            user_template = """请基于以下待办事项数据，生成结构化的待办任务清单：

$todos_json

直接返回Markdown格式内容，不要添加代码块标记。"""
        
        user_prompt = Template(user_template).safe_substitute(
            todos_json=todos_json
        )
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 直接使用Markdown文本作为卡片内容
        card = {
            "type": "todo",
            "title": f"待办任务清单 ({len(todos)}项)",
            "content": result_text,
            "cover": _generate_cover_url("todo", "todo_list", date_str),
            "source_url": None  # 待办卡片没有特定来源URL
        }
        
        logger.info("Todo card generated successfully with Markdown content")
        return card
        
    except Exception as e:
        logger.exception(f"Error generating todo card: {e}")
        return None


async def _generate_news_cards(context: Dict[str, Any], date_str: str, count: int = 4) -> List[Dict[str, Any]]:
    """
    生成News新闻/资讯推荐卡片
    基于用户今天的行为推荐相关新闻
    每条新闻生成一张独立的卡片
    """
    try:
        logger.info(f"Generating up to {count} news cards...")
        
        client = _init_llm()
        
        # 准备上下文数据
        web_data = context.get('web_data', [])
        activities = context.get('activities', [])
        
        if not web_data and not activities:
            logger.info("No data for news generation")
            return []
        
        # 为news推荐预留足够的上下文空间（约8000 tokens）
        max_context_tokens = 8000
        truncated_web_data = truncate_web_data_by_tokens(
            web_data, 
            max_tokens=max_context_tokens,
            content_field='detailed_summary',  # 使用detailed_summary字段
            use_metadata=False
        )
        
        logger.info(f"News generation: using {len(truncated_web_data)}/{len(web_data)} web_data items after token truncation")
        
        # 构建上下文JSON
        context_data = {
            "web_data": truncated_web_data,
            "activities": activities[:30]  # activities通常较短，可以保留更多
        }
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
        
        # 获取prompt
        news_prompt = PROMPTS.get("news_recommendation", {})
        system_prompt = news_prompt.get("system", "")
        user_template = news_prompt.get("user_template", "")
        
        # 添加日志检查prompt是否被正确加载
        if system_prompt:
            logger.info(f"Using configured news_recommendation prompt (length: {len(system_prompt)})")
        else:
            logger.warning("news_recommendation prompt not found in PROMPTS, using fallback")
        
        # 如果没有配置prompt，使用默认的
        if not system_prompt:
            system_prompt = """你是一位智能新闻推荐助手。基于用户今天的浏览和活动数据，推荐相关的新闻或资讯。

返回JSON格式，每条新闻包含：
- title: 新闻标题
- content: Markdown格式的新闻内容
- source_url: 来源URL
- category: 分类（重磅发布|深度洞察|行业动态）

输出格式：
{
  "recommendations": [
    {
      "title": "...",
      "content": "## 📌 ...",
      "source_url": "...",
      "category": "..."
    }
  ]
}"""
        
        if not user_template:
            user_template = """请基于以下用户数据，推荐相关的新闻或资讯：

$context_json

请生成推荐列表（最多$count个）。"""
        
        user_prompt = Template(user_template).safe_substitute(
            context_json=context_json,
            count=count
        )
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content.strip()
        result = parse_llm_json_response(result_text)
        
        if not result or 'recommendations' not in result:
            logger.warning("Failed to parse news recommendations")
            return []
        
        recommendations = result['recommendations']
        
        # 为每条新闻生成一张独立的卡片
        cards = []
        for idx, rec in enumerate(recommendations[:count]):
            title = rec.get('title', '')
            content = rec.get('content', '')
            source_url = rec.get('source_url', '')
            category = rec.get('category', '技术资讯')
            
            if not title or not content:
                continue
            
            card = {
                "type": "news",
                "title": title,
                "content": content,  # Markdown格式的新闻内容
                "cover": _generate_cover_url("news", title, date_str),
                "source_url": source_url
            }
            cards.append(card)
        
        logger.info(f"Generated {len(cards)} news cards")
        return cards
        
    except Exception as e:
        logger.exception(f"Error generating news cards: {e}")
        return []


async def _generate_knowledge_cards(context: Dict[str, Any], date_str: str, count: int = 4) -> List[Dict[str, Any]]:
    """
    生成Knowledge知识类推荐卡片
    基于用户今天的学习和探索推荐相关知识
    每条知识生成一张独立的卡片
    """
    try:
        logger.info(f"Generating up to {count} knowledge cards...")
        
        client = _init_llm()
        
        # 准备上下文数据
        web_data = context.get('web_data', [])
        activities = context.get('activities', [])
        
        if not web_data and not activities:
            logger.info("No data for knowledge generation")
            return []
        
        # 为knowledge推荐预留足够的上下文空间
        max_context_tokens = 10000
        truncated_web_data = truncate_web_data_by_tokens(
            web_data, 
            max_tokens=max_context_tokens,
            content_field='detailed_summary',  # 使用detailed_summary字段
            use_metadata=False
        )
        
        logger.info(f"Knowledge generation: using {len(truncated_web_data)}/{len(web_data)} web_data items after token truncation")
        
        # 构建上下文JSON
        context_data = {
            "web_data": truncated_web_data,
            "activities": activities[:30]  # activities通常较短，可以保留更多
        }
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
        
        # 获取prompt
        knowledge_prompt = PROMPTS.get("knowledge_recommendation", {})
        system_prompt = knowledge_prompt.get("system", "")
        user_template = knowledge_prompt.get("user_template", "")
        
        # 添加日志检查prompt是否被正确加载
        if system_prompt:
            logger.info(f"Using configured knowledge_recommendation prompt (length: {len(system_prompt)})")
        else:
            logger.warning("knowledge_recommendation prompt not found in PROMPTS, using fallback")
        
        # 如果没有配置prompt，使用默认的（保留向后兼容）
        if not system_prompt:
            system_prompt = """你是一位智能知识推荐助手。基于用户今天的学习和浏览数据，推荐相关的知识类内容。

返回JSON格式，每条知识包含：
- title: 知识点标题
- content: Markdown格式的知识内容（What-Why-How-Value结构）
- source_url: 来源URL
- learning_value: 学习价值

输出格式：
{
  "recommendations": [
    {
      "title": "...",
      "content": "## 📚 ...",
      "source_url": "...",
      "learning_value": "..."
    }
  ]
}"""
        
        if not user_template:
            user_template = """请基于以下用户数据，推荐相关的知识内容：

$context_json

请生成推荐列表（最多$count个知识点）。"""
        
        user_prompt = Template(user_template).safe_substitute(
            context_json=context_json,
            count=count
        )
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        result_text = response.choices[0].message.content.strip()
        result = parse_llm_json_response(result_text)
        
        if not result or 'recommendations' not in result:
            logger.warning("Failed to parse knowledge recommendations")
            return []
        
        recommendations = result['recommendations']
        
        # 为每条知识生成一张独立的卡片
        cards = []
        for idx, rec in enumerate(recommendations[:count]):
            title = rec.get('title', '')
            content = rec.get('content', '')
            source_url = rec.get('source_url', '')
            learning_value = rec.get('learning_value', '')
            
            if not title or not content:
                continue
            
            card = {
                "type": "knowledge",
                "title": title,
                "content": content,  # Markdown格式的知识内容
                "cover": _generate_cover_url("knowledge", title, date_str),
                "source_url": source_url
            }
            cards.append(card)
        
        logger.info(f"Generated {len(cards)} knowledge cards")
        return cards
        
    except Exception as e:
        logger.exception(f"Error generating knowledge cards: {e}")
        return []

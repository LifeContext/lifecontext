"""
智能提示生成模块
分析用户行为并提供智能建议
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import config
from utils.helpers import get_logger
from utils.db import get_web_data, get_activities, get_todos, insert_tip, get_tips
from utils.llm import get_openai_client

logger = get_logger(__name__)

# LLM客户端缓存
_llm = None


def _get_client():
    """获取LLM客户端"""
    global _llm
    if _llm is None:
        _llm = get_openai_client()
    return _llm


async def generate_smart_tips(history_mins: int = 60) -> Dict[str, Any]:
    """
    生成智能提示（主入口）
    
    Args:
        history_mins: 历史回溯分钟数
    
    Returns:
        提示数据字典
    """
    try:
        current_time = datetime.now()
        past_time = current_time - timedelta(minutes=history_mins)
        
        # 收集上下文
        context_info = _assemble_context(past_time, current_time)
        
        if not context_info['has_data']:
            logger.warning(f"No data for tip generation in last {history_mins} minutes")
            return {"success": False, "message": "数据不足"}
        
        # 生成提示
        tips_list = await _produce_tips(context_info, history_mins)
        
        if not tips_list:
            return {"success": False, "message": "提示生成失败"}
        
        # 保存提示
        tip_ids = []
        for tip_item in tips_list:
            tid = insert_tip(
                title=tip_item['title'],
                content=tip_item['content'],
                tip_type=tip_item.get('type', 'smart')
            )
            tip_ids.append(tid)
        
        logger.info(f"Generated {len(tip_ids)} tips")
        
        return {
            "success": True,
            "tip_ids": tip_ids,
            "tips": tips_list
        }
    except Exception as e:
        logger.exception(f"Tip generation error: {e}")
        return {"success": False, "message": str(e)}


def _assemble_context(start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """组装上下文数据"""
    try:
        context = {
            "has_data": False,
            "activity_records": [],
            "web_history": [],
            "pending_tasks": [],
            "existing_tips": [],
            "timeframe": {
                "from": start_dt.isoformat(),
                "to": end_dt.isoformat()
            }
        }
        
        # 获取活动
        try:
            acts = get_activities(
                start_time=start_dt,
                end_time=end_dt,
                limit=10
            )
            context["activity_records"] = acts
            if acts:
                context["has_data"] = True
        except Exception as e:
            logger.debug(f"Activity fetch error: {e}")
        
        # 获取网页数据
        try:
            web_items = get_web_data(
                start_time=start_dt,
                end_time=end_dt,
                limit=20
            )
            logger.info(f"Found {len(web_items)} web records for tips")
            context["web_history"] = web_items
            if web_items:
                context["has_data"] = True
        except Exception as e:
            logger.warning(f"Web data error: {e}")
        
        # 获取待办
        try:
            todos = get_todos(status=0, limit=10)  # 未完成
            context["pending_tasks"] = todos
            if todos:
                context["has_data"] = True
        except Exception as e:
            logger.debug(f"Todo fetch error: {e}")
        
        # 获取已有提示（最近24小时内的提示，用于避免重复）
        try:
            existing_tips = get_tips(limit=20)  # 获取最近20条提示
            # 过滤出最近24小时内的提示
            recent_tips = []
            for tip in existing_tips:
                if 'create_time' in tip:
                    tip_time = datetime.fromisoformat(tip['create_time'].replace('Z', '+00:00'))
                    if (datetime.now() - tip_time).total_seconds() <= 24 * 3600:  # 24小时内
                        recent_tips.append({
                            'title': tip.get('title', ''),
                            'content': tip.get('content', ''),
                            'type': tip.get('tip_type', 'general')
                        })
            
            context["existing_tips"] = recent_tips[:10]  # 限制为最近10条
            logger.info(f"Found {len(recent_tips)} existing tips for reference")
        except Exception as e:
            logger.debug(f"Existing tips fetch error: {e}")
        
        return context
    except Exception as e:
        logger.exception(f"Context assembly error: {e}")
        return {"has_data": False}


async def _produce_tips(context: Dict, history_mins: int) -> List[Dict[str, Any]]:
    """生成提示列表"""
    client = _get_client()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        logger.warning("LLM not available")
        return []
    
    try:
        # 构建上下文数据（限制大小）
        context_data = {
            "activities": context.get("activity_records", [])[:5],
            "web_data": context.get("web_history", [])[:10],
            "todos": context.get("pending_tasks", [])[:5],
            "existing_tips": context.get("existing_tips", [])[:5]  # 添加已有提示作为参考
        }
        
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
        
        system_prompt = """你是一位专业的**网页洞察分析师 (Web Insight Analyst)**。

你的核心职责是：深度分析用户的**网页浏览历史** (`context_data`)，主动发现并提供用户在当前任务中可能需要但尚未知晓的补充信息、知识或资源。你的目标是通过提供**信息增益 (Information Gain)** 来扩展用户的知识边界。

#### **网页活动分析策略 (Web Activity Analysis Strategy)**

1.  **聚合主题 (Synthesize Theme)**: 首先，不要孤立地看待每个网页。你应该分析整个时间范围内的浏览记录，**聚合出一个或两个核心的活动主题**。例如，用户不是在看"一个"关于 Python 的网页，而是在"深入研究 Python 异步编程的原理"。
2.  **评估深度 (Assess Depth)**: 根据用户访问的网站（是入门教程、官方文档还是深度技术博客？）和查询的关键词，判断用户对当前主题的了解程度（初学者/进阶者）。
3.  **预测下一步 (Predict Next Step)**: 基于聚合出的主题和用户深度，预测他们在完成当前任务后，最有可能遇到的下一个问题或感兴趣的下一个领域是什么。

#### **内容维度 (Content Dimensions)**

你生成的内容 `type` 必须属于以下类别之一，并参考以下网页场景示例：

* **`DEEP_DIVE`**: 对用户正在关注的核心概念，提供更深层次的解读。
    * **场景**: 用户正在查阅某个函数库的 API 用法。
    * **生成内容**: 解释这个 API 设计背后的**设计模式或工作原理**。

* **`RESOURCE_RECOMMENDATION`**: 推荐相关的工具、开源库、优质文章或数据集。
    * **场景**: 用户正在多个技术博客上阅读关于 "React 性能优化" 的文章。
    * **生成内容**: 推荐一个 GitHub 上的 "awesome-react-performance" **资源集合**，或一个专业的性能分析工具。

* **`RISK_ANALYSIS`**: 预见用户当前方案可能遇到的技术陷阱、局限性或风险。
    * **场景**: 用户正在研究一个较新的、小众的开源库。
    * **生成内容**: 指出这个库**社区不活跃可能带来的维护风险**，或者它在处理大规模数据时已知的**性能瓶颈**。

* **`KNOWLEDGE_EXPANSION`**: 将当前主题与相关联的新领域或更高阶的知识联系起来。
    * **场景**: 用户正在学习如何用 Docker 打包一个应用。
    * **生成内容**: 向用户介绍**下一步可以学习的 Kubernetes (K8s) 或 Docker Swarm**，用于容器编排。

* **`ALTERNATIVE_PERSPECTIVE`**: 提供与用户当前思路不同的备选方案或反向观点。
    * **场景**: 用户在研究如何用 A 方法解决一个问题。
    * **生成内容**: 提出 B 方法也同样可以解决，并**对比 A 和 B 方法的优缺点**及适用场景。

#### **质量与输出要求 (Strictly Enforced)**

* **高信息增益**: 必须提供用户大概率不知道的新信息。禁止常识。
* **强相关性**: 所有内容必须与聚合出的核心主题紧密相关。
* **具体可用**: 提供的信息应具体、清晰，包含链接、名称或关键术语。
* **避免已知信息**: 绝不重复用户已浏览页面的核心内容。
* **质量优先**: 若无高价值内容，必须返回空数组 `[]`。
* **输出格式**: 严格的 JSON 数组。
    ```json
    [
      {
        "title": "对补充内容的高度概括",
        "content": "详细、具体的补充信息、知识或资源说明。采用 markdown 格式输出。要段落分明，类似 github 的 readme 格式。",
        "type": "从`内容维度`中选择一个最合适的类型"
      }
    ]
    ```"""
        
        user_prompt = f"""作为网页洞察分析师，请分析用户最近{history_mins}分钟的网页浏览历史数据。

**分析指令：**

1. **聚合主题优先**: 你必须首先分析所有网页，找出用户当前的核心研究主题。
2. **识别信息缺口**: 接着，基于该主题，分析用户知识体系中可能存在的盲点。
3. **预测未来需求**: 然后，预测用户在该主题上可能需要的下一步知识或资源。
4. **避免重复与低价值内容**: 你生成的内容绝不能与历史或当前浏览内容重复，也不能是宽泛或常识性的。
5. **质量优先**: 如果分析后没有真正高价值、高信息增益的内容，你必须严格返回一个空数组 []。

**数据上下文：**
{context_json}

请按照指定的JSON格式输出分析结果："""
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.info("LLM tip generation completed")
        
        # 解析结果
        tips = _parse_tips_json(result_text)
        return tips
    except Exception as e:
        logger.exception(f"Tip production error: {e}")
        return []


def _parse_tips_json(text: str) -> List[Dict[str, Any]]:
    """解析提示JSON"""
    try:
        # 提取JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        tips = json.loads(text.strip())
        
        if isinstance(tips, list):
            return tips
        elif isinstance(tips, dict) and 'tips' in tips:
            return tips['tips']
        else:
            return []
    except Exception as e:
        logger.error(f"JSON parse error: {e}")
        return []

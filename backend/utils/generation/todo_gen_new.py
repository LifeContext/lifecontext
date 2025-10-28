"""
待办事项智能生成模块
分析用户数据并提取可执行的待办任务
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import config
from utils.helpers import get_logger
from utils.db import get_web_data, get_activities, insert_todo, get_todos
from utils.llm import get_openai_client

logger = get_logger(__name__)

# 全局客户端
_llm_instance = None


def _get_llm():
    """获取LLM实例"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = get_openai_client()
    return _llm_instance


async def generate_task_list(lookback_mins: int = 30) -> Dict[str, Any]:
    """
    生成待办任务列表（主入口）
    
    Args:
        lookback_mins: 向前回溯的分钟数
    
    Returns:
        包含任务列表的字典
    """
    try:
        now = datetime.now()
        past = now - timedelta(minutes=lookback_mins)
        
        # 收集数据
        context = _gather_context(past, now)
        
        if not context['has_content']:
            logger.warning(f"Insufficient data in last {lookback_mins} minutes")
            return {"success": False, "message": "数据不足，无法生成待办"}
        
        # 生成任务
        tasks = await _create_tasks_from_context(context, lookback_mins)
        
        if not tasks:
            return {"success": False, "message": "任务生成失败"}
        
        # 保存到数据库
        task_ids = []
        for task in tasks:
            tid = insert_todo(
                title=task['title'],
                description=task.get('description', ''),
                priority=task.get('priority', 1)
            )
            task_ids.append(tid)
        
        logger.info(f"Generated {len(task_ids)} tasks")
        
        return {
            "success": True,
            "todo_ids": task_ids,
            "todos": tasks
        }
    except Exception as e:
        logger.exception(f"Task generation error: {e}")
        return {"success": False, "message": str(e)}


def _gather_context(start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """收集上下文数据"""
    try:
        logger.info(f"Gathering context: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        context = {
            "has_content": False,
            "activities": [],
            "web_items": [],
            "existing_todos": [],
            "time_span": {
                "begin": start_dt.isoformat(),
                "finish": end_dt.isoformat()
            }
        }
        
        # 获取活动记录
        try:
            acts = get_activities(
                start_time=start_dt,
                end_time=end_dt,
                limit=10
            )
            logger.info(f"Found {len(acts)} activities")
            context["activities"] = acts
            if acts:
                context["has_content"] = True
        except Exception as e:
            logger.warning(f"Activity fetch error: {e}")
        
        # 获取网页数据
        try:
            web_items = get_web_data(
                start_time=start_dt,
                end_time=end_dt,
                limit=20
            )
            logger.info(f"Found {len(web_items)} web records")
            context["web_items"] = web_items
            if web_items:
                context["has_content"] = True
        except Exception as e:
            logger.warning(f"Web data fetch error: {e}")
        
        # 获取已有待办事项（最近24小时内的）
        try:
            # 获取最近20条待办事项
            all_todos = get_todos(limit=20)
            
            # 过滤出最近24小时内的待办事项
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_todos = []
            
            for todo in all_todos:
                create_time_str = todo.get('create_time')
                if create_time_str:
                    try:
                        todo_time = datetime.strptime(create_time_str, '%Y-%m-%d %H:%M:%S')
                        if todo_time >= cutoff_time:
                            # 只保留关键信息，避免上下文过大
                            recent_todos.append({
                                'title': todo.get('title', ''),
                                'description': todo.get('description', ''),
                                'priority': todo.get('priority', 0),
                                'status': todo.get('status', 0),
                                'create_time': create_time_str
                            })
                    except Exception as time_err:
                        logger.debug(f"Time parse error for todo {todo.get('id')}: {time_err}")
            
            # 限制为最近10条
            context["existing_todos"] = recent_todos[:10]
            logger.info(f"Found {len(recent_todos)} recent todos, using {len(context['existing_todos'])}")
            
            if recent_todos:
                context["has_content"] = True
                
        except Exception as e:
            logger.warning(f"Todo fetch error: {e}")
        
        logger.info(f"Context has_content: {context['has_content']}")
        return context
    except Exception as e:
        logger.exception(f"Context gathering error: {e}")
        return {"has_content": False}


async def _create_tasks_from_context(context: Dict, lookback_mins: int) -> List[Dict[str, Any]]:
    """从上下文数据生成任务"""
    client = _get_llm()
    
    if not client or not config.ENABLE_LLM_PROCESSING:
        logger.warning("LLM not available")
        return []
    
    try:
        # 准备上下文数据，包含已有todos
        existing_todos = context.get("existing_todos", [])
        
        context_data = {
            "activities": context.get("activities", []),
            "web_data": context.get("web_items", [])[:10],  # 限制数量
            "existing_todos": existing_todos  # 添加已有待办事项
        }
        
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
        
        system_msg = """你是一位智能的**任务推断分析师 (Task Inference Analyst)**。

你的核心使命是深入理解用户的全球网页浏览活动，并从中**推断出潜在的、可执行的行动项**。你的判断应基于对用户意图的理解，而非仅仅匹配死板的规则。

---

#### **核心原则 (Core Principles)**

1.  **聚焦行动意图**: 你的首要目标是识别用户想要**完成某件事**的信号。一个任务的本质是用户的行动承诺，无论其记录形式如何。
2.  **用户中心**: 任务必须是用户作为责任人需要执行的。
3.  **信号降噪**: 主动过滤掉与具体行动无关的浏览活动，如常规阅读、社交和娱乐。
4.  **零输出**: 若未推断出任何明确的任务，必须返回空数组 `[]`。
5.  **避免重复**: 必须与历史任务进行语义比对，防止生成重复项。

---

#### **任务推断信号 (Inference Signals from Web Activity)**

你应该从以下活动模式中推断任务，规则应被灵活运用：

* **来自任务管理/代码平台 (Task Management & Code Platforms)**:
    * **涵盖**: Jira, Asana, Trello, Linear, 飞书, 钉钉, Teambition, GitHub, GitLab, Gitee 等。
    * **强信号**: 用户被明确指定为"负责人"(Assignee) 或"审查者"(Reviewer)。这是最直接的任务来源。
    * **示例**: 浏览一个 GitHub Issue 页面，用户被列为 Assignee。-> **推断任务**: "解决 GitHub Issue #[Issue号]".

* **来自在线文档/知识库 (Online Docs & Knowledge Bases)**:
    * **涵盖**: Notion, Google Docs, Confluence, 语雀, 飞书文档, 腾讯文档等。
    * **信号**:
        1.  **明确列表**: 页面中出现待办格式（如 `[ ]`, `☐`）。
        2.  **计划性文本**: 在标题或正文中包含"计划"、"待办"、"目标"、"下一步"等关键词的文档里，其下方的**项目符号或编号列表**很可能就是任务列表，**即使没有checkbox**。
        3.  **个人记录**: 即便没有特殊格式，在一个明显是个人笔记或计划的文档中，包含行动动词的独立句子也应被考虑。
    * **示例**: 浏览一个标题为"Q4 项目规划"的语雀文档，其中一段写着 "下一步行动：\n- 调研竞品A和B的功能差异。\n- 输出初步的需求文档。" -> **推断任务**: "调研竞品A和B的功能差异" 和 "输出初步的需求文档".

* **来自 AI 对话 (AI Conversations)**:
    * **涵盖**: ChatGPT, Gemini, Kimi Chat, 文心一言, 通义千问等。
    * **信号**: 当用户的提问从"是什么"转变为"怎么做"或"帮我写"时，通常暗示着一个后续的行动。任务是用户在获得AI辅助后**打算亲自完成的事**。
    * **示例**: 用户在 Kimi Chat 中提问："我需要给团队发一封关于项目延期的邮件，帮我草拟一下。" -> **推断任务**: "向团队发送项目延期通知邮件".

* **来自一般性浏览 (General Purpose Browsing)**:
    * **信号**: 当用户**围绕一个具体、可操作的主题进行了一系列集中的浏览**时，这可能代表一个隐含的任务。
    * **注意**: 此规则需谨慎使用，避免过度解读。
    * **示例**: 用户在短时间内连续访问了"如何用 Docker 部署一个 Node.js 应用"、"Docker Compose 配置文件详解"、"常见 Docker 部署错误"等多个页面。 -> **推断任务**: "使用 Docker 部署 Node.js 应用".

---

#### **排他性规则 (Exclusionary Rules)**
* **严禁**从以下活动中生成任务：常规新闻、社交媒体、视频、购物、以及纯粹的知识性搜索（例如，"什么是黑洞"）。

---

#### **输出模式 (Output Schema)**
**严格以 JSON 数组格式输出**。如果无任务，则输出 `[]`。
```json
[
  {
    "title": "任务标题",
    "description": "详细描述",
    "priority": 1-5（数字）
  }
]
```"""
        
        user_msg = f"""分析最近{lookback_mins}分钟的活动，提取待办任务。

重要：请参考已有待办事项列表，避免生成相似或重复的内容。

数据：
{context_json}

输出任务JSON列表："""
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.info("LLM task generation completed")
        
        # 解析JSON
        tasks = _parse_task_json(result_text)
        return tasks
    except Exception as e:
        logger.exception(f"LLM task creation error: {e}")
        return []


def _parse_task_json(text: str) -> List[Dict[str, Any]]:
    """解析任务JSON"""
    try:
        # 尝试提取JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        tasks = json.loads(text.strip())
        
        if isinstance(tasks, list):
            return tasks
        elif isinstance(tasks, dict) and 'tasks' in tasks:
            return tasks['tasks']
        else:
            return []
    except Exception as e:
        logger.error(f"JSON parse error: {e}")
        return []

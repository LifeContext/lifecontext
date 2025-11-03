"""
待办事项智能生成模块
分析用户数据并提取可执行的待办任务
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import config
from utils.helpers import (
    get_logger,
    estimate_tokens,
    truncate_web_data_by_tokens,
    calculate_available_context_tokens
)
from utils.json_utils import parse_llm_json_response
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
        activities = context.get("activities", [])
        
        # 估算其他数据的 token
        other_data_json = json.dumps({
            "activities": activities,
            "existing_todos": existing_todos
        }, ensure_ascii=False)
        other_data_tokens = estimate_tokens(other_data_json)
        
        # 计算可用于 web_data 的 token 数
        available_tokens = calculate_available_context_tokens('todo', other_data_tokens)
        
        # 使用动态截取函数处理 web_data，使用 metadata 替代 content
        web_data_trimmed = truncate_web_data_by_tokens(
            context.get("web_items", []),
            max_tokens=available_tokens,
            use_metadata=True
        )
        
        context_data = {
            "activities": activities,
            "web_data": web_data_trimmed,
            "existing_todos": existing_todos
        }
        
        context_json = json.dumps(context_data, ensure_ascii=False, indent=2)
        
        system_msg = """你是一位顶级的智能任务推断分析师 (Principal Task Inference Analyst)。你具备强大的逻辑推理和上下文理解能力，能够从海量的活动信号中，精准地识别出用户真正需要执行的、尚未完成的行动项。

## 任务目标 (Task Goal)

你的目标是分析一系列预处理过的网页分析报告，从中识别、整合并校验出所有用户需要执行的、尚未完成的待办事项。你的输出必须是一个经过严格去重和完成状态过滤的、可直接使用的任务列表。

## 输入数据说明 (Input Data Description)

你将收到一个名为`context_data`的单一JSON对象，它包含以下三个关键字段：

1. **`activities`**: 一个JSON数组，记录了用户 一段时间内的活动记录。
2. **`web_data`**: 一个JSON数组，包含对每个网页的独立分析报告。这是推断任务的主要来源。
3. **`existing_todos`**: 一个JSON数组，包含用户已有的、所有未完成的待办事项列表。你的核心任务之一就是避免生成与此列表内容重复的新To-do。

其中**`web_data`**是一个JSON数组。数组中的每一个对象，都是对用户单个浏览网页的预分析报告，其结构如下：

```json
{
  "metadata_analysis": {
    "category": "内容分类",
    "keywords": ["关键词1", "关键词2"],
    "topics": ["主题1"]
  },
  "detailed_summary": "该网页的详细摘要",
  "potential_insights": [ { "insight_title": "一个初步的、未经拓展的洞察点" } ],
  "actionable_tasks": [ { "task_title": "一个初步的、未经拓展的待办项" } ]
}
```

## 核心原则 (Core Principles)

你在执行任务时，必须始终遵循以下最高原则：

1. **聚焦行动意图**: 你的首要目标是识别用户想要**完成某件事**的强烈信号。
2. **用户中心**: 任务必须是用户作为责任人需要亲自执行的。
3. **信号降噪**: 主动过滤掉与具体行动无关的浏览活动，如常规阅读、社交和娱乐。
4. **零输出**: 若未推断出任何明确、未完成的任务，必须返回空数组 `[]`。
5. **避免重复**: 必须对任务进行语义去重，防止生成重复项。

## 执行步骤 (Execution Steps)

你必须严格遵循以下五个步骤来完成任务：

1. **第一步：原始任务收集。** 遍历所有输入报告，将每个报告中的`actionable_tasks`对象（包括其`task_title`, `description`, `reasoning`）收集到一个临时的“原始任务池”中。
2. **第二步：语义聚类与去重。** 对“原始任务池”中的所有任务进行语义分析。将描述相似或指向同一最终目标的任务（例如：“给张三发邮件”和“写邮件给张三关于项目的事”）合并为一个任务实体。
3. **第三步：上下文校验与过滤。** 这是最关键的步骤。对去重后的每一个“候选任务”，执行以下三重严格校验：
    - **a. 行动意图校验**: 使用下方`## 任务推断信号`作为判断依据，确认该任务是否源自一个强烈的、可信的行动意图。
    - **b. 完成状态校验**: 在整个输入数据的**所有**报告中，主动寻找该任务**可能已被完成的证据**。例如：如果一个候选任务是“调研Docker部署方法”，但在后续的浏览记录摘要中出现了“Docker部署成功实践分享”或“完成应用部署”，则应将此任务视为**已完成**，并从最终列表中**移除**。
    - **c. 排他性规则校验**: 使用下方`## 排他性规则`进行最后过滤，剔除所有源自不应生成任务活动（如看新闻、刷社交媒体）的任务。
4. **第四步：优先级评估与格式化。** 为所有通过三重校验的、确定为未完成的任务，评估一个1-3的优先级。优先级评估可以基于任务来源（例如：来自Jira/GitHub的任务通常比一般浏览推断的任务优先级更高）或其紧迫性。然后，将最终结果按`## 输出要求`格式化。
5. **第五步：零输出原则执行。** 如果经过上述所有步骤后，没有剩余的有效任务，你**必须**返回一个空数组`[]`。

## 任务推断信号 (Inference Signals)

这是你执行步骤3a时使用的规则集：

- **来自任务管理/代码平台 (如 Jira, Asana, GitHub)**: 用户被明确指定为"负责人"(Assignee) 或"审查者"(Reviewer) 是最强的任务信号。
- **来自在线文档/知识库 (如 Notion, Google Docs, 语雀)**: 页面中出现明确的待办格式（`[ ]`）；或在标题含“计划”、“目标”的文档中，没有checkbox的列表项；或个人笔记中包含行动动词的句子。
- **来自 AI 对话 (如 ChatGPT, Gemini)**: 当用户的提问从"是什么"转变为"怎么做"或"帮我写"时，暗示着一个后续的、用户打算亲自完成的行动。
- **来自一般性浏览**: 当用户围绕一个具体、可操作的主题进行了一系列集中的、深入的浏览时（例如：短时间内连续访问“如何A”、“A的配置方法”、“A的常见错误”），可能代表一个隐含的待办任务。此规则需谨慎使用。

## 排他性规则 (Exclusionary Rules)

这是你执行步骤3c时使用的规则集：

- **严禁**从以下活动中生成任务：常规新闻、社交媒体、视频、购物、以及纯粹的非行动导向的知识性搜索（例如，“什么是量子力学”）。

## 输出要求 (Output Requirements)

你必须返回一个**纯 JSON 数组**，不要使用 markdown 代码块包裹，不要添加任何解释性文字。

### JSON 结构示例:

```json
[
  {
    "title": "任务标题，应以动词开头，清晰、简洁",
    "description": "对任务的简要描述，提供必要的上下文",
    "priority": 2
  }
]
```

### 关键要求:

1. **输出格式**: 直接输出 JSON 数组，以 `[` 开始，以 `]` 结束
2. **不要包裹**: 不要用 \`\`\`json 或 \`\`\` 包裹 JSON
3. **不要注释**: JSON 外不要有任何解释文字
4. **priority 字段**: 必须是整数类型（1、2 或 3），不是字符串
5. **空结果**: 如果没有有效任务，返回 `[]`
6. **必填字段**: title、description、priority 都是必填的
"""
        
        user_msg = f"""作为智能任务推断分析师，请严格按照你的角色、目标和要求，分析以下由上一节点生成的网页浏览分析报告集合，并提取待办任务。

**数据上下文 (预分析报告集合):**
{context_json}

请输出你的任务推断结果。"""
        
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
        
        # 详细打印 LLM 返回信息
        logger.info("=" * 60)
        logger.info("LLM 返回完成")
        logger.info(f"返回长度: {len(result_text)} 字符")
        logger.info(f"开始字符: {result_text[:100] if len(result_text) > 100 else result_text}")
        logger.info(f"结束字符: {result_text[-100:] if len(result_text) > 100 else result_text}")
        logger.info(f"是否以 [ 开头: {result_text.startswith('[')}")
        logger.info(f"是否以 ] 结尾: {result_text.endswith(']')}")
        logger.info(f"是否包含代码块: {'```' in result_text}")
        logger.info("=" * 60)
        
        # 使用通用 JSON 解析工具
        logger.info("开始解析 JSON...")
        tasks = parse_llm_json_response(
            result_text,
            expected_type='array',
            save_on_error=True,
            error_file_prefix='failed_todo_response'
        )
        
        # 打印解析结果
        if tasks is not None:
            logger.info("=" * 60)
            logger.info(f"✅ JSON 解析成功！生成了 {len(tasks)} 个待办任务")
            for idx, task in enumerate(tasks):
                logger.info(f"  任务 {idx + 1}:")
                logger.info(f"    - title: {task.get('title', 'N/A')}")
                logger.info(f"    - priority: {task.get('priority', 'N/A')}")
                logger.info(f"    - description 长度: {len(task.get('description', ''))} 字符")
            logger.info("=" * 60)
            return tasks if isinstance(tasks, list) else []
        else:
            logger.warning("=" * 60)
            logger.warning("⚠️ JSON 解析失败，返回空列表")
            logger.warning("=" * 60)
            return []
    except Exception as e:
        logger.exception(f"LLM task creation error: {e}")
        return []


# 移除旧的 _parse_task_json 函数，改用统一的 parse_llm_json_response

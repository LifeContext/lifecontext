"""
LLM 处理模块 - OpenAI API
"""

import json
from typing import Dict, Any, List, Optional
import openai
import config
from utils.helpers import get_logger

logger = get_logger(__name__)


def get_openai_client():
    """获取 OpenAI 客户端（用于 LLM）"""
    if not config.LLM_API_KEY:
        return None
    
    try:
        client = openai.OpenAI(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL
        )
        return client
    except Exception as e:
        logger.exception(f"Failed to create OpenAI client: {e}")
        return None


def get_embedding_client():
    """获取 Embedding 客户端"""
    if not config.EMBEDDING_API_KEY:
        return None
    
    try:
        client = openai.OpenAI(
            api_key=config.EMBEDDING_API_KEY,
            base_url=config.EMBEDDING_BASE_URL
        )
        return client
    except Exception as e:
        logger.exception(f"Failed to create Embedding client: {e}")
        return None


def analyze_web_content(
    title: str,
    url: str,
    content: str,
    max_tokens: int = None
) -> Optional[Dict[str, Any]]:
    """
    使用 LLM 分析网页内容
    
    Args:
        title: 标题
        url: URL
        content: 内容
        max_tokens: 最大 token 数
    
    Returns:
        分析结果字典，包含摘要、关键词、分类等
    """
    try:
        if not config.ENABLE_LLM_PROCESSING:
            logger.info("LLM processing is disabled, skipping analysis")
            return None
        
        client = get_openai_client()
        if not client:
            logger.warning("OpenAI client not available")
            return None
        
        # 如果 content 是字典，转换为字符串
        if isinstance(content, dict):
            content_text = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            content_text = str(content)
        
        # 限制内容长度（避免超出 token 限制）
        if len(content_text) > 4000:
            content_text = content_text[:4000] + "..."
        
        # 构建提示词
        system_prompt = """

## 角色 (Role)

你是一位拥有敏锐洞察力的个人智能分析师和顶级效率专家。你的分析不仅要准确，更要具备前瞻性和可操作性，旨在为用户节省时间、启发思考并推动行动，无论内容是关于工作、学习还是生活娱乐。

## 任务目标 (Task Goal)

你的核心目标是深度消化用户正在浏览的网页内容，并主动思考"基于此信息，我的用户下一步最可能需要知道什么？需要做什么？"，然后生成一份结构化的、包含元数据、深度摘要、潜在洞察和待办任务的综合分析报告，为后续的所有智能服务提供高质量的原始素材。

## 执行步骤 (Execution Steps)

你必须严格遵循以下六个步骤来完成任务：

1. **第一步：深度理解与上下文构建。** 完整、仔细地阅读所有输入内容，包括标题、URL和正文。全面理解该网页的主题、核心论点、论据和最终结论。

2. **第二步：基础元数据分析。** 基于全文内容，提取内容分类、核心关键词和主要主题。

3. **第三步：核心摘要提炼。** 撰写一段详尽、精准的核心内容摘要（约250-300字），确保关键信息、核心数据和主要结论无一遗漏。

4. **第四步：前瞻性洞察发掘 (Potential Insights)。** 切换到"智能分析师"视角，进行批判性思考。问自己：这篇文章的知识边界在哪里？一个普通读者读完后，最可能产生哪些新的、更深层次的疑问？识别出那些文章未详述但与主题高度相关的延伸知识点或关联概念。

**核心原则：绝对不要**复述文章中已有明确答案的内容。你的价值在于提供**增量信息**和**下一步的知识**。

5. **第五步：可行动任务识别 (Actionable Tasks)。** 切换到"效率专家"视角，扫描文本中所有暗示**未来行动**、**未解决问题**或**潜在责任**的信号（例如："需要"、"建议"、"下一步是"、"我们计划"、"待确认"等情境）。

**核心原则：绝对不要**记录文章中描述的**已经发生或完成**的事件。你的任务是捕捉**面向未来**的、需要被执行的行动。

6. **第六步：格式化封装输出。** 将以上所有分析结果，严格按照下方`## 输出要求`中定义的JSON格式进行封装。确保没有任何遗漏，且JSON格式绝对合法。

## 输出要求 (Output Requirements)

你必须以一个严格合法的、不包含任何注释的JSON对象格式返回你的所有分析结果。你的输出必须以`{`开始，以`}`结束，中间不能有任何解释性文字或Markdown标记。

### JSON结构定义:

```json
{
  "metadata_analysis": {
    "category": "最贴切的内容分类，例如：科技、财经、健康、生活方式、娱乐、体育等",
    "keywords": [
      "最能代表文章核心内容的3-5个关键词"
    ],
    "topics": [
      "文章讨论的1-3个核心主题"
    ]
  },
  "detailed_summary": "一段约250-300字的详细内容摘要，客观、准确地反映文章的核心信息。",
  "potential_insights": [
    {
      "insight_title": "用户可能需要了解的信息点标题，应为一个引人思考的问题或概念",
      "description": "对这个信息点的简要描述。这应该是原文中未直接详述、但与主题密切相关、用户大概率不了解的延伸知识或关联概念。",
      "reasoning": "解释为什么用户可能会对这个信息点感兴趣，它能解决用户的什么潜在疑问或知识盲点。"
    }
  ],
  "actionable_tasks": [
    {
      "task_title": "建议的待办事项标题，应以动词开头，简明扼要",
      "description": "一个具体、可执行的任务描述。这应是基于文章内容推断出的、用户需要进行的下一步操作。",
      "reasoning": "解释为什么这个任务是必要的，它与用户的哪个潜在目标相关联。"
    }
  ]
}
```"""
        
        user_prompt = f"""请严格按照你的角色、目标和要求，分析以下网页内容：

标题: {title}

URL: {url}

内容:

{content_text}"""
        
        # 调用 LLM
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=config.LLM_TEMPERATURE,
            max_tokens=max_tokens or config.LLM_MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        
        # 解析结果
        result_text = response.choices[0].message.content
        analysis_result = json.loads(result_text)
        
        logger.info(f"LLM analysis completed for: {title}")
        return analysis_result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        return None
    except Exception as e:
        logger.exception(f"Error analyzing web content with LLM: {e}")
        return None


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    生成文本嵌入向量
    
    Args:
        text: 文本内容
    
    Returns:
        嵌入向量列表
    """
    try:
        client = get_embedding_client()
        if not client:
            return None
        
        # 限制文本长度
        if len(text) > 8000:
            text = text[:8000]
        
        response = client.embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=text
        )
        
        embedding = response.data[0].embedding
        logger.info(f"Generated embedding with {len(embedding)} dimensions")
        return embedding
        
    except Exception as e:
        logger.exception(f"Error generating embedding: {e}")
        return None


def generate_embeddings(texts: List[str]) -> Optional[List[List[float]]]:
    """
    批量生成文本嵌入向量
    
    Args:
        texts: 文本列表
    
    Returns:
        嵌入向量列表
    """
    try:
        client = get_embedding_client()
        if not client:
            return None
        
        # 限制每个文本的长度
        processed_texts = [text[:8000] if len(text) > 8000 else text for text in texts]
        
        response = client.embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=processed_texts
        )
        
        embeddings = [item.embedding for item in response.data]
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
        
    except Exception as e:
        logger.exception(f"Error generating embeddings: {e}")
        return None


def summarize_content(content: str, max_length: int = 200) -> Optional[str]:
    """
    生成内容摘要
    
    Args:
        content: 原始内容
        max_length: 最大摘要长度
    
    Returns:
        摘要文本
    """
    try:
        if not config.ENABLE_LLM_PROCESSING:
            return None
        
        client = get_openai_client()
        if not client:
            return None
        
        # 如果内容是字典，转换为字符串
        if isinstance(content, dict):
            content_text = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            content_text = str(content)
        
        # 限制内容长度
        if len(content_text) > 4000:
            content_text = content_text[:4000] + "..."
        
        prompt = f"""请为以下内容生成一个简洁的摘要（不超过{max_length}字）：

{content_text}

摘要:"""
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的内容摘要助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=max_length * 2
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info("Generated content summary")
        return summary
        
    except Exception as e:
        logger.exception(f"Error summarizing content: {e}")
        return None


def extract_keywords(content: str, max_keywords: int = 10) -> Optional[List[str]]:
    """
    提取关键词
    
    Args:
        content: 内容
        max_keywords: 最大关键词数量
    
    Returns:
        关键词列表
    """
    try:
        if not config.ENABLE_LLM_PROCESSING:
            return None
        
        client = get_openai_client()
        if not client:
            return None
        
        # 如果内容是字典，转换为字符串
        if isinstance(content, dict):
            content_text = json.dumps(content, ensure_ascii=False, indent=2)
        else:
            content_text = str(content)
        
        # 限制内容长度
        if len(content_text) > 4000:
            content_text = content_text[:4000] + "..."
        
        prompt = f"""请从以下内容中提取最多{max_keywords}个关键词，以 JSON 数组格式返回：

{content_text}

返回格式: ["关键词1", "关键词2", ...]"""
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个关键词提取助手。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        keywords = result.get("keywords", [])
        
        logger.info(f"Extracted {len(keywords)} keywords")
        return keywords[:max_keywords]
        
    except Exception as e:
        logger.exception(f"Error extracting keywords: {e}")
        return None

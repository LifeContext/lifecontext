"""
LLM 处理模块 - OpenAI API
"""

import json
from string import Template
from typing import Dict, Any, List, Optional
import openai
import config
from utils.helpers import get_logger
from utils.prompt_config import get_prompt_set

logger = get_logger(__name__)

PROMPTS = get_prompt_set(config.PROMPT_LANGUAGE)


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
        
        system_prompt = PROMPTS["web_analysis"]["system"]

        user_template = Template(PROMPTS["web_analysis"]["user_template"])
        user_prompt = user_template.safe_substitute(
            title=title,
            url=url or "",
            content_text=content_text
        )
        
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
        
        system_prompt = PROMPTS["content_summary"]["system"]
        prompt_template = Template(PROMPTS["content_summary"]["user_template"])
        prompt = prompt_template.safe_substitute(
            max_length=max_length,
            content_text=content_text
        )
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
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
        
        system_prompt = PROMPTS["keyword_extraction"]["system"]
        prompt_template = Template(PROMPTS["keyword_extraction"]["user_template"])
        prompt = prompt_template.safe_substitute(
            max_keywords=max_keywords,
            content_text=content_text
        )
        
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
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

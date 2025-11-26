"""
提示词配置入口
根据语言返回对应的提示词集合
"""

from typing import Dict

from .prompt_config_zh import PROMPTS as PROMPTS_ZH
from .prompt_config_en import PROMPTS as PROMPTS_EN

_PROMPT_SETS = {
    "zh": PROMPTS_ZH,
    "zh-cn": PROMPTS_ZH,
    "zh_cn": PROMPTS_ZH,
    "cn": PROMPTS_ZH,
    "中文": PROMPTS_ZH,
    "en": PROMPTS_EN,
    "en-us": PROMPTS_EN,
    "en_us": PROMPTS_EN,
    "english": PROMPTS_EN,
}


def get_prompt_set(language: str) -> Dict[str, Dict[str, str]]:
    """根据配置语言获取提示词集合，默认返回中文配置"""
    if not language:
        return PROMPTS_ZH
    return _PROMPT_SETS.get(language.lower(), PROMPTS_ZH)


def get_current_prompts() -> Dict[str, Dict[str, str]]:
    """
    获取当前配置的提示词集合
    优先从数据库读取 prompt_language 设置，如果没有则使用环境变量
    """
    try:
        from utils.db import get_setting
        import config
        
        # 优先从数据库读取
        db_language = get_setting('prompt_language')
        if db_language:
            return get_prompt_set(db_language)
        
        # 如果数据库没有，使用环境变量配置
        return get_prompt_set(config.PROMPT_LANGUAGE)
    except Exception:
        # 如果读取失败，使用环境变量配置
        import config
        return get_prompt_set(config.PROMPT_LANGUAGE)


__all__ = ["get_prompt_set", "get_current_prompts"]


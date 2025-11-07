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


__all__ = ["get_prompt_set"]


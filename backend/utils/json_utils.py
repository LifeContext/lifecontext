"""
JSON处理相关工具函数
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
import config
from json_repair import repair_json


def get_logger(name):
    """获取日志记录器"""
    return logging.getLogger(name)


def parse_llm_json_response(
    text: str,
    expected_type: str = 'auto',
    extract_key: str = None,
    save_on_error: bool = False,
    error_file_prefix: str = 'failed_llm_response'
) -> Any:
    """
    从 LLM 响应中提取和解析 JSON（使用 json_repair 库）
    
    Args:
        text: LLM 返回的原始文本
        expected_type: 期望的JSON类型，可选值：'auto'(自动检测), 'array', 'object'
        extract_key: 如果返回的是对象，从指定的key中提取数据（例如：'tips', 'todos'）
        save_on_error: 解析失败时是否保存到文件以便调试
        error_file_prefix: 错误文件的前缀名
    
    Returns:
        解析后的 JSON 对象（dict、list 或 None）
    
    Examples:
        >>> parse_llm_json_response('[{"title": "test"}]', expected_type='array')
        [{"title": "test"}]
        
        >>> parse_llm_json_response('{"tips": [...]}', extract_key='tips')
        [...]
    """
    logger = get_logger(__name__)
    
    try:
        # 记录原始返回（用于调试）
        logger.info(f"[JSON解析] 输入文本长度: {len(text)} 字符")
        logger.debug(f"[JSON解析] 开始 500 字符: {text[:500]}")
        
        # 第一步：从 markdown 代码块中提取 JSON
        json_text = _extract_json_from_markdown(text)
        
        if json_text != text:
            logger.info(f"[JSON解析] 从 markdown 代码块中提取了 JSON")
        
        # 第二步：清理文本
        json_text = json_text.strip()
        logger.info(f"[JSON解析] 清理后的 JSON 长度: {len(json_text)} 字符")
        
        # 第三步：使用 json_repair 尝试解析
        try:
            logger.info("[JSON解析] 尝试直接解析 JSON...")
            parsed_data = json.loads(json_text)
            logger.info("[JSON解析] ✅ 直接解析成功")
        except json.JSONDecodeError as e:
            logger.warning(f"[JSON解析] ❌ 初次解析失败: {e}")
            logger.warning(f"[JSON解析] 错误位置: line {e.lineno}, column {e.colno}")
            logger.info("[JSON解析] 使用 json_repair 修复 JSON 格式问题...")
            
            # 使用 json_repair 修复 JSON
            repaired_json = repair_json(json_text)
            logger.info(f"[JSON解析] 修复后的 JSON 长度: {len(repaired_json)} 字符")
            
            # 再次尝试解析
            parsed_data = json.loads(repaired_json)
            logger.info("[JSON解析] ✅ 修复后解析成功")
        
        # 第四步：根据 expected_type 和 extract_key 处理结果
        logger.info(f"[JSON解析] 原始解析结果类型: {type(parsed_data).__name__}")
        result = _process_parsed_data(parsed_data, expected_type, extract_key)
        
        logger.info(f"[JSON解析] ✅ 最终结果类型: {type(result).__name__}")
        if isinstance(result, list):
            logger.info(f"[JSON解析] 数组长度: {len(result)}")
        elif isinstance(result, dict):
            logger.info(f"[JSON解析] 对象键: {list(result.keys())}")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error("=" * 60)
        logger.error(f"[JSON解析] ❌ JSON 解析失败")
        logger.error(f"[JSON解析] 错误类型: JSONDecodeError")
        logger.error(f"[JSON解析] 错误信息: {e}")
        logger.error(f"[JSON解析] 错误位置: line {e.lineno}, column {e.colno}")
        logger.error(f"[JSON解析] 失败的文本（前 1000 字符）:")
        logger.error(text[:1000])
        logger.error("=" * 60)
        
        # 可选：保存失败的响应到文件用于调试
        if save_on_error:
            _save_failed_response(text, str(e), error_file_prefix)
            logger.error(f"[JSON解析] 失败响应已保存到文件: {error_file_prefix}_*.txt")
        
        return None
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"[JSON解析] ❌ 解析过程中发生未知错误")
        logger.error(f"[JSON解析] 错误类型: {type(e).__name__}")
        logger.error(f"[JSON解析] 错误信息: {e}")
        logger.exception(f"[JSON解析] 完整堆栈:")
        logger.error("=" * 60)
        return None


def _extract_json_from_markdown(text: str) -> str:
    """
    从 markdown 代码块中提取 JSON 文本（改进版，处理嵌套代码块）
    
    Args:
        text: 可能包含 markdown 代码块的文本
    
    Returns:
        提取的 JSON 文本
    """
    import re
    
    json_text = text.strip()
    
    # 如果文本以 [ 或 { 开始，且以 ] 或 } 结束，直接返回（不在代码块中）
    if (json_text.startswith('[') and json_text.endswith(']')) or \
       (json_text.startswith('{') and json_text.endswith('}')):
        return json_text
    
    # 方法1：使用正则表达式提取 ```json ... ``` 代码块（最外层）
    # 注意：这里使用非贪婪匹配和 DOTALL 模式来正确处理嵌套的代码块
    if "```json" in text:
        # 找到第一个 ```json 标记
        start_marker = "```json"
        start_idx = text.find(start_marker)
        if start_idx != -1:
            # 从 ```json 后开始查找内容
            content_start = start_idx + len(start_marker)
            remaining = text[content_start:]
            
            # 寻找匹配的结束 ``` 标记
            # 需要跳过JSON内容中的代码块（如 ```python ... ```）
            end_idx = _find_closing_markdown_fence(remaining)
            if end_idx != -1:
                json_text = remaining[:end_idx].strip()
                return json_text
    
    # 方法2：尝试提取第一个 ``` ... ``` 代码块（通用）
    elif "```" in text:
        start_marker = "```"
        start_idx = text.find(start_marker)
        if start_idx != -1:
            content_start = start_idx + len(start_marker)
            # 跳过第一行（可能是语言标识符，如 ```python）
            newline_idx = text.find('\n', content_start)
            if newline_idx != -1:
                content_start = newline_idx + 1
            
            remaining = text[content_start:]
            end_idx = _find_closing_markdown_fence(remaining)
            if end_idx != -1:
                json_text = remaining[:end_idx].strip()
                return json_text
    
    # 方法3：尝试通过查找 JSON 的开始和结束标记来提取
    # 查找第一个 [ 或 {
    start_bracket = text.find('[')
    start_brace = text.find('{')
    
    if start_bracket == -1 and start_brace == -1:
        return json_text  # 无法找到JSON起始标记
    
    # 确定起始位置
    if start_bracket != -1 and start_brace != -1:
        start_pos = min(start_bracket, start_brace)
        is_array = start_bracket < start_brace
    elif start_bracket != -1:
        start_pos = start_bracket
        is_array = True
    else:
        start_pos = start_brace
        is_array = False
    
    # 从起始位置开始提取完整的JSON结构
    extracted = _extract_complete_json(text[start_pos:], is_array)
    if extracted:
        return extracted
    
    return json_text


def _find_closing_markdown_fence(text: str) -> int:
    """
    在文本中找到匹配的markdown代码块结束标记
    这个函数会跳过JSON字符串内部的```标记
    
    Args:
        text: 要搜索的文本
    
    Returns:
        结束标记的位置，如果未找到返回-1
    """
    in_string = False
    escape_next = False
    i = 0
    
    while i < len(text):
        char = text[i]
        
        # 处理转义字符
        if escape_next:
            escape_next = False
            i += 1
            continue
        
        if char == '\\':
            escape_next = True
            i += 1
            continue
        
        # 检测是否在字符串内
        if char == '"':
            in_string = not in_string
            i += 1
            continue
        
        # 如果不在字符串内，检查是否是代码块结束标记
        if not in_string:
            if text[i:i+3] == '```':
                return i
        
        i += 1
    
    return -1


def _extract_complete_json(text: str, is_array: bool) -> str:
    """
    从文本中提取完整的JSON结构
    
    Args:
        text: 以JSON开始的文本
        is_array: 是否是数组
    
    Returns:
        完整的JSON文本
    """
    if not text:
        return ""
    
    start_char = '[' if is_array else '{'
    end_char = ']' if is_array else '}'
    
    if not text.startswith(start_char):
        return ""
    
    depth = 0
    in_string = False
    escape_next = False
    
    for i, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"':
            in_string = not in_string
            continue
        
        if not in_string:
            if char == start_char:
                depth += 1
            elif char == end_char:
                depth -= 1
                if depth == 0:
                    return text[:i+1]
    
    # 如果没有找到完整的结构，返回整个文本
    return text


def _process_parsed_data(
    parsed_data: Any,
    expected_type: str,
    extract_key: str = None
) -> Any:
    """
    根据期望的类型处理解析后的数据
    
    Args:
        parsed_data: 解析后的 JSON 数据
        expected_type: 期望的类型
        extract_key: 要提取的键
    
    Returns:
        处理后的数据
    """
    logger = get_logger(__name__)
    
    # 如果指定了 extract_key，尝试提取
    if extract_key and isinstance(parsed_data, dict):
        if extract_key in parsed_data:
            parsed_data = parsed_data[extract_key]
            logger.debug(f"Extracted data from key '{extract_key}'")
        else:
            logger.warning(f"Key '{extract_key}' not found in response")
    
    # 根据 expected_type 验证和转换
    if expected_type == 'array':
        if isinstance(parsed_data, list):
            return parsed_data
        elif isinstance(parsed_data, dict):
            # 尝试自动寻找数组
            for key in ['items', 'data', 'results', 'list']:
                if key in parsed_data and isinstance(parsed_data[key], list):
                    logger.debug(f"Auto-extracted array from key '{key}'")
                    return parsed_data[key]
            logger.warning(f"Expected array but got dict: {list(parsed_data.keys())}")
            return []
        else:
            logger.warning(f"Expected array but got {type(parsed_data)}")
            return []
    
    elif expected_type == 'object':
        if isinstance(parsed_data, dict):
            return parsed_data
        else:
            logger.warning(f"Expected object but got {type(parsed_data)}")
            return {}
    
    else:  # expected_type == 'auto'
        return parsed_data


def _save_failed_response(text: str, error_msg: str, prefix: str):
    """
    保存失败的 LLM 响应到文件以便调试
    
    Args:
        text: LLM 响应文本
        error_msg: 错误消息
        prefix: 文件前缀
    """
    logger = get_logger(__name__)
    
    try:
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = os.path.join(config.DATA_DIR, f"{prefix}_{timestamp}.txt")
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("=== Failed LLM Response ===\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Error: {error_msg}\n")
            f.write("\n=== Full Response ===\n")
            f.write(text)
        
        logger.info(f"Failed response saved to: {debug_file}")
        
    except Exception as e:
        logger.warning(f"Could not save failed response: {e}")
"""
JSON处理相关工具函数
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any
import config


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
    从 LLM 响应中提取和解析 JSON（通用工具函数）
    
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
        
        # 第三步：尝试解析
        try:
            logger.info("[JSON解析] 尝试直接解析 JSON...")
            parsed_data = json.loads(json_text)
            logger.info("[JSON解析] ✅ 直接解析成功")
        except json.JSONDecodeError as e:
            logger.warning(f"[JSON解析] ❌ 初次解析失败: {e}")
            logger.warning(f"[JSON解析] 错误位置: line {e.lineno}, column {e.colno}")
            logger.info("[JSON解析] 尝试修复 JSON 格式问题...")
            # 尝试修复常见问题
            json_text = _fix_json_string(json_text)
            logger.info(f"[JSON解析] 修复后的 JSON 长度: {len(json_text)} 字符")
            parsed_data = json.loads(json_text)
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


def _fix_unescaped_quotes_in_json_strings(text: str) -> str:
    """
    修复JSON字符串值中未转义的双引号（专注于代码块）
    
    这个函数用于处理LLM生成的JSON中，字符串值包含代码块时，
    代码块内的双引号没有被正确转义的情况。
    
    策略：
    1. 找到JSON字符串内的所有代码块标记（```）
    2. 在代码块内部，转义所有未转义的双引号
    
    Args:
        text: 原始JSON文本
    
    Returns:
        修复后的JSON文本
    """
    logger = get_logger(__name__)
    
    try:
        # 先尝试解析，如果成功则不需要修复
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        logger.info("[引号修复] 开始修复JSON字符串中代码块的引号...")
        
        result = []
        i = 0
        in_json_string = False
        escape_next = False
        fixes_count = 0
        
        while i < len(text):
            char = text[i]
            
            # 处理转义
            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue
            
            if char == '\\':
                result.append(char)
                escape_next = True
                i += 1
                continue
            
            # 跟踪是否在JSON字符串内
            if char == '"':
                in_json_string = not in_json_string
                result.append(char)
                i += 1
                continue
            
            # 如果在JSON字符串内，查找代码块
            if in_json_string and i + 2 < len(text) and text[i:i+3] == '```':
                # 找到代码块的结束
                code_block_end = text.find('```', i + 3)
                if code_block_end != -1:
                    # 处理代码块内容
                    code_block_content = text[i:code_block_end+3]
                    logger.debug(f"[引号修复] 发现代码块，位置: {i} - {code_block_end+3}")
                    
                    # 在代码块内容中转义所有未转义的双引号
                    fixed_block = []
                    j = 0
                    block_escape_next = False
                    block_fixes = 0
                    for ch in code_block_content:
                        if block_escape_next:
                            fixed_block.append(ch)
                            block_escape_next = False
                        elif ch == '\\':
                            fixed_block.append(ch)
                            block_escape_next = True
                        elif ch == '"':
                            # 在代码块中，转义这个引号
                            fixed_block.append('\\"')
                            block_fixes += 1
                        else:
                            fixed_block.append(ch)
                    
                    if block_fixes > 0:
                        logger.debug(f"[引号修复] 在该代码块中修复了 {block_fixes} 个引号")
                        fixes_count += block_fixes
                    
                    result.extend(fixed_block)
                    i = code_block_end + 3
                    continue
            
            result.append(char)
            i += 1
        
        fixed_text = ''.join(result)
        
        # 验证修复后的JSON
        try:
            json.loads(fixed_text)
            logger.info(f"[引号修复] ✅ 成功修复JSON，共修复 {fixes_count} 个引号")
            return fixed_text
        except json.JSONDecodeError as e:
            logger.warning(f"[引号修复] ❌ 修复后的JSON仍然无效: {e}")
            return text
        
    except Exception as e:
        logger.warning(f"[引号修复] 修复过程中发生错误: {e}")
        logger.exception("详细堆栈:")
        return text


def _fix_latex_escapes_in_json(text: str) -> str:
    r"""
    修复JSON字符串中的LaTeX转义字符
    将无效的LaTeX转义序列（如 \[, \frac, \times）转换为有效的JSON转义序列
    
    Args:
        text: 原始JSON文本
    
    Returns:
        修复后的JSON文本
    """
    import re
    
    logger = get_logger(__name__)
    
    try:
        # 策略：逐个字符扫描，智能处理反斜杠
        result = []
        i = 0
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                next_char = text[i + 1]
                
                # 合法的JSON转义字符
                valid_escapes = ['n', 't', 'r', '"', '\\', '/', 'b', 'f', 'u']
                
                if next_char in valid_escapes:
                    # 有效的转义序列，保持不变
                    result.append('\\')
                    result.append(next_char)
                    i += 2
                else:
                    # 无效的转义序列（如\[, \frac），需要转义反斜杠
                    result.append('\\\\')  # 添加额外的反斜杠
                    result.append(next_char)
                    i += 2
            else:
                # 普通字符，直接添加
                result.append(text[i])
                i += 1
        
        fixed_text = ''.join(result)
        logger.debug("[LaTeX修复] 已修复LaTeX转义字符")
        return fixed_text
        
    except Exception as e:
        logger.warning(f"[LaTeX修复] 修复LaTeX转义字符时发生错误: {e}")
        return text


def _fix_json_string(text: str) -> str:
    """
    尝试修复常见的 JSON 格式问题（增强版）
    
    Args:
        text: 原始 JSON 文本
    
    Returns:
        修复后的 JSON 文本
    """
    import re
    
    logger = get_logger(__name__)
    
    try:
        original_text = text
        
        # 第一步：清理文本
        # 移除可能的 BOM 标记
        text = text.replace('\ufeff', '')
        
        # 替换全角引号为半角引号
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # 移除控制字符（保留换行符、制表符和回车符）
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # 修复LaTeX转义字符（在JSON字符串中是无效的）
        text = _fix_latex_escapes_in_json(text)
        
        # 修复JSON字符串值中未转义的双引号（用于处理包含代码块等内容的情况）
        text = _fix_unescaped_quotes_in_json_strings(text)
        
        # 第二步：检测JSON结构类型
        text = text.strip()
        is_array = text.startswith('[')
        is_object = text.startswith('{')
        
        if not is_array and not is_object:
            # 尝试找到JSON的开始
            start_bracket = text.find('[')
            start_brace = text.find('{')
            
            if start_bracket != -1 and start_brace != -1:
                if start_bracket < start_brace:
                    text = text[start_bracket:]
                    is_array = True
                else:
                    text = text[start_brace:]
                    is_object = True
            elif start_bracket != -1:
                text = text[start_bracket:]
                is_array = True
            elif start_brace != -1:
                text = text[start_brace:]
                is_object = True
            else:
                logger.warning("无法找到JSON的开始标记")
                return original_text
        
        # 第三步：检查并修复不完整的JSON
        if is_array:
            # 检查数组是否正确闭合
            if not text.endswith(']'):
                logger.warning("检测到不完整的JSON数组，尝试修复...")
                text = _fix_incomplete_array(text)
            
            # 如果修复后仍然无效，尝试提取有效的对象
            try:
                json.loads(text)
                return text
            except json.JSONDecodeError:
                logger.info("尝试从不完整的数组中提取有效对象...")
                fixed_text = _extract_valid_objects_from_array(text)
                if fixed_text:
                    return fixed_text
        
        elif is_object:
            # 检查对象是否正确闭合
            if not text.endswith('}'):
                logger.warning("检测到不完整的JSON对象，尝试修复...")
                text = _fix_incomplete_object(text)
        
        return text
        
    except Exception as e:
        logger.warning(f"修复JSON时发生错误: {e}")
        logger.exception("详细堆栈:")
        return text


def _fix_incomplete_array(text: str) -> str:
    """
    修复不完整的JSON数组
    
    Args:
        text: 不完整的JSON数组文本
    
    Returns:
        修复后的JSON数组文本
    """
    logger = get_logger(__name__)
    
    # 找到最后一个完整的对象
    last_complete_brace = -1
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
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    last_complete_brace = i
    
    # 如果找到了完整的对象，截断到那里
    if last_complete_brace > 0:
        truncated = text[:last_complete_brace + 1]
        # 添加数组结束符
        if not truncated.rstrip().endswith(']'):
            truncated = truncated.rstrip()
            # 移除可能的尾随逗号
            if truncated.endswith(','):
                truncated = truncated[:-1]
            truncated += '\n]'
        
        logger.info(f"成功修复不完整的JSON数组，从 {len(text)} 字符截断到 {len(truncated)} 字符")
        return truncated
    
    # 如果没有找到完整对象，尝试添加结束符
    if not text.endswith(']'):
        if text.rstrip().endswith(','):
            return text.rstrip()[:-1] + ']'
        else:
            return text + ']'
    
    return text


def _fix_incomplete_object(text: str) -> str:
    """
    修复不完整的JSON对象
    
    Args:
        text: 不完整的JSON对象文本
    
    Returns:
        修复后的JSON对象文本
    """
    logger = get_logger(__name__)
    
    # 找到最后一个完整的键值对
    depth = 0
    in_string = False
    escape_next = False
    last_complete_comma = -1
    
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
            if char in '{[':
                depth += 1
            elif char in '}]':
                depth -= 1
            elif char == ',' and depth == 1:  # 顶层的逗号
                last_complete_comma = i
    
    # 如果找到了完整的键值对，截断到那里
    if last_complete_comma > 0:
        truncated = text[:last_complete_comma] + '\n}'
        logger.info(f"成功修复不完整的JSON对象")
        return truncated
    
    # 如果没有找到，尝试简单地添加结束符
    if not text.endswith('}'):
        if text.rstrip().endswith(','):
            return text.rstrip()[:-1] + '}'
        else:
            return text + '}'
    
    return text


def _extract_valid_objects_from_array(text: str) -> str:
    """
    从可能不完整的JSON数组中提取有效的对象
    
    Args:
        text: JSON数组文本
    
    Returns:
        包含有效对象的JSON数组文本
    """
    logger = get_logger(__name__)
    
    try:
        # 提取所有可能的对象
        objects = _extract_json_objects(text)
        valid_objects = []
        
        for obj_text in objects:
            try:
                # 验证对象是否有效
                obj = json.loads(obj_text)
                valid_objects.append(obj_text)
            except json.JSONDecodeError as e:
                logger.debug(f"跳过无效对象: {e}")
                # 尝试修复这个对象
                try:
                    fixed_obj = _fix_incomplete_object(obj_text)
                    json.loads(fixed_obj)  # 验证修复后的对象
                    valid_objects.append(fixed_obj)
                    logger.debug(f"成功修复一个对象")
                except:
                    logger.debug(f"无法修复对象，跳过")
                    continue
        
        if valid_objects:
            result = '[' + ','.join(valid_objects) + ']'
            logger.info(f"从数组中提取了 {len(valid_objects)} 个有效对象")
            return result
        
        return None
        
    except Exception as e:
        logger.warning(f"提取有效对象时发生错误: {e}")
        return None


def _extract_json_objects(text: str) -> List[str]:
    """
    从 JSON 数组文本中提取独立的对象
    
    Args:
        text: JSON 数组文本
    
    Returns:
        对象文本列表
    """
    objects = []
    depth = 0
    current_obj = []
    in_string = False
    escape_next = False
    
    for char in text:
        if escape_next:
            current_obj.append(char)
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            current_obj.append(char)
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            current_obj.append(char)
            continue
        
        if not in_string:
            if char == '{':
                if depth == 0:
                    current_obj = [char]
                else:
                    current_obj.append(char)
                depth += 1
            elif char == '}':
                depth -= 1
                current_obj.append(char)
                if depth == 0 and current_obj:
                    objects.append(''.join(current_obj))
                    current_obj = []
            elif depth > 0:
                current_obj.append(char)
        else:
            current_obj.append(char)
    
    return objects


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
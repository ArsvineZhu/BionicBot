# utils/helpers.py
import re
from typing import Optional, Union

# 敏感数据掩码模式
SENSITIVE_PATTERNS = [
    # QQ号码（9-12位数字）
    (r'\b\d{9,12}\b', r'********'),
    # 群号（5-12位数字）
    (r'\b\d{5,12}\b', r'********'),
    # API密钥模式（以sk-或ak-开头，后跟字母数字）
    (r'\b(sk|ak)-[a-zA-Z0-9_-]{16,}\b', r'\1-****************'),
    # 身份证号码
    (r'\b\d{17}[\dXx]\b', r'*****************************'),
    # 手机号
    (r'\b1[3-9]\d{9}\b', r'1**********'),
]


def mask_sensitive_data(text: Optional[str]) -> Optional[str]:
    """掩码处理敏感数据
    
    Args:
        text: 待处理的文本
        
    Returns:
        处理后的文本，敏感数据已被掩码
    """
    if not text:
        return text
    
    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result)
    
    return result


def get_masked_display_name(name: str, user_id: str) -> str:
    """获取掩码处理后的显示名称
    
    Args:
        name: 原始名称
        user_id: 用户ID
        
    Returns:
        掩码处理后的显示名称
    """
    masked_id = mask_sensitive_data(user_id)
    return f"{name}({masked_id})"


def is_sensitive_data(text: Optional[str]) -> bool:
    """检查文本是否包含敏感数据
    
    Args:
        text: 待检查的文本
        
    Returns:
        是否包含敏感数据
    """
    if not text:
        return False
    
    for pattern, _ in SENSITIVE_PATTERNS:
        if re.search(pattern, text):
            return True
    
    return False


def get_display_length(text: str) -> int:
    """计算字符串的显示长度，中文字符算2个，英文字符算1个
    
    Args:
        text: 待计算的文本
        
    Returns:
        字符串的显示长度
    """
    length = 0
    for char in text:
        # 中文字符范围
        if ord(char) > 127:
            length += 2
        else:
            length += 1
    return length


def format_log_text(text: str, max_length: int = 30) -> str:
    """格式化日志文本，超过指定长度后用...省略
    
    Args:
        text: 待格式化的文本
        max_length: 最大显示长度（中文字符算2个，英文字符算1个）
        
    Returns:
        格式化后的文本
    """
    if not text:
        return ""
    
    display_length = get_display_length(text)
    if display_length <= max_length:
        return text
    
    # 截断文本，确保显示长度不超过max_length
    result = ""
    current_length = 0
    for char in text:
        char_length = 2 if ord(char) > 127 else 1
        if current_length + char_length > max_length - 3:  # 减去"..."的3个字符长度
            result += "..."
            break
        result += char
        current_length += char_length
    
    return result
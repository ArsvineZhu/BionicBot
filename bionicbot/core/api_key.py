#! python3.13
from pathlib import Path

# 获取data目录路径
data_dir = Path(__file__).parent.parent / "data"

# 确保key文件存在
key_file = data_dir / "key"
if not key_file.exists():
    raise FileNotFoundError(f"API密钥文件不存在: {key_file}")

with open(key_file, 'r', encoding="utf-8") as f:
    _API_KEY: str = f.read().strip()


def get_api_key() -> str:
    """获取API密钥
    
    Returns:
        API密钥
    """
    return _API_KEY


def get_masked_api_key() -> str:
    """获取掩码处理后的API密钥，用于日志记录
    
    Returns:
        掩码处理后的API密钥
    """
    if not _API_KEY:
        return ""
    
    # 只显示API密钥的前3位和后4位，中间用星号替换
    if len(_API_KEY) < 8:
        return "*" * len(_API_KEY)
    
    prefix = _API_KEY[:3]
    suffix = _API_KEY[-4:]
    return f"{prefix}{'*' * (len(_API_KEY) - 7)}{suffix}"


# 导出API密钥访问函数
__all__ = ["get_api_key", "get_masked_api_key"]

# 为了向后兼容，保留API_KEY变量，但建议使用get_api_key()函数
API_KEY = _API_KEY

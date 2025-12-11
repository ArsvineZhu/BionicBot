# config/settings.py
import os
import yaml
from typing import List, Dict, Any
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = BASE_DIR / "bot" / "config"
DATA_DIR = BASE_DIR / "bot" / "data"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)

# 加载YAML配置文件
def load_config() -> Dict[str, Any]:
    """安全加载配置文件，配置文件不存在时返回空字典"""
    config_path = DATA_DIR / "config" / "config.yaml"
    if not config_path.exists():
        print(f"[WARN] 配置文件不存在: {config_path}，将使用默认配置")
        return {}
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            # 尝试加载YAML文件
            config = yaml.safe_load(f)
            # 确保返回的是字典类型
            if config is None:
                print(f"[WARN] 配置文件为空: {config_path}，将使用默认配置")
                return {}
            if not isinstance(config, dict):
                print(f"[WARN] 配置文件格式错误，期望字典类型，实际为: {type(config).__name__}，将使用默认配置")
                return {}
            return config
    except yaml.YAMLError as e:
        print(f"[WARN] YAML配置文件解析错误: {e}，将使用默认配置")
        return {}
    except PermissionError:
        print(f"[WARN] 无权限读取配置文件: {config_path}，将使用默认配置")
        return {}
    except UnicodeDecodeError:
        print(f"[WARN] 配置文件编码错误，无法使用UTF-8解码: {config_path}，将使用默认配置")
        return {}
    except Exception as e:
        print(f"[WARN] 加载配置文件失败: {e}，将使用默认配置")
        return {}

# 加载配置
CONFIG = load_config()

# 默认配置体系
DEFAULT_CONFIG = {
    "target_groups": [],
    "target_users": [],
    "model": "doubao-seed-1-6-lite-251015",
    "bot_name": "AI助手",
    "short_term_memory_limit": 30,
    "long_term_memory_path": "data/long_term_memory.json",
    "long_term_memory_limit": 5,
    "long_term_memory_default_importance": 1.0,
    "soul_doc_path": "config/soul_doc/bot.md",
    "response_modes": {
        "none": "无回复",
        "keyword": "关键词触发",
        "at": "@触发",
        "at_and_keyword": "@+关键词",
        "ai_decide": "AI自主判断",
        "random": "随机回复"
    },
    "default_response_mode": "at_and_keyword",
    "trigger_keywords": [],
    "random_threshold": 0.1,
    "max_message_length": 2000,
    "enable_at_reply": True,
    "context_timeout_hours": 2,
    "context_switch_threshold": 0.2,
    "context_switch_min_messages": 5,
    "context_switch_analyze_count": 3,
    "topic_relevance_threshold": 0.3,
    "topic_detection_interval": 5,
    "thread_timeout_minutes": 60,
    "thread_cleanup_interval": 30,
    "context_related_response_enabled": True,
    "context_related_timeout_minutes": 5,
    "enable_regex_keywords": True,
    "enable_history_retrieval": True,
    "history_retrieval_limit": 20,
    "history_retrieval_max_length": 1000,
    "history_retrieval_on_first_message": True,
    "history_retrieval_on_new_session": True,
    "nickname_address_mapping": {},
    "enable_nickname_address_injection": True,
    "nickname_address_injection_position": "bottom"
}


# 机器人配置
class BotSettings:
    # 目标群组和用户
    TARGET_GROUPS: List[str] = CONFIG.get("target_groups", DEFAULT_CONFIG["target_groups"])
    TARGET_USERS: List[str] = CONFIG.get("target_users", DEFAULT_CONFIG["target_users"])
    
    # AI模型配置
    MODEL: str = CONFIG.get("model", DEFAULT_CONFIG["model"])
    
    # 机器人基础配置
    BOT_NAME: str = CONFIG.get("bot_name", DEFAULT_CONFIG["bot_name"])
    
    # 记忆配置
    SHORT_TERM_MEMORY_LIMIT: int = CONFIG.get("short_term_memory_limit", DEFAULT_CONFIG["short_term_memory_limit"])
    LONG_TERM_MEMORY_PATH: str = str(DATA_DIR / CONFIG.get("long_term_memory_path", DEFAULT_CONFIG["long_term_memory_path"]).replace("data/", ""))
    
    # 灵魂文档路径
    SOUL_DOC_PATH: str = str(BASE_DIR / "bot" / "config" / "soul_doc" / CONFIG.get("soul_doc_path", DEFAULT_CONFIG["soul_doc_path"]).replace("config/soul_doc/", ""))
    
    # 回复模式配置
    RESPONSE_MODES = CONFIG.get("response_modes", DEFAULT_CONFIG["response_modes"])
    
    DEFAULT_RESPONSE_MODE: str = CONFIG.get("default_response_mode", DEFAULT_CONFIG["default_response_mode"])
    TRIGGER_KEYWORDS: List[str] = CONFIG.get("trigger_keywords", DEFAULT_CONFIG["trigger_keywords"])
    RANDOM_THRESHOLD: float = CONFIG.get("random_threshold", DEFAULT_CONFIG["random_threshold"])
    
    # 消息处理
    MAX_MESSAGE_LENGTH: int = CONFIG.get("max_message_length", DEFAULT_CONFIG["max_message_length"])
    ENABLE_AT_REPLY: bool = CONFIG.get("enable_at_reply", DEFAULT_CONFIG["enable_at_reply"])
    
    # 上下文管理配置
    CONTEXT_TIMEOUT_HOURS: int = CONFIG.get("context_timeout_hours", DEFAULT_CONFIG["context_timeout_hours"])
    CONTEXT_SWITCH_THRESHOLD: float = CONFIG.get("context_switch_threshold", DEFAULT_CONFIG["context_switch_threshold"])
    CONTEXT_SWITCH_MIN_MESSAGES: int = CONFIG.get("context_switch_min_messages", DEFAULT_CONFIG["context_switch_min_messages"])
    CONTEXT_SWITCH_ANALYZE_COUNT: int = CONFIG.get("context_switch_analyze_count", DEFAULT_CONFIG["context_switch_analyze_count"])
    
    # 话题检测配置
    TOPIC_RELEVANCE_THRESHOLD: float = CONFIG.get("topic_relevance_threshold", DEFAULT_CONFIG["topic_relevance_threshold"])
    TOPIC_DETECTION_INTERVAL: int = CONFIG.get("topic_detection_interval", DEFAULT_CONFIG["topic_detection_interval"])  # 每N条消息更新一次话题
    
    # 长期记忆配置
    LONG_TERM_MEMORY_LIMIT: int = CONFIG.get("long_term_memory_limit", DEFAULT_CONFIG["long_term_memory_limit"])
    LONG_TERM_MEMORY_DEFAULT_IMPORTANCE: float = CONFIG.get("long_term_memory_default_importance", DEFAULT_CONFIG["long_term_memory_default_importance"])
    
    # 对话线程配置
    THREAD_TIMEOUT_MINUTES: int = CONFIG.get("thread_timeout_minutes", DEFAULT_CONFIG["thread_timeout_minutes"])
    THREAD_CLEANUP_INTERVAL: int = CONFIG.get("thread_cleanup_interval", DEFAULT_CONFIG["thread_cleanup_interval"])  # 每N分钟清理一次不活跃线程
    
    # 响应优化配置
    CONTEXT_RELATED_RESPONSE_ENABLED: bool = CONFIG.get("context_related_response_enabled", DEFAULT_CONFIG["context_related_response_enabled"])
    CONTEXT_RELATED_TIMEOUT_MINUTES: int = CONFIG.get("context_related_timeout_minutes", DEFAULT_CONFIG["context_related_timeout_minutes"])  # 上下文关联响应的超时时间
    
    # 关键词增强配置
    ENABLE_REGEX_KEYWORDS: bool = CONFIG.get("enable_regex_keywords", DEFAULT_CONFIG["enable_regex_keywords"])
    
    # 历史记录配置
    ENABLE_HISTORY_RETRIEVAL: bool = CONFIG.get("enable_history_retrieval", DEFAULT_CONFIG["enable_history_retrieval"])
    HISTORY_RETRIEVAL_LIMIT: int = CONFIG.get("history_retrieval_limit", DEFAULT_CONFIG["history_retrieval_limit"])
    HISTORY_RETRIEVAL_MAX_LENGTH: int = CONFIG.get("history_retrieval_max_length", DEFAULT_CONFIG["history_retrieval_max_length"])
    
    # 历史记录获取时机配置
    HISTORY_RETRIEVAL_ON_FIRST_MESSAGE: bool = CONFIG.get("history_retrieval_on_first_message", DEFAULT_CONFIG["history_retrieval_on_first_message"])
    HISTORY_RETRIEVAL_ON_NEW_SESSION: bool = CONFIG.get("history_retrieval_on_new_session", DEFAULT_CONFIG["history_retrieval_on_new_session"])
    
    # 昵称-称呼映射表配置
    # 昵称-称呼映射表，用于在系统提示中注入用户昵称和对应的称呼信息
    NICKNAME_ADDRESS_MAPPING: Dict[str, str] = CONFIG.get("nickname_address_mapping", DEFAULT_CONFIG["nickname_address_mapping"])
    # 是否启用昵称-称呼映射表注入
    ENABLE_NICKNAME_ADDRESS_INJECTION: bool = CONFIG.get("enable_nickname_address_injection", DEFAULT_CONFIG["enable_nickname_address_injection"])
    # 昵称-称呼映射表在系统提示中的注入位置
    # 可选值：top（顶部）、bottom（底部）
    NICKNAME_ADDRESS_INJECTION_POSITION: str = CONFIG.get("nickname_address_injection_position", DEFAULT_CONFIG["nickname_address_injection_position"])

    
    @classmethod
    def validate_config(cls):
        """验证配置有效性"""
        assert cls.MODEL, "模型名称不能为空"
        assert cls.SOUL_DOC_PATH and os.path.exists(cls.SOUL_DOC_PATH), "灵魂文档不存在"
        assert cls.RANDOM_THRESHOLD >= 0 and cls.RANDOM_THRESHOLD <= 1, "随机阈值必须在0-1之间"
        
        # 验证昵称-地址映射表配置
        assert isinstance(cls.NICKNAME_ADDRESS_MAPPING, dict), "昵称-地址映射表必须是字典类型"
        for key, value in cls.NICKNAME_ADDRESS_MAPPING.items():
            assert isinstance(key, str), f"昵称-地址映射表的键（{key}）必须是字符串类型"
            assert isinstance(value, str), f"昵称-地址映射表的值（{value}）必须是字符串类型"
            assert key.strip(), f"昵称-地址映射表的键（{key}）不能为空字符串"
            assert value.strip(), f"昵称-地址映射表的值（{value}）不能为空字符串"
        
        assert isinstance(cls.ENABLE_NICKNAME_ADDRESS_INJECTION, bool), "enable_nickname_address_injection必须是布尔类型"
        assert cls.NICKNAME_ADDRESS_INJECTION_POSITION in ["top", "bottom"], "nickname_address_injection_position必须是'top'或'bottom'"
        
        # 确保长期记忆目录存在
        os.makedirs(os.path.dirname(cls.LONG_TERM_MEMORY_PATH), exist_ok=True)
        
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """转换为字典，对敏感数据进行掩码处理"""
        from bot.utils.helpers import mask_sensitive_data
        
        config_dict = {
            key: getattr(cls, key) 
            for key in dir(cls) 
            if not key.startswith("_") and not callable(getattr(cls, key))
        }
        
        # 掩码处理敏感数据
        if "TARGET_GROUPS" in config_dict:
            config_dict["TARGET_GROUPS"] = [mask_sensitive_data(group) for group in config_dict["TARGET_GROUPS"]]
        if "TARGET_USERS" in config_dict:
            config_dict["TARGET_USERS"] = [mask_sensitive_data(user) for user in config_dict["TARGET_USERS"]]
        
        return config_dict
# config/settings.py
import os
import yaml
from typing import List, Dict, Any, Optional
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
    config_dir = DATA_DIR / "config"
    config_files = [
        config_dir / "ai.yaml",
        config_dir / "bot.yaml",
        config_dir / "system.yaml"
    ]
    
    merged_config = {}
    
    for config_path in config_files:
        if not config_path.exists():
            print(f"[WARN] 配置文件不存在: {config_path}，将跳过该配置")
            continue
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                # 尝试加载YAML文件
                config = yaml.safe_load(f)
                # 确保返回的是字典类型
                if config is None:
                    print(f"[WARN] 配置文件为空: {config_path}，将跳过该配置")
                    continue
                if not isinstance(config, dict):
                    print(f"[WARN] 配置文件格式错误，期望字典类型，实际为: {type(config).__name__}，将跳过该配置")
                    continue
                
                # 合并配置，后面的配置会覆盖前面的同名配置
                merged_config.update(config)
                print(f"[INFO] 成功加载配置文件: {config_path}")
        except yaml.YAMLError as e:
            print(f"[WARN] YAML配置文件解析错误: {e}，将跳过该配置")
            continue
        except PermissionError:
            print(f"[WARN] 无权限读取配置文件: {config_path}，将跳过该配置")
            continue
        except UnicodeDecodeError:
            print(f"[WARN] 配置文件编码错误，无法使用UTF-8解码: {config_path}，将跳过该配置")
            continue
        except Exception as e:
            print(f"[WARN] 加载配置文件失败: {e}，将跳过该配置")
            continue
    
    return merged_config

# 加载配置
CONFIG = load_config()

# 默认配置体系
DEFAULT_CONFIG = {
    # AI配置
    "model": "doubao-seed-1-6-lite-251015",
    "decision_model": "doubao-seed-1-6-flash-250828",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "api_key_path": "../key",
    
    # 模型配置 - Main model
    "temperature": 0.8,
    "reasoning": "MEDIUM",
    "reasoning_available": True,
    "cache": True,
    "max_tokens": None,
    "top_p": None,
    "top_k": None,
    "presence_penalty": None,
    "frequency_penalty": None,
    "stop": None,
    
    # 模型配置 - Decision model
    "decision_temperature": 0.0,
    "decision_reasoning": "MINIMAL",
    "decision_reasoning_available": False,
    "decision_cache": False,
    "decision_max_tokens": 100,
    "decision_top_p": None,
    "decision_top_k": None,
    "decision_stop": ["\n"],
    
    # 摘要系统配置
    "summary_enabled": True,
    "summary_model": "doubao-seed-1-6-flash-250828",
    "summary_temperature": 0.1,
    "summary_min_messages": 50,
    "summary_max_messages": 100,
    "summary_interval_hours": 2,
    "summary_short_interval_minutes": 60,
    "summary_check_frequency": 50,
    
    # 图片解读配置
    "image_model": "doubao-seed-1-6-flash-250828",
    "image_reasoning": "MINIMAL",
    "image_temperature": 0.6,
    "image_max_tokens": 200,
    
    # 记忆配置
    "short_term_memory_limit": 30,
    "long_term_memory_path": "long_term_memory.json",
    "long_term_memory_limit": 5,
    "long_term_memory_default_importance": 1.0,
    
    # 历史记录配置
    "enable_history_retrieval": True,
    "history_retrieval_limit": 20,
    "history_retrieval_max_length": 1000,
    "history_retrieval_on_first_message": True,
    "history_retrieval_on_new_session": True,
    
    # 上下文管理
    "context_timeout_hours": 2,
    "context_switch_threshold": 0.2,
    "context_switch_min_messages": 5,
    "context_switch_analyze_count": 3,
    "context_related_response_enabled": True,
    "context_related_timeout_minutes": 5,
    
    # 话题检测
    "topic_relevance_threshold": 0.3,
    "topic_detection_interval": 5,
    
    # 对话线程
    "thread_timeout_minutes": 60,
    "thread_cleanup_interval": 30,
    
    # 机器人配置
    "bot_name": "AI助手",
    "soul_doc_path": "soul_doc/yuki.md",
    
    # 目标配置
    "target_groups": [],
    "target_users": [],
    
    # 回复模式
    "response_modes": {
        "none": "无回复",
        "keyword": "关键词触发",
        "at": "@触发",
        "at_and_keyword": "@+关键词",
        "ai_decide": "AI自主判断",
        "random": "随机回复"
    },
    "default_response_mode": "at_and_keyword",
    
    # 关键词配置
    "trigger_keywords": [],
    "enable_regex_keywords": True,
    
    # 随机回复
    "random_threshold": 0.1,
    
    # 消息处理
    "max_message_length": 2000,
    "enable_at_reply": True,
    
    # 昵称-称呼映射
    "nickname_address_mapping": {},
    "enable_nickname_address_injection": True,
    "nickname_address_injection_position": "bottom",
    
    # 系统配置
    "log_level": "INFO",
    "debug": False,
    "enable_plugins": True,
    "napcat_enabled": True,
    "napcat_ws_uri": "ws://localhost:3001",
    "webui_enabled": False,
    "webui_port": 6099,
    
    # AI决策提示词
    "should_respond_prompt_path": "bot/config/prompt/should_respond_prompt.txt"
}


# 加载提示词的辅助函数
def _load_prompt_from_file(file_path: str) -> str:
    """从文件加载提示词"""
    try:
        # 处理路径，确保可以找到文件
        if file_path.startswith("bot/"):
            full_path = BASE_DIR / file_path
        else:
            full_path = BASE_DIR / "bot" / file_path
        
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        # 确保提示词包含要求的结尾
        required_ending = "请只回复'YES'或'NO'，不要添加任何其他内容。"
        if not content.endswith(required_ending):
            content += "\n" + required_ending
        
        return content
    except Exception as e:
        print(f"[ERROR] 加载AI决策提示词失败: {e}")
        # 返回默认提示词
        default_prompt = "你需要判断是否应该回复用户的消息。请仅根据上下文和当前消息判断。"
        return default_prompt + "\n" + required_ending

# 机器人配置
class BotSettings:
    # 目标群组和用户
    TARGET_GROUPS: List[str] = CONFIG.get("target_groups", DEFAULT_CONFIG["target_groups"])
    TARGET_USERS: List[str] = CONFIG.get("target_users", DEFAULT_CONFIG["target_users"])
    
    # AI模型配置
    MODEL: str = CONFIG.get("model", DEFAULT_CONFIG["model"])
    DECISION_MODEL: str = CONFIG.get("decision_model", DEFAULT_CONFIG["decision_model"])
    BASE_URL: str = CONFIG.get("base_url", DEFAULT_CONFIG["base_url"])
    
    # 模型配置 - Main model
    TEMPERATURE: float = CONFIG.get("temperature", DEFAULT_CONFIG["temperature"])
    REASONING: str = CONFIG.get("reasoning", DEFAULT_CONFIG["reasoning"])
    REASONING_AVAILABLE: bool = CONFIG.get("reasoning_available", DEFAULT_CONFIG["reasoning_available"])
    CACHE: bool = CONFIG.get("cache", DEFAULT_CONFIG["cache"])
    MAX_TOKENS: Optional[int] = CONFIG.get("max_tokens", DEFAULT_CONFIG["max_tokens"])
    TOP_P: Optional[float] = CONFIG.get("top_p", DEFAULT_CONFIG["top_p"])
    TOP_K: Optional[int] = CONFIG.get("top_k", DEFAULT_CONFIG["top_k"])
    PRESENCE_PENALTY: Optional[float] = CONFIG.get("presence_penalty", DEFAULT_CONFIG["presence_penalty"])
    FREQUENCY_PENALTY: Optional[float] = CONFIG.get("frequency_penalty", DEFAULT_CONFIG["frequency_penalty"])
    STOP: Optional[List[str]] = CONFIG.get("stop", DEFAULT_CONFIG["stop"])
    
    # 模型配置 - Decision model
    DECISION_TEMPERATURE: float = CONFIG.get("decision_temperature", DEFAULT_CONFIG["decision_temperature"])
    DECISION_REASONING: str = CONFIG.get("decision_reasoning", DEFAULT_CONFIG["decision_reasoning"])
    DECISION_REASONING_AVAILABLE: bool = CONFIG.get("decision_reasoning_available", DEFAULT_CONFIG["decision_reasoning_available"])
    DECISION_CACHE: bool = CONFIG.get("decision_cache", DEFAULT_CONFIG["decision_cache"])
    DECISION_MAX_TOKENS: Optional[int] = CONFIG.get("decision_max_tokens", DEFAULT_CONFIG["decision_max_tokens"])
    DECISION_TOP_P: Optional[float] = CONFIG.get("decision_top_p", DEFAULT_CONFIG["decision_top_p"])
    DECISION_TOP_K: Optional[int] = CONFIG.get("decision_top_k", DEFAULT_CONFIG["decision_top_k"])
    DECISION_STOP: Optional[List[str]] = CONFIG.get("decision_stop", DEFAULT_CONFIG["decision_stop"])
    
    # 摘要系统配置
    SUMMARY_ENABLED: bool = CONFIG.get("summary_enabled", DEFAULT_CONFIG["summary_enabled"])
    SUMMARY_MODEL: str = CONFIG.get("summary_model", DEFAULT_CONFIG["summary_model"])
    SUMMARY_TEMPERATURE: float = CONFIG.get("summary_temperature", DEFAULT_CONFIG["summary_temperature"])
    SUMMARY_MIN_MESSAGES: int = CONFIG.get("summary_min_messages", DEFAULT_CONFIG["summary_min_messages"])
    SUMMARY_MAX_MESSAGES: int = CONFIG.get("summary_max_messages", DEFAULT_CONFIG["summary_max_messages"])
    SUMMARY_INTERVAL_HOURS: int = CONFIG.get("summary_interval_hours", DEFAULT_CONFIG["summary_interval_hours"])
    SUMMARY_SHORT_INTERVAL_MINUTES: int = CONFIG.get("summary_short_interval_minutes", DEFAULT_CONFIG["summary_short_interval_minutes"])
    SUMMARY_CHECK_FREQUENCY: int = CONFIG.get("summary_check_frequency", DEFAULT_CONFIG["summary_check_frequency"])
    
    # 图片解读配置
    IMAGE_MODEL: str = CONFIG.get("image_model", DEFAULT_CONFIG["image_model"])
    IMAGE_REASONING: str = CONFIG.get("image_reasoning", DEFAULT_CONFIG["image_reasoning"])
    IMAGE_TEMPERATURE: float = CONFIG.get("image_temperature", DEFAULT_CONFIG["image_temperature"])
    IMAGE_MAX_TOKENS: Optional[int] = CONFIG.get("image_max_tokens", DEFAULT_CONFIG["image_max_tokens"])
    
    # AI决策提示词配置
    SHOULD_RESPOND_PROMPT_PATH: str = CONFIG.get("should_respond_prompt_path", DEFAULT_CONFIG["should_respond_prompt_path"])
    SHOULD_RESPOND_PROMPT: str = _load_prompt_from_file(SHOULD_RESPOND_PROMPT_PATH)
    
    # 机器人基础配置
    BOT_NAME: str = CONFIG.get("bot_name", DEFAULT_CONFIG["bot_name"])
    
    # 记忆配置
    SHORT_TERM_MEMORY_LIMIT: int = CONFIG.get("short_term_memory_limit", DEFAULT_CONFIG["short_term_memory_limit"])
    LONG_TERM_MEMORY_PATH: str = str(DATA_DIR / CONFIG.get("long_term_memory_path", DEFAULT_CONFIG["long_term_memory_path"]).replace("data/", ""))
    
    # 灵魂文档路径
    soul_doc_path = CONFIG.get("soul_doc_path", DEFAULT_CONFIG["soul_doc_path"])
    # 如果路径已经包含 bot/ 或 config/，直接使用
    if soul_doc_path.startswith("bot/"):
        SOUL_DOC_PATH: str = str(BASE_DIR / soul_doc_path)
    elif soul_doc_path.startswith("config/"):
        SOUL_DOC_PATH: str = str(BASE_DIR / "bot" / soul_doc_path)
    else:
        # 默认处理，假设是相对于 bot/config/ 的路径
        SOUL_DOC_PATH: str = str(BASE_DIR / "bot" / "config" / soul_doc_path)
    
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
    # 支持两种格式：
    # 1. 简单格式：{"昵称": "称呼"} - 仅用于称呼转换
    # 2. 高级格式：{"昵称": {"address": "称呼", "qq": "123456"}} - 同时支持称呼转换和@功能
    NICKNAME_ADDRESS_MAPPING: Dict[str, Any] = CONFIG.get("nickname_address_mapping", DEFAULT_CONFIG["nickname_address_mapping"])
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
        
        # 验证回复模式配置
        from bot.core.tracker import ResponseMode
        valid_modes = [mode.value for mode in ResponseMode]
        assert cls.DEFAULT_RESPONSE_MODE in valid_modes, f"默认回复模式必须是以下之一: {', '.join(valid_modes)}"
        
        # 验证触发关键词配置
        assert isinstance(cls.TRIGGER_KEYWORDS, list), "触发关键词必须是列表类型"
        for keyword in cls.TRIGGER_KEYWORDS:
            assert isinstance(keyword, str), f"触发关键词必须是字符串类型，当前类型: {type(keyword).__name__}"
        
        # 验证上下文相关配置
        assert isinstance(cls.CONTEXT_RELATED_RESPONSE_ENABLED, bool), "上下文相关响应开关必须是布尔类型"
        assert cls.CONTEXT_RELATED_TIMEOUT_MINUTES > 0, "上下文相关响应超时时间必须大于0"
        
        # 验证昵称-地址映射表配置
        assert isinstance(cls.NICKNAME_ADDRESS_MAPPING, dict), "昵称-地址映射表必须是字典类型"
        for key, value in cls.NICKNAME_ADDRESS_MAPPING.items():
            assert isinstance(key, str), f"昵称-地址映射表的键（{key}）必须是字符串类型"
            assert key.strip(), f"昵称-地址映射表的键（{key}）不能为空字符串"
            
            # 支持两种格式：字符串或字典
            if isinstance(value, str):
                assert value.strip(), f"昵称-地址映射表的值（{value}）不能为空字符串"
            elif isinstance(value, dict):
                # 字典格式必须包含address字段
                assert "address" in value, f"昵称-地址映射表的字典格式必须包含address字段: {key}"
                assert isinstance(value["address"], str), f"address字段必须是字符串类型: {key}"
                assert value["address"].strip(), f"address字段不能为空字符串: {key}"
                # qq字段是可选的，但如果存在必须是字符串
                if "qq" in value:
                    assert isinstance(value["qq"], str), f"qq字段必须是字符串类型: {key}"
            else:
                assert False, f"昵称-地址映射表的值必须是字符串或字典类型，当前类型: {type(value).__name__}"
        
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
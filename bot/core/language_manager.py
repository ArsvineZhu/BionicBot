import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from ncatbot.utils import get_log
from bot.config.settings import BotSettings

logger = get_log("LanguageManager")


class LanguageManager:
    """语言管理器"""
    
    def __init__(self, language: str = "zh_cn"):
        self.language = language
        self.language_dir = Path(__file__).parent.parent / "data" / "config" / "languages"
        self.translations: Dict[str, Any] = {}
        self._load_translations()
    
    def _load_translations(self):
        """加载语言配置文件"""
        try:
            file_path = self.language_dir / f"{self.language}.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
                logger.info(f"成功加载语言配置: {self.language}")
            else:
                logger.warning(f"语言配置文件不存在: {file_path}")
                # 尝试加载默认语言
                default_path = self.language_dir / "zh_cn.json"
                if default_path.exists():
                    with open(default_path, "r", encoding="utf-8") as f:
                        self.translations = json.load(f)
                    logger.info(f"使用默认语言配置: zh_cn")
        except Exception as e:
            logger.error(f"加载语言配置失败: {e}")
            self.translations = {}
    
    def get(self, key: str, **kwargs) -> str:
        """获取翻译文本
        
        Args:
            key: 翻译键，格式为 "level.key"，level为info、debug或error
            **kwargs: 格式化参数
            
        Returns:
            翻译后的文本
        """
        try:
            # 确保键格式正确，包含级别和子键
            if "." not in key:
                logger.error(f"翻译键格式错误，缺少级别: {key}")
                return key
            
            level, subkey = key.split(".", 1)
            
            # 确保级别是有效的
            if level not in ["info", "debug", "error"]:
                logger.error(f"无效的日志级别: {level}，键: {key}")
                return key
            
            # 获取翻译模板
            template = self.translations.get(level, {}).get(subkey, key)
            return template.format(**kwargs)
        except Exception as e:
            logger.error(f"获取翻译失败: {key}, 错误: {e}")
            return key
    
    def change_language(self, language: str):
        """切换语言
        
        Args:
            language: 语言代码，如 "zh_cn", "en_us"
        """
        self.language = language
        self._load_translations()
    
    def available_languages(self) -> list:
        """获取可用的语言列表
        
        Returns:
            可用语言代码列表
        """
        languages = []
        try:
            if self.language_dir.exists():
                for file in os.listdir(self.language_dir):
                    if file.endswith(".json"):
                        lang_code = file[:-5]  # 移除.json后缀
                        languages.append(lang_code)
        except Exception as e:
            logger.error(f"获取可用语言列表失败: {e}")
        return languages

# 单例实例
language_manager = LanguageManager(BotSettings.LANGUAGE)

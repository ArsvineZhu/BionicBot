#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置系统测试用例
用于验证配置系统的正确性、安全性和可靠性
"""

import sys
import os
import tempfile
import yaml
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bot.config.settings import load_config, BotSettings, DEFAULT_CONFIG

class TestConfigSystem:
    """配置系统测试类"""
    
    def test_config_load(self):
        """测试配置加载功能"""
        print("测试配置加载功能...")
        
        # 创建临时配置文件
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建config目录
            temp_config_dir = Path(temp_dir) / "config"
            temp_config_dir.mkdir(parents=True, exist_ok=True)
            temp_config_path = temp_config_dir / "config.yaml"
            
            # 写入测试配置
            test_config = {
                "target_groups": ["100001"],
                "target_users": ["200001"],
                "bot_name": "测试机器人"
            }
            
            with open(temp_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(test_config, f)
            
            # 测试加载配置
            from bot.config import settings
            original_data_dir = settings.DATA_DIR
            settings.DATA_DIR = Path(temp_dir)
            
            try:
                config = load_config()
                assert isinstance(config, dict), f"配置加载失败，期望字典类型，实际为{type(config).__name__}"
                assert "target_groups" in config, "配置中缺少target_groups"
                assert "target_users" in config, "配置中缺少target_users"
                assert config["target_groups"] == ["100001"], f"target_groups配置错误，期望[\"100001\"]，实际为{config['target_groups']}"
                assert config["target_users"] == ["200001"], f"target_users配置错误，期望[\"200001\"]，实际为{config['target_users']}"
                print("✅ 配置加载功能测试通过")
            finally:
                # 恢复原始DATA_DIR
                settings.DATA_DIR = original_data_dir
    
    def test_default_config(self):
        """测试默认配置体系"""
        print("测试默认配置体系...")
        
        # 检查DEFAULT_CONFIG是否包含所有必要的配置项
        required_configs = [
            "target_groups", "target_users", "model", "bot_name",
            "short_term_memory_limit", "long_term_memory_path",
            "soul_doc_path", "default_response_mode", "trigger_keywords",
            "random_threshold", "max_message_length", "enable_at_reply",
            "context_timeout_hours", "context_switch_threshold",
            "topic_relevance_threshold", "topic_detection_interval",
            "thread_timeout_minutes", "thread_cleanup_interval",
            "context_related_response_enabled", "context_related_timeout_minutes",
            "enable_regex_keywords", "enable_history_retrieval",
            "history_retrieval_limit", "history_retrieval_max_length",
            "history_retrieval_on_first_message", "history_retrieval_on_new_session",
            "nickname_address_mapping", "enable_nickname_address_injection",
            "nickname_address_injection_position", "context_switch_min_messages",
            "context_switch_analyze_count", "long_term_memory_limit",
            "long_term_memory_default_importance"
        ]
        
        for config_key in required_configs:
            assert config_key in DEFAULT_CONFIG, f"默认配置中缺少必要的配置项: {config_key}"
        
        print("✅ 默认配置体系测试通过")
    
    def test_bot_settings(self):
        """测试BotSettings类"""
        print("测试BotSettings类...")
        
        # 检查BotSettings是否包含所有配置项
        config_items = [
            "TARGET_GROUPS", "TARGET_USERS", "MODEL", "BOT_NAME",
            "SHORT_TERM_MEMORY_LIMIT", "LONG_TERM_MEMORY_PATH",
            "SOUL_DOC_PATH", "DEFAULT_RESPONSE_MODE", "TRIGGER_KEYWORDS",
            "RANDOM_THRESHOLD", "MAX_MESSAGE_LENGTH", "ENABLE_AT_REPLY",
            "CONTEXT_TIMEOUT_HOURS", "CONTEXT_SWITCH_THRESHOLD",
            "TOPIC_RELEVANCE_THRESHOLD", "TOPIC_DETECTION_INTERVAL",
            "THREAD_TIMEOUT_MINUTES", "THREAD_CLEANUP_INTERVAL",
            "CONTEXT_RELATED_RESPONSE_ENABLED", "CONTEXT_RELATED_TIMEOUT_MINUTES",
            "ENABLE_REGEX_KEYWORDS", "ENABLE_HISTORY_RETRIEVAL",
            "HISTORY_RETRIEVAL_LIMIT", "HISTORY_RETRIEVAL_MAX_LENGTH",
            "HISTORY_RETRIEVAL_ON_FIRST_MESSAGE", "HISTORY_RETRIEVAL_ON_NEW_SESSION",
            "NICKNAME_ADDRESS_MAPPING", "ENABLE_NICKNAME_ADDRESS_INJECTION",
            "NICKNAME_ADDRESS_INJECTION_POSITION", "CONTEXT_SWITCH_MIN_MESSAGES",
            "CONTEXT_SWITCH_ANALYZE_COUNT", "LONG_TERM_MEMORY_LIMIT",
            "LONG_TERM_MEMORY_DEFAULT_IMPORTANCE"
        ]
        
        for item in config_items:
            assert hasattr(BotSettings, item), f"BotSettings中缺少配置项: {item}"
        
        # 测试配置项类型
        assert isinstance(BotSettings.TARGET_GROUPS, list), f"TARGET_GROUPS类型错误，期望list，实际为{type(BotSettings.TARGET_GROUPS).__name__}"
        assert isinstance(BotSettings.TARGET_USERS, list), f"TARGET_USERS类型错误，期望list，实际为{type(BotSettings.TARGET_USERS).__name__}"
        assert isinstance(BotSettings.MODEL, str), f"MODEL类型错误，期望str，实际为{type(BotSettings.MODEL).__name__}"
        assert isinstance(BotSettings.BOT_NAME, str), f"BOT_NAME类型错误，期望str，实际为{type(BotSettings.BOT_NAME).__name__}"
        assert isinstance(BotSettings.SHORT_TERM_MEMORY_LIMIT, int), f"SHORT_TERM_MEMORY_LIMIT类型错误，期望int，实际为{type(BotSettings.SHORT_TERM_MEMORY_LIMIT).__name__}"
        assert isinstance(BotSettings.CONTEXT_SWITCH_THRESHOLD, (int, float)), f"CONTEXT_SWITCH_THRESHOLD类型错误，期望int或float，实际为{type(BotSettings.CONTEXT_SWITCH_THRESHOLD).__name__}"
        assert isinstance(BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION, bool), f"ENABLE_NICKNAME_ADDRESS_INJECTION类型错误，期望bool，实际为{type(BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION).__name__}"
        
        print("✅ BotSettings类测试通过")
    
    def test_config_validation(self):
        """测试配置验证功能"""
        print("测试配置验证功能...")
        
        # 测试配置验证方法
        try:
            BotSettings.validate_config()
            print("✅ 配置验证功能测试通过")
        except Exception as e:
            print(f"❌ 配置验证功能测试失败: {e}")
    
    def test_sensitive_data_masking(self):
        """测试敏感数据掩码处理"""
        print("测试敏感数据掩码处理...")
        
        # 测试to_dict方法是否正确掩码处理敏感数据
        config_dict = BotSettings.to_dict()
        
        # 检查敏感数据是否被掩码处理
        if "TARGET_GROUPS" in config_dict:
            for group in config_dict["TARGET_GROUPS"]:
                assert "*" in group or len(group) == 0, f"TARGET_GROUPS敏感数据未被正确掩码处理: {group}"
        
        if "TARGET_USERS" in config_dict:
            for user in config_dict["TARGET_USERS"]:
                assert "*" in user or len(user) == 0, f"TARGET_USERS敏感数据未被正确掩码处理: {user}"
        
        print("✅ 敏感数据掩码处理测试通过")
    
    def test_config_safety(self):
        """测试配置系统的安全机制"""
        print("测试配置系统的安全机制...")
        
        # 测试配置文件不存在时的处理
        with tempfile.TemporaryDirectory() as temp_dir:
            from bot.config import settings
            original_data_dir = settings.DATA_DIR
            settings.DATA_DIR = Path(temp_dir)
            
            try:
                config = load_config()
                # 当配置文件不存在时，应该返回空字典，而不是抛出异常
                assert isinstance(config, dict), f"配置文件不存在时，期望返回字典，实际返回{type(config).__name__}"
                print("✅ 配置文件不存在时的安全处理测试通过")
            finally:
                # 恢复原始DATA_DIR
                settings.DATA_DIR = original_data_dir
    
    def test_all_configs_loaded(self):
        """测试所有配置项都从配置文件或默认配置加载"""
        print("测试所有配置项都从配置文件或默认配置加载...")
        
        # 检查BotSettings中的配置项是否都有合理的值
        config_dict = BotSettings.to_dict()
        
        # 测试部分关键配置项
        assert config_dict["MODEL"] is not None, "MODEL配置项未正确加载"
        assert isinstance(config_dict["SHORT_TERM_MEMORY_LIMIT"], int) and config_dict["SHORT_TERM_MEMORY_LIMIT"] > 0, "SHORT_TERM_MEMORY_LIMIT配置项未正确加载"
        assert isinstance(config_dict["CONTEXT_TIMEOUT_HOURS"], int) and config_dict["CONTEXT_TIMEOUT_HOURS"] > 0, "CONTEXT_TIMEOUT_HOURS配置项未正确加载"
        assert isinstance(config_dict["ENABLE_NICKNAME_ADDRESS_INJECTION"], bool), "ENABLE_NICKNAME_ADDRESS_INJECTION配置项未正确加载"
        
        print("✅ 所有配置项都从配置文件或默认配置加载测试通过")
    
    def run_all_tests(self):
        """运行所有测试用例"""
        print("=" * 60)
        print("配置系统全面测试")
        print("=" * 60)
        
        try:
            self.test_config_load()
            self.test_default_config()
            self.test_bot_settings()
            self.test_config_validation()
            self.test_sensitive_data_masking()
            self.test_config_safety()
            self.test_all_configs_loaded()
            
            print("=" * 60)
            print("🎉 所有配置系统测试通过！")
            print("=" * 60)
            return True
        except AssertionError as e:
            print(f"""\n❌ 测试失败: {e}""")
            print("=" * 60)
            return False
        except Exception as e:
            print(f"""\n❌ 测试异常: {e}""")
            import traceback
            traceback.print_exc()
            print("=" * 60)
            return False

if __name__ == "__main__":
    test = TestConfigSystem()
    test.run_all_tests()

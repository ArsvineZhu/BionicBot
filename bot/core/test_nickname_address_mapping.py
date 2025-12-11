#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
昵称-地址映射表功能单元测试
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import yaml
from bot.config.settings import load_config, BotSettings
from bot.core.memory import MemoryManager
from bot.core.model import Message, Content, ROLE_TYPE


class TestNicknameAddressMapping(unittest.TestCase):
    """昵称-地址映射表功能测试"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时配置文件
        self.temp_dir = tempfile.TemporaryDirectory()
        # 创建config目录
        self.temp_config_dir = Path(self.temp_dir.name) / "config"
        self.temp_config_dir.mkdir(parents=True, exist_ok=True)
        self.temp_config_path = self.temp_config_dir / "config.yaml"
        
        # 备份原始配置路径
        self.original_data_dir = BotSettings.__dict__.get('DATA_DIR', None)
        
    def tearDown(self):
        """清理测试环境"""
        self.temp_dir.cleanup()
        
    def create_test_config(self, config_data: Dict[str, Any]) -> None:
        """创建测试配置文件"""
        with open(self.temp_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
    
    def test_load_config_with_nickname_mapping(self):
        """测试加载包含昵称-地址映射表的配置文件"""
        # 创建测试配置
        test_config = {
            "nickname_address_mapping": {
                "TestUser1": "测试地址1",
                "TestUser2": "测试地址2"
            },
            "enable_nickname_address_injection": True,
            "nickname_address_injection_position": "bottom"
        }
        self.create_test_config(test_config)
        
        # 修改DATA_DIR为临时目录，以便测试load_config函数
        from bot.config import settings
        original_data_dir = settings.DATA_DIR
        settings.DATA_DIR = Path(self.temp_dir.name)
        
        try:
            # 测试加载配置
            config = load_config()
            self.assertIsInstance(config, dict)
            self.assertIn("nickname_address_mapping", config)
            self.assertIsInstance(config["nickname_address_mapping"], dict)
            self.assertEqual(config["nickname_address_mapping"]["TestUser1"], "测试地址1")
            self.assertEqual(config["nickname_address_mapping"]["TestUser2"], "测试地址2")
        finally:
            # 恢复原始DATA_DIR
            settings.DATA_DIR = original_data_dir
    
    def test_validate_valid_nickname_mapping(self):
        """测试验证有效的昵称-地址映射表配置"""
        # 修改BotSettings类的属性进行测试
        original_mapping = BotSettings.NICKNAME_ADDRESS_MAPPING
        original_enable = BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION
        original_position = BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION
        
        try:
            # 设置有效配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = {
                "ValidUser": "有效地址"
            }
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = True
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = "top"
            
            # 验证配置应该通过
            BotSettings.validate_config()
        finally:
            # 恢复原始配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = original_mapping
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = original_enable
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = original_position
    
    def test_validate_invalid_nickname_mapping(self):
        """测试验证无效的昵称-地址映射表配置"""
        # 修改BotSettings类的属性进行测试
        original_mapping = BotSettings.NICKNAME_ADDRESS_MAPPING
        original_enable = BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION
        original_position = BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION
        
        try:
            # 测试非字典类型映射表
            BotSettings.NICKNAME_ADDRESS_MAPPING = ["invalid", "mapping"]
            with self.assertRaises(AssertionError):
                BotSettings.validate_config()
            
            # 测试空字符串键
            BotSettings.NICKNAME_ADDRESS_MAPPING = {
                "": "无效地址"
            }
            with self.assertRaises(AssertionError):
                BotSettings.validate_config()
            
            # 测试空字符串值
            BotSettings.NICKNAME_ADDRESS_MAPPING = {
                "InvalidUser": ""
            }
            with self.assertRaises(AssertionError):
                BotSettings.validate_config()
            
            # 测试无效的注入位置
            BotSettings.NICKNAME_ADDRESS_MAPPING = {
                "ValidUser": "有效地址"
            }
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = "invalid_position"
            with self.assertRaises(AssertionError):
                BotSettings.validate_config()
        finally:
            # 恢复原始配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = original_mapping
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = original_enable
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = original_position
    
    def test_system_prompt_injection_bottom(self):
        """测试昵称-地址映射表在系统提示底部注入"""
        # 修改BotSettings类的属性进行测试
        original_mapping = BotSettings.NICKNAME_ADDRESS_MAPPING
        original_enable = BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION
        original_position = BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION
        
        try:
            # 设置测试配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = {
                "TestUser1": "测试地址1",
                "TestUser2": "测试地址2"
            }
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = True
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = "bottom"
            
            # 创建MemoryManager实例
            memory_manager = MemoryManager()
            
            # 测试构建系统提示
            system_msg = memory_manager.build_system_prompt("test_key", is_group=False)
            system_content = system_msg.content.msg
            
            # 验证映射表被注入到底部
            self.assertIn("用户昵称-地址映射表（请在回复中参考使用）:", system_content)
            self.assertIn("- TestUser1: 测试地址1", system_content)
            self.assertIn("- TestUser2: 测试地址2", system_content)
        finally:
            # 恢复原始配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = original_mapping
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = original_enable
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = original_position
    
    def test_system_prompt_injection_top(self):
        """测试昵称-地址映射表在系统提示顶部注入"""
        # 修改BotSettings类的属性进行测试
        original_mapping = BotSettings.NICKNAME_ADDRESS_MAPPING
        original_enable = BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION
        original_position = BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION
        
        try:
            # 设置测试配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = {
                "TestUser1": "测试地址1"
            }
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = True
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = "top"
            
            # 创建MemoryManager实例
            memory_manager = MemoryManager()
            
            # 测试构建系统提示
            system_msg = memory_manager.build_system_prompt("test_key", is_group=False)
            system_content = system_msg.content.msg
            
            # 验证映射表被注入到顶部
            lines = system_content.splitlines()
            # 前几行应该包含映射表
            self.assertIn("用户昵称-地址映射表（请在回复中参考使用）:", lines[0:5])
            self.assertIn("- TestUser1: 测试地址1", lines[0:5])
        finally:
            # 恢复原始配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = original_mapping
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = original_enable
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = original_position
    
    def test_system_prompt_injection_disabled(self):
        """测试禁用昵称-地址映射表注入"""
        # 修改BotSettings类的属性进行测试
        original_mapping = BotSettings.NICKNAME_ADDRESS_MAPPING
        original_enable = BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION
        original_position = BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION
        
        try:
            # 设置测试配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = {
                "TestUser1": "测试地址1"
            }
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = False
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = "bottom"
            
            # 创建MemoryManager实例
            memory_manager = MemoryManager()
            
            # 测试构建系统提示
            system_msg = memory_manager.build_system_prompt("test_key", is_group=False)
            system_content = system_msg.content.msg
            
            # 验证映射表没有被注入
            self.assertNotIn("用户昵称-地址映射表（请在回复中参考使用）:", system_content)
            self.assertNotIn("- TestUser1: 测试地址1", system_content)
        finally:
            # 恢复原始配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = original_mapping
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = original_enable
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = original_position
    
    def test_system_prompt_injection_empty_mapping(self):
        """测试空昵称-地址映射表的情况"""
        # 修改BotSettings类的属性进行测试
        original_mapping = BotSettings.NICKNAME_ADDRESS_MAPPING
        original_enable = BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION
        original_position = BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION
        
        try:
            # 设置测试配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = {}
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = True
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = "bottom"
            
            # 创建MemoryManager实例
            memory_manager = MemoryManager()
            
            # 测试构建系统提示
            system_msg = memory_manager.build_system_prompt("test_key", is_group=False)
            system_content = system_msg.content.msg
            
            # 验证映射表没有被注入（因为是空的）
            self.assertNotIn("用户昵称-地址映射表（请在回复中参考使用）:", system_content)
        finally:
            # 恢复原始配置
            BotSettings.NICKNAME_ADDRESS_MAPPING = original_mapping
            BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION = original_enable
            BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION = original_position


if __name__ == "__main__":
    unittest.main(verbosity=2)

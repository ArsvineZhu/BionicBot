#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置系统测试脚本
用于验证配置项是否正确加载，是否存在硬编码值
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.config.settings import BotSettings

def test_config_load():
    """测试配置项加载情况"""
    print("=" * 60)
    print("配置系统测试报告")
    print("=" * 60)
    
    # 打印所有配置项
    config_items = [
        key for key in dir(BotSettings) 
        if not key.startswith('_') and not callable(getattr(BotSettings, key))
    ]
    
    print(f"共检测到 {len(config_items)} 个配置项")
    print("=" * 60)
    
    for item in sorted(config_items):
        value = getattr(BotSettings, item)
        print(f"{item}: {value}")
    
    print("=" * 60)
    
    # 检查敏感配置项
    sensitive_items = [
        "TARGET_GROUPS",
        "TARGET_USERS",
    ]
    
    print("敏感配置项检查")
    print("=" * 60)
    
    for item in sensitive_items:
        if hasattr(BotSettings, item):
            value = getattr(BotSettings, item)
            print(f"{item}: {value} (类型: {type(value).__name__})")
        else:
            print(f"{item}: 未找到")
    
    print("=" * 60)
    print("配置系统测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_config_load()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置值验证脚本
用于验证配置文件中的值是否被正确加载到代码中
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.config.settings import BotSettings
from bot.config.settings import load_config

print("=" * 60)
print("配置值验证脚本")
print("=" * 60)

# 1. 直接查看BotSettings中的配置值
print("1. BotSettings配置值:")
print(f"   CONTEXT_SWITCH_ANALYZE_COUNT: {BotSettings.CONTEXT_SWITCH_ANALYZE_COUNT}")
print(f"   CONTEXT_SWITCH_MIN_MESSAGES: {BotSettings.CONTEXT_SWITCH_MIN_MESSAGES}")
print(f"   LONG_TERM_MEMORY_LIMIT: {BotSettings.LONG_TERM_MEMORY_LIMIT}")
print(f"   BOT_NAME: {BotSettings.BOT_NAME}")

# 2. 直接加载配置文件，查看原始配置值
print("\n2. 原始配置文件值:")
config = load_config()
print(f"   context_switch_analyze_count: {config.get('context_switch_analyze_count', '未配置')}")
print(f"   context_switch_min_messages: {config.get('context_switch_min_messages', '未配置')}")
print(f"   long_term_memory_limit: {config.get('long_term_memory_limit', '未配置')}")
print(f"   bot_name: {config.get('bot_name', '未配置')}")

# 3. 验证配置值是否一致
print("\n3. 配置值一致性验证:")
if config.get('context_switch_analyze_count') == BotSettings.CONTEXT_SWITCH_ANALYZE_COUNT:
    print("   ✅ context_switch_analyze_count配置值一致")
else:
    print(f"   ❌ context_switch_analyze_count配置值不一致: 配置文件={config.get('context_switch_analyze_count')}, BotSettings={BotSettings.CONTEXT_SWITCH_ANALYZE_COUNT}")

if config.get('context_switch_min_messages') == BotSettings.CONTEXT_SWITCH_MIN_MESSAGES:
    print("   ✅ context_switch_min_messages配置值一致")
else:
    print(f"   ❌ context_switch_min_messages配置值不一致: 配置文件={config.get('context_switch_min_messages')}, BotSettings={BotSettings.CONTEXT_SWITCH_MIN_MESSAGES}")

if config.get('long_term_memory_limit') == BotSettings.LONG_TERM_MEMORY_LIMIT:
    print("   ✅ long_term_memory_limit配置值一致")
else:
    print(f"   ❌ long_term_memory_limit配置值不一致: 配置文件={config.get('long_term_memory_limit')}, BotSettings={BotSettings.LONG_TERM_MEMORY_LIMIT}")

if config.get('bot_name') == BotSettings.BOT_NAME:
    print("   ✅ bot_name配置值一致")
else:
    print(f"   ❌ bot_name配置值不一致: 配置文件={config.get('bot_name')}, BotSettings={BotSettings.BOT_NAME}")

print("\n=" * 60)
print("配置值验证完成！")
print("=" * 60)

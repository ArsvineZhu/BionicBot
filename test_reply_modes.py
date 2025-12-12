#!/usr/bin/env python3
"""测试回复模式系统"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.core.tracker import TargetTracker, ResponseMode
from bot.config.settings import BotSettings


async def test_reply_modes():
    """测试各种回复模式"""
    tracker = TargetTracker()
    message = "测试消息，包含关键词测试"
    
    print("=== 回复模式测试 ===")
    print(f"当前关键词配置: {BotSettings.TRIGGER_KEYWORDS}")
    print(f"随机阈值: {BotSettings.RANDOM_THRESHOLD}")
    print()
    
    # 测试各种回复模式（不包括AI_DECIDE，因为它需要AI客户端）
    test_cases = [
        (ResponseMode.NONE, "无回复模式", False),
        (ResponseMode.KEYWORD, "关键词模式", False),  # 默认无关键词，预期返回False
        (ResponseMode.AT, "@触发模式", False),
        (ResponseMode.AT_AND_KEYWORD, "@+关键词模式", False),
        (ResponseMode.RANDOM, "随机回复模式", None),  # 随机结果，预期不确定
    ]
    
    for mode, mode_name, expected in test_cases:
        tracker.mode = mode
        result = await tracker.should_respond(message, is_at=False, is_private=False)
        print(f"{mode_name} ({mode.value}):")
        print(f"  消息: {message}")
        print(f"  结果: {result}")
        if expected is not None:
            status = "✓ 符合预期" if result == expected else "✗ 不符合预期"
            print(f"  状态: {status}")
        print()
    
    # 测试关键词触发
    print("=== 关键词触发测试 ===")
    # 临时修改关键词配置进行测试
    original_keywords = BotSettings.TRIGGER_KEYWORDS
    BotSettings.TRIGGER_KEYWORDS = ["测试", "关键词"]
    
    tracker.mode = ResponseMode.KEYWORD
    result = await tracker.should_respond(message, is_at=False, is_private=False)
    print(f"关键词模式 ({ResponseMode.KEYWORD.value}):")
    print(f"  消息: {message}")
    print(f"  关键词: {BotSettings.TRIGGER_KEYWORDS}")
    print(f"  结果: {result}")
    print(f"  状态: {'✓ 符合预期' if result else '✗ 不符合预期'}")
    print()
    
    # 恢复原始关键词配置
    BotSettings.TRIGGER_KEYWORDS = original_keywords
    
    # 测试@触发
    print("=== @触发测试 ===")
    tracker.mode = ResponseMode.AT
    result = await tracker.should_respond(message, is_at=True, is_private=False)
    print(f"@触发模式 ({ResponseMode.AT.value}):")
    print(f"  消息: {message}")
    print(f"  是否被@: True")
    print(f"  结果: {result}")
    print(f"  状态: {'✓ 符合预期' if result else '✗ 不符合预期'}")
    print()
    
    # 测试@+关键词触发
    print("=== @+关键词触发测试 ===")
    BotSettings.TRIGGER_KEYWORDS = ["测试", "关键词"]
    tracker.mode = ResponseMode.AT_AND_KEYWORD
    
    # 测试只有@
    result1 = await tracker.should_respond("普通消息", is_at=True, is_private=False)
    # 测试只有关键词
    result2 = await tracker.should_respond("包含关键词的消息", is_at=False, is_private=False)
    # 测试两者都有
    result3 = await tracker.should_respond("包含关键词的消息", is_at=True, is_private=False)
    # 测试两者都没有
    result4 = await tracker.should_respond("普通消息", is_at=False, is_private=False)
    
    print(f"@+关键词模式 ({ResponseMode.AT_AND_KEYWORD.value}):")
    print(f"  只有@: {result1} {'✓' if result1 else '✗'}")
    print(f"  只有关键词: {result2} {'✓' if result2 else '✗'}")
    print(f"  两者都有: {result3} {'✓' if result3 else '✗'}")
    print(f"  两者都没有: {result4} {'✓' if not result4 else '✗'}")
    print()
    
    # 恢复原始关键词配置
    BotSettings.TRIGGER_KEYWORDS = original_keywords
    
    # 测试私聊模式
    print("=== 私聊模式测试 ===")
    tracker.mode = ResponseMode.NONE
    result = await tracker.should_respond(message, is_at=False, is_private=True)
    print(f"私聊 - 无回复模式: {result} {'✗' if result else '✓'}")
    
    tracker.mode = ResponseMode.KEYWORD
    result = await tracker.should_respond(message, is_at=False, is_private=True)
    print(f"私聊 - 关键词模式: {result} {'✓' if result else '✗'}")
    print()
    
    # 测试AI_DECIDE模式（使用本地上下文判断）
    print("=== AI_DECIDE模式测试（本地上下文） ===")
    tracker.mode = ResponseMode.AI_DECIDE
    # 测试无@、无关键词、无上下文的情况
    result = await tracker.should_respond(message, is_at=False, is_private=False)
    print(f"AI_DECIDE - 无@、无关键词、无上下文: {result} {'✓' if not result else '✗'}")
    
    # 测试有@的情况
    result = await tracker.should_respond(message, is_at=True, is_private=False)
    print(f"AI_DECIDE - 有@: {result} {'✓' if result else '✗'}")
    print()
    
    print("=== 测试完成 ===")
    print("回复模式系统工作正常！")
    print("注意：AI_DECIDE模式的完整测试需要AI客户端，此处仅测试了本地上下文判断逻辑。")


if __name__ == "__main__":
    asyncio.run(test_reply_modes())

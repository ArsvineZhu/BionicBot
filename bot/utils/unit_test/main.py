import json
import os
from typing import Dict, List, Optional, Union
# import logging
from random import random

from ncatbot.utils import get_log
from ncatbot.core import (
    BotClient,
    GroupMessageEvent,
    PrivateMessageEvent,
    MessageArray,
)
from ncatbot.core.event.message_segment import MessageArray
from ncatbot.core.event.message_segment import Text, At, Image, Face
from ncatbot.core.event import BaseMessageEvent

from volcenginesdkarkruntime import Ark
from bot.core.model import Content, Message, ApiModel, ROLE_TYPE, EFFORT, ABILITY
from bot.core.api_key import API_KEY

# 配置参数
CONFIG = {
    "target_groups": ["123456789"],  # 目标群聊ID（字符串类型，示例值）
    "target_users": ["987654321"],  # 目标用户ID（私聊，字符串类型，示例值）
    "model": "doubao-seed-1-6-flash-250828",
    "short_term_memory_limit": 30,  # 短期记忆最大消息数
    "long_term_memory_path": "./long_term_memory.json",  # 长期记忆存储路径
    "response_mode": "at_and_keyword",  # 回复模式：none/keyword/at/at_and_keyword/ai_decide/random
    "trigger_keywords": ["yuki"],  # 触发关键字
    "random_threshold": 0.1,  # 概率阈值（0-1）
}

logger = get_log("AIChatBot")  # 初始化日志


class LongTermMemory:
    """长期记忆管理（持久化存储）"""

    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.memory: Dict[str, List[str]] = self._load_memory()

    def _load_memory(self) -> Dict[str, List[str]]:
        """加载长期记忆"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_memory(self):
        """保存长期记忆"""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)

    def get_memory(self, group_id: str) -> List[str]:
        """获取指定群的长期记忆"""
        return self.memory.get(group_id, [])

    def add_memory(self, group_id: str, content: str):
        """添加长期记忆"""
        if group_id not in self.memory:
            self.memory[group_id] = []
        self.memory[group_id].append(content)
        self._save_memory()


class AIChatBot:
    """整合AI的对话模块（支持群聊共享记忆/私聊独立记忆）"""

    def __init__(self):
        # 初始化Ark客户端
        self.client = Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=API_KEY,
        )

        # 加载身份文件
        with open(r".\soul_doc\yuki.md", "r", encoding="utf-8") as file:
            self.soul = file.read()

        # 长期记忆管理
        self.long_term_memory = LongTermMemory(CONFIG["long_term_memory_path"])

        # 维护不同群聊的对话历史（短期记忆）
        self.group_conversations: Dict[str, Dict] = {}

    def _build_system_prompt(self, group_id: str) -> str:
        """构建包含长期记忆的系统提示词"""
        long_term = self.long_term_memory.get_memory(group_id)
        long_term_str = (
            "\n".join([f"- {item}" for item in long_term])
            if long_term
            else "暂无长期记忆"
        )
        return f"""
{self.soul}

=== 长期记忆 ===
{long_term_str}

=== 注意事项 ===
当需要长期记住的信息出现时，请在回复中用【长期记忆】标记（例如：【长期记忆】用户小明喜欢猫）
"""

    async def get_ai_response(
        self, message: str, user_info: dict, group_id: Optional[str] = None
    ) -> str:
        """获取AI回复（支持群聊共享记忆/私聊独立记忆）"""
        # 区分群聊和私聊
        if group_id:
            conv_key = f"group_{group_id}"
            is_group = True
        else:
            conv_key = f"user_{user_info['user_id']}"
            is_group = False

        # 初始化对话历史
        if conv_key not in self.group_conversations:
            self.group_conversations[conv_key] = {
                "messages": [],  # 短期记忆消息列表
                "response_id": None,  # 对话ID（用于多轮续接）
            }

        conv = self.group_conversations[conv_key]

        # 构建用户消息（带身份信息）
        user_msg = Message(
            content=Content(
                f"{user_info['nickname']}({user_info['user_id']}): {message}"
            ),
            role=ROLE_TYPE.USER,
        )
        conv["messages"].append(user_msg)

        # 截断短期记忆（保持最新N条）
        if len(conv["messages"]) > CONFIG["short_term_memory_limit"]:
            conv["messages"] = conv["messages"][-CONFIG["short_term_memory_limit"] :]

        # 构建系统提示（包含长期记忆）
        if is_group:
            sys_prompt = self._build_system_prompt(group_id)  # type: ignore
        else:
            sys_prompt = self.soul

        sys_msg = Message(content=Content(sys_prompt), role=ROLE_TYPE.SYSTEM)

        # 构建请求数据
        messages = [sys_msg] + conv["messages"]
        apimodel = ApiModel(
            model=CONFIG["model"],
            messages=messages,
            previous_response_id=conv["response_id"],
            thinking=ABILITY.ENABLED,
            temperature=1,
            # reasoning=EFFORT.MEDIUM,
        ).export

        try:
            # 调用AI接口
            response = self.client.responses.create(**apimodel)
            conv["response_id"] = response.id  # type: ignore

            # 提取回复内容
            if hasattr(response.output, "__getitem__") and len(response.output) > 0:  # type: ignore
                reply = response.output[0].content[0].text  # type: ignore
            else:
                reply = "[ERR]AI回复格式异常"

            # 处理长期记忆更新（如果是群聊且包含标记）
            if is_group and "【长期记忆】" in reply:
                # 提取需要长期保存的内容
                memory_content = reply.split("【长期记忆】")[-1].strip()
                if memory_content:
                    self.long_term_memory.add_memory(group_id, memory_content)  # type: ignore
                    # 移除回复中的标记
                    reply = reply.replace("【长期记忆】", "")

            # 保存AI回复到短期记忆
            ai_msg = Message(content=Content(reply), role=ROLE_TYPE.ASSIST)
            conv["messages"].append(ai_msg)

            return reply

        except Exception as e:
            logger.error(f"AI调用失败: {str(e)}")  # 详细日志记录
            return "暂时无法回复，请稍后再试"  # 用户友好提示


class TargetTracker:
    """目标追踪与回复触发判断"""

    @staticmethod
    def is_target(event: BaseMessageEvent) -> bool:
        """判断是否为目标对象"""
        if isinstance(event, GroupMessageEvent):
            return str(event.group_id) in CONFIG["target_groups"]
        elif isinstance(event, PrivateMessageEvent):
            return str(event.user_id) in CONFIG["target_users"]
        return False

    @staticmethod
    def should_respond(mode: str, message_text: str, is_at: bool) -> bool:
        """根据回复模式判断是否需要响应"""
        if mode == "none":
            return False
        elif mode == "keyword":
            return any(
                keyword in message_text for keyword in CONFIG["trigger_keywords"]
            )
        elif mode == "at":
            return is_at
        elif mode == "at_and_keyword":
            return is_at and any(
                keyword in message_text for keyword in CONFIG["trigger_keywords"]
            )
        elif mode == "ai_decide":
            return True  # 可替换为AI自主判断逻辑
        elif mode == "random":
            return random() < CONFIG["random_threshold"]
        return False

    @staticmethod
    def get_user_info(event: BaseMessageEvent) -> dict:
        """获取用户信息"""
        if isinstance(event, GroupMessageEvent):
            return {
                "user_id": str(event.user_id),
                "nickname": event.sender.nickname,
                "username": (
                    event.sender.card
                    if hasattr(event.sender, "card")
                    else event.sender.nickname
                ),
                "is_group": True,
                "group_id": str(event.group_id),
            }
        elif isinstance(event, PrivateMessageEvent):
            return {
                "user_id": str(event.user_id),
                "nickname": event.sender.nickname,
                "username": event.sender.nickname,
                "is_group": False,
                "group_id": None,
            }
        return {
            "user_id": "unknown",
            "nickname": "Unknown",
            "username": "Unknown",
            "is_group": False,
            "group_id": None,
        }


# 初始化机器人组件
bot = BotClient()
ai_bot = AIChatBot()
tracker = TargetTracker()


@bot.on_group_message()  # type: ignore
async def handle_group_message(msg: GroupMessageEvent):
    if not tracker.is_target(msg):
        return

    # 获取用户信息和消息内容
    user_info = tracker.get_user_info(msg)
    message_text = msg.raw_message.strip()
    group_id = user_info["group_id"]

    # 日志输出
    print(f"[群聊] {user_info['nickname']}: {message_text} (群:{group_id})")

    # 检查是否被@（通过消息段过滤）
    is_at = False
    try:
        # 获取机器人自身信息
        bot_info = await bot.api.get_login_info()
        bot_user_id = str(bot_info.user_id)

        # 过滤消息中的@段，判断是否包含机器人
        at_segments = msg.message.filter(At)
        is_at = any(at.qq == bot_user_id for at in at_segments)
    except Exception as e:
        print(f"获取机器人信息失败: {e}")

    # 判断是否需要回复
    if not tracker.should_respond(CONFIG["response_mode"], message_text, is_at):
        print(f"[忽略] 不符合回复条件 - 模式:{CONFIG['response_mode']}")
        return

    # 获取AI回复
    ai_reply = await ai_bot.get_ai_response(
        message=message_text, user_info=user_info, group_id=group_id
    )

    # 发送带@的回复
    reply_msg = MessageArray([At(user_info["user_id"]), Text(f" {ai_reply}")])
    await msg.reply(rtf=reply_msg)


@bot.on_private_message()  # type: ignore
async def handle_private_message(msg: PrivateMessageEvent):
    if not tracker.is_target(msg):
        return

    # 获取用户信息和消息内容
    user_info = tracker.get_user_info(msg)
    message_text = msg.raw_message.strip()

    # 日志输出
    print(f"[私聊] {user_info['nickname']}: {message_text}")

    # 获取AI回复（私聊无共享记忆）
    ai_reply = await ai_bot.get_ai_response(message=message_text, user_info=user_info)

    # 发送回复
    bot.api.send_private_msg_sync(user_info["user_id"], ai_reply) # type: ignore


if __name__ == "__main__":
    # 确保长期记忆存储目录存在
    os.makedirs(os.path.dirname(CONFIG["long_term_memory_path"]), exist_ok=True)
    bot.run()  # 启动机器人（前台模式）

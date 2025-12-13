# core/memory.py
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import re

from ncatbot.utils import get_log
from bot.utils.helpers import mask_sensitive_data
from bot.config.settings import BotSettings
from bot.core.model import Content, Message, ROLE_TYPE
from bot.core.conversation_manager import ConversationManager, ConversationThread

logger = get_log("MemoryManager")


@dataclass
class UserContext:
    """用户上下文"""
    messages: List[Message] = field(default_factory=list)
    last_active: datetime = field(default_factory=datetime.now)
    context_id: Optional[str] = None

@dataclass
class Conversation:
    """单次对话上下文"""
    # 全局消息（群聊所有消息）
    global_messages: List[Message] = field(default_factory=list)
    # 按用户区分的上下文
    user_contexts: Dict[str, UserContext] = field(default_factory=dict)
    response_id: Optional[str] = None
    last_active: datetime = field(default_factory=datetime.now)
    # 对话摘要
    summary: Optional[str] = None
    # 上次生成摘要的时间
    last_summarized: datetime = field(default_factory=datetime.now)


class LongTermMemory:
    """增强的长期记忆管理"""

    def __init__(self, storage_path: str = None):  # type: ignore
        self.storage_path = storage_path or BotSettings.LONG_TERM_MEMORY_PATH
        self.memory: Dict[str, List[Dict]] = self._load_memory()

    def _load_memory(self) -> Dict[str, List[Dict]]:
        """加载长期记忆"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载长期记忆失败: {e}")
                return {}
        return {}

    def _save_memory(self):
        """保存长期记忆"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存长期记忆失败: {e}")

    def get_memory(self, group_id: str, limit: int = 10) -> List[str]:
        """获取指定群的长期记忆"""
        if group_id not in self.memory:
            return []

        memories = (
            self.memory[group_id][-limit:] if limit > 0 else self.memory[group_id]
        )
        return [mem["content"] for mem in memories]

    def add_memory(self, group_id: str, content: str, importance: float = 1.0):
        """添加长期记忆"""
        if group_id not in self.memory:
            self.memory[group_id] = []

        # 生成内容哈希，避免重复
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]

        # 检查是否已存在
        existing_hashes = {mem.get("hash", "") for mem in self.memory[group_id]}
        if content_hash in existing_hashes:
            return

        memory_entry = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "importance": importance,
            "hash": content_hash,
        }

        self.memory[group_id].append(memory_entry)

        # 限制每个群的记忆数量
        if len(self.memory[group_id]) > 100:
            self.memory[group_id] = self.memory[group_id][-100:]

        self._save_memory()

    @staticmethod
    def extract_memory_tags(text: str) -> Optional[str]:
        """提取长期记忆标记"""

        patterns = [
            r"【长期记忆】(.+?)【/长期记忆】",
            r"\[长期记忆\](.+?)\[/长期记忆\]",
            r"<长期记忆>(.+?)</长期记忆>",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                # 清理多余的空白字符
                content = re.sub(r"\s+", " ", content)
                return content
        return None


class MemoryManager:
    """记忆管理器"""

    def __init__(self):
        self.long_term_memory = LongTermMemory()
        self.conversations: Dict[str, Conversation] = {}
        self.conversation_manager = ConversationManager()
        self.context_timeout = timedelta(hours=BotSettings.CONTEXT_TIMEOUT_HOURS)  # 上下文过期时间

    def get_conversation(self, key: str) -> Conversation:
        """获取或创建对话上下文"""
        if key not in self.conversations:
            self.conversations[key] = Conversation()
        return self.conversations[key]
        
    async def generate_conversation_summary(self, key: str, ai_client) -> Optional[str]:
        """生成对话摘要"""
        conv = self.get_conversation(key)
        
        # 如果没有足够的消息，不需要生成摘要
        if len(conv.global_messages) < BotSettings.SUMMARY_MIN_MESSAGES:
            return None
        
        # 生成摘要
        limit = min(BotSettings.SUMMARY_MAX_MESSAGES, len(conv.global_messages))
        summary = await ai_client.generate_summary(conv.global_messages[-limit:])  # 使用最近消息生成摘要
        if summary:
            conv.summary = summary
            conv.last_summarized = datetime.now()
            logger.info(f"成功生成对话摘要: {key}")
            logger.debug(f"摘要内容: {summary}")
            return summary
        
        return None
    
    async def check_and_generate_summaries(self, ai_client):
        """检查并生成所有需要的对话摘要"""
        logger.info("开始检查并生成对话摘要")
        for key, conv in self.conversations.items():
            # 检查是否需要生成摘要：
            # 1. 没有摘要
            # 2. 距离上次生成摘要超过指定小时数
            # 3. 消息数量超过指定数量且距离上次生成摘要超过指定分钟数
            need_summary = False
            time_since_last = datetime.now() - conv.last_summarized
            message_count = len(conv.global_messages)
            
            logger.debug(f"检查对话 {key}: 消息数量={message_count}, 上次摘要时间={time_since_last}")
            
            if not conv.summary:
                need_summary = True
                logger.debug(f"对话 {key}: 需要生成摘要，原因: 没有现有摘要")
            elif time_since_last > timedelta(hours=BotSettings.SUMMARY_INTERVAL_HOURS):
                need_summary = True
                logger.debug(f"对话 {key}: 需要生成摘要，原因: 距离上次摘要已超过 {BotSettings.SUMMARY_INTERVAL_HOURS} 小时")
            elif message_count > BotSettings.SUMMARY_MAX_MESSAGES and time_since_last > timedelta(minutes=BotSettings.SUMMARY_SHORT_INTERVAL_MINUTES):
                need_summary = True
                logger.debug(f"对话 {key}: 需要生成摘要，原因: 消息数量({message_count})超过限制，且距离上次摘要已超过 {BotSettings.SUMMARY_SHORT_INTERVAL_MINUTES} 分钟")
            
            if need_summary:
                logger.info(f"开始生成对话 {key} 的摘要")
                result = await self.generate_conversation_summary(key, ai_client)
                if result:
                    logger.info(f"对话 {key} 摘要生成完成")
                else:
                    logger.warning(f"对话 {key} 摘要生成失败")
        
        logger.info("所有对话摘要检查和生成完成")
    
    def cleanup_expired_contexts(self):
        """清理过期上下文"""
        expired_keys = []
        for key, conv in self.conversations.items():
            if datetime.now() - conv.last_active > self.context_timeout:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.conversations[key]
        
        # 清理不活跃的对话线程
        self.conversation_manager.cleanup_inactive_threads()
        
    def detect_context_switch(self, key: str, message: Message, user_id: str) -> bool:
        """检测是否需要切换上下文"""
        conv = self.get_conversation(key)
        
        # 如果是新用户，不需要切换
        if user_id not in conv.user_contexts:
            return False
        
        user_context = conv.user_contexts[user_id]
        
        # 如果用户上下文消息较少，不需要切换
        if len(user_context.messages) < BotSettings.CONTEXT_SWITCH_MIN_MESSAGES:
            return False
        
        # 简单的上下文切换检测：检查消息主题变化
        recent_messages = user_context.messages[-BotSettings.CONTEXT_SWITCH_ANALYZE_COUNT:]
        recent_text = " "
        
        for msg in recent_messages:
            if hasattr(msg, 'content') and hasattr(msg.content, 'content'):
                recent_text += msg.content.content + " "
        
        current_text = message.content.content if hasattr(message, 'content') and hasattr(message.content, 'content') else ""
        
        # 提取关键词
        recent_words = set(re.findall(r'\b\w{2,}\b', recent_text.lower()))
        current_words = set(re.findall(r'\b\w{2,}\b', current_text.lower()))
        
        # 如果共同关键词少于配置的阈值，认为需要切换上下文
        if not recent_words:
            return False
        
        common_ratio = len(recent_words.intersection(current_words)) / len(recent_words)
        return common_ratio < BotSettings.CONTEXT_SWITCH_THRESHOLD
        
    def switch_context(self, key: str, user_id: str) -> str:
        """切换上下文"""
        conv = self.get_conversation(key)
        
        # 创建新的用户上下文
        new_context = UserContext(
            context_id=f"ctx_{user_id}_{int(datetime.now().timestamp())}"
        )
        conv.user_contexts[user_id] = new_context
        
        return new_context.context_id

    def add_message(self, key: str, message: Message, user_id: str = None):
        """添加消息到对话，支持按用户区分上下文和上下文切换检测"""
        conv = self.get_conversation(key)
        
        # 添加到全局消息列表
        conv.global_messages.append(message)
        conv.last_active = datetime.now()
        
        # 限制全局消息数量
        if len(conv.global_messages) > BotSettings.SHORT_TERM_MEMORY_LIMIT:
            conv.global_messages = conv.global_messages[-BotSettings.SHORT_TERM_MEMORY_LIMIT :]
            logger.debug(f"上下文消息数量超过限制，已截取最近{BotSettings.SHORT_TERM_MEMORY_LIMIT}条消息")
        
        # 如果提供了user_id，添加到用户特定上下文
        if user_id:
            # 检测是否需要切换上下文
            if self.detect_context_switch(key, message, user_id):
                self.switch_context(key, user_id)
            
            if user_id not in conv.user_contexts:
                conv.user_contexts[user_id] = UserContext()
            
            user_context = conv.user_contexts[user_id]
            user_context.messages.append(message)
            user_context.last_active = datetime.now()
            
            # 限制用户上下文消息数量
            if len(user_context.messages) > BotSettings.SHORT_TERM_MEMORY_LIMIT:
                user_context.messages = user_context.messages[-BotSettings.SHORT_TERM_MEMORY_LIMIT :]
        
        # 对话线程管理
        if key.startswith("group_"):
            # 为群聊添加消息到对话线程
            message_text = message.content.content if hasattr(message, 'content') and hasattr(message.content, 'content') else ""
            thread_id = self.conversation_manager.detect_thread(message_text, user_id, conv.global_messages)
            thread = self.conversation_manager.get_or_create_thread(thread_id)
            thread.add_message(message, user_id)
            
            # 更新线程话题
            if not thread.topic or len(thread.messages) % BotSettings.TOPIC_DETECTION_INTERVAL == 0:  # 每N条消息更新一次话题
                thread.topic = self.conversation_manager.analyze_topic(thread)

    def get_messages(self, key: str, limit: int = None, user_id: str = None) -> List[Message]:  # type: ignore
        """获取对话消息，支持获取全局消息或用户特定消息，当有摘要时使用摘要+最近消息来减少tokens消耗"""
        conv = self.get_conversation(key)
        
        if user_id and user_id in conv.user_contexts:
            # 获取用户特定消息
            messages = conv.user_contexts[user_id].messages
        else:
            # 获取全局消息
            messages = conv.global_messages
        
        # 如果有摘要，并且消息数量超过阈值，使用摘要+最近消息
        if conv.summary and len(messages) > BotSettings.SUMMARY_MIN_MESSAGES * 2:
            # 使用摘要+最近消息，摘要作为第一条消息
            summary_message = Message(
                content=Content(f"[对话摘要] {conv.summary}"),
                role=ROLE_TYPE.SYSTEM
            )
            
            # 获取最近的几条消息，数量为限制的一半或固定数量
            recent_count = limit // 2 if limit and limit > 2 else 5
            recent_messages = messages[-recent_count:] if recent_count > 0 else []
            
            return [summary_message] + recent_messages
        
        if limit and len(messages) > limit:
            return messages[-limit:]
        return messages.copy()

    def build_system_prompt(self, key: str, is_group: bool = True) -> Message:
        """构建系统提示词"""
        # 读取灵魂文档
        try:
            with open(BotSettings.SOUL_DOC_PATH, "r", encoding="utf-8") as f:
                soul_content = f.read()
        except FileNotFoundError:
            logger.warning("灵魂文档未找到，使用默认描述")
            soul_content = f"你是一个名为Bionic的AI助手，乐于助人且知识渊博。"

        # 基础系统提示（原本有时间，改为每条消息提供）
        base_content = soul_content

        # 构建昵称-地址映射表内容
        nickname_address_content = ""
        if BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION and BotSettings.NICKNAME_ADDRESS_MAPPING:
            nickname_address_content = "\n\n用户【昵称】-【称呼】映射表（请在回复中参考使用，格式为【昵称】:【称呼】，同一个人可以有多个昵称，但你应当只用【称呼】指代）:"
            for nickname, mapping in BotSettings.NICKNAME_ADDRESS_MAPPING.items():
                # 处理两种格式：字符串或字典
                if isinstance(mapping, dict):
                    address = mapping.get("address", "")
                else:
                    address = mapping
                nickname_address_content += f"\n- {nickname}: {address}"

        # 根据配置的位置注入映射表
        system_content = ""
        if nickname_address_content:
            if BotSettings.NICKNAME_ADDRESS_INJECTION_POSITION == "top":
                system_content = f"{nickname_address_content}\n\n{base_content}"
            else:  # bottom
                system_content = f"{base_content}{nickname_address_content}"
        else:
            system_content = base_content

        # 如果是群聊，添加长期记忆
        if is_group and hasattr(key, "startswith") and key.startswith("group_"):
            group_id = key.replace("group_", "")
            long_memories = self.long_term_memory.get_memory(group_id, limit=BotSettings.LONG_TERM_MEMORY_LIMIT)
            if long_memories:
                system_content += "\n\n长期记忆（重要信息，请记住）:"
                for i, memory in enumerate(long_memories, 1):
                    # 掩码处理记忆中的敏感数据
                    masked_memory = mask_sensitive_data(memory)
                    system_content += f"\n{i}. {masked_memory}"

        system_content += """\n如果有需要长期记住的信息，请在回复中使用【长期记忆】内容【/长期记忆】格式标记"""

        return Message(content=Content(system_content), role=ROLE_TYPE.SYSTEM)

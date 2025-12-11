# core/conversation_manager.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import re

from bot.core.model import Message


@dataclass
class ConversationThread:
    """对话线程"""
    thread_id: str
    messages: List[Message] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    last_active: datetime = field(default_factory=datetime.now)
    topic: Optional[str] = None
    
    def add_message(self, message: Message, user_id: str):
        """添加消息到线程"""
        self.messages.append(message)
        self.last_active = datetime.now()
        if user_id not in self.participants:
            self.participants.append(user_id)
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """获取最近的消息"""
        return self.messages[-limit:] if limit < len(self.messages) else self.messages
    
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """判断线程是否活跃"""
        return datetime.now() - self.last_active < timedelta(minutes=timeout_minutes)


class ConversationManager:
    """对话线程管理器"""
    
    def __init__(self):
        self.threads: Dict[str, ConversationThread] = {}
        self.thread_counter = 0
        self.default_thread_id = "default"
        
        # 创建默认线程
        self.threads[self.default_thread_id] = ConversationThread(
            thread_id=self.default_thread_id,
            topic="默认话题"
        )
    
    def _generate_thread_id(self) -> str:
        """生成线程ID"""
        self.thread_counter += 1
        return f"thread_{self.thread_counter}_{int(datetime.now().timestamp())}"
    
    def get_or_create_thread(self, thread_id: Optional[str] = None) -> ConversationThread:
        """获取或创建线程"""
        if not thread_id or thread_id not in self.threads:
            thread_id = self._generate_thread_id()
            self.threads[thread_id] = ConversationThread(thread_id=thread_id)
        return self.threads[thread_id]
    
    def detect_thread(self, message_text: str, user_id: str, conversation_history: List[Message]) -> str:
        """检测消息属于哪个线程"""
        # 简单的线程检测逻辑
        
        # 1. 检查是否引用了特定消息
        # 这里可以扩展为检查消息引用、回复等
        
        # 2. 检查是否有明确的话题切换
        topic_switch_patterns = [
            r"^(?:新话题|换个话题|讨论一下|聊点别的).*",
            r"^(?:关于|针对|对于).*?的话题",
        ]
        
        for pattern in topic_switch_patterns:
            if re.match(pattern, message_text, re.IGNORECASE):
                # 创建新线程
                return self._generate_thread_id()
        
        # 3. 检查与最近线程的相关性
        recent_threads = sorted(
            [t for t in self.threads.values() if t.is_active()],
            key=lambda x: x.last_active,
            reverse=True
        )
        
        for thread in recent_threads:
            if self._is_message_related_to_thread(message_text, thread):
                return thread.thread_id
        
        # 4. 检查与默认线程的相关性
        default_thread = self.threads[self.default_thread_id]
        if self._is_message_related_to_thread(message_text, default_thread):
            return self.default_thread_id
        
        # 5. 创建新线程
        return self._generate_thread_id()
    
    def _is_message_related_to_thread(self, message_text: str, thread: ConversationThread) -> bool:
        """判断消息是否与线程相关"""
        if not thread.messages:
            return True
        
        # 检查关键词重叠
        recent_messages = thread.get_recent_messages(limit=5)
        thread_keywords = set()
        
        for msg in recent_messages:
            if hasattr(msg, 'content') and hasattr(msg.content, 'content'):
                msg_text = msg.content.content.lower()
                thread_keywords.update(re.findall(r'\b\w{2,}\b', msg_text))
        
        message_keywords = set(re.findall(r'\b\w{2,}\b', message_text.lower()))
        
        # 如果有2个以上共同关键词，认为相关
        if len(thread_keywords.intersection(message_keywords)) >= 2:
            return True
        
        # 如果消息很短，相关性要求降低
        if len(message_text) < 20:
            return len(thread_keywords.intersection(message_keywords)) >= 1
        
        return False
    
    def cleanup_inactive_threads(self, timeout_minutes: int = 60):
        """清理不活跃的线程"""
        inactive_threads = [
            thread_id for thread_id, thread in self.threads.items()
            if thread_id != self.default_thread_id and not thread.is_active(timeout_minutes)
        ]
        
        for thread_id in inactive_threads:
            del self.threads[thread_id]
    
    def get_active_threads(self, limit: int = 5) -> List[ConversationThread]:
        """获取活跃线程"""
        return sorted(
            [t for t in self.threads.values() if t.is_active()],
            key=lambda x: x.last_active,
            reverse=True
        )[:limit]
    
    def merge_threads(self, thread_id1: str, thread_id2: str) -> str:
        """合并两个线程"""
        if thread_id1 not in self.threads or thread_id2 not in self.threads:
            return thread_id1
        
        thread1 = self.threads[thread_id1]
        thread2 = self.threads[thread_id2]
        
        # 将thread2的消息合并到thread1
        for msg in thread2.messages:
            thread1.messages.append(msg)
        
        # 合并参与者
        for participant in thread2.participants:
            if participant not in thread1.participants:
                thread1.participants.append(participant)
        
        # 更新最后活跃时间
        thread1.last_active = max(thread1.last_active, thread2.last_active)
        
        # 删除thread2
        del self.threads[thread_id2]
        
        return thread_id1
    
    def analyze_topic(self, thread: ConversationThread) -> str:
        """分析线程话题"""
        if not thread.messages:
            return "未确定话题"
        
        # 简单的话题提取：使用最近消息的关键词
        recent_messages = thread.get_recent_messages(limit=3)
        all_text = " "
        
        for msg in recent_messages:
            if hasattr(msg, 'content') and hasattr(msg.content, 'content'):
                all_text += msg.content.content + " "
        
        # 提取关键词
        words = re.findall(r'\b\w{2,}\b', all_text.lower())
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # 过滤常见词
        common_words = {'的', '了', '和', '是', '在', '有', '就', '不', '这', '那', '我', '你', '他', '她', '它', '们', '也', '还', '但', '而', '却', '因为', '所以', '虽然', '但是', '如果', '那么'}
        filtered_words = {word: count for word, count in word_counts.items() if word not in common_words}
        
        # 获取前3个关键词
        top_keywords = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:3]
        
        if top_keywords:
            return ",".join([word for word, _ in top_keywords])
        
        return "未确定话题"

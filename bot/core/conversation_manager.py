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
            thread_id=self.default_thread_id
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

# core/tracker.py
import random
from typing import Union, Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import re

from ncatbot.core.event import BaseMessageEvent, GroupMessageEvent, PrivateMessageEvent
from ncatbot.utils import get_log
from bot.core.model import Message, ResponseMode
from bot.config.settings import BotSettings
from bot.core.language_manager import language_manager

logger = get_log("TargetTracker")


@dataclass
class UserInfo:
    """用户信息"""
    user_id: str
    nickname: str
    card: str = ""
    is_group: bool = False
    group_id: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.card or self.nickname


class TargetTracker:
    """目标追踪与触发判断"""
    
    def __init__(self):
        self.mode = ResponseMode(BotSettings.DEFAULT_RESPONSE_MODE)
        
    def is_target(self, event: BaseMessageEvent) -> bool:
        """判断是否为目标对象"""
        if isinstance(event, GroupMessageEvent):
            return str(event.group_id) in BotSettings.TARGET_GROUPS
        elif isinstance(event, PrivateMessageEvent):
            return str(event.user_id) in BotSettings.TARGET_USERS
        return False
    
    async def should_respond(
        self, 
        message_text: str, 
        is_at: bool = False, 
        is_private: bool = False,
        conversation_history: List[Message] = None,
        last_response_time: datetime = None,
        ai_client = None,
        user_info = None,
        group_id = None
    ) -> bool:
        """判断是否需要响应"""
        conversation_history = conversation_history or []
        
        # 回复决策日志字典
        decision_log = {
            "mode": self.mode.value,
            "is_at": is_at,
            "is_private": is_private,
            "contains_keyword": self._contains_keyword(message_text),
            "random_result": None,
            "context_related": None,
            "final_decision": False,
            "ai_decision": None
        }
        
        # 私聊总是回复（除非明确设置none模式）
        if is_private:
            decision = self.mode != ResponseMode.NONE
            decision_log["final_decision"] = decision
            logger.info(language_manager.get("info.reply_decision", decision=decision_log))
            return decision
        
        # 根据回复模式判断
        if self.mode == ResponseMode.NONE:
            decision_log["final_decision"] = False
            logger.info(language_manager.get("info.reply_decision", decision=decision_log))
            return False
        
        elif self.mode == ResponseMode.KEYWORD:
            contains_keyword = self._contains_keyword(message_text)
            decision_log["contains_keyword"] = contains_keyword
            decision_log["final_decision"] = contains_keyword
            logger.info(language_manager.get("info.reply_decision", decision=decision_log))
            return contains_keyword
        
        elif self.mode == ResponseMode.AT:
            decision_log["final_decision"] = is_at
            logger.info(language_manager.get("info.reply_decision", decision=decision_log))
            return is_at
        
        elif self.mode == ResponseMode.AT_AND_KEYWORD:
            decision = is_at or self._contains_keyword(message_text)
            decision_log["final_decision"] = decision
            logger.info(language_manager.get("info.reply_decision", decision=decision_log))
            return decision
        
        elif self.mode == ResponseMode.RANDOM:
            if is_at:
                decision_log["final_decision"] = True
                logger.info(language_manager.get("info.reply_decision", decision=decision_log))
                return True
            
            random_value = random.random()
            decision_log["random_result"] = {
                "value": random_value,
                "threshold": BotSettings.RANDOM_THRESHOLD
            }
            decision = random_value < BotSettings.RANDOM_THRESHOLD
            decision_log["final_decision"] = decision
            logger.info(language_manager.get("info.reply_decision", decision=decision_log))
            return decision
        
        elif self.mode == ResponseMode.AI_DECIDE:
            # 快速判断：如果被@或包含关键词，直接回复
            if is_at or self._contains_keyword(message_text):
                decision_log["final_decision"] = True
                logger.info(language_manager.get("info.reply_decision", decision=decision_log))
                return True
            
            # 添加随机概率控制
            random_value = random.random()
            decision_log["random_result"] = {
                "value": random_value,
                "threshold": BotSettings.RANDOM_THRESHOLD
            }
            
            # 如果随机值大于阈值，直接返回不回复
            if random_value >= BotSettings.RANDOM_THRESHOLD:
                decision_log["final_decision"] = False
                logger.info(language_manager.get("info.reply_decision", decision=decision_log))
                return False
            
            # 检查是否有AI客户端，否则使用本地上下文判断
            if ai_client and user_info:
                # 调用AI客户端判断是否应该回复
                ai_decision = await ai_client.should_respond(
                    message=message_text,
                    user_info=user_info,
                    group_id=group_id,
                    conversation_history=conversation_history
                )
                decision_log["ai_decision"] = ai_decision
                decision_log["final_decision"] = ai_decision
                logger.info(language_manager.get("info.reply_decision", decision=decision_log))
                return ai_decision
            
            # 备用方案：本地上下文关联判断
            context_related = self._is_context_related(message_text, conversation_history, last_response_time)
            decision_log["context_related"] = context_related
            decision_log["final_decision"] = context_related
            logger.info(language_manager.get("info.reply_decision", decision=decision_log))
            return context_related
        
        decision_log["final_decision"] = False
        logger.info(f"回复决策: {decision_log}")
        return False
    
    def _is_context_related(
        self, 
        message_text: str, 
        conversation_history: List[Message], 
        last_response_time: datetime = None
    ) -> bool:
        """判断消息是否与上下文相关"""
        # 检查是否启用上下文关联响应
        if not BotSettings.CONTEXT_RELATED_RESPONSE_ENABLED:
            return False
        
        # 如果没有对话历史，不相关
        if not conversation_history:
            return False
        
        # 如果最后回复时间超过配置的超时时间，不相关
        if last_response_time and datetime.now() - last_response_time > timedelta(minutes=BotSettings.CONTEXT_RELATED_TIMEOUT_MINUTES):
            return False
        
        # 获取最近的几条消息作为上下文
        recent_messages = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        # 简单的上下文相关性判断：检查关键词重叠
        context_keywords = set()
        for msg in recent_messages:
            if hasattr(msg, 'content') and hasattr(msg.content, 'content'):
                msg_text = msg.content.content.lower()
                context_keywords.update(re.findall(r'\b\w+\b', msg_text))
        
        # 提取当前消息的关键词
        current_keywords = set(re.findall(r'\b\w+\b', message_text.lower()))
        
        # 如果有2个以上共同关键词，认为相关
        if len(context_keywords.intersection(current_keywords)) >= 2:
            return True
        
        # 检查是否是对最近消息的直接回应
        if len(recent_messages) > 0:
            last_msg = recent_messages[-1]
            if hasattr(last_msg, 'content') and hasattr(last_msg.content, 'content'):
                last_msg_text = last_msg.content.content.lower()
                # 如果当前消息包含对最近消息的引用或延续
                if any(phrase in message_text.lower() for phrase in ['接着说', '继续', '然后呢', '后来呢', '还有吗']):
                    return True
        
        return False
    
    def _contains_keyword(self, text: str) -> bool:
        """检查是否包含关键词，支持正则表达式和模糊匹配"""
        if not text or not BotSettings.TRIGGER_KEYWORDS:
            return False
            
        text_lower = text.lower()
        
        for keyword in BotSettings.TRIGGER_KEYWORDS:
            keyword_lower = keyword.lower()
            
            # 检查是否为正则表达式（以^开头或$结尾或包含特殊字符）
            is_regex = any(special_char in keyword for special_char in ['^', '$', '*', '+', '?', '.', '(', ')', '[', ']', '{', '}', '|', '\\'])
            
            if BotSettings.ENABLE_REGEX_KEYWORDS and is_regex:
                try:
                    if re.search(keyword, text, re.IGNORECASE):
                        return True
                except re.error:
                    # 如果正则表达式无效，回退到普通匹配
                    if keyword_lower in text_lower:
                        return True
            else:
                # 普通关键词匹配
                if keyword_lower in text_lower:
                    return True
        return False
    
    def extract_user_info(self, event: BaseMessageEvent) -> UserInfo:
        """提取用户信息"""
        if isinstance(event, GroupMessageEvent):
            return UserInfo(
                user_id=str(event.user_id),
                nickname=event.sender.nickname,
                card=getattr(event.sender, 'card', ''),
                is_group=True,
                group_id=str(event.group_id)
            )
        elif isinstance(event, PrivateMessageEvent):
            return UserInfo(
                user_id=str(event.user_id),
                nickname=event.sender.nickname,
                is_group=False
            )
        
        # 默认返回
        return UserInfo(
            user_id="unknown",
            nickname="Unknown",
            is_group=False
        )
    
    def clean_message(self, raw_message: str, remove_at: bool = True) -> str:
        """清理消息内容"""
        if not raw_message:
            return ""
        
        # 移除CQ码
        import re
        cleaned = re.sub(r'\[CQ:.*?\]', '', raw_message)
        
        # 如果需要，移除@信息
        if remove_at:
            cleaned = re.sub(r'@[\w\u4e00-\u9fa5]+\s*', '', cleaned)
        
        return cleaned.strip()
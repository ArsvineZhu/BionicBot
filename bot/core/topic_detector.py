# core/topic_detector.py
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import re

from bot.core.model import Message
from bot.config.settings import BotSettings


@dataclass
class TopicInfo:
    """话题信息"""
    topic_words: List[str]
    confidence: float
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0


class TopicDetector:
    """话题相关性判断"""
    
    def __init__(self):
        # 常见停用词
        self.stop_words = {
            '的', '了', '和', '是', '在', '有', '就', '不', '这', '那', '我', '你', '他', '她', '它',
            '们', '也', '还', '但', '而', '却', '因为', '所以', '虽然', '但是', '如果', '那么',
            '一个', '这个', '那个', '这些', '那些', '时候', '地方', '可以', '可能', '应该',
            '会', '要', '人', '事', '物', '东西', '问题', '情况', '结果', '原因', '方法'
        }
        
        # 话题相关性阈值
        self.relevance_threshold = BotSettings.TOPIC_RELEVANCE_THRESHOLD
    
    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        
        # 清理文本
        text = re.sub(r'[^\w\u4e00-\u9fa5\s]', '', text)
        text = text.lower()
        
        # 分词（简单空格分割，可替换为更复杂的分词库）
        words = re.findall(r'\b\w{2,}\b', text)
        
        # 过滤停用词
        filtered_words = [word for word in words if word not in self.stop_words]
        
        # 统计词频
        word_freq: Dict[str, int] = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按词频排序，取前N个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]
    
    def analyze_topic(self, messages: List[Message], top_n: int = 5) -> TopicInfo:
        """分析一组消息的话题"""
        if not messages:
            return TopicInfo(topic_words=[], confidence=0.0)
        
        # 合并所有消息文本
        all_text = " "
        for msg in messages:
            if hasattr(msg, 'content') and hasattr(msg.content, 'content'):
                all_text += msg.content.content + " "
        
        # 提取关键词
        topic_words = self._extract_keywords(all_text, top_n)
        
        # 计算置信度（基于关键词数量）
        confidence = len(topic_words) / top_n
        
        return TopicInfo(
            topic_words=topic_words,
            confidence=confidence,
            message_count=len(messages)
        )
    
    def is_relevant(self, message: Message, current_topic: TopicInfo) -> bool:
        """判断消息是否与当前话题相关"""
        if not current_topic.topic_words:
            return True
        
        message_text = message.content.content if hasattr(message, 'content') and hasattr(message.content, 'content') else ""
        if not message_text:
            return False
        
        # 提取消息关键词
        message_keywords = self._extract_keywords(message_text, top_n=5)
        if not message_keywords:
            return False
        
        # 计算关键词重叠度
        topic_word_set = set(current_topic.topic_words)
        message_word_set = set(message_keywords)
        
        common_words = topic_word_set.intersection(message_word_set)
        overlap_ratio = len(common_words) / len(topic_word_set)
        
        # 计算相关性分数
        relevance_score = overlap_ratio * current_topic.confidence
        
        return relevance_score >= self.relevance_threshold
    
    def update_topic(self, current_topic: TopicInfo, new_messages: List[Message]) -> TopicInfo:
        """更新话题信息"""
        if not new_messages:
            return current_topic
        
        # 分析新消息的话题
        new_topic = self.analyze_topic(new_messages)
        
        # 合并话题关键词
        all_topic_words = list(set(current_topic.topic_words + new_topic.topic_words))
        
        # 计算新的置信度
        new_confidence = (current_topic.confidence * current_topic.message_count + 
                         new_topic.confidence * new_topic.message_count) / (current_topic.message_count + new_topic.message_count)
        
        return TopicInfo(
            topic_words=all_topic_words[:5],  # 保持最多5个关键词
            confidence=new_confidence,
            created_at=current_topic.created_at,
            updated_at=datetime.now(),
            message_count=current_topic.message_count + new_topic.message_count
        )
    
    def detect_topic_change(self, message: Message, current_topic: TopicInfo) -> bool:
        """检测是否发生话题变化"""
        if not current_topic.topic_words:
            return False
        
        return not self.is_relevant(message, current_topic)
    
    def get_topic_description(self, topic: TopicInfo) -> str:
        """获取话题描述"""
        if not topic.topic_words:
            return "未确定话题"
        
        return ",".join(topic.topic_words)
    
    def calculate_topic_similarity(self, topic1: TopicInfo, topic2: TopicInfo) -> float:
        """计算两个话题的相似度"""
        if not topic1.topic_words or not topic2.topic_words:
            return 0.0
        
        set1 = set(topic1.topic_words)
        set2 = set(topic2.topic_words)
        
        if not set1 and not set2:
            return 1.0
        
        # Jaccard相似度
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

# bot/core/__init__.py
# 核心功能模块
from .ai_client import AIClient, AIResponse
from .api_key import API_KEY
from .conversation_manager import ConversationManager
from .memory import MemoryManager
from .model import Message, Content, ApiModel, ROLE_TYPE, ABILITY, EFFORT
from .topic_detector import TopicDetector
from .tracker import TargetTracker, ResponseMode, UserInfo

__all__ = [
    # AI Client
    'AIClient',
    'AIResponse',
    # API Key
    'API_KEY',
    # Conversation Management
    'ConversationManager',
    # Memory Management
    'MemoryManager',
    # Model Classes
    'Message',
    'Content',
    'ApiModel',
    'ROLE_TYPE',
    'ABILITY',
    'EFFORT',
    # Topic Detection
    'TopicDetector',
    # Tracker
    'TargetTracker',
    'ResponseMode',
    'UserInfo'
]

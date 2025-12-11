# bot/handlers/__init__.py
# 消息处理器模块
from .group_handler import GroupMessageHandler
from .private_handler import PrivateMessageHandler

__all__ = [
    'GroupMessageHandler',
    'PrivateMessageHandler'
]

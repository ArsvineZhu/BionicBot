# main.py
import asyncio
from ncatbot.core import BotClient, GroupMessageEvent, PrivateMessageEvent
from ncatbot.utils import get_log

from .config.settings import BotSettings
from .core.ai_client import AIClient
from .core.tracker import TargetTracker
from .handlers.group_handler import GroupMessageHandler
from .handlers.private_handler import PrivateMessageHandler
from .utils.helpers import mask_sensitive_data

logger = get_log("Main")


class BionicBot:
    """Bionic 机器人"""
    
    def __init__(self):
        # 验证配置
        BotSettings.validate_config()
        
        # 初始化核心组件
        self.bot = BotClient()
        self.ai_client = AIClient()
        self.tracker = TargetTracker()
        
        # 初始化处理器
        self.group_handler = GroupMessageHandler(self.ai_client, self.tracker)
        self.private_handler = PrivateMessageHandler(self.ai_client, self.tracker)
        
        # 注册事件处理器
        self._register_handlers()
        
        logger.info("Bionic Bot 初始化完成")
        # 掩码处理目标群组ID，避免泄露真实群号
        masked_groups = [mask_sensitive_data(group) for group in BotSettings.TARGET_GROUPS]
        logger.info(f"目标群组: {masked_groups}")
        logger.info(f"回复模式: {BotSettings.DEFAULT_RESPONSE_MODE}")
    
    def _register_handlers(self):
        """注册事件处理器"""
        
        @self.bot.on_group_message() # type: ignore
        async def handle_group_message(event: GroupMessageEvent):
            """处理群聊消息"""
            await self.group_handler.handle(event, self.bot.api)
        
        @self.bot.on_private_message() # type: ignore
        async def handle_private_message(event: PrivateMessageEvent):
            """处理私聊消息"""
            await self.private_handler.handle(event, self.bot.api)
    
    def run(self):
        """启动机器人"""
        try:
            # 启动机器人
            self.bot.run_frontend()
            
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭机器人...")
        except Exception as e:
            logger.error(f"机器人运行异常: {e}", exc_info=True)
        finally:
            logger.info("机器人已关闭")

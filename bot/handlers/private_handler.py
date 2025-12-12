# handlers/private_handler.py
import asyncio
from ncatbot.core.api import BotAPI
from ncatbot.core import PrivateMessageEvent
from ncatbot.utils import get_log

from bot.core.ai_client import AIClient
from bot.core.tracker import TargetTracker
from bot.utils.helpers import mask_sensitive_data, get_masked_display_name

logger = get_log("PrivateHandler")


class PrivateMessageHandler:
    """私聊消息处理器"""
    
    def __init__(self, ai_client: AIClient, tracker: TargetTracker):
        self.ai_client = ai_client
        self.tracker = tracker
    
    async def handle(self, event: PrivateMessageEvent, bot_api: BotAPI) -> bool:
        """处理私聊消息"""
        # 检查是否是目标用户
        if not self.tracker.is_target(event):
            return False
        
        # 提取用户信息
        user_info = self.tracker.extract_user_info(event)
        cleaned_message = self.tracker.clean_message(event.raw_message, remove_at=False)
        
        # 跳过空消息
        if not cleaned_message:
            return False
        
        # 记录日志
        masked_display_name = get_masked_display_name(user_info.display_name, user_info.user_id)
        logger.info(f"[私聊] {masked_display_name}: {cleaned_message[:50]}...")
        
        # 判断是否需要回复
        should_reply = await self.tracker.should_respond(
            message_text=cleaned_message,
            is_at=False,
            is_private=True,
            ai_client=self.ai_client,
            user_info=user_info.__dict__,
            group_id=None
        )
        
        if not should_reply:
            logger.debug(f"[忽略] 不符合回复条件 - 模式:{self.tracker.mode.value}")
            return False
        
        # 状态管理标志
        status_set = False
        
        try:
            # 设置状态为忙碌（表示输入中）- 只在开始处理时设置一次
            await bot_api.set_online_status(status=50, ext_status=0, battery_status=0)
            status_set = True
            logger.debug("[状态] 已设置为输入中")
            
            # 记录API调用开始时间
            import time
            api_start_time = time.time()
            
            # 获取AI回复
            ai_response = await self.ai_client.get_response(
                message=cleaned_message,
                user_info=user_info.__dict__,
                group_id=None,  # 私聊无群ID
                bot_api=bot_api
            )
            
            # 记录API调用结束时间
            api_end_time = time.time()
            
            # 计算API调用花费的时间
            api_time = api_end_time - api_start_time
            
            if not ai_response.content or ai_response.content.startswith("[错误]"):
                logger.error(f"AI回复失败: {ai_response.content}")
                return False
            
            # 处理多行消息(\n)
            msgs = ai_response.content.splitlines()
            
            # 计算消息总长度
            total_length = len(ai_response.content)
            
            # 计算基础延迟时间 (每字符延迟1秒，基础延迟1秒)
            base_delay = 1.0 + total_length * 1.0
            
            # 减去API调用已经花费的时间，确保延迟不会为负数
            delay_seconds = max(0.1, base_delay - api_time)
            
            # 发送消息，添加延迟
            for i, msg in enumerate(msgs):
                await bot_api.send_private_text(event.user_id, msg)
                
                # 除了最后一行，其他行之间添加延迟
                if i < len(msgs) - 1:
                    await asyncio.sleep(delay_seconds / len(msgs))
            
            logger.info(f"[回复] 已发送私聊回复，长度: {len(ai_response.content)}")
            
            return True
            
        except Exception as e:
            logger.error(f"处理私聊消息失败: {e}", exc_info=True)
            return False
        finally:
            # 只在成功设置过状态的情况下，恢复在线状态
            if status_set:
                await bot_api.set_online_status(status=10, ext_status=0, battery_status=0)
                logger.debug("[状态] 已恢复为在线")
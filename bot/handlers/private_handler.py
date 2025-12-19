# handlers/private_handler.py
import asyncio
import re
import time
from ncatbot.core.api import BotAPI
from ncatbot.core import PrivateMessageEvent, MessageArray
from ncatbot.core.event.message_segment import Image, Text, PlainText
from ncatbot.utils import get_log
from bot.config.settings import BotSettings
from bot.core.ai_client import AIClient
from bot.core.model import Message, Content, ROLE_TYPE
from bot.core.tracker import TargetTracker
from bot.utils.helpers import get_masked_display_name, format_log_text
from bot.core.language_manager import language_manager

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
        
        # 检查消息中是否包含图片
        images = []
        text_content = ""
        cleaned_message = ""
        
        # 遍历消息段
        if isinstance(event.message, MessageArray):
            for segment in event.message:
                if isinstance(segment, Text) or isinstance(segment, PlainText):
                    text_content += segment.text
                elif isinstance(segment, Image):
                    # 获取图片URL
                    if hasattr(segment, 'url') and segment.url:
                        images.append({
                            "file": segment.file,
                            "url": segment.url,
                            "type": segment.type if hasattr(segment, 'type') else "未知类型"
                        })
            
            # 清理文本消息
            cleaned_message = self.tracker.clean_message(text_content, remove_at=False)
        else:
            # 兼容旧格式
            cleaned_message = self.tracker.clean_message(event.raw_message, remove_at=False)
        
        # 跳过空消息（除非有图片）
        if not cleaned_message and not images:
            logger.debug(language_manager.get("debug.message_ignored", mode="空消息"))
            return False
        
        # 记录日志
        masked_display_name = get_masked_display_name(user_info.display_name, user_info.user_id)
        if images:
            logger.info(language_manager.get("info.private_message_received", user=masked_display_name, message=f"发送了 {len(images)} 张图片"))
        else:
            logger.info(language_manager.get("info.private_message_received", user=masked_display_name, message=format_log_text(cleaned_message, BotSettings.LOG_MAX_LENGTH)))
        
        try:
            # 处理图片消息
            if images:
                # 检查是否启用了图片解读
                if not BotSettings.ENABLE_IMAGE_INTERPRETATION:
                    logger.info(language_manager.get("info.image_interpretation_disabled", count=len(images)))
                    return True
                
                for i, img in enumerate(images, 1):
                    # 根据概率决定是否解读该图片
                    import random
                    if random.random() > BotSettings.IMAGE_INTERPRETATION_PROBABILITY:
                        logger.info(language_manager.get("info.image_skipped_by_probability", index=i))
                        continue
                    
                    logger.info(language_manager.get("info.image_interpreting", index=i, url=img['url']))
                    
                    # 获取AI图片解读
                    ai_response = await self.ai_client.get_image_response(
                        image_url=img['url'],
                        text_content=cleaned_message,
                        user_info=user_info.__dict__
                    )
                    
                    # 格式化解读内容
                    formatted_content = f"[{user_info.display_name}发送了图片/表情]解读内容：{ai_response.content}"
                    
                    # 构建系统消息，存入上下文
                    
                    # 生成系统消息
                    system_message = Message(
                        content=Content(formatted_content),
                        role=ROLE_TYPE.SYSTEM
                    )
                    
                    # 获取对话键名
                    conv_key = f"user_{user_info.user_id}"
                    
                    # 将消息添加到记忆管理器
                    self.ai_client.memory_manager.add_message(
                        key=conv_key,
                        message=system_message,
                        user_id=str(user_info.user_id)
                    )
                    
                    logger.info(language_manager.get("info.image_interpretation_stored", index=i))
            
                logger.info(language_manager.get("info.image_processing_complete"))
                return True
            
            # 判断是否需要回复文本消息
            should_reply = await self.tracker.should_respond(
                message_text=cleaned_message,
                is_at=False,
                is_private=True,
                ai_client=self.ai_client,
                user_info=user_info.__dict__,
                group_id=None
            )
            
            if not should_reply:
                logger.debug(language_manager.get("debug.message_ignored", mode=self.tracker.mode.value))
                return False
            
            # 处理文本消息
            # 记录API调用开始时间
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
                logger.error(language_manager.get("error.ai_response_failed", content=ai_response.content))
                return False
            
            # 清理AI回复中的@信息（私聊中通常不需要@）
            cleaned_content = ai_response.content
            
            # 移除CQ码格式的@
            cleaned_content = re.sub(r'\[CQ:at,qq=\d+\]', '', cleaned_content)
            
            # 移除@机器人自身的信息
            cleaned_content = re.sub(fr'@{BotSettings.BOT_NAME}', '', cleaned_content, flags=re.IGNORECASE)
            
            # 移除无意义的@
            cleaned_content = re.sub(r'@\s+', '', cleaned_content)
            
            # 处理多行消息(\n)
            msgs = cleaned_content.splitlines()
            # 过滤空行
            msgs = [msg.strip() for msg in msgs if msg.strip()]
            
            # 发送消息，添加延迟
            for i, msg in enumerate(msgs):
                await bot_api.send_private_text(event.user_id, msg)
                
                # 除了最后一行，其他行之间添加延迟
                if i < len(msgs) - 1:
                    if i == 0:
                        # 首条消息：计算总延迟并减去API调用时间
                        total_length = len(ai_response.content)
                        # 计算基础延迟时间
                        base_delay = BotSettings.BASE_DELAY_SECONDS + total_length * BotSettings.DELAY_PER_CHARACTER
                        # 减去API调用已经花费的时间，确保延迟不会为负数
                        delay_seconds = max(BotSettings.MIN_DELAY_SECONDS, base_delay - api_time)
                        await asyncio.sleep(delay_seconds / len(msgs))
                    else:
                        # 其他消息：使用单条消息的基础延迟，不减去API时间
                        msg_length = len(msg)
                        # 计算当前行的基础延迟
                        msg_delay = max(BotSettings.MIN_DELAY_SECONDS, BotSettings.BASE_DELAY_SECONDS + msg_length * BotSettings.DELAY_PER_CHARACTER)
                        await asyncio.sleep(msg_delay)
            
                logger.info(language_manager.get("info.message_sent", length=len(msg)))
            
            return True
            
        except Exception as e:
            logger.error(language_manager.get("error.message_processing_failed", error=str(e)), exc_info=True)
            return False
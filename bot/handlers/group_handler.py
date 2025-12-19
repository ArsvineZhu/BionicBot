# handlers/group_handler.py
import asyncio
import re
import time
from ncatbot.core.api import BotAPI
from ncatbot.core import GroupMessageEvent, MessageArray
from ncatbot.core.event.message_segment import At, Text, Image, PlainText
from ncatbot.utils import get_log

from bot.core.ai_client import AIClient
from bot.core.model import Message, Content, ROLE_TYPE
from bot.core.tracker import TargetTracker
from bot.config.settings import BotSettings
from bot.utils.helpers import get_masked_display_name, format_log_text
from bot.core.language_manager import language_manager

logger = get_log("GroupHandler")


class GroupMessageHandler:
    """群聊消息处理器"""
    
    def __init__(self, ai_client: AIClient, tracker: TargetTracker):
        self.ai_client = ai_client
        self.tracker = tracker
        self.bot_user_id = None
    
    async def handle(self, event: GroupMessageEvent, bot_api: BotAPI) -> bool:
        """处理群聊消息"""
        # 检查是否是目标群
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
            cleaned_message = self.tracker.clean_message(text_content)
        else:
            # 兼容旧格式
            cleaned_message = self.tracker.clean_message(event.raw_message)
        
        # 跳过空消息（除非有图片）
        if not cleaned_message and not images:
            logger.debug(language_manager.get("debug.message_ignored", mode="空消息"))
            return False
        
        # 记录日志
        masked_display_name = get_masked_display_name(user_info.display_name, user_info.user_id)
        if images:
            logger.info(language_manager.get("info.group_message_received", user=masked_display_name, message=f"发送了 {len(images)} 张图片"))
        else:
            logger.info(language_manager.get("info.group_message_received", user=masked_display_name, message=format_log_text(cleaned_message, BotSettings.LOG_MAX_LENGTH)))
        
        # 检查是否被@
        is_at = False
        
        # 如果bot_user_id未获取，尝试重新获取
        if not self.bot_user_id:
            try:
                bot_info = await bot_api.get_login_info()
                self.bot_user_id = str(bot_info.user_id)
                logger.info(language_manager.get("info.get_bot_info_success", user_id=self.bot_user_id))
            except Exception as e:
                logger.error(language_manager.get("error.get_bot_info_failed", error=e))
        
        if self.bot_user_id:
            # 优化@判断逻辑
            at_segments = event.message.filter(At)
            at_users = [at.qq for at in at_segments]
            logger.debug(language_manager.get("debug.at_list_in_message", at_list=at_users, bot_id=self.bot_user_id))
            
            # 精确匹配@机器人
            is_at = any(str(at_qq) == self.bot_user_id for at_qq in at_users)
            
            # 调试信息
            if is_at:
                logger.debug(language_manager.get("debug.at_bot_detected", user=masked_display_name))
            else:
                logger.debug(language_manager.get("debug.at_bot_not_detected"))
        else:
            logger.error(language_manager.get("error.bot_user_id_not_retrieved"))
        
        logger.debug(language_manager.get("debug.at_bot_detected", is_at=is_at, raw_message=event.raw_message))
        
        # 优化：处理@机器人但消息为空的情况
        if is_at and not cleaned_message:
            logger.debug(language_manager.get("debug.at_bot_empty_message", user=masked_display_name))
        
        # 处理图片消息
        if images:
            try:
                # 检查是否启用了图片解读
                if not BotSettings.ENABLE_IMAGE_INTERPRETATION:
                    logger.info(language_manager.get("info.image_interpretation_disabled", count=len(images)))
                    return True
                
                # 遍历每张图片
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
                    conv_key = f"group_{user_info.group_id}"
                    
                    # 将消息添加到记忆管理器
                    self.ai_client.memory_manager.add_message(
                        key=conv_key,
                        message=system_message,
                        user_id=str(user_info.user_id)
                    )
                    
                    logger.info(language_manager.get("info.image_interpretation_stored", index=i))
                
                logger.info(language_manager.get("info.image_processing_complete"))
                return True
            except Exception as e:
                logger.error(language_manager.get("error.failed_to_process_group_message", error=e), exc_info=True)
                return False
        
        # 判断是否需要回复文本消息
        should_reply = await self.tracker.should_respond(
            message_text=event.raw_message,
            is_at=is_at,
            is_private=False,
            ai_client=self.ai_client,
            user_info=user_info.__dict__,
            group_id=user_info.group_id
        )
        
        logger.debug(language_manager.get("debug.reply_judgment", should_reply=should_reply, mode=self.tracker.mode.value, is_at=is_at, keyword=self.tracker._contains_keyword(cleaned_message)))
        
        if not should_reply:
                logger.debug(language_manager.get("debug.message_ignored", mode=self.tracker.mode.value))
                return False
        
        try:
            # 记录API调用开始时间
            api_start_time = time.time()
            
            # 获取AI回复
            ai_response = await self.ai_client.get_response(
                message=cleaned_message,
                user_info=user_info.__dict__,
                group_id=user_info.group_id,
                bot_api=bot_api
            )
            
            # 记录API调用结束时间
            api_end_time = time.time()
            
            # 计算API调用花费的时间
            api_time = api_end_time - api_start_time
            
            if not ai_response.content or ai_response.content.startswith("[错误]"):
                logger.error(language_manager.get("error.ai_reply_failed", content=ai_response.content))
                return False
            
            # 清理AI回复中的@信息，避免重复@
            cleaned_content = ai_response.content
            
            # 智能清理@信息 - 保留有意义的@，移除重复的@
            # 1. 移除CQ码格式的@（避免格式冲突）
            cleaned_content = re.sub(r'\[CQ:at,qq=\d+\]', '', cleaned_content)
            
            # 2. 移除@机器人自身的信息（避免自我@）
            if self.bot_user_id:
                cleaned_content = re.sub(fr'@{BotSettings.BOT_NAME}', '', cleaned_content, flags=re.IGNORECASE)
            
            # 3. 移除无意义的@（如@空、@连续空格等）
            cleaned_content = re.sub(r'@\s+', '', cleaned_content)
            
            # 4. 移除重复的@（同一个用户被多次@）
            # 这里保持简单，只移除明显的重复@
            cleaned_content = re.sub(r'(@[\w\u4e00-\u9fa5]+)\s*\1', r'\1', cleaned_content, flags=re.IGNORECASE)
            
            # 处理多行消息(\n)
            msgs = cleaned_content.splitlines()
            # 过滤空行
            msgs = [msg.strip() for msg in msgs if msg.strip()]
            
            # 计算消息总长度
            total_length = len(cleaned_content)
            
            # 计算延迟时间
            base_delay = BotSettings.BASE_DELAY_SECONDS + total_length * BotSettings.DELAY_PER_CHARACTER
            
            # 减去API调用已经花费的时间，确保延迟不会为负数
            delay_seconds = max(BotSettings.MIN_DELAY_SECONDS, base_delay - api_time)
            
            # 发送首行消息（智能@）
            if msgs:
                # 构建首行消息
                first_line_segments = []
                
                # 智能@策略
                should_at = BotSettings.ENABLE_AT_REPLY and is_at
                
                # 调试信息
                logger.debug(language_manager.get("debug.at_reply_strategy", should_at=should_at, enable_at=BotSettings.ENABLE_AT_REPLY, is_at=is_at))
                
                # 只有在被@的情况下才@回复用户，避免不必要的@
                if should_at:
                    first_line_segments.append(At(user_info.user_id))
                    first_line_segments.append(Text(" "))
                    logger.debug(language_manager.get("debug.at_user_added", qq=user_info.user_id))
                
                # 根据昵称映射表添加@
                if BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION and BotSettings.NICKNAME_ADDRESS_MAPPING:
                    first_msg = msgs[0]
                    
                    # 遍历昵称映射表，检查消息中是否包含映射的昵称
                    for address, mapping in BotSettings.NICKNAME_ADDRESS_MAPPING.items():
                        # 获取昵称列表
                        nicknames = mapping.get("nicknames", []) if isinstance(mapping, dict) else []
                        
                        # 检查消息中是否包含该称呼或对应的任何昵称
                        if address in first_msg or any(nickname in first_msg for nickname in nicknames):
                            logger.debug(language_manager.get("debug.nickname_detected", address=address, nicknames=nicknames))
                            
                            # 如果映射中包含QQ号，添加@
                            if isinstance(mapping, dict) and "qq" in mapping and mapping["qq"]:
                                qq_number = mapping["qq"]
                                # 避免@发送者两次
                                if qq_number != str(user_info.user_id):
                                    first_line_segments.append(At(qq_number))
                                    first_line_segments.append(Text(" "))
                                    logger.debug(language_manager.get("debug.nickname_mapped_at", qq=qq_number, address=address))
                
                first_line_segments.append(Text(msgs[0]))
                
                # 发送首行
                first_line_msg = MessageArray(first_line_segments)
                await asyncio.sleep(delay_seconds)
                await bot_api.post_group_array_msg(event.group_id, first_line_msg)
                
                # 发送后续行（不带@）
                for i in range(1, len(msgs)):
                    # 计算当前行的基础延迟
                    msg = msgs[i]
                    msg_length = len(msg)
                    msg_delay = max(BotSettings.MIN_DELAY_SECONDS, BotSettings.BASE_DELAY_SECONDS + msg_length * BotSettings.DELAY_PER_CHARACTER)
                    
                    # 添加延迟
                    await asyncio.sleep(msg_delay)
                    
                    # 构建后续行消息（只包含文本）
                    next_line_segments = [Text(msg)]
                    next_line_msg = MessageArray(next_line_segments)
                    await bot_api.post_group_array_msg(event.group_id, next_line_msg)
            
            # 记录记忆添加情况
            if ai_response.contains_memory_tag:
                logger.info(language_manager.get("info.memory_added", content=format_log_text(ai_response.memory_content, BotSettings.LOG_MAX_LENGTH))) # type: ignore
            
            logger.info(language_manager.get("info.message_sent", length=len(ai_response.content)))
            return True
            
        except Exception as e:
            logger.error(language_manager.get("error.message_processing_failed", error=str(e)), exc_info=True)
            return False
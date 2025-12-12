# handlers/group_handler.py
import asyncio
from ncatbot.core.api import BotAPI
from ncatbot.core import GroupMessageEvent, MessageArray
from ncatbot.core.event.message_segment import At, Text
from ncatbot.utils import get_log

from bot.core.ai_client import AIClient
from bot.core.tracker import TargetTracker
from bot.config.settings import BotSettings
from bot.utils.helpers import mask_sensitive_data, get_masked_display_name

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
        raw_message = event.raw_message
        cleaned_message = self.tracker.clean_message(raw_message)
        
        # 跳过空消息
        if not cleaned_message:
            return False
        
        # 记录日志
        masked_display_name = get_masked_display_name(user_info.display_name, user_info.user_id)
        logger.info(f"[群聊] {masked_display_name}: {cleaned_message[:50]}...")
        
        # 检查是否被@
        is_at = False
        
        # 如果bot_user_id未获取，尝试重新获取
        if not self.bot_user_id:
            try:
                bot_info = await bot_api.get_login_info()
                self.bot_user_id = str(bot_info.user_id)
                logger.info(f"重新获取机器人用户ID: {self.bot_user_id}")
            except Exception as e:
                logger.error(f"获取机器人信息失败: {e}")
        
        if self.bot_user_id:
            at_segments = event.message.filter(At)
            logger.debug(f"[调试] 消息中的@列表: {[at.qq for at in at_segments]}, 机器人ID: {self.bot_user_id}")
            is_at = any(at.qq == self.bot_user_id for at in at_segments)
        else:
            logger.error("[调试] bot_user_id未获取到")
        
        logger.debug(f"[调试] 是否被@: {is_at}, 原始消息: {raw_message}")
        
        # 判断是否需要回复
        should_reply = await self.tracker.should_respond(
            message_text=raw_message,
            is_at=is_at,
            is_private=False,
            ai_client=self.ai_client,
            user_info=user_info.__dict__,
            group_id=user_info.group_id
        )
        
        logger.debug(f"[调试] 回复判断: {should_reply}, 模式: {self.tracker.mode.value}, 是否被@: {is_at}, 关键词: {self.tracker._contains_keyword(cleaned_message)}")
        
        if not should_reply:
            logger.debug(f"[忽略] 不符合回复条件 - 模式:{self.tracker.mode.value}, 是否被@: {is_at}, 关键词: {self.tracker._contains_keyword(cleaned_message)}")
            return False
        
        try:
            # 记录API调用开始时间
            import time
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
                logger.error(f"AI回复失败: {ai_response.content}")
                return False
            
            # 清理AI回复中的@信息，避免重复@
            import re
            cleaned_content = ai_response.content
            # 移除所有@用户名格式的文本
            cleaned_content = re.sub(r'@[\w\u4e00-\u9fa5]+\s*', '', cleaned_content)
            # 移除CQ码格式的@
            cleaned_content = re.sub(r'\[CQ:at,qq=\d+\]', '', cleaned_content)
            
            # 处理多行消息(\n)
            msgs = cleaned_content.splitlines()
            
            # 计算消息总长度
            total_length = len(cleaned_content)
            
            # 计算延迟时间 (每字符延迟1秒，基础延迟1秒)
            base_delay = 1.0 + total_length * 1.0
            
            # 减去API调用已经花费的时间，确保延迟不会为负数
            delay_seconds = max(0.1, base_delay - api_time)
            
            # 发送首行消息（带@）
            if msgs:
                # 构建首行消息
                first_line_segments = []
                if BotSettings.ENABLE_AT_REPLY:
                    first_line_segments.append(At(user_info.user_id))
                    first_line_segments.append(Text(" "))
                first_line_segments.append(Text(msgs[0]))
                
                # 发送首行
                first_line_msg = MessageArray(first_line_segments)
                await bot_api.post_group_array_msg(event.group_id, first_line_msg)
                
                # 发送后续行（不带@）
                for i in range(1, len(msgs)):
                    # 添加延迟
                    await asyncio.sleep(delay_seconds / len(msgs))
                    
                    # 构建后续行消息（只包含文本）
                    next_line_segments = [Text(msgs[i])]
                    next_line_msg = MessageArray(next_line_segments)
                    await bot_api.post_group_array_msg(event.group_id, next_line_msg)
            
            # 记录记忆添加情况
            if ai_response.contains_memory_tag:
                logger.info(f"[记忆] 添加长期记忆: {ai_response.memory_content[:50]}...") # type: ignore
            
            logger.info(f"[回复] 已发送回复，长度: {len(ai_response.content)}")
            return True
            
        except Exception as e:
            logger.error(f"处理群消息失败: {e}", exc_info=True)
            return False
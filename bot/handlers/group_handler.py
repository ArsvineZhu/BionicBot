# handlers/group_handler.py
import asyncio
from ncatbot.core.api import BotAPI
from ncatbot.core import GroupMessageEvent, MessageArray
from ncatbot.core.event.message_segment import At, Text, Image, PlainText
from ncatbot.utils import get_log

from bot.core.ai_client import AIClient
from bot.core.tracker import TargetTracker
from bot.config.settings import BotSettings
from bot.utils.helpers import get_masked_display_name

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
        
        # 跳过空消息（除非有图片或被@）
        if not cleaned_message and not images and not is_at:
            logger.debug("[调试] 消息为空且未被@，跳过处理")
            return False
        
        # 记录日志
        masked_display_name = get_masked_display_name(user_info.display_name, user_info.user_id)
        if images:
            logger.info(f"[群聊] {masked_display_name}: 发送了 {len(images)} 张图片")
        else:
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
            # 优化@判断逻辑
            at_segments = event.message.filter(At)
            at_users = [at.qq for at in at_segments]
            logger.debug(f"[调试] 消息中的@列表: {at_users}, 机器人ID: {self.bot_user_id}")
            
            # 精确匹配@机器人
            is_at = any(str(at_qq) == self.bot_user_id for at_qq in at_users)
            
            # 调试信息
            if is_at:
                logger.debug(f"[调试] 检测到@机器人消息")
            else:
                logger.debug(f"[调试] 未检测到@机器人消息")
        else:
            logger.error("[调试] bot_user_id未获取到")
        
        logger.debug(f"[调试] 是否被@: {is_at}, 原始消息: {event.raw_message}")
        
        # 优化：处理@机器人但消息为空的情况
        if is_at and not cleaned_message:
            logger.debug("[调试] 检测到@机器人但消息为空，准备回复")
        
        # 处理图片消息
        if images:
            try:
                for i, img in enumerate(images, 1):
                    logger.info(f"[群聊] 正在解读图片 {i}: {img['url']}")
                    
                    # 获取AI图片解读
                    ai_response = await self.ai_client.get_image_response(
                        image_url=img['url'],
                        text_content=cleaned_message,
                        user_info=user_info.__dict__
                    )
                    
                    # 格式化解读内容
                    formatted_content = f"[{user_info.display_name}发送了图片/表情]解读内容：{ai_response.content}"
                    
                    # 构建系统消息，存入上下文
                    from bot.core.model import Message, Content, ROLE_TYPE
                    
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
                    
                    logger.info(f"[上下文] 已将图片 {i} 的解读结果存入上下文")
                
                logger.info(f"[处理] 已完成 {len(images)} 张图片的解读和上下文存储")
                return True
            except Exception as e:
                logger.error(f"处理群图片消息失败: {e}", exc_info=True)
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
            
            # 计算消息总长度
            total_length = len(cleaned_content)
            
            # 计算延迟时间 (每字符延迟1秒，基础延迟1秒)
            base_delay = 1.0 + total_length * 1.0
            
            # 减去API调用已经花费的时间，确保延迟不会为负数
            delay_seconds = max(0.1, base_delay - api_time)
            
            # 发送首行消息（智能@）
            if msgs:
                # 构建首行消息
                first_line_segments = []
                
                # 智能@策略
                should_at = BotSettings.ENABLE_AT_REPLY and is_at
                
                # 调试信息
                logger.debug(f"[调试] 是否启用@回复: {should_at}, ENABLE_AT_REPLY: {BotSettings.ENABLE_AT_REPLY}, is_at: {is_at}")
                
                # 只有在被@的情况下才@回复用户，避免不必要的@
                if should_at:
                    first_line_segments.append(At(user_info.user_id))
                    first_line_segments.append(Text(" "))
                    logger.debug(f"[调试] 添加@用户 {user_info.user_id} 到回复消息")
                
                # 根据昵称映射表添加@
                if BotSettings.ENABLE_NICKNAME_ADDRESS_INJECTION and BotSettings.NICKNAME_ADDRESS_MAPPING:
                    first_msg = msgs[0]
                    
                    # 遍历昵称映射表，检查消息中是否包含映射的昵称
                    for nickname, mapping in BotSettings.NICKNAME_ADDRESS_MAPPING.items():
                        # 获取称呼
                        address = mapping.get("address", nickname) if isinstance(mapping, dict) else mapping
                        
                        # 检查消息中是否包含该昵称或称呼
                        if nickname in first_msg or address in first_msg:
                            logger.debug(f"[调试] 检测到消息中包含昵称映射表中的名称: {nickname} -> {address}")
                            
                            # 如果映射中包含QQ号，添加@
                            if isinstance(mapping, dict) and "qq" in mapping and mapping["qq"]:
                                qq_number = mapping["qq"]
                                # 避免@发送者两次
                                if qq_number != str(user_info.user_id):
                                    first_line_segments.append(At(qq_number))
                                    first_line_segments.append(Text(" "))
                                    logger.debug(f"[调试] 根据昵称映射表添加@用户 {qq_number} (对应称呼: {address})")
                
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
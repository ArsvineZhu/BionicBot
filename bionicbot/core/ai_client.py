# core/ai_client.py
import asyncio
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from volcenginesdkarkruntime import Ark
from bot.core.model import Content, Message, ApiModel, ROLE_TYPE, ABILITY, EFFORT
from bot.core.api_key import get_api_key, get_masked_api_key
from bot.config.settings import BotSettings
from bot.core.memory import MemoryManager


@dataclass
class AIResponse:
    """AI响应结果"""
    content: str
    response_id: Optional[str] = None
    contains_memory_tag: bool = False
    memory_content: Optional[str] = None


class AIClient:
    """AI客户端"""
    
    def __init__(self):
        self.client = Ark(
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key=get_api_key(),
        )
        self.memory_manager = MemoryManager()
        
    def _get_conversation_key(self, user_info: dict, group_id: Optional[str] = None) -> str:
        """获取对话键名"""
        if group_id:
            return f"group_{group_id}"
        return f"user_{user_info['user_id']}"
    
    async def get_response(
        self, 
        message: str, 
        user_info: dict, 
        group_id: Optional[str] = None,
        bot_api = None
    ) -> AIResponse:
        """获取AI响应"""
        # 获取对话键名
        conv_key = self._get_conversation_key(user_info, group_id)
        conv = self.memory_manager.get_conversation(conv_key)
        is_group = group_id is not None
        
        # 检查是否需要获取历史记录
        need_history = False
        if BotSettings.ENABLE_HISTORY_RETRIEVAL:
            # 检查是否是新会话或首条消息
            is_new_session = len(self.memory_manager.get_messages(conv_key)) == 0
            if is_new_session and BotSettings.HISTORY_RETRIEVAL_ON_NEW_SESSION:
                need_history = True
            elif BotSettings.HISTORY_RETRIEVAL_ON_FIRST_MESSAGE:
                need_history = True
        
        # 获取历史记录
        if need_history and bot_api:
            try:
                await self._fetch_and_integrate_history(
                    bot_api=bot_api,
                    user_info=user_info,
                    group_id=group_id,
                    conv_key=conv_key
                )
            except Exception as e:
                print(f"获取历史记录失败: {e}")
        
        # 构建用户消息，优先使用群昵称（card）而非用户名（nickname）
        display_name = user_info.get('card', '') or user_info.get('nickname', '未知用户')
        # 不要在用户消息中包含真实ID，避免泄露隐私
        # 添加时间戳，格式：25年22:45
        current_time = datetime.now().strftime('%y年%H:%M')
        user_message = Message(
            content=Content(f"{display_name}[{current_time}]: {message}"),
            role=ROLE_TYPE.USER
        )
        
        # 添加用户消息到记忆
        self.memory_manager.add_message(conv_key, user_message)
        
        # 构建系统提示词
        system_message = self.memory_manager.build_system_prompt(conv_key, is_group)
        
        # 获取对话历史
        history_messages = self.memory_manager.get_messages(conv_key, limit=10)
        
        # 构建请求消息
        messages = [system_message] + history_messages
        
        # 构建API请求
        apimodel = ApiModel(
            model=BotSettings.MODEL,
            messages=messages,
            previous_response_id=conv.response_id,
            thinking=ABILITY.ENABLED,
            temperature=1.0,
            #reasoning=EFFORT.MEDIUM,
        ).export(reasoning_available=False)
        
        try:
            # 调用AI接口
            response = self.client.responses.create(**apimodel)
            
            # 更新response_id
            conv.response_id = response.id # type: ignore
            
            # 提取回复内容
            reply_text = self._extract_reply_text(response)
            
            # 检查是否包含长期记忆标记
            memory_content = None
            if is_group:
                memory_content = self.memory_manager.long_term_memory.extract_memory_tags(reply_text)
                if memory_content:
                    self.memory_manager.long_term_memory.add_memory(group_id, memory_content)
                    # 从回复中移除标记
                    import re
                    for pattern in [r"【长期记忆】.+?【/长期记忆】", r"\[长期记忆\].+?\[/长期记忆\]"]:
                        reply_text = re.sub(pattern, "", reply_text, flags=re.DOTALL)
                    reply_text = reply_text.strip()
            
            # 添加AI回复到记忆
            # 添加时间戳，格式：25年22:45
            current_time = datetime.now().strftime('%y年%H:%M')
            ai_message = Message(
                content=Content(f"{BotSettings.BOT_NAME}[{current_time}]: {reply_text}"),
                role=ROLE_TYPE.ASSIST
            )
            self.memory_manager.add_message(conv_key, ai_message)
            
            return AIResponse(
                content=reply_text,
                response_id=conv.response_id,
                contains_memory_tag=memory_content is not None,
                memory_content=memory_content
            )
            
        except Exception as e:
            print(f"AI调用失败: {e}")
            return AIResponse(content="抱歉，我现在无法处理您的请求，请稍后再试。")
    
    async def _fetch_and_integrate_history(self, bot_api, user_info: dict, group_id: Optional[str], conv_key: str):
        """获取并整合历史记录"""
        is_group = group_id is not None
        history_messages = []
        
        try:
            if is_group:
                # 获取群聊历史记录
                history_events = await bot_api.get_group_msg_history(
                    group_id=group_id,
                    count=BotSettings.HISTORY_RETRIEVAL_LIMIT,
                    reverseOrder=True  # 获取最新的消息
                )
                
                # 解析群聊历史记录
                for event in history_events:
                    # 提取发送者信息和内容
                    sender_id = str(event.user_id)
                    sender_name = event.sender.nickname if hasattr(event.sender, 'nickname') else f"用户{sender_id}"
                    msg_content = event.raw_message
                    
                    # 构建Message对象，添加时间戳
                    # 注意：历史消息的时间信息可能无法获取，使用当前时间或格式化显示
                    # 由于无法获取历史消息的真实时间，我们使用简化的时间格式
                    history_msg = Message(
                        content=Content(f"{sender_name}[{datetime.now().strftime('%y年%H:%M')}]: {msg_content}"),
                        role=ROLE_TYPE.USER
                    )
                    history_messages.append(history_msg)
            else:
                # 获取私聊历史记录
                user_id = user_info['user_id']
                # 对于私聊，我们需要先获取最新的message_seq
                # 这里使用0获取最新的消息
                history_events = await bot_api.get_friend_msg_history(
                    user_id=user_id,
                    message_seq=0,  # 使用0获取最新消息
                    count=BotSettings.HISTORY_RETRIEVAL_LIMIT,
                    reverseOrder=True  # 获取最新的消息
                )
                
                # 解析私聊历史记录
                for event in history_events:
                    # 提取发送者信息和内容
                    sender_id = str(event.user_id)
                    msg_content = event.raw_message
                    
                    # 确定角色
                    if sender_id == user_id:
                        # 对方发送的消息
                        role = ROLE_TYPE.USER
                    else:
                        # 机器人自己发送的消息
                        role = ROLE_TYPE.ASSIST
                    
                    # 构建Message对象，添加时间戳
                    # 注意：历史消息的时间信息无法获取
                    # 由于无法获取历史消息的真实时间，我们使用简化的时间格式
                    # 确定发送者名称
                    # 尝试从event对象获取发送者信息
                    if hasattr(event, 'sender') and hasattr(event.sender, 'nickname'):
                        sender_name = event.sender.nickname
                    elif role == ROLE_TYPE.ASSIST:
                        sender_name = BotSettings.BOT_NAME  # 从配置中读取机器人名称
                    else:
                        sender_name = user_info.get('nickname', '用户')  # 使用用户提供的昵称或默认值
                    history_msg = Message(
                        content=Content(f"{sender_name}[历史对话]: {msg_content}"),
                        role=role
                    )
                    history_messages.append(history_msg)
            
            # 限制历史记录长度
            total_length = 0
            filtered_messages = []
            for msg in reversed(history_messages):
                msg_len = len(msg.content.msg)
                if total_length + msg_len <= BotSettings.HISTORY_RETRIEVAL_MAX_LENGTH:
                    filtered_messages.insert(0, msg)
                    total_length += msg_len
                else:
                    break
            
            # 将历史记录添加到记忆管理器
            for msg in filtered_messages:
                self.memory_manager.add_message(conv_key, msg)
            
            print(f"成功获取并整合{len(filtered_messages)}条历史记录到上下文")
        except Exception as e:
            print(f"获取历史记录失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_reply_text(self, response) -> str:
        """从响应中提取回复文本"""
        try:
            # 尝试从不同位置提取回复
            if hasattr(response, 'output') and response.output:
                for output in response.output:
                    if hasattr(output, 'content') and output.content:
                        for content in output.content:
                            if hasattr(content, 'text') and content.text:
                                return content.text.strip()
        except (AttributeError, IndexError):
            pass
        
        return "[错误] 无法解析AI回复"
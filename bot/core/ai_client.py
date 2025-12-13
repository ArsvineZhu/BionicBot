# core/ai_client.py
import asyncio
import re
import traceback
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

from volcenginesdkarkruntime import Ark
from ncatbot.utils import get_log
from bot.core.conversation_manager import ConversationManager
from bot.core.model import Content, Message, ApiModel, ROLE_TYPE, ABILITY, EFFORT
from bot.core.api_key import get_api_key, get_masked_api_key
from bot.config.settings import BotSettings
from bot.core.memory import MemoryManager

logger = get_log("AIClient")


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
            base_url=BotSettings.BASE_URL,
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
        
        # 获取对话历史
        history_messages = self.memory_manager.get_messages(conv_key, limit=10)
        
        # 检测是否需要添加系统提示词：仅在新建对话或新话题时添加
        need_system_prompt = False
        
        # 1. 新建对话：如果没有历史消息，需要系统提示词
        if not history_messages:
            need_system_prompt = True
        else:
            # 2. 新话题检测：检查最近的对话线程是否有新话题
            thread_id = self.memory_manager.conversation_manager.detect_thread(
                message, 
                user_info['user_id'], 
                self.memory_manager.get_conversation(conv_key).global_messages
            )
            thread = self.memory_manager.conversation_manager.get_or_create_thread(thread_id)
            
            # 如果是新创建的线程或者话题发生了变化，需要系统提示词
            if len(thread.messages) <= 1 or hasattr(thread, 'topic_just_changed') and thread.topic_just_changed:
                need_system_prompt = True
                # 重置话题变化标记
                if hasattr(thread, 'topic_just_changed'):
                    thread.topic_just_changed = False
        
        # 构建请求消息
        if need_system_prompt:
            # 构建系统提示词
            system_message = self.memory_manager.build_system_prompt(conv_key, is_group)
            messages = [system_message] + history_messages
        else:
            # 不需要系统提示词，直接使用历史消息
            messages = history_messages
        
        # 定期检查并生成对话摘要（每N条消息检查一次，N由配置指定）
        if BotSettings.SUMMARY_ENABLED:
            conv = self.memory_manager.get_conversation(conv_key)
            if len(conv.global_messages) % BotSettings.SUMMARY_CHECK_FREQUENCY == 0:
                await self.memory_manager.check_and_generate_summaries(self)
        
        # 构建API请求
        # 只在支持的情况下使用reasoning参数
        reasoning_value = getattr(EFFORT, BotSettings.REASONING, EFFORT.MEDIUM) if BotSettings.REASONING_AVAILABLE else EFFORT.MEDIUM
        
        apimodel = ApiModel(
            model=BotSettings.MODEL,
            messages=messages,
            previous_response_id=conv.response_id,
            thinking=ABILITY.ENABLED,
            temperature=BotSettings.TEMPERATURE,
            reasoning=reasoning_value,
            caching=BotSettings.CACHE,
            max_tokens=BotSettings.MAX_TOKENS,
            top_p=BotSettings.TOP_P,
            top_k=BotSettings.TOP_K,
            presence_penalty=BotSettings.PRESENCE_PENALTY,
            frequency_penalty=BotSettings.FREQUENCY_PENALTY,
            stop=BotSettings.STOP,
        ).export
        
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
            return AIResponse(content="抱歉，我现在无法处理您的请求，请稍后再试")
    
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
            
            # 在获取历史记录后生成对话摘要
            await self.memory_manager.generate_conversation_summary(conv_key, self)
            
            logger.info(f"成功获取并整合{len(filtered_messages)}条历史记录到上下文")
            
            # 记录整合的历史记录内容
            if filtered_messages:
                logger.debug("整合的历史记录内容:")
                for i, msg in enumerate(filtered_messages, 1):
                    logger.debug(f"  {i}. {msg.content.msg[:50]}...")
        except Exception as e:
            print(f"获取历史记录失败: {e}")
            traceback.print_exc()
    
    async def should_respond(
        self, 
        message: str, 
        user_info: dict, 
        group_id: Optional[str] = None,
        conversation_history: List[Message] = None
    ) -> bool:
        """询问AI是否应该回复当前消息"""
        conversation_history = conversation_history or []
        
        # 获取对话键名
        conv_key = self._get_conversation_key(user_info, group_id)
        is_group = group_id is not None
        
        # 构建系统提示词，专门用于判断是否应该回复
        decision_prompt = Message(
            content=Content(BotSettings.SHOULD_RESPOND_PROMPT),
            role=ROLE_TYPE.SYSTEM
        )
        
        # 构建用户消息
        display_name = user_info.get('card', '') or user_info.get('nickname', '未知用户')
        current_time = datetime.now().strftime('%y年%H:%M')
        user_msg = Message(
            content=Content(f"{display_name}[{current_time}]: {message}"),
            role=ROLE_TYPE.USER
        )
        
        # 构建请求消息列表，包含历史上下文和当前消息
        limit = min(BotSettings.HISTORY_RETRIEVAL_LIMIT, len(conversation_history))
        messages = [decision_prompt] + conversation_history[-limit:] + [user_msg]
        
        # 构建API请求
        # 只在支持的情况下使用reasoning参数
        reasoning_value = getattr(EFFORT, BotSettings.DECISION_REASONING, EFFORT.MINIMAL) if BotSettings.DECISION_REASONING_AVAILABLE else EFFORT.MEDIUM
        
        apimodel = ApiModel(
            model=BotSettings.DECISION_MODEL,
            messages=messages,
            thinking=ABILITY.DISABLED,  # 不需要思考过程
            temperature=BotSettings.DECISION_TEMPERATURE,  # 确定性输出
            reasoning=reasoning_value,
            caching=BotSettings.DECISION_CACHE,
            max_tokens=BotSettings.DECISION_MAX_TOKENS,
            top_p=BotSettings.DECISION_TOP_P,
            top_k=BotSettings.DECISION_TOP_K,
            stop=BotSettings.DECISION_STOP,
        ).export
        
        try:
            # 调用AI接口
            response = self.client.responses.create(**apimodel)
            
            # 提取回复内容
            reply_text = self._extract_reply_text(response).strip().upper()
            
            # 返回判断结果
            return reply_text == "YES"
        except Exception as e:
            logger.error(f"AI回复判断失败: {e}")
            # 失败时默认不回复
            return False
    
    async def generate_summary(self, messages: List[Message]) -> str:
        """生成聊天信息摘要"""
        # 如果摘要系统未启用，返回空字符串
        if not BotSettings.SUMMARY_ENABLED:
            logger.debug("摘要系统未启用，跳过摘要生成")
            return ""
        
        logger.info(f"开始生成摘要，输入消息数量: {len(messages)}")
        
        # 记录输入消息内容
        logger.debug("输入摘要的消息内容:")
        for i, msg in enumerate(messages, 1):
            logger.debug(f"  {i}. {msg.content.msg[:50]}...")
        
        # 构建摘要提示词
        summary_prompt = Message(
            content=Content("你是一个智能对话助手，需要对以下聊天记录进行摘要。请用简洁明了的语言概括聊天的主要内容和关键信息，确保可以分清不同用户的发言，不要添加任何主观评论或解释。"),
            role=ROLE_TYPE.SYSTEM
        )
        
        # 构建请求消息列表
        prompt_messages = [summary_prompt] + messages
        
        # 构建API请求
        apimodel = ApiModel(
            model=BotSettings.SUMMARY_MODEL,  # 使用配置的模型生成摘要
            messages=prompt_messages,
            thinking=ABILITY.DISABLED,
            temperature=BotSettings.SUMMARY_TEMPERATURE,  # 使用配置的温度
            max_tokens=BotSettings.DECISION_MAX_TOKENS,  # 摘要不需要太长，使用决策模型的max_tokens
            top_p=BotSettings.DECISION_TOP_P,
            top_k=BotSettings.DECISION_TOP_K,
        ).export
        
        try:
            # 调用AI接口
            response = self.client.responses.create(**apimodel)
            
            # 提取回复内容
            summary = self._extract_reply_text(response).strip()
            
            logger.info(f"摘要生成完成，摘要长度: {len(summary)}")
            logger.debug(f"生成的摘要: {summary}")
            
            return summary
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            traceback.print_exc()
            return ""
    
    async def get_image_response(
        self,
        image_url: str,
        text_content: str = "",
        user_info: dict = None
    ) -> AIResponse:
        """获取图片解读的AI响应"""
        try:
            user_question = "如果你认为这是一个表情包图片，请解读，并强调其表达的情绪或者状态，不要超过30字；若只是普通图片，请直接解读，不要超过100字"
            
            # 直接调用API，使用图片解读模型
            response = self.client.responses.create(
                model=BotSettings.IMAGE_MODEL,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_image",
                                "image_url": image_url
                            },
                            {
                                "type": "input_text",
                                "text": user_question
                            },
                        ],
                    }
                ]
            )
            
            # 提取AI回复
            reply_text = self._extract_reply_text(response)
            
            if not reply_text:
                raise ValueError("无法提取AI回复内容")
            
            return AIResponse(
                content=reply_text,
                response_id=getattr(response, 'id', None)
            )
        except Exception as e:
            logger.error(f"图片解读失败: {e}")
            traceback.print_exc()
            return AIResponse(content="抱歉，我无法解读这张图片，请稍后再试")
    
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
            
            # 尝试直接从响应中提取文本（不同AI服务可能有不同的响应格式）
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            
            # 尝试从响应的其他属性中提取
            if hasattr(response, 'choices') and response.choices:
                for choice in response.choices:
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        return choice.message.content.strip()
                            
        except Exception as e:
            logger.error(f"提取回复失败: {e}")
        
        return "[错误] 无法解析AI回复"
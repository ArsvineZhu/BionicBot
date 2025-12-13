#! /usr/bin/env python3
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import asyncio
from volcenginesdkarkruntime import Ark
from ncatbot.core import BotClient, GroupMessageEvent, PrivateMessageEvent
from ncatbot.core.event.message_segment import MessageArray, Text, Image, PlainText
from ncatbot.utils import get_log

# 初始化日志
logger = get_log("PicResponseExample")

class PicResponseBot:
    """图片回复机器人示例，用于处理图片消息并通过AI解读"""
    
    def __init__(self):
        # 初始化机器人客户端
        self.bot = BotClient()
        
        # 初始化Ark客户端 - 使用环境变量API密钥
        self.ark_client = self._init_ark_client()
        
        # 注册事件处理器
        self._register_handlers()
        logger.info("图片回复机器人初始化完成")
    
    def _init_ark_client(self) -> Ark:
        """初始化Ark客户端 - 使用环境变量API密钥"""
        api_key = input('KEY:')
        
        if not api_key:
            logger.error("ARK_API_KEY环境变量未设置")
            raise ValueError("ARK_API_KEY环境变量未设置")
        
        # 初始化Ark客户端 - 使用用户提供的配置
        return Ark(
            base_url='https://ark.cn-beijing.volces.com/api/v3',
            api_key=api_key,
        )
    
    def _register_handlers(self):
        """注册事件处理器"""
        
        @self.bot.on_group_message()
        async def handle_group_message(event: GroupMessageEvent):
            """处理群聊消息"""
            await self._handle_message(event, is_group=True)
        
        @self.bot.on_private_message()
        async def handle_private_message(event: PrivateMessageEvent):
            """处理私聊消息"""
            await self._handle_message(event, is_group=False)
    
    async def _handle_message(self, event, is_group: bool):
        """统一处理消息"""
        # 获取消息类型和发送者信息
        message_type = "群聊" if is_group else "私聊"
        if is_group:
            sender_info = f"[{event.sender.nickname}({event.sender.user_id})]"
            group_info = f"[{event.group_id}]"
        else:
            sender_info = f"[{event.sender.user_id}]"
            group_info = ""
        
        logger.info(f"[{message_type}] {group_info} {sender_info} 发送了消息")
        
        # 检查消息中是否包含图片
        images = []
        text_content = ""
        
        # 遍历消息段
        if isinstance(event.message, MessageArray):
            for segment in event.message:
                if isinstance(segment, Text) or isinstance(segment, PlainText):
                    text_content += segment.text
                elif isinstance(segment, Image):
                    # 获取图片信息
                    image_info = {
                        "file": segment.file,
                        "url": segment.url if hasattr(segment, 'url') else "无URL",
                        "type": segment.type if hasattr(segment, 'type') else "未知类型"
                    }
                    images.append(image_info)
        
        # 如果包含图片，处理图片
        if images:
            logger.info(f"[{message_type}] 收到 {len(images)} 张图片")
            
            # 处理每张图片
            for i, img in enumerate(images, 1):
                if img["url"] != "无URL":
                    logger.info(f"[{message_type}] 正在解读图片 {i}: {img['url']}")
                    
                    # 构建用户提问
                    if text_content:
                        user_question = f"请详细解读这张图片，并考虑用户的描述：{text_content}"
                    else:
                        user_question = "请解读这张图片，不要超过50字，强调图片表达的情绪或者状态"
                    
                    # 直接调用用户提供的API调用代码
                    try:
                        # 使用用户指定的API调用方式
                        response = self.ark_client.responses.create(
                            model="doubao-seed-1-6-flash-250828",
                            input=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_image",
                                            "image_url": img["url"]
                                        },
                                        {
                                            "type": "input_text",
                                            "text": user_question
                                        },
                                    ],
                                }
                            ]
                        )
                        
                        # 调试：打印响应结构
                        logger.info(f"[{message_type}] 响应结构: {response.__dict__}")
                        
                        # 提取AI回复 - 修复ResponseReasoningItem错误
                        reply_text = ""
                        if hasattr(response, 'output') and response.output:
                            # 遍历output列表，寻找包含content的项
                            for item in response.output:
                                if hasattr(item, 'content') and item.content:
                                    # 提取文本内容
                                    for content_item in item.content:
                                        if hasattr(content_item, 'text'):
                                            reply_text += content_item.text
                                    break
                                elif hasattr(item, 'text'):
                                    # 直接提取文本
                                    reply_text += item.text
                                    break
                        
                        if not reply_text:
                            # 尝试另一种响应提取方式
                            if hasattr(response, 'choices') and response.choices:
                                for choice in response.choices:
                                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                                        reply_text = choice.message.content
                                        break
                        
                        if not reply_text:
                            raise ValueError("无法提取AI回复内容")
                        
                        # 回复AI解读结果
                        response_text = f"图片 {i} 解读结果：\n{reply_text}"
                        
                        if is_group:
                            await self.bot.api.send_group_msg(
                                group_id=event.group_id,
                                message=MessageArray([Text(response_text)]).to_list()
                            )
                        else:
                            await self.bot.api.send_private_msg(
                                user_id=event.sender.user_id,
                                message=MessageArray([Text(response_text)]).to_list()
                            )
                            
                        logger.info(f"[{message_type}] 图片 {i} 解读完成")
                    except Exception as e:
                        logger.error(f"[{message_type}] 图片解读失败: {e}")
                        # 添加详细的调试信息
                        import traceback
                        logger.error(f"[{message_type}] 详细错误: {traceback.format_exc()}")
                        error_msg = f"抱歉，图片 {i} 解读失败：{str(e)}"
                        
                        if is_group:
                            await self.bot.api.send_group_msg(
                                group_id=event.group_id,
                                message=MessageArray([Text(error_msg)]).to_list()
                            )
                        else:
                            await self.bot.api.send_private_msg(
                                user_id=event.sender.user_id,
                                message=MessageArray([Text(error_msg)]).to_list()
                            )
                else:
                    logger.warning(f"[{message_type}] 图片 {i} 没有URL，无法解读")
                    no_url_msg = f"抱歉，图片 {i} 没有URL，无法解读"
                    
                    if is_group:
                        await self.bot.api.send_group_msg(
                            group_id=event.group_id,
                            message=MessageArray([Text(no_url_msg)]).to_list()
                        )
                    else:
                        await self.bot.api.send_private_msg(
                            user_id=event.sender.user_id,
                            message=MessageArray([Text(no_url_msg)]).to_list()
                        )
    
    def run(self):
        """启动机器人"""
        logger.info("正在启动图片回复机器人...")
        logger.info("支持的功能: 接收图片消息，提取URL，通过AI解读并回复")
        self.bot.run_frontend()

if __name__ == "__main__":
    # 创建并运行机器人
    bot = PicResponseBot()
    bot.run()

#! /usr/bin/env python3
import asyncio
from ncatbot.core import BotClient, GroupMessageEvent, PrivateMessageEvent
from ncatbot.core.event.message_segment import (
    MessageArray, Text, Image, At, AtAll, Face, 
    Record, Video, File, Reply, Location, PlainText,
    Anonymous, Contact, Dice, Forward, Json, Markdown,
    Music, Node, Poke, Rps, Sentence, Shake, Share, XML
)
from ncatbot.utils import get_log

# 初始化日志
logger = get_log("AdvancedMsgResponseExample")

class AdvancedMessageBot:
    """高级消息处理机器人示例，用于处理各种非文本消息"""
    
    def __init__(self):
        # 初始化机器人客户端
        self.bot = BotClient()
        # 注册事件处理器
        self._register_handlers()
        logger.info("高级消息处理机器人初始化完成")
    
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
        
        # 统计不同类型的消息段
        segment_stats = {
            "text": 0,
            "image": 0,
            "at": 0,
            "face": 0,
            "record": 0,
            "video": 0,
            "file": 0,
            "reply": 0,
            "location": 0,
            "contact": 0,
            "dice": 0,
            "forward": 0,
            "json": 0,
            "markdown": 0,
            "music": 0,
            "node": 0,
            "poke": 0,
            "rps": 0,
            "sentence": 0,
            "shake": 0,
            "share": 0,
            "xml": 0,
            "anonymous": 0,
            "other": 0
        }
        
        # 存储消息内容
        text_content = ""
        images = []
        at_users = []
        pokes = []  # 存储戳一戳动作
        
        # 遍历消息段
        if isinstance(event.message, MessageArray):
            for segment in event.message:
                if isinstance(segment, Text) or isinstance(segment, PlainText):
                    segment_stats["text"] += 1
                    text_content += segment.text
                    logger.info(f"[{message_type}] 文本: {segment.text}")
                
                elif isinstance(segment, Image):
                    segment_stats["image"] += 1
                    image_info = self._get_image_info(segment)
                    images.append(image_info)
                    logger.info(f"[{message_type}] 图片: {image_info}")
                
                elif isinstance(segment, At):
                    segment_stats["at"] += 1
                    at_info = {
                        "qq": segment.qq,
                        "name": segment.name if hasattr(segment, 'name') else "未知"
                    }
                    at_users.append(at_info)
                    logger.info(f"[{message_type}] @用户: {at_info}")
                
                elif isinstance(segment, AtAll):
                    segment_stats["at"] += 1
                    logger.info(f"[{message_type}] @全体成员")
                
                elif isinstance(segment, Face):
                    segment_stats["face"] += 1
                    face_info = {
                        "id": segment.id,
                        "type": segment.type if hasattr(segment, 'type') else "未知"
                    }
                    logger.info(f"[{message_type}] 表情: {face_info}")
                
                elif isinstance(segment, Record):
                    segment_stats["record"] += 1
                    record_info = {
                        "file": segment.file,
                        "url": segment.url if hasattr(segment, 'url') else "无URL"
                    }
                    logger.info(f"[{message_type}] 语音: {record_info}")
                
                elif isinstance(segment, Video):
                    segment_stats["video"] += 1
                    video_info = {
                        "file": segment.file,
                        "url": segment.url if hasattr(segment, 'url') else "无URL"
                    }
                    logger.info(f"[{message_type}] 视频: {video_info}")
                
                elif isinstance(segment, File):
                    segment_stats["file"] += 1
                    file_info = {
                        "file": segment.file,
                        "name": segment.name,
                        "size": segment.size,
                        "url": segment.url if hasattr(segment, 'url') else "无URL"
                    }
                    logger.info(f"[{message_type}] 文件: {file_info}")
                
                elif isinstance(segment, Reply):
                    segment_stats["reply"] += 1
                    reply_info = {
                        "message_id": segment.message_id,
                        "user_id": segment.user_id if hasattr(segment, 'user_id') else "未知"
                    }
                    logger.info(f"[{message_type}] 回复: {reply_info}")
                
                elif isinstance(segment, Location):
                    segment_stats["location"] += 1
                    location_info = {
                        "lat": segment.lat,
                        "lon": segment.lon,
                        "title": segment.title,
                        "content": segment.content
                    }
                    logger.info(f"[{message_type}] 位置: {location_info}")
                
                elif isinstance(segment, Anonymous):
                    segment_stats["anonymous"] += 1
                    anonymous_info = {
                        "flag": segment.flag if hasattr(segment, 'flag') else "未知"
                    }
                    logger.info(f"[{message_type}] 匿名消息: {anonymous_info}")
                
                elif isinstance(segment, Contact):
                    segment_stats["contact"] += 1
                    contact_info = {
                        "type": segment.type if hasattr(segment, 'type') else "未知",
                        "id": segment.id if hasattr(segment, 'id') else "未知"
                    }
                    logger.info(f"[{message_type}] 联系人: {contact_info}")
                
                elif isinstance(segment, Dice):
                    segment_stats["dice"] += 1
                    dice_info = {
                        "value": segment.value if hasattr(segment, 'value') else "未知"
                    }
                    logger.info(f"[{message_type}] 骰子: {dice_info}")
                
                elif isinstance(segment, Forward):
                    segment_stats["forward"] += 1
                    forward_info = {
                        "id": segment.id if hasattr(segment, 'id') else "未知"
                    }
                    logger.info(f"[{message_type}] 转发消息: {forward_info}")
                
                elif isinstance(segment, Json):
                    segment_stats["json"] += 1
                    json_info = {
                        "data": segment.data if hasattr(segment, 'data') else "未知"
                    }
                    logger.info(f"[{message_type}] JSON消息: {json_info}")
                
                elif isinstance(segment, Markdown):
                    segment_stats["markdown"] += 1
                    markdown_info = {
                        "content": segment.content if hasattr(segment, 'content') else "未知"
                    }
                    logger.info(f"[{message_type}] Markdown消息: {markdown_info}")
                
                elif isinstance(segment, Music):
                    segment_stats["music"] += 1
                    music_info = {
                        "type": segment.type if hasattr(segment, 'type') else "未知",
                        "id": segment.id if hasattr(segment, 'id') else "未知"
                    }
                    logger.info(f"[{message_type}] 音乐: {music_info}")
                
                elif isinstance(segment, Node):
                    segment_stats["node"] += 1
                    node_info = {
                        "id": segment.id if hasattr(segment, 'id') else "未知"
                    }
                    logger.info(f"[{message_type}] 消息节点: {node_info}")
                
                elif isinstance(segment, Poke):
                    segment_stats["poke"] += 1
                    
                    # 获取poke动作的详细信息
                    poke_type = segment.type if hasattr(segment, 'type') else "未知"
                    poke_id = segment.id if hasattr(segment, 'id') else "未知"
                    
                    # 定义常见poke动作的友好描述
                    poke_actions = {
                        "1": "戳了戳你",
                        "2": "摸了摸你",
                        "3": "蹭了蹭你",
                        "4": "抱了抱你",
                        "5": "亲了亲你",
                        "6": "踢了踢你",
                        "7": "踹了你一脚",
                        "8": "拍了拍你",
                        "9": "捏了捏你",
                        "10": "挠了你痒痒",
                        "11": "电了你一下",
                        "12": "咬了你一口",
                        "13": "砸了你一锤",
                        "14": "给了你一拳",
                        "15": "敲了敲你",
                        "16": "戳了戳你的小脸蛋",
                        "17": "摸了摸你的头",
                        "18": "弹了你一下",
                        "19": "揉了你一把",
                        "20": "戳了戳你的腰",
                        "21": "扯了扯你的耳朵",
                        "22": "摸了摸你的肚子",
                        "23": "戳了戳你的后背",
                        "24": "拍了拍你的肩膀",
                        "25": "捏了捏你的脸",
                        "26": "摸了摸你的手",
                        "27": "戳了戳你的大腿",
                        "28": "拍了拍你的屁股",
                        "29": "踢了踢你的小腿",
                        "30": "戳了戳你的脚丫子"
                    }
                    
                    # 获取友好描述
                    action_desc = poke_actions.get(str(poke_id), f"做了个动作(ID:{poke_id})")
                    sender_name = event.sender.nickname if is_group else str(event.sender.user_id)
                    
                    poke_info = {
                        "type": poke_type,
                        "id": poke_id,
                        "action": action_desc,
                        "sender": sender_name
                    }
                    
                    logger.info(f"[{message_type}] {sender_name} {action_desc}")
                    
                    # 特殊处理：记录poke动作
                    if "poke" not in locals():
                        pokes = []
                    pokes.append(poke_info)
                    
                    # 被poke时给出反应
                    if is_group:
                        # 群聊中被poke，回复一条消息
                        await self.bot.api.send_group_msg(
                            group_id=event.group_id,
                            message=MessageArray([Text(f"{sender_name} 戳了我！我也想戳戳你～")]).to_list()
                        )
                    else:
                        # 私聊中被poke，发送回戳动作
                        await self.bot.api.send_private_msg(
                            user_id=event.sender.user_id,
                            message=MessageArray([Text(f"你戳了我！我也戳戳你～")]).to_list()
                        )
                
                elif isinstance(segment, Rps):
                    segment_stats["rps"] += 1
                    rps_info = {
                        "value": segment.value if hasattr(segment, 'value') else "未知"
                    }
                    logger.info(f"[{message_type}] 猜拳: {rps_info}")
                
                elif isinstance(segment, Sentence):
                    segment_stats["sentence"] += 1
                    sentence_info = {
                        "text": segment.text if hasattr(segment, 'text') else "未知"
                    }
                    logger.info(f"[{message_type}] 短句: {sentence_info}")
                
                elif isinstance(segment, Shake):
                    segment_stats["shake"] += 1
                    logger.info(f"[{message_type}] 抖一抖")
                
                elif isinstance(segment, Share):
                    segment_stats["share"] += 1
                    share_info = {
                        "url": segment.url if hasattr(segment, 'url') else "未知",
                        "title": segment.title if hasattr(segment, 'title') else "未知",
                        "content": segment.content if hasattr(segment, 'content') else "未知",
                        "image": segment.image if hasattr(segment, 'image') else "未知"
                    }
                    logger.info(f"[{message_type}] 分享: {share_info}")
                
                elif isinstance(segment, XML):
                    segment_stats["xml"] += 1
                    xml_info = {
                        "data": segment.data if hasattr(segment, 'data') else "未知"
                    }
                    logger.info(f"[{message_type}] XML消息: {xml_info}")
                
                else:
                    logger.info(f"[{message_type}] 其他类型: {type(segment).__name__}")
                    segment_stats["other"] += 1
        
        # 构建回复消息
        response = await self._build_response(
            message_type, segment_stats, text_content, 
            images, at_users, pokes, is_group, event
        )
        
        # 发送回复
        if response:
            if is_group:
                await self.bot.api.send_group_msg(
                    group_id=event.group_id,
                    message=response.to_list()
                )
            else:
                await self.bot.api.send_private_msg(
                    user_id=event.sender.user_id,
                    message=response.to_list()
                )
    
    def _get_image_info(self, image_segment: Image) -> dict:
        """获取图片详细信息"""
        # 获取图片格式（从文件名或URL推断）
        file_name = image_segment.file if hasattr(image_segment, 'file') else ""
        image_format = file_name.split('.')[-1].lower() if '.' in file_name else "未知格式"
        
        # 构建图片详细信息
        image_info = {
            "file": image_segment.file,
            "type": image_segment.type if hasattr(image_segment, 'type') else "未知",
            "url": image_segment.url if hasattr(image_segment, 'url') else "无URL",
            "sub_type": image_segment.sub_type if hasattr(image_segment, 'sub_type') else "未知子类型",
            "id": image_segment.id if hasattr(image_segment, 'id') else "无ID",
            "cache": image_segment.cache if hasattr(image_segment, 'cache') else "未知缓存状态",
            "format": image_format,
            "size": image_segment.size if hasattr(image_segment, 'size') else "未知大小",
            "width": image_segment.width if hasattr(image_segment, 'width') else "未知宽度",
            "height": image_segment.height if hasattr(image_segment, 'height') else "未知高度"
        }
        
        # 简单的图片类型识别
        if image_format in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
            image_info["category"] = "常规图片"
        elif image_format in ['svg']:
            image_info["category"] = "矢量图"
        elif image_format in ['mp4', 'avi', 'mov']:
            image_info["category"] = "视频文件"
        else:
            image_info["category"] = "其他类型"
        
        return image_info
    
    async def _build_response(self, message_type: str, stats: dict, 
                            text_content: str, images: list, at_users: list, 
                            pokes: list, is_group: bool, event) -> MessageArray:
        """构建回复消息"""
        
        # 构建回复文本
        response_parts = []
        
        # 1. 基本统计信息
        total_segments = sum(stats.values())
        response_parts.append(f"我收到了你的消息！共 {total_segments} 个消息段。\n")
        
        # 2. 文本内容（如果有）
        if text_content:
            response_parts.append(f"文本内容: {text_content}\n")
        
        # 3. 图片信息（增强版）
        if images:
            response_parts.append(f"图片: 共 {stats['image']} 张\n")
            for i, img in enumerate(images, 1):
                # 增强图片信息展示
                img_desc = f"  图片 {i}: \n"
                img_desc += f"    文件ID: {img['file']}\n"
                img_desc += f"    类型: {img['type']}\n"
                img_desc += f"    格式: {img['format']}\n"
                img_desc += f"    类别: {img['category']}\n"
                img_desc += f"    子类型: {img['sub_type']}\n"
                img_desc += f"    尺寸: {img['width']}x{img['height']}\n"
                img_desc += f"    缓存状态: {img['cache']}\n"
                if img['url'] != "无URL":
                    img_desc += f"    URL: {img['url'][:50]}...\n"
                response_parts.append(img_desc)
        
        # 4. @用户信息（如果有）
        if at_users:
            response_parts.append(f"@用户: 共 {stats['at']} 个\n")
            for at in at_users:
                response_parts.append(f"  - @{at['name']}({at['qq']})\n")
        
        # 5. 戳一戳信息（增强版）
        if pokes:
            response_parts.append(f"戳一戳: 共 {stats['poke']} 个动作\n")
            for i, poke in enumerate(pokes, 1):
                response_parts.append(f"  {i}. {poke['sender']} {poke['action']}\n")
        
        # 6. 其他类型统计
        other_types = []
        if stats['face'] > 0:
            other_types.append(f"表情({stats['face']})")
        if stats['record'] > 0:
            other_types.append(f"语音({stats['record']})")
        if stats['video'] > 0:
            other_types.append(f"视频({stats['video']})")
        if stats['file'] > 0:
            other_types.append(f"文件({stats['file']})")
        if stats['reply'] > 0:
            other_types.append(f"回复({stats['reply']})")
        if stats['location'] > 0:
            other_types.append(f"位置({stats['location']})")
        if stats['contact'] > 0:
            other_types.append(f"联系人({stats['contact']})")
        if stats['dice'] > 0:
            other_types.append(f"骰子({stats['dice']})")
        if stats['forward'] > 0:
            other_types.append(f"转发({stats['forward']})")
        if stats['json'] > 0:
            other_types.append(f"JSON({stats['json']})")
        if stats['markdown'] > 0:
            other_types.append(f"Markdown({stats['markdown']})")
        if stats['music'] > 0:
            other_types.append(f"音乐({stats['music']})")
        if stats['node'] > 0:
            other_types.append(f"消息节点({stats['node']})")
        if stats['rps'] > 0:
            other_types.append(f"猜拳({stats['rps']})")
        if stats['sentence'] > 0:
            other_types.append(f"短句({stats['sentence']})")
        if stats['shake'] > 0:
            other_types.append(f"抖一抖({stats['shake']})")
        if stats['share'] > 0:
            other_types.append(f"分享({stats['share']})")
        if stats['xml'] > 0:
            other_types.append(f"XML({stats['xml']})")
        if stats['anonymous'] > 0:
            other_types.append(f"匿名消息({stats['anonymous']})")
        if stats['other'] > 0:
            other_types.append(f"其他({stats['other']})")
        
        if other_types:
            response_parts.append(f"其他内容: {', '.join(other_types)}\n")
        
        # 7. 总结
        response_parts.append("\n这是一个高级消息处理示例，展示了如何处理各种类型的消息段。")
        
        # 构建回复消息
        response_text = "".join(response_parts)
        return MessageArray([Text(response_text)])
    
    def run(self):
        """启动机器人"""
        logger.info("正在启动高级消息处理机器人...")
        logger.info("支持的消息类型: 文本、图片、@用户、@全体、表情、语音、视频、文件、回复、位置、匿名消息、联系人、骰子、转发消息、JSON、Markdown、音乐、消息节点、戳一戳、猜拳、短句、抖一抖、分享、XML")
        self.bot.run()

if __name__ == "__main__":
    # 创建并运行机器人
    bot = AdvancedMessageBot()
    bot.run()

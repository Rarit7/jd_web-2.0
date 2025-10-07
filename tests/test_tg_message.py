#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import pprint
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jd import app
from jd.services.spider.tg import TgService
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_user_info import TgGroupUserInfo

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_subsection(title):
    """打印子节标题"""
    print(f"\n--- {title} ---")

def safe_getattr(obj, attr, default='N/A'):
    """安全获取属性"""
    try:
        return getattr(obj, attr, default)
    except Exception:
        return f"<Error accessing {attr}>"

def print_all_attributes(obj, title="对象属性"):
    """打印对象的所有属性"""
    print(f"\n{title}:")
    for attr_name in sorted(dir(obj)):
        if not attr_name.startswith('_'):
            try:
                attr_value = getattr(obj, attr_name)
                if not callable(attr_value):
                    # 限制输出长度
                    str_value = str(attr_value)
                    if len(str_value) > 200:
                        str_value = str_value[:200] + "..."
                    print(f"  {attr_name}: {str_value}")
            except Exception as e:
                print(f"  {attr_name}: <Error: {e}>")

async def analyze_message_content(tg_service, chat_id, message_id):
    """分析消息内容的完整信息"""
    try:
        # 从Telegram API获取消息
        print_subsection("从Telegram API获取消息")
        message = await tg_service.client.get_messages(int(chat_id), ids=[int(message_id)])

        if not message or len(message) == 0:
            print(f"未找到消息 {message_id}")
            return None

        msg = message[0]
        print(f"消息类型: {type(msg)}")

        # 基本消息信息
        print_subsection("基本消息属性")
        basic_attrs = ['id', 'date', 'message', 'from_id', 'peer_id', 'reply_to', 'views', 'forwards', 'edit_date']
        for attr in basic_attrs:
            print(f"  {attr}: {safe_getattr(msg, attr)}")

        # 媒体信息
        if hasattr(msg, 'media') and msg.media:
            print_subsection("媒体信息")
            print(f"  媒体类型: {type(msg.media)}")
            print_all_attributes(msg.media, "媒体对象属性")

            # 详细分析不同媒体类型
            from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

            if isinstance(msg.media, MessageMediaPhoto):
                print_subsection("照片详细信息")
                if hasattr(msg.media, 'photo'):
                    photo = msg.media.photo
                    print(f"    照片ID: {safe_getattr(photo, 'id')}")
                    print(f"    访问哈希: {safe_getattr(photo, 'access_hash')}")
                    print(f"    文件引用: {safe_getattr(photo, 'file_reference')}")
                    print(f"    日期: {safe_getattr(photo, 'date')}")
                    print(f"    尺寸: {safe_getattr(photo, 'sizes')}")
                    if hasattr(photo, 'sizes'):
                        for i, size in enumerate(photo.sizes):
                            print(f"      尺寸 {i}: {type(size)} - {safe_getattr(size, 'w')}x{safe_getattr(size, 'h')}")

            elif isinstance(msg.media, MessageMediaDocument):
                print_subsection("文档详细信息")
                if hasattr(msg.media, 'document'):
                    doc = msg.media.document
                    print(f"    文档ID: {safe_getattr(doc, 'id')}")
                    print(f"    访问哈希: {safe_getattr(doc, 'access_hash')}")
                    print(f"    文件引用: {safe_getattr(doc, 'file_reference')}")
                    print(f"    日期: {safe_getattr(doc, 'date')}")
                    print(f"    MIME类型: {safe_getattr(doc, 'mime_type')}")
                    print(f"    文件大小: {safe_getattr(doc, 'size')}")
                    print(f"    DC ID: {safe_getattr(doc, 'dc_id')}")

                    if hasattr(doc, 'attributes'):
                        print(f"    属性数量: {len(doc.attributes)}")
                        for i, attr in enumerate(doc.attributes):
                            print(f"      属性 {i}: {type(attr)}")
                            print_all_attributes(attr, f"        属性 {i} 详情")

        # 完整消息属性
        print_subsection("完整消息属性")
        print_all_attributes(msg, "消息对象所有属性")

        return msg

    except Exception as e:
        print(f"分析消息时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_comprehensive_message_analysis():
    """全面测试Telethon可获取的消息信息"""
    print_section("Telethon消息信息全面分析测试")

    # 初始化Flask应用
    app.ready()

    with app.app_context():
        # 初始化TG客户端
        tg_service = await TgService.init_tg(sessionname='111')

        if not tg_service:
            print("Failed to initialize Telegram service")
            return

        try:
            pavel_chat_id = "1006503122"  # Pavel Durov频道

            # 测试用例：不同类型的消息
            test_cases = [
                {
                    'type': '纯文本消息',
                    'chat_id': pavel_chat_id,
                    'message_id': '445'  # 纯文本消息
                },
                {
                    'type': '带图片的消息',
                    'chat_id': pavel_chat_id,
                    'message_id': '446'  # 带图片消息
                },
                {
                    'type': '带文档的消息',
                    'chat_id': pavel_chat_id,
                    'message_id': '431'  # 带文档消息
                }
            ]

            for case in test_cases:
                print_section(f"测试 {case['type']}")
                print(f"频道ID: {case['chat_id']}")
                print(f"消息ID: {case['message_id']}")

                # 先从数据库获取基本信息
                print_subsection("数据库中的消息记录")
                message_record = TgGroupChatHistory.query.filter_by(
                    chat_id=case['chat_id'],
                    message_id=case['message_id']
                ).first()

                if message_record:
                    print(f"  消息ID: {message_record.message_id}")
                    print(f"  用户ID: {message_record.user_id}")
                    print(f"  用户名: {message_record.username}")
                    print(f"  昵称: {message_record.nickname}")
                    print(f"  发布时间: {message_record.postal_time}")
                    print(f"  消息内容: {message_record.message[:100]}...")
                    print(f"  图片路径: {message_record.photo_path}")
                    print(f"  文档路径: {message_record.document_path}")
                    print(f"  文档扩展名: {message_record.document_ext}")
                    print(f"  回复消息ID: {message_record.reply_to_msg_id}")
                    print(f"  回复信息: {message_record.replies_info}")
                else:
                    print("  数据库中未找到消息记录")
                    continue

                # 从Telegram API获取完整信息
                await analyze_message_content(tg_service, case['chat_id'], case['message_id'])

                print("\n" + "─" * 80)

            # 额外测试：频道信息
            print_section("频道信息分析")
            try:
                channel_entity = await tg_service.client.get_entity(int(pavel_chat_id))
                print(f"频道实体类型: {type(channel_entity)}")
                print_all_attributes(channel_entity, "频道实体属性")

                # 获取完整频道信息
                from telethon.tl.functions.channels import GetFullChannelRequest
                full_channel = await tg_service.client(GetFullChannelRequest(channel_entity))
                print_subsection("完整频道信息")
                print(f"完整频道类型: {type(full_channel)}")
                if hasattr(full_channel, 'full_chat'):
                    print_all_attributes(full_channel.full_chat, "完整频道信息属性")

            except Exception as e:
                print(f"获取频道信息时出错: {e}")

        except Exception as e:
            print(f"测试过程中出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await tg_service.client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_comprehensive_message_analysis())
#!/usr/bin/env python3
"""
测试脚本：测试telegram_spider中的get_dialog_list方法
详细打印群组信息，包括dialog.entity和full_chat的信息
"""
import asyncio
import os
import sys
import json
from pprint import pprint
from datetime import datetime
from telethon.utils import get_peer_id

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jd.services.spider.tg import TgService
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest


def print_separator(title):
    """打印分隔线"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")


def safe_print_object(obj, name="Object"):
    """安全打印对象属性，避免循环引用"""
    print(f"\n--- {name} 详细信息 ---")
    
    # 基本属性
    basic_attrs = ['id', 'title', 'username', 'date', 'access_hash', 'participants_count']
    print("基本属性:")
    for attr in basic_attrs:
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            print(f"  {attr}: {value} (type: {type(value).__name__})")
    
    # 布尔属性
    bool_attrs = ['megagroup', 'broadcast', 'verified', 'restricted', 'democracy', 
                  'signatures', 'min', 'scam', 'fake', 'gigagroup', 'noforwards']
    print("\n布尔属性:")
    for attr in bool_attrs:
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            if value is not None:
                print(f"  {attr}: {value}")
    
    # 其他重要属性
    other_attrs = ['restriction_reason', 'admin_rights', 'banned_rights', 'default_banned_rights']
    print("\n其他属性:")
    for attr in other_attrs:
        if hasattr(obj, attr):
            value = getattr(obj, attr)
            if value is not None:
                print(f"  {attr}: {value}")
    
    # 打印对象类型
    print(f"\n对象类型: {type(obj).__name__}")
    print(f"对象模块: {type(obj).__module__}")


def safe_print_full_chat(full_chat, name="FullChat"):
    """安全打印full_chat信息"""
    print(f"\n--- {name} 详细信息 ---")
    
    if hasattr(full_chat, 'full_chat'):
        fc = full_chat.full_chat
        print("full_chat 属性:")
        fc_attrs = ['about', 'participants_count', 'admins_count', 'kicked_count', 
                   'banned_count', 'online_count', 'read_inbox_max_id', 'read_outbox_max_id',
                   'unread_count', 'chat_photo', 'notify_settings', 'exported_invite',
                   'bot_info', 'migrated_from_chat_id', 'migrated_from_max_id',
                   'pinned_msg_id', 'stickerset', 'available_min_id', 'folder_id']
        
        for attr in fc_attrs:
            if hasattr(fc, attr):
                value = getattr(fc, attr)
                if value is not None:
                    print(f"  {attr}: {value}")
    
    if hasattr(full_chat, 'chats') and full_chat.chats:
        print(f"\nchats 列表长度: {len(full_chat.chats)}")
        for i, chat in enumerate(full_chat.chats):
            print(f"\nchats[{i}] 信息:")
            safe_print_object(chat, f"Chat-{i}")
    
    if hasattr(full_chat, 'users') and full_chat.users:
        print(f"\nusers 列表长度: {len(full_chat.users)}")


async def test_get_dialog_list():
    """测试get_dialog_list方法"""
    print_separator("开始测试 get_dialog_list 方法")
    
    # 创建TelegramSpider实例
    session_name = 'default'
    spider = await TgService.init_tg(session_name)
    
    try:
        print(f"使用会话文件: {session_name}.session")
        print(f"当前工作目录: {os.getcwd()}")
        
        # 检查session文件是否存在
        
        # 获取自己的信息
        me = await spider.get_me()
        print(f"当前用户: {me.first_name} {me.last_name or ''} (@{me.username or 'N/A'})")
        print(f"用户ID: {me.id}")
        
        print_separator("开始获取对话列表")
        
        dialog_count = 0
        async for result in spider.get_dialog_list():
            dialog_count += 1
            
            print_separator(f"对话 #{dialog_count}")
            
            # 打印spider返回的结果
            print("=== Spider返回的结果 ===")
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
            
            # 获取原始dialog信息进行详细分析
            print("\n=== 原始Dialog详细分析 ===")
            
            # 重新获取dialog进行详细分析
            async for dialog in spider.client.iter_dialogs():
                if hasattr(dialog.entity, "title"):
                    chat = dialog.entity
                    
                    # 检查是否是当前处理的群组
                    if chat.id == result['data'].get('id'):
                        print(f"找到匹配的dialog: {chat.title} (ID: {chat.id})")
                        
                       
                        
                        # 打印entity详细信息
                        safe_print_object(chat, "Dialog.Entity")
                        
                        cid = get_peer_id(dialog.entity)
                        print(f'peer_id={cid}')
                                
                      
                        
                        break
            
            # 只处理前5个对话，避免输出太多
            if dialog_count >= 5:
                print(f"\n已处理前{dialog_count}个对话，停止测试...")
                break
        
        print_separator(f"测试完成，共处理 {dialog_count} 个对话")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if spider.client.is_connected():
            await spider.client.disconnect()
            print("✓ 已断开Telegram连接")


async def main():
    """主函数"""
    print("Telegram Dialog List 测试脚本")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await test_get_dialog_list()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"程序异常退出: {e}")
        import traceback
        traceback.print_exc()
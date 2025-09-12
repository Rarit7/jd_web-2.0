#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jd import app
from jd.services.spider.tg import TgService
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_user_info import TgGroupUserInfo

async def test_process_document():
    # 初始化Flask应用
    app.ready()
    
    with app.app_context():
        # 初始化TG客户端
        tg_service = await TgService.init_tg(sessionname='111')
        
        if not tg_service:
            print("Failed to initialize Telegram service")
            return
        
        chat_id = "1712944034"  # 使用字符串格式
        message_id = "2170148"
        
        try:
            # 1. 根据chat_id和message_id查询聊天记录
            message_record = TgGroupChatHistory.query.filter_by(
                chat_id=chat_id, 
                message_id=message_id
            ).first()
            
            if not message_record:
                print(f"Message not found for chat_id={chat_id}, message_id={message_id}")
                return
                
            print(f"Found message record:")
            print(f"  Message ID: {message_record.message_id}")
            print(f"  Chat ID: {message_record.chat_id}")
            print(f"  User ID: {message_record.user_id}")
            print(f"  Username: {message_record.username}")
            print(f"  Nickname: {message_record.nickname}")
            print(f"  Message: {message_record.message}")
            print(f"  Postal Time: {message_record.postal_time}")
            print("-" * 50)
            
            # 2. 根据user_id获取用户实体信息
            user_record = TgGroupUserInfo.query.filter_by(
                chat_id=chat_id,
                user_id=message_record.user_id
            ).first()
            
            if user_record:
                print(f"Found user record in database:")
                print("All user entity attributes from database:")
                # 打印用户实体的所有属性
                for attr_name in dir(user_record):
                    # 跳过私有属性和方法
                    if not attr_name.startswith('_'):
                        try:
                            attr_value = getattr(user_record, attr_name)
                            # 跳过方法
                            if not callable(attr_value):
                                print(f"  {attr_name}: {attr_value}")
                        except Exception as e:
                            print(f"  {attr_name}: <Error accessing attribute: {e}>")
                print("-" * 50)
            else:
                print(f"User record not found in database for user_id={message_record.user_id}")
            
            # 3. 尝试从Telegram API获取用户实体
            try:
                print("Attempting to get user entity from Telegram API...")
                user_entity = await tg_service.client.get_entity(int(message_record.user_id))
                
                print(f"Telegram user entity type: {type(user_entity)}")
                print("Key user information:")
                print(f"  id: {getattr(user_entity, 'id', 'N/A')}")
                print(f"  first_name: {getattr(user_entity, 'first_name', 'N/A')}")
                print(f"  last_name: {getattr(user_entity, 'last_name', 'N/A')}")
                print(f"  username: {getattr(user_entity, 'username', 'N/A')}")
                print(f"  phone: {getattr(user_entity, 'phone', 'N/A')}")
                print(f"  about: {getattr(user_entity, 'about', 'N/A')}")
                print(f"  bio: {getattr(user_entity, 'bio', 'N/A')}")
                print("-" * 30)
                
                # 4. 使用GetFullUserRequest获取完整用户信息
                print("Attempting to get full user information...")
                from telethon.tl.functions.users import GetFullUserRequest
                
                full_user = await tg_service.client(GetFullUserRequest(user_entity.id))
                print(f"Full user response type: {type(full_user)}")
                print("Full user information:")
                
                if hasattr(full_user, 'full_user'):
                    full_user_obj = full_user.full_user
                    print(f"  about: {getattr(full_user_obj, 'about', 'N/A')}")
                    print(f"  bio: {getattr(full_user_obj, 'bio', 'N/A')}")
                    print(f"  pinned_msg_id: {getattr(full_user_obj, 'pinned_msg_id', 'N/A')}")
                    print(f"  folder_id: {getattr(full_user_obj, 'folder_id', 'N/A')}")
                    print(f"  common_chats_count: {getattr(full_user_obj, 'common_chats_count', 'N/A')}")
                    
                    # 检查用户个人简介
                    user_about = getattr(full_user_obj, 'about', '')
                    if user_about:
                        print(f"  ✓ 找到用户个人简介: {user_about}")
                    else:
                        print("  ✗ 用户没有设置个人简介")
                        
                if hasattr(full_user, 'users') and full_user.users:
                    basic_user = full_user.users[0]
                    print(f"Basic user info from full request:")
                    print(f"  first_name: {getattr(basic_user, 'first_name', 'N/A')}")
                    print(f"  last_name: {getattr(basic_user, 'last_name', 'N/A')}")
                    print(f"  username: {getattr(basic_user, 'username', 'N/A')}")
                            
            except Exception as tg_error:
                print(f"Could not get user entity from Telegram API: {tg_error}")
                import traceback
                traceback.print_exc()
                        
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await tg_service.client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_process_document())
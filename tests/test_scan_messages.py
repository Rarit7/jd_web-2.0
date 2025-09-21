#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import asyncio
import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jd import app
from jd.services.spider.tg import TgService

async def test_scan_messages():
    """
    测试脚本：扫描指定chat_id的群组消息
    获取最近的300条消息，打印发言人名称、发言内容、时间戳，并记录总时间
    """
    # 记录开始时间
    start_time = time.time()
    
    # 初始化Flask应用
    app.ready()
    
    with app.app_context():
        # 初始化TG客户端
        print("正在初始化Telegram客户端...")
        tg_service = await TgService.init_tg(sessionname='111')
        
        if not tg_service:
            print("Failed to initialize Telegram service")
            return
        
        print("Telegram客户端初始化成功")
        
        # 指定要扫描的chat_id（可以修改为实际的群组ID）
        chat_id = "1712944034"  # 使用字符串格式
        message_limit = 300     # 获取最近300条消息
        
        try:
            # 获取聊天实体
            print(f"正在获取chat_id为 {chat_id} 的群组信息...")
            chat_entity = await tg_service.get_dialog(int(chat_id))
            
            if not chat_entity:
                print(f"无法获取chat_id为 {chat_id} 的群组信息，请检查ID是否正确")
                return
            
            print(f"成功获取群组信息: {chat_entity.title}")
            print(f"开始扫描最近 {message_limit} 条消息...")
            print("-" * 80)
            
            # 使用scan_message方法获取消息
            message_count = 0
            async for message_data in tg_service.scan_message(
                chat_entity, 
                limit=message_limit
            ):
                message_count += 1
                
                # 提取消息信息
                message_id = message_data.get('message_id', 'N/A')
                user_id = message_data.get('user_id', 'N/A')
                nick_name = message_data.get('nick_name', 'N/A')
                user_name = message_data.get('user_name', 'N/A')
                message_content = message_data.get('message', '')
                postal_time = message_data.get('postal_time')
                
                # 格式化时间戳
                if postal_time:
                    time_str = postal_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    time_str = "N/A"
                
                # 处理消息内容（截断过长的消息）
                if message_content:
                    if len(message_content) > 100:
                        display_message = message_content[:100] + "..."
                    else:
                        display_message = message_content
                else:
                    display_message = "[无文本内容]"
                
                # 发言人显示名称（优先显示昵称，其次用户名，最后用户ID）
                if nick_name and nick_name.strip():
                    sender_name = nick_name.strip()
                elif user_name and user_name.strip():
                    sender_name = f"@{user_name}"
                else:
                    sender_name = f"用户ID:{user_id}"
                
                # 打印消息信息
                print(f"#{message_count:03d} | 消息ID: {message_id}")
                print(f"      | 发言人: {sender_name}")
                print(f"      | 时间戳: {time_str}")
                print(f"      | 内容: {display_message}")
                print("-" * 40)
                
                # 每处理50条消息显示一下进度
                if message_count % 50 == 0:
                    elapsed_time = time.time() - start_time
                    print(f"[进度] 已处理 {message_count}/{message_limit} 条消息，耗时: {elapsed_time:.2f}秒")
                    print("-" * 40)
            
            # 计算总耗时
            total_time = time.time() - start_time
            
            print("=" * 80)
            print(f"扫描完成!")
            print(f"群组: {chat_entity.title} (ID: {chat_id})")
            print(f"总消息数: {message_count} 条")
            print(f"总耗时: {total_time:.2f} 秒")
            print(f"平均处理速度: {message_count/total_time:.2f} 条/秒")
            print("=" * 80)
                        
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 关闭客户端连接
            print("正在关闭Telegram客户端连接...")
            await tg_service.client.disconnect()
            print("连接已关闭")

if __name__ == "__main__":
    print("Telegram消息扫描测试脚本")
    print("=" * 50)
    asyncio.run(test_scan_messages())
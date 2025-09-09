#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jd import app
from jd.services.spider.tg import TgService
from jd.services.spider.tg_download import TelegramDownloadManager

async def test_process_document():
    # 初始化Flask应用
    app.ready()
    
    with app.app_context():
        # 初始化TG客户端
        tg_service = await TgService.init_tg(sessionname='123')
        
        if not tg_service:
            print("Failed to initialize Telegram service")
            return
        
        chat_id = 1498073945
        message_id = 2383
        
        try:
            # 获取消息实体
            message = await tg_service.client.get_messages(chat_id, ids=message_id)
            
            if message and message.document:
                print(f"Found document message: {message.document.attributes[1].file_name}")
                print(f"Document ID: {message.document.id}")
                print(f"MIME type: {message.document.mime_type}")
                
                # 创建TelegramDownloadManager实例
                downloader = TelegramDownloadManager(tg_service.client)
                
                # 设置下载根目录
                download_root = "/home/ec2-user/workspace/jd_web/static/document/"
                
                print(f"Using download root: {download_root}")
                
                # 调用process_document方法
                result = await downloader.process_document(
                    message=message,
                    document_path=download_root
                )
                
                print(f"Process document result: {result}")
                
                # 检查是否生成了缩略图
                if message.video and message.video.thumbs:
                    video_filename = message.video.attributes[1].file_name
                    name_without_ext = os.path.splitext(video_filename)[0]
                    thumb_filename = f'{name_without_ext}.jpg'
                    thumbs_path = os.path.join(download_root, 'thumbs')
                    thumb_filepath = os.path.join(thumbs_path, thumb_filename)
                    
                    print(f"Expected thumbnail path: {thumb_filepath}")
                    if os.path.exists(thumb_filepath):
                        print(f"✓ Thumbnail file exists: {thumb_filepath}")
                        file_size = os.path.getsize(thumb_filepath)
                        print(f"  File size: {file_size} bytes")
                    else:
                        print(f"✗ Thumbnail file not found: {thumb_filepath}")
                
            else:
                print("Message not found or not a document message")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await tg_service.client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_process_document())
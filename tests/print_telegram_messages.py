#!/usr/bin/env python3
"""
脚本名称: print_telegram_messages.py
功能描述: 打印Telegram的对话记录（消息历史）
作者: Claude Code
创建时间: 2025-09-22
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jd.services.spider.tg import TgService
from jd import app
from telethon.tl.types import Channel, Chat, User, MessageMediaPhoto, MessageMediaDocument

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def list_available_sessions():
    """
    列出所有可用的session文件
    """
    utils_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'utils')
    session_files = []

    if os.path.exists(utils_dir):
        for file in os.listdir(utils_dir):
            if file.endswith('-telegram.session'):
                session_name = file.replace('-telegram.session', '')
                file_path = os.path.join(utils_dir, file)
                file_size = os.path.getsize(file_path)
                modification_time = os.path.getmtime(file_path)
                session_files.append({
                    'name': session_name,
                    'size': file_size,
                    'mtime': modification_time,
                    'file': file
                })

    # 按修改时间排序，最新的在前
    session_files.sort(key=lambda x: x['mtime'], reverse=True)
    return session_files


async def get_dialog_list(raw_client):
    """
    获取对话列表供用户选择
    """
    dialogs = []
    dialog_data = await raw_client.get_dialogs(limit=None)

    for dialog in dialog_data:
        entity = dialog.entity
        dialog_info = {
            'entity': entity,
            'dialog': dialog,
            'id': entity.id,
            'unread_count': dialog.unread_count
        }

        if isinstance(entity, Channel):
            dialog_info.update({
                'title': getattr(entity, 'title', 'N/A'),
                'username': getattr(entity, 'username', None),
                'type': 'supergroup' if getattr(entity, 'megagroup', False) else 'channel'
            })
        elif isinstance(entity, Chat):
            dialog_info.update({
                'title': getattr(entity, 'title', 'N/A'),
                'username': None,
                'type': 'group'
            })
        elif isinstance(entity, User):
            full_name = f"{getattr(entity, 'first_name', '')} {getattr(entity, 'last_name', '')}".strip()
            dialog_info.update({
                'title': full_name if full_name else 'N/A',
                'username': getattr(entity, 'username', None),
                'type': 'user'
            })

        dialogs.append(dialog_info)

    return dialogs


def format_message_media(message):
    """
    格式化消息媒体信息
    """
    if not message.media:
        return ""

    media_info = []
    if isinstance(message.media, MessageMediaPhoto):
        media_info.append("[图片]")
    elif isinstance(message.media, MessageMediaDocument):
        if message.media.document:
            # 检查文档类型
            mime_type = getattr(message.media.document, 'mime_type', '')
            if 'video' in mime_type:
                media_info.append("[视频]")
            elif 'audio' in mime_type:
                media_info.append("[音频]")
            elif 'image' in mime_type:
                media_info.append("[图片文档]")
            else:
                # 尝试获取文件名
                for attr in message.media.document.attributes:
                    if hasattr(attr, 'file_name') and attr.file_name:
                        media_info.append(f"[文档: {attr.file_name}]")
                        break
                else:
                    media_info.append("[文档]")
    # elif isinstance(message.media, MessageMediaVideo):
    #     media_info.append("[视频]")
    else:
        media_info.append(f"[媒体: {type(message.media).__name__}]")

    return " ".join(media_info)


async def print_telegram_messages(session_name='default2', target_dialog=None, limit=50, days=None):
    """
    打印Telegram的对话记录

    Args:
        session_name (str): session文件名前缀
        target_dialog (str): 目标对话ID或用户名
        limit (int): 消息数量限制
        days (int): 获取最近几天的消息
    """
    try:
        with app.app_context():
            logger.info(f"开始读取Telegram对话记录，使用{session_name}-telegram.session文件")

            # 使用TgService的init_tg方法
            tg_client = await TgService.init_tg(sessionname=session_name)
            if tg_client is None:
                logger.error(f"Session '{session_name}' 初始化失败，可能未授权或已过期")
                return

            logger.info("Telegram客户端初始化成功，正在获取对话列表...")

            raw_client = tg_client.client

            # 获取对话列表
            dialogs = await get_dialog_list(raw_client)

            if not target_dialog:
                # 显示对话列表供用户选择
                print("\n" + "="*80)
                print(f"可用对话列表 (使用session: {session_name})")
                print("="*80)

                print(f"{'序号':<4} {'类型':<10} {'标题':<30} {'用户名':<20} {'未读':<6} {'ID'}")
                print("-" * 80)

                for i, dialog in enumerate(dialogs, 1):
                    title = dialog['title'][:28] + '..' if len(dialog['title']) > 30 else dialog['title']
                    username = f"@{dialog['username']}" if dialog['username'] else "无"
                    print(f"{i:<4} {dialog['type']:<10} {title:<30} {username:<20} {dialog['unread_count']:<6} {dialog['id']}")

                print("\n请选择要查看消息的对话:")
                print("1. 输入序号 (1-{})".format(len(dialogs)))
                print("2. 输入对话ID")
                print("3. 输入用户名 (包含@)")
                print("4. 输入 'quit' 退出")

                choice = input("\n请输入选择: ").strip()

                if choice.lower() == 'quit':
                    print("用户退出")
                    return

                # 解析用户选择
                selected_dialog = None

                if choice.isdigit():
                    # 按序号选择
                    idx = int(choice) - 1
                    if 0 <= idx < len(dialogs):
                        selected_dialog = dialogs[idx]
                    else:
                        print("无效的序号")
                        return
                elif choice.startswith('@'):
                    # 按用户名选择
                    username = choice[1:]
                    for dialog in dialogs:
                        if dialog['username'] == username:
                            selected_dialog = dialog
                            break
                    if not selected_dialog:
                        print(f"未找到用户名为 {choice} 的对话")
                        return
                elif choice.isdigit() or (choice.startswith('-') and choice[1:].isdigit()):
                    # 按ID选择
                    dialog_id = int(choice)
                    for dialog in dialogs:
                        if dialog['id'] == dialog_id:
                            selected_dialog = dialog
                            break
                    if not selected_dialog:
                        print(f"未找到ID为 {choice} 的对话")
                        return
                else:
                    print("无效的选择格式")
                    return

                target_entity = selected_dialog['entity']
                dialog_title = selected_dialog['title']
                dialog_type = selected_dialog['type']

            else:
                # 直接使用指定的对话
                target_entity = None
                if target_dialog.startswith('@'):
                    # 用户名
                    username = target_dialog[1:]
                    for dialog in dialogs:
                        if dialog['username'] == username:
                            target_entity = dialog['entity']
                            dialog_title = dialog['title']
                            dialog_type = dialog['type']
                            break
                elif target_dialog.isdigit() or (target_dialog.startswith('-') and target_dialog[1:].isdigit()):
                    # ID
                    dialog_id = int(target_dialog)
                    for dialog in dialogs:
                        if dialog['id'] == dialog_id:
                            target_entity = dialog['entity']
                            dialog_title = dialog['title']
                            dialog_type = dialog['type']
                            break

                if not target_entity:
                    print(f"未找到指定的对话: {target_dialog}")
                    return

            # 设置时间过滤
            offset_date = None
            if days:
                offset_date = datetime.now() - timedelta(days=days)

            print(f"\n" + "="*80)
            print(f"对话记录: {dialog_title} ({dialog_type})")
            if days:
                print(f"时间范围: 最近 {days} 天")
            print(f"消息数量: 最多 {limit} 条")
            print("="*80)

            # 获取消息
            messages = await raw_client.get_messages(
                target_entity,
                limit=limit,
                offset_date=offset_date
            )

            if not messages:
                print("未找到任何消息")
                return

            # 按时间正序排列（最早的在前）
            messages.reverse()

            print(f"\n找到 {len(messages)} 条消息:\n")

            message_data = []
            for i, message in enumerate(messages, 1):
                # 获取发送者信息
                sender_name = "未知发送者"
                sender_id = None

                if message.sender:
                    sender_id = message.sender_id
                    if isinstance(message.sender, User):
                        first_name = getattr(message.sender, 'first_name', '')
                        last_name = getattr(message.sender, 'last_name', '')
                        username = getattr(message.sender, 'username', None)

                        sender_name = f"{first_name} {last_name}".strip()
                        if username:
                            sender_name += f" (@{username})"
                        if not sender_name.strip():
                            sender_name = f"用户_{sender_id}"
                    else:
                        sender_name = f"发送者_{sender_id}"

                # 格式化时间
                msg_time = message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else "未知时间"

                # 获取消息内容
                msg_text = message.text or ""

                # 获取媒体信息
                media_info = format_message_media(message)

                # 获取回复信息
                reply_info = ""
                if message.reply_to and hasattr(message.reply_to, 'reply_to_msg_id'):
                    reply_info = f" [回复消息ID: {message.reply_to.reply_to_msg_id}]"

                # 获取转发信息
                forward_info = ""
                if message.forward:
                    if hasattr(message.forward, 'from_name'):
                        forward_info = f" [转发自: {message.forward.from_name}]"
                    elif hasattr(message.forward, 'from_id'):
                        forward_info = f" [转发自ID: {message.forward.from_id}]"
                    else:
                        forward_info = " [转发消息]"

                # 格式化输出
                print(f"消息 #{i} (ID: {message.id})")
                print(f"时间: {msg_time}")
                print(f"发送者: {sender_name}")

                if reply_info:
                    print(f"回复: {reply_info}")
                if forward_info:
                    print(f"转发: {forward_info}")
                if media_info:
                    print(f"媒体: {media_info}")

                if msg_text:
                    # 处理长消息
                    if len(msg_text) > 200:
                        print(f"内容: {msg_text[:200]}...")
                        print(f"      [消息总长度: {len(msg_text)} 字符]")
                    else:
                        print(f"内容: {msg_text}")
                else:
                    print("内容: [无文本内容]")

                print("-" * 60)

                # 保存消息数据
                message_data.append({
                    'id': message.id,
                    'date': msg_time,
                    'sender_name': sender_name,
                    'sender_id': sender_id,
                    'text': msg_text,
                    'media_info': media_info,
                    'reply_info': reply_info,
                    'forward_info': forward_info,
                    'raw_message_type': type(message).__name__
                })

            # 保存消息记录到文件
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'session_name': session_name,
                'dialog_info': {
                    'title': dialog_title,
                    'type': dialog_type,
                    'id': target_entity.id
                },
                'message_count': len(messages),
                'limit': limit,
                'days_filter': days,
                'messages': message_data
            }

            safe_title = "".join(c for c in dialog_title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
            output_file = f'telegram_messages_{safe_title}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n消息记录已保存到: {output_file}")

            # 关闭客户端连接
            await tg_client.close_client()
            logger.info("Telegram客户端连接已关闭")

            return output_data

    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return None


def check_session_file(session_name='default2'):
    """
    检查session文件是否存在
    """
    session_file = os.path.join(os.path.dirname(__file__), '..', 'static', 'utils', f'{session_name}-telegram.session')
    if not os.path.exists(session_file):
        logger.error(f"Session文件不存在: {session_file}")
        return False

    logger.info(f"Session文件存在: {session_file}")
    file_size = os.path.getsize(session_file)
    logger.info(f"Session文件大小: {file_size} bytes")
    return True


def print_usage():
    """打印使用说明"""
    print("用法:")
    print("  python tests/print_telegram_messages.py [session_name] [options]")
    print("")
    print("参数:")
    print("  session_name    指定要使用的session名称 (默认: default2)")
    print("")
    print("选项:")
    print("  --dialog ID/USERNAME    指定对话ID或用户名")
    print("  --limit NUMBER         消息数量限制 (默认: 50)")
    print("  --days NUMBER          获取最近几天的消息")
    print("")
    print("示例:")
    print("  python tests/print_telegram_messages.py                    # 交互式选择对话")
    print("  python tests/print_telegram_messages.py --dialog @username # 指定用户名")
    print("  python tests/print_telegram_messages.py --dialog 123456    # 指定对话ID")
    print("  python tests/print_telegram_messages.py --limit 100        # 获取100条消息")
    print("  python tests/print_telegram_messages.py --days 7           # 获取最近7天消息")


async def main():
    """
    主函数：解析命令行参数并打印Telegram对话记录
    """
    print("Telegram对话记录查看工具")

    # 解析命令行参数
    session_name = 'default2'
    target_dialog = None
    limit = 50
    days = None

    # 检查帮助参数
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_usage()
        sys.exit(0)

    # 解析参数
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--dialog' and i + 1 < len(sys.argv):
            target_dialog = sys.argv[i + 1]
            i += 2
        elif arg == '--limit' and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
            i += 2
        elif arg == '--days' and i + 1 < len(sys.argv):
            days = int(sys.argv[i + 1])
            i += 2
        elif not arg.startswith('--'):
            session_name = arg
            i += 1
        else:
            i += 1

    print("\n可用的Session文件:")
    sessions = list_available_sessions()
    if not sessions:
        print("未找到任何session文件")
        sys.exit(1)

    print("序号  Session名称      文件大小    最后修改时间")
    print("-" * 60)
    for i, session in enumerate(sessions, 1):
        import time
        mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session['mtime']))
        print(f"{i:2d}    {session['name']:<15} {session['size']:>8} bytes  {mtime_str}")

    # 检查session文件
    if not check_session_file(session_name):
        if sessions:
            latest_session = sessions[0]['name']
            print(f"\n指定的session '{session_name}' 不存在")
            print(f"是否使用最新的session '{latest_session}'? (y/n): ", end='')
            choice = input().strip().lower()
            if choice in ['y', 'yes', '是']:
                session_name = latest_session
            else:
                print("用户取消操作")
                sys.exit(1)
        else:
            print("错误: 没有可用的session文件，请先运行Telegram初始化")
            sys.exit(1)

    print(f"\n使用session: {session_name}")
    if target_dialog:
        print(f"目标对话: {target_dialog}")
    print(f"消息限制: {limit} 条")
    if days:
        print(f"时间范围: 最近 {days} 天")

    # 初始化应用（仅必要组件）
    app.ready(db_switch=False, web_switch=False, worker_switch=False, socketio_switch=False)

    print("\n开始连接Telegram并读取对话记录...")
    result = await print_telegram_messages(session_name, target_dialog, limit, days)

    if result:
        print(f"\n对话记录读取完成")
        print(f"对话: {result['dialog_info']['title']}")
        print(f"消息数量: {result['message_count']}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序执行失败: {e}")
        sys.exit(1)
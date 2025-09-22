#!/usr/bin/env python3
"""
脚本名称: read_telegram_private_messages.py
功能描述: 使用get_dialogs方法读取与Telegram官方的私人对话
作者: Claude Code
创建时间: 2025-09-22
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jd.services.spider.tg import TgService
from jd import app
from telethon.tl.types import Channel, Chat, User

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


async def read_telegram_private_conversations(session_name='default2'):
    """
    使用get_dialogs方法读取与Telegram官方和个人用户的私人对话

    Args:
        session_name (str): session文件名前缀，默认为'default2'
    """
    try:
        with app.app_context():
            logger.info(f"开始读取Telegram私人对话，使用{session_name}-telegram.session文件")

            # 使用TgService的init_tg方法
            tg_client = await TgService.init_tg(sessionname=session_name)
            if tg_client is None:
                logger.error(f"Session '{session_name}' 初始化失败，可能未授权或已过期")
                return

            logger.info("Telegram客户端初始化成功，正在获取私人对话列表...")

            raw_client = tg_client.client

            # 使用get_dialogs方法一次性获取所有对话
            telegram_dialogs = await raw_client.get_dialogs(limit=None)

            private_conversations = []
            telegram_official_conversations = []
            user_conversations = []

            print("\n" + "="*80)
            print(f"Telegram 私人对话分析 (使用session: {session_name})")
            print("="*80)

            for dialog in telegram_dialogs:
                entity = dialog.entity

                # 只处理User类型的对话（私人对话）
                if isinstance(entity, User):
                    user_info = {
                        'id': entity.id,
                        'first_name': getattr(entity, 'first_name', ''),
                        'last_name': getattr(entity, 'last_name', ''),
                        'username': getattr(entity, 'username', None),
                        'phone': getattr(entity, 'phone', None),
                        'bot': getattr(entity, 'bot', False),
                        'verified': getattr(entity, 'verified', False),
                        'premium': getattr(entity, 'premium', False),
                        'scam': getattr(entity, 'scam', False),
                        'fake': getattr(entity, 'fake', False),
                        'restricted': getattr(entity, 'restricted', False),
                        'deleted': getattr(entity, 'deleted', False),
                        'support': getattr(entity, 'support', False),
                        'unread_count': dialog.unread_count,
                        'is_pinned': getattr(dialog, 'pinned', False),
                        'date': dialog.date.strftime("%Y-%m-%d %H:%M:%S+%Z") if dialog.date else 'N/A'
                    }

                    private_conversations.append(user_info)

                    # 识别Telegram官方对话
                    if (entity.id == 777000 or  # Telegram官方通知
                        getattr(entity, 'support', False) or  # 支持账户
                        getattr(entity, 'verified', False) or  # 认证账户
                        'telegram' in str(getattr(entity, 'username', '')).lower()):
                        telegram_official_conversations.append(user_info)
                    else:
                        user_conversations.append(user_info)

            # 显示统计信息
            print(f"\n私人对话统计:")
            print(f"总私人对话数: {len(private_conversations)}")
            print(f"Telegram官方对话: {len(telegram_official_conversations)}")
            print(f"个人用户对话: {len(user_conversations)}")

            # 显示Telegram官方对话详情
            if telegram_official_conversations:
                print(f"\n" + "="*60)
                print(f"Telegram官方对话详情 ({len(telegram_official_conversations)} 个)")
                print("="*60)

                for i, conv in enumerate(telegram_official_conversations, 1):
                    print(f"\n官方对话 #{i}:")
                    print("-" * 40)
                    print(f"用户ID: {conv['id']}")

                    full_name = f"{conv['first_name']} {conv['last_name']}".strip()
                    print(f"姓名: {full_name if full_name else 'N/A'}")

                    if conv['username']:
                        print(f"用户名: @{conv['username']}")
                    else:
                        print("用户名: 未设置")

                    if conv['phone']:
                        print(f"电话号码: {conv['phone']}")
                    else:
                        print("电话号码: 未设置")

                    print(f"是否为机器人: {'是' if conv['bot'] else '否'}")
                    print(f"是否已验证: {'是' if conv['verified'] else '否'}")
                    print(f"是否为高级用户: {'是' if conv['premium'] else '否'}")
                    print(f"是否为支持账户: {'是' if conv['support'] else '否'}")
                    print(f"未读消息数: {conv['unread_count']}")
                    print(f"是否置顶: {'是' if conv['is_pinned'] else '否'}")
                    print(f"最后活动时间: {conv['date']}")

                    # 特殊标识
                    flags = []
                    if conv['scam']:
                        flags.append("诈骗标记")
                    if conv['fake']:
                        flags.append("虚假标记")
                    if conv['restricted']:
                        flags.append("受限账户")
                    if conv['deleted']:
                        flags.append("已删除")

                    if flags:
                        print(f"特殊标识: {', '.join(flags)}")

                    # 尝试获取最近消息（如果有未读消息）
                    if conv['unread_count'] > 0:
                        print(f"\n正在获取最近消息...")
                        try:
                            # 获取最近的几条消息
                            messages = await raw_client.get_messages(entity, limit=min(conv['unread_count'], 5))

                            if messages:
                                print(f"最近 {len(messages)} 条消息:")
                                for j, message in enumerate(messages, 1):
                                    msg_date = message.date.strftime("%Y-%m-%d %H:%M:%S") if message.date else 'N/A'
                                    msg_text = message.text[:100] + '...' if len(message.text) > 100 else message.text
                                    print(f"  {j}. [{msg_date}] {msg_text}")
                            else:
                                print("  无法获取消息内容")
                        except Exception as e:
                            print(f"  获取消息失败: {e}")

            # 显示个人用户对话
            if user_conversations:
                print(f"\n" + "="*60)
                print(f"个人用户对话列表 ({len(user_conversations)} 个)")
                print("="*60)

                for i, conv in enumerate(user_conversations, 1):
                    full_name = f"{conv['first_name']} {conv['last_name']}".strip()
                    username_str = f"@{conv['username']}" if conv['username'] else "无用户名"
                    bot_str = " [机器人]" if conv['bot'] else ""
                    premium_str = " [高级用户]" if conv['premium'] else ""
                    unread_str = f" (未读: {conv['unread_count']})" if conv['unread_count'] > 0 else ""

                    print(f"{i:2d}. {full_name} ({username_str}){bot_str}{premium_str}{unread_str} - ID: {conv['id']}")

            # 保存完整数据到JSON文件
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'session_name': session_name,
                'statistics': {
                    'total_private_conversations': len(private_conversations),
                    'telegram_official_conversations': len(telegram_official_conversations),
                    'user_conversations': len(user_conversations)
                },
                'telegram_official_conversations': telegram_official_conversations,
                'user_conversations': user_conversations,
                'all_private_conversations': private_conversations
            }

            output_file = f'telegram_private_conversations_{session_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n完整私人对话数据已保存到: {output_file}")

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

    Args:
        session_name (str): session文件名前缀
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
    print("  python tests/read_telegram_private_messages.py [session_name]")
    print("")
    print("参数:")
    print("  session_name    指定要使用的session名称 (默认: default2)")
    print("")
    print("示例:")
    print("  python tests/read_telegram_private_messages.py          # 使用default2 session")
    print("  python tests/read_telegram_private_messages.py 111      # 使用111 session")
    print("  python tests/read_telegram_private_messages.py web      # 使用web session")


async def main():
    """
    主函数：解析命令行参数并读取Telegram私人对话
    """
    print("Telegram私人对话读取工具")

    # 解析命令行参数
    session_name = 'default2'  # 默认使用default2 session

    # 检查帮助参数
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_usage()
        sys.exit(0)

    # 解析session名称参数
    if len(sys.argv) > 1:
        session_name = sys.argv[1]

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

    # 如果指定的session不存在，询问是否使用最新的
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
    print("模式: 读取Telegram私人对话（不写入数据库）")

    # 初始化应用（仅必要组件）
    app.ready(db_switch=False, web_switch=False, worker_switch=False, socketio_switch=False)

    print("开始连接Telegram并读取私人对话...")
    result = await read_telegram_private_conversations(session_name)

    if result:
        print(f"\n最终统计:")
        print(f"总私人对话数: {result['statistics']['total_private_conversations']}")
        print(f"Telegram官方对话: {result['statistics']['telegram_official_conversations']}")
        print(f"个人用户对话: {result['statistics']['user_conversations']}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序执行失败: {e}")
        sys.exit(1)
#!/usr/bin/env python3
"""
脚本名称: test_raw_iter_dialogs.py
功能描述: 使用Telethon底层的iter_dialogs方法获取对话列表，与get_dialog_list结果进行对比
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


async def test_raw_iter_dialogs(session_name='default2'):
    """
    使用Telethon底层的iter_dialogs方法获取对话列表

    Args:
        session_name (str): session文件名前缀，默认为'default2'
    """
    try:
        # 在应用上下文中执行
        with app.app_context():
            logger.info(f"开始初始化Telegram客户端，使用{session_name}-telegram.session文件")

            # 使用TgService的init_tg方法
            tg_client = await TgService.init_tg(sessionname=session_name)

            if tg_client is None:
                logger.error(f"Session '{session_name}' 初始化失败，可能未授权或已过期")
                return

            logger.info("Telegram客户端初始化成功，正在使用底层iter_dialogs获取对话列表...")

            # 获取原始客户端对象
            raw_client = tg_client.client

            # 使用底层iter_dialogs方法获取对话列表
            dialog_count = 0
            all_dialogs = []
            channel_dialogs = []
            chat_dialogs = []
            user_dialogs = []
            other_dialogs = []

            print("\n" + "="*80)
            print(f"Telethon 原始 iter_dialogs 结果 (使用session: {session_name})")
            print("="*80)

            async for dialog in raw_client.iter_dialogs():
                dialog_count += 1
                entity = dialog.entity

                # 基本信息
                dialog_info = {
                    'id': entity.id,
                    'unread_count': dialog.unread_count,
                    'dialog_type': type(entity).__name__,
                    'date': dialog.date.strftime("%Y-%m-%d %H:%M:%S+%Z") if dialog.date else 'N/A'
                }

                # 根据实体类型分类和获取详细信息
                if isinstance(entity, Channel):
                    dialog_info.update({
                        'title': getattr(entity, 'title', 'N/A'),
                        'username': getattr(entity, 'username', None),
                        'megagroup': getattr(entity, 'megagroup', False),
                        'broadcast': getattr(entity, 'broadcast', False),
                        'verified': getattr(entity, 'verified', False),
                        'restricted': getattr(entity, 'restricted', False),
                        'scam': getattr(entity, 'scam', False),
                        'fake': getattr(entity, 'fake', False),
                        'gigagroup': getattr(entity, 'gigagroup', False)
                    })
                    channel_dialogs.append(dialog_info)

                elif isinstance(entity, Chat):
                    dialog_info.update({
                        'title': getattr(entity, 'title', 'N/A'),
                        'participants_count': getattr(entity, 'participants_count', 0),
                        'creator': getattr(entity, 'creator', False),
                        'kicked': getattr(entity, 'kicked', False),
                        'left': getattr(entity, 'left', False),
                        'deactivated': getattr(entity, 'deactivated', False)
                    })
                    chat_dialogs.append(dialog_info)

                elif isinstance(entity, User):
                    dialog_info.update({
                        'first_name': getattr(entity, 'first_name', ''),
                        'last_name': getattr(entity, 'last_name', ''),
                        'username': getattr(entity, 'username', None),
                        'phone': getattr(entity, 'phone', None),
                        'bot': getattr(entity, 'bot', False),
                        'verified': getattr(entity, 'verified', False),
                        'restricted': getattr(entity, 'restricted', False),
                        'scam': getattr(entity, 'scam', False),
                        'fake': getattr(entity, 'fake', False),
                        'premium': getattr(entity, 'premium', False)
                    })
                    user_dialogs.append(dialog_info)

                else:
                    dialog_info.update({
                        'raw_entity': str(entity)
                    })
                    other_dialogs.append(dialog_info)

                all_dialogs.append(dialog_info)

                # 打印每个对话的基本信息
                print(f"\n对话 #{dialog_count}: [{dialog_info['dialog_type']}]")
                print("-" * 60)
                print(f"ID: {dialog_info['id']}")

                if 'title' in dialog_info:
                    print(f"标题: {dialog_info['title']}")
                elif 'first_name' in dialog_info:
                    full_name = f"{dialog_info['first_name']} {dialog_info.get('last_name', '')}".strip()
                    print(f"姓名: {full_name}")

                if 'username' in dialog_info and dialog_info['username']:
                    print(f"用户名: @{dialog_info['username']}")
                else:
                    print("用户名: 未设置")

                print(f"未读消息: {dialog_info['unread_count']}")
                print(f"日期: {dialog_info['date']}")

                # 特殊属性
                if isinstance(entity, Channel):
                    print(f"是否为超级群组: {dialog_info['megagroup']}")
                    print(f"是否为广播频道: {dialog_info['broadcast']}")
                    print(f"是否已验证: {dialog_info['verified']}")
                elif isinstance(entity, Chat):
                    print(f"参与者数量: {dialog_info['participants_count']}")
                    print(f"是否为创建者: {dialog_info['creator']}")
                elif isinstance(entity, User):
                    print(f"是否为机器人: {dialog_info['bot']}")
                    print(f"是否为高级用户: {dialog_info.get('premium', False)}")

            # 统计总结
            print(f"\n" + "="*80)
            print("统计总结:")
            print(f"总对话数: {dialog_count}")
            print(f"频道 (Channel): {len(channel_dialogs)}")
            print(f"群组 (Chat): {len(chat_dialogs)}")
            print(f"用户 (User): {len(user_dialogs)}")
            print(f"其他类型: {len(other_dialogs)}")
            print("="*80)

            # 详细分类显示
            print(f"\n频道列表 ({len(channel_dialogs)} 个):")
            print("-" * 60)
            for i, ch in enumerate(channel_dialogs, 1):
                type_str = "超级群组" if ch['megagroup'] else "广播频道"
                username_str = f"@{ch['username']}" if ch['username'] else "无用户名"
                print(f"{i:2d}. [{type_str}] {ch['title']} ({username_str}) - ID: {ch['id']}")

            print(f"\n群组列表 ({len(chat_dialogs)} 个):")
            print("-" * 60)
            for i, ch in enumerate(chat_dialogs, 1):
                print(f"{i:2d}. [普通群组] {ch['title']} (成员: {ch['participants_count']}) - ID: {ch['id']}")

            print(f"\n用户对话列表 ({len(user_dialogs)} 个):")
            print("-" * 60)
            for i, user in enumerate(user_dialogs, 1):
                full_name = f"{user['first_name']} {user.get('last_name', '')}".strip()
                username_str = f"@{user['username']}" if user['username'] else "无用户名"
                bot_str = " [机器人]" if user['bot'] else ""
                print(f"{i:2d}. [用户] {full_name} ({username_str}){bot_str} - ID: {user['id']}")

            if other_dialogs:
                print(f"\n其他类型对话 ({len(other_dialogs)} 个):")
                print("-" * 60)
                for i, other in enumerate(other_dialogs, 1):
                    print(f"{i:2d}. [其他] ID: {other['id']} - 类型: {other['dialog_type']}")

            # 保存完整数据到JSON文件（可选）
            output_file = f'raw_dialogs_{session_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'session_name': session_name,
                    'total_count': dialog_count,
                    'channels': channel_dialogs,
                    'chats': chat_dialogs,
                    'users': user_dialogs,
                    'others': other_dialogs,
                    'all_dialogs': all_dialogs
                }, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n完整数据已保存到: {output_file}")

            # 关闭客户端连接
            await tg_client.close_client()
            logger.info("Telegram客户端连接已关闭")

            return {
                'total': dialog_count,
                'channels': len(channel_dialogs),
                'chats': len(chat_dialogs),
                'users': len(user_dialogs),
                'others': len(other_dialogs),
                'channel_ids': [ch['id'] for ch in channel_dialogs],
                'chat_ids': [ch['id'] for ch in chat_dialogs],
                'user_ids': [u['id'] for u in user_dialogs]
            }

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
    print("  python tests/test_raw_iter_dialogs.py [session_name]")
    print("")
    print("参数:")
    print("  session_name    指定要使用的session名称 (默认: default2)")
    print("")
    print("示例:")
    print("  python tests/test_raw_iter_dialogs.py          # 使用default2 session")
    print("  python tests/test_raw_iter_dialogs.py 111      # 使用111 session")
    print("  python tests/test_raw_iter_dialogs.py web      # 使用web session")


async def main():
    """
    主函数：解析命令行参数并运行原始iter_dialogs测试
    """
    print("Telegram 原始 iter_dialogs 测试工具")

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
    print("模式: 使用Telethon原始iter_dialogs获取所有对话（不写入数据库）")

    # 初始化应用（仅必要组件）
    app.ready(db_switch=False, web_switch=False, worker_switch=False, socketio_switch=False)

    print("开始连接Telegram并使用原始iter_dialogs获取对话列表...")
    result = await test_raw_iter_dialogs(session_name)

    if result:
        print(f"\n最终统计结果:")
        print(f"总对话数: {result['total']}")
        print(f"- 频道: {result['channels']} 个")
        print(f"- 群组: {result['chats']} 个")
        print(f"- 用户: {result['users']} 个")
        print(f"- 其他: {result['others']} 个")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序执行失败: {e}")
        sys.exit(1)
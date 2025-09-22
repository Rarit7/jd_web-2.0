#!/usr/bin/env python3
"""
脚本名称: test_get_dialog_list.py (修改版)
功能描述: 使用真实session文件测试get_dialog_list方法，打印所有获取的对话信息
作者: Claude Code
修改时间: 2025-09-22
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

async def test_real_get_dialog_list(session_name='default2'):
    """
    使用真实session文件测试get_dialog_list方法

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

            logger.info("Telegram客户端初始化成功，正在获取对话列表...")

            # 获取对话列表
            dialog_count = 0
            print("\n" + "="*80)
            print(f"Telegram 对话列表信息 (使用session: {session_name})")
            print("="*80)

            async for dialog_info in tg_client.get_dialog_list():
                dialog_count += 1

                # 打印每个对话的详细信息
                print(f"\n对话 #{dialog_count}:")
                print("-" * 60)

                if dialog_info.get('data'):
                    data = dialog_info['data']

                    # 基本信息
                    print(f"ID: {data.get('id', 'N/A')}")
                    print(f"标题: {data.get('title', 'N/A')}")
                    print(f"用户名: @{data.get('username', '未设置') if data.get('username') else '未设置'}")
                    print(f"类型: {data.get('group_type', 'N/A')}")
                    print(f"分类: {data.get('megagroup', 'N/A')}")

                    # 统计信息
                    print(f"成员数量: {data.get('member_count', 'N/A')}")
                    print(f"未读消息: {data.get('unread_count', 'N/A')}")
                    print(f"是否公开: {'是' if data.get('is_public') == 1 else '否'}")

                    # 时间信息
                    print(f"加入时间: {data.get('join_date', 'N/A')}")

                    # 描述信息
                    description = data.get('channel_description', '')
                    if description:
                        print(f"描述: {description[:100]}{'...' if len(description) > 100 else ''}")
                    else:
                        print("描述: 无")

                    # 头像信息
                    photo_path = data.get('photo_path', '')
                    if photo_path:
                        print(f"头像路径: {photo_path}")
                    else:
                        print("头像路径: 无")

                    # 完整JSON数据（可选，用于调试）
                    print("\n完整数据JSON:")
                    print(json.dumps(dialog_info, indent=2, ensure_ascii=False))

                else:
                    print("数据: 无（可能是个人对话，已跳过）")
                    print(f"状态: {dialog_info.get('result', 'unknown')}")
                    print(f"原因: {dialog_info.get('reason', 'unknown')}")

                print("-" * 60)

            print(f"\n总计找到 {dialog_count} 个对话")
            print("="*80)

            # 关闭客户端连接
            await tg_client.close_client()
            logger.info("Telegram客户端连接已关闭")

    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")

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
    print("  python tests/test_get_dialog_list.py [session_name]")
    print("")
    print("参数:")
    print("  session_name    指定要使用的session名称 (默认: default2)")
    print("")
    print("示例:")
    print("  python tests/test_get_dialog_list.py          # 使用default2 session")
    print("  python tests/test_get_dialog_list.py 111      # 使用111 session")
    print("  python tests/test_get_dialog_list.py web      # 使用web session")

async def main():
    """
    主函数：解析命令行参数并运行真实的get_dialog_list测试
    """
    print("Telegram get_dialog_list 真实测试工具")

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
    print("模式: 获取并显示对话列表（不写入数据库）")

    # 初始化应用（仅必要组件）
    app.ready(db_switch=False, web_switch=False, worker_switch=False, socketio_switch=False)

    print("开始连接Telegram并获取对话列表...")
    await test_real_get_dialog_list(session_name)








if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序执行失败: {e}")
        sys.exit(1)
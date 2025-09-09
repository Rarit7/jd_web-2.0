#!/usr/bin/env python3
"""
脚本名称: read_tg_session_info.py
功能描述: 利用init_tg方法登录TG客户端，读取web-telegram.session文件并获取账户信息
作者: Claude Code
创建时间: 2025-09-09
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from jd.services.spider.tg import TgService
from jd import app, db
from jd.models.tg_account import TgAccount

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def save_account_to_database(account_info, session_name, config_info):
    """
    将账户信息保存到数据库tg_account表
    
    Args:
        account_info: Telegram账户信息对象
        session_name (str): 使用的session名称
        config_info (dict): TG配置信息
    
    Returns:
        bool: 保存是否成功
    """
    try:
        # 检查是否已存在相同的账户记录
        existing_account = TgAccount.query.filter_by(user_id=str(account_info.id)).first()
        
        if existing_account:
            # 更新现有记录
            existing_account.name = session_name
            existing_account.phone = account_info.phone or ''
            existing_account.username = account_info.username or ''
            existing_account.nickname = f"{account_info.first_name} {account_info.last_name or ''}".strip()
            existing_account.api_id = str(config_info.get('api_id', ''))
            existing_account.api_hash = config_info.get('api_hash', '')
            existing_account.status = TgAccount.StatusType.JOIN_SUCCESS  # 能获取到信息说明连接成功
            existing_account.updated_at = datetime.now()
            
            logger.info(f"更新现有账户记录: user_id={account_info.id}")
        else:
            # 创建新记录
            new_account = TgAccount(
                creator_id=1,  # 默认创建者ID，可根据需要调整
                name=session_name,
                phone=account_info.phone or '',
                user_id=str(account_info.id),
                username=account_info.username or '',
                nickname=f"{account_info.first_name} {account_info.last_name or ''}".strip(),
                api_id=str(config_info.get('api_id', '')),
                api_hash=config_info.get('api_hash', ''),
                status=TgAccount.StatusType.JOIN_SUCCESS,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(new_account)
            logger.info(f"创建新账户记录: user_id={account_info.id}")
        
        # 提交事务
        db.session.commit()
        logger.info("账户信息已成功保存到数据库")
        return True
        
    except Exception as e:
        logger.error(f"保存账户信息到数据库失败: {e}")
        db.session.rollback()
        return False


async def main(session_name='web', save_to_db=False):
    """
    主函数：使用init_tg方法登录TG客户端，获取指定session的账户信息
    
    Args:
        session_name (str): session文件名前缀，默认为'web'
        save_to_db (bool): 是否保存到数据库，默认为False
    """
    try:
        # 在应用上下文中执行
        with app.app_context():
            logger.info(f"开始初始化Telegram客户端，使用{session_name}-telegram.session文件")
            
            # 使用TgService的init_tg方法
            tg_client = await TgService.init_tg(sessionname=session_name)
            
            if tg_client is None:
                logger.error(f"Session '{session_name}' 初始化失败，可能未授权或已过期")
                
                # 如果指定session失败，尝试使用其他可用的session
                if session_name != '111':  # 避免无限循环
                    logger.info("尝试使用其他可用的session...")
                    sessions = list_available_sessions()
                    for session_info in sessions:
                        if session_info['name'] != session_name:
                            logger.info(f"尝试session: {session_info['name']}")
                            tg_client = await TgService.init_tg(sessionname=session_info['name'])
                            if tg_client is not None:
                                logger.info(f"成功使用session: {session_info['name']}")
                                session_name = session_info['name']  # 更新session名称用于显示
                                break
                
                if tg_client is None:
                    logger.error("所有session都无法使用，请检查Telegram授权状态")
                    return
            
            logger.info("Telegram客户端初始化成功，正在获取账户信息...")
            
            # 获取当前登录账户的信息
            account_info = await tg_client.get_me()
            
            if account_info:
                logger.info("成功获取账户信息:")
                print("\n" + "="*50)
                print(f"Telegram 账户信息 (使用session: {session_name})")
                print("="*50)
                print(f"用户ID: {account_info.id}")
                print(f"用户名: @{account_info.username if account_info.username else '未设置'}")
                print(f"姓名: {account_info.first_name} {account_info.last_name or ''}")
                print(f"电话号码: {account_info.phone or '未设置'}")
                print(f"是否为机器人: {'是' if account_info.bot else '否'}")
                print(f"是否已验证: {'是' if account_info.verified else '否'}")
                print(f"是否为高级用户: {'是' if account_info.premium else '否'}")
                print(f"语言代码: {account_info.lang_code or '未设置'}")
                
                # 如果有个人简介
                if hasattr(account_info, 'about') and account_info.about:
                    print(f"个人简介: {account_info.about}")
                    
                print("="*50)
                
                # 保存到数据库
                if save_to_db:
                    print("\n正在保存账户信息到数据库...")
                    # 获取TG配置信息
                    config_info = app.config.get('TG_CONFIG', {})
                    success = save_account_to_database(account_info, session_name, config_info)
                    if success:
                        print("✓ 账户信息已成功保存到tg_account表")
                    else:
                        print("✗ 保存账户信息到数据库失败")
                
            else:
                logger.error("无法获取账户信息")
            
            # 关闭客户端连接
            await tg_client.close_client()
            logger.info("Telegram客户端连接已关闭")
            
    except Exception as e:
        logger.error(f"执行过程中发生错误: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")


def check_session_file(session_name='web'):
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


def print_usage():
    """打印使用说明"""
    print("用法:")
    print("  python utils/read_tg_session_info.py [session_name] [--save-db]")
    print("")
    print("参数:")
    print("  session_name    指定要使用的session名称 (默认: web)")
    print("  --save-db       保存账户信息到数据库")
    print("")
    print("示例:")
    print("  python utils/read_tg_session_info.py          # 使用web session，只显示信息")
    print("  python utils/read_tg_session_info.py 111      # 使用111 session，只显示信息")
    print("  python utils/read_tg_session_info.py web --save-db  # 使用web session并保存到数据库")


if __name__ == '__main__':
    print("Telegram Session 账户信息读取工具")
    
    # 解析命令行参数
    session_name = 'web'  # 默认使用web session
    save_to_db = False
    
    # 检查帮助参数
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print_usage()
        sys.exit(0)
    
    # 解析参数
    for arg in sys.argv[1:]:
        if arg == '--save-db':
            save_to_db = True
        elif not arg.startswith('--'):
            session_name = arg
    
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
    if save_to_db:
        print("模式: 获取账户信息并保存到数据库")
        # 初始化数据库
        app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)
    else:
        print("模式: 仅获取并显示账户信息")
    
    print("开始连接Telegram并获取账户信息...")
    try:
        asyncio.run(main(session_name, save_to_db))
    except KeyboardInterrupt:
        print("\n用户中断操作")
    except Exception as e:
        print(f"程序执行失败: {e}")
        sys.exit(1)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram群组统计数据每日备份管理脚本

该脚本提供手动执行备份操作的能力，支持：
1. 立即执行所有群组备份
2. 备份单个群组
3. 查看备份统计信息
4. 测试备份功能

用法示例：
    python jd/jobs/tg_daily_backup_manager.py --action backup_all
    python jd/jobs/tg_daily_backup_manager.py --action backup_single --chat_id -123456789
    python jd/jobs/tg_daily_backup_manager.py --action stats
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jd import app, db
from jd.tasks.telegram.tg_daily_backup import (
    daily_backup_group_stats,
    backup_single_group_stats, 
    get_backup_stats
)

logger = logging.getLogger(__name__)


def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def execute_backup_all():
    """执行所有群组备份"""
    print("=" * 60)
    print("开始执行所有群组统计数据备份...")
    print("=" * 60)
    
    try:
        # 通过Celery执行任务
        from jCelery import celery
        result = celery.send_task('jd.tasks.telegram.tg_daily_backup.daily_backup_group_stats').get(timeout=300)
            
        if result['success']:
            print(f"✅ 备份成功完成!")
            print(f"   备份日期: {result['backup_date']}")
            print(f"   处理群组数: {result['backup_count']}")
            print(f"   有数据变更: {result['updated_count']}")
            return True
        else:
            print(f"❌ 备份失败: {result.get('message', '未知错误')}")
            return False
                
    except Exception as e:
        print(f"❌ 执行备份时发生错误: {str(e)}")
        logger.error(f"备份执行失败: {str(e)}", exc_info=True)
        return False


def execute_backup_single(chat_id):
    """执行单个群组备份"""
    print("=" * 60)
    print(f"开始备份群组 {chat_id} 的统计数据...")
    print("=" * 60)
    
    try:
        from jCelery import celery
        result = celery.send_task('jd.tasks.telegram.tg_daily_backup.backup_single_group_stats', args=[chat_id]).get(timeout=60)
            
        if result['success']:
            print(f"✅ 单个群组备份成功!")
            print(f"   群组ID: {result['chat_id']}")
            print(f"   成员数据: {result['members_backup']}")
            print(f"   消息数据: {result['records_backup']}")
            return True
        else:
            print(f"❌ 备份失败: {result.get('message', '未知错误')}")
            return False
                
    except Exception as e:
        print(f"❌ 执行单个群组备份时发生错误: {str(e)}")
        logger.error(f"单个群组备份失败: {str(e)}", exc_info=True)
        return False


def show_backup_stats():
    """显示备份统计信息"""
    print("=" * 60)
    print("群组备份统计信息")
    print("=" * 60)
    
    try:
        from jCelery import celery
        result = celery.send_task('jd.tasks.telegram.tg_daily_backup.get_backup_stats').get(timeout=60)
            
        print(f"总群组数: {result['total_groups']}")
        print(f"有成员数据的群组: {result['groups_with_members']}")
        print(f"有消息记录的群组: {result['groups_with_records']}")
        print(f"成员数据已同步: {result['synced_members_count']}")
        print(f"消息数据已同步: {result['synced_records_count']}")
        print(f"检查时间: {result['last_check']}")
        
        # 计算同步百分比
        if result['total_groups'] > 0:
            member_sync_percent = (result['synced_members_count'] / result['total_groups']) * 100
            record_sync_percent = (result['synced_records_count'] / result['total_groups']) * 100
            print(f"\n同步率:")
            print(f"  成员数据同步率: {member_sync_percent:.1f}%")
            print(f"  消息数据同步率: {record_sync_percent:.1f}%")
        
        return True
            
    except Exception as e:
        print(f"❌ 获取统计信息时发生错误: {str(e)}")
        logger.error(f"获取统计信息失败: {str(e)}", exc_info=True)
        return False


def test_backup_functionality():
    """测试备份功能"""
    print("=" * 60)
    print("测试备份功能...")
    print("=" * 60)
    
    # 首先显示统计信息
    print("1. 当前统计信息:")
    show_backup_stats()
    
    print("\n2. 测试是否可以连接数据库...")
    try:
        with app.app_context():
            from jd.models.tg_group_status import TgGroupStatus
            test_count = TgGroupStatus.query.count()
            print(f"✅ 数据库连接正常，共有 {test_count} 个群组状态记录")
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False
    
    print("\n3. 检查Celery任务是否可用...")
    try:
        # 尝试导入任务
        from jd.tasks.telegram.tg_daily_backup import daily_backup_group_stats
        print("✅ Celery任务导入成功")
    except Exception as e:
        print(f"❌ Celery任务导入失败: {str(e)}")
        return False
    
    print("\n✅ 所有功能测试通过！")
    return True


def main():
    parser = argparse.ArgumentParser(description='Telegram群组统计数据备份管理工具')
    parser.add_argument(
        '--action', 
        choices=['backup_all', 'backup_single', 'stats', 'test'],
        required=True,
        help='要执行的操作'
    )
    parser.add_argument(
        '--chat_id',
        type=str,
        help='单个群组备份时的群组ID (用于backup_single操作)'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    # 显示开始信息
    print(f"\nTelegram群组数据备份管理器")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"操作: {args.action}")
    
    success = False
    
    if args.action == 'backup_all':
        success = execute_backup_all()
        
    elif args.action == 'backup_single':
        if not args.chat_id:
            print("❌ 错误: --chat_id 参数是必需的")
            sys.exit(1)
        success = execute_backup_single(args.chat_id)
        
    elif args.action == 'stats':
        success = show_backup_stats()
        
    elif args.action == 'test':
        success = test_backup_functionality()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 操作完成")
        sys.exit(0)
    else:
        print("❌ 操作失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
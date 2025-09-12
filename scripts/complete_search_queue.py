#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量完成搜索队列中的所有任务
标记 keyword_search_queue 表中的所有待处理和处理中的任务为已完成状态
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目路径到sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jd import app, db
from jd.models.keyword_search_queue import KeywordSearchQueue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SearchQueueCompleter:
    def __init__(self):
        self.completed_count = 0
        self.error_count = 0
        self.total_count = 0

    def get_pending_tasks(self):
        """获取所有待处理和处理中的任务"""
        try:
            # 查询状态为待处理(0)和处理中(1)的任务
            tasks = KeywordSearchQueue.query.filter(
                KeywordSearchQueue.status.in_([
                    KeywordSearchQueue.StatusType.PENDING,
                    KeywordSearchQueue.StatusType.PROCESSING
                ])
            ).all()
            
            logger.info(f"找到 {len(tasks)} 个需要完成的搜索任务")
            return tasks
        except Exception as e:
            logger.error(f"获取待处理任务时发生错误: {e}")
            return []

    def complete_task(self, task):
        """标记单个任务为已完成"""
        try:
            original_status = task.status
            task.status = KeywordSearchQueue.StatusType.PROCESSED
            task.updated_at = datetime.now()
            
            logger.info(f"任务 ID: {task.id}, 关键词: '{task.keyword}', 状态: {original_status} -> {task.status}")
            return True
        except Exception as e:
            logger.error(f"完成任务 ID {task.id} 时发生错误: {e}")
            return False

    def complete_all_tasks(self, dry_run=False):
        """批量完成所有任务"""
        tasks = self.get_pending_tasks()
        if not tasks:
            logger.info("没有找到需要完成的任务")
            return
        
        self.total_count = len(tasks)
        
        if dry_run:
            logger.info(f"【预览模式】将要完成以下 {self.total_count} 个任务:")
            for task in tasks:
                status_name = "待处理" if task.status == KeywordSearchQueue.StatusType.PENDING else "处理中"
                logger.info(f"  - ID: {task.id}, 批次: {task.batch_id}, 关键词: '{task.keyword}', "
                          f"搜索类型: {task.search_type}, 状态: {status_name}")
            logger.info("【预览结束】使用 --execute 参数执行实际操作")
            return
        
        logger.info(f"开始批量完成 {self.total_count} 个搜索任务...")
        
        try:
            # 批量更新，提高性能
            updated_count = KeywordSearchQueue.query.filter(
                KeywordSearchQueue.status.in_([
                    KeywordSearchQueue.StatusType.PENDING,
                    KeywordSearchQueue.StatusType.PROCESSING
                ])
            ).update({
                KeywordSearchQueue.status: KeywordSearchQueue.StatusType.PROCESSED,
                KeywordSearchQueue.updated_at: datetime.now()
            }, synchronize_session=False)
            
            # 提交事务
            db.session.commit()
            
            self.completed_count = updated_count
            logger.info(f"批量操作完成！成功标记 {self.completed_count} 个任务为已完成")
            
        except Exception as e:
            logger.error(f"批量更新过程中发生错误: {e}")
            db.session.rollback()
            self.error_count = self.total_count

    def get_status_summary(self):
        """获取当前队列状态统计"""
        try:
            status_counts = db.session.query(
                KeywordSearchQueue.status,
                db.func.count(KeywordSearchQueue.id).label('count')
            ).group_by(KeywordSearchQueue.status).all()
            
            status_map = {
                KeywordSearchQueue.StatusType.PENDING: "待处理",
                KeywordSearchQueue.StatusType.PROCESSING: "处理中", 
                KeywordSearchQueue.StatusType.PROCESSED: "已处理"
            }
            
            logger.info("=" * 50)
            logger.info("搜索队列状态统计:")
            total = 0
            for status, count in status_counts:
                status_name = status_map.get(status, f"未知状态({status})")
                logger.info(f"  {status_name}: {count} 个任务")
                total += count
            logger.info(f"  总计: {total} 个任务")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"获取状态统计时发生错误: {e}")

    def print_summary(self):
        """输出执行总结"""
        logger.info("=" * 50)
        logger.info("执行完成！统计信息:")
        logger.info(f"需要处理的任务数: {self.total_count}")
        logger.info(f"成功完成: {self.completed_count}")
        logger.info(f"处理错误: {self.error_count}")
        logger.info("=" * 50)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='批量完成搜索队列中的所有待处理任务',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python scripts/complete_search_queue.py --status          # 查看当前队列状态
  python scripts/complete_search_queue.py                   # 预览将要完成的任务
  python scripts/complete_search_queue.py --execute         # 执行实际完成操作

说明:
  - 脚本会将所有状态为"待处理"(0)和"处理中"(1)的任务标记为"已处理"(2)
  - 默认为预览模式，只显示将要操作的任务，不会实际修改数据库
  - 使用 --execute 参数执行实际的数据库更新操作
  - 使用 --status 参数查看当前队列中各状态任务的数量统计
        """
    )
    parser.add_argument('--execute', action='store_true', 
                       help='执行实际操作（不加此参数只会预览）')
    parser.add_argument('--status', action='store_true',
                       help='只显示当前队列状态统计')
    
    args = parser.parse_args()
    
    completer = SearchQueueCompleter()
    
    try:
        # 初始化Flask应用
        app.ready()
        
        with app.app_context():
            if args.status:
                # 只显示状态统计
                completer.get_status_summary()
                return
            
            # 显示执行前状态
            logger.info("执行前的队列状态:")
            completer.get_status_summary()
            
            # 执行任务完成操作
            dry_run = not args.execute
            completer.complete_all_tasks(dry_run=dry_run)
            
            if args.execute:
                # 显示执行后状态
                logger.info("执行后的队列状态:")
                completer.get_status_summary()
                completer.print_summary()
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"程序执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
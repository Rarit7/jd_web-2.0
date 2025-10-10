"""
自动标签任务 - BaseTask 包装器和 Celery 任务定义

将现有的 AutoTaggingService 集成到 BaseTask 框架中，
提供任务队列管理、冲突检测、状态跟踪等功能。
同时提供 Celery 任务入口点供 API 调用。
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from scripts.worker import celery
from jd import db
from jd.tasks.base_task import BaseTask
from jd.jobs.auto_tagging import AutoTaggingService
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_user_info import TgGroupUserInfo

logger = logging.getLogger(__name__)


class AutoTaggingTask(BaseTask):
    """
    自动标签任务 - BaseTask 包装器

    支持两种任务类型：
    - daily: 每日增量任务（处理昨天的数据）
    - historical: 历史数据全量处理
    - date_range: 指定日期范围处理
    """

    def __init__(self, task_type: str = 'daily',
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 wait_if_conflict: bool = True):
        """
        初始化自动标签任务

        Args:
            task_type: 任务类型 ('daily', 'historical', 'date_range')
            start_date: 起始日期 (ISO格式字符串，仅 date_range 模式使用)
            end_date: 结束日期 (ISO格式字符串，仅 date_range 模式使用)
            wait_if_conflict: 任务冲突时是否等待（默认 True）
        """
        # 使用任务类型作为 resource_id，确保同类型任务互斥
        super().__init__(resource_id=f"auto_tagging_{task_type}")

        self.task_type = task_type
        self.start_date = start_date
        self.end_date = end_date
        self.wait_if_conflict = wait_if_conflict

        # 任务统计
        self.stats = {
            'task_type': task_type,
            'start_time': None,
            'end_time': None,
            'duration_seconds': 0,
            'chat_stats': {},
            'user_stats': {}
        }

    def get_job_name(self) -> str:
        """获取任务名称"""
        return 'auto_tagging_task'

    def execute_task(self) -> Dict[str, Any]:
        """
        执行自动标签任务

        Returns:
            任务执行结果
        """
        start_time = datetime.now()
        self.stats['start_time'] = start_time.isoformat()

        logger.info(f"开始执行自动标签任务，类型: {self.task_type}")

        try:
            # 实例化服务（启用AC自动机缓存）
            service = AutoTaggingService(use_ac_automaton=True)

            # 根据任务类型执行不同的处理逻辑
            if self.task_type == 'daily':
                result = self._execute_daily_task(service)
            elif self.task_type == 'historical':
                result = self._execute_historical_task(service)
            elif self.task_type == 'date_range':
                result = self._execute_date_range_task(service)
            else:
                return {
                    'err_code': 1,
                    'err_msg': f'不支持的任务类型: {self.task_type}'
                }

            # 计算耗时
            end_time = datetime.now()
            self.stats['end_time'] = end_time.isoformat()
            self.stats['duration_seconds'] = (end_time - start_time).total_seconds()

            # 合并结果
            result['payload'] = {
                **result.get('payload', {}),
                **self.stats
            }

            logger.info(f"自动标签任务完成，耗时: {self.stats['duration_seconds']:.1f}秒")
            return result

        except Exception as e:
            logger.error(f"自动标签任务执行失败: {str(e)}", exc_info=True)
            return {
                'err_code': 1,
                'err_msg': f'任务执行失败: {str(e)}',
                'payload': self.stats
            }

    def _execute_daily_task(self, service: AutoTaggingService) -> Dict[str, Any]:
        """
        执行每日任务（处理昨天的数据）

        Args:
            service: AutoTaggingService 实例

        Returns:
            任务执行结果
        """
        # 确定时间范围（昨天 00:00 - 23:59）
        yesterday = datetime.now() - timedelta(days=1)
        start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

        logger.info(f"每日任务时间范围: {start_time} ~ {end_time}")

        # 处理聊天记录
        chat_records = TgGroupChatHistory.query.filter(
            TgGroupChatHistory.created_at >= start_time,
            TgGroupChatHistory.created_at <= end_time
        ).all()

        if self.check_should_stop():
            return {'err_code': 1, 'err_msg': '任务被手动停止'}

        chat_stats = service.process_chat_history_batch(
            chat_records,
            batch_commit_size=100
        )

        # 处理用户信息
        user_infos = TgGroupUserInfo.query.filter(
            TgGroupUserInfo.updated_at >= start_time,
            TgGroupUserInfo.updated_at <= end_time
        ).all()

        if self.check_should_stop():
            return {'err_code': 1, 'err_msg': '任务被手动停止'}

        user_stats = service.process_user_info_batch(
            user_infos,
            batch_commit_size=100
        )

        # 更新统计信息
        self.stats['chat_stats'] = chat_stats
        self.stats['user_stats'] = user_stats
        self.stats['date_range'] = {
            'start': start_time.isoformat(),
            'end': end_time.isoformat(),
            'date': yesterday.strftime('%Y-%m-%d')
        }
        self.stats['total_chat_records'] = len(chat_records)
        self.stats['total_user_infos'] = len(user_infos)

        return {
            'err_code': 0,
            'err_msg': f"每日任务完成: 处理 {len(chat_records)} 条聊天记录, {len(user_infos)} 个用户信息",
            'payload': self.stats
        }

    def _execute_historical_task(self, service: AutoTaggingService) -> Dict[str, Any]:
        """
        执行历史数据全量处理任务

        Args:
            service: AutoTaggingService 实例

        Returns:
            任务执行结果
        """
        import time

        batch_size = 1000
        chat_offset = 0
        user_offset = 0

        total_chat_stats = {
            'total_processed': 0,
            'total_tags_applied': 0,
            'failed_count': 0
        }

        total_user_stats = {
            'total_processed': 0,
            'total_tags_applied': 0,
            'failed_count': 0
        }

        logger.info("开始处理历史聊天记录...")

        # 分批处理聊天记录
        batch_count = 0
        while True:
            if self.check_should_stop():
                logger.warning("任务被手动停止，中断处理")
                break

            chat_records = TgGroupChatHistory.query.offset(chat_offset).limit(batch_size).all()
            if not chat_records:
                break

            batch_stats = service.process_chat_history_batch(
                chat_records,
                batch_commit_size=100
            )

            # 累加统计
            total_chat_stats['total_processed'] += batch_stats['total_processed']
            total_chat_stats['total_tags_applied'] += batch_stats['total_tags_applied']
            total_chat_stats['failed_count'] += batch_stats['failed_count']

            chat_offset += batch_size
            batch_count += 1

            if batch_count % 5 == 0:  # 每5批输出一次日志
                logger.info(f"已处理 {total_chat_stats['total_processed']} 条聊天记录, "
                           f"应用标签 {total_chat_stats['total_tags_applied']} 个")

            # 避免长时间占用资源
            time.sleep(0.5)

        logger.info("开始处理历史用户信息...")

        # 分批处理用户信息
        batch_count = 0
        while True:
            if self.check_should_stop():
                logger.warning("任务被手动停止，中断处理")
                break

            user_infos = TgGroupUserInfo.query.offset(user_offset).limit(batch_size).all()
            if not user_infos:
                break

            batch_stats = service.process_user_info_batch(
                user_infos,
                batch_commit_size=100
            )

            # 累加统计
            total_user_stats['total_processed'] += batch_stats['total_processed']
            total_user_stats['total_tags_applied'] += batch_stats['total_tags_applied']
            total_user_stats['failed_count'] += batch_stats['failed_count']

            user_offset += batch_size
            batch_count += 1

            if batch_count % 5 == 0:
                logger.info(f"已处理 {total_user_stats['total_processed']} 个用户信息, "
                           f"应用标签 {total_user_stats['total_tags_applied']} 个")

            time.sleep(0.5)

        # 更新统计信息
        self.stats['chat_stats'] = total_chat_stats
        self.stats['user_stats'] = total_user_stats

        return {
            'err_code': 0,
            'err_msg': f"历史任务完成: 处理 {total_chat_stats['total_processed']} 条聊天记录, "
                      f"{total_user_stats['total_processed']} 个用户信息",
            'payload': self.stats
        }

    def _execute_date_range_task(self, service: AutoTaggingService) -> Dict[str, Any]:
        """
        执行指定日期范围的任务

        Args:
            service: AutoTaggingService 实例

        Returns:
            任务执行结果
        """
        # 解析日期范围
        try:
            if self.start_date and self.end_date:
                start_time = datetime.fromisoformat(self.start_date)
                end_time = datetime.fromisoformat(self.end_date)
            else:
                # 默认处理最近60天
                end_time = datetime.now()
                start_time = end_time - timedelta(days=60)
        except Exception as e:
            return {
                'err_code': 1,
                'err_msg': f'日期格式错误: {str(e)}'
            }

        logger.info(f"日期范围任务时间范围: {start_time} ~ {end_time}")

        # 处理聊天记录
        chat_records = TgGroupChatHistory.query.filter(
            TgGroupChatHistory.created_at >= start_time,
            TgGroupChatHistory.created_at <= end_time
        ).all()

        if self.check_should_stop():
            return {'err_code': 1, 'err_msg': '任务被手动停止'}

        chat_stats = service.process_chat_history_batch(
            chat_records,
            batch_commit_size=100
        )

        # 处理用户信息
        user_infos = TgGroupUserInfo.query.filter(
            TgGroupUserInfo.updated_at >= start_time,
            TgGroupUserInfo.updated_at <= end_time
        ).all()

        if self.check_should_stop():
            return {'err_code': 1, 'err_msg': '任务被手动停止'}

        user_stats = service.process_user_info_batch(
            user_infos,
            batch_commit_size=100
        )

        # 更新统计信息
        self.stats['chat_stats'] = chat_stats
        self.stats['user_stats'] = user_stats
        self.stats['date_range'] = {
            'start': start_time.isoformat(),
            'end': end_time.isoformat()
        }
        self.stats['total_chat_records'] = len(chat_records)
        self.stats['total_user_infos'] = len(user_infos)

        return {
            'err_code': 0,
            'err_msg': f"日期范围任务完成: 处理 {len(chat_records)} 条聊天记录, {len(user_infos)} 个用户信息",
            'payload': self.stats
        }

    def generate_result_summary(self, result: Dict[str, Any]) -> str:
        """
        生成任务结果的友好摘要文本

        Args:
            result: 任务执行结果字典

        Returns:
            友好的结果摘要文本
        """
        if not result:
            return "自动标签任务完成，无结果数据"

        err_code = result.get('err_code', 0)
        if err_code != 0:
            return f"自动标签任务失败: {result.get('err_msg', '未知错误')}"

        payload = result.get('payload', {})
        chat_stats = payload.get('chat_stats', {})
        user_stats = payload.get('user_stats', {})
        duration = payload.get('duration_seconds', 0)

        # 构建摘要
        summary_parts = [
            f"任务类型: {self.task_type}",
            f"聊天记录: 处理 {chat_stats.get('total_processed', 0)} 条，应用标签 {chat_stats.get('total_tags_applied', 0)} 个",
            f"用户信息: 处理 {user_stats.get('total_processed', 0)} 个，应用标签 {user_stats.get('total_tags_applied', 0)} 个",
            f"耗时: {duration:.1f}秒"
        ]

        # 添加日期范围信息
        if 'date_range' in payload:
            date_info = payload['date_range']
            if 'date' in date_info:
                summary_parts.insert(1, f"日期: {date_info['date']}")

        return " | ".join(summary_parts)


# ==================== Celery 任务定义 ====================

@celery.task(bind=True, queue='jd.celery.first')
def execute_auto_tagging_basetask(self, task_type='daily', start_date=None, end_date=None, wait_if_conflict=True):
    """
    异步执行自动标签 BaseTask

    Args:
        task_type: 任务类型 ('daily', 'historical', 'date_range')
        start_date: 开始日期（可选）
        end_date: 结束日期（可选）
        wait_if_conflict: 是否在冲突时等待

    Returns:
        dict: 任务执行结果
    """
    try:
        logger.info(f"Celery异步执行自动标签任务: type={task_type}")

        task = AutoTaggingTask(
            task_type=task_type,
            start_date=start_date,
            end_date=end_date,
            wait_if_conflict=wait_if_conflict
        )

        result = task.start_task()
        logger.info(f"自动标签任务完成: {result.get('err_msg', 'success')}")
        return result

    except Exception as e:
        error_msg = f"自动标签任务执行失败: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise self.retry(countdown=60, max_retries=3)

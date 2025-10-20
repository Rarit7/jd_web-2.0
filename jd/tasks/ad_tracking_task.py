"""
广告追踪 Celery 异步任务

功能：
1. 每日增量广告追踪任务（定时执行）
2. 历史数据批量处理任务（手动触发）
3. 单条记录处理任务（即时处理）
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from scripts.worker import celery
from jd import app, db
from jd.jobs.ad_tracking_job import AdTrackingJob

logger = logging.getLogger(__name__)


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.daily_task')
def daily_ad_tracking_task(self, target_date: str = None) -> Dict[str, Any]:
    """
    每日广告追踪任务

    Args:
        target_date: 目标日期（YYYY-MM-DD格式），默认为昨天

    Returns:
        执行结果统计
    """
    try:
        logger.info("Starting daily ad tracking task")

        with app.app_context():
            job = AdTrackingJob()

            # 解析日期参数
            if target_date:
                date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            else:
                date_obj = None

            result = job.run_daily_task(date_obj)

            logger.info(f"Daily ad tracking task completed: {result}")
            return result

    except Exception as e:
        logger.error(f"Daily ad tracking task failed: {str(e)}", exc_info=True)
        # Celery重试机制
        raise self.retry(countdown=300, max_retries=3, exc=e)


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.date_range_task')
def date_range_ad_tracking_task(self, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    时间范围广告追踪任务（前端手动触发用于任意时间段处理）

    Args:
        start_date: 开始日期（YYYY-MM-DD格式）
        end_date: 结束日期（YYYY-MM-DD格式）

    Returns:
        执行结果统计
    """
    try:
        logger.info(f"Starting date range ad tracking task from {start_date} to {end_date}")

        with app.app_context():
            job = AdTrackingJob()

            # 解析日期参数
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)

            from jd.models.tg_group_chat_history import TgGroupChatHistory
            from jd.models.tg_group_user_info import TgGroupUserInfo
            from jd.models.tg_group import TgGroup
            from jd import db

            result = {
                'start_date': start_date,
                'end_date': end_date,
                'chat_records_processed': 0,
                'user_infos_processed': 0,
                'group_infos_processed': 0,
                'total_urls': 0,
                'total_accounts': 0,
                'total_items': 0,
                'errors': 0
            }

            try:
                # 处理指定范围内的聊天记录
                chat_records = TgGroupChatHistory.query.filter(
                    TgGroupChatHistory.postal_time >= start_datetime,
                    TgGroupChatHistory.postal_time <= end_datetime
                ).all()

                for record in chat_records:
                    try:
                        stats = job.process_chat_record(record)
                        result['chat_records_processed'] += 1
                        result['total_urls'] += stats['urls']
                        result['total_accounts'] += stats['telegram_accounts']
                        result['total_items'] += stats['total_items']
                    except Exception as e:
                        logger.error(f"Error processing chat record {record.id}: {str(e)}")
                        result['errors'] += 1

                # 处理指定范围内更新的用户信息
                user_infos = TgGroupUserInfo.query.filter(
                    TgGroupUserInfo.updated_at >= start_datetime,
                    TgGroupUserInfo.updated_at <= end_datetime
                ).all()

                for user_info in user_infos:
                    try:
                        stats = job.process_user_info(user_info)
                        result['user_infos_processed'] += 1
                        result['total_urls'] += stats['urls']
                        result['total_accounts'] += stats['telegram_accounts']
                        result['total_items'] += stats['total_items']
                    except Exception as e:
                        logger.error(f"Error processing user info {user_info.user_id}: {str(e)}")
                        result['errors'] += 1

                # 处理指定范围内更新的群组信息
                groups = TgGroup.query.filter(
                    TgGroup.updated_at >= start_datetime,
                    TgGroup.updated_at <= end_datetime
                ).all()

                for group in groups:
                    try:
                        stats = job.process_group_info(group)
                        result['group_infos_processed'] += 1
                        result['total_urls'] += stats['urls']
                        result['total_accounts'] += stats['telegram_accounts']
                        result['total_items'] += stats['total_items']
                    except Exception as e:
                        logger.error(f"Error processing group {group.chat_id}: {str(e)}")
                        result['errors'] += 1

                # 提交数据库
                db.session.commit()
                result['status'] = 'success'
                logger.info(f"Date range ad tracking task completed: {result}")

            except Exception as e:
                db.session.rollback()
                logger.error(f"Date range ad tracking task failed: {str(e)}")
                result['status'] = 'failed'
                result['error'] = str(e)
                raise

            return result

    except Exception as e:
        logger.error(f"Date range ad tracking task failed: {str(e)}", exc_info=True)
        # Celery重试机制
        raise self.retry(countdown=300, max_retries=3, exc=e)


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.historical_batch')
def historical_ad_tracking_batch_task(self, batch_size: int = 1000, max_batches: int = None) -> Dict[str, Any]:
    """
    历史数据批量处理任务

    Args:
        batch_size: 每批处理数量
        max_batches: 最大批次数（None表示处理全部）

    Returns:
        执行结果统计
    """
    try:
        logger.info(f"Starting historical ad tracking batch task (batch_size={batch_size}, max_batches={max_batches})")

        with app.app_context():
            job = AdTrackingJob()
            result = job.run_historical_batch(batch_size, max_batches)

            logger.info(f"Historical ad tracking batch task completed: {result}")
            return result

    except Exception as e:
        logger.error(f"Historical ad tracking batch task failed: {str(e)}", exc_info=True)
        # 批量任务失败不重试，避免重复处理
        raise


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.process_chat_record')
def process_chat_record_task(self, chat_record_id: int) -> Dict[str, Any]:
    """
    处理单条聊天记录（即时任务）

    Args:
        chat_record_id: 聊天记录ID

    Returns:
        处理结果
    """
    try:
        logger.info(f"Processing chat record {chat_record_id}")

        with app.app_context():
            from jd.models.tg_group_chat_history import TgGroupChatHistory

            job = AdTrackingJob()
            chat_record = TgGroupChatHistory.query.get(chat_record_id)

            if not chat_record:
                logger.warning(f"Chat record {chat_record_id} not found")
                return {'status': 'failed', 'error': 'Record not found'}

            stats = job.process_chat_record(chat_record)
            db.session.commit()

            result = {
                'status': 'success',
                'chat_record_id': chat_record_id,
                'stats': stats
            }

            logger.info(f"Chat record {chat_record_id} processed: {result}")
            return result

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to process chat record {chat_record_id}: {str(e)}", exc_info=True)
        raise self.retry(countdown=60, max_retries=3, exc=e)


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.process_user_info')
def process_user_info_task(self, user_id: str) -> Dict[str, Any]:
    """
    处理用户信息（即时任务）

    Args:
        user_id: 用户ID

    Returns:
        处理结果
    """
    try:
        logger.info(f"Processing user info {user_id}")

        with app.app_context():
            from jd.models.tg_group_user_info import TgGroupUserInfo

            job = AdTrackingJob()
            user_info = TgGroupUserInfo.query.filter_by(user_id=user_id).first()

            if not user_info:
                logger.warning(f"User info {user_id} not found")
                return {'status': 'failed', 'error': 'User not found'}

            stats = job.process_user_info(user_info)
            db.session.commit()

            result = {
                'status': 'success',
                'user_id': user_id,
                'stats': stats
            }

            logger.info(f"User info {user_id} processed: {result}")
            return result

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to process user info {user_id}: {str(e)}", exc_info=True)
        raise self.retry(countdown=60, max_retries=3, exc=e)


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.process_group_info')
def process_group_info_task(self, chat_id: str) -> Dict[str, Any]:
    """
    处理群组信息（即时任务）

    Args:
        chat_id: 群组ID

    Returns:
        处理结果
    """
    try:
        logger.info(f"Processing group info {chat_id}")

        with app.app_context():
            from jd.models.tg_group import TgGroup

            job = AdTrackingJob()
            group = TgGroup.query.filter_by(chat_id=chat_id).first()

            if not group:
                logger.warning(f"Group {chat_id} not found")
                return {'status': 'failed', 'error': 'Group not found'}

            stats = job.process_group_info(group)
            db.session.commit()

            result = {
                'status': 'success',
                'chat_id': chat_id,
                'stats': stats
            }

            logger.info(f"Group info {chat_id} processed: {result}")
            return result

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to process group info {chat_id}: {str(e)}", exc_info=True)
        raise self.retry(countdown=60, max_retries=3, exc=e)




# 定时任务配置（在 jCelery/celeryconfig.py 的 beat_schedule 中配置）
"""
beat_schedule 配置示例：

from celery.schedules import crontab

beat_schedule = {
    # 每日凌晨3:07执行广告追踪任务
    # 处理上一日的新增聊天记录、新增或修改的用户信息、新增或修改的群组信息
    'daily-ad-tracking': {
        'task': 'ad_tracking.daily_task',
        'schedule': crontab(hour=3, minute=7),
        'options': {
            'expires': 3600,  # 任务1小时后过期
        }
    },
}

前端API手动触发支持：
1. 指定日期处理（处理该日期的内容）:
   {
     "task_type": "daily",
     "target_date": "2025-10-19"
   }

2. 时间范围处理（处理指定范围的内容）:
   {
     "task_type": "date_range",
     "start_date": "2025-10-10",
     "end_date": "2025-10-19"
   }
"""

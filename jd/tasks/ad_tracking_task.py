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




# 定时任务配置（在 scripts/worker.py 的 beat_schedule 中配置）
"""
beat_schedule 配置示例：

from celery.schedules import crontab

celery.conf.beat_schedule = {
    # 每日凌晨1点执行广告追踪任务
    'daily-ad-tracking': {
        'task': 'ad_tracking.daily_task',
        'schedule': crontab(hour=1, minute=0),
        'args': ()
    },
}
"""

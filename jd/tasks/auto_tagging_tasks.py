import logging
import time
from datetime import datetime, timedelta

from scripts.worker import celery
from jd import db
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.services.auto_tagging_service import AutoTaggingService

logger = logging.getLogger(__name__)


@celery.task(bind=True, queue='jd.celery.first')
def daily_auto_tagging_task(self):
    """每日自动标签任务"""
    try:
        logger.info("开始执行每日自动标签任务")

        # 处理昨天的聊天记录
        yesterday = datetime.now() - timedelta(days=1)
        start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

        chat_records = TgGroupChatHistory.query.filter(
            TgGroupChatHistory.created_at >= start_time,
            TgGroupChatHistory.created_at <= end_time
        ).all()

        processed_chats = 0
        processed_users = 0

        # 处理聊天记录
        for record in chat_records:
            if record.message:
                try:
                    AutoTaggingService.process_chat_message(
                        record.message,
                        str(record.user_id),
                        str(record.id)
                    )
                    processed_chats += 1
                except Exception as e:
                    logger.error(f"处理聊天记录失败 ID:{record.id}, 错误:{str(e)}")

        # 处理昨天有变更的用户信息
        user_changes = TgGroupUserInfo.query.filter(
            TgGroupUserInfo.updated_at >= start_time,
            TgGroupUserInfo.updated_at <= end_time
        ).all()

        for user_info in user_changes:
            try:
                AutoTaggingService.process_user_info(
                    str(user_info.user_id),
                    user_info.nickname,
                    user_info.desc
                )
                processed_users += 1
            except Exception as e:
                logger.error(f"处理用户信息失败 user_id:{user_info.user_id}, 错误:{str(e)}")

        result = {
            'status': 'success',
            'processed_chats': processed_chats,
            'processed_users': processed_users,
            'total_chat_records': len(chat_records),
            'total_user_changes': len(user_changes),
            'date': yesterday.strftime('%Y-%m-%d')
        }

        logger.info(f"每日自动标签任务完成: {result}")
        return result

    except Exception as e:
        logger.error(f"每日自动标签任务失败: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)


@celery.task(bind=True, queue='jd.celery.first')
def historical_auto_tagging_task(self):
    """历史数据一次性处理任务"""
    try:
        logger.info("开始执行历史数据自动标签任务")

        batch_size = 1000
        chat_offset = 0
        user_offset = 0

        total_processed_chats = 0
        total_processed_users = 0

        # 分批处理聊天记录
        while True:
            chat_records = TgGroupChatHistory.query.offset(chat_offset).limit(batch_size).all()
            if not chat_records:
                break

            batch_processed = 0
            for record in chat_records:
                if record.message:
                    try:
                        AutoTaggingService.process_chat_message(
                            record.message,
                            str(record.user_id),
                            str(record.id)
                        )
                        batch_processed += 1
                    except Exception as e:
                        logger.error(f"处理历史聊天记录失败 ID:{record.id}, 错误:{str(e)}")

            total_processed_chats += batch_processed
            chat_offset += batch_size

            logger.info(f"已处理 {total_processed_chats} 条聊天记录")

            # 避免长时间占用资源
            time.sleep(1)

        # 分批处理用户信息
        while True:
            user_infos = TgGroupUserInfo.query.offset(user_offset).limit(batch_size).all()
            if not user_infos:
                break

            batch_processed = 0
            for user_info in user_infos:
                try:
                    AutoTaggingService.process_user_info(
                        str(user_info.user_id),
                        user_info.nickname,
                        user_info.desc
                    )
                    batch_processed += 1
                except Exception as e:
                    logger.error(f"处理历史用户信息失败 user_id:{user_info.user_id}, 错误:{str(e)}")

            total_processed_users += batch_processed
            user_offset += batch_size

            logger.info(f"已处理 {total_processed_users} 个用户信息")

            # 避免长时间占用资源
            time.sleep(1)

        result = {
            'status': 'success',
            'total_processed_chats': total_processed_chats,
            'total_processed_users': total_processed_users,
            'completed_at': datetime.now().isoformat()
        }

        logger.info(f"历史数据自动标签任务完成: {result}")
        return result

    except Exception as e:
        logger.error(f"历史数据自动标签任务失败: {str(e)}")
        raise self.retry(countdown=60, max_retries=3)
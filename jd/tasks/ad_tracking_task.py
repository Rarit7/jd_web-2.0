"""
广告追踪 BaseTask 任务系统

功能：
1. 每日增量广告追踪任务（定时执行）
2. 历史数据批量处理任务（手动触发）
3. 单条记录处理任务（即时处理）
4. 时间范围处理任务（前端手动触发）

基于 BaseTask 框架实现，支持队列管理和冲突检测
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from jd.tasks.base_task import BaseTask
from jd import app, db
from jd.jobs.ad_tracking_job import AdTrackingJob
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_group import TgGroup
from jd.utils.logging_config import get_logger, PerformanceLogger

logger = get_logger(__name__, {
    'component': 'ad_tracking',
    'module': 'task'
})


class DailyAdTrackingTask(BaseTask):
    """每日广告追踪任务"""

    def __init__(self, target_date: Optional[str] = None):
        """
        初始化每日广告追踪任务

        Args:
            target_date: 目标日期（YYYY-MM-DD格式），默认为昨天
        """
        super().__init__(resource_id='daily_ad_tracking')
        self.target_date = target_date

    def get_job_name(self) -> str:
        """获取任务名称"""
        return 'ad_tracking.daily_task'

    def execute_task(self) -> Dict[str, Any]:
        """执行每日广告追踪任务"""
        perf_logger = PerformanceLogger()
        perf_logger.start('daily_ad_tracking', task_type='daily_ad_tracking')

        try:
            logger.info("启动每日广告追踪任务", extra={
                'extra_fields': {
                    'target_date': self.target_date,
                    'task_id': self.resource_id
                }
            })

            job = AdTrackingJob()

            # 解析日期参数
            if self.target_date:
                date_obj = datetime.strptime(self.target_date, '%Y-%m-%d')
            else:
                date_obj = None

            result = job.run_daily_task(date_obj)

            logger.info("每日广告追踪任务完成", extra={
                'extra_fields': {
                    'target_date': self.target_date,
                    'chat_records': result.get('chat_records_processed', 0),
                    'user_infos': result.get('user_infos_processed', 0),
                    'group_infos': result.get('group_infos_processed', 0),
                    'total_urls': result.get('total_urls', 0),
                    'total_accounts': result.get('total_accounts', 0),
                    'total_items': result.get('total_items', 0),
                    'status': result.get('status')
                }
            })

            perf_logger.end(success=True, **result)

            return {
                'err_code': 0,
                'err_msg': '任务执行完成',
                'payload': result
            }

        except Exception as e:
            logger.error("每日广告追踪任务失败", extra={
                'extra_fields': {
                    'target_date': self.target_date,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            perf_logger.end(success=False, error=str(e))

            return {
                'err_code': 1,
                'err_msg': f'任务执行失败: {str(e)}',
                'exception': str(e)
            }


class DateRangeAdTrackingTask(BaseTask):
    """时间范围广告追踪任务"""

    def __init__(self, start_date: str, end_date: str):
        """
        初始化时间范围广告追踪任务

        Args:
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
        """
        super().__init__(resource_id=f'date_range_{start_date}_{end_date}')
        self.start_date = start_date
        self.end_date = end_date

    def get_job_name(self) -> str:
        """获取任务名称"""
        return 'ad_tracking.date_range_task'

    def execute_task(self) -> Dict[str, Any]:
        """执行时间范围广告追踪任务"""
        perf_logger = PerformanceLogger()
        perf_logger.start('date_range_ad_tracking', start_date=self.start_date, end_date=self.end_date)

        try:
            logger.info("启动时间范围广告追踪任务", extra={
                'extra_fields': {
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'task_id': self.resource_id
                }
            })

            job = AdTrackingJob()

            # 解析日期参数
            start_datetime = datetime.strptime(self.start_date, '%Y-%m-%d').replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_datetime = datetime.strptime(self.end_date, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

            result = {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'chat_records_processed': 0,
                'user_infos_processed': 0,
                'group_infos_processed': 0,
                'total_urls': 0,
                'total_accounts': 0,
                'total_items': 0,
                'errors': 0
            }

            # 处理指定范围内的聊天记录
            chat_records = TgGroupChatHistory.query.filter(
                TgGroupChatHistory.postal_time >= start_datetime,
                TgGroupChatHistory.postal_time <= end_datetime
            ).all()

            logger.info(f"查询到 {len(chat_records)} 条聊天记录", extra={
                'extra_fields': {
                    'record_count': len(chat_records),
                    'start_date': self.start_date,
                    'end_date': self.end_date
                }
            })

            for record in chat_records:
                if self.check_should_stop():
                    logger.warning("任务被中止", extra={'extra_fields': {'reason': 'stop_signal'}})
                    break
                try:
                    stats = job.process_chat_record(record)
                    result['chat_records_processed'] += 1
                    result['total_urls'] += stats['urls']
                    result['total_accounts'] += stats['telegram_accounts']
                    result['total_items'] += stats['total_items']
                except Exception as e:
                    logger.error(f"处理聊天记录失败", extra={
                        'extra_fields': {
                            'record_id': record.id,
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        }
                    })
                    result['errors'] += 1

            # 处理指定范围内更新的用户信息
            user_infos = TgGroupUserInfo.query.filter(
                TgGroupUserInfo.updated_at >= start_datetime,
                TgGroupUserInfo.updated_at <= end_datetime
            ).all()

            logger.info(f"查询到 {len(user_infos)} 条用户信息", extra={
                'extra_fields': {
                    'user_info_count': len(user_infos),
                    'start_date': self.start_date,
                    'end_date': self.end_date
                }
            })

            for user_info in user_infos:
                if self.check_should_stop():
                    logger.warning("任务被中止", extra={'extra_fields': {'reason': 'stop_signal'}})
                    break
                try:
                    stats = job.process_user_info(user_info)
                    result['user_infos_processed'] += 1
                    result['total_urls'] += stats['urls']
                    result['total_accounts'] += stats['telegram_accounts']
                    result['total_items'] += stats['total_items']
                except Exception as e:
                    logger.error(f"处理用户信息失败", extra={
                        'extra_fields': {
                            'user_id': user_info.user_id,
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        }
                    })
                    result['errors'] += 1

            # 处理指定范围内更新的群组信息
            groups = TgGroup.query.filter(
                TgGroup.updated_at >= start_datetime,
                TgGroup.updated_at <= end_datetime
            ).all()

            logger.info(f"查询到 {len(groups)} 个群组", extra={
                'extra_fields': {
                    'group_count': len(groups),
                    'start_date': self.start_date,
                    'end_date': self.end_date
                }
            })

            for group in groups:
                if self.check_should_stop():
                    logger.warning("任务被中止", extra={'extra_fields': {'reason': 'stop_signal'}})
                    break
                try:
                    stats = job.process_group_info(group)
                    result['group_infos_processed'] += 1
                    result['total_urls'] += stats['urls']
                    result['total_accounts'] += stats['telegram_accounts']
                    result['total_items'] += stats['total_items']
                except Exception as e:
                    logger.error(f"处理群组信息失败", extra={
                        'extra_fields': {
                            'chat_id': group.chat_id,
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        }
                    })
                    result['errors'] += 1

            # 提交数据库
            db.session.commit()
            result['status'] = 'success'

            logger.info("时间范围广告追踪任务完成", extra={
                'extra_fields': {
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'chat_records': result['chat_records_processed'],
                    'user_infos': result['user_infos_processed'],
                    'group_infos': result['group_infos_processed'],
                    'total_urls': result['total_urls'],
                    'total_accounts': result['total_accounts'],
                    'total_items': result['total_items'],
                    'errors': result['errors'],
                    'status': result['status']
                }
            })

            perf_logger.end(success=True, **result)

            return {
                'err_code': 0,
                'err_msg': '任务执行完成',
                'payload': result
            }

        except Exception as e:
            db.session.rollback()
            logger.error("时间范围广告追踪任务失败", extra={
                'extra_fields': {
                    'start_date': self.start_date,
                    'end_date': self.end_date,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            perf_logger.end(success=False, error=str(e))

            return {
                'err_code': 1,
                'err_msg': f'任务执行失败: {str(e)}',
                'exception': str(e)
            }


class HistoricalAdTrackingBatchTask(BaseTask):
    """历史数据批量处理任务"""

    def __init__(self, batch_size: int = 1000, max_batches: Optional[int] = None):
        """
        初始化历史数据批量处理任务

        Args:
            batch_size: 每批处理数量
            max_batches: 最大批次数（None表示处理全部）
        """
        super().__init__(resource_id='historical_batch')
        self.batch_size = batch_size
        self.max_batches = max_batches

    def get_job_name(self) -> str:
        """获取任务名称"""
        return 'ad_tracking.historical_batch'

    def execute_task(self) -> Dict[str, Any]:
        """执行历史数据批量处理任务"""
        perf_logger = PerformanceLogger()
        perf_logger.start('historical_ad_tracking_batch', batch_size=self.batch_size, max_batches=self.max_batches)

        try:
            logger.info("启动历史广告追踪批量处理任务", extra={
                'extra_fields': {
                    'batch_size': self.batch_size,
                    'max_batches': self.max_batches,
                    'task_id': self.resource_id
                }
            })

            job = AdTrackingJob()
            result = job.run_historical_batch(self.batch_size, self.max_batches)

            logger.info("历史广告追踪批量处理任务完成", extra={
                'extra_fields': {
                    'batch_size': self.batch_size,
                    'max_batches': self.max_batches,
                    'chat_records': result.get('chat_records_processed', 0),
                    'user_infos': result.get('user_infos_processed', 0),
                    'group_infos': result.get('group_infos_processed', 0),
                    'total_urls': result.get('total_urls', 0),
                    'total_accounts': result.get('total_accounts', 0),
                    'total_items': result.get('total_items', 0),
                    'batches_processed': result.get('batches_processed', 0),
                    'status': result.get('status')
                }
            })

            perf_logger.end(success=True, **result)

            return {
                'err_code': 0,
                'err_msg': '任务执行完成',
                'payload': result
            }

        except Exception as e:
            logger.error("历史广告追踪批量处理任务失败", extra={
                'extra_fields': {
                    'batch_size': self.batch_size,
                    'max_batches': self.max_batches,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            perf_logger.end(success=False, error=str(e))

            return {
                'err_code': 1,
                'err_msg': f'任务执行失败: {str(e)}',
                'exception': str(e)
            }


class ProcessChatRecordTask(BaseTask):
    """处理单条聊天记录任务"""

    def __init__(self, chat_record_id: int):
        """
        初始化处理单条聊天记录任务

        Args:
            chat_record_id: 聊天记录ID
        """
        super().__init__(resource_id=str(chat_record_id))
        self.chat_record_id = chat_record_id

    def get_job_name(self) -> str:
        """获取任务名称"""
        return 'ad_tracking.process_chat_record'

    def execute_task(self) -> Dict[str, Any]:
        """执行处理单条聊天记录任务"""
        perf_logger = PerformanceLogger()
        perf_logger.start('process_chat_record', chat_record_id=self.chat_record_id)

        try:
            logger.info("处理单条聊天记录", extra={
                'extra_fields': {
                    'chat_record_id': self.chat_record_id,
                    'task_id': self.resource_id
                }
            })

            job = AdTrackingJob()
            chat_record = TgGroupChatHistory.query.get(self.chat_record_id)

            if not chat_record:
                logger.warning("聊天记录未找到", extra={
                    'extra_fields': {
                        'chat_record_id': self.chat_record_id
                    }
                })
                return {
                    'err_code': 1,
                    'err_msg': '聊天记录未找到'
                }

            stats = job.process_chat_record(chat_record)
            db.session.commit()

            logger.info("聊天记录处理完成", extra={
                'extra_fields': {
                    'chat_record_id': self.chat_record_id,
                    'urls': stats.get('urls', 0),
                    'telegram_accounts': stats.get('telegram_accounts', 0),
                    'total_items': stats.get('total_items', 0)
                }
            })

            perf_logger.end(success=True, **stats)

            return {
                'err_code': 0,
                'err_msg': '处理完成',
                'payload': {
                    'chat_record_id': self.chat_record_id,
                    'stats': stats
                }
            }

        except Exception as e:
            db.session.rollback()
            logger.error("聊天记录处理失败", extra={
                'extra_fields': {
                    'chat_record_id': self.chat_record_id,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            perf_logger.end(success=False, error=str(e))

            return {
                'err_code': 1,
                'err_msg': f'处理失败: {str(e)}',
                'exception': str(e)
            }


class ProcessUserInfoTask(BaseTask):
    """处理用户信息任务"""

    def __init__(self, user_id: str):
        """
        初始化处理用户信息任务

        Args:
            user_id: 用户ID
        """
        super().__init__(resource_id=user_id)
        self.user_id = user_id

    def get_job_name(self) -> str:
        """获取任务名称"""
        return 'ad_tracking.process_user_info'

    def execute_task(self) -> Dict[str, Any]:
        """执行处理用户信息任务"""
        perf_logger = PerformanceLogger()
        perf_logger.start('process_user_info', user_id=self.user_id)

        try:
            logger.info("处理用户信息", extra={
                'extra_fields': {
                    'user_id': self.user_id,
                    'task_id': self.resource_id
                }
            })

            job = AdTrackingJob()
            user_info = TgGroupUserInfo.query.filter_by(user_id=self.user_id).first()

            if not user_info:
                logger.warning("用户信息未找到", extra={
                    'extra_fields': {
                        'user_id': self.user_id
                    }
                })
                return {
                    'err_code': 1,
                    'err_msg': '用户信息未找到'
                }

            stats = job.process_user_info(user_info)
            db.session.commit()

            logger.info("用户信息处理完成", extra={
                'extra_fields': {
                    'user_id': self.user_id,
                    'urls': stats.get('urls', 0),
                    'telegram_accounts': stats.get('telegram_accounts', 0),
                    'total_items': stats.get('total_items', 0)
                }
            })

            perf_logger.end(success=True, **stats)

            return {
                'err_code': 0,
                'err_msg': '处理完成',
                'payload': {
                    'user_id': self.user_id,
                    'stats': stats
                }
            }

        except Exception as e:
            db.session.rollback()
            logger.error("用户信息处理失败", extra={
                'extra_fields': {
                    'user_id': self.user_id,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            perf_logger.end(success=False, error=str(e))

            return {
                'err_code': 1,
                'err_msg': f'处理失败: {str(e)}',
                'exception': str(e)
            }


class ProcessGroupInfoTask(BaseTask):
    """处理群组信息任务"""

    def __init__(self, chat_id: str):
        """
        初始化处理群组信息任务

        Args:
            chat_id: 群组ID
        """
        super().__init__(resource_id=chat_id)
        self.chat_id = chat_id

    def get_job_name(self) -> str:
        """获取任务名称"""
        return 'ad_tracking.process_group_info'

    def execute_task(self) -> Dict[str, Any]:
        """执行处理群组信息任务"""
        perf_logger = PerformanceLogger()
        perf_logger.start('process_group_info', chat_id=self.chat_id)

        try:
            logger.info("处理群组信息", extra={
                'extra_fields': {
                    'chat_id': self.chat_id,
                    'task_id': self.resource_id
                }
            })

            job = AdTrackingJob()
            group = TgGroup.query.filter_by(chat_id=self.chat_id).first()

            if not group:
                logger.warning("群组信息未找到", extra={
                    'extra_fields': {
                        'chat_id': self.chat_id
                    }
                })
                return {
                    'err_code': 1,
                    'err_msg': '群组信息未找到'
                }

            stats = job.process_group_info(group)
            db.session.commit()

            logger.info("群组信息处理完成", extra={
                'extra_fields': {
                    'chat_id': self.chat_id,
                    'urls': stats.get('urls', 0),
                    'telegram_accounts': stats.get('telegram_accounts', 0),
                    'total_items': stats.get('total_items', 0)
                }
            })

            perf_logger.end(success=True, **stats)

            return {
                'err_code': 0,
                'err_msg': '处理完成',
                'payload': {
                    'chat_id': self.chat_id,
                    'stats': stats
                }
            }

        except Exception as e:
            db.session.rollback()
            logger.error("群组信息处理失败", extra={
                'extra_fields': {
                    'chat_id': self.chat_id,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            perf_logger.end(success=False, error=str(e))

            return {
                'err_code': 1,
                'err_msg': f'处理失败: {str(e)}',
                'exception': str(e)
            }


# ============================================================================
# Celery 包装器 - 将 BaseTask 实例包装成 Celery 任务
# ============================================================================

from scripts.worker import celery


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.daily_task')
def daily_ad_tracking_task(self, target_date: str = None) -> Dict[str, Any]:
    """
    每日广告追踪任务 (Celery 包装器)

    Args:
        target_date: 目标日期（YYYY-MM-DD格式），默认为昨天

    Returns:
        执行结果统计
    """
    try:
        logger.info("Celery 每日广告追踪任务启动", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'target_date': target_date,
                'retry': self.request.retries
            }
        })

        with app.app_context():
            task = DailyAdTrackingTask(target_date=target_date)
            result = task.start_task()

            logger.info("Celery 每日广告追踪任务完成", extra={
                'extra_fields': {
                    'task_id': self.request.id,
                    'target_date': target_date,
                    'result': result.get('err_code', 'unknown')
                }
            })

            return result

    except Exception as e:
        logger.error("Celery 每日广告追踪任务失败，准备重试", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'target_date': target_date,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'retry_count': self.request.retries,
                'max_retries': 3
            }
        }, exc_info=True)
        raise self.retry(countdown=300, max_retries=3, exc=e)


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.date_range_task')
def date_range_ad_tracking_task(self, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    时间范围广告追踪任务 (Celery 包装器)

    Args:
        start_date: 开始日期（YYYY-MM-DD格式）
        end_date: 结束日期（YYYY-MM-DD格式）

    Returns:
        执行结果统计
    """
    try:
        logger.info("Celery 时间范围广告追踪任务启动", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'start_date': start_date,
                'end_date': end_date,
                'retry': self.request.retries
            }
        })

        with app.app_context():
            task = DateRangeAdTrackingTask(start_date=start_date, end_date=end_date)
            result = task.start_task()

            logger.info("Celery 时间范围广告追踪任务完成", extra={
                'extra_fields': {
                    'task_id': self.request.id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'result': result.get('err_code', 'unknown')
                }
            })

            return result

    except Exception as e:
        logger.error("Celery 时间范围广告追踪任务失败，准备重试", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'start_date': start_date,
                'end_date': end_date,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'retry_count': self.request.retries,
                'max_retries': 3
            }
        }, exc_info=True)
        raise self.retry(countdown=300, max_retries=3, exc=e)


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.historical_batch')
def historical_ad_tracking_batch_task(self, batch_size: int = 1000, max_batches: int = None) -> Dict[str, Any]:
    """
    历史数据批量处理任务 (Celery 包装器)

    Args:
        batch_size: 每批处理数量
        max_batches: 最大批次数（None表示处理全部）

    Returns:
        执行结果统计
    """
    try:
        logger.info("Celery 历史广告追踪批量处理任务启动", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'batch_size': batch_size,
                'max_batches': max_batches
            }
        })

        with app.app_context():
            task = HistoricalAdTrackingBatchTask(batch_size=batch_size, max_batches=max_batches)
            result = task.start_task()

            logger.info("Celery 历史广告追踪批量处理任务完成", extra={
                'extra_fields': {
                    'task_id': self.request.id,
                    'batch_size': batch_size,
                    'max_batches': max_batches,
                    'result': result.get('err_code', 'unknown')
                }
            })

            return result

    except Exception as e:
        logger.error("Celery 历史广告追踪批量处理任务失败", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'batch_size': batch_size,
                'max_batches': max_batches,
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        }, exc_info=True)
        raise


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.process_chat_record')
def process_chat_record_task(self, chat_record_id: int) -> Dict[str, Any]:
    """
    处理单条聊天记录任务 (Celery 包装器)

    Args:
        chat_record_id: 聊天记录ID

    Returns:
        处理结果
    """
    try:
        logger.info("Celery 处理聊天记录任务启动", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'chat_record_id': chat_record_id,
                'retry': self.request.retries
            }
        })

        with app.app_context():
            task = ProcessChatRecordTask(chat_record_id=chat_record_id)
            result = task.start_task()

            logger.info("Celery 处理聊天记录任务完成", extra={
                'extra_fields': {
                    'task_id': self.request.id,
                    'chat_record_id': chat_record_id,
                    'result': result.get('err_code', 'unknown')
                }
            })

            return result

    except Exception as e:
        logger.error("Celery 处理聊天记录任务失败，准备重试", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'chat_record_id': chat_record_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'retry_count': self.request.retries,
                'max_retries': 3
            }
        }, exc_info=True)
        raise self.retry(countdown=60, max_retries=3, exc=e)


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.process_user_info')
def process_user_info_task(self, user_id: str) -> Dict[str, Any]:
    """
    处理用户信息任务 (Celery 包装器)

    Args:
        user_id: 用户ID

    Returns:
        处理结果
    """
    try:
        logger.info("Celery 处理用户信息任务启动", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'user_id': user_id,
                'retry': self.request.retries
            }
        })

        with app.app_context():
            task = ProcessUserInfoTask(user_id=user_id)
            result = task.start_task()

            logger.info("Celery 处理用户信息任务完成", extra={
                'extra_fields': {
                    'task_id': self.request.id,
                    'user_id': user_id,
                    'result': result.get('err_code', 'unknown')
                }
            })

            return result

    except Exception as e:
        logger.error("Celery 处理用户信息任务失败，准备重试", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'user_id': user_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'retry_count': self.request.retries,
                'max_retries': 3
            }
        }, exc_info=True)
        raise self.retry(countdown=60, max_retries=3, exc=e)


@celery.task(bind=True, queue='jd.celery.first', name='ad_tracking.process_group_info')
def process_group_info_task(self, chat_id: str) -> Dict[str, Any]:
    """
    处理群组信息任务 (Celery 包装器)

    Args:
        chat_id: 群组ID

    Returns:
        处理结果
    """
    try:
        logger.info("Celery 处理群组信息任务启动", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'chat_id': chat_id,
                'retry': self.request.retries
            }
        })

        with app.app_context():
            task = ProcessGroupInfoTask(chat_id=chat_id)
            result = task.start_task()

            logger.info("Celery 处理群组信息任务完成", extra={
                'extra_fields': {
                    'task_id': self.request.id,
                    'chat_id': chat_id,
                    'result': result.get('err_code', 'unknown')
                }
            })

            return result

    except Exception as e:
        logger.error("Celery 处理群组信息任务失败，准备重试", extra={
            'extra_fields': {
                'task_id': self.request.id,
                'chat_id': chat_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'retry_count': self.request.retries,
                'max_retries': 3
            }
        }, exc_info=True)
        raise self.retry(countdown=60, max_retries=3, exc=e)


# ============================================================================
# 定时任务配置参考
# ============================================================================
"""
beat_schedule 配置示例（在 scripts/celeryconfig.py 的 beat_schedule 中配置）：

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
   POST /api/ad-tracking/trigger
   {
     "task_type": "daily",
     "target_date": "2025-10-19"
   }

2. 时间范围处理（处理指定范围的内容）:
   POST /api/ad-tracking/trigger
   {
     "task_type": "date_range",
     "start_date": "2025-10-10",
     "end_date": "2025-10-19"
   }

3. 历史数据批量处理：
   POST /api/ad-tracking/trigger
   {
     "task_type": "historical_batch",
     "batch_size": 1000,
     "max_batches": null
   }

使用 BaseTask 的优势：
- 自动的队列管理和冲突检测
- 防止资源冲突导致的重复处理
- 支持等待队列模式，避免立即返回失败
- 任务执行状态跟踪
- 任务停止能力
- 统一的错误处理和结果格式
"""

# -*- coding: utf-8 -*-
"""
广告分析每日统计任务 - Celery 定时任务

功能：
- 每天凌晨 2:00 自动执行
- 计算前一天的各类统计数据（黑词、交易方式、价格、地理位置）
- 保存到 MySQL 统计表
- 完全替代 Redis 缓存方案
"""

from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional

from jd.tasks.base_task import BaseTask
from jd import app, db, celery
from jd.services.daily_stats_computation_service import DailyStatsComputationService
from jd.models.ad_tracking_daily_stats import (
    AdTrackingDarkKeywordDailyStats,
    AdTrackingTransactionMethodDailyStats,
    AdTrackingPriceDailyStats,
    AdTrackingGeoLocationDailyStats
)
from jd.utils.logging_config import get_logger, PerformanceLogger

logger = get_logger(__name__, {
    'component': 'ad_analysis',
    'module': 'daily_stats_task'
})


class AdAnalysisDailyStatsTask(BaseTask):
    """
    广告分析每日统计任务

    负责计算前一天的统计数据并保存到数据库
    """

    def __init__(self, target_date: Optional[date] = None):
        """
        初始化任务

        Args:
            target_date: 目标统计日期（date对象），默认为昨天
        """
        super().__init__(resource_id='ad_analysis_daily_stats')
        # 如果没有指定日期，默认为昨天
        self.target_date = target_date or (datetime.now() - timedelta(days=1)).date()

    def get_job_name(self) -> str:
        """获取任务名称"""
        return 'ad_analysis.daily_stats'

    def execute_task(self) -> Dict[str, Any]:
        """
        执行每日统计任务

        流程：
        1. 计算黑词统计 → upsert → commit
        2. 计算交易方式统计 → upsert → commit
        3. 计算价格统计 → upsert → commit
        4. 计算地理位置统计 → upsert → commit
        5. 返回汇总结果
        """
        perf_logger = PerformanceLogger()
        perf_logger.start('ad_analysis_daily_stats', task_type='ad_analysis_daily_stats')

        try:
            logger.info("启动广告分析每日统计任务", extra={
                'extra_fields': {
                    'target_date': self.target_date.isoformat(),
                    'task_id': self.resource_id
                }
            })

            summary = self._compute_and_save_all_stats()

            logger.info("广告分析每日统计任务完成", extra={
                'extra_fields': {
                    'target_date': self.target_date.isoformat(),
                    'summary': summary
                }
            })

            perf_logger.end(success=True, **summary)

            return {
                'err_code': 0,
                'err_msg': '每日统计计算完成',
                'payload': {
                    'target_date': self.target_date.isoformat(),
                    'summary': summary
                }
            }

        except Exception as e:
            logger.error("广告分析每日统计任务失败", extra={
                'extra_fields': {
                    'target_date': self.target_date.isoformat(),
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            }, exc_info=True)
            perf_logger.end(success=False, error=str(e))

            return {
                'err_code': 1,
                'err_msg': f'每日统计计算失败: {str(e)}',
                'payload': {}
            }

    def _compute_and_save_all_stats(self) -> Dict[str, Any]:
        """
        计算并保存所有类型的统计数据

        Returns:
            dict: 统计摘要
        """
        summary = {}

        # 1. 黑词统计
        logger.info(f"计算黑词统计: {self.target_date}")
        dark_stats = DailyStatsComputationService.compute_dark_keyword_stats(self.target_date)
        inserted, updated = DailyStatsComputationService.upsert_stats(
            dark_stats, AdTrackingDarkKeywordDailyStats
        )
        db.session.commit()
        summary['dark_keyword'] = {
            'inserted': inserted,
            'updated': updated,
            'total': len(dark_stats)
        }
        logger.info(f"黑词统计完成: {summary['dark_keyword']}")

        # 2. 交易方式统计
        logger.info(f"计算交易方式统计: {self.target_date}")
        transaction_stats = DailyStatsComputationService.compute_transaction_method_stats(self.target_date)
        inserted, updated = DailyStatsComputationService.upsert_stats(
            transaction_stats, AdTrackingTransactionMethodDailyStats
        )
        db.session.commit()
        summary['transaction_method'] = {
            'inserted': inserted,
            'updated': updated,
            'total': len(transaction_stats)
        }
        logger.info(f"交易方式统计完成: {summary['transaction_method']}")

        # 3. 价格统计
        logger.info(f"计算价格统计: {self.target_date}")
        price_stats = DailyStatsComputationService.compute_price_stats(self.target_date)
        inserted, updated = DailyStatsComputationService.upsert_stats(
            price_stats, AdTrackingPriceDailyStats
        )
        db.session.commit()
        summary['price'] = {
            'inserted': inserted,
            'updated': updated,
            'total': len(price_stats)
        }
        logger.info(f"价格统计完成: {summary['price']}")

        # 4. 地理位置统计
        logger.info(f"计算地理位置统计: {self.target_date}")
        geo_stats = DailyStatsComputationService.compute_geo_location_stats(self.target_date)
        inserted, updated = DailyStatsComputationService.upsert_stats(
            geo_stats, AdTrackingGeoLocationDailyStats
        )
        db.session.commit()
        summary['geo_location'] = {
            'inserted': inserted,
            'updated': updated,
            'total': len(geo_stats)
        }
        logger.info(f"地理位置统计完成: {summary['geo_location']}")

        return summary


# ============================================================================
# Celery 任务定义和包装器
# ============================================================================

@celery.task(bind=True, queue='jd.celery.first')
def compute_ad_analysis_daily_stats(self, target_date_str: Optional[str] = None):
    """
    Celery 包装函数 - 计算广告分析每日统计

    Args:
        self: Celery task instance
        target_date_str: 目标统计日期（YYYY-MM-DD格式），默认为昨天

    Returns:
        dict: 任务执行结果
    """
    try:
        # 解析日期参数
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        else:
            target_date = None

        # 创建任务实例并执行
        task = AdAnalysisDailyStatsTask(target_date=target_date)
        result = task.execute_task()

        return result

    except Exception as e:
        logger.error(f"Celery 任务执行失败: {str(e)}", exc_info=True)
        return {
            'err_code': 1,
            'err_msg': f'任务执行失败: {str(e)}',
            'payload': {}
        }

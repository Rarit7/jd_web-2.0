# -*- coding: utf-8 -*-
"""
广告分析每日统计数据回填脚本

功能：
1. 自动检测源表数据日期范围
2. 按日期循环计算统计
3. 批量提交（每 N 天提交一次）
4. 进度显示
5. 错误处理和回滚

使用方法：
    # 回填全部历史数据（自动检测日期范围）
    python -m utils.backfill_ad_analysis_daily_stats

    # 指定日期范围
    python -m utils.backfill_ad_analysis_daily_stats --start-date 2025-01-01 --end-date 2026-01-09

    # 指定批量提交大小
    python -m utils.backfill_ad_analysis_daily_stats --batch-size 20
"""

import logging
import sys
from datetime import datetime, timedelta, date
from typing import Optional, Tuple

import click
from sqlalchemy import func

from jd import db, app
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeyword
from jd.models.ad_tracking_transaction_method import AdTrackingTransactionMethod
from jd.models.ad_tracking_price import AdTrackingPrice
from jd.models.ad_tracking_geo_location import AdTrackingGeoLocation
from jd.services.daily_stats_computation_service import DailyStatsComputationService
from jd.models.ad_tracking_daily_stats import (
    AdTrackingDarkKeywordDailyStats,
    AdTrackingTransactionMethodDailyStats,
    AdTrackingPriceDailyStats,
    AdTrackingGeoLocationDailyStats
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdAnalysisBackfiller:
    """广告分析数据回填工具"""

    def __init__(self, app):
        self.app = app
        self.app_context = app.app_context()
        self.app_context.push()
        logger.info("应用上下文已初始化")

    def get_date_range_from_source_tables(self) -> Tuple[Optional[date], Optional[date]]:
        """
        查询源表的最早和最晚 msg_date

        Returns:
            Tuple[date, date]: (最早日期, 最晚日期)
        """
        logger.info("检测源表数据日期范围...")

        min_dates = []
        max_dates = []

        try:
            # 检查 ad_tracking_dark_keyword
            result = db.session.query(
                func.min(AdTrackingDarkKeyword.msg_date),
                func.max(AdTrackingDarkKeyword.msg_date)
            ).first()
            if result[0]:
                min_dates.append(result[0])
                max_dates.append(result[1])
                logger.info(f"  黑词表: {result[0]} ~ {result[1]}")

            # 检查 ad_tracking_transaction_method
            result = db.session.query(
                func.min(AdTrackingTransactionMethod.msg_date),
                func.max(AdTrackingTransactionMethod.msg_date)
            ).first()
            if result[0]:
                min_dates.append(result[0])
                max_dates.append(result[1])
                logger.info(f"  交易方式表: {result[0]} ~ {result[1]}")

            # 检查 ad_tracking_price
            result = db.session.query(
                func.min(AdTrackingPrice.msg_date),
                func.max(AdTrackingPrice.msg_date)
            ).first()
            if result[0]:
                min_dates.append(result[0])
                max_dates.append(result[1])
                logger.info(f"  价格表: {result[0]} ~ {result[1]}")

            # 检查 ad_tracking_geo_location
            result = db.session.query(
                func.min(AdTrackingGeoLocation.msg_date),
                func.max(AdTrackingGeoLocation.msg_date)
            ).first()
            if result[0]:
                min_dates.append(result[0])
                max_dates.append(result[1])
                logger.info(f"  地理位置表: {result[0]} ~ {result[1]}")

        except Exception as e:
            logger.error(f"查询源表失败: {e}")
            return None, None

        if not min_dates or not max_dates:
            logger.warning("源表中没有数据")
            return None, None

        min_date = min(min_dates)
        max_date = max(max_dates)

        logger.info(f"检测到数据范围: {min_date} ~ {max_date}")
        return min_date, max_date

    def backfill_stats(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        batch_size: int = 10
    ) -> dict:
        """
        循环计算每天的统计数据并插入

        Args:
            start_date: 开始日期，默认自动检测
            end_date: 结束日期，默认自动检测
            batch_size: 每次提交的日期数

        Returns:
            dict: 统计摘要
        """
        # 自动检测日期范围
        if not start_date or not end_date:
            detected_start, detected_end = self.get_date_range_from_source_tables()
            if not detected_start or not detected_end:
                logger.error("无法检测数据范围，请手动指定")
                return {}
            start_date = start_date or detected_start
            end_date = end_date or detected_end

        logger.info(f"开始回填数据: {start_date} ~ {end_date}, 批大小: {batch_size}")

        total_summary = {
            'dark_keyword': {'inserted': 0, 'updated': 0, 'total': 0},
            'transaction_method': {'inserted': 0, 'updated': 0, 'total': 0},
            'price': {'inserted': 0, 'updated': 0, 'total': 0},
            'geo_location': {'inserted': 0, 'updated': 0, 'total': 0}
        }

        current_date = start_date
        batch_count = 0

        try:
            while current_date <= end_date:
                logger.info(f"处理日期: {current_date}")

                # 1. 黑词统计
                dark_stats = DailyStatsComputationService.compute_dark_keyword_stats(current_date)
                inserted, updated = DailyStatsComputationService.upsert_stats(
                    dark_stats, AdTrackingDarkKeywordDailyStats
                )
                total_summary['dark_keyword']['inserted'] += inserted
                total_summary['dark_keyword']['updated'] += updated
                total_summary['dark_keyword']['total'] += len(dark_stats)

                # 2. 交易方式统计
                transaction_stats = DailyStatsComputationService.compute_transaction_method_stats(current_date)
                inserted, updated = DailyStatsComputationService.upsert_stats(
                    transaction_stats, AdTrackingTransactionMethodDailyStats
                )
                total_summary['transaction_method']['inserted'] += inserted
                total_summary['transaction_method']['updated'] += updated
                total_summary['transaction_method']['total'] += len(transaction_stats)

                # 3. 价格统计
                price_stats = DailyStatsComputationService.compute_price_stats(current_date)
                inserted, updated = DailyStatsComputationService.upsert_stats(
                    price_stats, AdTrackingPriceDailyStats
                )
                total_summary['price']['inserted'] += inserted
                total_summary['price']['updated'] += updated
                total_summary['price']['total'] += len(price_stats)

                # 4. 地理位置统计
                geo_stats = DailyStatsComputationService.compute_geo_location_stats(current_date)
                inserted, updated = DailyStatsComputationService.upsert_stats(
                    geo_stats, AdTrackingGeoLocationDailyStats
                )
                total_summary['geo_location']['inserted'] += inserted
                total_summary['geo_location']['updated'] += updated
                total_summary['geo_location']['total'] += len(geo_stats)

                # 更新批计数器
                batch_count += 1

                # 每 batch_size 天提交一次
                if batch_count >= batch_size:
                    db.session.commit()
                    logger.info(f"批量提交完成 ({batch_count} 天)")
                    batch_count = 0

                current_date += timedelta(days=1)

            # 最后一批提交
            if batch_count > 0:
                db.session.commit()
                logger.info(f"最后批量提交完成 ({batch_count} 天)")

            logger.info("回填完成！统计摘要:")
            logger.info(f"  黑词: 插入 {total_summary['dark_keyword']['inserted']}, "
                       f"更新 {total_summary['dark_keyword']['updated']}, "
                       f"总计 {total_summary['dark_keyword']['total']}")
            logger.info(f"  交易方式: 插入 {total_summary['transaction_method']['inserted']}, "
                       f"更新 {total_summary['transaction_method']['updated']}, "
                       f"总计 {total_summary['transaction_method']['total']}")
            logger.info(f"  价格: 插入 {total_summary['price']['inserted']}, "
                       f"更新 {total_summary['price']['updated']}, "
                       f"总计 {total_summary['price']['total']}")
            logger.info(f"  地理位置: 插入 {total_summary['geo_location']['inserted']}, "
                       f"更新 {total_summary['geo_location']['updated']}, "
                       f"总计 {total_summary['geo_location']['total']}")

            return total_summary

        except Exception as e:
            logger.error(f"回填失败: {e}", exc_info=True)
            logger.info("回滚未提交的更改...")
            db.session.rollback()
            raise

    def cleanup(self):
        """清理资源"""
        self.app_context.pop()


@click.command()
@click.option(
    '--start-date',
    type=click.STRING,
    default=None,
    help='开始日期（YYYY-MM-DD 格式），默认自动检测'
)
@click.option(
    '--end-date',
    type=click.STRING,
    default=None,
    help='结束日期（YYYY-MM-DD 格式），默认自动检测'
)
@click.option(
    '--batch-size',
    type=int,
    default=10,
    help='批量提交的日期数（默认10）'
)
def main(start_date, end_date, batch_size):
    """
    回填广告分析每日统计数据

    示例:
        python -m utils.backfill_ad_analysis_daily_stats
        python -m utils.backfill_ad_analysis_daily_stats --start-date 2025-01-01
        python -m utils.backfill_ad_analysis_daily_stats --batch-size 20
    """
    try:
        # 初始化 Flask 应用
        app.ready(db_switch=True, web_switch=False, worker_switch=False)

        # 解析日期参数
        parsed_start_date = None
        parsed_end_date = None

        if start_date:
            parsed_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            parsed_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # 执行回填
        backfiller = AdAnalysisBackfiller(app)
        result = backfiller.backfill_stats(
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            batch_size=batch_size
        )
        backfiller.cleanup()

        logger.info("回填脚本完成")
        sys.exit(0)

    except Exception as e:
        logger.error(f"脚本执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

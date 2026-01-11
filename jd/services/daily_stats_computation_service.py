# -*- coding: utf-8 -*-
"""
每日统计计算服务 - 负责计算并生成日度统计数据
从源表聚合数据，生成统计对象，由任务层处理提交
"""

import logging
from datetime import date
from typing import List, Tuple

from sqlalchemy import func

from jd import db
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeyword
from jd.models.ad_tracking_transaction_method import AdTrackingTransactionMethod
from jd.models.ad_tracking_price import AdTrackingPrice
from jd.models.ad_tracking_geo_location import AdTrackingGeoLocation
from jd.models.ad_tracking_daily_stats import (
    AdTrackingDarkKeywordDailyStats,
    AdTrackingTransactionMethodDailyStats,
    AdTrackingPriceDailyStats,
    AdTrackingGeoLocationDailyStats
)

logger = logging.getLogger(__name__)


class DailyStatsComputationService:
    """
    每日统计计算服务

    负责：
    1. 计算各类统计数据
    2. 返回统计对象列表（不提交数据库）
    3. 处理 upsert 逻辑（插入或更新）

    注意：本服务遵循架构规则，不进行数据库提交
    """

    @staticmethod
    def compute_dark_keyword_stats(stat_date: date) -> List[AdTrackingDarkKeywordDailyStats]:
        """
        计算黑词每日统计（全局，不按 chat_id 分组）

        Args:
            stat_date: 统计日期

        Returns:
            List[AdTrackingDarkKeywordDailyStats]: 统计记录列表
        """
        logger.info(f"计算黑词统计: date={stat_date}")
        stats_records = []

        try:
            # 全局统计：聚合所有群组的黑词数据
            results = db.session.query(
                AdTrackingDarkKeyword.drug_id,
                AdTrackingDarkKeyword.category_id,
                func.sum(AdTrackingDarkKeyword.count).label('keyword_count'),
                func.count(func.distinct(AdTrackingDarkKeyword.message_id)).label('message_count')
            ).filter(
                AdTrackingDarkKeyword.msg_date == stat_date
            ).group_by(
                AdTrackingDarkKeyword.drug_id,
                AdTrackingDarkKeyword.category_id
            ).all()

            for drug_id, category_id, keyword_count, message_count in results:
                stat = AdTrackingDarkKeywordDailyStats(
                    stat_date=stat_date,
                    drug_id=drug_id,
                    category_id=category_id,
                    keyword_count=int(keyword_count or 0),
                    message_count=int(message_count or 0)
                )
                stats_records.append(stat)

            logger.info(f"黑词统计计算完成: {len(stats_records)} 条记录")
        except Exception as e:
            logger.error(f"黑词统计计算失败: {e}")
            raise

        return stats_records

    @staticmethod
    def compute_transaction_method_stats(stat_date: date) -> List[AdTrackingTransactionMethodDailyStats]:
        """
        计算交易方式每日统计（全局，不按 chat_id 分组）

        Args:
            stat_date: 统计日期

        Returns:
            List[AdTrackingTransactionMethodDailyStats]: 统计记录列表
        """
        logger.info(f"计算交易方式统计: date={stat_date}")
        stats_records = []

        try:
            # 全局统计：聚合所有群组的交易方式数据
            results = db.session.query(
                AdTrackingTransactionMethod.method,
                AdTrackingTransactionMethod.tag_id,
                func.count().label('record_count')
            ).filter(
                AdTrackingTransactionMethod.msg_date == stat_date
            ).group_by(
                AdTrackingTransactionMethod.method,
                AdTrackingTransactionMethod.tag_id
            ).all()

            for method, tag_id, record_count in results:
                stat = AdTrackingTransactionMethodDailyStats(
                    stat_date=stat_date,
                    method=method,
                    tag_id=tag_id,
                    record_count=int(record_count or 0)
                )
                stats_records.append(stat)

            logger.info(f"交易方式统计计算完成: {len(stats_records)} 条记录")
        except Exception as e:
            logger.error(f"交易方式统计计算失败: {e}")
            raise

        return stats_records

    @staticmethod
    def compute_price_stats(stat_date: date) -> List[AdTrackingPriceDailyStats]:
        """
        计算价格每日统计（全局，不按 chat_id 分组）

        Args:
            stat_date: 统计日期

        Returns:
            List[AdTrackingPriceDailyStats]: 统计记录列表
        """
        logger.info(f"计算价格统计: date={stat_date}")
        stats_records = []

        try:
            # 全局统计：聚合所有群组的价格数据
            results = db.session.query(
                AdTrackingPrice.unit,
                func.avg(AdTrackingPrice.price_value).label('avg_price'),
                func.min(AdTrackingPrice.price_value).label('min_price'),
                func.max(AdTrackingPrice.price_value).label('max_price'),
                func.count().label('record_count')
            ).filter(
                AdTrackingPrice.msg_date == stat_date
            ).group_by(
                AdTrackingPrice.unit
            ).all()

            for unit, avg_price, min_price, max_price, record_count in results:
                stat = AdTrackingPriceDailyStats(
                    stat_date=stat_date,
                    unit=unit,
                    avg_price=float(avg_price or 0.0),
                    min_price=float(min_price or 0.0),
                    max_price=float(max_price or 0.0),
                    record_count=int(record_count or 0)
                )
                stats_records.append(stat)

            logger.info(f"价格统计计算完成: {len(stats_records)} 条记录")
        except Exception as e:
            logger.error(f"价格统计计算失败: {e}")
            raise

        return stats_records

    @staticmethod
    def compute_geo_location_stats(stat_date: date) -> List[AdTrackingGeoLocationDailyStats]:
        """
        计算地理位置每日统计（全局，不按 chat_id 分组）

        Args:
            stat_date: 统计日期

        Returns:
            List[AdTrackingGeoLocationDailyStats]: 统计记录列表
        """
        logger.info(f"计算地理位置统计: date={stat_date}")
        stats_records = []

        try:
            # 全局统计：聚合所有群组的地理位置数据
            results = db.session.query(
                AdTrackingGeoLocation.province,
                AdTrackingGeoLocation.city,
                func.count().label('record_count')
            ).filter(
                AdTrackingGeoLocation.msg_date == stat_date
            ).group_by(
                AdTrackingGeoLocation.province,
                AdTrackingGeoLocation.city
            ).all()

            for province, city, record_count in results:
                stat = AdTrackingGeoLocationDailyStats(
                    stat_date=stat_date,
                    province=province,
                    city=city,
                    record_count=int(record_count or 0)
                )
                stats_records.append(stat)

            logger.info(f"地理位置统计计算完成: {len(stats_records)} 条记录")
        except Exception as e:
            logger.error(f"地理位置统计计算失败: {e}")
            raise

        return stats_records

    @staticmethod
    def upsert_stats(stats_records: List, model_class) -> Tuple[int, int]:
        """
        批量 upsert 统计记录（插入或更新）

        采用 INSERT ... ON DUPLICATE KEY UPDATE 策略
        这是服务层的纯业务逻辑，由任务层负责提交

        Args:
            stats_records: 统计记录列表
            model_class: 统计模型类

        Returns:
            Tuple[int, int]: (插入数, 更新数)
        """
        if not stats_records:
            logger.info(f"无统计记录需要处理: {model_class.__name__}")
            return 0, 0

        logger.info(f"开始 upsert {model_class.__name__}: {len(stats_records)} 条记录")

        try:
            # 获取表名和主键列
            table_name = model_class.__tablename__

            # 注意：由于这是服务层，我们不能直接提交
            # 这个方法返回需要插入/更新的对象
            # 任务层会处理批量操作和提交

            # 对于每条记录，检查是否存在
            inserted_count = 0
            updated_count = 0

            for stat_record in stats_records:
                # 根据唯一键查找既有记录
                existing = _find_existing_stat(stat_record, model_class)

                if existing:
                    # 更新既有记录
                    _update_existing_stat(existing, stat_record, model_class)
                    updated_count += 1
                else:
                    # 标记为新插入
                    inserted_count += 1
                    # 将记录添加到会话（不提交）
                    db.session.add(stat_record)

            logger.info(f"upsert 完成: {inserted_count} 插入, {updated_count} 更新")
            return inserted_count, updated_count

        except Exception as e:
            logger.error(f"upsert 失败: {e}")
            raise

    @staticmethod
    def batch_upsert_stats(stats_list: List[Tuple[List, type]]) -> dict:
        """
        批量处理多类统计的 upsert

        Args:
            stats_list: [(记录列表, 模型类), ...] 列表

        Returns:
            dict: 包含各类统计的插入/更新数量统计
        """
        summary = {}

        for stats_records, model_class in stats_list:
            inserted, updated = DailyStatsComputationService.upsert_stats(stats_records, model_class)
            summary[model_class.__tablename__] = {
                'inserted': inserted,
                'updated': updated
            }

        return summary


# ============================================================================
# 辅助函数（私有）
# ============================================================================

def _find_existing_stat(stat_record, model_class):
    """
    根据唯一键查找既有统计记录

    Returns:
        existing record or None
    """
    if model_class == AdTrackingDarkKeywordDailyStats:
        return model_class.query.filter_by(
            stat_date=stat_record.stat_date,
            drug_id=stat_record.drug_id,
            category_id=stat_record.category_id
        ).first()
    elif model_class == AdTrackingTransactionMethodDailyStats:
        return model_class.query.filter_by(
            stat_date=stat_record.stat_date,
            method=stat_record.method,
            tag_id=stat_record.tag_id
        ).first()
    elif model_class == AdTrackingPriceDailyStats:
        return model_class.query.filter_by(
            stat_date=stat_record.stat_date,
            unit=stat_record.unit
        ).first()
    elif model_class == AdTrackingGeoLocationDailyStats:
        return model_class.query.filter_by(
            stat_date=stat_record.stat_date,
            province=stat_record.province,
            city=stat_record.city
        ).first()
    return None


def _update_existing_stat(existing_record, new_record, model_class):
    """
    更新既有统计记录的值
    """
    if model_class == AdTrackingDarkKeywordDailyStats:
        existing_record.keyword_count = new_record.keyword_count
        existing_record.message_count = new_record.message_count
    elif model_class == AdTrackingTransactionMethodDailyStats:
        existing_record.record_count = new_record.record_count
    elif model_class == AdTrackingPriceDailyStats:
        existing_record.avg_price = new_record.avg_price
        existing_record.min_price = new_record.min_price
        existing_record.max_price = new_record.max_price
        existing_record.record_count = new_record.record_count
    elif model_class == AdTrackingGeoLocationDailyStats:
        existing_record.record_count = new_record.record_count

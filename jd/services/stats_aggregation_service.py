"""
统计聚合服务 - 负责各类统计数据的查询和聚合

注意：
- 从 MySQL 统计表查询聚合数据（全局统计，不区分 chat_id）
- 不再使用 Redis 缓存
- API 参数保持兼容性（chat_id 参数被接受但忽略）
- use_cache 参数被接受但忽略（数据直接从 MySQL 统计表获取）
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import func, text

from jd import db
from jd.helpers.geo_helper import normalize_province_name, normalize_provinces_list, normalize_cities_with_provinces
from jd.models.ad_tracking_price import AdTrackingPrice
from jd.models.ad_tracking_transaction_method import AdTrackingTransactionMethod
from jd.models.ad_tracking_geo_location import AdTrackingGeoLocation
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeyword
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeywordDrug
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeywordCategory
from jd.models.ad_tracking_daily_stats import (
    AdTrackingDarkKeywordDailyStats,
    AdTrackingTransactionMethodDailyStats,
    AdTrackingPriceDailyStats,
    AdTrackingGeoLocationDailyStats
)

logger = logging.getLogger(__name__)


class StatsAggregationService:
    """
    统计聚合服务 - 负责各类统计数据的查询和聚合

    迁移说明：
    - 饼图和趋势线数据从 MySQL 统计表聚合（全局统计）
    - 表格数据从源表查询（显示详细记录）
    - 忽略 chat_id 参数（完全兼容前端调用）
    - 移除所有 Redis 缓存逻辑
    """

    @staticmethod
    def get_dark_keywords_stats(
        chat_id: Optional[int] = None,
        tag_ids: Optional[List[int]] = None,
        days: int = 365,
        use_cache: bool = True
    ) -> Dict:
        """
        获取黑词分析统计（全局统计，忽略 chat_id）

        Args:
            chat_id: 群组ID（已弃用，用于 API 兼容性）
            tag_ids: 标签ID列表（已弃用，用于 API 兼容性）
            days: 统计天数
            use_cache: 是否使用缓存（已弃用，数据直接从 MySQL 统计表获取）

        Returns:
            dict: 包含 pie、line、table 三部分数据
                {
                    'pie': [{'name': '大麻', 'value': 150}, ...],
                    'line': {'months': ['1月', ...], 'data': {...}},
                    'table': [...]
                }
        """
        start_date = (datetime.now() - timedelta(days=days)).date()
        end_date = datetime.now().date()

        try:
            # 1. 从统计表构建圆环图数据（全局统计）
            pie_data = StatsAggregationService._build_dark_keywords_pie_from_stats(
                start_date, end_date
            )

            # 2. 从统计表构建趋势线数据（全局统计）
            line_data = StatsAggregationService._build_dark_keywords_line_from_stats(
                start_date, end_date
            )

            # 3. 从源表构建表格数据（详细记录）
            table_data = StatsAggregationService._build_dark_keywords_table(
                start_date
            )

            result = {
                'pie': pie_data,
                'line': line_data,
                'table': table_data
            }

            logger.info(f"黑词统计查询完成: {len(pie_data)} 毒品, {len(table_data)} 记录")
            return result
        except Exception as e:
            logger.error(f"黑词统计查询失败: {e}")
            return {'pie': [], 'line': {}, 'table': []}

    @staticmethod
    def _build_dark_keywords_pie_from_stats(start_date: datetime.date, end_date: datetime.date) -> List[Dict]:
        """
        从统计表构建圆环图数据（按毒品名称统计，全局）
        """
        logger.debug(f"从统计表构建黑词圆环图数据: {start_date} ~ {end_date}")

        results = AdTrackingDarkKeywordDailyStats.aggregate_by_drug(start_date, end_date)

        # 获取毒品名称映射
        drug_names = {}
        for drug_id, _ in results:
            drug = AdTrackingDarkKeywordDrug.query.get(drug_id)
            if drug:
                drug_names[drug_id] = drug.display_name or drug.name

        # 构建圆环图数据（使用毒品名称作为名称）
        pie_data = []
        for drug_id, total_count in results:
            drug_name = drug_names.get(drug_id, f'未知({drug_id})')
            pie_data.append({
                'name': drug_name,
                'value': int(total_count or 0)
            })

        # 按数量降序排序
        pie_data.sort(key=lambda x: x['value'], reverse=True)
        return pie_data

    @staticmethod
    def _build_dark_keywords_line_from_stats(start_date: datetime.date, end_date: datetime.date) -> Dict:
        """
        从统计表构建趋势线数据（按月份和毒品，全局）
        """
        logger.debug(f"从统计表构建黑词趋势线数据: {start_date} ~ {end_date}")

        results = AdTrackingDarkKeywordDailyStats.aggregate_by_month_and_drug(start_date, end_date)

        # 构建趋势数据
        months = sorted(set(m[0] for m in results if m[0]))
        drug_ids = sorted(set(d[1] for d in results if d[1]))

        # 获取毒品名称映射
        drug_names = {}
        for drug_id in drug_ids:
            drug = AdTrackingDarkKeywordDrug.query.get(drug_id)
            if drug:
                drug_names[drug_id] = drug.display_name or drug.name

        trend_data = {}
        for drug_id in drug_ids:
            drug_name = drug_names.get(drug_id, f'未知({drug_id})')
            trend_data[drug_name] = [
                int(next(
                    (c[2] for c in results if c[0] == month and c[1] == drug_id),
                    0
                ))
                for month in months
            ]

        return {
            'months': [f"{m.split('-')[1]}月" for m in months],
            'data': trend_data
        }

    @staticmethod
    def _build_dark_keywords_table(start_date: datetime.date) -> List[Dict]:
        """
        从源表构建表格数据（详细记录，全局）
        """
        logger.debug(f"从源表构建黑词表格数据: {start_date} 之后")

        records = db.session.query(AdTrackingDarkKeyword).filter(
            AdTrackingDarkKeyword.msg_date >= start_date
        ).order_by(
            AdTrackingDarkKeyword.msg_date.desc(),
            AdTrackingDarkKeyword.created_at.desc()
        ).limit(1000).all()

        # 转换为字典格式（包含关联的毒品和分类信息）
        table_data = []
        for record in records:
            data = record.to_dict()
            table_data.append(data)

        return table_data

    @staticmethod
    def get_transaction_methods_distribution(
        chat_id: Optional[str] = None,
        days: int = 365,
        use_cache: bool = True
    ) -> Dict:
        """
        获取交易方式分布（全局统计，忽略 chat_id）

        Args:
            chat_id: 群组ID（已弃用，用于 API 兼容性）
            days: 统计天数
            use_cache: 是否使用缓存（已弃用）

        Returns:
            dict:
                {
                    'bar': [{'name': '埋包', 'value': 3000, 'id': 1}, ...],
                    'line': {'months': [...], 'data': {...}}
                }
        """
        start_date = (datetime.now() - timedelta(days=days)).date()
        end_date = datetime.now().date()

        try:
            # 1. 按方式总数统计 (柱状图，从统计表聚合)
            bar_results = AdTrackingTransactionMethodDailyStats.aggregate_by_method(start_date, end_date)

            bar_result = [
                {'name': method, 'value': count, 'id': idx}
                for idx, (method, count) in enumerate(bar_results)
                if method  # 过滤掉 None 值
            ]

            # 2. 按月趋势统计 (折线图，从统计表聚合)
            line_results = AdTrackingTransactionMethodDailyStats.aggregate_by_month_and_method(
                start_date, end_date
            )

            # 构建趋势数据
            months = sorted(set(m[0] for m in line_results if m[0]))
            methods = [r[0] for r in bar_results if r[0]]

            trend_data = {}
            for method in methods:
                trend_data[method] = [
                    int(next(
                        (c[2] for c in line_results if c[0] == month and c[1] == method),
                        0
                    ))
                    for month in months
                ]

            result = {
                'bar': bar_result,
                'line': {
                    'months': [f"{m.split('-')[1]}月" for m in months],
                    'data': trend_data
                }
            }

            logger.info(f"交易方式分布查询完成: {len(bar_result)} 方式")
            return result
        except Exception as e:
            logger.error(f"交易方式分布查询失败: {e}")
            return {'bar': [], 'line': {'months': [], 'data': {}}}

    @staticmethod
    def get_price_trend(
        chat_id: Optional[str] = None,
        unit: Optional[str] = None,
        days: int = 365,
        use_cache: bool = True
    ) -> Dict:
        """
        获取价格趋势数据（全局统计，忽略 chat_id）

        Args:
            chat_id: 群组ID（已弃用，用于 API 兼容性）
            unit: 价格单位（可选，如果指定则只返回该单位的数据）
            days: 统计天数
            use_cache: 是否使用缓存（已弃用）

        Returns:
            dict:
                {
                    'months': ['1月', ...],
                    'data': {'g': [100, 110, ...], ...}
                }
        """
        start_date = (datetime.now() - timedelta(days=days)).date()
        end_date = datetime.now().date()

        try:
            # 从统计表按月、单位聚合平均价格
            monthly_prices = AdTrackingPriceDailyStats.aggregate_by_month_and_unit(
                start_date, end_date
            )

            # 构建响应
            months = sorted(set(m[0] for m in monthly_prices if m[0]))
            all_units = sorted(set(m[1] for m in monthly_prices if m[1]))

            # 如果指定了单位，只返回该单位
            if unit:
                all_units = [u for u in all_units if u == unit]

            data = {}
            for u in all_units:
                data[u] = [
                    float(round(
                        next(
                            (float(m[2]) for m in monthly_prices if m[0] == month and m[1] == u),
                            0
                        ),
                        2
                    ))
                    for month in months
                ]

            result = {
                'months': [f"{m.split('-')[1]}月" for m in months],
                'data': data
            }

            logger.info(f"价格趋势查询完成: {len(all_units)} 单位")
            return result
        except Exception as e:
            logger.error(f"价格趋势查询失败: {e}")
            return {'months': [], 'data': {}}

    @staticmethod
    def get_geo_heatmap(
        chat_id: Optional[str] = None,
        days: int = 365,
        use_cache: bool = True
    ) -> Dict:
        """
        获取地理热力图数据（全局统计，忽略 chat_id）

        Args:
            chat_id: 群组ID（已弃用，用于 API 兼容性）
            days: 统计天数
            use_cache: 是否使用缓存（已弃用）

        Returns:
            dict:
                {
                    'provinces': [{'name': '山东省', 'value': 100}, ...],
                    'shandong_cities': [{'name': '青岛市', 'value': 50}, ...],
                    'all_cities': [{'name': '成都市', 'value': 600, 'province': '四川省'}, ...]
                }
        """
        start_date = (datetime.now() - timedelta(days=days)).date()
        end_date = datetime.now().date()

        try:
            # 1. 按省份统计（从统计表聚合）
            province_results = AdTrackingGeoLocationDailyStats.aggregate_by_province(
                start_date, end_date
            )

            provinces = [
                {'name': prov, 'value': count}
                for prov, count in province_results
                if prov
            ]

            # 2. 山东省按市统计（从统计表聚合）
            shandong_cities = []
            if any(p['name'] == '山东省' for p in provinces):
                city_results = db.session.query(
                    AdTrackingGeoLocationDailyStats.city,
                    func.sum(AdTrackingGeoLocationDailyStats.record_count).label('total_count')
                ).filter(
                    AdTrackingGeoLocationDailyStats.province == '山东省',
                    AdTrackingGeoLocationDailyStats.stat_date >= start_date,
                    AdTrackingGeoLocationDailyStats.stat_date <= end_date,
                    AdTrackingGeoLocationDailyStats.city.isnot(None)
                ).group_by(
                    AdTrackingGeoLocationDailyStats.city
                ).all()

                shandong_cities = [
                    {'name': city, 'value': count}
                    for city, count in city_results
                    if city
                ]

            # 3. 所有城市统计（用于热点排名 TOP 50，从统计表聚合）
            all_cities_results = AdTrackingGeoLocationDailyStats.aggregate_by_city(
                start_date, end_date
            )

            all_cities = [
                {'name': city, 'value': count, 'province': prov}
                for city, prov, count in all_cities_results[:50]
                if city and prov
            ]

            # 规范化省份名称为地图标准格式（便于前端ECharts地图绘制）
            normalized_provinces = normalize_provinces_list(
                sorted(provinces, key=lambda x: x['value'], reverse=True)
            )
            normalized_shandong_cities = normalize_cities_with_provinces(
                sorted(shandong_cities, key=lambda x: x['value'], reverse=True)
            )
            normalized_all_cities = normalize_cities_with_provinces(all_cities)

            result = {
                'provinces': normalized_provinces,
                'shandong_cities': normalized_shandong_cities,
                'all_cities': normalized_all_cities
            }

            logger.info(f"地理热力图查询完成: {len(normalized_provinces)} 省份")
            return result
        except Exception as e:
            logger.error(f"地理热力图查询失败: {e}")
            return {'provinces': [], 'shandong_cities': [], 'all_cities': []}

    @staticmethod
    def clear_cache_by_chat_id(chat_id: int) -> int:
        """
        缓存清除端点（已弃用，系统不再使用 Redis 缓存）

        Args:
            chat_id: 群组ID

        Returns:
            int: 总是返回 0（兼容性）
        """
        logger.info(f"缓存清除请求（已弃用）: chat_id={chat_id}, 系统不再使用 Redis 缓存")
        return 0

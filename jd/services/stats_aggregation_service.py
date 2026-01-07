"""统计聚合服务 - 负责各类统计数据的计算和缓存"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import func, text

from jd import db
from jd.models.ad_tracking_price import AdTrackingPrice
from jd.models.ad_tracking_transaction_method import AdTrackingTransactionMethod
from jd.models.ad_tracking_geo_location import AdTrackingGeoLocation
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeyword
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeywordDrug
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeywordCategory
from jd.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class StatsAggregationService:
    """统计聚合服务 - 负责各类统计数据的计算和缓存"""

    @staticmethod
    def get_dark_keywords_stats(
        chat_id: Optional[int] = None,
        tag_ids: Optional[List[int]] = None,
        days: int = 365,
        use_cache: bool = True
    ) -> Dict:
        """
        获取黑词分析统计

        Args:
            chat_id: 群组ID（可选，不提供时统计全表）
            tag_ids: 标签ID列表（可选）
            days: 统计天数
            use_cache: 是否使用缓存

        Returns:
            dict: 包含 pie、line、table 三部分数据
                {
                    'pie': [{'name': '大麻', 'value': 150}, ...],
                    'line': {'months': ['1月', ...], 'data': {...}},
                    'table': [...]
                }
        """
        # 尝试从缓存获取
        cache_key = f'dark_keywords:{"all" if not chat_id else chat_id}:{days}'
        if tag_ids:
            cache_key += f':{",".join(map(str, sorted(tag_ids)))}'

        if use_cache:
            cached = CacheService.get(cache_key)
            if cached:
                logger.debug(f"黑词统计命中缓存: {cache_key}")
                return cached

        start_date = datetime.now() - timedelta(days=days)

        try:
            # 1. 构建圆环图数据
            pie_data = StatsAggregationService._build_dark_keywords_pie(
                chat_id, tag_ids, start_date
            )

            # 2. 构建趋势线数据
            line_data = StatsAggregationService._build_dark_keywords_line(
                chat_id, tag_ids, start_date
            )

            # 3. 构建表格数据
            table_data = StatsAggregationService._build_dark_keywords_table(
                chat_id, tag_ids, start_date
            )

            result = {
                'pie': pie_data,
                'line': line_data,
                'table': table_data
            }

            # 缓存结果（24小时）
            if use_cache:
                CacheService.set(cache_key, result, ttl=86400)
                logger.debug(f"黑词统计缓存已设置: {cache_key}")

            return result
        except Exception as e:
            logger.error(f"黑词统计查询失败: {e}")
            return {'pie': [], 'line': {}, 'table': []}

    @staticmethod
    def _build_dark_keywords_pie(chat_id: Optional[int], tag_ids: Optional[List[int]], start_date: datetime) -> List[Dict]:
        """构建圆环图数据（按毒品名称统计）"""
        logger.debug("构建黑词圆环图数据")

        query = db.session.query(
            AdTrackingDarkKeyword.drug_id,
            func.sum(AdTrackingDarkKeyword.count).label('total_count')
        ).filter(
            AdTrackingDarkKeyword.msg_date >= start_date,
            AdTrackingDarkKeyword.drug_id.isnot(None)
        )

        # 如果指定了chat_id，添加过滤条件
        if chat_id:
            query = query.filter(AdTrackingDarkKeyword.chat_id == str(chat_id))

        # 如果指定了标签，需要通过标签关联查询
        if tag_ids:
            # 这里假设标签与黑词记录有关联，如果需要可以添加
            pass

        results = query.group_by(AdTrackingDarkKeyword.drug_id).all()

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
                'value': int(total_count)
            })

        # 按数量降序排序
        pie_data.sort(key=lambda x: x['value'], reverse=True)
        return pie_data

    @staticmethod
    def _build_dark_keywords_line(chat_id: Optional[int], tag_ids: Optional[List[int]], start_date: datetime) -> Dict:
        """构建趋势线数据"""
        logger.debug("构建黑词趋势线数据")

        query = db.session.query(
            func.date_format(AdTrackingDarkKeyword.msg_date, '%Y-%m').label('month'),
            AdTrackingDarkKeyword.drug_id,
            func.sum(AdTrackingDarkKeyword.count).label('total_count')
        ).filter(
            AdTrackingDarkKeyword.msg_date >= start_date
        )

        # 如果指定了chat_id，添加过滤条件
        if chat_id:
            query = query.filter(AdTrackingDarkKeyword.chat_id == str(chat_id))

        # 如果指定了标签，需要通过标签关联查询
        if tag_ids:
            pass

        results = query.group_by('month', AdTrackingDarkKeyword.drug_id).all()

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
    def _build_dark_keywords_table(chat_id: Optional[int], tag_ids: Optional[List[int]], start_date: datetime) -> List[Dict]:
        """构建表格数据"""
        logger.debug("构建黑词表格数据")

        query = db.session.query(AdTrackingDarkKeyword).filter(
            AdTrackingDarkKeyword.msg_date >= start_date
        )

        # 如果指定了chat_id，添加过滤条件
        if chat_id:
            query = query.filter(AdTrackingDarkKeyword.chat_id == str(chat_id))

        # 如果指定了标签，需要通过标签关联查询
        if tag_ids:
            pass

        records = query.order_by(
            AdTrackingDarkKeyword.msg_date.desc(),
            AdTrackingDarkKeyword.created_at.desc()
        ).all()

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
        获取交易方式分布

        Args:
            chat_id: 群组ID (可选，不提供时统计全表)
            days: 统计天数
            use_cache: 是否使用缓存

        Returns:
            dict:
                {
                    'bar': [{'name': '埋包', 'value': 3000, 'id': 1}, ...],
                    'line': {'months': [...], 'data': {...}}
                }
        """
        cache_key = f'transaction_methods:{"all" if not chat_id else chat_id}:{days}'

        if use_cache:
            cached = CacheService.get(cache_key)
            if cached:
                logger.debug(f"交易方式分布命中缓存: {cache_key}")
                return cached

        start_date = datetime.now() - timedelta(days=days)

        try:
            # 1. 按方式总数统计 (柱状图)
            query = db.session.query(
                AdTrackingTransactionMethod.method,
                func.count(AdTrackingTransactionMethod.id).label('count')
            ).filter(
                AdTrackingTransactionMethod.msg_date >= start_date
            )

            # 如果指定了 chat_id，则添加该过滤条件
            if chat_id:
                query = query.filter(AdTrackingTransactionMethod.chat_id == chat_id)

            bar_data = query.group_by(
                AdTrackingTransactionMethod.method
            ).order_by(
                func.count(AdTrackingTransactionMethod.id).desc()
            ).all()

            bar_result = [
                {'name': method, 'value': count, 'id': idx}
                for idx, (method, count) in enumerate(bar_data)
                if method  # 过滤掉 None 值
            ]

            # 2. 按月趋势统计 (折线图)
            line_query = db.session.query(
                func.date_format(AdTrackingTransactionMethod.msg_date, '%Y-%m').label('month'),
                AdTrackingTransactionMethod.method,
                func.count(AdTrackingTransactionMethod.id).label('count')
            ).filter(
                AdTrackingTransactionMethod.msg_date >= start_date
            )

            # 如果指定了 chat_id，则添加该过滤条件
            if chat_id:
                line_query = line_query.filter(AdTrackingTransactionMethod.chat_id == chat_id)

            line_data = line_query.group_by(
                'month',
                AdTrackingTransactionMethod.method
            ).all()

            # 构建趋势数据
            months = sorted(set(m[0] for m in line_data if m[0]))
            methods = [r[0] for r in bar_data if r[0]]

            trend_data = {}
            for method in methods:
                trend_data[method] = [
                    int(next(
                        (c[2] for c in line_data if c[0] == month and c[1] == method),
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

            if use_cache:
                CacheService.set(cache_key, result, ttl=86400)
                logger.debug(f"交易方式分布缓存已设置: {cache_key}")

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
        获取价格趋势数据

        Args:
            chat_id: 群组ID (可选，不提供时统计全表)
            unit: 价格单位（可选，如果指定则只返回该单位的数据）
            days: 统计天数
            use_cache: 是否使用缓存

        Returns:
            dict:
                {
                    'months': ['1月', ...],
                    'data': {'g': [100, 110, ...], ...}
                }
        """
        cache_key = f'price_trend:{"all" if not chat_id else chat_id}:{unit}:{days}'

        if use_cache:
            cached = CacheService.get(cache_key)
            if cached:
                logger.debug(f"价格趋势命中缓存: {cache_key}")
                return cached

        start_date = datetime.now() - timedelta(days=days)

        try:
            # 按月、单位统计平均价格
            query = db.session.query(
                func.date_format(AdTrackingPrice.msg_date, '%Y-%m').label('month'),
                AdTrackingPrice.unit,
                func.avg(AdTrackingPrice.price_value).label('avg_price'),
                func.count(AdTrackingPrice.id).label('count')
            ).filter(
                AdTrackingPrice.msg_date >= start_date
            )

            # 如果指定了 chat_id，则添加该过滤条件
            if chat_id:
                query = query.filter(AdTrackingPrice.chat_id == chat_id)

            monthly_prices = query.group_by(
                'month',
                AdTrackingPrice.unit
            ).order_by('month').all()

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

            if use_cache:
                CacheService.set(cache_key, result, ttl=86400)
                logger.debug(f"价格趋势缓存已设置: {cache_key}")

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
        获取地理热力图数据

        Args:
            chat_id: 群组ID (可选，不提供时统计全表)
            days: 统计天数
            use_cache: 是否使用缓存

        Returns:
            dict:
                {
                    'provinces': [{'name': '山东省', 'value': 100}, ...],
                    'shandong_cities': [{'name': '青岛市', 'value': 50}, ...],
                    'all_cities': [{'name': '成都市', 'value': 600, 'province': '四川省'}, ...]
                }
        """
        cache_key = f'geo_heatmap:{"all" if not chat_id else chat_id}:{days}'

        if use_cache:
            cached = CacheService.get(cache_key)
            if cached:
                logger.debug(f"地理热力图命中缓存: {cache_key}")
                return cached

        start_date = datetime.now() - timedelta(days=days)

        try:
            # 1. 按省份统计
            prov_query = db.session.query(
                AdTrackingGeoLocation.province,
                func.count(AdTrackingGeoLocation.id).label('count')
            ).filter(
                AdTrackingGeoLocation.msg_date >= start_date
            )

            # 如果指定了 chat_id，则添加该过滤条件
            if chat_id:
                prov_query = prov_query.filter(AdTrackingGeoLocation.chat_id == chat_id)

            province_stats = prov_query.group_by(
                AdTrackingGeoLocation.province
            ).all()

            provinces = [
                {'name': prov, 'value': count}
                for prov, count in province_stats
                if prov
            ]

            # 2. 山东省按市统计
            shandong_cities = []
            if any(p['name'] == '山东省' for p in provinces):
                city_query = db.session.query(
                    AdTrackingGeoLocation.city,
                    func.count(AdTrackingGeoLocation.id).label('count')
                ).filter(
                    AdTrackingGeoLocation.province == '山东省',
                    AdTrackingGeoLocation.msg_date >= start_date
                )

                # 如果指定了 chat_id，则添加该过滤条件
                if chat_id:
                    city_query = city_query.filter(AdTrackingGeoLocation.chat_id == chat_id)

                city_stats = city_query.group_by(
                    AdTrackingGeoLocation.city
                ).all()

                shandong_cities = [
                    {'name': city, 'value': count}
                    for city, count in city_stats
                    if city
                ]

            # 3. 所有城市统计（用于热点排名 TOP 50）
            all_cities_query = db.session.query(
                AdTrackingGeoLocation.province,
                AdTrackingGeoLocation.city,
                func.count(AdTrackingGeoLocation.id).label('count')
            ).filter(
                AdTrackingGeoLocation.msg_date >= start_date,
                AdTrackingGeoLocation.city.isnot(None)
            )

            # 如果指定了 chat_id，则添加该过滤条件
            if chat_id:
                all_cities_query = all_cities_query.filter(AdTrackingGeoLocation.chat_id == chat_id)

            all_cities_stats = all_cities_query.group_by(
                AdTrackingGeoLocation.province,
                AdTrackingGeoLocation.city
            ).order_by(
                func.count(AdTrackingGeoLocation.id).desc()
            ).limit(50).all()

            all_cities = [
                {'name': city, 'value': count, 'province': prov}
                for prov, city, count in all_cities_stats
                if city and prov
            ]

            result = {
                'provinces': sorted(provinces, key=lambda x: x['value'], reverse=True),
                'shandong_cities': sorted(shandong_cities, key=lambda x: x['value'], reverse=True),
                'all_cities': all_cities  # 已按 count DESC 排序，TOP 50
            }

            if use_cache:
                CacheService.set(cache_key, result, ttl=86400)
                logger.debug(f"地理热力图缓存已设置: {cache_key}")

            return result
        except Exception as e:
            logger.error(f"地理热力图查询失败: {e}")
            return {'provinces': [], 'shandong_cities': [], 'all_cities': []}

    @staticmethod
    def clear_cache_by_chat_id(chat_id: int) -> int:
        """
        清除指定群组的所有缓存

        Args:
            chat_id: 群组ID

        Returns:
            int: 清除的缓存数量
        """
        pattern = f'*{chat_id}*'
        count = CacheService.clear_pattern(pattern)
        logger.info(f"清除群组 {chat_id} 的缓存: {count} 条")
        return count

"""
广告分析 API 端点
- 黑词分析
- 交易方式分析
- 价格趋势分析
- 地理位置热力图分析
"""
import logging
from datetime import datetime
from flask import request
from jd import db
from jd.views.api import api
from jd.helpers.response import api_response
from jd.services.stats_aggregation_service import StatsAggregationService
# CacheService 已不再使用（系统迁移到 MySQL 统计表）
# from jd.services.cache_service import CacheService
from jd.models.ad_tracking_price import AdTrackingPrice
from jd.models.ad_tracking_geo_location import AdTrackingGeoLocation
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeyword
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeywordCategory
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeywordDrug

logger = logging.getLogger(__name__)


# ============================================================================
# 黑词分析 API
# ============================================================================

@api.route('/ad-tracking/ad-analysis/dark-keywords', methods=['GET'], need_login=False)
def get_dark_keywords_analysis():
    """
    获取黑词分析数据

    Query Parameters:
        - chat_id: 群组ID (可选，不提供时统计全表)
        - tag_ids: 标签ID列表 (可选)
        - keyword: 搜索关键词 (可选)
        - category: 分类ID (可选)
        - drug: 毒品ID (可选)
        - days: 天数范围 (默认365)
        - offset: 分页偏移 (默认0)
        - limit: 分页大小 (默认20)
    """
    try:
        chat_id = request.args.get('chat_id', type=int)
        tag_ids = request.args.getlist('tag_ids', type=int)
        keyword = request.args.get('keyword')
        category = request.args.get('category', type=int)
        drug = request.args.get('drug', type=int)
        days = request.args.get('days', 365, type=int)
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)

        if days < 1 or days > 3650:
            return api_response(
                {},
                err_code=2,
                err_msg='days 参数必须在 1-3650 之间',
                status_code=400
            )

        # 获取统计数据
        stats_data = StatsAggregationService.get_dark_keywords_stats(
            chat_id=chat_id,
            tag_ids=tag_ids if tag_ids else None,
            days=days,
            use_cache=True
        )

        # 根据筛选条件过滤表格数据
        filtered_table = stats_data['table']
        if keyword:
            filtered_table = [r for r in filtered_table if keyword.lower() in r.get('keyword', '').lower()]
        if category:
            filtered_table = [r for r in filtered_table if r.get('category_id') == category]
        if drug:
            filtered_table = [r for r in filtered_table if r.get('drug_id') == drug]

        # 获取总数（分页用）
        total = len(filtered_table)

        # 分页表格数据
        table_data = filtered_table[offset:offset + limit]

        return api_response({
            'pie': stats_data['pie'],
            'line': stats_data['line'],
            'table': table_data,
            'total': total,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'page_size': limit
        })

    except ValueError as e:
        logger.warning(f"参数验证失败: {e}")
        return api_response(
            {},
            err_code=2,
            err_msg=f'参数错误: {str(e)}',
            status_code=400
        )
    except Exception as e:
        logger.error(f"获取黑词分析数据失败: {e}", exc_info=True)
        return api_response(
            {},
            err_code=99,
            err_msg='服务器内部错误',
            status_code=500
        )


@api.route('/ad-tracking/ad-analysis/dark-keywords/word-cloud', methods=['GET'], need_login=False)
def get_dark_keywords_word_cloud():
    """
    获取黑词词云数据（所有触发过的关键词）

    Query Parameters:
        - chat_id: 群组ID (可选，不提供时统计全表)
        - tag_ids: 标签ID列表 (可选)
        - keyword: 搜索关键词 (可选，用于过滤)
        - category: 分类ID (可选，用于过滤)
        - drug: 毒品ID (可选，用于过滤)
        - days: 天数范围 (默认365)

    Returns:
        {
            "err_code": 0,
            "payload": [
                {"name": "D", "value": 7206},
                {"name": "粉", "value": 3592},
                ...
            ]
        }
    """
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta

        chat_id = request.args.get('chat_id', type=int)
        tag_ids = request.args.getlist('tag_ids', type=int)
        keyword = request.args.get('keyword')
        category = request.args.get('category', type=int)
        drug = request.args.get('drug', type=int)
        days = request.args.get('days', 365, type=int)

        if days < 1 or days > 3650:
            return api_response(
                {},
                err_code=2,
                err_msg='days 参数必须在 1-3650 之间',
                status_code=400
            )

        # 计算起始日期
        start_date = datetime.now().date() - timedelta(days=days)

        # 构建查询
        query = db.session.query(
            AdTrackingDarkKeyword.keyword,
            func.sum(AdTrackingDarkKeyword.count).label('total_count')
        ).filter(
            AdTrackingDarkKeyword.msg_date >= start_date
        )

        # 按条件过滤
        if chat_id:
            query = query.filter(AdTrackingDarkKeyword.chat_id == str(chat_id))

        if keyword:
            query = query.filter(AdTrackingDarkKeyword.keyword.like(f'%{keyword}%'))

        if category:
            query = query.filter(AdTrackingDarkKeyword.category_id == category)

        if drug:
            query = query.filter(AdTrackingDarkKeyword.drug_id == drug)

        # 分组统计并排序
        results = query.group_by(
            AdTrackingDarkKeyword.keyword
        ).order_by(
            func.sum(AdTrackingDarkKeyword.count).desc()
        ).all()

        # 转换为词云格式
        word_cloud_data = [
            {'name': kw, 'value': int(count)}
            for kw, count in results
        ]

        return api_response(word_cloud_data)

    except ValueError as e:
        logger.warning(f"参数验证失败: {e}")
        return api_response(
            [],
            err_code=2,
            err_msg=f'参数错误: {str(e)}',
            status_code=400
        )
    except Exception as e:
        logger.error(f"获取黑词词云数据失败: {e}", exc_info=True)
        return api_response(
            [],
            err_code=99,
            err_msg='服务器内部错误',
            status_code=500
        )


@api.route('/ad-tracking/ad-analysis/dark-keywords/categories', methods=['GET'], need_login=False)
def get_dark_keywords_categories():
    """
    获取黑词分类列表（包含每个分类下的毒品）
    """
    try:
        categories = AdTrackingDarkKeywordCategory.get_all_active()

        result = []
        for category in categories:
            category_dict = {
                'id': category.id,
                'name': category.name,
                'drugs': []
            }
            # 获取该分类下所有启用的毒品
            drugs = AdTrackingDarkKeywordDrug.get_by_category(category.id)
            for drug in drugs:
                category_dict['drugs'].append({
                    'id': drug.id,
                    'name': drug.display_name or drug.name
                })
            result.append(category_dict)

        return api_response({
            'categories': result
        })

    except Exception as e:
        logger.error(f"获取黑词分类失败: {e}", exc_info=True)
        return api_response(
            {},
            err_code=99,
            err_msg='服务器内部错误',
            status_code=500
        )


@api.route('/ad-tracking/ad-analysis/dark-keywords/<int:keyword_id>', methods=['DELETE'], need_login=False)
def delete_dark_keyword(keyword_id):
    """
    删除黑词记录

    Path Parameters:
        keyword_id: 黑词记录ID

    Returns:
        {
            "success": true,
            "id": 123
        }
    """
    try:
        keyword = AdTrackingDarkKeyword.query.get(keyword_id)

        if not keyword:
            return api_response(
                {},
                err_code=5,
                err_msg='黑词记录不存在',
                status_code=404
            )

        db.session.delete(keyword)
        db.session.commit()

        # 注意：系统已迁移到 MySQL 统计表，无需清除 Redis 缓存
        # 统计数据将在下一次定时任务中自动重新计算

        logger.info(f"删除黑词记录: id={keyword_id}, keyword={keyword.keyword}")

        return api_response({
            'success': True,
            'id': keyword_id
        })

    except Exception as e:
        logger.error(f"删除黑词记录失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response(
            {},
            err_code=99,
            err_msg='服务器错误',
            status_code=500
        )


# ============================================================================
# 交易方式 API
# ============================================================================

@api.route('/ad-tracking/ad-analysis/transaction-methods', methods=['GET'], need_login=False)
def get_transaction_methods():
    """
    获取交易方式分布（柱状图）

    Query Parameters:
        - chat_id: 群组ID (可选，不提供时统计全表)
        - days: 天数范围 (默认365)
    """
    try:
        chat_id = request.args.get('chat_id')
        days = request.args.get('days', 365, type=int)

        if days < 1 or days > 3650:
            return api_response(
                {},
                err_code=2,
                err_msg='days 参数必须在 1-3650 之间',
                status_code=400
            )

        stats = StatsAggregationService.get_transaction_methods_distribution(
            chat_id=chat_id,
            days=days,
            use_cache=True
        )

        return api_response({'bar': stats['bar']})

    except Exception as e:
        logger.error(f"获取交易方式分布失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/ad-tracking/ad-analysis/transaction-methods/trend', methods=['GET'], need_login=False)
def get_transaction_methods_trend():
    """
    获取交易方式趋势（折线图）

    Query Parameters:
        - chat_id: 群组ID (可选，不提供时统计全表)
        - days: 天数范围 (默认365)
    """
    try:
        chat_id = request.args.get('chat_id')
        days = request.args.get('days', 365, type=int)

        if days < 1 or days > 3650:
            return api_response(
                {},
                err_code=2,
                err_msg='days 参数必须在 1-3650 之间',
                status_code=400
            )

        stats = StatsAggregationService.get_transaction_methods_distribution(
            chat_id=chat_id,
            days=days,
            use_cache=True
        )

        return api_response({'line': stats['line']})

    except Exception as e:
        logger.error(f"获取交易方式趋势失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/ad-tracking/ad-analysis/transaction-methods/list', methods=['GET'], need_login=False)
def get_transaction_methods_list():
    """
    获取交易方式列表（统计每种方式的数量）

    Query Parameters:
        - chat_id: 群组ID (可选，如果提供则只统计该群组)
    """
    try:
        from sqlalchemy import func
        from jd.models.ad_tracking_transaction_method import AdTrackingTransactionMethod

        chat_id = request.args.get('chat_id', type=int)

        # 构建查询
        query = db.session.query(
            func.coalesce(AdTrackingTransactionMethod.method, '未知').label('method'),
            func.count(AdTrackingTransactionMethod.id).label('count')
        )

        # 如果提供了 chat_id，则筛选特定群组
        if chat_id:
            query = query.filter(AdTrackingTransactionMethod.chat_id == chat_id)

        # 按交易方式分组统计
        methods = query.group_by('method').all()

        return api_response({
            'methods': [
                {'name': m.method or '未知', 'count': m.count}
                for m in methods
            ]
        })

    except Exception as e:
        logger.error(f"获取交易方式列表失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


# ============================================================================
# 价格趋势 API
# ============================================================================

@api.route('/ad-tracking/ad-analysis/price-trend', methods=['GET'], need_login=False)
def get_price_trend():
    """
    获取价格趋势数据

    Query Parameters:
        - chat_id: 群组ID (可选，不提供时统计全表)
        - unit: 价格单位 (可选，如 'g', 'piece' 等)
        - days: 天数范围 (默认365)
    """
    try:
        chat_id = request.args.get('chat_id')
        unit = request.args.get('unit')
        days = request.args.get('days', 365, type=int)

        if days < 1 or days > 3650:
            return api_response(
                {},
                err_code=2,
                err_msg='days 参数必须在 1-3650 之间',
                status_code=400
            )

        trend_data = StatsAggregationService.get_price_trend(
            chat_id=chat_id,
            unit=unit,
            days=days,
            use_cache=True
        )

        return api_response(trend_data)

    except Exception as e:
        logger.error(f"获取价格趋势失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/ad-tracking/ad-analysis/price-history', methods=['GET'], need_login=False)
def get_price_history():
    """
    获取价格历史记录

    Query Parameters:
        - chat_id: 群组ID (可选，不提供时查询全表)
        - unit: 价格单位 (可选)
        - offset: 分页偏移 (默认0)
        - limit: 分页大小 (默认20)
    """
    try:
        chat_id = request.args.get('chat_id')
        unit = request.args.get('unit')
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)

        # 参数验证
        if offset < 0 or limit < 1 or limit > 100:
            return api_response(
                {},
                err_code=2,
                err_msg='offset 必须 >= 0, limit 必须在 1-100 之间',
                status_code=400
            )

        query = db.session.query(AdTrackingPrice)

        # 如果指定了 chat_id，则添加过滤条件
        if chat_id:
            query = query.filter(AdTrackingPrice.chat_id == chat_id)

        if unit:
            query = query.filter(AdTrackingPrice.unit == unit)

        total = query.count()
        records = query.order_by(AdTrackingPrice.msg_date.desc())\
            .offset(offset).limit(limit).all()

        return api_response({
            'data': [r.to_dict() for r in records],
            'total': total,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'page_size': limit
        })

    except Exception as e:
        logger.error(f"获取价格历史失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


# ============================================================================
# 地理位置分析 API
# ============================================================================

@api.route('/ad-tracking/ad-analysis/geo-heatmap', methods=['GET'], need_login=False)
def get_geo_heatmap():
    """
    获取地理位置热力图数据

    Query Parameters:
        - chat_id: 群组ID (可选，不提供时统计全表)
        - province: 省份 (可选，用于筛选)
        - days: 天数范围 (默认365)
    """
    try:
        chat_id = request.args.get('chat_id')
        province = request.args.get('province')
        days = request.args.get('days', 365, type=int)

        if days < 1 or days > 3650:
            return api_response(
                {},
                err_code=2,
                err_msg='days 参数必须在 1-3650 之间',
                status_code=400
            )

        heatmap_data = StatsAggregationService.get_geo_heatmap(
            chat_id=chat_id,
            days=days,
            use_cache=True
        )

        # 筛选特定省份
        if province:
            heatmap_data['provinces'] = [
                p for p in heatmap_data['provinces']
                if p['name'] == province
            ]

            # 如果是山东省，也返回城市级别数据
            if province == '山东省':
                pass  # shandong_cities 已在查询中处理
            else:
                heatmap_data['shandong_cities'] = []

        return api_response(heatmap_data)

    except Exception as e:
        logger.error(f"获取热力图失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/ad-tracking/ad-analysis/geo-records', methods=['GET'], need_login=False)
def get_geo_records():
    """
    获取地理位置记录详情

    Query Parameters:
        - chat_id: 群组ID (可选，不提供时查询全表)
        - province: 省份 (可选)
        - city: 城市 (可选)
        - offset: 分页偏移 (默认0)
        - limit: 分页大小 (默认20)
    """
    try:
        chat_id = request.args.get('chat_id')
        province = request.args.get('province')
        city = request.args.get('city')
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)

        # 参数验证
        if offset < 0 or limit < 1 or limit > 100:
            return api_response(
                {},
                err_code=2,
                err_msg='offset 必须 >= 0, limit 必须在 1-100 之间',
                status_code=400
            )

        query = db.session.query(AdTrackingGeoLocation)

        # 如果指定了 chat_id，则添加过滤条件
        if chat_id:
            query = query.filter(AdTrackingGeoLocation.chat_id == chat_id)

        if province:
            query = query.filter(AdTrackingGeoLocation.province == province)
        if city:
            query = query.filter(AdTrackingGeoLocation.city == city)

        total = query.count()
        records = query.order_by(AdTrackingGeoLocation.msg_date.desc())\
            .offset(offset).limit(limit).all()

        return api_response({
            'data': [r.to_dict() for r in records],
            'total': total,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'page_size': limit
        })

    except Exception as e:
        logger.error(f"获取地理记录失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)

"""
配置管理 API 端点
- 交易方式配置管理
- 地理位置配置管理
"""
import logging
from flask import request
from jd import db
from jd.views.api import api
from jd.helpers.response import api_response
from jd.models.ad_tracking_transaction_method_config import (
    AdTrackingTransactionMethodConfig,
    AdTrackingTransactionMethodKeyword
)
from jd.models.ad_tracking_geo_location_master import AdTrackingGeoLocationMaster
from jd.models.ad_tracking_dark_keyword import (
    AdTrackingDarkKeywordCategory,
    AdTrackingDarkKeywordDrug,
    AdTrackingDarkKeywordKeyword
)
from jd.services.keyword_extraction_service import KeywordExtractionService
from jd.services.geo_location_service import GeoLocationService
from jd.services.dark_keyword_extraction_service import DarkKeywordExtractionService

logger = logging.getLogger(__name__)


# ============================================================================
# 交易方式配置管理 API
# ============================================================================

@api.route('/config/transaction-methods', methods=['GET'], need_login=False)
def list_transaction_methods():
    """
    获取所有交易方式配置

    Query Parameters:
        - is_active: 是否启用 (可选，true/false)
        - offset: 分页偏移 (默认0)
        - limit: 分页大小 (默认20)
    """
    try:
        is_active = request.args.get('is_active', type=lambda x: x.lower() == 'true')
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

        query = AdTrackingTransactionMethodConfig.query

        # 如果指定了 is_active，按其过滤
        is_active_param = request.args.get('is_active')
        if is_active_param is not None:
            query = query.filter_by(is_active=is_active)

        total = query.count()
        methods = query.order_by(AdTrackingTransactionMethodConfig.priority.desc())\
            .offset(offset).limit(limit).all()

        return api_response({
            'methods': [m.to_dict() for m in methods],
            'total': total,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'page_size': limit
        })

    except Exception as e:
        logger.error(f"获取交易方式列表失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/transaction-methods', methods=['POST'], need_login=False)
def create_transaction_method():
    """
    创建新的交易方式

    Request Body:
        {
            "method_name": "埋包",
            "display_name": "埋包配送",
            "description": "通过埋包方式配送产品",
            "priority": 10
        }
    """
    try:
        data = request.get_json() or {}

        # 参数验证
        method_name = data.get('method_name', '').strip()
        if not method_name:
            return api_response(
                {},
                err_code=2,
                err_msg='method_name 不能为空',
                status_code=400
            )

        # 检查是否已存在
        existing = AdTrackingTransactionMethodConfig.query.filter_by(
            method_name=method_name
        ).first()
        if existing:
            return api_response(
                {},
                err_code=1,
                err_msg=f'交易方式 "{method_name}" 已存在',
                status_code=400
            )

        method = AdTrackingTransactionMethodConfig(
            method_name=method_name,
            display_name=data.get('display_name', method_name),
            description=data.get('description'),
            priority=data.get('priority', 0),
            is_active=data.get('is_active', True)
        )

        db.session.add(method)
        db.session.commit()

        # 刷新缓存
        KeywordExtractionService.refresh_transaction_matcher_cache()
        logger.info(f"创建交易方式: {method_name}")

        return api_response({'id': method.id, 'method_name': method.method_name}, status_code=201)

    except Exception as e:
        logger.error(f"创建交易方式失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/transaction-methods/<int:method_id>', methods=['GET'], need_login=False)
def get_transaction_method(method_id):
    """获取交易方式详情"""
    try:
        method = AdTrackingTransactionMethodConfig.query.get(method_id)
        if not method:
            return api_response({}, err_code=5, err_msg='交易方式不存在', status_code=404)

        return api_response(method.to_dict())

    except Exception as e:
        logger.error(f"获取交易方式详情失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/transaction-methods/<int:method_id>', methods=['PUT'], need_login=False)
def update_transaction_method(method_id):
    """更新交易方式"""
    try:
        method = AdTrackingTransactionMethodConfig.query.get(method_id)
        if not method:
            return api_response({}, err_code=5, err_msg='交易方式不存在', status_code=404)

        data = request.get_json() or {}

        # 更新字段
        if 'display_name' in data:
            method.display_name = data['display_name']
        if 'description' in data:
            method.description = data['description']
        if 'priority' in data:
            method.priority = data['priority']
        if 'is_active' in data:
            method.is_active = data['is_active']

        db.session.commit()

        # 刷新缓存
        KeywordExtractionService.refresh_transaction_matcher_cache()
        logger.info(f"更新交易方式: {method.method_name}")

        return api_response(method.to_dict())

    except Exception as e:
        logger.error(f"更新交易方式失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/transaction-methods/<int:method_id>', methods=['DELETE'], need_login=False)
def delete_transaction_method(method_id):
    """删除交易方式"""
    try:
        method = AdTrackingTransactionMethodConfig.query.get(method_id)
        if not method:
            return api_response({}, err_code=5, err_msg='交易方式不存在', status_code=404)

        db.session.delete(method)
        db.session.commit()

        # 刷新缓存
        KeywordExtractionService.refresh_transaction_matcher_cache()
        logger.info(f"删除交易方式: {method.method_name}")

        return api_response({'id': method_id})

    except Exception as e:
        logger.error(f"删除交易方式失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


# ============================================================================
# 交易方式关键词管理 API
# ============================================================================

@api.route('/config/transaction-methods/<int:method_id>/keywords', methods=['GET'], need_login=False)
def list_transaction_keywords(method_id):
    """获取交易方式的所有关键词"""
    try:
        method = AdTrackingTransactionMethodConfig.query.get(method_id)
        if not method:
            return api_response({}, err_code=5, err_msg='交易方式不存在', status_code=404)

        keywords = AdTrackingTransactionMethodKeyword.query.filter_by(
            method_id=method_id
        ).all()

        return api_response({
            'keywords': [kw.to_dict() for kw in keywords]
        })

    except Exception as e:
        logger.error(f"获取关键词列表失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/transaction-methods/<int:method_id>/keywords', methods=['POST'], need_login=False)
def add_transaction_keyword(method_id):
    """
    为交易方式添加关键词

    Request Body:
        {
            "keyword": "埋",
            "weight": 1,
            "is_active": true
        }
    """
    try:
        method = AdTrackingTransactionMethodConfig.query.get(method_id)
        if not method:
            return api_response({}, err_code=5, err_msg='交易方式不存在', status_code=404)

        data = request.get_json() or {}
        keyword_text = data.get('keyword', '').strip()

        if not keyword_text:
            return api_response(
                {},
                err_code=2,
                err_msg='keyword 不能为空',
                status_code=400
            )

        # 检查是否已存在
        existing = AdTrackingTransactionMethodKeyword.query.filter_by(
            method_id=method_id,
            keyword=keyword_text
        ).first()
        if existing:
            return api_response(
                {},
                err_code=1,
                err_msg=f'关键词 "{keyword_text}" 已存在',
                status_code=400
            )

        keyword = AdTrackingTransactionMethodKeyword(
            method_id=method_id,
            keyword=keyword_text,
            weight=data.get('weight', 1),
            is_active=data.get('is_active', True)
        )

        db.session.add(keyword)
        db.session.commit()

        # 刷新缓存
        KeywordExtractionService.refresh_transaction_matcher_cache()
        logger.info(f"添加关键词: {keyword_text} 到 {method.method_name}")

        return api_response({'id': keyword.id}, status_code=201)

    except Exception as e:
        logger.error(f"添加关键词失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/transaction-methods/<int:method_id>/keywords/<int:keyword_id>',
           methods=['PUT'], need_login=False)
def update_transaction_keyword(method_id, keyword_id):
    """更新交易方式关键词"""
    try:
        keyword = AdTrackingTransactionMethodKeyword.query.get(keyword_id)
        if not keyword or keyword.method_id != method_id:
            return api_response({}, err_code=5, err_msg='关键词不存在', status_code=404)

        data = request.get_json() or {}

        if 'is_active' in data:
            keyword.is_active = data['is_active']
        if 'weight' in data:
            keyword.weight = data['weight']

        db.session.commit()

        # 刷新缓存
        KeywordExtractionService.refresh_transaction_matcher_cache()
        logger.info(f"更新关键词: {keyword.keyword}")

        return api_response(keyword.to_dict())

    except Exception as e:
        logger.error(f"更新关键词失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/transaction-methods/<int:method_id>/keywords/<int:keyword_id>',
           methods=['DELETE'], need_login=False)
def delete_transaction_keyword(method_id, keyword_id):
    """删除交易方式关键词"""
    try:
        keyword = AdTrackingTransactionMethodKeyword.query.get(keyword_id)
        if not keyword or keyword.method_id != method_id:
            return api_response({}, err_code=5, err_msg='关键词不存在', status_code=404)

        db.session.delete(keyword)
        db.session.commit()

        # 刷新缓存
        KeywordExtractionService.refresh_transaction_matcher_cache()
        logger.info(f"删除关键词: {keyword.keyword}")

        return api_response({'id': keyword_id})

    except Exception as e:
        logger.error(f"删除关键词失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


# ============================================================================
# 地理位置配置管理 API
# ============================================================================

@api.route('/config/geo-locations', methods=['GET'], need_login=False)
def list_geo_locations():
    """
    获取地理位置列表（支持分页和筛选）

    Query Parameters:
        - level: 行政级别 (1=省份, 2=城市, 3=区县) (可选)
        - parent_id: 父级ID (可选)
        - name: 地名 (可选，模糊查询)
        - is_active: 是否启用 (可选)
        - offset: 分页偏移 (默认0)
        - limit: 分页大小 (默认20)
    """
    try:
        level = request.args.get('level', type=int)
        parent_id = request.args.get('parent_id', type=int)
        name = request.args.get('name')
        is_active = request.args.get('is_active', type=lambda x: x.lower() == 'true')
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

        query = AdTrackingGeoLocationMaster.query

        if level:
            query = query.filter_by(level=level)
        if parent_id is not None:
            query = query.filter_by(parent_id=parent_id)
        if name:
            query = query.filter(AdTrackingGeoLocationMaster.name.ilike(f'%{name}%'))

        # 如果指定了 is_active，按其过滤
        is_active_param = request.args.get('is_active')
        if is_active_param is not None:
            query = query.filter_by(is_active=is_active)
        else:
            # 默认只返回启用的
            query = query.filter_by(is_active=True)

        total = query.count()
        locations = query.offset(offset).limit(limit).all()

        return api_response({
            'locations': [loc.to_dict() for loc in locations],
            'total': total,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'page_size': limit
        })

    except Exception as e:
        logger.error(f"获取地理位置列表失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/geo-locations', methods=['POST'], need_login=False)
def create_geo_location():
    """
    创建新的地理位置

    Request Body:
        {
            "level": 1,
            "name": "山东省",
            "parent_id": null,
            "code": "37",
            "latitude": 36.5,
            "longitude": 117.1,
            "aliases": ["山东", "鲁"],
            "short_name": "鲁",
            "description": "中国东部沿海省份"
        }
    """
    try:
        data = request.get_json() or {}

        # 参数验证
        name = data.get('name', '').strip()
        if not name:
            return api_response(
                {},
                err_code=2,
                err_msg='name 不能为空',
                status_code=400
            )

        level = data.get('level')
        if not level or level not in [1, 2, 3]:
            return api_response(
                {},
                err_code=2,
                err_msg='level 必须为 1、2 或 3',
                status_code=400
            )

        # 检查是否已存在
        existing = AdTrackingGeoLocationMaster.query.filter_by(
            name=name,
            level=level
        ).first()
        if existing:
            return api_response(
                {},
                err_code=1,
                err_msg=f'地理位置 "{name}" (级别{level}) 已存在',
                status_code=400
            )

        location = AdTrackingGeoLocationMaster(
            level=level,
            name=name,
            parent_id=data.get('parent_id'),
            code=data.get('code'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            aliases=','.join(data.get('aliases', [])) if data.get('aliases') else None,
            short_name=data.get('short_name'),
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )

        db.session.add(location)
        db.session.commit()

        # 刷新缓存
        GeoLocationService.refresh_geo_matcher_cache()
        logger.info(f"创建地理位置: {name}")

        return api_response({'id': location.id, 'name': location.name}, status_code=201)

    except Exception as e:
        logger.error(f"创建地理位置失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/geo-locations/<int:location_id>', methods=['GET'], need_login=False)
def get_geo_location(location_id):
    """获取地理位置详情"""
    try:
        location = AdTrackingGeoLocationMaster.query.get(location_id)
        if not location:
            return api_response({}, err_code=5, err_msg='地理位置不存在', status_code=404)

        return api_response(location.to_dict())

    except Exception as e:
        logger.error(f"获取地理位置失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/geo-locations/<int:location_id>', methods=['PUT'], need_login=False)
def update_geo_location(location_id):
    """更新地理位置"""
    try:
        location = AdTrackingGeoLocationMaster.query.get(location_id)
        if not location:
            return api_response({}, err_code=5, err_msg='地理位置不存在', status_code=404)

        data = request.get_json() or {}

        # 更新字段
        if 'name' in data:
            location.name = data['name']
        if 'aliases' in data:
            location.aliases = ','.join(data['aliases']) if data['aliases'] else None
        if 'short_name' in data:
            location.short_name = data['short_name']
        if 'latitude' in data:
            location.latitude = data['latitude']
        if 'longitude' in data:
            location.longitude = data['longitude']
        if 'description' in data:
            location.description = data['description']
        if 'is_active' in data:
            location.is_active = data['is_active']

        db.session.commit()

        # 刷新缓存
        GeoLocationService.refresh_geo_matcher_cache()
        logger.info(f"更新地理位置: {location.name}")

        return api_response(location.to_dict())

    except Exception as e:
        logger.error(f"更新地理位置失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/geo-locations/<int:location_id>', methods=['DELETE'], need_login=False)
def delete_geo_location(location_id):
    """删除地理位置"""
    try:
        location = AdTrackingGeoLocationMaster.query.get(location_id)
        if not location:
            return api_response({}, err_code=5, err_msg='地理位置不存在', status_code=404)

        db.session.delete(location)
        db.session.commit()

        # 刷新缓存
        GeoLocationService.refresh_geo_matcher_cache()
        logger.info(f"删除地理位置: {location.name}")

        return api_response({'id': location_id})

    except Exception as e:
        logger.error(f"删除地理位置失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


# ============================================================================
# 黑词分类配置管理 API
# ============================================================================

@api.route('/config/dark-keywords/categories', methods=['GET'], need_login=False)
def list_dark_keyword_categories():
    """
    获取所有黑词分类

    Query Parameters:
        - is_active: 是否启用 (可选，true/false)
        - offset: 分页偏移 (默认0)
        - limit: 分页大小 (默认20)
    """
    try:
        is_active = request.args.get('is_active', type=lambda x: x.lower() == 'true')
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

        query = AdTrackingDarkKeywordCategory.query

        # 如果指定了 is_active，按其过滤
        is_active_param = request.args.get('is_active')
        if is_active_param is not None:
            query = query.filter_by(is_active=is_active)

        total = query.count()
        categories = query.order_by(AdTrackingDarkKeywordCategory.priority.desc())\
            .offset(offset).limit(limit).all()

        return api_response({
            'categories': [c.to_dict(include_drugs=False) for c in categories],
            'total': total,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'page_size': limit
        })

    except Exception as e:
        logger.error(f"获取黑词分类列表失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/categories', methods=['POST'], need_login=False)
def create_dark_keyword_category():
    """
    创建新的黑词分类

    Request Body:
        {
            "name": "毒品相关",
            "display_name": "毒品类",
            "description": "毒品相关的黑词",
            "priority": 10
        }
    """
    try:
        data = request.get_json() or {}

        # 参数验证
        name = data.get('name', '').strip()
        if not name:
            return api_response(
                {},
                err_code=2,
                err_msg='name 不能为空',
                status_code=400
            )

        # 检查是否已存在
        existing = AdTrackingDarkKeywordCategory.query.filter_by(name=name).first()
        if existing:
            return api_response(
                {},
                err_code=1,
                err_msg=f'分类 "{name}" 已存在',
                status_code=400
            )

        category = AdTrackingDarkKeywordCategory(
            name=name,
            display_name=data.get('display_name'),
            description=data.get('description'),
            priority=data.get('priority', 0),
            is_active=data.get('is_active', True)
        )

        db.session.add(category)
        db.session.commit()

        logger.info(f"创建黑词分类: {name}")

        return api_response({'id': category.id, 'name': category.name}, status_code=201)

    except Exception as e:
        logger.error(f"创建黑词分类失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/categories/<int:category_id>', methods=['GET'], need_login=False)
def get_dark_keyword_category(category_id):
    """获取黑词分类详情"""
    try:
        category = AdTrackingDarkKeywordCategory.query.get(category_id)
        if not category:
            return api_response({}, err_code=5, err_msg='分类不存在', status_code=404)

        return api_response(category.to_dict(include_drugs=True))

    except Exception as e:
        logger.error(f"获取黑词分类详情失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/categories/<int:category_id>', methods=['PUT'], need_login=False)
def update_dark_keyword_category(category_id):
    """更新黑词分类"""
    try:
        category = AdTrackingDarkKeywordCategory.query.get(category_id)
        if not category:
            return api_response({}, err_code=5, err_msg='分类不存在', status_code=404)

        data = request.get_json() or {}

        # 更新字段
        if 'display_name' in data:
            category.display_name = data['display_name']
        if 'description' in data:
            category.description = data['description']
        if 'priority' in data:
            category.priority = data['priority']
        if 'is_active' in data:
            category.is_active = data['is_active']

        db.session.commit()

        logger.info(f"更新黑词分类: {category.name}")

        return api_response(category.to_dict(include_drugs=False))

    except Exception as e:
        logger.error(f"更新黑词分类失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/categories/<int:category_id>', methods=['DELETE'], need_login=False)
def delete_dark_keyword_category(category_id):
    """删除黑词分类"""
    try:
        category = AdTrackingDarkKeywordCategory.query.get(category_id)
        if not category:
            return api_response({}, err_code=5, err_msg='分类不存在', status_code=404)

        db.session.delete(category)
        db.session.commit()

        logger.info(f"删除黑词分类: {category.name}")

        return api_response({'id': category_id})

    except Exception as e:
        logger.error(f"删除黑词分类失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


# ============================================================================
# 黑词毒品配置管理 API
# ============================================================================

@api.route('/config/dark-keywords/drugs', methods=['GET'], need_login=False)
def list_dark_keyword_drugs():
    """
    获取所有毒品配置

    Query Parameters:
        - category_id: 分类ID (可选)
        - is_active: 是否启用 (可选，true/false)
        - offset: 分页偏移 (默认0)
        - limit: 分页大小 (默认20)
    """
    try:
        category_id = request.args.get('category_id', type=int)
        is_active = request.args.get('is_active', type=lambda x: x.lower() == 'true')
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

        query = AdTrackingDarkKeywordDrug.query

        if category_id:
            query = query.filter_by(category_id=category_id)

        # 如果指定了 is_active，按其过滤
        is_active_param = request.args.get('is_active')
        if is_active_param is not None:
            query = query.filter_by(is_active=is_active)

        total = query.count()
        drugs = query.order_by(AdTrackingDarkKeywordDrug.priority.desc())\
            .offset(offset).limit(limit).all()

        return api_response({
            'drugs': [d.to_dict() for d in drugs],
            'total': total,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'page_size': limit
        })

    except Exception as e:
        logger.error(f"获取毒品列表失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/drugs', methods=['POST'], need_login=False)
def create_dark_keyword_drug():
    """
    创建新的毒品配置

    Request Body:
        {
            "category_id": 1,
            "name": "冰毒",
            "display_name": "甲基苯丙胺",
            "description": "常见合成毒品",
            "priority": 10
        }
    """
    try:
        data = request.get_json() or {}

        # 参数验证
        category_id = data.get('category_id')
        if not category_id:
            return api_response(
                {},
                err_code=2,
                err_msg='category_id 不能为空',
                status_code=400
            )

        category = AdTrackingDarkKeywordCategory.query.get(category_id)
        if not category:
            return api_response(
                {},
                err_code=5,
                err_msg='分类不存在',
                status_code=400
            )

        name = data.get('name', '').strip()
        if not name:
            return api_response(
                {},
                err_code=2,
                err_msg='name 不能为空',
                status_code=400
            )

        # 检查是否已存在
        existing = AdTrackingDarkKeywordDrug.query.filter_by(
            category_id=category_id,
            name=name
        ).first()
        if existing:
            return api_response(
                {},
                err_code=1,
                err_msg=f'毒品 "{name}" 在该分类下已存在',
                status_code=400
            )

        drug = AdTrackingDarkKeywordDrug(
            category_id=category_id,
            name=name,
            display_name=data.get('display_name'),
            description=data.get('description'),
            priority=data.get('priority', 0),
            is_active=data.get('is_active', True)
        )

        db.session.add(drug)
        db.session.commit()

        logger.info(f"创建毒品配置: {name}")

        return api_response({'id': drug.id, 'name': drug.name}, status_code=201)

    except Exception as e:
        logger.error(f"创建毒品配置失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/drugs/<int:drug_id>', methods=['GET'], need_login=False)
def get_dark_keyword_drug(drug_id):
    """获取毒品详情"""
    try:
        drug = AdTrackingDarkKeywordDrug.query.get(drug_id)
        if not drug:
            return api_response({}, err_code=5, err_msg='毒品不存在', status_code=404)

        return api_response(drug.to_dict())

    except Exception as e:
        logger.error(f"获取毒品详情失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/drugs/<int:drug_id>', methods=['PUT'], need_login=False)
def update_dark_keyword_drug(drug_id):
    """更新毒品配置"""
    try:
        drug = AdTrackingDarkKeywordDrug.query.get(drug_id)
        if not drug:
            return api_response({}, err_code=5, err_msg='毒品不存在', status_code=404)

        data = request.get_json() or {}

        # 更新字段
        if 'display_name' in data:
            drug.display_name = data['display_name']
        if 'description' in data:
            drug.description = data['description']
        if 'priority' in data:
            drug.priority = data['priority']
        if 'is_active' in data:
            drug.is_active = data['is_active']

        db.session.commit()

        logger.info(f"更新毒品配置: {drug.name}")

        return api_response(drug.to_dict())

    except Exception as e:
        logger.error(f"更新毒品配置失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/drugs/<int:drug_id>', methods=['DELETE'], need_login=False)
def delete_dark_keyword_drug(drug_id):
    """删除毒品配置"""
    try:
        drug = AdTrackingDarkKeywordDrug.query.get(drug_id)
        if not drug:
            return api_response({}, err_code=5, err_msg='毒品不存在', status_code=404)

        db.session.delete(drug)
        db.session.commit()

        logger.info(f"删除毒品配置: {drug.name}")

        return api_response({'id': drug_id})

    except Exception as e:
        logger.error(f"删除毒品配置失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


# ============================================================================
# 黑词关键词管理 API
# ============================================================================

@api.route('/config/dark-keywords/drugs/<int:drug_id>/keywords', methods=['GET'], need_login=False)
def list_dark_keywords(drug_id):
    """获取毒品的所有关键词"""
    try:
        drug = AdTrackingDarkKeywordDrug.query.get(drug_id)
        if not drug:
            return api_response({}, err_code=5, err_msg='毒品不存在', status_code=404)

        keywords = AdTrackingDarkKeywordKeyword.query.filter_by(
            drug_id=drug_id
        ).order_by(AdTrackingDarkKeywordKeyword.weight.desc()).all()

        return api_response({
            'keywords': [kw.to_dict() for kw in keywords]
        })

    except Exception as e:
        logger.error(f"获取关键词列表失败: {e}", exc_info=True)
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/keywords', methods=['POST'], need_login=False)
def create_dark_keyword():
    """
    创建黑词关键词

    Request Body:
        {
            "drug_id": 1,
            "keyword": "冰",
            "weight": 1,
            "is_active": true
        }
    """
    try:
        data = request.get_json() or {}

        # 参数验证
        drug_id = data.get('drug_id')
        if not drug_id:
            return api_response(
                {},
                err_code=2,
                err_msg='drug_id 不能为空',
                status_code=400
            )

        drug = AdTrackingDarkKeywordDrug.query.get(drug_id)
        if not drug:
            return api_response(
                {},
                err_code=5,
                err_msg='毒品不存在',
                status_code=400
            )

        keyword_text = data.get('keyword', '').strip()
        if not keyword_text:
            return api_response(
                {},
                err_code=2,
                err_msg='keyword 不能为空',
                status_code=400
            )

        # 检查是否已存在
        existing = AdTrackingDarkKeywordKeyword.query.filter_by(
            drug_id=drug_id,
            keyword=keyword_text
        ).first()
        if existing:
            return api_response(
                {},
                err_code=1,
                err_msg=f'关键词 "{keyword_text}" 已存在',
                status_code=400
            )

        keyword = AdTrackingDarkKeywordKeyword(
            drug_id=drug_id,
            keyword=keyword_text,
            weight=data.get('weight', 1),
            is_active=data.get('is_active', True)
        )

        db.session.add(keyword)
        db.session.commit()

        logger.info(f"创建关键词: {keyword_text}")

        return api_response({'id': keyword.id}, status_code=201)

    except Exception as e:
        logger.error(f"创建关键词失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/keywords/<int:keyword_id>', methods=['PUT'], need_login=False)
def update_dark_keyword(keyword_id):
    """更新黑词关键词"""
    try:
        keyword = AdTrackingDarkKeywordKeyword.query.get(keyword_id)
        if not keyword:
            return api_response({}, err_code=5, err_msg='关键词不存在', status_code=404)

        data = request.get_json() or {}

        if 'is_active' in data:
            keyword.is_active = data['is_active']
        if 'weight' in data:
            keyword.weight = data['weight']

        db.session.commit()

        logger.info(f"更新关键词: {keyword.keyword}")

        return api_response(keyword.to_dict())

    except Exception as e:
        logger.error(f"更新关键词失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)


@api.route('/config/dark-keywords/keywords/<int:keyword_id>', methods=['DELETE'], need_login=False)
def delete_dark_keyword_config(keyword_id):
    """删除黑词关键词"""
    try:
        keyword = AdTrackingDarkKeywordKeyword.query.get(keyword_id)
        if not keyword:
            return api_response({}, err_code=5, err_msg='关键词不存在', status_code=404)

        db.session.delete(keyword)
        db.session.commit()

        logger.info(f"删除关键词: {keyword.keyword}")

        return api_response({'id': keyword_id})

    except Exception as e:
        logger.error(f"删除关键词失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response({}, err_code=99, err_msg='服务器错误', status_code=500)

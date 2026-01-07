"""地理位置服务 - 管理地理数据和地名提取"""
import logging
import time
from typing import List, Dict, Any

from flask import has_app_context, current_app
from jd.helpers.keyword_matcher import AhoCorasickMatcher

logger = logging.getLogger(__name__)


class GeoLocationService:
    """地理位置处理服务 - 数据库驱动 + AC自动机优化"""

    _GEO_MATCHER = None
    _LAST_LOAD_TIME = None
    _LOAD_INTERVAL = 3600  # 1小时更新一次

    @classmethod
    def _should_reload_geo_data(cls) -> bool:
        """检查是否需要重新加载地理位置数据"""
        current_time = time.time()

        if cls._LAST_LOAD_TIME is None:
            return True

        return (current_time - cls._LAST_LOAD_TIME) > cls._LOAD_INTERVAL

    @classmethod
    def _build_geo_matcher(cls) -> AhoCorasickMatcher:
        """从数据库构建地理位置AC自动机"""
        try:
            from jd.models.ad_tracking_geo_location_master import AdTrackingGeoLocationMaster
            from jd import db as app_db
        except ImportError:
            logger.warning("无法导入地理位置主表模型，返回空匹配器")
            return AhoCorasickMatcher(case_sensitive=False)

        if cls._GEO_MATCHER and not cls._should_reload_geo_data():
            return cls._GEO_MATCHER

        logger.info("Building geographic AC matcher from database")

        matcher = AhoCorasickMatcher(case_sensitive=False)

        try:
            # 如果没有应用上下文，从 Flask 应用获取
            if not has_app_context():
                logger.warning("无应用上下文，尝试从 current_app 获取...")
                try:
                    # 尝试直接从 SQLAlchemy session 查询
                    geo_data = app_db.session.query(AdTrackingGeoLocationMaster).filter_by(is_active=True).all()
                except Exception as ctx_error:
                    logger.warning(f"无应用上下文，无法从数据库加载地理位置数据: {ctx_error}")
                    matcher.build()
                    return matcher
            else:
                geo_data = AdTrackingGeoLocationMaster.query.filter_by(is_active=True).all()

            # 为地理位置数据添加父级名称
            parent_map = {}  # parent_id -> parent_name
            for location in geo_data:
                if location.parent_id and location.level > 1:  # 非省级别，查找父级
                    parent = next((p for p in geo_data if p.id == location.parent_id), None)
                    if parent:
                        parent_map[location.parent_id] = parent.name

            for location in geo_data:
                # 添加主名称
                parent_name = parent_map.get(location.parent_id) if location.parent_id else None

                metadata = {
                    'type': ['province', 'city', 'district'][location.level - 1],
                    'id': location.id,
                    'name': location.name,
                    'level': location.level,
                    'parent_id': location.parent_id,
                    'parent_name': parent_name,  # 填充父级名称
                    'latitude': float(location.latitude) if location.latitude else None,
                    'longitude': float(location.longitude) if location.longitude else None,
                }
                matcher.add_keyword(location.name, metadata)

                # 添加别名（使用相同的metadata，包括parent_name）
                if location.aliases:
                    for alias in location.aliases.split(','):
                        alias = alias.strip()
                        if alias:
                            matcher.add_keyword(alias, metadata)

                # 添加简称（使用相同的metadata，包括parent_name）
                if location.short_name:
                    matcher.add_keyword(location.short_name, metadata)

            matcher.build()

            cls._GEO_MATCHER = matcher
            cls._LAST_LOAD_TIME = time.time()

            stats = matcher.get_stats()
            logger.info(f"Geographic matcher built: {stats['keyword_count']} keywords")
        except Exception as e:
            logger.error(f"构建地理位置matcher失败: {e}")
            # 返回空matcher
            matcher.build()

        return matcher

    @classmethod
    def extract_locations(cls, text: str, chat_id: int) -> List[Dict]:
        """
        从文本中提取地理位置

        使用 AC自动机 进行高效匹配
        性能：O(n + z) 其中 n=文本长度，z=匹配数

        Args:
            text: 输入文本
            chat_id: 群组ID

        Returns:
            list: 地理位置列表，每个元素包含：
                {
                    'id': 地理位置ID,
                    'type': 'province'|'city'|'district',
                    'name': '山东省',
                    'level': 1,
                    'parent_id': None,
                    'parent_name': '省份名称',  # 新增字段
                    'latitude': 36.5,
                    'longitude': 117.1,
                    'keyword_matched': '山东'
                }
        """
        if not text or not text.strip():
            return []

        try:
            matcher = cls._build_geo_matcher()
            matches = matcher.search_unique(text)

            locations = []
            for match in matches:
                metadata = match['metadata']

                # 构建返回结果，省份字段将根据匹配到的类型填充
                location_info = {
                    'id': metadata['id'],
                    'type': metadata['type'],
                    'name': metadata['name'],
                    'level': metadata['level'],
                    'parent_id': metadata['parent_id'],
                    'latitude': metadata['latitude'],
                    'longitude': metadata['longitude'],
                    'keyword_matched': match['keyword']
                }

                # 如果匹配到的是城市或区县，且有其省份信息，则在province字段填充
                if metadata['type'] in ['city', 'district'] and metadata['parent_name']:
                    location_info['province'] = metadata['parent_name']
                elif metadata['type'] == 'province':
                    location_info['province'] = metadata['name']
                else:
                    location_info['province'] = None

                # city字段只对city类型有效
                if metadata['type'] == 'city':
                    location_info['city'] = metadata['name']
                else:
                    location_info['city'] = None

                # district字段只对district类型有效
                if metadata['type'] == 'district':
                    location_info['district'] = metadata['name']
                else:
                    location_info['district'] = None

                locations.append(location_info)

            return locations
        except Exception as e:
            logger.error(f"地理位置提取失败: {e}")
            return []

    @staticmethod
    def refresh_geo_matcher_cache():
        """刷新地理位置matcher缓存（在更新配置后调用）"""
        GeoLocationService._GEO_MATCHER = None
        GeoLocationService._LAST_LOAD_TIME = None
        logger.info("Geographic matcher cache cleared")

    @classmethod
    def get_location_by_id(cls, location_id: int) -> Dict:
        """
        根据地理位置ID获取详细信息

        Args:
            location_id: 地理位置ID

        Returns:
            dict: 地理位置详细信息，包含坐标、别名等
        """
        try:
            from jd.models.ad_tracking_geo_location_master import AdTrackingGeoLocationMaster

            # 确保有应用上下文
            if not has_app_context():
                logger.warning("无应用上下文，无法获取地理位置详情")
                return {}

            location = AdTrackingGeoLocationMaster.query.get(location_id)
            if not location:
                return {}

            return {
                'id': location.id,
                'name': location.name,
                'level': location.level,
                'parent_id': location.parent_id,
                'latitude': float(location.latitude) if location.latitude else None,
                'longitude': float(location.longitude) if location.longitude else None,
                'short_name': location.short_name,
                'aliases': location.aliases.split(',') if location.aliases else [],
                'is_active': location.is_active
            }
        except Exception as e:
            logger.error(f"获取地理位置详情失败: {e}")
            return {}

    @classmethod
    def get_children_locations(cls, parent_id: int) -> List[Dict]:
        """
        获取指定地理位置的子级地点

        Args:
            parent_id: 父级地理位置ID

        Returns:
            list: 子级地点列表
        """
        try:
            from jd.models.ad_tracking_geo_location_master import AdTrackingGeoLocationMaster

            # 确保有应用上下文
            if not has_app_context():
                logger.warning("无应用上下文，无法获取子级地点")
                return []

            children = AdTrackingGeoLocationMaster.query.filter_by(
                parent_id=parent_id,
                is_active=True
            ).all()

            return [
                {
                    'id': child.id,
                    'name': child.name,
                    'level': child.level,
                    'latitude': float(child.latitude) if child.latitude else None,
                    'longitude': float(child.longitude) if child.longitude else None,
                }
                for child in children
            ]
        except Exception as e:
            logger.error(f"获取子级地点失败: {e}")
            return []

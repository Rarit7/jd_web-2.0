"""黑词提取服务 - 从聊天记录中提取黑词（毒品相关关键词）"""
import logging
import time
from typing import List, Dict, Optional

from flask import has_app_context
from jd.helpers.keyword_matcher import AhoCorasickMatcher

logger = logging.getLogger(__name__)


class DarkKeywordExtractionService:
    """黑词提取服务 - 数据库驱动 + AC自动机优化"""

    # 黑词AC自动机缓存
    _dark_keyword_matcher = None
    _matcher_update_time = None
    _matcher_cache_ttl = 3600  # 缓存1小时

    @classmethod
    def _should_refresh_matcher(cls) -> bool:
        """检查是否需要刷新matcher缓存"""
        current_time = time.time()

        if cls._matcher_update_time is None:
            return True

        return (current_time - cls._matcher_update_time) > cls._matcher_cache_ttl

    @classmethod
    def _build_dark_keyword_matcher(cls) -> AhoCorasickMatcher:
        """从数据库构建黑词AC自动机"""
        try:
            from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeywordKeyword
            from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeywordDrug
            from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeywordCategory
            from jd import db as app_db
        except ImportError:
            logger.warning("无法导入黑词配置模型，返回空匹配器")
            return AhoCorasickMatcher(case_sensitive=False)

        # 检查缓存有效性
        if cls._dark_keyword_matcher and not cls._should_refresh_matcher():
            return cls._dark_keyword_matcher

        logger.info("Building dark keyword AC matcher from database")

        matcher = AhoCorasickMatcher(case_sensitive=False)

        try:
            # 如果没有应用上下文，从 SQLAlchemy session 获取
            if not has_app_context():
                logger.warning("无应用上下文，尝试从 SQLAlchemy session 获取...")
                try:
                    keywords = app_db.session.query(
                        AdTrackingDarkKeywordKeyword,
                        AdTrackingDarkKeywordDrug,
                        AdTrackingDarkKeywordCategory
                    ).join(
                        AdTrackingDarkKeywordDrug,
                        AdTrackingDarkKeywordKeyword.drug_id == AdTrackingDarkKeywordDrug.id
                    ).join(
                        AdTrackingDarkKeywordCategory,
                        AdTrackingDarkKeywordDrug.category_id == AdTrackingDarkKeywordCategory.id
                    ).filter(
                        AdTrackingDarkKeywordKeyword.is_active == True,
                        AdTrackingDarkKeywordDrug.is_active == True,
                        AdTrackingDarkKeywordCategory.is_active == True
                    ).all()
                except Exception as ctx_error:
                    logger.warning(f"无应用上下文，无法从数据库加载黑词: {ctx_error}")
                    matcher.build()
                    return matcher
            else:
                # 从数据库获取所有启用的黑词关键词（包含关联的毒品和分类信息）
                keywords = app_db.session.query(
                    AdTrackingDarkKeywordKeyword,
                    AdTrackingDarkKeywordDrug,
                    AdTrackingDarkKeywordCategory
                ).join(
                    AdTrackingDarkKeywordDrug,
                    AdTrackingDarkKeywordKeyword.drug_id == AdTrackingDarkKeywordDrug.id
                ).join(
                    AdTrackingDarkKeywordCategory,
                    AdTrackingDarkKeywordDrug.category_id == AdTrackingDarkKeywordCategory.id
                ).filter(
                    AdTrackingDarkKeywordKeyword.is_active == True,
                    AdTrackingDarkKeywordDrug.is_active == True,
                    AdTrackingDarkKeywordCategory.is_active == True
                ).all()

            # 添加关键词到匹配器
            for keyword_obj, drug_obj, category_obj in keywords:
                metadata = {
                    'keyword_id': keyword_obj.id,
                    'drug_id': drug_obj.id,
                    'drug_name': drug_obj.display_name or drug_obj.name,
                    'category_id': category_obj.id,
                    'category_name': category_obj.name,
                    'weight': keyword_obj.weight
                }
                matcher.add_keyword(keyword_obj.keyword, metadata)

            matcher.build()

            cls._dark_keyword_matcher = matcher
            cls._matcher_update_time = time.time()

            stats = matcher.get_stats()
            logger.info(f"Dark keyword matcher built: {stats['keyword_count']} keywords")
        except Exception as e:
            logger.error(f"构建黑词matcher失败: {e}")
            # 返回空matcher
            matcher.build()

        return matcher

    @classmethod
    def extract_dark_keywords(cls, text: str) -> List[Dict]:
        """
        使用 AC自动机 提取黑词

        性能：O(n + z) 其中 n=文本长度，z=匹配数

        Args:
            text: 输入文本

        Returns:
            list: 提取的黑词列表，每个元素包含：
                {
                    'keyword': '冰毒',
                    'drug_id': 1,
                    'drug_name': '冰毒',
                    'category_id': 1,
                    'category_name': '毒品相关',
                    'weight': 3,
                    'confidence': 0.9
                }
        """
        if not text or not text.strip():
            return []

        try:
            matcher = cls._build_dark_keyword_matcher()
            matches = matcher.search_unique(text)

            results = []
            seen = set()  # 用于去重：(drug_id, keyword)

            for match in matches:
                metadata = match['metadata']
                drug_id = metadata['drug_id']
                keyword = match['keyword']

                # 去重：同一个毒品的关键词只保留权重最高的
                key = (drug_id, keyword)
                if key not in seen:
                    results.append({
                        'keyword': keyword,
                        'drug_id': drug_id,
                        'drug_name': metadata['drug_name'],
                        'category_id': metadata['category_id'],
                        'category_name': metadata['category_name'],
                        'weight': metadata['weight'],
                        'confidence': 0.9
                    })
                    seen.add(key)

            return results
        except Exception as e:
            logger.error(f"黑词提取失败: {e}")
            return []

    @classmethod
    def extract_dark_keywords_with_count(cls, text: str) -> List[Dict]:
        """
        提取黑词并统计每个关键词在文本中出现的次数

        Args:
            text: 输入文本

        Returns:
            list: 提取的黑词列表，每个元素包含：
                {
                    'keyword': '冰毒',
                    'drug_id': 1,
                    'drug_name': '冰毒',
                    'category_id': 1,
                    'category_name': '毒品相关',
                    'count': 2,  # 该关键词在文本中出现的次数
                    'weight': 3,
                    'confidence': 0.9
                }
        """
        if not text or not text.strip():
            return []

        try:
            matcher = cls._build_dark_keyword_matcher()
            # 获取所有匹配（包括重复的）
            all_matches = matcher.search(text)

            # 统计每个关键词出现的次数
            keyword_counts = {}
            keyword_metadata = {}

            for match in all_matches:
                keyword = match['keyword']
                metadata = match['metadata']

                if keyword not in keyword_metadata:
                    keyword_metadata[keyword] = metadata

                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

            # 构建结果
            results = []
            for keyword, count in keyword_counts.items():
                metadata = keyword_metadata[keyword]
                results.append({
                    'keyword': keyword,
                    'drug_id': metadata['drug_id'],
                    'drug_name': metadata['drug_name'],
                    'category_id': metadata['category_id'],
                    'category_name': metadata['category_name'],
                    'count': count,
                    'weight': metadata['weight'],
                    'confidence': 0.9
                })

            # 按权重降序排序
            results.sort(key=lambda x: x['weight'], reverse=True)

            return results
        except Exception as e:
            logger.error(f"黑词提取（带计数）失败: {e}")
            return []

    @staticmethod
    def refresh_matcher_cache():
        """刷新黑词matcher缓存（在更新配置后调用）"""
        DarkKeywordExtractionService._dark_keyword_matcher = None
        DarkKeywordExtractionService._matcher_update_time = None
        logger.info("Dark keyword matcher cache cleared")

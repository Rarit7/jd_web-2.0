from jd import db
from jd.models.ad_tracking_record import AdTrackingRecord
from jd.models.ad_tracking_processing_batch import AdTrackingProcessingBatch
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tag_keyword_mapping import TagKeywordMapping
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
import json


class AdTrackingService:
    """广告追踪服务类"""

    @staticmethod
    def get_records_statistics(channel_id=None, days=30):
        """
        获取广告记录统计信息

        Args:
            channel_id: 频道ID（可选）
            days: 统计天数

        Returns:
            dict: 统计信息
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # 基础查询
        query = AdTrackingRecord.query.filter(
            AdTrackingRecord.created_at >= cutoff_date
        )

        if channel_id:
            query = query.filter_by(channel_id=channel_id)

        # 总记录数
        total_records = query.count()

        # 按频道统计
        channel_stats = db.session.query(
            AdTrackingRecord.channel_id,
            AdTrackingRecord.channel_name,
            func.count(AdTrackingRecord.id).label('count')
        ).filter(
            AdTrackingRecord.created_at >= cutoff_date
        ).group_by(
            AdTrackingRecord.channel_id,
            AdTrackingRecord.channel_name
        ).order_by(
            desc('count')
        ).limit(10).all()

        # 按关键词统计
        keyword_stats = db.session.query(
            AdTrackingRecord.trigger_keyword,
            func.count(AdTrackingRecord.id).label('count')
        ).filter(
            AdTrackingRecord.created_at >= cutoff_date
        ).group_by(
            AdTrackingRecord.trigger_keyword
        ).order_by(
            desc('count')
        ).limit(10).all()

        # 按日期统计
        date_stats = db.session.query(
            func.date(AdTrackingRecord.created_at).label('date'),
            func.count(AdTrackingRecord.id).label('count')
        ).filter(
            AdTrackingRecord.created_at >= cutoff_date
        ).group_by(
            func.date(AdTrackingRecord.created_at)
        ).order_by('date').all()

        # 处理日期统计
        date_stats_dict = {}
        for stat in date_stats:
            date_stats_dict[stat.date.strftime('%Y-%m-%d')] = stat.count

        return {
            'total_records': total_records,
            'channel_stats': [
                {
                    'channel_id': stat.channel_id,
                    'channel_name': stat.channel_name,
                    'count': stat.count
                } for stat in channel_stats
            ],
            'keyword_stats': [
                {
                    'keyword': stat.trigger_keyword,
                    'count': stat.count
                } for stat in keyword_stats
            ],
            'date_stats': date_stats_dict
        }

    @staticmethod
    def get_channel_message_count(channel_id, start_date=None, end_date=None):
        """
        获取频道的消息数量

        Args:
            channel_id: 频道ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            int: 消息数量
        """
        query = TgGroupChatHistory.query.filter_by(
            group_id=channel_id,
            is_deleted=False
        )

        if start_date:
            query = query.filter(TgGroupChatHistory.postal_time >= start_date)
        if end_date:
            query = query.filter(TgGroupChatHistory.postal_time <= end_date)

        return query.count()

    @staticmethod
    def get_batch_summary(batch_id):
        """
        获取处理批次摘要信息

        Args:
            batch_id: 批次ID

        Returns:
            dict: 批次摘要信息
        """
        batch = AdTrackingProcessingBatch.query.get(batch_id)
        if not batch:
            return None

        # 获取批次创建的广告记录
        records = AdTrackingRecord.query.filter_by(
            process_batch_id=batch_id
        ).all()

        # 统计信息
        total_records = len(records)
        processed_records = sum(1 for r in records if r.is_processed)

        # 关键词分布
        keyword_stats = {}
        for record in records:
            keyword = record.trigger_keyword
            keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1

        return {
            'batch_id': batch_id,
            'channel_id': batch.channel_id,
            'total_records': total_records,
            'processed_records': processed_records,
            'progress_percent': (processed_records / total_records * 100) if total_records > 0 else 0,
            'keyword_distribution': keyword_stats,
            'started_at': batch.started_at.isoformat() if batch.started_at else None,
            'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
            'status': batch.status,
            'error_message': batch.error_message
        }

    @staticmethod
    def check_channel_processing_status(channel_id):
        """
        检查频道的处理状态

        Args:
            channel_id: 频道ID

        Returns:
            dict: 处理状态信息
        """
        # 查找最近的处理批次
        batch = AdTrackingProcessingBatch.query.filter_by(
            channel_id=channel_id
        ).order_by(
            AdTrackingProcessingBatch.created_at.desc()
        ).first()

        if not batch:
            return {
                'has_processing': False,
                'status': None,
                'last_processed': None
            }

        return {
            'has_processing': True,
            'batch_id': batch.id,
            'status': batch.status,
            'progress': batch.get_progress(),
            'started_at': batch.started_at.isoformat() if batch.started_at else None,
            'last_processed': batch.created_at.isoformat()
        }

    @staticmethod
    def get_related_records(record_id, limit=5):
        """
        获取相关的广告记录

        Args:
            record_id: 记录ID
            limit: 返回数量限制

        Returns:
            list: 相关记录列表
        """
        record = AdTrackingRecord.query.get(record_id)
        if not record:
            return []

        # 查找相关记录（相同频道或相同关键词）
        related_records = AdTrackingRecord.query.filter(
            or_(
                AdTrackingRecord.channel_id == record.channel_id,
                AdTrackingRecord.trigger_keyword == record.trigger_keyword
            ),
            AdTrackingRecord.id != record_id
        ).order_by(
            desc(AdTrackingRecord.send_time)
        ).limit(limit).all()

        return [r.to_dict() for r in related_records]

    @staticmethod
    def calculate_message_similarity(text1, text2):
        """
        计算两条消息的相似度

        Args:
            text1: 消息1文本
            text2: 消息2文本

        Returns:
            float: 相似度得分 (0-1)
        """
        if not text1 or not text2:
            return 0.0

        # 简单的基于词集的相似度计算
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        # 计算交集和并集
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        # Jaccard相似度
        similarity = len(intersection) / len(union) if union else 0.0

        return similarity

    @staticmethod
    def get_duplicate_records(channel_id, days=7):
        """
        获取重复的广告记录

        Args:
            channel_id: 频道ID
            days: 检查最近几天

        Returns:
            list: 重复记录列表
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        # 查找重复记录
        duplicates = db.session.query(
            AdTrackingRecord.channel_id,
            AdTrackingRecord.message_id,
            AdTrackingRecord.trigger_keyword,
            func.count(AdTrackingRecord.id).label('count')
        ).filter(
            AdTrackingRecord.channel_id == channel_id,
            AdTrackingRecord.created_at >= cutoff_date
        ).group_by(
            AdTrackingRecord.channel_id,
            AdTrackingRecord.message_id,
            AdTrackingRecord.trigger_keyword
        ).having(
            func.count(AdTrackingRecord.id) > 1
        ).all()

        duplicate_records = []

        for duplicate in duplicates:
            # 获取所有重复的记录
            records = AdTrackingRecord.query.filter(
                AdTrackingRecord.channel_id == duplicate.channel_id,
                AdTrackingRecord.message_id == duplicate.message_id,
                AdTrackingRecord.trigger_keyword == duplicate.trigger_keyword
            ).order_by(
                desc(AdTrackingRecord.created_at)
            ).all()

            duplicate_records.append({
                'channel_id': duplicate.channel_id,
                'message_id': duplicate.message_id,
                'trigger_keyword': duplicate.trigger_keyword,
                'count': duplicate.count,
                'records': [r.to_dict() for r in records]
            })

        return duplicate_records

    @staticmethod
    def batch_update_records_status(record_ids, is_processed):
        """
        批量更新记录状态

        Args:
            record_ids: 记录ID列表
            is_processed: 是否已处理

        Returns:
            int: 更新的记录数
        """
        updated = AdTrackingRecord.query.filter(
            AdTrackingRecord.id.in_(record_ids)
        ).update(
            {'is_processed': is_processed},
            synchronize_session=False
        )

        db.session.commit()
        return updated

    @staticmethod
    def export_records_by_criteria(criteria):
        """
        根据条件导出记录

        Args:
            criteria: 导出条件字典

        Returns:
            list: 记录列表
        """
        query = AdTrackingRecord.query

        # 应用过滤条件
        if 'channel_ids' in criteria:
            query = query.filter(
                AdTrackingRecord.channel_id.in_(criteria['channel_ids'])
            )

        if 'trigger_keywords' in criteria:
            query = query.filter(
                AdTrackingRecord.trigger_keyword.in_(criteria['trigger_keywords'])
            )

        if 'start_date' in criteria:
            query = query.filter(
                AdTrackingRecord.send_time >= criteria['start_date']
            )

        if 'end_date' in criteria:
            query = query.filter(
                AdTrackingRecord.send_time <= criteria['end_date']
            )

        if 'is_processed' in criteria:
            query = query.filter_by(
                is_processed=criteria['is_processed']
            )

        # 排序和限制
        if 'order_by' in criteria:
            order_field = getattr(AdTrackingRecord, criteria['order_by'], AdTrackingRecord.send_time)
            if criteria.get('order_desc', True):
                query = query.order_by(desc(order_field))
            else:
                query = query.order_by(order_field)

        limit = criteria.get('limit', 10000)
        if limit:
            query = query.limit(limit)

        return query.all()
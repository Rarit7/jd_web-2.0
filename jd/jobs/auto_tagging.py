import datetime
import logging
from typing import Dict, List, Any, Optional

from jd import app, db
from jd.models.tag_keyword_mapping import TagKeywordMapping
from jd.models.auto_tag_log import AutoTagLog
from jd.models.tg_group_user_tag import TgGroupUserTag
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_user_info_change import TgUserInfoChange

logger = logging.getLogger(__name__)


class AutoTaggingService:
    """
    自动标签服务
    负责根据关键词自动为用户添加标签
    """

    def __init__(self):
        self._keyword_cache = {}  # 关键词映射缓存
        self._cache_timestamp = None  # 缓存时间戳
        self._cache_ttl = 300  # 缓存5分钟

    def _get_keyword_mappings(self) -> List[TagKeywordMapping]:
        """获取所有激活的关键词映射，带缓存机制"""
        current_time = datetime.datetime.now()

        # 检查缓存是否有效
        if (self._cache_timestamp and
            (current_time - self._cache_timestamp).total_seconds() < self._cache_ttl and
            self._keyword_cache):
            logger.debug("Using cached keyword mappings")
            return self._keyword_cache

        # 重新获取数据
        mappings = TagKeywordMapping.query.filter_by(is_active=True).all()
        self._keyword_cache = mappings
        self._cache_timestamp = current_time

        logger.info(f"Loaded {len(mappings)} active keyword mappings")
        return mappings

    def process_text_for_tags(self, text: str, user_id: str, source_type: str,
                             source_id: str = None) -> List[Dict[str, Any]]:
        """
        处理文本进行自动标签匹配

        Args:
            text: 要处理的文本
            user_id: 用户ID
            source_type: 来源类型 (chat, nickname, desc)
            source_id: 来源记录ID

        Returns:
            匹配到的标签信息列表
        """
        if not text or not text.strip():
            return []

        keyword_mappings = self._get_keyword_mappings()
        matched_tags = []

        for mapping in keyword_mappings:
            if mapping.keyword.lower() in text.lower():
                # 检查是否已经有此标签，避免重复
                existing_log = AutoTagLog.query.filter_by(
                    tg_user_id=user_id,
                    tag_id=mapping.tag_id
                ).first()

                if not existing_log:
                    matched_tags.append({
                        'tag_id': mapping.tag_id,
                        'keyword': mapping.keyword,
                        'auto_focus': mapping.auto_focus,
                        'mapping_id': mapping.id
                    })
                    logger.debug(f"Matched keyword '{mapping.keyword}' for user {user_id}")

        return matched_tags

    def apply_auto_tags(self, user_id: str, matched_tags: List[Dict[str, Any]],
                       source_type: str, source_id: str = None) -> int:
        """
        应用自动标签

        Args:
            user_id: 用户ID
            matched_tags: 匹配到的标签信息列表
            source_type: 来源类型
            source_id: 来源记录ID

        Returns:
            成功应用的标签数量
        """
        if not matched_tags:
            return 0

        applied_count = 0

        try:
            for tag_info in matched_tags:
                # 检查用户标签是否已存在
                existing_user_tag = TgGroupUserTag.query.filter_by(
                    tg_user_id=user_id,
                    tag_id=tag_info['tag_id']
                ).first()

                if not existing_user_tag:
                    # 添加用户标签
                    user_tag = TgGroupUserTag(
                        tg_user_id=user_id,
                        tag_id=tag_info['tag_id']
                    )
                    db.session.add(user_tag)

                # 记录自动标签日志
                auto_log = AutoTagLog(
                    tg_user_id=user_id,
                    tag_id=tag_info['tag_id'],
                    keyword=tag_info['keyword'],
                    source_type=source_type,
                    source_id=source_id
                )
                db.session.add(auto_log)

                # 如果需要自动关注
                if tag_info['auto_focus']:
                    user_info = TgGroupUserInfo.query.filter_by(user_id=user_id).first()
                    if user_info:
                        user_info.is_key_focus = True
                        logger.info(f"Auto focus enabled for user {user_id}")

                applied_count += 1
                logger.info(f"Applied tag {tag_info['tag_id']} to user {user_id} "
                           f"via keyword '{tag_info['keyword']}'")

            db.session.commit()
            logger.info(f"Successfully applied {applied_count} auto tags for user {user_id}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to apply auto tags for user {user_id}: {str(e)}")
            raise

        return applied_count

    def process_chat_message(self, message_data: Dict[str, Any]) -> int:
        """
        处理聊天消息进行自动标签

        Args:
            message_data: 消息数据字典

        Returns:
            应用的标签数量
        """
        if not message_data.get('message') or not message_data.get('user_id'):
            return 0

        try:
            matched_tags = self.process_text_for_tags(
                message_data['message'],
                message_data['user_id'],
                'chat',
                message_data.get('message_id')
            )

            if matched_tags:
                return self.apply_auto_tags(
                    message_data['user_id'],
                    matched_tags,
                    'chat',
                    message_data.get('message_id')
                )

        except Exception as e:
            logger.error(f"Failed to process chat message for auto tagging: {str(e)}")

        return 0

    def process_user_info(self, user_data: Dict[str, Any]) -> int:
        """
        处理用户信息进行自动标签

        Args:
            user_data: 用户信息数据字典

        Returns:
            应用的标签数量
        """
        if not user_data.get('user_id'):
            return 0

        total_applied = 0

        # 检测用户名、昵称、描述中的关键词
        text_sources = [
            ('nickname', user_data.get('nickname', '')),
            ('desc', user_data.get('desc', ''))
        ]

        try:
            for source_type, text in text_sources:
                if text and text.strip():
                    matched_tags = self.process_text_for_tags(
                        text,
                        user_data['user_id'],
                        source_type,
                        user_data['user_id']  # 用户信息的source_id使用user_id
                    )

                    if matched_tags:
                        applied = self.apply_auto_tags(
                            user_data['user_id'],
                            matched_tags,
                            source_type,
                            user_data['user_id']
                        )
                        total_applied += applied

        except Exception as e:
            logger.error(f"Failed to process user info for auto tagging: {str(e)}")

        return total_applied

    def process_chat_history_batch(self, chat_records: List[TgGroupChatHistory],
                                  batch_size: int = 100) -> Dict[str, int]:
        """
        批量处理聊天记录进行自动标签

        Args:
            chat_records: 聊天记录列表
            batch_size: 批处理大小

        Returns:
            处理统计信息
        """
        stats = {
            'total_processed': 0,
            'total_tags_applied': 0,
            'failed_count': 0
        }

        for i in range(0, len(chat_records), batch_size):
            batch = chat_records[i:i + batch_size]

            for record in batch:
                try:
                    if record.message:
                        message_data = {
                            'message': record.message,
                            'user_id': record.user_id,
                            'message_id': str(record.id)
                        }

                        applied = self.process_chat_message(message_data)
                        stats['total_tags_applied'] += applied

                    stats['total_processed'] += 1

                except Exception as e:
                    stats['failed_count'] += 1
                    logger.error(f"Failed to process chat record {record.id}: {str(e)}")

            # 每批次后稍作休息，避免数据库压力过大
            if i + batch_size < len(chat_records):
                import time
                time.sleep(0.1)

        logger.info(f"Batch processing completed: {stats}")
        return stats

    def process_user_info_changes_batch(self, user_changes: List[TgUserInfoChange],
                                       batch_size: int = 100) -> Dict[str, int]:
        """
        批量处理用户信息变更进行自动标签

        Args:
            user_changes: 用户信息变更列表
            batch_size: 批处理大小

        Returns:
            处理统计信息
        """
        stats = {
            'total_processed': 0,
            'total_tags_applied': 0,
            'failed_count': 0
        }

        for i in range(0, len(user_changes), batch_size):
            batch = user_changes[i:i + batch_size]

            for change in batch:
                try:
                    user_data = {
                        'user_id': change.user_id,
                        'nickname': change.new_value if change.field_name == 'nickname' else '',
                        'desc': change.new_value if change.field_name == 'desc' else ''
                    }

                    applied = self.process_user_info(user_data)
                    stats['total_tags_applied'] += applied
                    stats['total_processed'] += 1

                except Exception as e:
                    stats['failed_count'] += 1
                    logger.error(f"Failed to process user change {change.id}: {str(e)}")

            # 每批次后稍作休息
            if i + batch_size < len(user_changes):
                import time
                time.sleep(0.1)

        logger.info(f"User info changes batch processing completed: {stats}")
        return stats

    def get_statistics(self) -> Dict[str, Any]:
        """获取自动标签统计信息"""
        try:
            # 总标签映射数
            total_mappings = TagKeywordMapping.query.filter_by(is_active=True).count()

            # 总自动标签记录数
            total_auto_tags = AutoTagLog.query.count()

            # 今日新增自动标签数
            today = datetime.date.today()
            today_auto_tags = AutoTagLog.query.filter(
                AutoTagLog.created_at >= today
            ).count()

            # 按来源类型统计
            source_type_stats = db.session.query(
                AutoTagLog.source_type,
                db.func.count(AutoTagLog.id).label('count')
            ).group_by(AutoTagLog.source_type).all()

            return {
                'total_mappings': total_mappings,
                'total_auto_tags': total_auto_tags,
                'today_auto_tags': today_auto_tags,
                'source_type_stats': [
                    {'source_type': stat.source_type, 'count': stat.count}
                    for stat in source_type_stats
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get auto tagging statistics: {str(e)}")
            return {}


def main():
    """主函数，用于测试自动标签功能"""
    app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)

    with app.app_context():
        service = AutoTaggingService()

        # 获取统计信息
        stats = service.get_statistics()
        print("Auto Tagging Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
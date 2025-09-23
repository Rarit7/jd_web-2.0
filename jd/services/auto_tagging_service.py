from jd import db
from jd.models.tag_keyword_mapping import TagKeywordMapping
from jd.models.auto_tag_log import AutoTagLog
from jd.models.tg_group_user_tag import TgGroupUserTag
from jd.models.tg_group_user_info import TgGroupUserInfo


class AutoTaggingService:
    """自动标签服务"""

    @staticmethod
    def process_text_for_tags(text: str, user_id: str, source_type: str, source_id: str = None):
        """处理文本进行自动标签匹配"""
        # 获取所有激活的关键词映射
        keyword_mappings = TagKeywordMapping.query.filter_by(is_active=True).all()

        matched_tags = []
        for mapping in keyword_mappings:
            if mapping.keyword.lower() in text.lower():
                # 检查是否已经有此标签，避免重复
                existing_tag = AutoTagLog.query.filter_by(
                    tg_user_id=user_id,
                    tag_id=mapping.tag_id
                ).first()

                if not existing_tag:
                    matched_tags.append({
                        'tag_id': mapping.tag_id,
                        'keyword': mapping.keyword,
                        'auto_focus': mapping.auto_focus
                    })

        return matched_tags

    @staticmethod
    def apply_auto_tags(user_id: str, matched_tags: list, source_type: str, source_id: str = None):
        """应用自动标签"""
        for tag_info in matched_tags:
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

        db.session.commit()

    @staticmethod
    def process_chat_message(message_text: str, user_id: str, message_id: str):
        """处理聊天消息的自动标签"""
        if not message_text:
            return

        matched_tags = AutoTaggingService.process_text_for_tags(
            message_text, user_id, 'chat', message_id
        )

        if matched_tags:
            AutoTaggingService.apply_auto_tags(
                user_id, matched_tags, 'chat', message_id
            )

    @staticmethod
    def process_user_info(user_id: str, nickname: str = None, desc: str = None):
        """处理用户信息的自动标签"""
        # 处理昵称
        if nickname:
            matched_tags = AutoTaggingService.process_text_for_tags(
                nickname, user_id, 'nickname', user_id
            )
            if matched_tags:
                AutoTaggingService.apply_auto_tags(
                    user_id, matched_tags, 'nickname', user_id
                )

        # 处理描述
        if desc:
            matched_tags = AutoTaggingService.process_text_for_tags(
                desc, user_id, 'desc', user_id
            )
            if matched_tags:
                AutoTaggingService.apply_auto_tags(
                    user_id, matched_tags, 'desc', user_id
                )
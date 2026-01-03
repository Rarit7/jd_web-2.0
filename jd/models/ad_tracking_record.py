from jd import db
from jd.models.base import BaseModel
from jd.models.tag_keyword_mapping import TagKeywordMapping
import json


class AdTrackingRecord(BaseModel):
    """广告追踪记录模型"""

    __tablename__ = 'ad_tracking_records'

    # 基础字段
    id = db.Column(db.BigInteger, primary_key=True, comment='记录ID')
    channel_id = db.Column(db.BigInteger, nullable=False, comment='频道ID')
    channel_name = db.Column(db.String(255), nullable=False, comment='频道名称')
    message_id = db.Column(db.BigInteger, nullable=False, comment='原始消息ID')
    sender_id = db.Column(db.BigInteger, nullable=False, comment='发送者ID')
    message_text = db.Column(db.Text, comment='消息文本')
    image_url = db.Column(db.String(500), nullable=False, comment='图片URL')
    send_time = db.Column(db.DateTime, nullable=False, comment='发送时间')
    trigger_keyword = db.Column(db.String(100), nullable=False, comment='触发关键词')
    trigger_tag_id = db.Column(db.Integer, comment='触发标签ID（已废弃，使用tag_ids替代）')
    tag_ids = db.Column(db.JSON, comment='匹配的所有标签ID列表')

    # 时间戳和状态字段
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')
    is_processed = db.Column(db.Boolean, default=False, comment='是否已处理')
    process_batch_id = db.Column(db.String(50), comment='处理批次ID')

    # 状态常量
    class Status:
        NOT_PROCESSED = False
        PROCESSED = True

    def _get_channel_title(self):
        """获取频道标题"""
        from jd.models.tg_group import TgGroup
        try:
            channel = TgGroup.query.get(self.channel_id)
            return channel.title if channel else self.channel_name
        except Exception as e:
            import logging
            logging.warning(f"Failed to get channel title: {e}")
            return self.channel_name

    def _get_sender_nickname(self):
        """获取发送者昵称"""
        from jd.models.tg_group_chat_history import TgGroupChatHistory
        try:
            # 尝试从聊天历史中获取用户的昵称或用户名
            # sender_id 可能是字符串格式的用户ID
            chat_record = TgGroupChatHistory.query.filter_by(
                user_id=str(self.sender_id)
            ).first()
            if chat_record:
                return chat_record.nickname or chat_record.username or str(self.sender_id)
            return str(self.sender_id)
        except Exception as e:
            import logging
            logging.warning(f"Failed to get sender nickname: {e}")
            return str(self.sender_id)

    def _convert_image_url(self):
        """将本地文件路径转换为web可访问的URL"""
        if not self.image_url:
            return ''

        url = self.image_url.strip()
        if not url:
            return ''

        # 如果已经是web URL格式，直接返回
        if url.startswith('http://') or url.startswith('https://') or url.startswith('/static/'):
            return url

        # 移除前导斜杠或 static/
        if url.startswith('/'):
            url = url[1:]
        if url.startswith('static/'):
            url = url[7:]

        # 构建完整的static URL路径
        return f'/static/images/{url}' if not url.startswith('images/') else f'/static/{url}'

    def to_dict(self):
        """转换为字典格式，用于API响应"""
        # 获取频道标题
        channel_title = self._get_channel_title()
        # 获取发送者昵称
        sender_nickname = self._get_sender_nickname()

        return {
            'id': self.id,
            'channel_id': self.channel_id,
            'channel_name': self.channel_name,
            'channel_title': channel_title,
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'sender_nickname': sender_nickname,
            'message_text': self.message_text,
            'image_url': self._convert_image_url(),
            'send_time': self.send_time.isoformat() if self.send_time else None,
            'trigger_keyword': self.trigger_keyword,
            'trigger_tag_id': self.trigger_tag_id,  # 保留以支持向后兼容
            'tag_ids': self.tag_ids or [],  # 返回所有匹配的标签ID列表
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_processed': self.is_processed,
            'process_batch_id': self.process_batch_id
        }

    def to_detail_dict(self):
        """转换为详情页面字典格式，包含额外信息"""
        data = self.to_dict()
        data['formatted_send_time'] = self.send_time.strftime('%Y-%m-%d %H:%M:%S') if self.send_time else None

        # 添加标签名称和关键词信息
        tag_info_list = []
        try:
            # 处理 tag_ids：可能是 JSON 字符串或 Python list
            tag_ids_list = None
            if self.tag_ids:
                if isinstance(self.tag_ids, str):
                    # 尝试解析 JSON 字符串
                    if self.tag_ids.startswith('['):
                        tag_ids_list = json.loads(self.tag_ids)
                    else:
                        tag_ids_list = None
                elif isinstance(self.tag_ids, list):
                    tag_ids_list = self.tag_ids

            # 如果成功获取标签ID列表，则获取标签详细信息
            if tag_ids_list:
                from jd.models.result_tag import ResultTag
                for tag_id in tag_ids_list:
                    if isinstance(tag_id, int):
                        try:
                            tag = ResultTag.query.get(tag_id)
                            if tag:
                                # 获取该标签的所有关键词
                                keywords = db.session.query(TagKeywordMapping.keyword).filter(
                                    TagKeywordMapping.tag_id == tag_id,
                                    TagKeywordMapping.is_active == True
                                ).all()
                                keyword_list = [k[0] for k in keywords] if keywords else []
                                tag_info_list.append({
                                    'tag_id': tag_id,
                                    'tag_name': tag.title,
                                    'color': tag.color if hasattr(tag, 'color') else '#409eff',
                                    'keywords': keyword_list
                                })
                        except Exception as tag_error:
                            import logging
                            logging.warning(f"Failed to process tag {tag_id} for record {self.id}: {str(tag_error)}")
                            continue
        except Exception as e:
            # 如果出现任何错误，只返回空的标签信息列表
            import logging
            logging.error(f"Failed to process tag_info for record {self.id}: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            tag_info_list = []

        data['tag_info'] = tag_info_list  # 标签详细信息列表

        return data

    @classmethod
    def get_by_batch_id(cls, batch_id):
        """根据批次ID获取所有记录"""
        return cls.query.filter_by(process_batch_id=batch_id).all()

    @classmethod
    def get_pending_records(cls, limit=100):
        """获取未处理的记录"""
        return cls.query.filter_by(is_processed=False).limit(limit).all()

    @classmethod
    def get_by_channel_and_keyword(cls, channel_id, keyword, limit=None):
        """根据频道ID和关键词查询记录"""
        query = cls.query.filter_by(channel_id=channel_id).filter(
            cls.trigger_keyword.ilike(f'%{keyword}%')
        )
        return query.limit(limit).all() if limit else query.all()

    def mark_as_processed(self):
        """标记为已处理"""
        self.is_processed = self.Status.PROCESSED
        db.session.commit()

    def get_highlight_positions(self, keyword=None):
        """获取关键词在文本中的位置（用于前端高亮）"""
        if not self.message_text:
            return []

        keyword = keyword or self.trigger_keyword
        if not keyword:
            return []

        text = self.message_text.lower()
        keyword_lower = keyword.lower()
        positions = []

        start = 0
        while True:
            pos = text.find(keyword_lower, start)
            if pos == -1:
                break
            positions.append([pos, pos + len(keyword)])
            start = pos + 1

        return positions
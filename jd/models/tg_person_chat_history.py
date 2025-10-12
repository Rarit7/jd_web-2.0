from jd import db
from jd.models.base import BaseModel


class TgPersonChatHistory(BaseModel):
    """Telegram私人聊天记录模型（优化版：使用业务ID，去除冗余字段）"""

    __tablename__ = 'tg_person_chat_history'

    id = db.Column(db.Integer, primary_key=True)

    # 基本标识
    chat_id = db.Column(db.String(128), nullable=False, default='', comment='聊天ID')
    message_id = db.Column(db.String(128), nullable=False, default='', comment='消息ID')

    # 私聊双方标识（使用业务ID）
    owner_user_id = db.Column(db.String(128), nullable=False, default='', comment='己方Telegram用户ID')
    owner_session_name = db.Column(db.String(128), nullable=False, default='', comment='己方Session名称')
    peer_user_id = db.Column(db.String(128), nullable=False, default='', comment='对方用户ID')

    # 消息发送方（使用枚举）
    sender_type = db.Column(db.Enum('owner', 'peer'), nullable=False, comment='发送方类型')

    # 消息内容
    message = db.Column(db.Text, nullable=False, comment='消息内容')
    postal_time = db.Column(db.DateTime, nullable=False, default='1970-10-30 00:00:00', comment='消息时间')
    reply_to_msg_id = db.Column(db.String(128), nullable=False, default='', comment='回复消息ID')

    # 附件
    photo_path = db.Column(db.String(256), nullable=False, default='', comment='图片路径')
    document_path = db.Column(db.String(256), nullable=False, default='', comment='文档路径')
    document_ext = db.Column(db.String(16), nullable=False, default='', comment='文件后缀')

    # 其他
    replies_info = db.Column(db.Text, nullable=True, comment='回复信息')
    status = db.Column(db.Integer, nullable=False, default=0, comment='状态')

    # 时间戳
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def get_sender_user_id(self):
        """动态获取发送方的实际user_id"""
        if self.sender_type == 'owner':
            return self.owner_user_id  # 直接使用业务ID
        else:  # peer
            return self.peer_user_id

    def get_sender_info(self):
        """获取发送方的详细信息（username, nickname等）"""
        from jd.models.tg_account import TgAccount
        from jd.models.tg_group_user_info import TgGroupUserInfo

        if self.sender_type == 'owner':
            # 通过user_id关联tg_account表
            account = TgAccount.query.filter_by(user_id=self.owner_user_id).first()
            if account:
                return {
                    'user_id': account.user_id,
                    'username': account.username,
                    'nickname': account.nickname
                }
        else:  # peer
            # 尝试从tg_group_user_info表获取用户信息
            user = TgGroupUserInfo.query.filter_by(user_id=self.peer_user_id).first()
            if user:
                return {
                    'user_id': user.user_id,
                    'username': user.username,
                    'nickname': user.nickname
                }
        return {'user_id': '', 'username': '', 'nickname': ''}

    def to_dict(self, include_sender_info=True):
        """
        转换为字典

        Args:
            include_sender_info: 是否包含发送方详细信息（默认True）
        """
        result = {
            'id': self.id,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'owner_user_id': self.owner_user_id,
            'owner_session_name': self.owner_session_name,
            'peer_user_id': self.peer_user_id,
            'sender_type': self.sender_type,
            'message': self.message,
            'postal_time': self.postal_time.isoformat() if self.postal_time else None,
            'reply_to_msg_id': self.reply_to_msg_id,
            'photo_path': self.photo_path,
            'document_path': self.document_path,
            'document_ext': self.document_ext,
            'replies_info': self.replies_info,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        # 可选：包含发送方详细信息
        if include_sender_info:
            sender_info = self.get_sender_info()
            result['sender_user_id'] = sender_info['user_id']
            result['sender_username'] = sender_info['username']
            result['sender_nickname'] = sender_info['nickname']

        return result

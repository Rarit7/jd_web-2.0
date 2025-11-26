from jd import db
from jd.models.base import BaseModel
from sqlalchemy.dialects.mysql import JSON


class AdTrackingHighValueMessage(BaseModel):
    """广告追踪高价值信息表 - 存储经大模型判断的高价值聊天信息"""
    __tablename__ = 'ad_tracking_high_value_message'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chat_history_id = db.Column(
        db.Integer,
        db.ForeignKey('tg_group_chat_history.id', ondelete='CASCADE'),
        nullable=False,
        comment='关联的tg_group_chat_history记录ID'
    )
    user_id = db.Column(db.String(128), nullable=True, comment='用户ID')
    username = db.Column(db.String(255), nullable=True, comment='用户名')
    chat_id = db.Column(db.String(128), nullable=True, comment='群组ID')
    group_name = db.Column(db.String(255), nullable=True, comment='群组名称')
    content = db.Column(db.Text, nullable=False, comment='聊天记录内容')
    images = db.Column(JSON, nullable=True, comment='聊天图片列表（JSON数组格式）')
    ai_judgment = db.Column(db.String(500), nullable=True, comment='大模型判断结果')
    publish_time = db.Column(db.DateTime, nullable=True, comment='消息发布时间')
    importance_score = db.Column(
        db.Numeric(5, 2),
        nullable=True,
        comment='重要程度评分（0-100）'
    )
    is_high_priority = db.Column(
        db.Boolean,
        default=False,
        comment='是否为高优先级'
    )
    remark = db.Column(db.Text, nullable=True, comment='备注说明')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now(),
        comment='更新时间'
    )

    # 外键关系 (注：字符串延迟解析以避免导入顺序问题)
    # ad_tracking = db.relationship(
    #     'AdTracking',
    #     backref=db.backref('high_value_messages', cascade='all, delete-orphan')
    # )

    # 索引
    __table_args__ = (
        db.Index('idx_chat_history', 'chat_history_id'),
        db.Index('idx_user', 'user_id'),
        db.Index('idx_chat', 'chat_id'),
        db.Index('idx_publish_time', 'publish_time'),
        db.Index('idx_importance_score', 'importance_score'),
        db.Index('idx_is_high_priority', 'is_high_priority'),
        db.Index('idx_created_at', 'created_at'),
    )

    def to_dict(self):
        """转换为字典格式"""
        data = super().to_dict()
        # 处理numeric类型
        if 'importance_score' in data and data['importance_score'] is not None:
            data['importance_score'] = float(data['importance_score'])
        # images已经是JSON格式，无需额外处理
        return data

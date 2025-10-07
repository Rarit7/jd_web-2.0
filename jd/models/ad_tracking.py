from jd import db
from jd.models.base import BaseModel
from sqlalchemy.dialects.mysql import JSON


class AdTracking(BaseModel):
    """广告追踪表"""
    __tablename__ = 'ad_tracking'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False, comment='原始内容（URL、@账户、Telegraph链接等）')
    content_type = db.Column(
        db.Enum('url', 'telegram_account', 't_me_invite', 't_me_channel_msg', 't_me_private_invite', 'telegraph'),
        nullable=False,
        comment='内容类型'
    )
    normalized_content = db.Column(db.Text, nullable=False, comment='标准化后的内容')
    extra_info = db.Column(JSON, nullable=True, comment='额外信息（JSON格式，如网站类型、钓鱼检测结果、@账户类型等）')
    merchant_name = db.Column(db.String(255), nullable=True, comment='商家名称')
    source_type = db.Column(
        db.Enum('chat', 'user_desc', 'username', 'nickname', 'group_intro'),
        nullable=False,
        comment='来源类型'
    )
    source_id = db.Column(db.String(128), nullable=False, comment='来源记录ID（消息ID、用户ID或群组ID）')
    user_id = db.Column(db.String(128), nullable=True, comment='用户ID（部分来源类型可能无用户ID）')
    chat_id = db.Column(db.String(128), nullable=True, comment='群组ID')
    first_seen = db.Column(db.DateTime, default=db.func.now(), comment='首次发现时间')
    last_seen = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='最后发现时间')
    occurrence_count = db.Column(db.Integer, default=1, comment='出现次数')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 索引已在DDL中定义
    __table_args__ = (
        db.Index('idx_content_type', 'content_type'),
        db.Index('idx_user', 'user_id'),
        db.Index('idx_chat', 'chat_id'),
        db.Index('idx_source', 'source_type', 'source_id'),
        db.Index('idx_normalized', 'normalized_content', mysql_length=255),
        db.Index('idx_merchant_name', 'merchant_name', mysql_length=100),
        db.Index('idx_first_seen', 'first_seen'),
        db.Index('idx_last_seen', 'last_seen'),
    )

    def to_dict(self):
        """转换为字典格式"""
        data = super().to_dict()
        # extra_info 已经是JSON格式，无需额外处理
        return data

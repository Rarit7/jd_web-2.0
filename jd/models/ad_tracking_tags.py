from jd import db
from jd.models.base import BaseModel


class AdTrackingTags(BaseModel):
    """广告追踪-标签关联表"""
    __tablename__ = 'ad_tracking_tags'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ad_tracking_id = db.Column(db.Integer, db.ForeignKey('ad_tracking.id', ondelete='CASCADE'), nullable=False, comment='广告追踪记录ID')
    tag_id = db.Column(db.Integer, nullable=False, comment='标签ID（关联tag_keyword_mapping表）')
    # 注意：tag_id 外键引用需要根据实际标签表名称调整
    # tag_id = db.Column(db.Integer, db.ForeignKey('tag_keyword_mapping.id', ondelete='CASCADE'), nullable=False, comment='标签ID')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')

    # 索引和唯一约束
    __table_args__ = (
        db.UniqueConstraint('ad_tracking_id', 'tag_id', name='uk_ad_tag'),
        db.Index('idx_ad', 'ad_tracking_id'),
        db.Index('idx_tag', 'tag_id'),
    )

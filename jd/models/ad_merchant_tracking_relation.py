from jd import db
from jd.models.base import BaseModel
from decimal import Decimal


class AdMerchantTrackingRelation(BaseModel):
    """商家与广告记录关联表（未来扩展功能）"""
    __tablename__ = 'ad_merchant_tracking_relation'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('ad_merchant.id', ondelete='CASCADE'), nullable=False, comment='商家ID')
    tracking_id = db.Column(db.Integer, db.ForeignKey('ad_tracking.id', ondelete='CASCADE'), nullable=False, comment='广告追踪记录ID')
    confidence_score = db.Column(db.Numeric(3, 2), default=Decimal('1.00'), comment='关联置信度')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 索引
    __table_args__ = (
        db.Index('idx_merchant', 'merchant_id'),
        db.Index('idx_tracking', 'tracking_id'),
    )

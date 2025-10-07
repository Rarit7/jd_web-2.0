from jd import db
from jd.models.base import BaseModel


class AdMerchant(BaseModel):
    """广告商家实体表（未来扩展功能）"""
    __tablename__ = 'ad_merchant'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    merchant_name = db.Column(db.String(255), nullable=False, comment='商家名称')
    merchant_type = db.Column(db.String(100), default='unknown', comment='商家类型')
    risk_level = db.Column(
        db.Enum('low', 'medium', 'high'),
        default='low',
        comment='风险等级'
    )
    identified_at = db.Column(db.DateTime, default=db.func.now(), comment='识别时间')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 索引
    __table_args__ = (
        db.Index('idx_merchant_name', 'merchant_name', mysql_length=100),
        db.Index('idx_risk_level', 'risk_level'),
    )

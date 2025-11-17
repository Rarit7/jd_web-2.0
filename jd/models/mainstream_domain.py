from jd import db
from jd.models.base import BaseModel


class MainstreamDomain(BaseModel):
    """
    主流域名白名单模型

    存储 Tranco Top 10k-20k 的主流域名列表
    用于 URL 过滤，排除主流平台，只处理小众域名
    """
    __tablename__ = 'mainstream_domains'

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False, comment='域名')
    rank = db.Column(db.Integer, comment='Tranco排名')
    source = db.Column(db.String(50), default='tranco', comment='数据来源')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'domain': self.domain,
            'rank': self.rank,
            'source': self.source,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

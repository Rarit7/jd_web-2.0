from jd import db
from jd.models.base import BaseModel


class UrlTagLog(BaseModel):
    """
    广告 URL 标签日志表

    记录广告 URL 的自动标签匹配历史
    维度：URL / 域名，而非 Telegram 用户
    表名统一采用 ad_ 前缀
    """
    __tablename__ = 'ad_url_tag_log'

    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.Integer, nullable=False, comment='广告追踪ID (ad_tracking.id)')
    url = db.Column(db.String(2048), nullable=False, comment='完整URL')
    domain = db.Column(db.String(255), nullable=False, comment='域名')
    tag_id = db.Column(db.Integer, nullable=False, comment='标签ID')
    keyword = db.Column(db.String(255), nullable=False, comment='触发的关键词')
    source_type = db.Column(
        db.Enum('website_title', 'website_content'),
        nullable=False,
        default='website_title',
        comment='标签来源类型'
    )
    detail_info = db.Column(db.JSON, nullable=True, comment='详细信息(JSON格式)')
    created_at = db.Column(db.DateTime, default=db.func.now())

    __table_args__ = (
        db.Index('idx_tracking_id', 'tracking_id'),
        db.Index('idx_domain', 'domain'),
        db.Index('idx_tag_id', 'tag_id'),
        db.Index('idx_source_type', 'source_type'),
        db.Index('idx_created_at', 'created_at'),
        db.UniqueConstraint('tracking_id', 'tag_id', name='uq_tracking_tag'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'tracking_id': self.tracking_id,
            'url': self.url,
            'domain': self.domain,
            'tag_id': self.tag_id,
            'keyword': self.keyword,
            'source_type': self.source_type,
            'detail_info': self.detail_info,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

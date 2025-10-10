from jd import db
from jd.models.base import BaseModel


class AutoTagLog(BaseModel):
    __tablename__ = 'auto_tag_log'

    id = db.Column(db.Integer, primary_key=True)
    tg_user_id = db.Column(db.String(128), nullable=False, comment='TG用户ID')
    tag_id = db.Column(db.Integer, nullable=False, comment='标签ID')
    keyword = db.Column(db.String(255), nullable=False, comment='触发的关键词')
    source_type = db.Column(db.Enum('chat', 'nickname', 'desc'), nullable=False, comment='来源类型')
    source_id = db.Column(db.String(128), nullable=True, comment='来源记录ID')
    detail_info = db.Column(db.JSON, nullable=True, comment='详细信息(JSON格式)')
    created_at = db.Column(db.DateTime, default=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'tg_user_id': self.tg_user_id,
            'tag_id': self.tag_id,
            'keyword': self.keyword,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'detail_info': self.detail_info,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
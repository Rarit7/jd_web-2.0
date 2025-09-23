from jd import db
from jd.models.base import BaseModel


class TagKeywordMapping(BaseModel):
    __tablename__ = 'tag_keyword_mapping'

    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.Integer, nullable=False, comment='标签ID')
    keyword = db.Column(db.String(255), nullable=False, comment='关键词')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    auto_focus = db.Column(db.Boolean, default=False, comment='是否自动加入特别关注')
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'tag_id': self.tag_id,
            'keyword': self.keyword,
            'is_active': self.is_active,
            'auto_focus': self.auto_focus,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
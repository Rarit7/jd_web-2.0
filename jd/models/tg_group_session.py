from jd import db
from jd.models.base import BaseModel


class TgGroupSession(BaseModel):
    __tablename__ = 'tg_group_session'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), nullable=False, default='', comment='telegram账户id')
    chat_id = db.Column(db.String(128), nullable=False, default='', comment='群聊id')
    session_name = db.Column(db.String(128), nullable=False, default='', comment='连接名称')
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
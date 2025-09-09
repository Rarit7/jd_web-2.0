from jd import db
from jd.models.base import BaseModel


class TgGroupStatus(BaseModel):
    __tablename__ = 'tg_group_status'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(128), nullable=False, comment='群聊id')
    members_now = db.Column(db.Integer, nullable=False, default=0, comment='群人数(最新)')
    members_previous = db.Column(db.Integer, nullable=False, default=0, comment='群人数(先前)')
    records_now = db.Column(db.Integer, nullable=False, default=0, comment='数据库中此群消息记录数(最新)')
    records_previous = db.Column(db.Integer, nullable=False, default=0, comment='数据库中此群消息记录数(先前)')
    first_record_date = db.Column(db.DateTime, nullable=True, comment='最早消息日期')
    first_record_id = db.Column(db.String(128), nullable=False, default='', comment='最早消息message_id')
    last_record_date = db.Column(db.DateTime, nullable=True, comment='最新消息日期')
    last_record_id = db.Column(db.String(128), nullable=False, default='', comment='最新消息message_id')
    jdweb_user_id = db.Column(db.Integer, nullable=False, default=0, comment='添加此群的用户id')
    jdweb_tg_id = db.Column(db.String(128), nullable=False, default='', comment='添加此群的用户的telegram_id')
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
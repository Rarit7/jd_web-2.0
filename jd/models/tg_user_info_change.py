from jd import db
from jd.models.base import BaseModel


class TgUserInfoChange(BaseModel):
    __tablename__ = 'tg_user_info_change'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), nullable=False, comment='用户id')
    changed_fields = db.Column(db.Integer, nullable=False, comment='变更字段(1-显示名称 2-用户名 3-头像 4-个人简介)')
    original_value = db.Column(db.Text, nullable=True, comment='原信息')
    new_value = db.Column(db.Text, nullable=True, comment='变更后信息')
    update_time = db.Column(db.DateTime, default=db.func.now(), comment='变更时间')

    class ChangedFieldType:
        DISPLAY_NAME = 1
        USERNAME = 2
        AVATAR = 3
        BIOGRAPHY = 4
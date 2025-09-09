from jd import db
from jd.models.base import BaseModel


class TgGroupInfoChange(BaseModel):
    __tablename__ = 'tg_group_info_change'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(128), nullable=False, comment='群聊id')
    changed_fields = db.Column(db.Integer, nullable=False, comment='变更字段(1-显示名称 2-群组名/邀请链接 3-群头像 4-群组简介)')
    original_value = db.Column(db.Text, nullable=True, comment='原信息')
    new_value = db.Column(db.Text, nullable=True, comment='变更后信息')
    update_time = db.Column(db.DateTime, default=db.func.now(), comment='变更时间')

    class ChangedFieldType:
        DISPLAY_NAME = 1
        GROUP_NAME_INVITE_LINK = 2
        GROUP_AVATAR = 3
        GROUP_DESCRIPTION = 4
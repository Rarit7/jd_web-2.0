from jd import db
from jd.models.base import BaseModel


class TgDocumentInfo(BaseModel):
    __tablename__ = 'tg_document_info'
    
    chat_id = db.Column(db.String(128), nullable=False, primary_key=True, comment='群聊id')
    message_id = db.Column(db.String(128), nullable=False, primary_key=True, comment='消息id')
    peer_id = db.Column(db.String(128), nullable=False, default='', comment='原始来源id')
    filename_origin = db.Column(db.String(256), nullable=False, default='', comment='原本文件名')
    file_ext_name = db.Column(db.String(32), nullable=False, default='', comment='文件扩展名')
    mime_type = db.Column(db.String(128), nullable=False, default='', comment='文件类型')
    filepath = db.Column(db.String(512), nullable=False, default='', comment='存储路径')
    video_thumb_path = db.Column(db.String(512), nullable=False, default='', comment='视频缩略图')
    file_hash = db.Column(db.String(128), nullable=False, default='', comment='文件哈希值')
    file_size = db.Column(db.BigInteger, nullable=False, default=0, comment='文件大小')
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
from jd import db
from jd.models.base import BaseModel


class AdTrackingTransactionMethod(BaseModel):
    """广告追踪-交易方式记录

    用途：存储识别到的交易方式（埋包、面交、邮寄等）
    包含交易方式、关联标签等信息
    """
    __tablename__ = 'ad_tracking_transaction_method'

    # 主键
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')

    # 外键和关联字段
    chat_id = db.Column(db.String(128), nullable=False, comment='群组ID')
    message_id = db.Column(db.String(128), nullable=False, comment='消息ID')

    # 交易方式字段
    method = db.Column(db.String(50), nullable=True, comment='交易方式（如：埋包、面交、邮寄）')
    tag_id = db.Column(db.Integer, nullable=True, comment='标签ID，关联result_tag表')

    # 日期字段
    msg_date = db.Column(db.Date, nullable=True, comment='消息日期')

    # 时间戳
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 索引定义
    __table_args__ = (
        db.Index('idx_method', 'method'),
        db.Index('idx_msg_date', 'msg_date'),
        db.Index('idx_chat_id', 'chat_id'),
        db.Index('idx_tag_id', 'tag_id'),
        db.Index('idx_transaction_method_composite', 'chat_id', 'msg_date', 'method'),
    )

    # 常见交易方式定义
    class TransactionMethodType:
        """交易方式常量"""
        BURIED = '埋包'  # 埋包
        FACE_TO_FACE = '面交'  # 面交
        MAIL = '邮寄'  # 邮寄
        PICK_UP = '自取'  # 自取
        EXPRESS = '快递'  # 快递
        UNKNOWN = '未知'  # 未知

    def to_dict(self):
        """转换为字典格式，用于JSON序列化"""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'method': self.method,
            'tag_id': self.tag_id,
            'msg_date': self.msg_date.isoformat() if self.msg_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_by_chat_and_date(cls, chat_id, msg_date):
        """按群组和日期查询交易方式记录"""
        return cls.query.filter_by(chat_id=chat_id, msg_date=msg_date).all()

    @classmethod
    def get_by_method(cls, method):
        """按交易方式查询记录"""
        return cls.query.filter_by(method=method).all()

    @classmethod
    def get_by_tag(cls, tag_id):
        """按标签ID查询记录"""
        return cls.query.filter_by(tag_id=tag_id).all()

    @classmethod
    def get_method_statistics_by_chat(cls, chat_id):
        """获取指定群组的交易方式统计"""
        from sqlalchemy import func
        results = cls.query.filter_by(chat_id=chat_id).with_entities(
            cls.method,
            func.count(cls.id).label('count')
        ).group_by(cls.method).all()
        return [
            {'method': r[0], 'count': r[1]}
            for r in results
        ]

    @classmethod
    def get_latest_by_chat(cls, chat_id, limit=100):
        """获取指定群组最近的交易方式记录"""
        return cls.query.filter_by(chat_id=chat_id).order_by(cls.msg_date.desc()).limit(limit).all()

    @classmethod
    def get_methods_by_chat_and_date_range(cls, chat_id, start_date, end_date):
        """按群组和日期范围查询交易方式记录"""
        return cls.query.filter(
            cls.chat_id == chat_id,
            cls.msg_date >= start_date,
            cls.msg_date <= end_date
        ).all()

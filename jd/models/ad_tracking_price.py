from jd import db
from jd.models.base import BaseModel


class AdTrackingPrice(BaseModel):
    """广告追踪-价格记录

    用途：存储从聊天记录中通过正则表达式提取的价格信息
    包含价格数值、单位、原始文本等数据
    """
    __tablename__ = 'ad_tracking_price'

    # 主键
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')

    # 外键和关联字段
    chat_id = db.Column(db.String(128), nullable=False, comment='群组ID')
    message_id = db.Column(db.String(128), nullable=False, comment='消息ID')

    # 价格相关字段
    price_value = db.Column(db.Numeric(10, 2), nullable=True, comment='价格数值')
    unit = db.Column(db.String(20), nullable=True, comment='价格单位（如：元/克、元/克克等）')
    extracted_text = db.Column(db.String(200), nullable=True, comment='提取的原始文本')

    # 日期字段
    msg_date = db.Column(db.Date, nullable=True, comment='消息日期')

    # 时间戳
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 索引定义
    __table_args__ = (
        db.Index('idx_chat_id', 'chat_id'),
        db.Index('idx_msg_date', 'msg_date'),
        db.Index('idx_unit', 'unit'),
        db.Index('idx_price_tracking_composite', 'chat_id', 'msg_date', 'unit'),
    )

    def to_dict(self):
        """转换为字典格式，用于JSON序列化"""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'price': float(self.price_value) if self.price_value else None,
            'unit': self.unit,
            'extracted_text': self.extracted_text,
            'msg_date': self.msg_date.isoformat() if self.msg_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_by_chat_and_date(cls, chat_id, msg_date):
        """按群组和日期查询价格记录"""
        return cls.query.filter_by(chat_id=chat_id, msg_date=msg_date).all()

    @classmethod
    def get_by_unit(cls, unit):
        """按单位查询价格记录"""
        return cls.query.filter_by(unit=unit).all()

    @classmethod
    def get_price_range_by_unit(cls, unit):
        """获取指定单位的价格范围（最低价格、最高价格、平均价格）"""
        from sqlalchemy import func
        result = cls.query.filter_by(unit=unit).with_entities(
            func.min(cls.price_value).label('min_price'),
            func.max(cls.price_value).label('max_price'),
            func.avg(cls.price_value).label('avg_price'),
            func.count(cls.id).label('count')
        ).first()
        return {
            'unit': unit,
            'min_price': float(result.min_price) if result.min_price else None,
            'max_price': float(result.max_price) if result.max_price else None,
            'avg_price': float(result.avg_price) if result.avg_price else None,
            'count': result.count or 0,
        }

    @classmethod
    def get_latest_by_chat(cls, chat_id, limit=100):
        """获取指定群组最近的价格记录"""
        return cls.query.filter_by(chat_id=chat_id).order_by(cls.msg_date.desc()).limit(limit).all()

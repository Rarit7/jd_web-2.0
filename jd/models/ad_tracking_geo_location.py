from jd import db
from jd.models.base import BaseModel


class AdTrackingGeoLocation(BaseModel):
    """广告追踪-地理位置记录

    用途：存储从聊天记录中提取的地理位置信息
    包含省份、城市、区县、坐标等地理数据
    """
    __tablename__ = 'ad_tracking_geo_location'

    # 主键
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')

    # 外键和关联字段
    chat_id = db.Column(db.String(128), nullable=False, comment='群组ID')
    message_id = db.Column(db.String(128), nullable=False, comment='消息ID')

    # 地理位置字段
    province = db.Column(db.String(50), nullable=True, comment='省份')
    city = db.Column(db.String(50), nullable=True, comment='城市')
    district = db.Column(db.String(50), nullable=True, comment='区县')
    keyword_matched = db.Column(db.String(100), nullable=True, comment='匹配的关键词')

    # 坐标字段
    latitude = db.Column(db.Numeric(10, 8), nullable=True, comment='纬度')
    longitude = db.Column(db.Numeric(11, 8), nullable=True, comment='经度')

    # 日期字段
    msg_date = db.Column(db.Date, nullable=True, comment='消息日期')

    # 时间戳
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 索引定义
    __table_args__ = (
        db.Index('idx_province', 'province'),
        db.Index('idx_city', 'city'),
        db.Index('idx_msg_date', 'msg_date'),
        db.Index('idx_chat_id', 'chat_id'),
        db.Index('idx_geo_tracking_composite', 'chat_id', 'msg_date', 'province', 'city'),
    )

    def to_dict(self):
        """转换为字典格式，用于JSON序列化"""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'message_id': self.message_id,
            'province': self.province,
            'city': self.city,
            'district': self.district,
            'keyword_matched': self.keyword_matched,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'msg_date': self.msg_date.isoformat() if self.msg_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_by_chat_and_date(cls, chat_id, msg_date):
        """按群组和日期查询地理位置记录"""
        return cls.query.filter_by(chat_id=chat_id, msg_date=msg_date).all()

    @classmethod
    def get_by_location(cls, province, city):
        """按省市查询地理位置记录"""
        query = cls.query
        if province:
            query = query.filter_by(province=province)
        if city:
            query = query.filter_by(city=city)
        return query.all()

    @classmethod
    def get_latest_by_chat(cls, chat_id, limit=100):
        """获取指定群组最近的地理位置记录"""
        return cls.query.filter_by(chat_id=chat_id).order_by(cls.msg_date.desc()).limit(limit).all()

# -*- coding: utf-8 -*-
"""
广告追踪 - 每日统计分析模型
包含 4 个每日统计表的模型定义：黑词、交易方式、价格、地理位置
"""

from datetime import date, datetime
from sqlalchemy import func
from jd import db
from jd.models.base import BaseModel


class AdTrackingDarkKeywordDailyStats(BaseModel):
    """
    黑词每日统计表

    用途：存储每日全局黑词统计数据（聚合所有群组）
    特点：仅保存全局统计，按日期+毒品+分类维度
    """
    __tablename__ = 'ad_tracking_dark_keyword_daily_stats'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    stat_date = db.Column(db.Date, nullable=False, comment='统计日期')
    drug_id = db.Column(db.Integer, nullable=True, comment='毒品ID')
    category_id = db.Column(db.Integer, nullable=True, comment='分类ID')
    keyword_count = db.Column(db.Integer, default=0, comment='关键词出现总次数')
    message_count = db.Column(db.Integer, default=0, comment='包含该关键词的消息数')
    created_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        comment='创建时间'
    )
    updated_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now(),
        comment='更新时间'
    )

    # 表级约束
    __table_args__ = (
        db.UniqueConstraint('stat_date', 'drug_id', 'category_id',
                           name='uk_dark_keyword_daily'),
        db.Index('idx_stat_date', 'stat_date'),
        db.Index('idx_drug_id', 'drug_id'),
        db.Index('idx_category_id', 'category_id'),
        db.Index('idx_daily_stats_composite', 'stat_date', 'drug_id'),
    )

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'stat_date': self.stat_date.isoformat() if self.stat_date else None,
            'drug_id': self.drug_id,
            'category_id': self.category_id,
            'keyword_count': self.keyword_count,
            'message_count': self.message_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_stats_by_date_range(cls, start_date: date, end_date: date):
        """按日期范围查询统计数据"""
        return cls.query.filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date
        ).order_by(cls.stat_date.desc()).all()

    @classmethod
    def aggregate_by_drug(cls, start_date: date, end_date: date):
        """按毒品聚合黑词统计（饼图数据）"""
        results = db.session.query(
            cls.drug_id,
            func.sum(cls.keyword_count).label('total_count')
        ).filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date,
            cls.drug_id.isnot(None)
        ).group_by(cls.drug_id).all()

        return results

    @classmethod
    def aggregate_by_month_and_drug(cls, start_date: date, end_date: date):
        """按月份和毒品聚合黑词统计（趋势折线图数据）"""
        results = db.session.query(
            func.date_format(cls.stat_date, '%Y-%m').label('month'),
            cls.drug_id,
            func.sum(cls.keyword_count).label('total_count')
        ).filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date,
            cls.drug_id.isnot(None)
        ).group_by(
            func.date_format(cls.stat_date, '%Y-%m'),
            cls.drug_id
        ).order_by(
            func.date_format(cls.stat_date, '%Y-%m')
        ).all()

        return results

    def __repr__(self):
        return f'<AdTrackingDarkKeywordDailyStats {self.stat_date} {self.drug_id}>'


class AdTrackingTransactionMethodDailyStats(BaseModel):
    """
    交易方式每日统计表

    用途：存储每日全局交易方式统计数据（聚合所有群组）
    特点：仅保存全局统计，按日期+交易方式+标签维度
    """
    __tablename__ = 'ad_tracking_transaction_method_daily_stats'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    stat_date = db.Column(db.Date, nullable=False, comment='统计日期')
    method = db.Column(db.String(50), nullable=True, comment='交易方式')
    tag_id = db.Column(db.Integer, nullable=True, comment='标签ID')
    record_count = db.Column(db.Integer, default=0, comment='记录数量')
    created_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        comment='创建时间'
    )
    updated_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now(),
        comment='更新时间'
    )

    # 表级约束
    __table_args__ = (
        db.UniqueConstraint('stat_date', 'method', 'tag_id',
                           name='uk_transaction_method_daily'),
        db.Index('idx_stat_date', 'stat_date'),
        db.Index('idx_method', 'method'),
        db.Index('idx_tag_id', 'tag_id'),
        db.Index('idx_transaction_daily_composite', 'stat_date', 'method'),
    )

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'stat_date': self.stat_date.isoformat() if self.stat_date else None,
            'method': self.method,
            'tag_id': self.tag_id,
            'record_count': self.record_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_stats_by_date_range(cls, start_date: date, end_date: date):
        """按日期范围查询统计数据"""
        return cls.query.filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date
        ).order_by(cls.stat_date.desc()).all()

    @classmethod
    def aggregate_by_method(cls, start_date: date, end_date: date):
        """按交易方式聚合统计（柱状图数据）"""
        results = db.session.query(
            cls.method,
            func.sum(cls.record_count).label('total_count')
        ).filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date,
            cls.method.isnot(None)
        ).group_by(cls.method).all()

        return results

    @classmethod
    def aggregate_by_month_and_method(cls, start_date: date, end_date: date):
        """按月份和交易方式聚合统计（趋势折线图数据）"""
        results = db.session.query(
            func.date_format(cls.stat_date, '%Y-%m').label('month'),
            cls.method,
            func.sum(cls.record_count).label('total_count')
        ).filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date,
            cls.method.isnot(None)
        ).group_by(
            func.date_format(cls.stat_date, '%Y-%m'),
            cls.method
        ).order_by(
            func.date_format(cls.stat_date, '%Y-%m')
        ).all()

        return results

    def __repr__(self):
        return f'<AdTrackingTransactionMethodDailyStats {self.stat_date} {self.method}>'


class AdTrackingPriceDailyStats(BaseModel):
    """
    价格每日统计表

    用途：存储每日全局价格统计数据（聚合所有群组）
    特点：仅保存全局统计，按日期+价格单位维度
    """
    __tablename__ = 'ad_tracking_price_daily_stats'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    stat_date = db.Column(db.Date, nullable=False, comment='统计日期')
    unit = db.Column(db.String(20), nullable=True, comment='价格单位')
    avg_price = db.Column(db.Numeric(10, 2), default=0.00, comment='平均价格')
    min_price = db.Column(db.Numeric(10, 2), default=0.00, comment='最低价格')
    max_price = db.Column(db.Numeric(10, 2), default=0.00, comment='最高价格')
    record_count = db.Column(db.Integer, default=0, comment='记录数量')
    created_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        comment='创建时间'
    )
    updated_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now(),
        comment='更新时间'
    )

    # 表级约束
    __table_args__ = (
        db.UniqueConstraint('stat_date', 'unit',
                           name='uk_price_daily'),
        db.Index('idx_stat_date', 'stat_date'),
        db.Index('idx_unit', 'unit'),
        db.Index('idx_price_daily_composite', 'stat_date', 'unit'),
    )

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'stat_date': self.stat_date.isoformat() if self.stat_date else None,
            'unit': self.unit,
            'avg_price': float(self.avg_price) if self.avg_price else 0.0,
            'min_price': float(self.min_price) if self.min_price else 0.0,
            'max_price': float(self.max_price) if self.max_price else 0.0,
            'record_count': self.record_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_stats_by_date_range(cls, start_date: date, end_date: date):
        """按日期范围查询统计数据"""
        return cls.query.filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date
        ).order_by(cls.stat_date.desc()).all()

    @classmethod
    def aggregate_by_unit(cls, start_date: date, end_date: date):
        """按价格单位聚合统计"""
        results = db.session.query(
            cls.unit,
            func.avg(cls.avg_price).label('avg_price'),
            func.min(cls.min_price).label('min_price'),
            func.max(cls.max_price).label('max_price'),
            func.sum(cls.record_count).label('total_count')
        ).filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date,
            cls.unit.isnot(None)
        ).group_by(cls.unit).all()

        return results

    @classmethod
    def aggregate_by_month_and_unit(cls, start_date: date, end_date: date):
        """按月份和价格单位聚合统计（趋势折线图数据）"""
        results = db.session.query(
            func.date_format(cls.stat_date, '%Y-%m').label('month'),
            cls.unit,
            func.avg(cls.avg_price).label('avg_price'),
            func.min(cls.min_price).label('min_price'),
            func.max(cls.max_price).label('max_price'),
            func.sum(cls.record_count).label('total_count')
        ).filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date,
            cls.unit.isnot(None)
        ).group_by(
            func.date_format(cls.stat_date, '%Y-%m'),
            cls.unit
        ).order_by(
            func.date_format(cls.stat_date, '%Y-%m')
        ).all()

        return results

    def __repr__(self):
        return f'<AdTrackingPriceDailyStats {self.stat_date} {self.unit}>'


class AdTrackingGeoLocationDailyStats(BaseModel):
    """
    地理位置每日统计表

    用途：存储每日全局地理位置统计数据（聚合所有群组）
    特点：仅保存全局统计，按日期+省份+城市维度
    """
    __tablename__ = 'ad_tracking_geo_location_daily_stats'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    stat_date = db.Column(db.Date, nullable=False, comment='统计日期')
    province = db.Column(db.String(50), nullable=True, comment='省份')
    city = db.Column(db.String(50), nullable=True, comment='城市')
    record_count = db.Column(db.Integer, default=0, comment='记录数量')
    created_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        comment='创建时间'
    )
    updated_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now(),
        comment='更新时间'
    )

    # 表级约束
    __table_args__ = (
        db.UniqueConstraint('stat_date', 'province', 'city',
                           name='uk_geo_daily'),
        db.Index('idx_stat_date', 'stat_date'),
        db.Index('idx_province', 'province'),
        db.Index('idx_city', 'city'),
        db.Index('idx_geo_daily_composite', 'stat_date', 'province', 'city'),
    )

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'stat_date': self.stat_date.isoformat() if self.stat_date else None,
            'province': self.province,
            'city': self.city,
            'record_count': self.record_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_stats_by_date_range(cls, start_date: date, end_date: date):
        """按日期范围查询统计数据"""
        return cls.query.filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date
        ).order_by(cls.stat_date.desc()).all()

    @classmethod
    def aggregate_by_province(cls, start_date: date, end_date: date):
        """按省份聚合统计（中国地图热力数据）"""
        results = db.session.query(
            cls.province,
            func.sum(cls.record_count).label('total_count')
        ).filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date,
            cls.province.isnot(None)
        ).group_by(cls.province).all()

        return results

    @classmethod
    def aggregate_by_city(cls, start_date: date, end_date: date):
        """按城市聚合统计（城市排名数据）"""
        results = db.session.query(
            cls.city,
            cls.province,
            func.sum(cls.record_count).label('total_count')
        ).filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date,
            cls.city.isnot(None)
        ).group_by(cls.city, cls.province).order_by(
            func.sum(cls.record_count).desc()
        ).all()

        return results

    @classmethod
    def aggregate_by_month_and_province(cls, start_date: date, end_date: date):
        """按月份和省份聚合统计（趋势数据）"""
        results = db.session.query(
            func.date_format(cls.stat_date, '%Y-%m').label('month'),
            cls.province,
            func.sum(cls.record_count).label('total_count')
        ).filter(
            cls.stat_date >= start_date,
            cls.stat_date <= end_date,
            cls.province.isnot(None)
        ).group_by(
            func.date_format(cls.stat_date, '%Y-%m'),
            cls.province
        ).order_by(
            func.date_format(cls.stat_date, '%Y-%m')
        ).all()

        return results

    def __repr__(self):
        return f'<AdTrackingGeoLocationDailyStats {self.stat_date} {self.province} {self.city}>'

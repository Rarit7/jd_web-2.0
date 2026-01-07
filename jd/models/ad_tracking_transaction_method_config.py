# -*- coding: utf-8 -*-
"""
广告追踪 - 交易方式配置模型
支持实时启用/禁用交易方式，配置关键词，无需重启应用
"""

from jd import db
from jd.models.base import BaseModel


class AdTrackingTransactionMethodConfig(BaseModel):
    """
    交易方式配置表

    用途：存储可配置的交易方式，支持实时启用/禁用
    优势：相比硬编码方案，支持热更新，无需修改代码和重启应用
    """
    __tablename__ = 'ad_tracking_transaction_method_config'

    id = db.Column(db.Integer, primary_key=True, comment='主键ID')
    method_name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        comment='交易方式名称（如：埋包、面交）'
    )
    display_name = db.Column(db.String(100), comment='显示名称')
    description = db.Column(db.Text, comment='方式描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    priority = db.Column(db.Integer, default=0, comment='优先级（值越大优先级越高）')
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

    # 关系：与关键词的一对多关系
    keywords = db.relationship(
        'AdTrackingTransactionMethodKeyword',
        backref='method',
        lazy='joined',
        cascade='all, delete-orphan'
    )

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'method_name': self.method_name,
            'display_name': self.display_name,
            'description': self.description,
            'is_active': self.is_active,
            'priority': self.priority,
            'keywords': [kw.to_dict() for kw in self.keywords] if self.keywords else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_all_active(cls):
        """获取所有启用的交易方式"""
        return cls.query.filter_by(is_active=True).order_by(cls.priority.desc()).all()

    @classmethod
    def get_by_name(cls, method_name):
        """按名称获取交易方式"""
        return cls.query.filter_by(method_name=method_name).first()

    def __repr__(self):
        return f'<AdTrackingTransactionMethodConfig {self.method_name}>'


class AdTrackingTransactionMethodKeyword(BaseModel):
    """
    交易方式关键词表

    用途：存储交易方式的关键词，用于AC自动机进行高效匹配
    特点：支持启用/禁用关键词，可设置匹配权重
    """
    __tablename__ = 'ad_tracking_transaction_method_keyword'

    id = db.Column(db.Integer, primary_key=True, comment='主键ID')
    method_id = db.Column(
        db.Integer,
        db.ForeignKey('ad_tracking_transaction_method_config.id', ondelete='CASCADE'),
        nullable=False,
        comment='交易方式ID'
    )
    keyword = db.Column(db.String(100), nullable=False, comment='关键词')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    weight = db.Column(db.Integer, default=1, comment='权重（AC自动机优先级）')
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

    # 表级约束：保证同一交易方式的关键词唯一
    __table_args__ = (
        db.UniqueConstraint('method_id', 'keyword', name='uk_method_keyword'),
    )

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'method_id': self.method_id,
            'keyword': self.keyword,
            'is_active': self.is_active,
            'weight': self.weight,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_by_method_and_keyword(cls, method_id, keyword):
        """按交易方式和关键词获取"""
        return cls.query.filter_by(method_id=method_id, keyword=keyword).first()

    @classmethod
    def get_active_keywords_by_method(cls, method_id):
        """获取指定交易方式的所有启用关键词"""
        return cls.query.filter_by(
            method_id=method_id,
            is_active=True
        ).order_by(cls.weight.desc()).all()

    def __repr__(self):
        return f'<AdTrackingTransactionMethodKeyword {self.keyword}>'

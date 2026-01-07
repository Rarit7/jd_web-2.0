# -*- coding: utf-8 -*-
"""
广告追踪 - 黑词分析模型
包含黑词分类、毒品配置、毒品关键词、黑词记录四个模型
"""

from jd import db
from jd.models.base import BaseModel


class AdTrackingDarkKeywordCategory(BaseModel):
    """
    黑词分类配置表

    用途：存储黑词的分类（如：毒品相关、违法交易、危害品等）
    优势：支持动态配置，可实时启用/禁用分类
    """
    __tablename__ = 'ad_tracking_dark_keyword_category'

    id = db.Column(db.Integer, primary_key=True, comment='主键ID')
    name = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        comment='分类名称（如：毒品相关、违法交易、危害品）'
    )
    display_name = db.Column(db.String(100), comment='显示名称')
    description = db.Column(db.Text, comment='分类描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    priority = db.Column(db.Integer, default=0, comment='优先级（用于排序）')
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

    # 关系：与毒品的一对多关系
    drugs = db.relationship(
        'AdTrackingDarkKeywordDrug',
        backref='category',
        lazy='joined',
        cascade='all, delete-orphan',
        order_by='AdTrackingDarkKeywordDrug.priority.desc()'
    )

    def to_dict(self, include_drugs=False):
        """将模型转换为字典"""
        result = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_active': self.is_active,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_drugs:
            result['drugs'] = [d.to_dict() for d in self.drugs] if self.drugs else []
        return result

    @classmethod
    def get_all_active(cls):
        """获取所有启用的分类（按优先级排序）"""
        return cls.query.filter_by(is_active=True).order_by(cls.priority.desc()).all()

    @classmethod
    def get_by_name(cls, name):
        """按名称获取分类"""
        return cls.query.filter_by(name=name).first()

    def __repr__(self):
        return f'<AdTrackingDarkKeywordCategory {self.name}>'


class AdTrackingDarkKeywordDrug(BaseModel):
    """
    毒品配置表

    用途：存储具体的毒品类型（如：冰毒、海洛因、大麻等）
    关系：属于某个分类，拥有多个关键词
    """
    __tablename__ = 'ad_tracking_dark_keyword_drug'

    id = db.Column(db.Integer, primary_key=True, comment='主键ID')
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('ad_tracking_dark_keyword_category.id', ondelete='CASCADE'),
        nullable=False,
        comment='分类ID'
    )
    name = db.Column(
        db.String(50),
        nullable=False,
        comment='毒品名称（如：冰毒、海洛因、大麻）'
    )
    display_name = db.Column(db.String(100), comment='显示名称')
    description = db.Column(db.Text, comment='毒品描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    priority = db.Column(db.Integer, default=0, comment='优先级（用于排序）')
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

    # 表级约束：保证同一分类下毒品名称唯一
    __table_args__ = (
        db.UniqueConstraint('category_id', 'name', name='uk_category_drug'),
    )

    # 关系：与关键词的一对多关系
    keywords = db.relationship(
        'AdTrackingDarkKeywordKeyword',
        backref='drug',
        lazy='joined',
        cascade='all, delete-orphan',
        order_by='AdTrackingDarkKeywordKeyword.weight.desc()'
    )

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'is_active': self.is_active,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_all_active(cls):
        """获取所有启用的毒品（按优先级排序）"""
        return cls.query.filter_by(is_active=True).order_by(cls.priority.desc()).all()

    @classmethod
    def get_by_category(cls, category_id):
        """按分类获取毒品列表"""
        return cls.query.filter_by(category_id=category_id, is_active=True)\
            .order_by(cls.priority.desc()).all()

    def __repr__(self):
        return f'<AdTrackingDarkKeywordDrug {self.name}>'


class AdTrackingDarkKeywordKeyword(BaseModel):
    """
    毒品关键词表

    用途：存储毒品的关键词，用于AC自动机进行高效匹配
    特点：支持启用/禁用关键词，可设置匹配权重
    """
    __tablename__ = 'ad_tracking_dark_keyword_keyword'

    id = db.Column(db.Integer, primary_key=True, comment='主键ID')
    drug_id = db.Column(
        db.Integer,
        db.ForeignKey('ad_tracking_dark_keyword_drug.id', ondelete='CASCADE'),
        nullable=False,
        comment='毒品ID'
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

    # 表级约束：保证同一毒品的关键词唯一
    __table_args__ = (
        db.UniqueConstraint('drug_id', 'keyword', name='uk_drug_keyword'),
    )

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'drug_id': self.drug_id,
            'keyword': self.keyword,
            'is_active': self.is_active,
            'weight': self.weight,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_all_active_keywords(cls):
        """获取所有启用的关键词（按权重排序，用于构建AC自动机）"""
        return cls.query.filter_by(is_active=True).order_by(cls.weight.desc()).all()

    @classmethod
    def get_active_keywords_by_drug(cls, drug_id):
        """获取指定毒品的所有启用关键词"""
        return cls.query.filter_by(
            drug_id=drug_id,
            is_active=True
        ).order_by(cls.weight.desc()).all()

    def __repr__(self):
        return f'<AdTrackingDarkKeywordKeyword {self.keyword}>'


class AdTrackingDarkKeyword(BaseModel):
    """
    黑词记录表

    用途：存储从聊天记录中提取的黑词匹配记录
    来源：通过AC自动机匹配聊天消息后自动提取
    """
    __tablename__ = 'ad_tracking_dark_keyword'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    chat_id = db.Column(db.String(128), nullable=False, comment='群组ID')
    message_id = db.Column(db.String(128), nullable=False, comment='消息ID')
    keyword = db.Column(db.String(100), nullable=False, comment='匹配到的关键词')
    drug_id = db.Column(
        db.Integer,
        db.ForeignKey('ad_tracking_dark_keyword_drug.id', ondelete='SET NULL'),
        nullable=True,
        comment='毒品ID'
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('ad_tracking_dark_keyword_category.id', ondelete='SET NULL'),
        nullable=True,
        comment='分类ID'
    )
    count = db.Column(db.Integer, default=1, comment='该关键词在消息中出现的次数')
    msg_date = db.Column(db.Date, nullable=True, comment='消息日期')
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

    # 索引已在DDL中定义
    __table_args__ = (
        db.Index('idx_chat_id', 'chat_id'),
        db.Index('idx_msg_date', 'msg_date'),
        db.Index('idx_keyword', 'keyword'),
        db.Index('idx_drug_id', 'drug_id'),
        db.Index('idx_category_id', 'category_id'),
        db.Index('idx_message_id', 'message_id'),
        db.Index('idx_dark_keyword_composite', 'chat_id', 'msg_date', 'drug_id', 'category_id'),
    )

    def to_dict(self):
        """将模型转换为字典"""
        result = {
            'id': self.id,
            'keyword': self.keyword,
            'count': self.count,
            'msg_date': self.msg_date.isoformat() if self.msg_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        # 添加关联的毒品和分类信息
        if self.drug_id:
            drug = AdTrackingDarkKeywordDrug.query.get(self.drug_id)
            if drug:
                result['drug_id'] = self.drug_id
                result['drug_name'] = drug.name
        if self.category_id:
            category = AdTrackingDarkKeywordCategory.query.get(self.category_id)
            if category:
                result['category_id'] = self.category_id
                result['category'] = category.name
        return result

    @classmethod
    def get_by_chat_id(cls, chat_id, start_date=None, end_date=None,
                       keyword=None, category_id=None, drug_id=None,
                       offset=0, limit=20):
        """按条件查询黑词记录"""
        query = cls.query.filter_by(chat_id=str(chat_id))

        if start_date:
            query = query.filter(cls.msg_date >= start_date)
        if end_date:
            query = query.filter(cls.msg_date <= end_date)
        if keyword:
            query = query.filter(cls.keyword.like(f'%{keyword}%'))
        if category_id:
            query = query.filter(cls.category_id == category_id)
        if drug_id:
            query = query.filter(cls.drug_id == drug_id)

        total = query.count()
        records = query.order_by(cls.msg_date.desc(), cls.created_at.desc())\
            .offset(offset).limit(limit).all()

        return total, records

    @classmethod
    def get_stats_by_drug(cls, chat_id, start_date=None, tag_ids=None):
        """按毒品统计黑词出现次数（用于圆环图）"""
        from sqlalchemy import func

        query = db.session.query(
            cls.drug_id,
            func.sum(cls.count).label('total_count')
        ).filter(cls.chat_id == str(chat_id))

        if start_date:
            query = query.filter(cls.msg_date >= start_date)

        results = query.group_by(cls.drug_id).all()

        # 获取毒品名称
        stats = []
        for drug_id, total_count in results:
            if drug_id:
                drug = AdTrackingDarkKeywordDrug.query.get(drug_id)
                if drug:
                    stats.append({
                        'name': drug.display_name or drug.name,
                        'value': int(total_count),
                        'id': drug_id
                    })

        return stats

    @classmethod
    def get_trend_by_month(cls, chat_id, start_date=None):
        """按月统计黑词趋势（用于折线图）"""
        from sqlalchemy import func

        query = db.session.query(
            func.date_format(cls.msg_date, '%Y-%m').label('month'),
            cls.drug_id,
            func.sum(cls.count).label('total_count')
        ).filter(cls.chat_id == str(chat_id))

        if start_date:
            query = query.filter(cls.msg_date >= start_date)

        results = query.group_by('month', cls.drug_id).all()

        # 构建趋势数据
        months = sorted(set(m[0] for m in results if m[0]))
        drug_ids = sorted(set(d[1] for d in results if d[1]))

        trend_data = {}
        for drug_id in drug_ids:
            drug = AdTrackingDarkKeywordDrug.query.get(drug_id)
            if drug:
                drug_name = drug.display_name or drug.name
                trend_data[drug_name] = [
                    next((c[2] for c in results if c[0] == month and c[1] == drug_id), 0)
                    for month in months
                ]

        return {
            'months': [f"{m.split('-')[1]}月" for m in months],
            'data': trend_data
        }

    def __repr__(self):
        return f'<AdTrackingDarkKeyword {self.keyword}>'

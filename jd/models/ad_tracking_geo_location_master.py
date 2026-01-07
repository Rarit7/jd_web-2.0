# -*- coding: utf-8 -*-
"""
广告追踪 - 地理位置主数据模型
存储中国所有地理位置数据（省、市、区县），支持坐标、别名、简称等扩展信息
"""

from jd import db
from jd.models.base import BaseModel


class AdTrackingGeoLocationMaster(BaseModel):
    """
    地理位置主数据表

    用途：存储中国所有地理位置数据（省、市、区县）
    优势：
        - 集中管理地理位置数据（相比CSV文件维护）
        - 支持坐标、别名、简称等扩展信息
        - 支持实时启用/禁用地理位置
        - 通过API管理，无需修改代码
    """
    __tablename__ = 'ad_tracking_geo_location_master'

    # 行政级别常量
    class Level:
        PROVINCE = 1
        CITY = 2
        DISTRICT = 3

    LEVEL_NAMES = {
        1: '省份',
        2: '城市',
        3: '区县'
    }

    id = db.Column(db.Integer, primary_key=True, comment='主键ID')
    level = db.Column(db.Integer, nullable=False, comment='行政级别(1=省份，2=城市，3=区县)')
    name = db.Column(db.String(50), nullable=False, comment='地名')
    parent_id = db.Column(db.Integer, comment='父级ID（上级行政区）')
    code = db.Column(db.String(20), unique=True, comment='行政区划代码（如：110000）')

    # 坐标信息
    latitude = db.Column(db.Numeric(10, 8), comment='纬度')
    longitude = db.Column(db.Numeric(11, 8), comment='经度')

    # 扩展字段
    aliases = db.Column(db.String(500), comment='别名（逗号分隔，如：北京,京,燕京）')
    short_name = db.Column(db.String(50), comment='简称（如：京）')
    description = db.Column(db.Text, comment='描述')

    # 状态字段
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')

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

    # 表级约束：保证同一级别的地名在同一父级下唯一
    __table_args__ = (
        db.UniqueConstraint('level', 'name', 'parent_id', name='uk_level_name_parent'),
    )

    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'level': self.level,
            'level_name': self.LEVEL_NAMES.get(self.level, '未知'),
            'name': self.name,
            'parent_id': self.parent_id,
            'code': self.code,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'aliases': self.aliases.split(',') if self.aliases else [],
            'short_name': self.short_name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    # 查询方法
    @classmethod
    def get_all_provinces(cls):
        """获取所有省份"""
        return cls.query.filter_by(
            level=cls.Level.PROVINCE,
            is_active=True
        ).all()

    @classmethod
    def get_cities_by_province(cls, province_id):
        """获取指定省份的所有城市"""
        return cls.query.filter_by(
            level=cls.Level.CITY,
            parent_id=province_id,
            is_active=True
        ).all()

    @classmethod
    def get_cities_by_province_name(cls, province_name):
        """按省份名称获取所有城市"""
        province = cls.query.filter_by(
            level=cls.Level.PROVINCE,
            name=province_name,
            is_active=True
        ).first()
        if not province:
            return []
        return cls.get_cities_by_province(province.id)

    @classmethod
    def get_districts_by_city(cls, city_id):
        """获取指定城市的所有区县"""
        return cls.query.filter_by(
            level=cls.Level.DISTRICT,
            parent_id=city_id,
            is_active=True
        ).all()

    @classmethod
    def get_districts_by_city_name(cls, city_name):
        """按城市名称获取所有区县"""
        city = cls.query.filter_by(
            level=cls.Level.CITY,
            name=city_name,
            is_active=True
        ).first()
        if not city:
            return []
        return cls.get_districts_by_city(city.id)

    @classmethod
    def get_by_name_and_level(cls, name, level):
        """按名称和级别获取地理位置"""
        return cls.query.filter_by(
            name=name,
            level=level,
            is_active=True
        ).first()

    @classmethod
    def get_by_code(cls, code):
        """按行政区划代码获取地理位置"""
        return cls.query.filter_by(code=code, is_active=True).first()

    @classmethod
    def search_by_name(cls, name_pattern):
        """模糊搜索地理位置"""
        return cls.query.filter(
            cls.name.ilike(f'%{name_pattern}%'),
            cls.is_active == True
        ).all()

    def get_full_name(self):
        """获取完整的地理位置名称（如：山东省济南市槐荫区）"""
        if self.level == self.Level.PROVINCE:
            return self.name

        parent = db.session.query(AdTrackingGeoLocationMaster).filter_by(
            id=self.parent_id
        ).first()

        if self.level == self.Level.CITY:
            return f"{parent.name}{self.name}" if parent else self.name

        if self.level == self.Level.DISTRICT:
            # 获取市级信息
            city = db.session.query(AdTrackingGeoLocationMaster).filter_by(
                id=self.parent_id
            ).first()
            if city and city.parent_id:
                # 获取省级信息
                province = db.session.query(AdTrackingGeoLocationMaster).filter_by(
                    id=city.parent_id
                ).first()
                return f"{province.name}{city.name}{self.name}" if province else f"{city.name}{self.name}"
            return f"{city.name}{self.name}" if city else self.name

        return self.name

    def get_all_keywords(self):
        """获取该地理位置的所有可能的匹配关键词（包括别名和简称）"""
        keywords = [self.name]

        if self.aliases:
            keywords.extend([alias.strip() for alias in self.aliases.split(',') if alias.strip()])

        if self.short_name:
            keywords.append(self.short_name)

        return keywords

    def __repr__(self):
        return f'<AdTrackingGeoLocationMaster {self.name} Level={self.level}>'

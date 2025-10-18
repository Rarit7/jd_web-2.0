from jd import db
from jd.models.base import BaseModel
from sqlalchemy.dialects.mysql import JSON


class AnalyticsUserProfile(BaseModel):
    """用户档案主表"""
    __tablename__ = 'analytics_user_profile'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tg_user_id = db.Column(db.String(128), nullable=False, comment='Telegram用户ID（关联tg_group_user_info.user_id）')
    folder_id = db.Column(db.Integer, db.ForeignKey('analytics_user_profile_folder.id', ondelete='SET NULL'), nullable=True, comment='所属文件夹ID（NULL表示根目录）')
    profile_name = db.Column(db.String(200), nullable=False, comment='档案名称（可自定义，默认使用用户昵称）')
    created_by = db.Column(db.Integer, nullable=False, comment='创建者ID（关联secure_user表）')
    status = db.Column(
        db.Enum('draft', 'generated', 'archived'),
        nullable=False,
        default='draft',
        comment='档案状态: draft-草稿, generated-已生成, archived-已归档'
    )
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序值（同文件夹内排序）')
    config = db.Column(JSON, nullable=True, comment='自定义配置（JSON格式，存储显示面板配置等）')
    last_refreshed_at = db.Column(db.DateTime, nullable=True, comment='最后刷新时间')
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, comment='是否删除: 0-否, 1-是')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 定义与文件夹的关系
    folder = db.relationship('AnalyticsUserProfileFolder', backref='profiles')

    # 定义索引
    __table_args__ = (
        db.Index('idx_tg_user_id', 'tg_user_id'),
        db.Index('idx_folder_id', 'folder_id'),
        db.Index('idx_created_by', 'created_by'),
        db.Index('idx_status', 'status'),
        db.Index('idx_deleted', 'is_deleted'),
        db.Index('idx_sort', 'folder_id', 'sort_order'),
    )

    # 状态常量
    class Status:
        DRAFT = 'draft'
        GENERATED = 'generated'
        ARCHIVED = 'archived'

    def to_dict(self, include_folder=False):
        """
        转换为字典格式

        Args:
            include_folder: 是否包含所属文件夹信息
        """
        data = super().to_dict()

        # 添加额外字段
        if include_folder:
            # 安全地访问folder关系，可能为None
            if hasattr(self, 'folder') and self.folder:
                data['folder'] = {
                    'id': self.folder.id,
                    'name': self.folder.name,
                    'parent_id': self.folder.parent_id
                }
            else:
                data['folder'] = None

        return data

    @classmethod
    def get_by_tg_user_id(cls, tg_user_id):
        """
        根据 Telegram 用户ID 获取档案

        Args:
            tg_user_id: Telegram用户ID

        Returns:
            AnalyticsUserProfile or None
        """
        return cls.query.filter_by(tg_user_id=tg_user_id, is_deleted=False).first()

    @classmethod
    def get_profiles_by_folder(cls, folder_id=None, include_deleted=False):
        """
        获取指定文件夹下的所有档案

        Args:
            folder_id: 文件夹ID（None表示根目录）
            include_deleted: 是否包含已删除档案

        Returns:
            List[AnalyticsUserProfile]
        """
        query = cls.query.filter_by(folder_id=folder_id)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.order_by(cls.sort_order).all()

    @classmethod
    def create_from_tg_user(cls, tg_user_id, profile_name, created_by, folder_id=None, **kwargs):
        """
        从 Telegram 用户创建档案

        Args:
            tg_user_id: Telegram用户ID
            profile_name: 档案名称
            created_by: 创建者ID
            folder_id: 所属文件夹ID（可选）
            **kwargs: 其他可选参数（status, config等）

        Returns:
            AnalyticsUserProfile
        """
        profile = cls(
            tg_user_id=tg_user_id,
            profile_name=profile_name,
            created_by=created_by,
            folder_id=folder_id,
            **kwargs
        )
        return profile

    def mark_as_generated(self):
        """标记档案为已生成状态"""
        self.status = self.Status.GENERATED
        self.last_refreshed_at = db.func.now()

    def mark_as_archived(self):
        """标记档案为已归档状态"""
        self.status = self.Status.ARCHIVED

    def refresh_data(self):
        """刷新档案数据（更新最后刷新时间）"""
        self.last_refreshed_at = db.func.now()

    def soft_delete(self):
        """软删除档案"""
        self.is_deleted = True

    def restore(self):
        """恢复已删除的档案"""
        self.is_deleted = False

    def move_to_folder(self, new_folder_id):
        """
        移动档案到新文件夹

        Args:
            new_folder_id: 新文件夹ID（None表示移动到根目录）
        """
        self.folder_id = new_folder_id

    def update_config(self, config_dict):
        """
        更新档案配置

        Args:
            config_dict: 配置字典
        """
        if self.config is None:
            self.config = {}
        self.config.update(config_dict)
        # 标记字段为已修改（针对JSON字段）
        db.session.merge(self)

    def get_tg_user_info(self):
        """
        获取关联的 Telegram 用户信息

        Returns:
            TgGroupUserInfo or None
        """
        from jd.models.tg_group_user_info import TgGroupUserInfo
        return TgGroupUserInfo.query.filter_by(user_id=self.tg_user_id).first()

    def __repr__(self):
        return f'<AnalyticsUserProfile {self.id}: {self.profile_name} ({self.tg_user_id})>'

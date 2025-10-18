from jd import db
from jd.models.base import BaseModel


class AnalyticsUserProfileFolder(BaseModel):
    """用户档案文件夹表 - 用于左侧导航树结构"""
    __tablename__ = 'analytics_user_profile_folder'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='文件夹名称')
    parent_id = db.Column(db.Integer, db.ForeignKey('analytics_user_profile_folder.id', ondelete='CASCADE'), nullable=True, comment='父文件夹ID（NULL表示根目录）')
    user_id = db.Column(db.Integer, nullable=False, comment='创建者ID（关联secure_user表）')
    sort_order = db.Column(db.Integer, nullable=False, default=0, comment='排序值（同级文件夹排序）')
    icon = db.Column(db.String(50), nullable=True, default='Folder', comment='文件夹图标名称')
    description = db.Column(db.String(500), nullable=True, comment='文件夹描述')
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, comment='是否删除: 0-否, 1-是')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 定义索引
    __table_args__ = (
        db.Index('idx_parent_id', 'parent_id'),
        db.Index('idx_user_id', 'user_id'),
        db.Index('idx_sort', 'parent_id', 'sort_order'),
        db.Index('idx_deleted', 'is_deleted'),
    )

    # 定义关系
    # 子文件夹关系（自引用）
    children = db.relationship(
        'AnalyticsUserProfileFolder',
        backref=db.backref('parent', remote_side=[id]),
        foreign_keys=[parent_id],
        lazy='dynamic'
    )

    # 文件夹内的档案 (关系由 AnalyticsUserProfile 的外键自动推断)
    # profiles = db.relationship(
    #     'AnalyticsUserProfile',
    #     backref='folder',
    #     lazy='dynamic'
    # )

    def to_dict(self, include_children=False, include_profiles=False):
        """
        转换为字典格式

        Args:
            include_children: 是否包含子文件夹
            include_profiles: 是否包含档案列表
        """
        data = super().to_dict()

        # 添加额外字段
        if include_children:
            data['children'] = [
                child.to_dict(include_children=True, include_profiles=include_profiles)
                for child in self.children.filter_by(is_deleted=False).order_by(
                    AnalyticsUserProfileFolder.sort_order
                )
            ]

        if include_profiles:
            from jd.models.analytics_user_profile import AnalyticsUserProfile
            data['profiles'] = [
                profile.to_dict()
                for profile in AnalyticsUserProfile.query.filter_by(
                    folder_id=self.id, is_deleted=False
                ).order_by(AnalyticsUserProfile.sort_order).all()
            ]

        return data

    def to_tree_node(self):
        """
        转换为前端树节点格式（适配 Element Plus Tree）

        Returns:
            {
                id: 'folder_1',
                label: '商家',
                type: 'folder',
                icon: 'Folder',
                children: [...]
            }
        """
        from jd.models.analytics_user_profile import AnalyticsUserProfile

        # 获取子文件夹
        children_folders = [
            child.to_tree_node()
            for child in self.children.filter_by(is_deleted=False).order_by(
                AnalyticsUserProfileFolder.sort_order
            )
        ]

        # 获取档案节点
        children_profiles = [
            {
                'id': f'profile_{profile.id}',
                'label': profile.profile_name,
                'type': 'resource',
                'tg_user_id': profile.tg_user_id,
                'status': profile.status,
                'folder_id': profile.folder_id  # 添加folder_id用于编辑时默认选中
            }
            for profile in AnalyticsUserProfile.query.filter_by(
                folder_id=self.id, is_deleted=False
            ).order_by(AnalyticsUserProfile.sort_order).all()
        ]

        return {
            'id': f'folder_{self.id}',
            'label': self.name,
            'type': 'folder',
            'icon': self.icon or 'Folder',
            'description': self.description,
            'children': children_folders + children_profiles
        }

    @classmethod
    def get_root_folders(cls, user_id=None):
        """
        获取根文件夹列表

        Args:
            user_id: 可选，筛选特定用户创建的文件夹
        """
        query = cls.query.filter_by(parent_id=None, is_deleted=False)
        if user_id:
            query = query.filter_by(user_id=user_id)
        return query.order_by(cls.sort_order).all()

    @classmethod
    def get_tree_data(cls, user_id=None):
        """
        获取完整的树形结构数据

        Args:
            user_id: 可选，筛选特定用户创建的文件夹

        Returns:
            List[Dict]: 树形结构数据数组，包括根文件夹和根目录档案
        """
        from jd.models.analytics_user_profile import AnalyticsUserProfile

        tree_data = []

        # 1. 获取根文件夹
        root_folders = cls.get_root_folders(user_id)
        tree_data.extend([folder.to_tree_node() for folder in root_folders])

        # 2. 获取根目录档案（folder_id = NULL）
        root_profiles_query = AnalyticsUserProfile.query.filter_by(
            folder_id=None, is_deleted=False
        )
        if user_id:
            root_profiles_query = root_profiles_query.filter_by(created_by=user_id)

        root_profiles = root_profiles_query.order_by(
            AnalyticsUserProfile.sort_order
        ).all()

        if root_profiles:
            # 如果有根目录档案，添加到结果列表
            root_profiles_nodes = [
                {
                    'id': f'profile_{profile.id}',
                    'label': profile.profile_name,
                    'type': 'resource',
                    'tg_user_id': profile.tg_user_id,
                    'status': profile.status,
                    'folder_id': profile.folder_id  # 添加folder_id用于编辑时默认选中
                }
                for profile in root_profiles
            ]
            tree_data.extend(root_profiles_nodes)

        return tree_data

    def __repr__(self):
        return f'<AnalyticsUserProfileFolder {self.id}: {self.name}>'

"""
部门模型 - 用于组织用户和TG账户的部门管理
"""
from jd import db


class Department(db.Model):
    __tablename__ = 'department'

    id = db.Column(db.Integer, primary_key=True, comment='部门ID')
    name = db.Column(db.String(100), unique=True, nullable=False, comment='部门名称')
    description = db.Column(db.String(500), nullable=True, comment='部门描述')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')
    is_active = db.Column(db.Integer, nullable=False, default=1, comment='是否启用: 1=启用, 0=禁用')

    # 关系定义
    users = db.relationship('SecureUser', backref='department', lazy='dynamic')
    tg_account_relations = db.relationship('DepartmentTgAccount', backref='department',
                                          lazy='dynamic', cascade='all, delete-orphan')

    class StatusType:
        DISABLED = 0  # 禁用
        ENABLED = 1   # 启用

    @staticmethod
    def is_global_department(dept_id):
        """检查是否为全局部门（ID=0）"""
        return dept_id == 0

    def is_active_department(self) -> bool:
        """检查部门是否启用"""
        return self.is_active == self.StatusType.ENABLED

    def get_user_count(self):
        """获取部门下的用户数量"""
        return self.users.count()

    def get_tg_account_count(self):
        """获取部门关联的TG账户数量"""
        return self.tg_account_relations.count()

    def get_tg_user_ids(self):
        """获取部门关联的所有TG账户user_id列表"""
        return [rel.tg_user_id for rel in self.tg_account_relations.all()]

    def to_dict(self, include_counts=True):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }

        if include_counts:
            data.update({
                'user_count': self.get_user_count(),
                'tg_account_count': self.get_tg_account_count(),
            })

        return data

    def __repr__(self):
        return f'<Department {self.name}>'

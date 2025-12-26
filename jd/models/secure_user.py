"""
安全用户模型 - 使用哈希密码存储和直接权限等级
"""
import hashlib
import secrets
from datetime import datetime
from jd import db


class SecureUser(db.Model):
    __tablename__ = 'secure_user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column(db.String(128), nullable=False, comment='密码哈希值')
    salt = db.Column(db.String(32), nullable=False, comment='密码盐值')
    permission_level = db.Column(db.Integer, nullable=False, default=2, comment='权限等级: 0=超级管理员, 1=部门管理员, 2=普通用户')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id', ondelete='RESTRICT'),
                             nullable=False, default=0, comment='所属部门ID，0为全局部门')
    status = db.Column(db.Integer, nullable=False, default=1, comment='状态: 0=禁用, 1=启用')
    last_login = db.Column(db.DateTime, nullable=True, comment='最后登录时间')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')
    created_by = db.Column(db.Integer, nullable=True, comment='创建者用户ID')
    
    class StatusType:
        DISABLED = 0  # 禁用
        ENABLED = 1   # 启用
    
    class PermissionLevel:
        SUPER_ADMIN = 0        # 超级管理员
        DEPT_MANAGER = 1       # 部门管理员
        REGULAR_USER = 2       # 普通用户
    
    @staticmethod
    def generate_salt():
        """生成随机盐值"""
        return secrets.token_hex(16)
    
    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """使用SHA-256和盐值哈希密码"""
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    
    def set_password(self, password: str):
        """设置密码（自动生成盐值和哈希）"""
        self.salt = self.generate_salt()
        self.password_hash = self.hash_password(password, self.salt)
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        if not self.salt or not self.password_hash:
            return False
        return self.password_hash == self.hash_password(password, self.salt)
    
    def is_super_admin(self) -> bool:
        """检查是否为超级管理员"""
        return self.permission_level == self.PermissionLevel.SUPER_ADMIN

    def is_dept_manager(self) -> bool:
        """检查是否为部门管理员"""
        return self.permission_level == self.PermissionLevel.DEPT_MANAGER

    def is_regular_user(self) -> bool:
        """检查是否为普通用户"""
        return self.permission_level == self.PermissionLevel.REGULAR_USER

    def is_in_global_department(self) -> bool:
        """检查是否属于全局部门（ID=0）"""
        return self.department_id == 0

    def can_manage_department(self, dept_id) -> bool:
        """检查是否可以管理指定部门

        Args:
            dept_id: 部门ID

        Returns:
            bool: True表示可以管理
        """
        # 超级管理员可以管理所有部门
        if self.is_super_admin():
            return True

        # 部门管理员只能管理自己的部门
        if self.is_dept_manager() and self.department_id == dept_id:
            return True

        return False

    def can_manage_user(self, target_user) -> bool:
        """检查是否可以管理目标用户

        Args:
            target_user: 目标用户对象

        Returns:
            bool: True表示可以管理
        """
        # 超级管理员可以管理所有用户
        if self.is_super_admin():
            return True

        # 部门管理员只能管理本部门的普通用户
        if self.is_dept_manager():
            return (self.department_id == target_user.department_id and
                   target_user.is_regular_user())

        return False
    
    def is_enabled(self) -> bool:
        """检查账户是否启用"""
        return self.status == self.StatusType.ENABLED
    
    def can_login(self) -> bool:
        """检查是否可以登录"""
        return self.is_enabled()
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.now()
    
    def get_permission_name(self) -> str:
        """获取权限等级名称"""
        permission_names = {
            self.PermissionLevel.SUPER_ADMIN: '超级管理员',
            self.PermissionLevel.DEPT_MANAGER: '部门管理员',
            self.PermissionLevel.REGULAR_USER: '普通用户'
        }
        return permission_names.get(self.permission_level, '未知权限')
    
    def to_dict(self, include_sensitive=False, include_department=True):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'username': self.username,
            'permission_level': self.permission_level,
            'permission_name': self.get_permission_name(),
            'department_id': self.department_id,
            'status': self.status,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': self.created_by
        }

        # 包含部门信息
        if include_department and hasattr(self, 'department') and self.department:
            data['department_name'] = self.department.name
        elif include_department:
            data['department_name'] = None

        if include_sensitive:
            data.update({
                'password_hash': self.password_hash,
                'salt': self.salt
            })

        return data
    
    def __repr__(self):
        return f'<SecureUser {self.username}>'
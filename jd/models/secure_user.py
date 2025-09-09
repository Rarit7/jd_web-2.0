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
    permission_level = db.Column(db.Integer, nullable=False, default=2, comment='权限等级: 1=超级管理员, 2=普通用户')
    status = db.Column(db.Integer, nullable=False, default=1, comment='状态: 0=禁用, 1=启用')
    last_login = db.Column(db.DateTime, nullable=True, comment='最后登录时间')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')
    created_by = db.Column(db.Integer, nullable=True, comment='创建者用户ID')
    
    class StatusType:
        DISABLED = 0  # 禁用
        ENABLED = 1   # 启用
    
    class PermissionLevel:
        SUPER_ADMIN = 1    # 超级管理员
        REGULAR_USER = 2   # 普通用户
    
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
            self.PermissionLevel.REGULAR_USER: '普通用户'
        }
        return permission_names.get(self.permission_level, '未知权限')
    
    def to_dict(self, include_sensitive=False):
        """转换为字典格式"""
        data = {
            'id': self.id,
            'username': self.username,
            'permission_level': self.permission_level,
            'permission_name': self.get_permission_name(),
            'status': self.status,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'created_by': self.created_by
        }
        
        if include_sensitive:
            data.update({
                'password_hash': self.password_hash,
                'salt': self.salt
            })
        
        return data
    
    def __repr__(self):
        return f'<SecureUser {self.username}>'
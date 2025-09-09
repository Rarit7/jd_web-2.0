#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
初始化角色和用户数据的脚本
"""

from jd import app, db
from jd.models.role import Role
from jd.models.secure_user import SecureUser
from jd.models.user_role import UserRole

# Initialize the Flask app with database
app.ready()


def run():
    """初始化角色和用户数据"""
    
    print("正在初始化角色数据...")
    
    # 创建默认角色
    roles_data = [
        {
            'id': 1,
            'name': '超级管理员',
            'detail': '拥有所有权限的管理员，可以管理用户、角色和系统设置',
            'status': Role.StatusType.VALID
        },
        {
            'id': 2, 
            'name': '普通用户',
            'detail': '具有基础查看和操作权限的用户，可以查看数据和执行基本操作',
            'status': Role.StatusType.VALID
        }
    ]
    
    for role_data in roles_data:
        existing_role = db.session.query(Role).filter(Role.id == role_data['id']).first()
        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)
            print(f"创建角色: {role_data['name']}")
        else:
            print(f"角色已存在: {role_data['name']}")
    
    print("\n正在创建示例用户...")
    
    # 创建示例用户 (使用SecureUser)
    users_data = [
        {
            'username': 'admin',
            'password': 'admin123',
            'permission_level': 1  # 超级管理员
        },
        {
            'username': 'user1',
            'password': '111111',
            'permission_level': 2  # 普通用户
        },
        {
            'username': 'user2', 
            'password': '111111',
            'permission_level': 2  # 普通用户
        }
    ]
    
    for user_data in users_data:
        existing_user = db.session.query(SecureUser).filter(SecureUser.username == user_data['username']).first()
        if not existing_user:
            # 创建安全用户
            user = SecureUser(
                username=user_data['username'],
                permission_level=user_data['permission_level'],
                status=SecureUser.StatusType.ENABLED
            )
            user.set_password(user_data['password'])  # 使用安全的密码哈希
            db.session.add(user)
            print(f"创建用户: {user_data['username']} (权限等级: {user_data['permission_level']})")
        else:
            print(f"用户已存在: {user_data['username']}")
    
    print("\n正在分配用户角色...")
    
    # 为用户分配角色（基于 permission_level）
    users = db.session.query(SecureUser).all()
    for user in users:
        # 根据用户的权限等级分配对应角色
        target_role_id = user.permission_level  # 1=超级管理员, 2=普通用户
        
        # 检查用户角色关联是否已存在
        existing_user_role = db.session.query(UserRole).filter(
            UserRole.user_id == user.id,
            UserRole.role_id == target_role_id,
            UserRole.status == UserRole.StatusType.VALID
        ).first()
        
        if not existing_user_role:
            user_role = UserRole(
                user_id=user.id,
                role_id=target_role_id,
                status=UserRole.StatusType.VALID
            )
            db.session.add(user_role)
            
            role_name = "超级管理员" if target_role_id == 1 else "普通用户"
            print(f"为用户 {user.username} 分配角色: {role_name}")
        else:
            role_name = "超级管理员" if target_role_id == 1 else "普通用户"
            print(f"用户 {user.username} 已具有角色: {role_name}")
    
    # 提交所有更改
    db.session.commit()
    
    print("\n初始化完成！")
    print("\n用户账户信息:")
    print("超级管理员: admin / admin123") 
    print("普通用户: user1 / 111111")
    print("普通用户: user2 / 111111")
    
    # 显示当前数据统计
    print("\n数据统计:")
    role_count = db.session.query(Role).filter(Role.status == Role.StatusType.VALID).count()
    user_count = db.session.query(SecureUser).filter(SecureUser.status == SecureUser.StatusType.ENABLED).count()
    user_role_count = db.session.query(UserRole).filter(UserRole.status == UserRole.StatusType.VALID).count()
    print(f"角色数量: {role_count}")
    print(f"用户数量: {user_count}")
    print(f"用户角色关联数量: {user_role_count}")


if __name__ == '__main__':
    with app.app_context():
        run()
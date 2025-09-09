"""
安全用户管理API - 使用新的哈希密码用户表
"""
from flask import request
from datetime import datetime

from jd import db
from jd.models.secure_user import SecureUser
from jd.services.role_service.role import ROLE_SUPER_ADMIN
from jd.views import get_or_exception, APIException, success
from jd.views.api import api
from jd.helpers.user import current_user_id


@api.route('/user/secure/list', roles=[ROLE_SUPER_ADMIN])
def secure_user_list():
    """获取安全用户列表，返回JSON格式"""
    users = db.session.query(SecureUser).order_by(SecureUser.id.desc()).all()
    
    users_data = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'role_name': user.get_permission_name(),
            'role_id': user.permission_level,  # 兼容前端
            'permission_level': user.permission_level,
            'permission_name': user.get_permission_name(),
            'status': user.status,
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '从未登录',
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        users_data.append(user_data)
    
    # 可用的权限等级
    roles_data = [
        {
            'id': SecureUser.PermissionLevel.SUPER_ADMIN,
            'name': '超级管理员'
        },
        {
            'id': SecureUser.PermissionLevel.REGULAR_USER,
            'name': '普通用户'
        }
    ]
    
    return success({
        'users': users_data,
        'roles': roles_data
    })


@api.route('/user/secure/create', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def create_secure_user():
    """创建安全用户"""
    args = request.get_json() or request.form
    username = get_or_exception('username', args, 'str')
    password = args.get('password', '123456')  # 默认密码
    permission_level = get_or_exception('permission_level', args, 'int', SecureUser.PermissionLevel.REGULAR_USER)
    
    # 验证输入
    if len(username.strip()) < 3:
        raise APIException('用户名长度不能少于3位')
    
    if permission_level not in [SecureUser.PermissionLevel.SUPER_ADMIN, SecureUser.PermissionLevel.REGULAR_USER]:
        raise APIException('无效的权限等级')
    
    # 检查用户名是否已存在
    existing_user = db.session.query(SecureUser).filter(SecureUser.username == username).first()
    if existing_user:
        raise APIException('用户名已存在')
    
    # 创建新用户
    new_user = SecureUser(
        username=username.strip(),
        permission_level=permission_level,
        status=SecureUser.StatusType.ENABLED,
        created_by=current_user_id
    )
    
    # 设置密码
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return success({
        'message': f'用户 {username} 创建成功',
        'default_password': password,
        'user_id': new_user.id
    })


@api.route('/user/secure/update', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def update_secure_user():
    """更新安全用户信息"""
    args = request.get_json() or request.form
    user_id = get_or_exception('user_id', args, 'int')
    permission_level = get_or_exception('permission_level', args, 'int')
    status = args.get('status', SecureUser.StatusType.ENABLED)
    
    # 验证权限等级
    if permission_level not in [SecureUser.PermissionLevel.SUPER_ADMIN, SecureUser.PermissionLevel.REGULAR_USER]:
        raise APIException('无效的权限等级')
    
    # 获取用户
    user = db.session.query(SecureUser).filter_by(id=user_id).first()
    if not user:
        raise APIException('用户不存在')
    
    # 不能修改自己的权限等级
    if user_id == current_user_id:
        raise APIException('不能修改自己的权限等级')
    
    # 更新用户信息
    user.permission_level = permission_level
    user.status = status
    user.updated_at = datetime.now()
    
    db.session.commit()
    
    return success({
        'message': f'用户 {user.username} 信息更新成功'
    })


@api.route('/user/secure/delete', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def delete_secure_user():
    """删除（禁用）安全用户"""
    args = request.get_json() or request.args
    user_id = get_or_exception('user_id', args, 'int')
    
    # 获取用户
    user = db.session.query(SecureUser).filter_by(id=user_id).first()
    if not user:
        raise APIException('用户不存在')
    
    # 不能删除自己
    if user_id == current_user_id:
        raise APIException('不能删除自己的账户')
    
    # 软删除（禁用账户）
    user.status = SecureUser.StatusType.DISABLED
    user.updated_at = datetime.now()
    db.session.commit()
    
    return success({
        'message': f'用户 {user.username} 已被禁用'
    })




@api.route('/user/secure/reset_password', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def reset_user_password():
    """重置用户密码"""
    args = request.get_json() or request.form
    user_id = get_or_exception('user_id', args, 'int')
    new_password = args.get('new_password', '123456')
    
    user = db.session.query(SecureUser).filter_by(id=user_id).first()
    if not user:
        raise APIException('用户不存在')
    
    # 重置密码
    user.set_password(new_password)
    user.updated_at = datetime.now()
    db.session.commit()
    
    return success({
        'message': f'用户 {user.username} 密码重置成功',
        'new_password': new_password
    })


@api.route('/user/secure/info', methods=['GET'])
def get_secure_user_detail():
    """获取指定用户详细信息"""
    args = request.args
    user_id = get_or_exception('user_id', args, 'int')
    
    user = db.session.query(SecureUser).filter_by(id=user_id).first()
    if not user:
        raise APIException('用户不存在')
    
    return success({
        'user': user.to_dict()
    })
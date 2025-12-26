"""
安全用户管理API - 使用新的哈希密码用户表
"""
from flask import request, g
from datetime import datetime

from jd import db
from jd.models.secure_user import SecureUser
from jd.models.department import Department
from jd.services.role_service.role import ROLE_SUPER_ADMIN
from jd.views import get_or_exception, APIException, success
from jd.views.api import api
from jd.helpers.user import current_user_id
from jd.helpers.permission_helper import check_can_manage_user


@api.route('/user/secure/list')
def secure_user_list():
    """获取安全用户列表，返回JSON格式

    权限：超级管理员可查看所有用户，部门管理员只能查看本部门用户
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        raise APIException('未登录', 40101, 401)

    current = g.current_user

    # 构建查询
    query = db.session.query(SecureUser)

    # 非超级管理员只能查看本部门用户
    if not current.is_super_admin():
        if not current.is_dept_manager():
            raise APIException('权限不足', 40301, 403)
        query = query.filter_by(department_id=current.department_id)

    users = query.order_by(SecureUser.id.desc()).all()

    users_data = []
    for user in users:
        user_data = user.to_dict(include_department=True)
        # 兼容前端旧字段
        user_data['role_name'] = user.get_permission_name()
        user_data['role_id'] = user.permission_level
        user_data['last_login'] = user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '从未登录'
        users_data.append(user_data)

    # 可用的权限等级（根据当前用户权限返回）
    if current.is_super_admin():
        roles_data = [
            {'id': SecureUser.PermissionLevel.SUPER_ADMIN, 'name': '超级管理员'},
            {'id': SecureUser.PermissionLevel.DEPT_MANAGER, 'name': '部门管理员'},
            {'id': SecureUser.PermissionLevel.REGULAR_USER, 'name': '普通用户'}
        ]
    else:
        # 部门管理员只能创建普通用户
        roles_data = [
            {'id': SecureUser.PermissionLevel.REGULAR_USER, 'name': '普通用户'}
        ]

    # 获取部门列表（用于筛选）
    if current.is_super_admin():
        departments = Department.query.filter_by(is_active=1).all()
    else:
        departments = [current.department]

    departments_data = [{'id': dept.id, 'name': dept.name} for dept in departments]

    return success({
        'users': users_data,
        'roles': roles_data,
        'departments': departments_data
    })


@api.route('/user/secure/create', methods=['POST'])
def create_secure_user():
    """创建安全用户

    权限：超级管理员可创建任意权限用户，部门管理员只能创建本部门的普通用户
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        raise APIException('未登录', 40101, 401)

    current = g.current_user
    args = request.get_json() or request.form
    username = get_or_exception('username', args, 'str')
    password = args.get('password') or '123456'  # 默认密码（空字符串也使用默认值）
    permission_level = get_or_exception('permission_level', args, 'int', SecureUser.PermissionLevel.REGULAR_USER)
    department_id = args.get('department_id', 0)

    # 验证输入
    if len(username.strip()) < 3:
        raise APIException('用户名长度不能少于3位')

    # 权限检查
    if current.is_super_admin():
        # 超级管理员可以创建任意权限的用户
        valid_levels = [
            SecureUser.PermissionLevel.SUPER_ADMIN,
            SecureUser.PermissionLevel.DEPT_MANAGER,
            SecureUser.PermissionLevel.REGULAR_USER
        ]
        if permission_level not in valid_levels:
            raise APIException('无效的权限等级')
    elif current.is_dept_manager():
        # 部门管理员只能创建本部门的普通用户
        if permission_level != SecureUser.PermissionLevel.REGULAR_USER:
            raise APIException('部门管理员只能创建普通用户')
        if department_id != current.department_id:
            raise APIException('只能在自己的部门创建用户')
        # 强制设置为当前用户的部门
        department_id = current.department_id
    else:
        raise APIException('权限不足', 40301, 403)

    # 验证部门是否存在
    if department_id:
        dept = Department.query.get(department_id)
        if not dept or not dept.is_active_department():
            raise APIException('部门不存在或已禁用')

    # 检查用户名是否已存在
    existing_user = db.session.query(SecureUser).filter(SecureUser.username == username).first()
    if existing_user:
        raise APIException('用户名已存在')

    # 创建新用户
    new_user = SecureUser(
        username=username.strip(),
        permission_level=permission_level,
        department_id=department_id,
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
        'user_id': new_user.id,
        'user': new_user.to_dict(include_department=True)
    })


@api.route('/user/secure/update', methods=['POST'])
def update_secure_user():
    """更新安全用户信息

    权限：超级管理员可修改任意用户，部门管理员只能修改本部门的普通用户
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        raise APIException('未登录', 40101, 401)

    current = g.current_user
    args = request.get_json() or request.form
    user_id = get_or_exception('user_id', args, 'int')
    permission_level = args.get('permission_level')
    department_id = args.get('department_id')
    status = args.get('status')

    # 获取目标用户
    user = db.session.query(SecureUser).filter_by(id=user_id).first()
    if not user:
        raise APIException('用户不存在')

    # 不能修改自己的权限等级和部门
    if user_id == current_user_id:
        if permission_level is not None and permission_level != user.permission_level:
            raise APIException('不能修改自己的权限等级')
        if department_id is not None and department_id != user.department_id:
            raise APIException('不能修改自己的部门')

    # 权限检查：是否可以管理目标用户
    error = check_can_manage_user(user)
    if error:
        return error

    # 超级管理员可以修改所有字段
    if current.is_super_admin():
        if permission_level is not None:
            valid_levels = [
                SecureUser.PermissionLevel.SUPER_ADMIN,
                SecureUser.PermissionLevel.DEPT_MANAGER,
                SecureUser.PermissionLevel.REGULAR_USER
            ]
            if permission_level not in valid_levels:
                raise APIException('无效的权限等级')
            user.permission_level = permission_level

        if department_id is not None:
            dept = Department.query.get(department_id)
            if not dept or not dept.is_active_department():
                raise APIException('部门不存在或已禁用')
            user.department_id = department_id

        if status is not None:
            user.status = status

    elif current.is_dept_manager():
        # 部门管理员只能修改状态，不能修改权限等级和部门
        if permission_level is not None and permission_level != user.permission_level:
            raise APIException('部门管理员不能修改用户权限等级')
        if department_id is not None and department_id != user.department_id:
            raise APIException('部门管理员不能修改用户部门')
        if status is not None:
            user.status = status

    user.updated_at = datetime.now()
    db.session.commit()

    return success({
        'message': f'用户 {user.username} 信息更新成功',
        'user': user.to_dict(include_department=True)
    })


@api.route('/user/secure/delete', methods=['POST'])
def delete_secure_user():
    """删除（禁用）安全用户

    权限：超级管理员可删除任意用户，部门管理员只能删除本部门的普通用户
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        raise APIException('未登录', 40101, 401)

    args = request.get_json() or request.args
    user_id = get_or_exception('user_id', args, 'int')

    # 获取用户
    user = db.session.query(SecureUser).filter_by(id=user_id).first()
    if not user:
        raise APIException('用户不存在')

    # 不能删除自己
    if user_id == current_user_id:
        raise APIException('不能删除自己的账户')

    # 权限检查：是否可以管理目标用户
    error = check_can_manage_user(user)
    if error:
        return error

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
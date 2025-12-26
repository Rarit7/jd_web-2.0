"""
权限检查辅助函数
用于部门和用户管理的权限验证
"""
from functools import wraps
from flask import g, jsonify

from jd.models.secure_user import SecureUser
from jd.models.department_tg_account import DepartmentTgAccount
from jd.views import APIException


def check_super_admin():
    """检查当前用户是否为超级管理员

    Returns:
        tuple: 如果不是超级管理员，返回错误响应；否则返回None
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        return jsonify({'err_code': 401, 'err_msg': '未登录'}), 401

    if g.current_user.permission_level != SecureUser.PermissionLevel.SUPER_ADMIN:
        return jsonify({'err_code': 403, 'err_msg': '仅超级管理员可操作'}), 403

    return None


def check_department_access(dept_id):
    """检查用户是否可访问指定部门

    Args:
        dept_id: 部门ID

    Returns:
        tuple: 如果无权访问，返回错误响应；否则返回None
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        return jsonify({'err_code': 401, 'err_msg': '未登录'}), 401

    user = g.current_user

    # 超级管理员可访问所有部门
    if user.permission_level == SecureUser.PermissionLevel.SUPER_ADMIN:
        return None

    # 其他用户只能访问自己的部门
    if user.department_id != dept_id:
        return jsonify({'err_code': 403, 'err_msg': '无权访问该部门'}), 403

    return None


def check_can_manage_user(target_user):
    """检查当前用户是否可以管理目标用户

    Args:
        target_user: 目标用户对象（SecureUser实例）

    Returns:
        tuple: 如果无权管理，返回错误响应；否则返回None
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        return jsonify({'err_code': 401, 'err_msg': '未登录'}), 401

    operator = g.current_user

    # 超级管理员可以管理所有用户
    if operator.is_super_admin():
        return None

    # 部门管理员只能管理本部门的普通用户
    if operator.is_dept_manager():
        if operator.department_id == target_user.department_id and target_user.is_regular_user():
            return None
        else:
            return jsonify({'err_code': 403, 'err_msg': '只能管理本部门的普通用户'}), 403

    # 普通用户无权管理其他用户
    return jsonify({'err_code': 403, 'err_msg': '权限不足'}), 403


def get_accessible_tg_user_ids(user):
    """获取用户可访问的TG账户ID列表

    Args:
        user: 用户对象（SecureUser实例）

    Returns:
        list or None: TG账户user_id列表，超级管理员返回None表示无限制
    """
    # 超级管理员可以访问所有TG账户
    if user.is_super_admin():
        return None

    # 其他用户根据部门过滤
    tg_user_ids = DepartmentTgAccount.get_tg_user_ids_by_department(user.department_id)

    return tg_user_ids


def get_accessible_department_ids(user):
    """获取用户可访问的部门ID列表

    Args:
        user: 用户对象（SecureUser实例）

    Returns:
        list or None: 部门ID列表，超级管理员返回None表示无限制
    """
    # 超级管理员可以访问所有部门
    if user.is_super_admin():
        return None

    # 其他用户只能访问自己的部门
    return [user.department_id]


def require_super_admin(f):
    """装饰器：要求超级管理员权限

    Usage:
        @require_super_admin
        def some_admin_function():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        error = check_super_admin()
        if error:
            return error
        return f(*args, **kwargs)
    return decorated_function


def require_manager_or_above(f):
    """装饰器：要求管理员权限（部门管理员或超级管理员）

    Usage:
        @require_manager_or_above
        def some_manager_function():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user:
            return jsonify({'err_code': 401, 'err_msg': '未登录'}), 401

        user = g.current_user
        if user.permission_level > SecureUser.PermissionLevel.DEPT_MANAGER:
            return jsonify({'err_code': 403, 'err_msg': '需要管理员权限'}), 403

        return f(*args, **kwargs)
    return decorated_function

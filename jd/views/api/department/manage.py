"""
部门管理API - CRUD操作
"""
from flask import request, g
from datetime import datetime

from jd import db
from jd.models.department import Department
from jd.models.secure_user import SecureUser
from jd.views import get_or_exception, APIException, success
from jd.views.api import api
from jd.helpers.permission_helper import check_super_admin, check_department_access
from jd.services.role_service.role import ROLE_SUPER_ADMIN


@api.route('/department/list', methods=['GET'])
def get_departments():
    """获取部门列表

    权限：超级管理员可查看所有部门，部门管理员只能查看自己的部门
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        raise APIException('未登录', 40101, 401)

    user = g.current_user

    # 构建查询
    query = Department.query.filter_by(is_active=Department.StatusType.ENABLED)

    # 非超级管理员只能看自己的部门
    if not user.is_super_admin():
        query = query.filter_by(id=user.department_id)

    departments = query.order_by(Department.id.asc()).all()

    # 转换为字典格式（包含统计信息）
    data = [dept.to_dict(include_counts=True) for dept in departments]

    return success({
        'data': data,
        'total': len(data)
    })


@api.route('/department/create', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def create_department():
    """创建部门

    权限：仅超级管理员
    """
    args = request.get_json() or request.form
    name = get_or_exception('name', args, 'str')
    description = args.get('description', '')

    # 验证部门名称
    if len(name.strip()) < 2:
        raise APIException('部门名称长度不能少于2位')

    # 检查部门名是否已存在
    existing = Department.query.filter_by(name=name).first()
    if existing:
        raise APIException('部门名称已存在')

    # 创建部门
    dept = Department(
        name=name.strip(),
        description=description.strip() if description else None
    )

    db.session.add(dept)
    db.session.commit()

    return success({
        'message': f'部门 {name} 创建成功',
        'data': dept.to_dict(include_counts=False)
    })


@api.route('/department/update', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def update_department():
    """更新部门信息

    权限：仅超级管理员
    """
    args = request.get_json() or request.form
    dept_id = get_or_exception('dept_id', args, 'int')
    name = args.get('name')
    description = args.get('description')
    is_active = args.get('is_active')

    # 获取部门
    dept = Department.query.get(dept_id)
    if not dept:
        raise APIException('部门不存在')

    # 不允许修改全局部门的某些属性
    if Department.is_global_department(dept_id) and name:
        raise APIException('不允许修改全局部门名称')

    # 更新字段
    if name and name.strip():
        # 检查名称是否重复
        existing = Department.query.filter(
            Department.name == name,
            Department.id != dept_id
        ).first()
        if existing:
            raise APIException('部门名称已存在')
        dept.name = name.strip()

    if description is not None:
        dept.description = description.strip() if description else None

    if is_active is not None:
        # 不允许禁用全局部门
        if Department.is_global_department(dept_id) and is_active == 0:
            raise APIException('不允许禁用全局部门')
        dept.is_active = int(is_active)

    dept.updated_at = datetime.now()
    db.session.commit()

    return success({
        'message': f'部门 {dept.name} 更新成功',
        'data': dept.to_dict(include_counts=False)
    })


@api.route('/department/delete', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def delete_department():
    """删除部门（软删除）

    权限：仅超级管理员
    逻辑：
      - 不允许删除全局部门（ID=0）
      - 检查是否有用户，有则拒绝删除
      - 软删除（设置is_active=0）
    """
    args = request.get_json() or request.args
    dept_id = get_or_exception('dept_id', args, 'int')

    # 不允许删除全局部门
    if Department.is_global_department(dept_id):
        raise APIException('不允许删除全局部门')

    # 获取部门
    dept = Department.query.get(dept_id)
    if not dept:
        raise APIException('部门不存在')

    # 检查是否有用户
    user_count = SecureUser.query.filter_by(department_id=dept_id).count()
    if user_count > 0:
        raise APIException(f'该部门还有 {user_count} 个用户，请先转移用户后再删除')

    # 软删除
    dept.is_active = Department.StatusType.DISABLED
    dept.updated_at = datetime.now()
    db.session.commit()

    return success({
        'message': f'部门 {dept.name} 已删除'
    })


@api.route('/department/info', methods=['GET'])
def get_department_info():
    """获取部门详细信息

    权限：超级管理员可查看所有部门，其他用户只能查看自己的部门
    """
    args = request.args
    dept_id = get_or_exception('dept_id', args, 'int')

    # 检查访问权限
    error = check_department_access(dept_id)
    if error:
        return error

    # 获取部门
    dept = Department.query.get(dept_id)
    if not dept:
        raise APIException('部门不存在')

    # 获取部门下的用户列表
    users = SecureUser.query.filter_by(department_id=dept_id).all()
    users_data = [user.to_dict(include_department=False) for user in users]

    # 返回部门信息及用户列表
    dept_data = dept.to_dict(include_counts=True)
    dept_data['users'] = users_data

    return success({
        'data': dept_data
    })


@api.route('/department/available', methods=['GET'])
def get_available_departments():
    """获取可用的部门列表（用于下拉选择）

    权限：所有登录用户
    返回：超级管理员看到所有部门，其他用户只看到自己的部门
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        raise APIException('未登录', 40101, 401)

    user = g.current_user

    # 构建查询（只返回启用的部门）
    query = Department.query.filter_by(is_active=Department.StatusType.ENABLED)

    # 非超级管理员只能看自己的部门
    if not user.is_super_admin():
        query = query.filter_by(id=user.department_id)

    departments = query.order_by(Department.id.asc()).all()

    # 简化的部门信息（只包含id和name）
    data = [{'id': dept.id, 'name': dept.name} for dept in departments]

    return success({
        'data': data
    })

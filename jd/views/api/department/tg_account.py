"""
部门-TG账户关联管理API
"""
from flask import request, g

from jd import db
from jd.models.department import Department
from jd.models.department_tg_account import DepartmentTgAccount
from jd.models.tg_account import TgAccount
from jd.views import get_or_exception, APIException, success
from jd.views.api import api
from jd.helpers.permission_helper import check_super_admin, check_department_access
from jd.helpers.user import current_user_id
from jd.services.role_service.role import ROLE_SUPER_ADMIN


@api.route('/department/<int:dept_id>/tg_accounts', methods=['GET'])
def get_department_tg_accounts(dept_id):
    """获取部门关联的TG账户列表

    权限：超级管理员可查看所有部门，其他用户只能查看自己的部门
    """
    # 检查访问权限
    error = check_department_access(dept_id)
    if error:
        return error

    # 获取部门
    dept = Department.query.get(dept_id)
    if not dept:
        raise APIException('部门不存在')

    # 获取关联记录
    relations = DepartmentTgAccount.query.filter_by(department_id=dept_id).all()

    # 获取TG账户详细信息
    data = []
    for rel in relations:
        rel_dict = rel.to_dict()

        # 尝试获取TG账户的详细信息
        tg_account = TgAccount.query.filter_by(user_id=rel.tg_user_id).first()
        if tg_account:
            rel_dict['tg_account_info'] = {
                'id': tg_account.id,
                'phone': tg_account.phone,
                'username': tg_account.username,
                'user_id': tg_account.user_id
            }
        else:
            rel_dict['tg_account_info'] = None

        data.append(rel_dict)

    return success({
        'data': data,
        'department': dept.to_dict(include_counts=False)
    })


@api.route('/department/<int:dept_id>/tg_accounts', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def update_department_tg_accounts(dept_id):
    """配置部门-TG账户关联（替换模式）

    权限：仅超级管理员
    逻辑：删除该部门的所有旧关联，添加新关联
    """
    args = request.get_json() or request.form
    tg_user_ids = args.get('tg_user_ids', [])

    # 验证输入
    if not isinstance(tg_user_ids, list):
        raise APIException('tg_user_ids必须是数组')

    # 获取部门
    dept = Department.query.get(dept_id)
    if not dept:
        raise APIException('部门不存在')

    # 使用模型方法替换关联
    try:
        DepartmentTgAccount.replace_department_relations(
            department_id=dept_id,
            tg_user_ids=tg_user_ids,
            created_by=current_user_id
        )
        db.session.commit()

        return success({
            'message': f'部门 {dept.name} 的TG账户关联已更新',
            'count': len(tg_user_ids)
        })

    except Exception as e:
        db.session.rollback()
        raise APIException(f'更新关联失败: {str(e)}')


@api.route('/department/<int:dept_id>/tg_accounts/add', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def add_department_tg_account(dept_id):
    """为部门添加单个TG账户关联

    权限：仅超级管理员
    """
    args = request.get_json() or request.form
    tg_user_id = get_or_exception('tg_user_id', args, 'str')

    # 获取部门
    dept = Department.query.get(dept_id)
    if not dept:
        raise APIException('部门不存在')

    # 检查关联是否已存在
    existing = DepartmentTgAccount.query.filter_by(
        department_id=dept_id,
        tg_user_id=tg_user_id
    ).first()

    if existing:
        raise APIException('该TG账户已关联到此部门')

    # 添加关联
    relation = DepartmentTgAccount.add_relation(
        department_id=dept_id,
        tg_user_id=tg_user_id,
        created_by=current_user_id
    )

    db.session.add(relation)
    db.session.commit()

    return success({
        'message': 'TG账户关联添加成功',
        'data': relation.to_dict()
    })


@api.route('/department/<int:dept_id>/tg_accounts/remove', methods=['POST'], roles=[ROLE_SUPER_ADMIN])
def remove_department_tg_account(dept_id):
    """移除部门的单个TG账户关联

    权限：仅超级管理员
    """
    args = request.get_json() or request.form
    tg_user_id = get_or_exception('tg_user_id', args, 'str')

    # 获取部门
    dept = Department.query.get(dept_id)
    if not dept:
        raise APIException('部门不存在')

    # 查找关联
    relation = DepartmentTgAccount.remove_relation(dept_id, tg_user_id)

    if not relation:
        raise APIException('该TG账户未关联到此部门')

    db.session.delete(relation)
    db.session.commit()

    return success({
        'message': 'TG账户关联已移除'
    })


@api.route('/tg_accounts/available', methods=['GET'])
def get_available_tg_accounts():
    """获取所有可用的TG账户列表（用于关联配置）

    权限：超级管理员
    返回：所有TG账户（去重by user_id）
    """
    if not hasattr(g, 'current_user') or not g.current_user:
        raise APIException('未登录', 40101, 401)

    if not g.current_user.is_super_admin():
        raise APIException('仅超级管理员可查看', 40301, 403)

    # 获取所有TG账户，按user_id去重
    # 注意：一个账户可能有多个session，我们只需要user_id唯一的账户
    tg_accounts = db.session.query(TgAccount)\
        .distinct(TgAccount.user_id)\
        .filter(TgAccount.user_id.isnot(None))\
        .order_by(TgAccount.user_id, TgAccount.id.desc())\
        .all()

    # 返回简化的账户信息
    data = []
    seen_user_ids = set()

    for account in tg_accounts:
        if account.user_id and account.user_id not in seen_user_ids:
            seen_user_ids.add(account.user_id)
            data.append({
                'user_id': account.user_id,
                'phone': account.phone,
                'username': account.username,
                'first_name': account.nickname or '',  # Use nickname as first_name
                'last_name': '',  # TgAccount model doesn't have last_name
                # 显示名称：优先使用username，否则使用nickname
                'display_name': account.username or account.nickname or account.phone
            })

    return success({
        'data': data,
        'total': len(data)
    })

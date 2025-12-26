from functools import wraps

from flask import Blueprint, redirect, url_for, g
from flask_jwt_extended import JWTManager

from jd import app, db
from jd.helpers.user import current_user_id
from jd.models.user_role import UserRole
from jd.models.secure_user import SecureUser
from jd.services.role_service.role import ROLE_MAP
from jd.views import APIException

jwtmanager = JWTManager(app)


class ApiBlueprint(Blueprint):

    def route(self, rule, need_login=True, roles=[], **options):
        """
        web api路由
        :param rule:
        :param need_login:
        :param roles: 角色列表
        :param options:
        :return:
        """

        def decorator(fn):
            endpoint = options.pop('endpoints', fn.__name__)

            @wraps(fn)
            def decorated_view(*args, **kwargs):
                # 设置g.current_user对象（用于部门权限检查）
                if current_user_id and not hasattr(g, 'current_user'):
                    user = db.session.query(SecureUser).filter_by(id=current_user_id).first()
                    g.current_user = user

                if need_login and not current_user_id:
                    raise APIException('未登录', 40101, 401)

                if roles:
                    role_ids = [ROLE_MAP.get(role, 0) for role in roles]
                    user_role = db.session.query(UserRole).filter(UserRole.user_id == current_user_id,
                                                                  UserRole.role_id.in_(role_ids),
                                                                  UserRole.status == UserRole.StatusType.VALID).first()
                    if not user_role:
                        raise APIException('权限不足', 40301, 403)

                api_rule = '%s.%s' % ('api', rule.lstrip('/').replace('.', '_'))
                rs = fn(*args, **kwargs)

                db.session.commit()

                return rs

            self.add_url_rule(rule, endpoint,
                              view_func=decorated_view, **options)
            return decorated_view

        return decorator


api = ApiBlueprint('api', 'api')

# 导入各个模块以注册路由
# from . import index  # removed
from . import user
from . import tg
from . import chemical
from . import black_keyword
from . import tag
from . import change_record
from . import system
from . import job_queue
from . import ad_tracking
from . import user_profile
from . import department

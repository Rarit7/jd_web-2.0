"""
用户档案管理 API
"""
from flask import request, jsonify

from jd import db
from jd.models.analytics_user_profile import AnalyticsUserProfile
from jd.models.analytics_user_profile_folder import AnalyticsUserProfileFolder
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.views import get_or_exception, success
from jd.views.api import api


@api.route('/user-profile/profiles', methods=['GET'])
def list_profiles():
    """
    获取档案列表

    Query Parameters:
        - folder_id (int, optional): 所属文件夹ID
        - status (str, optional): 档案状态 (draft/generated/archived)
        - search_name (str, optional): 搜索档案名称
        - tg_user_id (str, optional): Telegram用户ID
        - page (int): 页码 (默认 1)
        - page_size (int): 每页数量 (默认 20)

    Returns:
        {
            "err_code": 0,
            "err_msg": "",
            "payload": {
                "data": [...],
                "total": 10,
                "page": 1,
                "page_size": 20
            }
        }
    """
    try:
        args = request.args
        folder_id = get_or_exception('folder_id', args, 'int', None)
        status = get_or_exception('status', args, 'str', '')
        search_name = get_or_exception('search_name', args, 'str', '')
        tg_user_id = get_or_exception('tg_user_id', args, 'str', '')
        page = get_or_exception('page', args, 'int', 1)
        page_size = get_or_exception('page_size', args, 'int', 20)

        query = AnalyticsUserProfile.query.filter_by(is_deleted=False)

        if folder_id is not None:
            query = query.filter_by(folder_id=folder_id)

        if status:
            query = query.filter_by(status=status)

        if search_name:
            query = query.filter(AnalyticsUserProfile.profile_name.like(f'%{search_name}%'))

        if tg_user_id:
            query = query.filter_by(tg_user_id=tg_user_id)

        total = query.count()
        offset = (page - 1) * page_size
        profiles = query.order_by(
            AnalyticsUserProfile.sort_order
        ).offset(offset).limit(page_size).all()

        data = [profile.to_dict(include_folder=True) for profile in profiles]

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'data': data,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/user-profile/profiles/<int:profile_id>', methods=['GET'])
def get_profile(profile_id):
    """
    获取单个档案详情

    Returns:
        {
            "err_code": 0,
            "err_msg": "",
            "payload": {
                "profile": {...},
                "tg_user_info": {...}  # 关联的TG用户信息
            }
        }
    """
    try:
        profile = AnalyticsUserProfile.query.filter_by(
            id=profile_id, is_deleted=False
        ).first()

        if not profile:
            return jsonify({
                'err_code': 1,
                'err_msg': '档案不存在',
                'payload': {}
            }), 404

        # 获取关联的TG用户信息
        tg_user_info = profile.get_tg_user_info()

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'profile': profile.to_dict(include_folder=True),
                'tg_user_info': tg_user_info.to_dict() if tg_user_info else None
            }
        })
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/user-profile/profiles/by-tg-user/<string:tg_user_id>', methods=['GET'])
def get_profile_by_tg_user(tg_user_id):
    """
    根据Telegram用户ID获取档案

    Returns:
        {
            "err_code": 0,
            "err_msg": "",
            "payload": {
                "profile": {...},
                "tg_user_info": {...}
            }
        }
    """
    try:
        profile = AnalyticsUserProfile.get_by_tg_user_id(tg_user_id)

        if not profile:
            # 档案不存在是正常业务状态
            # 返回 200 + err_code:1，但不使用 err_msg 以避免前端axios拦截器自动弹窗
            return jsonify({
                'err_code': 1,
                'err_msg': '',  # 空的err_msg，这样axios拦截器不会弹窗
                'payload': {}
            })

        tg_user_info = profile.get_tg_user_info()

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'profile': profile.to_dict(include_folder=True),
                'tg_user_info': tg_user_info.to_dict() if tg_user_info else None
            }
        })
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/user-profile/profiles', methods=['POST'])
def create_profile():
    """
    创建档案

    Request Body:
        {
            "tg_user_id": "123456789",
            "profile_name": "张三",
            "created_by": 1,
            "folder_id": 1,  # 可选
            "status": "draft"  # 可选 (draft/generated/archived)
        }

    Returns:
        {
            "err_code": 0,
            "err_msg": "创建成功",
            "payload": {
                "profile": {...}
            }
        }
    """
    try:
        data = request.json
        tg_user_id = get_or_exception('tg_user_id', data, 'str')
        profile_name = get_or_exception('profile_name', data, 'str')
        created_by = get_or_exception('created_by', data, 'int')
        # 处理 folder_id，允许为 null
        folder_id_raw = data.get('folder_id', None)
        folder_id = int(folder_id_raw) if folder_id_raw is not None else None
        status = get_or_exception('status', data, 'str', 'draft')

        # 检查该用户是否已有档案
        existing = AnalyticsUserProfile.get_by_tg_user_id(tg_user_id)
        if existing:
            return jsonify({
                'err_code': 1,
                'err_msg': '该用户已存在档案',
                'payload': {'profile_id': existing.id}
            }), 400

        # 验证TG用户是否存在
        tg_user = TgGroupUserInfo.query.filter_by(user_id=tg_user_id).first()
        if not tg_user:
            return jsonify({
                'err_code': 1,
                'err_msg': 'Telegram用户不存在',
                'payload': {}
            }), 404

        # 验证文件夹是否存在
        if folder_id is not None:
            folder = AnalyticsUserProfileFolder.query.filter_by(
                id=folder_id, is_deleted=False
            ).first()
            if not folder:
                return jsonify({
                    'err_code': 1,
                    'err_msg': '文件夹不存在',
                    'payload': {}
                }), 404

        # 计算排序值
        if folder_id is not None:
            max_order = db.session.query(
                db.func.max(AnalyticsUserProfile.sort_order)
            ).filter_by(folder_id=folder_id, is_deleted=False).scalar() or 0
        else:
            max_order = db.session.query(
                db.func.max(AnalyticsUserProfile.sort_order)
            ).filter_by(folder_id=None, is_deleted=False).scalar() or 0

        profile = AnalyticsUserProfile.create_from_tg_user(
            tg_user_id=tg_user_id,
            profile_name=profile_name,
            created_by=created_by,
            folder_id=folder_id,
            status=status
        )
        profile.sort_order = max_order + 1

        db.session.add(profile)
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '创建成功',
            'payload': {
                'profile': profile.to_dict(include_folder=True)
            }
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR in create_profile: {error_detail}")
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {'error_detail': error_detail}
        }), 500


@api.route('/user-profile/profiles/<int:profile_id>', methods=['PUT'])
def update_user_profile(profile_id):
    """
    更新档案信息

    Request Body:
        {
            "profile_name": "新名称",  # 可选
            "status": "generated",  # 可选
            "folder_id": 1,  # 可选，更新所属文件夹
            "config": {...}  # 可选
        }
    """
    try:
        profile = AnalyticsUserProfile.query.filter_by(
            id=profile_id, is_deleted=False
        ).first()

        if not profile:
            return jsonify({
                'err_code': 1,
                'err_msg': '档案不存在',
                'payload': {}
            }), 404

        data = request.json or {}

        if 'profile_name' in data:
            profile.profile_name = data['profile_name']

        if 'status' in data:
            profile.status = data['status']

        if 'folder_id' in data:
            folder_id = data.get('folder_id')
            # 转换为整数或 None
            if folder_id is not None:
                try:
                    folder_id = int(folder_id)
                    # 验证文件夹是否存在
                    folder = AnalyticsUserProfileFolder.query.filter_by(
                        id=folder_id, is_deleted=False
                    ).first()
                    if not folder:
                        return jsonify({
                            'err_code': 1,
                            'err_msg': '指定的文件夹不存在',
                            'payload': {}
                        }), 404
                except (ValueError, TypeError):
                    return jsonify({
                        'err_code': 1,
                        'err_msg': '文件夹ID格式错误',
                        'payload': {}
                    }), 400
            else:
                folder_id = None
            profile.folder_id = folder_id

        if 'config' in data:
            profile.update_config(data['config'])

        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '更新成功',
            'payload': {
                'profile': profile.to_dict()
            }
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR in update_user_profile: {error_detail}")
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {'traceback': error_detail}
        }), 500


@api.route('/user-profile/profiles/<int:profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    """
    删除档案(软删除)
    """
    try:
        profile = AnalyticsUserProfile.query.filter_by(
            id=profile_id, is_deleted=False
        ).first()

        if not profile:
            return jsonify({
                'err_code': 1,
                'err_msg': '档案不存在',
                'payload': {}
            }), 404

        profile.soft_delete()
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '删除成功',
            'payload': {}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/user-profile/profiles/<int:profile_id>/move', methods=['POST'])
def move_profile(profile_id):
    """
    移动档案到新文件夹

    Request Body:
        {
            "new_folder_id": 2  # null 表示移动到根目录
        }
    """
    try:
        profile = AnalyticsUserProfile.query.filter_by(
            id=profile_id, is_deleted=False
        ).first()

        if not profile:
            return jsonify({
                'err_code': 1,
                'err_msg': '档案不存在',
                'payload': {}
            }), 404

        data = request.json
        new_folder_id = data.get('new_folder_id', None)

        # 验证目标文件夹
        if new_folder_id is not None:
            folder = AnalyticsUserProfileFolder.query.filter_by(
                id=new_folder_id, is_deleted=False
            ).first()
            if not folder:
                return jsonify({
                    'err_code': 1,
                    'err_msg': '目标文件夹不存在',
                    'payload': {}
                }), 404

        profile.move_to_folder(new_folder_id)
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '移动成功',
            'payload': {
                'profile': profile.to_dict(include_folder=True)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/user-profile/profiles/<int:profile_id>/refresh', methods=['POST'])
def refresh_profile(profile_id):
    """
    刷新档案数据(更新最后刷新时间)
    """
    try:
        profile = AnalyticsUserProfile.query.filter_by(
            id=profile_id, is_deleted=False
        ).first()

        if not profile:
            return jsonify({
                'err_code': 1,
                'err_msg': '档案不存在',
                'payload': {}
            }), 404

        profile.refresh_data()
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '刷新成功',
            'payload': {
                'profile': profile.to_dict(include_folder=True)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500

"""
用户档案文件夹管理 API
"""
from flask import request, jsonify

from jd import db
from jd.models.analytics_user_profile_folder import AnalyticsUserProfileFolder
from jd.views import get_or_exception, success
from jd.views.api import api


@api.route('/user-profile/folders/tree', methods=['GET'])
def get_folder_tree():
    """
    获取文件夹树形结构数据

    Query Parameters:
        - user_id (int, optional): 筛选特定用户创建的文件夹

    Returns:
        {
            "err_code": 0,
            "err_msg": "",
            "payload": {
                "tree_data": [
                    {
                        "id": "folder_1",
                        "label": "商家",
                        "type": "folder",
                        "icon": "Folder",
                        "children": [...]
                    }
                ]
            }
        }
    """
    try:
        args = request.args
        # user_id 是可选参数，直接从 request.args 获取
        user_id = args.get('user_id', None)
        if user_id is not None:
            user_id = int(user_id)

        tree_data = AnalyticsUserProfileFolder.get_tree_data(user_id=user_id)

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'tree_data': tree_data
            }
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR in get_folder_tree: {error_detail}")
        return jsonify({
            'err_code': 1,
            'err_msg': f'{type(e).__name__}: {str(e)}',
            'payload': {'traceback': error_detail}
        }), 500


@api.route('/user-profile/folders', methods=['GET'])
def list_folders():
    """
    获取文件夹列表(扁平结构)

    Query Parameters:
        - parent_id (int, optional): 父文件夹ID
        - user_id (int, optional): 创建者ID
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
        parent_id = args.get('parent_id', None)
        if parent_id is not None:
            parent_id = int(parent_id)
        user_id = args.get('user_id', None)
        if user_id is not None:
            user_id = int(user_id)
        page = int(args.get('page', 1))
        page_size = int(args.get('page_size', 20))

        query = AnalyticsUserProfileFolder.query.filter_by(is_deleted=False)

        if parent_id is not None:
            query = query.filter_by(parent_id=parent_id)

        if user_id is not None:
            query = query.filter_by(user_id=user_id)

        total = query.count()
        offset = (page - 1) * page_size
        folders = query.order_by(
            AnalyticsUserProfileFolder.sort_order
        ).offset(offset).limit(page_size).all()

        data = [folder.to_dict() for folder in folders]

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


@api.route('/user-profile/folders', methods=['POST'])
def create_folder():
    """
    创建文件夹

    Request Body:
        {
            "name": "文件夹名称",
            "parent_id": 1,  # 可选
            "user_id": 1
        }

    Returns:
        {
            "err_code": 0,
            "err_msg": "创建成功",
            "payload": {
                "folder": {...}
            }
        }
    """
    try:
        data = request.json
        name = get_or_exception('name', data, 'str')
        user_id = get_or_exception('user_id', data, 'int')
        parent_id = data.get('parent_id', None)
        if parent_id is not None:
            parent_id = int(parent_id)

        # 验证父文件夹是否存在
        if parent_id is not None:
            parent = AnalyticsUserProfileFolder.query.filter_by(
                id=parent_id, is_deleted=False
            ).first()
            if not parent:
                return jsonify({
                    'err_code': 1,
                    'err_msg': '父文件夹不存在',
                    'payload': {}
                }), 404

        # 计算排序值(同级最后)
        if parent_id is not None:
            max_order = db.session.query(
                db.func.max(AnalyticsUserProfileFolder.sort_order)
            ).filter_by(parent_id=parent_id, is_deleted=False).scalar() or 0
        else:
            max_order = db.session.query(
                db.func.max(AnalyticsUserProfileFolder.sort_order)
            ).filter_by(parent_id=None, is_deleted=False).scalar() or 0

        folder = AnalyticsUserProfileFolder(
            name=name,
            parent_id=parent_id,
            user_id=user_id,
            sort_order=max_order + 1
        )

        db.session.add(folder)
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '创建成功',
            'payload': {
                'folder': folder.to_dict()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/user-profile/folders/<int:folder_id>', methods=['PUT'])
def update_folder(folder_id):
    """
    更新文件夹信息

    Request Body:
        {
            "name": "新名称"
        }
    """
    try:
        folder = AnalyticsUserProfileFolder.query.filter_by(
            id=folder_id, is_deleted=False
        ).first()

        if not folder:
            return jsonify({
                'err_code': 1,
                'err_msg': '文件夹不存在',
                'payload': {}
            }), 404

        data = request.json

        if 'name' in data:
            folder.name = data['name']

        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '更新成功',
            'payload': {
                'folder': folder.to_dict()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/user-profile/folders/<int:folder_id>', methods=['DELETE'])
def delete_folder(folder_id):
    """
    删除文件夹(软删除)

    注意: 会同时软删除所有子文件夹，但子文件夹中的档案会被移至根目录

    处理流程:
    1. 找出此文件夹及其所有子文件夹中的档案
    2. 将这些档案的 folder_id 设置为 NULL（移至根目录）
    3. 软删除此文件夹及其所有子文件夹
    """
    try:
        folder = AnalyticsUserProfileFolder.query.filter_by(
            id=folder_id, is_deleted=False
        ).first()

        if not folder:
            return jsonify({
                'err_code': 1,
                'err_msg': '文件夹不存在',
                'payload': {}
            }), 404

        # 导入 AnalyticsUserProfile 模型
        from jd.models.analytics_user_profile import AnalyticsUserProfile

        # 递归获取此文件夹及所有子文件夹的ID
        def get_all_folder_ids(f):
            folder_ids = [f.id]
            for child in f.children.filter_by(is_deleted=False):
                folder_ids.extend(get_all_folder_ids(child))
            return folder_ids

        all_folder_ids = get_all_folder_ids(folder)

        # 将这些文件夹中的所有档案移至根目录（folder_id = NULL）
        profiles_to_move = AnalyticsUserProfile.query.filter(
            AnalyticsUserProfile.folder_id.in_(all_folder_ids),
            AnalyticsUserProfile.is_deleted == False
        ).all()

        for profile in profiles_to_move:
            profile.folder_id = None

        # 软删除文件夹及其所有子文件夹
        def soft_delete_recursive(f):
            f.is_deleted = True
            for child in f.children.filter_by(is_deleted=False):
                soft_delete_recursive(child)

        soft_delete_recursive(folder)
        db.session.commit()

        moved_count = len(profiles_to_move)
        return jsonify({
            'err_code': 0,
            'err_msg': '删除成功' + (f'，已将 {moved_count} 个档案移至根目录' if moved_count > 0 else ''),
            'payload': {
                'moved_profiles_count': moved_count
            }
        })
    except Exception as e:
        db.session.rollback()
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR in delete_folder: {error_detail}")
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/user-profile/folders/<int:folder_id>/move', methods=['POST'])
def move_folder(folder_id):
    """
    移动文件夹到新父文件夹

    Request Body:
        {
            "new_parent_id": 2  # null 表示移动到根目录
        }
    """
    try:
        folder = AnalyticsUserProfileFolder.query.filter_by(
            id=folder_id, is_deleted=False
        ).first()

        if not folder:
            return jsonify({
                'err_code': 1,
                'err_msg': '文件夹不存在',
                'payload': {}
            }), 404

        data = request.json
        new_parent_id = data.get('new_parent_id', None)

        # 验证新父文件夹
        if new_parent_id is not None:
            new_parent = AnalyticsUserProfileFolder.query.filter_by(
                id=new_parent_id, is_deleted=False
            ).first()
            if not new_parent:
                return jsonify({
                    'err_code': 1,
                    'err_msg': '目标文件夹不存在',
                    'payload': {}
                }), 404

            # 防止循环引用 (不能移动到自己的子文件夹下)
            current = new_parent
            while current:
                if current.id == folder_id:
                    return jsonify({
                        'err_code': 1,
                        'err_msg': '不能移动到自己的子文件夹',
                        'payload': {}
                    }), 400
                current = current.parent

        folder.parent_id = new_parent_id
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '移动成功',
            'payload': {
                'folder': folder.to_dict()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500

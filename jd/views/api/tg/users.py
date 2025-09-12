import collections
from io import BytesIO
from urllib.parse import quote

import pandas as pd
from flask import request, make_response, session, jsonify
from sqlalchemy import or_

from jd import db
from jd.helpers.user import current_user_id
from jd.models.tg_group import TgGroup
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_group_user_tag import TgGroupUserTag
from jd.services.role_service.role import ROLE_SUPER_ADMIN, RoleService
from jd.services.tag import TagService
from jd.views import get_or_exception, success
from jd.views.api import api


@api.route('/tg/group_user/list', methods=['GET'])
def tg_group_user_list():
    args = request.args
    page = get_or_exception('page', args, 'int', 1)
    page_size = get_or_exception('page_size', args, 'int', 20)
    search_nickname = get_or_exception('search_nickname', args, 'str', '')
    search_desc = get_or_exception('search_desc', args, 'str', '')
    search_group_id = get_or_exception('search_group_id', args, 'str', '')
    group_id = get_or_exception('group_id', args, 'str', '')  # 支持前端发送的group_id参数
    search_username = get_or_exception('search_username', args, 'str', '')
    remark = get_or_exception('remark', args, 'str', '')
    keyword = get_or_exception('keyword', args, 'str', '')
    tag_ids = get_or_exception('tag_ids', args, 'str', '')
    
    try:
        offset = (page - 1) * page_size
        query = TgGroupUserInfo.query
        # 支持两种群组ID参数格式
        filter_group_id = search_group_id or group_id
        if filter_group_id:
            query = query.filter_by(chat_id=filter_group_id)
        if search_username:
            query = query.filter(TgGroupUserInfo.username.like(f'%{search_username}%'))
        if search_nickname:
            query = query.filter(TgGroupUserInfo.nickname.like(f'%{search_nickname}%'))
        if search_desc:
            query = query.filter(TgGroupUserInfo.desc.like(f'%{search_desc}%'))
        if remark:
            query = query.filter(TgGroupUserInfo.remark.like(f'%{remark}%'))
        if keyword:
            # 关键字搜索：昵称、用户名、备注、用户ID
            keyword_condition = or_(
                TgGroupUserInfo.nickname.like(f'%{keyword}%'),
                TgGroupUserInfo.username.like(f'%{keyword}%'),
                TgGroupUserInfo.remark.like(f'%{keyword}%'),
                TgGroupUserInfo.user_id.like(f'%{keyword}%'),
                TgGroupUserInfo.user_id == keyword  # 精确匹配数字类型的user_id
            )
            query = query.filter(keyword_condition)
        
        # Filter by tags if provided
        total_records = 0
        group_user_list = []
        if tag_ids:
            tag_id_list = [int(tid.strip()) for tid in tag_ids.split(',') if tid.strip().isdigit()]
            if tag_id_list:
                # Get user IDs that have any of the selected tags
                user_ids_with_tags = db.session.query(TgGroupUserTag.tg_user_id)\
                    .filter(TgGroupUserTag.tag_id.in_(tag_id_list))\
                    .distinct().all()
                if user_ids_with_tags:
                    user_ids_list = [uid[0] for uid in user_ids_with_tags]
                    query = query.filter(TgGroupUserInfo.id.in_(user_ids_list))
                    total_records = query.count()
                    group_user_list = query.order_by(TgGroupUserInfo.id.desc()).offset(offset).limit(page_size).all()
                else:
                    # No users match the tag filter, return empty result
                    total_records = 0
                    group_user_list = []
            else:
                total_records = 0
                group_user_list = []
        else:
            total_records = query.count()
            group_user_list = query.order_by(TgGroupUserInfo.id.desc()).offset(offset).limit(page_size).all()
        
        # Handle case when tag filtering returns empty results
        if tag_ids and (total_records == 0 or not group_user_list):
            return jsonify({
                'err_code': 0,
                'err_msg': '',
                'payload': {
                    'data': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0
                }
            })
        
        tag_list = TagService.list()
        chat_room = TgGroup.query.filter_by(status=TgGroup.StatusType.JOIN_SUCCESS).all()
        chat_room = {r.chat_id: r.name for r in chat_room}
        group_user_id_list = [group_user.id for group_user in group_user_list]
        parse_tag_list = TgGroupUserTag.query.filter(TgGroupUserTag.tg_user_id.in_(group_user_id_list)).all()
        parse_tag_result = collections.defaultdict(list)
        for p in parse_tag_list:
            parse_tag_result[p.tg_user_id].append(str(p.tag_id))
        tag_dict = {t['id']: t['name'] for t in tag_list}
        
        data = []
        for group_user in group_user_list:
            parse_tag = parse_tag_result.get(group_user.id, [])
            tag_text = ','.join([tag_dict.get(int(t), '') for t in parse_tag if tag_dict.get(int(t), '')])
            
            # 格式化数据以匹配前端TgUser接口
            user_data = {
                'id': group_user.id,
                'user_id': str(group_user.user_id),
                'username': group_user.username or '',
                'first_name': group_user.nickname or '',
                'last_name': '',
                'nickname': group_user.nickname or '',
                'avatar': group_user.avatar_path or '',
                'phone': '',
                'bio': group_user.desc or '',
                'notes': group_user.remark or '',
                'tags': tag_text,
                'tag_id_list': ','.join(parse_tag) if parse_tag else '',
                'status': 'active',
                'last_seen': group_user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if group_user.updated_at else '',
                'created_at': group_user.created_at.strftime('%Y-%m-%d %H:%M:%S') if group_user.created_at else '',
                'updated_at': group_user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if group_user.updated_at else '',
                'chat_id': group_user.chat_id,
                'group_name': chat_room.get(group_user.chat_id, ''),
                'is_key_focus': bool(group_user.is_key_focus) if hasattr(group_user, 'is_key_focus') else False
            }
            data.append(user_data)

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'data': data,
                'total': total_records,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_records + page_size - 1) // page_size
            }
        })
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/tg/group_user/download', methods=['GET'])
def tg_group_user_download():
    args = request.args
    search_nickname = get_or_exception('search_nickname', args, 'str', '')
    search_desc = get_or_exception('search_desc', args, 'str', '')
    search_group_id = get_or_exception('search_group_id', args, 'str', '')
    search_username = get_or_exception('search_username', args, 'str', '')
    query = TgGroupUserInfo.query
    if search_group_id:
        query = query.filter_by(chat_id=search_group_id)
    if search_username:
        query = query.filter(TgGroupUserInfo.username.like(f'%{search_username}%'))
    if search_nickname:
        query = query.filter(TgGroupUserInfo.nickname.like(f'%{search_nickname}%'))
    if search_desc:
        query = query.filter(TgGroupUserInfo.desc.like(f'%{search_desc}%'))
    group_user_list = query.order_by(TgGroupUserInfo.id.desc()).all()
    chat_room = TgGroup.query.filter_by(status=TgGroup.StatusType.JOIN_SUCCESS).all()
    chat_room = {r.chat_id: r.name for r in chat_room}
    unique_user = {}
    group_user = {group_user.user_id: {
        '群组': chat_room.get(group_user.chat_id, ''),
        '用户ID': group_user.user_id,
        '用户昵称': group_user.nickname,
        '用户名': group_user.username,
        '个人简介': group_user.desc,
    } for group_user in group_user_list}
    data = list(group_user.values())

    # 创建DataFrame
    columns = ['群组', '用户ID', '用户昵称', '用户名', '个人简介']
    df = pd.DataFrame(data, columns=columns)

    # 将DataFrame保存到Excel文件
    output = BytesIO()
    df.to_csv(output, index=False)

    # 设置响应头
    output.seek(0)
    response = make_response(output.getvalue())
    file_name = 'users.csv'
    response.headers[
        "Content-Disposition"] = f"attachment; filename={quote(file_name)}; filename*=utf-8''{quote(file_name)}"
    response.headers["Content-type"] = "text/csv"

    return response


@api.route('/tg/group_user/tag/update', methods=['POST'])
def tg_group_user_modify_tag():
    args = request.json
    tg_user_id = get_or_exception('tg_user_id', args, 'int')
    tag_id_list = get_or_exception('tag_id_list', args, 'str', '')
    remark = get_or_exception('remark', args, 'str', '')
    if tag_id_list:
        tag_id_list = tag_id_list.split(',')
        tag_id_list = [int(t) for t in tag_id_list]
    TgGroupUserTag.query.filter(TgGroupUserTag.tg_user_id == tg_user_id).delete()
    for tag_id in tag_id_list:
        obj = TgGroupUserTag(tg_user_id=tg_user_id, tag_id=tag_id)
        db.session.add(obj)
    TgGroupUserInfo.query.filter(TgGroupUserInfo.id == tg_user_id).update({
        'remark': remark
    })
    db.session.commit()
    return success()


@api.route('/tg/group_user/focus/toggle', methods=['POST'])
def tg_group_user_toggle_focus():
    """切换用户关注状态"""
    try:
        args = request.json
        tg_user_id = get_or_exception('tg_user_id', args, 'int')
        
        user = TgGroupUserInfo.query.filter(TgGroupUserInfo.id == tg_user_id).first()
        if not user:
            return jsonify({
                'err_code': 1,
                'err_msg': '用户不存在',
                'payload': {}
            }), 404
        
        # 切换关注状态
        current_focus = bool(user.is_key_focus) if hasattr(user, 'is_key_focus') else False
        new_focus = not current_focus
        
        TgGroupUserInfo.query.filter(TgGroupUserInfo.id == tg_user_id).update({
            'is_key_focus': new_focus
        })
        db.session.commit()
        
        return jsonify({
            'err_code': 0,
            'err_msg': '操作成功',
            'payload': {
                'is_key_focus': new_focus,
                'message': '已关注' if new_focus else '已取消关注'
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/tg/group_user/by_user_id', methods=['GET'])
def get_user_by_user_id():
    """根据user_id获取用户信息"""
    args = request.args
    user_id = get_or_exception('user_id', args, 'str')
    
    try:
        # 直接根据user_id查询，返回第一个匹配的记录
        user_record = TgGroupUserInfo.query.filter_by(user_id=user_id).first()
        
        if not user_record:
            return jsonify({
                'err_code': 1,
                'err_msg': f'未找到user_id为{user_id}的用户',
                'payload': {}
            })
        
        # 获取标签信息
        tag_list = TagService.list()
        chat_room = TgGroup.query.filter_by(status=TgGroup.StatusType.JOIN_SUCCESS).all()
        chat_room = {r.chat_id: r.name for r in chat_room}
        
        parse_tag_list = TgGroupUserTag.query.filter(TgGroupUserTag.tg_user_id == user_record.id).all()
        tag_ids = [str(p.tag_id) for p in parse_tag_list]
        tag_dict = {t['id']: t['name'] for t in tag_list}
        tag_text = ','.join([tag_dict.get(int(t), '') for t in tag_ids if tag_dict.get(int(t), '')])
        
        user_data = {
            'id': user_record.id,
            'user_id': str(user_record.user_id),
            'username': user_record.username or '',
            'first_name': user_record.nickname or '',
            'last_name': '',
            'nickname': user_record.nickname or '',
            'avatar': user_record.avatar_path or '',
            'phone': '',
            'bio': user_record.desc or '',
            'notes': user_record.remark or '',
            'tags': tag_text,
            'tag_id_list': ','.join(tag_ids) if tag_ids else '',
            'status': 'active',
            'last_seen': user_record.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user_record.updated_at else '',
            'created_at': user_record.created_at.strftime('%Y-%m-%d %H:%M:%S') if user_record.created_at else '',
            'updated_at': user_record.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user_record.updated_at else '',
            'chat_id': user_record.chat_id,
            'group_name': chat_room.get(user_record.chat_id, ''),
            'is_key_focus': bool(user_record.is_key_focus) if hasattr(user_record, 'is_key_focus') else False
        }
        
        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': user_data
        })
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/tg/group_user/key_focus', methods=['GET'])
def tg_group_user_key_focus_list():
    """获取重点关注用户（支持分页）"""
    try:
        # 查询所有重点关注用户
        query = TgGroupUserInfo.query.filter(TgGroupUserInfo.is_key_focus == True)
        
        # 支持搜索参数（与普通列表API保持一致）
        args = request.args
        search_nickname = get_or_exception('search_nickname', args, 'str', '')
        search_desc = get_or_exception('search_desc', args, 'str', '')
        search_group_id = get_or_exception('search_group_id', args, 'str', '')
        group_id = get_or_exception('group_id', args, 'str', '')  # 支持前端发送的group_id参数
        search_username = get_or_exception('search_username', args, 'str', '')
        remark = get_or_exception('remark', args, 'str', '')
        keyword = get_or_exception('keyword', args, 'str', '')
        tag_ids = get_or_exception('tag_ids', args, 'str', '')
        
        # 支持分页参数
        page = get_or_exception('page', args, 'int', 1)
        page_size = get_or_exception('page_size', args, 'int', 20)
        
        # 支持两种群组ID参数格式
        filter_group_id = search_group_id or group_id
        if filter_group_id:
            query = query.filter_by(chat_id=filter_group_id)
        if search_username:
            query = query.filter(TgGroupUserInfo.username.like(f'%{search_username}%'))
        if search_nickname:
            query = query.filter(TgGroupUserInfo.nickname.like(f'%{search_nickname}%'))
        if search_desc:
            query = query.filter(TgGroupUserInfo.desc.like(f'%{search_desc}%'))
        if remark:
            query = query.filter(TgGroupUserInfo.remark.like(f'%{remark}%'))
        if keyword:
            # 关键字搜索：昵称、用户名、备注、用户ID
            keyword_condition = or_(
                TgGroupUserInfo.nickname.like(f'%{keyword}%'),
                TgGroupUserInfo.username.like(f'%{keyword}%'),
                TgGroupUserInfo.remark.like(f'%{keyword}%'),
                TgGroupUserInfo.user_id.like(f'%{keyword}%'),
                TgGroupUserInfo.user_id == keyword  # 精确匹配数字类型的user_id
            )
            query = query.filter(keyword_condition)
        
        # Filter by tags if provided
        if tag_ids:
            tag_id_list = [int(tid.strip()) for tid in tag_ids.split(',') if tid.strip().isdigit()]
            if tag_id_list:
                # Get user IDs that have any of the selected tags
                user_ids_with_tags = db.session.query(TgGroupUserTag.tg_user_id)\
                    .filter(TgGroupUserTag.tag_id.in_(tag_id_list))\
                    .distinct().all()
                if user_ids_with_tags:
                    user_ids_list = [uid[0] for uid in user_ids_with_tags]
                    query = query.filter(TgGroupUserInfo.id.in_(user_ids_list))
                else:
                    # No users match the tag filter, return empty result
                    return jsonify({
                        'err_code': 0,
                        'err_msg': '',
                        'payload': {
                            'data': [],
                            'total': 0,
                            'page': page,
                            'page_size': page_size,
                            'total_pages': 0
                        }
                    })
            else:
                return jsonify({
                    'err_code': 0,
                    'err_msg': '',
                    'payload': {
                        'data': [],
                        'total': 0,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': 0
                    }
                })
        
        # 获取总记录数
        total_records = query.count()
        
        # 应用分页
        offset = (page - 1) * page_size
        group_user_list = query.order_by(TgGroupUserInfo.id.desc()).offset(offset).limit(page_size).all()
        
        # 获取标签和群组信息
        tag_list = TagService.list()
        chat_room = TgGroup.query.filter_by(status=TgGroup.StatusType.JOIN_SUCCESS).all()
        chat_room = {r.chat_id: r.name for r in chat_room}
        
        # 获取标签信息
        group_user_id_list = [group_user.id for group_user in group_user_list]
        parse_tag_list = TgGroupUserTag.query.filter(TgGroupUserTag.tg_user_id.in_(group_user_id_list)).all()
        parse_tag_result = collections.defaultdict(list)
        for p in parse_tag_list:
            parse_tag_result[p.tg_user_id].append(str(p.tag_id))
        tag_dict = {t['id']: t['name'] for t in tag_list}
        
        data = []
        for group_user in group_user_list:
            parse_tag = parse_tag_result.get(group_user.id, [])
            tag_text = ','.join([tag_dict.get(int(t), '') for t in parse_tag if tag_dict.get(int(t), '')])
            
            # 格式化数据以匹配前端TgUser接口
            user_data = {
                'id': group_user.id,
                'user_id': str(group_user.user_id),
                'username': group_user.username or '',
                'first_name': group_user.nickname or '',
                'last_name': '',
                'nickname': group_user.nickname or '',
                'avatar': group_user.avatar_path or '',
                'phone': '',
                'bio': group_user.desc or '',
                'notes': group_user.remark or '',
                'tags': tag_text,
                'tag_id_list': ','.join(parse_tag) if parse_tag else '',
                'status': 'active',
                'last_seen': group_user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if group_user.updated_at else '',
                'created_at': group_user.created_at.strftime('%Y-%m-%d %H:%M:%S') if group_user.created_at else '',
                'updated_at': group_user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if group_user.updated_at else '',
                'chat_id': group_user.chat_id,
                'group_name': chat_room.get(group_user.chat_id, ''),
                'is_key_focus': True  # 这里所有用户都是重点关注的
            }
            data.append(user_data)

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'data': data,
                'total': total_records,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_records + page_size - 1) // page_size
            }
        })
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500

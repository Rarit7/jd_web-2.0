import collections
import datetime
from io import BytesIO
from urllib.parse import quote

import pandas as pd
from flask import request, make_response, session, g, jsonify
from sqlalchemy import func

from jd import db
from jd.models.tg_group import TgGroup
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_tag import TgGroupTag
from jd.models.tg_group_status import TgGroupStatus
from jd.models.tg_group_session import TgGroupSession
from jd.models.tg_account import TgAccount
from jd.services.role_service.role import ROLE_SUPER_ADMIN, RoleService
from jd.services.spider.tg import TgService
from jd.services.tag import TagService
from jd.tasks.telegram.tg_join_group import join_group
from jd.tasks.first.tg_new_joined_history import run_new_group_history_fetch, start_group_history_fetch
from jd.views import get_or_exception, success
from jd.views.api import api
from jd.helpers.permission_helper import get_accessible_tg_user_ids


@api.route('/tg/group/list/json', methods=['GET'])
def tg_group_list_json():
    """返回JSON格式的群组列表数据

    自动应用部门过滤：非超级管理员只能查看本部门关联的TG账户的群组
    """
    args = request.args
    account_id = get_or_exception('account_id', args, 'str', '')
    group_name = get_or_exception('group_name', args, 'str', '')
    chat_id = get_or_exception('chat_id', args, 'str', '')
    group_link = get_or_exception('group_link', args, 'str', '')
    remark = get_or_exception('remark', args, 'str', '')
    tag_ids = get_or_exception('tag_ids', args, 'str', '')

    query = TgGroup.query

    # 部门过滤：非超级管理员只能查看本部门的群组
    if hasattr(g, 'current_user') and g.current_user:
        accessible_tg_user_ids = get_accessible_tg_user_ids(g.current_user)

        # 如果不是None（即不是超级管理员），应用部门过滤
        if accessible_tg_user_ids is not None:
            if accessible_tg_user_ids:
                # 通过TgGroupSession查找这些TG账户相关的群组
                accessible_chat_ids = db.session.query(TgGroupSession.chat_id)\
                    .filter(TgGroupSession.user_id.in_(accessible_tg_user_ids))\
                    .distinct().all()

                if accessible_chat_ids:
                    chat_ids_list = [chat_id[0] for chat_id in accessible_chat_ids]
                    query = query.filter(TgGroup.chat_id.in_(chat_ids_list))
                else:
                    # 部门没有关联任何群组，返回空结果
                    query = query.filter(TgGroup.id == -1)
            else:
                # 部门没有关联任何TG账户，返回空结果
                query = query.filter(TgGroup.id == -1)

    if account_id:
        # 只通过TgGroupSession表找到该账户所在的群组
        # 1. 先从TgAccount获取该账户的user_id
        account = TgAccount.query.filter(TgAccount.id == account_id).first()
        if account and account.user_id:
            # 2. 从TgGroupSession找到该user_id对应的所有chat_id
            session_chat_ids = db.session.query(TgGroupSession.chat_id)\
                .filter(TgGroupSession.user_id == account.user_id)\
                .distinct().all()
            if session_chat_ids:
                chat_ids_list = [chat_id[0] for chat_id in session_chat_ids]
                # 只显示在TgGroupSession中有记录的群组
                query = query.filter(TgGroup.chat_id.in_(chat_ids_list))
            else:
                # 如果该账户没有在TgGroupSession中有记录，返回空结果
                query = query.filter(TgGroup.id == -1)
        else:
            # 账户不存在或没有user_id，返回空结果
            query = query.filter(TgGroup.id == -1)
    if group_name:
        query = query.filter(TgGroup.title.like('%' + group_name + '%'))
    if chat_id:
        query = query.filter(TgGroup.chat_id.like('%' + chat_id + '%'))
    if group_link:
        query = query.filter(TgGroup.name.like('%' + group_link + '%'))
    if remark:
        query = query.filter(TgGroup.remark.like('%' + remark + '%'))
    
    # Filter by tags if provided
    groups = []
    if tag_ids:
        tag_id_list = [int(tid.strip()) for tid in tag_ids.split(',') if tid.strip().isdigit()]
        if tag_id_list:
            # Get group IDs that have any of the selected tags
            group_ids_with_tags = db.session.query(TgGroupTag.group_id)\
                .filter(TgGroupTag.tag_id.in_(tag_id_list))\
                .distinct().all()
            if group_ids_with_tags:
                group_ids_list = [gid[0] for gid in group_ids_with_tags]
                query = query.filter(TgGroup.id.in_(group_ids_list))
                groups = query.order_by(TgGroup.id.desc()).all()
            else:
                # No groups match the tag filter, return empty result
                groups = []
        else:
            groups = []
    else:
        groups = query.order_by(TgGroup.id.desc()).all()
    tag_list = TagService.list()
    
    if not groups:
        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'data': [],
                'tag_list': tag_list,
                'default_account_id': account_id,
                'default_group_name': group_name,
                'default_chat_id': chat_id,
                'default_group_link': group_link,
                'default_remark': remark,
                'role_ids': RoleService.user_roles(session.get('current_user_id', 1))
            }
        })
    
    group_id_list = [grp.id for grp in groups]
    parse_tag_list = TgGroupTag.query.filter(TgGroupTag.group_id.in_(group_id_list)).all()
    parse_tag_result = collections.defaultdict(list)
    for p in parse_tag_list:
        parse_tag_result[p.group_id].append(str(p.tag_id))
    tag_dict = {t['id']: t['name'] for t in tag_list}
    chat_postal_time = TgGroupChatHistory.query.with_entities(TgGroupChatHistory.chat_id,
                                                              func.max(TgGroupChatHistory.postal_time).label(
                                                                  'latest_postal_time')).group_by(
        TgGroupChatHistory.chat_id).all()
    chat_postal_time_dict = {t.chat_id: t.latest_postal_time for t in chat_postal_time}

    # Get group status data (members and conversation count)
    chat_id_list = [grp.chat_id for grp in groups]
    group_status = TgGroupStatus.query.filter(TgGroupStatus.chat_id.in_(chat_id_list)).all()
    group_status_dict = {gs.chat_id: gs for gs in group_status}

    data = []
    no_chat_history_group = []
    for group in groups:
        parse_tag = parse_tag_result.get(group.id, [])
        tag_text = ','.join([tag_dict.get(int(t), '') for t in parse_tag if tag_dict.get(int(t), '')])
        latest_postal_time = chat_postal_time_dict.get(group.chat_id, '')

        # Get status data for this group
        status_data = group_status_dict.get(group.chat_id)
        members_count = status_data.members_now if status_data else 0
        members_increment = (status_data.members_now - status_data.members_previous) if status_data and status_data.members_previous else 0
        records_count = status_data.records_now if status_data else 0
        records_increment = (status_data.records_now - status_data.records_previous) if status_data and status_data.records_previous else 0

        d = {
            'id': group.id,
            'name': group.name,
            'chat_id': group.chat_id,
            'status': TgService.STATUS_MAP[group.status],
            'desc': group.desc,
            'tag': tag_text,
            'tag_id_list': ','.join(parse_tag) if parse_tag else '',
            'created_at': group.created_at.strftime('%Y-%m-%d %H:%M:%S') if group.created_at else '',
            'account_id': group.account_id,
            'photo': group.avatar_path,
            'title': group.title,
            'remark': group.remark,
            'latest_postal_time': latest_postal_time.strftime('%Y-%m-%d %H:%M:%S') if latest_postal_time else '',
            'three_days_ago': 1 if latest_postal_time and latest_postal_time < (
                    datetime.datetime.now() - datetime.timedelta(days=3)) else 0,
            'group_type': group.group_type,
            'members_count': members_count,
            'members_increment': members_increment,
            'records_count': records_count,
            'records_increment': records_increment,
        }
        if not latest_postal_time:
            no_chat_history_group.append(d)
            continue
        data.append(d)
    # 按最后发言时间降序排列（最新的在前面），没有发言记录的放在最后
    data = sorted(data, key=lambda x: x['latest_postal_time'] if x['latest_postal_time'] else '', reverse=True)
    data.extend(no_chat_history_group)

    return jsonify({
        'err_code': 0,
        'err_msg': '',
        'payload': {
            'data': data,
            'tag_list': tag_list,
            'default_account_id': account_id,
            'default_group_name': group_name,
            'default_chat_id': chat_id,
            'default_group_link': group_link,
            'default_remark': remark,
            'role_ids': RoleService.user_roles(session.get('current_user_id', 1))
        }
    })


@api.route('/tg/group/list', methods=['GET'])
def tg_group_list_legacy():
    # Return error message directing to use the JSON endpoint
    return jsonify({
        'err_code': 400,
        'err_msg': 'Please use /api/tg/group/list/json endpoint instead',
        'payload': {}
    }), 400


@api.route('/tg/group/delete')
def tg_group_delete():
    group_id = get_or_exception('group_id', request.args, 'int')
    TgGroup.query.filter(TgGroup.id == group_id).delete()
    db.session.commit()
    return success({'message': '群组删除成功'})


def extract_group_name_from_url(input_text):
    """
    从Telegram链接中提取群组名称或邀请hash
    支持格式:
    - https://t.me/+invitehash (私有群组邀请链接)
    - t.me/+invitehash (不带协议的私有邀请链接)
    - +invitehash (只有邀请hash)
    - https://t.me/joinchat/invitehash (旧格式私有邀请链接)
    - https://t.me/groupname (公开群组链接)
    - t.me/groupname
    - @groupname
    - groupname

    返回:
    - 私有邀请链接: 返回hash部分 (用于ImportChatInviteRequest)
    - 公开群组: 返回群组名称 (用于JoinChannelRequest)
    """
    import re

    # 移除首尾空格
    input_text = input_text.strip()

    # 1. 处理私有群组邀请链接: https://t.me/+xxx 或 t.me/+xxx
    if 't.me/+' in input_text:
        # 提取 + 号后面的hash部分
        hash_match = re.search(r't\.me/\+([a-zA-Z0-9_-]+)', input_text)
        if hash_match:
            return hash_match.group(1)  # 返回纯hash,不带+号

    # 2. 处理只有邀请hash的情况: +invitehash
    if input_text.startswith('+') and len(input_text) > 1:
        # 移除开头的 + 号，返回纯hash
        return input_text[1:]

    # 3. 处理旧格式私有邀请链接: https://t.me/joinchat/xxx
    if 't.me/joinchat/' in input_text:
        joinchat_match = re.search(r't\.me/joinchat/([a-zA-Z0-9_-]+)', input_text)
        if joinchat_match:
            return joinchat_match.group(1)

    # 4. 处理公开群组链接: https://t.me/groupname 或 t.me/groupname
    telegram_url_pattern = r'(?:https?://)?t\.me/([a-zA-Z0-9_]+)'
    match = re.match(telegram_url_pattern, input_text)
    if match:
        return match.group(1)

    # 5. 处理 @groupname 格式
    if input_text.startswith('@'):
        return input_text[1:]  # 移除 @ 符号

    # 6. 如果都不匹配，直接返回原文本（假设是群组名称或hash）
    return input_text

@api.route('/tg/group/add', methods=['POST'])
def tg_group_add():
    name = get_or_exception('name', request.form, 'str')
    session_name = get_or_exception('session_name', request.form, 'str', 'web')
    name_list = name.split(',')
    
    for name in name_list:
        # 提取群组名称（处理链接格式）
        group_name = extract_group_name_from_url(name)
        
        if not TgGroup.query.filter(TgGroup.name == group_name).first():
            db.session.add(TgGroup(name=group_name))
            db.session.flush()
        TgGroup.query.filter_by(name=group_name).update(
            {'status': TgGroup.StatusType.JOIN_ONGOING})
        db.session.commit()
        join_group.delay(group_name, session_name, session.get('current_user_id'))

    return success({'message': '群组添加成功'})


@api.route('/tg/group/tag/update', methods=['POST'])
def tg_group_tag_update():
    args = request.json
    group_id = get_or_exception('group_id', args, 'int')
    tag_id_list = get_or_exception('tag_id_list', args, 'str', '')
    remark = get_or_exception('remark', args, 'str', '')
    if tag_id_list:
        tag_id_list = tag_id_list.split(',')
        tag_id_list = [int(t) for t in tag_id_list]
    TgGroupTag.query.filter(TgGroupTag.group_id == group_id).delete()
    for tag_id in tag_id_list:
        obj = TgGroupTag(group_id=group_id, tag_id=tag_id)
        db.session.add(obj)
    TgGroup.query.filter(TgGroup.id == group_id).update({
        'remark': remark
    })
    db.session.commit()
    return success()


@api.route('/tg/group/fetch-history', methods=['POST'])
def tg_group_fetch_history():
    """Trigger history fetching task for a specific group"""
    args = request.json
    group_name = get_or_exception('group_name', args, 'str')
    chat_id = get_or_exception('chat_id', args, 'int', 0)
    
    # 直接调用task层的函数，包含完整的jobqueue管理逻辑
    result = start_group_history_fetch(group_name, chat_id)
    
    # 如果有错误，直接返回结果
    if result.get('err_code') != 0:
        return jsonify(result)
    
    # 成功情况，使用success格式返回
    return success(result.get('payload', {}), result.get('err_code', 0), result.get('err_msg', ''))


@api.route('/tg/group/download', methods=['GET'])
def tg_group_download():
    args = request.args
    account_id = get_or_exception('account_id', args, 'str', '')
    group_name = get_or_exception('group_name', args, 'str', '')
    chat_id = get_or_exception('chat_id', args, 'str', '')
    group_link = get_or_exception('group_link', args, 'str', '')
    remark = get_or_exception('remark', args, 'str', '')
    tag_ids = get_or_exception('tag_ids', args, 'str', '')

    query = TgGroup.query
    if account_id:
        # 只通过TgGroupSession表找到该账户所在的群组
        # 1. 先从TgAccount获取该账户的user_id
        account = TgAccount.query.filter(TgAccount.id == account_id).first()
        if account and account.user_id:
            # 2. 从TgGroupSession找到该user_id对应的所有chat_id
            session_chat_ids = db.session.query(TgGroupSession.chat_id)\
                .filter(TgGroupSession.user_id == account.user_id)\
                .distinct().all()
            if session_chat_ids:
                chat_ids_list = [chat_id[0] for chat_id in session_chat_ids]
                # 只显示在TgGroupSession中有记录的群组
                query = query.filter(TgGroup.chat_id.in_(chat_ids_list))
            else:
                # 如果该账户没有在TgGroupSession中有记录，返回空结果
                query = query.filter(TgGroup.id == -1)
        else:
            # 账户不存在或没有user_id，返回空结果
            query = query.filter(TgGroup.id == -1)
    if group_name:
        query = query.filter(TgGroup.title.like('%' + group_name + '%'))
    if chat_id:
        query = query.filter(TgGroup.chat_id.like('%' + chat_id + '%'))
    if group_link:
        query = query.filter(TgGroup.name.like('%' + group_link + '%'))
    if remark:
        query = query.filter(TgGroup.remark.like('%' + remark + '%'))
    
    # Filter by tags if provided
    groups = []
    if tag_ids:
        tag_id_list = [int(tid.strip()) for tid in tag_ids.split(',') if tid.strip().isdigit()]
        if tag_id_list:
            # Get group IDs that have any of the selected tags
            group_ids_with_tags = db.session.query(TgGroupTag.group_id)\
                .filter(TgGroupTag.tag_id.in_(tag_id_list))\
                .distinct().all()
            if group_ids_with_tags:
                group_ids_list = [gid[0] for gid in group_ids_with_tags]
                query = query.filter(TgGroup.id.in_(group_ids_list))
                groups = query.order_by(TgGroup.id.desc()).all()
            else:
                groups = []
        else:
            groups = []
    else:
        groups = query.order_by(TgGroup.id.desc()).all()
    tag_list = TagService.list()
    if not groups:
        # Return empty file for download
        output = BytesIO()
        df = pd.DataFrame([], columns=['群组名称', '账户id', '链接', '群组id', '标签', '类型', '备注', '最新时间', '描述'])
        writer = pd.ExcelWriter(output, engine='openpyxl')
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.close()
        output.seek(0)
        response = make_response(output.getvalue())
        file_name = 'group.xlsx'
        response.headers["Content-Disposition"] = f"attachment; filename={quote(file_name)}; filename*=utf-8''{quote(file_name)}"
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response
    group_id_list = [grp.id for grp in groups]
    parse_tag_list = TgGroupTag.query.filter(TgGroupTag.group_id.in_(group_id_list)).all()
    parse_tag_result = collections.defaultdict(list)
    for p in parse_tag_list:
        parse_tag_result[p.group_id].append(str(p.tag_id))
    tag_dict = {t['id']: t['name'] for t in tag_list}
    chat_postal_time = TgGroupChatHistory.query.with_entities(TgGroupChatHistory.chat_id,
                                                              func.max(TgGroupChatHistory.postal_time).label(
                                                                  'latest_postal_time')).group_by(
        TgGroupChatHistory.chat_id).all()
    chat_postal_time_dict = {t.chat_id: t.latest_postal_time for t in chat_postal_time}

    data = []
    no_chat_history_group = []
    for group in groups:
        parse_tag = parse_tag_result.get(group.id, [])
        tag_text = ','.join([tag_dict.get(int(t), '') for t in parse_tag if tag_dict.get(int(t), '')])
        latest_postal_time = chat_postal_time_dict.get(group.chat_id, '')
        d = {
            'id': group.id,
            'name': group.name,
            'chat_id': group.chat_id,
            'status': TgService.STATUS_MAP[group.status],
            'desc': group.desc,
            'tag': tag_text,
            'tag_id_list': ','.join(parse_tag) if parse_tag else '',
            'created_at': group.created_at.strftime('%Y-%m-%d %H:%M:%S') if group.created_at else '',
            'account_id': group.account_id,
            'photo': group.avatar_path,
            'title': group.title,
            'remark': group.remark,
            'latest_postal_time': latest_postal_time.strftime('%Y-%m-%d %H:%M:%S') if latest_postal_time else '',
            'three_days_ago': 1 if latest_postal_time and latest_postal_time < (
                    datetime.datetime.now() - datetime.timedelta(days=3)) else 0,
            'group_type': group.group_type,
        }
        if not latest_postal_time:
            no_chat_history_group.append(d)
            continue
        data.append(d)
    # 按最后发言时间降序排列（最新的在前面），没有发言记录的放在最后
    data = sorted(data, key=lambda x: x['latest_postal_time'] if x['latest_postal_time'] else '', reverse=True)
    data.extend(no_chat_history_group)

    result = []
    for d in data:
        result.append({
            '群组名称': d['title'],
            '账户id': d['account_id'],
            '链接': d['name'],
            '群组id': d['chat_id'],
            '标签': d['tag'],
            '类型': '群组' if d['group_type'] == 1 else '频道',
            '备注': d['remark'],
            '最新时间': d['latest_postal_time'],
            '描述': d['desc'],
        })

    columns = ['群组名称', '账户id', '链接', '群组id', '标签', '类型', '备注', '最新时间', '描述']
    df = pd.DataFrame(result, columns=columns)
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    # 设置响应头
    output.seek(0)
    response = make_response(output.getvalue())
    file_name = 'group.xlsx'
    response.headers[
        "Content-Disposition"] = f"attachment; filename={quote(file_name)}; filename*=utf-8''{quote(file_name)}"
    response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return response

from flask import request, jsonify
from jd.views.api import api
from jd.models.tg_user_info_change import TgUserInfoChange
from jd.models.tg_group_info_change import TgGroupInfoChange
from jd import db
from datetime import datetime


@api.route('/change_record/user', methods=['GET'])
def get_user_change_records():
    """获取用户信息变动记录"""
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        user_id = request.args.get('user_id', '', type=str)
        change_type = request.args.get('change_type', 0, type=int)
        
        # 构建查询
        query = TgUserInfoChange.query
        
        # 按用户ID过滤
        if user_id:
            query = query.filter(TgUserInfoChange.user_id.like(f'%{user_id}%'))
        
        # 按变动类型过滤
        if change_type > 0:
            query = query.filter(TgUserInfoChange.changed_fields == change_type)
        
        # 分页查询 - 按时间降序，id降序确保最新记录在最前面
        pagination = query.order_by(
            TgUserInfoChange.update_time.desc(),
            TgUserInfoChange.id.desc()
        ).paginate(
            page=page, 
            per_page=size, 
            error_out=False
        )
        
        # 变动类型映射
        change_type_map = {
            TgUserInfoChange.ChangedFieldType.DISPLAY_NAME: '显示名称',
            TgUserInfoChange.ChangedFieldType.USERNAME: '用户名',
            TgUserInfoChange.ChangedFieldType.AVATAR: '头像',
            TgUserInfoChange.ChangedFieldType.BIOGRAPHY: '个人简介'
        }
        
        # 格式化数据
        items = []
        for record in pagination.items:
            items.append({
                'id': record.id,
                'user_id': record.user_id,
                'changed_fields': record.changed_fields,
                'change_type_text': change_type_map.get(record.changed_fields, '未知'),
                'original_value': record.original_value,
                'new_value': record.new_value,
                'update_time': record.update_time.strftime('%Y-%m-%d %H:%M:%S') if record.update_time else ''
            })
        
        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'items': items,
                'pagination': {
                    'page': page,
                    'size': size,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': f'获取用户变动记录失败: {str(e)}',
            'payload': {}
        }), 500


@api.route('/change_record/group', methods=['GET'])  
def get_group_change_records():
    """获取群组信息变动记录"""
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        group_id = request.args.get('group_id', '', type=str)
        change_type = request.args.get('change_type', 0, type=int)
        
        # 构建查询 - 先检查表是否存在
        try:
            query = TgGroupInfoChange.query
        except Exception:
            # 如果表不存在，返回空数据
            return jsonify({
                'err_code': 0,
                'err_msg': '',
                'payload': {
                    'items': [],
                    'pagination': {
                        'page': page,
                        'size': size,
                        'total': 0,
                        'pages': 0
                    }
                }
            })
        
        # 按群组ID过滤
        if group_id:
            query = query.filter(TgGroupInfoChange.chat_id.like(f'%{group_id}%'))
        
        # 按变动类型过滤
        if change_type > 0:
            query = query.filter(TgGroupInfoChange.changed_fields == change_type)
        
        # 分页查询 - 按时间降序，id降序确保最新记录在最前面
        pagination = query.order_by(
            TgGroupInfoChange.update_time.desc(),
            TgGroupInfoChange.id.desc()
        ).paginate(
            page=page, 
            per_page=size, 
            error_out=False
        )
        
        # 变动类型映射
        change_type_map = {
            TgGroupInfoChange.ChangedFieldType.DISPLAY_NAME: '群组名称',
            TgGroupInfoChange.ChangedFieldType.GROUP_NAME_INVITE_LINK: '群组名/邀请链接',
            TgGroupInfoChange.ChangedFieldType.GROUP_AVATAR: '群组头像',
            TgGroupInfoChange.ChangedFieldType.GROUP_DESCRIPTION: '群组简介'
        }
        
        # 格式化数据
        items = []
        for record in pagination.items:
            items.append({
                'id': record.id,
                'group_id': record.chat_id,
                'changed_fields': record.changed_fields,
                'change_type_text': change_type_map.get(record.changed_fields, '未知'),
                'original_value': record.original_value,
                'new_value': record.new_value,
                'update_time': record.update_time.strftime('%Y-%m-%d %H:%M:%S') if record.update_time else ''
            })
        
        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'items': items,
                'pagination': {
                    'page': page,
                    'size': size,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': f'获取群组变动记录失败: {str(e)}',
            'payload': {}
        }), 500


@api.route('/change_record/stats', methods=['GET'])
def get_change_stats():
    """获取变动统计信息"""
    try:
        # 用户变动统计
        user_stats = db.session.query(
            TgUserInfoChange.changed_fields,
            db.func.count(TgUserInfoChange.id).label('count')
        ).group_by(TgUserInfoChange.changed_fields).all()
        
        user_change_map = {
            TgUserInfoChange.ChangedFieldType.DISPLAY_NAME: '显示名称',
            TgUserInfoChange.ChangedFieldType.USERNAME: '用户名', 
            TgUserInfoChange.ChangedFieldType.AVATAR: '头像',
            TgUserInfoChange.ChangedFieldType.BIOGRAPHY: '个人简介'
        }
        
        user_stats_data = []
        for field_type, count in user_stats:
            user_stats_data.append({
                'type': field_type,
                'type_text': user_change_map.get(field_type, '未知'),
                'count': count
            })
        
        # 群组变动统计（如果表存在）
        group_stats_data = []
        try:
            group_stats = db.session.query(
                TgGroupInfoChange.changed_fields,
                db.func.count(TgGroupInfoChange.id).label('count')
            ).group_by(TgGroupInfoChange.changed_fields).all()
            
            group_change_map = {
                1: '群组名称',
                2: '群组用户名', 
                3: '群组头像',
                4: '群组简介'
            }
            
            for field_type, count in group_stats:
                group_stats_data.append({
                    'type': field_type,
                    'type_text': group_change_map.get(field_type, '未知'),
                    'count': count
                })
        except Exception:
            pass
        
        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'user_stats': user_stats_data,
                'group_stats': group_stats_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'err_code': 1,
            'err_msg': f'获取统计信息失败: {str(e)}',
            'payload': {}
        }), 500
"""
Telegram私人聊天API端点
"""
import logging
from flask import request, jsonify
from sqlalchemy import func, and_, or_

from jd import db
from jd.models.tg_person_chat_history import TgPersonChatHistory
from jd.models.tg_account import TgAccount
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.views import get_or_exception
from jd.views.api import api

logger = logging.getLogger(__name__)


@api.route('/tg/private_chat/history/json', methods=['GET'])
def get_private_chat_history():
    """获取私聊记录（JSON格式）"""
    try:
        args = request.args
        page = get_or_exception('page', args, 'int', 1)
        page_size = get_or_exception('page_size', args, 'int', 20)
        search_content = get_or_exception('search_content', args, 'str', '')
        start_date = get_or_exception('start_date', args, 'str', '')
        end_date = get_or_exception('end_date', args, 'str', '')

        # 私聊参数
        owner_user_id = get_or_exception('owner_user_id', args, 'str', '')
        owner_session_name = get_or_exception('owner_session_name', args, 'str', '')
        peer_user_id = get_or_exception('peer_user_id', args, 'str', '')

        # 验证必要参数
        if not owner_user_id or not peer_user_id:
            return jsonify({
                'err_code': 1,
                'err_msg': '缺少必要参数：owner_user_id 和 peer_user_id',
                'payload': {}
            }), 400

        # 构建查询
        query = TgPersonChatHistory.query.filter(
            TgPersonChatHistory.owner_user_id == owner_user_id,
            TgPersonChatHistory.peer_user_id == peer_user_id
        )

        # Session名称过滤（如果提供）
        if owner_session_name:
            query = query.filter(TgPersonChatHistory.owner_session_name == owner_session_name)

        # 时间范围过滤
        if start_date and end_date:
            f_start_date = start_date + ' 00:00:00'
            f_end_date = end_date + ' 23:59:59'
            query = query.filter(TgPersonChatHistory.postal_time.between(f_start_date, f_end_date))

        # 内容搜索
        if search_content:
            query = query.filter(TgPersonChatHistory.message.like(f'%{search_content}%'))

        # 获取总数
        total_records = query.count()
        total_pages = (total_records + page_size - 1) // page_size

        # 分页和排序
        query = query.order_by(TgPersonChatHistory.postal_time.asc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        # 执行查询
        messages = query.all()

        # 获取己方和对方的用户信息（用于头像）
        owner_account = TgAccount.query.filter_by(user_id=owner_user_id).first()
        peer_user_info = TgGroupUserInfo.query.filter_by(user_id=peer_user_id).first()

        # 尝试从tg_group_user_info表获取owner的头像信息
        owner_user_info = TgGroupUserInfo.query.filter_by(user_id=owner_user_id).first()

        # 构建用户信息映射
        user_info_map = {}
        if owner_account:
            # 优先使用tg_group_user_info中的头像,如果没有则为空
            owner_avatar = ''
            if owner_user_info:
                owner_avatar = owner_user_info.avatar_path or owner_user_info.photo or ''

            user_info_map[owner_user_id] = {
                'nickname': owner_account.nickname,
                'username': owner_account.username,
                'avatar': owner_avatar
            }
        if peer_user_info:
            user_info_map[peer_user_id] = {
                'nickname': peer_user_info.nickname,
                'username': peer_user_info.username,
                'avatar': peer_user_info.avatar_path or peer_user_info.photo or ''
            }

        # 转换为前端格式
        data = []
        for msg in messages:
            # 获取发送方的实际user_id
            sender_user_id = msg.get_sender_user_id()
            sender_info = msg.get_sender_info()

            # 从映射中获取用户信息
            user_info = user_info_map.get(sender_user_id, {})

            data.append({
                'id': msg.id,
                'chat_id': msg.chat_id,
                'message_id': msg.message_id,
                'message': msg.message,
                'nickname': sender_info.get('nickname', '') or user_info.get('nickname', ''),
                'username': sender_info.get('username', '') or user_info.get('username', ''),
                'user_id': sender_user_id,
                'user_avatar': user_info.get('avatar', ''),
                'is_key_focus': False,
                'postal_time': msg.postal_time.strftime('%Y-%m-%d %H:%M:%S') if msg.postal_time else '',
                'photo_paths': [msg.photo_path] if msg.photo_path else [],
                'document_paths': [msg.document_path] if msg.document_path else [],
                'documents': [],  # TODO: 增强文档信息
                'reply_to_msg_id': int(msg.reply_to_msg_id) if msg.reply_to_msg_id and msg.reply_to_msg_id.isdigit() else 0,
            })

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'data': data,
                'total_pages': total_pages,
                'current_page': page,
                'total_records': total_records
            }
        })

    except Exception as e:
        logger.error(f'获取私聊记录失败: {e}', exc_info=True)
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500


@api.route('/tg/private_chat/by_user/<owner_user_id>', methods=['GET'])
def get_private_chat_conversations(owner_user_id):
    """获取指定用户的所有私聊对话列表"""
    try:
        # 验证参数
        if not owner_user_id:
            return jsonify({
                'err_code': 1,
                'err_msg': '用户ID不能为空',
                'payload': {}
            }), 400

        # 查询该用户的所有私聊对话，按最后消息时间分组
        conversations_query = db.session.query(
            TgPersonChatHistory.peer_user_id,
            func.count(TgPersonChatHistory.id).label('message_count'),
            func.max(TgPersonChatHistory.postal_time).label('last_message_time')
        ).filter(
            TgPersonChatHistory.owner_user_id == owner_user_id
        ).group_by(
            TgPersonChatHistory.peer_user_id
        ).order_by(
            func.max(TgPersonChatHistory.postal_time).desc()
        )

        results = conversations_query.all()

        # 获取对方用户信息
        peer_user_ids = [r.peer_user_id for r in results]
        peer_users = {}
        if peer_user_ids:
            user_infos = TgGroupUserInfo.query.filter(
                TgGroupUserInfo.user_id.in_(peer_user_ids)
            ).all()
            for user in user_infos:
                if user.user_id not in peer_users:
                    peer_users[user.user_id] = user

        # 构建对话列表
        conversations = []
        for r in results:
            peer_user = peer_users.get(r.peer_user_id)
            # 安全地获取头像路径
            peer_avatar = ''
            if peer_user:
                peer_avatar = (peer_user.avatar_path or peer_user.photo or '').strip()

            conversations.append({
                'peer_user_id': r.peer_user_id,
                'peer_nickname': peer_user.nickname if peer_user else '',
                'peer_username': peer_user.username if peer_user else '',
                'peer_avatar': peer_avatar,
                'message_count': r.message_count,
                'last_message_time': r.last_message_time.strftime('%Y-%m-%d %H:%M:%S') if r.last_message_time else ''
            })

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'conversations': conversations,
                'total': len(conversations)
            }
        })

    except Exception as e:
        logger.error(f'获取私聊对话列表失败: {e}', exc_info=True)
        return jsonify({
            'err_code': 1,
            'err_msg': str(e),
            'payload': {}
        }), 500

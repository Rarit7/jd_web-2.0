from flask import jsonify
from sqlalchemy import func, distinct

from jd import db
from jd.views.api import api
from jd.models.tg_group import TgGroup
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.black_keyword import BlackKeyword


@api.route('/user/no_permission')
def user_no_permission():
    return jsonify({
        'err_code': 40103,
        'err_msg': '无权限访问',
        'payload': {}
    }), 403


@api.route('/dashboard/statistics')
def dashboard_statistics():
    """获取首页统计数据"""
    try:
        # TG群组数（join_success的群组）
        group_count = db.session.query(TgGroup).filter(
            TgGroup.status == TgGroup.StatusType.JOIN_SUCCESS
        ).count()
        
        # TG用户数（tggroupuserinfo userid去重）
        user_count = db.session.query(func.count(distinct(TgGroupUserInfo.user_id))).scalar()
        
        # TG聊天记录总数（tggroupchathistory总数）
        message_count = db.session.query(TgGroupChatHistory).count()
        
        # 黑词记录数（正常状态的黑词）
        blackword_count = db.session.query(BlackKeyword).filter(
            BlackKeyword.is_delete == BlackKeyword.DeleteType.NORMAL
        ).count()
        
        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'group_count': group_count or 0,
                'user_count': user_count or 0,
                'message_count': message_count or 0,
                'blackword_count': blackword_count or 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'err_code': 500,
            'err_msg': f'获取统计数据失败: {str(e)}',
            'payload': {}
        }), 500
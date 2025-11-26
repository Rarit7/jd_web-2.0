"""
广告追踪高价值信息 API 端点
"""
import logging
from datetime import datetime
from flask import request, jsonify

from jd import db
from jd.models.ad_tracking_high_value_message import AdTrackingHighValueMessage
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.views.api import api

logger = logging.getLogger(__name__)


@api.route('/ad-tracking/high-value-messages', methods=['GET'])
def get_high_value_messages():
    """
    获取高价值信息列表

    Query Parameters:
        - page: 页码，默认1
        - page_size: 每页记录数，默认10
        - user_id: 用户ID过滤
        - chat_id: 群组ID过滤
        - is_high_priority: 是否高优先级（1/0）
        - start_date: 开始日期（YYYY-MM-DD）
        - end_date: 结束日期（YYYY-MM-DD）
        - search: 搜索关键词（搜索content和ai_judgment）
        - sort_by: 排序字段（importance_score, publish_time, created_at），默认created_at
        - sort_order: 排序方向（asc, desc），默认desc
    """
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        page_size = min(page_size, 100)  # 限制最大每页100条

        # 获取过滤参数
        user_id = request.args.get('user_id')
        chat_id = request.args.get('chat_id')
        is_high_priority = request.args.get('is_high_priority', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')

        # 获取排序参数
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # 构建查询
        query = AdTrackingHighValueMessage.query

        # 应用过滤条件
        if user_id:
            query = query.filter(AdTrackingHighValueMessage.user_id == user_id)

        if chat_id:
            query = query.filter(AdTrackingHighValueMessage.chat_id == chat_id)

        if is_high_priority is not None:
            query = query.filter(AdTrackingHighValueMessage.is_high_priority == is_high_priority)

        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(AdTrackingHighValueMessage.publish_time >= start_datetime)

        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(AdTrackingHighValueMessage.publish_time <= end_datetime)

        if search:
            search_pattern = f'%{search}%'
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    AdTrackingHighValueMessage.content.like(search_pattern),
                    AdTrackingHighValueMessage.ai_judgment.like(search_pattern)
                )
            )

        # 应用排序
        if sort_by == 'importance_score':
            order_col = AdTrackingHighValueMessage.importance_score
        elif sort_by == 'publish_time':
            order_col = AdTrackingHighValueMessage.publish_time
        else:
            order_col = AdTrackingHighValueMessage.created_at

        from sqlalchemy import desc, asc
        if sort_order == 'asc':
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))

        # 获取总数
        total = query.count()

        # 获取分页数据
        offset = (page - 1) * page_size
        messages = query.offset(offset).limit(page_size).all()

        # 转换为字典
        data = [msg.to_dict() for msg in messages]

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'data': data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        })

    except Exception as e:
        logger.error(f'获取高价值信息列表失败: {e}', exc_info=True)
        return jsonify({
            'err_code': 500,
            'err_msg': f'获取高价值信息列表失败: {str(e)}',
            'payload': None
        }), 500


@api.route('/ad-tracking/high-value-messages/<int:message_id>', methods=['GET'])
def get_high_value_message(message_id):
    """
    获取单个高价值信息详情

    Path Parameters:
        - message_id: 高价值信息ID
    """
    try:
        message = AdTrackingHighValueMessage.query.get(message_id)
        if not message:
            return jsonify({
                'err_code': 404,
                'err_msg': '高价值信息不存在',
                'payload': None
            }), 404

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {'data': message.to_dict()}
        })

    except Exception as e:
        logger.error(f'获取高价值信息详情失败: {e}', exc_info=True)
        return jsonify({
            'err_code': 500,
            'err_msg': f'获取高价值信息详情失败: {str(e)}',
            'payload': None
        }), 500


@api.route('/ad-tracking/high-value-messages', methods=['POST'])
def create_high_value_message():
    """
    创建高价值信息记录

    Request Body:
        - chat_history_id: (必须) 关联的tg_group_chat_history记录ID
        - user_id: 用户ID
        - username: 用户名
        - chat_id: 群组ID
        - group_name: 群组名称
        - content: (必须) 聊天记录内容
        - images: 聊天图片列表（JSON数组）
        - ai_judgment: 大模型判断结果
        - publish_time: 消息发布时间（ISO 8601格式）
        - importance_score: 重要程度评分（0-100）
        - is_high_priority: 是否为高优先级（true/false）
        - remark: 备注说明
    """
    try:
        data = request.get_json() or {}

        # 验证必填字段
        if not data.get('chat_history_id'):
            return jsonify({
                'err_code': 400,
                'err_msg': 'chat_history_id 是必填项',
                'payload': None
            }), 400

        if not data.get('content'):
            return jsonify({
                'err_code': 400,
                'err_msg': 'content 是必填项',
                'payload': None
            }), 400

        # 检查chat_history_id是否存在
        chat_history = TgGroupChatHistory.query.get(data.get('chat_history_id'))
        if not chat_history:
            return jsonify({
                'err_code': 404,
                'err_msg': '关联的聊天记录不存在',
                'payload': None
            }), 404

        # 创建记录
        message = AdTrackingHighValueMessage(
            chat_history_id=data.get('chat_history_id'),
            user_id=data.get('user_id'),
            username=data.get('username'),
            chat_id=data.get('chat_id'),
            group_name=data.get('group_name'),
            content=data.get('content'),
            images=data.get('images'),
            ai_judgment=data.get('ai_judgment'),
            publish_time=datetime.fromisoformat(data['publish_time']) if data.get('publish_time') else None,
            importance_score=float(data['importance_score']) if data.get('importance_score') else None,
            is_high_priority=bool(data.get('is_high_priority', False)),
            remark=data.get('remark')
        )

        db.session.add(message)
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {'data': message.to_dict()}
        }), 201

    except ValueError as e:
        logger.error(f'创建高价值信息失败（参数错误）: {e}', exc_info=True)
        return jsonify({
            'err_code': 400,
            'err_msg': f'参数错误: {str(e)}',
            'payload': None
        }), 400
    except Exception as e:
        logger.error(f'创建高价值信息失败: {e}', exc_info=True)
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'创建高价值信息失败: {str(e)}',
            'payload': None
        }), 500


@api.route('/ad-tracking/high-value-messages/<int:message_id>', methods=['PUT'])
def update_high_value_message(message_id):
    """
    更新高价值信息记录

    Path Parameters:
        - message_id: 高价值信息ID

    Request Body:
        - user_id: 用户ID
        - username: 用户名
        - chat_id: 群组ID
        - group_name: 群组名称
        - content: 聊天记录内容
        - images: 聊天图片列表
        - ai_judgment: 大模型判断结果
        - publish_time: 消息发布时间
        - importance_score: 重要程度评分
        - is_high_priority: 是否为高优先级
        - remark: 备注说明
    """
    try:
        message = AdTrackingHighValueMessage.query.get(message_id)
        if not message:
            return jsonify({
                'err_code': 404,
                'err_msg': '高价值信息不存在',
                'payload': None
            }), 404

        data = request.get_json() or {}

        # 更新字段
        if 'user_id' in data:
            message.user_id = data['user_id']
        if 'username' in data:
            message.username = data['username']
        if 'chat_id' in data:
            message.chat_id = data['chat_id']
        if 'group_name' in data:
            message.group_name = data['group_name']
        if 'content' in data:
            message.content = data['content']
        if 'images' in data:
            message.images = data['images']
        if 'ai_judgment' in data:
            message.ai_judgment = data['ai_judgment']
        if 'publish_time' in data and data['publish_time']:
            message.publish_time = datetime.fromisoformat(data['publish_time'])
        if 'importance_score' in data and data['importance_score'] is not None:
            message.importance_score = float(data['importance_score'])
        if 'is_high_priority' in data:
            message.is_high_priority = bool(data['is_high_priority'])
        if 'remark' in data:
            message.remark = data['remark']

        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '',
            'payload': {'data': message.to_dict()}
        })

    except ValueError as e:
        logger.error(f'更新高价值信息失败（参数错误）: {e}', exc_info=True)
        return jsonify({
            'err_code': 400,
            'err_msg': f'参数错误: {str(e)}',
            'payload': None
        }), 400
    except Exception as e:
        logger.error(f'更新高价值信息失败: {e}', exc_info=True)
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'更新高价值信息失败: {str(e)}',
            'payload': None
        }), 500


@api.route('/ad-tracking/high-value-messages/<int:message_id>', methods=['DELETE'])
def delete_high_value_message(message_id):
    """
    删除高价值信息记录

    Path Parameters:
        - message_id: 高价值信息ID
    """
    try:
        message = AdTrackingHighValueMessage.query.get(message_id)
        if not message:
            return jsonify({
                'err_code': 404,
                'err_msg': '高价值信息不存在',
                'payload': None
            }), 404

        db.session.delete(message)
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'err_msg': '删除成功',
            'payload': None
        })

    except Exception as e:
        logger.error(f'删除高价值信息失败: {e}', exc_info=True)
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'删除高价值信息失败: {str(e)}',
            'payload': None
        }), 500

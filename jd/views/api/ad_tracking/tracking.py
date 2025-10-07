"""
广告追踪 API 端点
"""
import logging
from datetime import datetime
from flask import request, jsonify
from sqlalchemy import func, and_, or_, desc

from jd import db
from jd.models.ad_tracking import AdTracking
from jd.models.ad_tracking_tags import AdTrackingTags
from jd.models.tg_group import TgGroup
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.views.api import api

logger = logging.getLogger(__name__)


@api.route('/ad-tracking/list', methods=['GET'])
def get_ad_tracking_list():
    """
    获取广告追踪列表

    Query Parameters:
        - page: 页码，默认1
        - page_size: 每页记录数，默认20
        - content_type: 内容类型过滤
        - user_id: 用户ID过滤
        - chat_id: 群组ID过滤
        - start_date: 开始日期（YYYY-MM-DD）
        - end_date: 结束日期（YYYY-MM-DD）
        - search: 搜索关键词（搜索content和normalized_content）
        - sort_by: 排序字段（first_seen, last_seen, occurrence_count），默认last_seen
        - sort_order: 排序方向（asc, desc），默认desc
    """
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        page_size = min(page_size, 100)  # 限制最大每页100条

        # 获取过滤参数
        content_type = request.args.get('content_type')
        user_id = request.args.get('user_id')
        chat_id = request.args.get('chat_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')
        source_type = request.args.get('source_type')

        # 获取排序参数
        sort_by = request.args.get('sort_by', 'last_seen')
        sort_order = request.args.get('sort_order', 'desc')

        # 构建查询
        query = AdTracking.query

        # 应用过滤条件
        if content_type:
            query = query.filter(AdTracking.content_type == content_type)

        if user_id:
            query = query.filter(AdTracking.user_id == user_id)

        if chat_id:
            query = query.filter(AdTracking.chat_id == chat_id)

        if source_type:
            query = query.filter(AdTracking.source_type == source_type)

        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(AdTracking.first_seen >= start_datetime)

        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(AdTracking.first_seen <= end_datetime)

        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                or_(
                    AdTracking.content.like(search_pattern),
                    AdTracking.normalized_content.like(search_pattern)
                )
            )

        # 应用排序
        if sort_by == 'first_seen':
            order_col = AdTracking.first_seen
        elif sort_by == 'occurrence_count':
            order_col = AdTracking.occurrence_count
        else:
            order_col = AdTracking.last_seen

        if sort_order == 'asc':
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        # 分页
        paginated = query.paginate(page=page, per_page=page_size, error_out=False)

        # 转换为字典并附加额外信息
        results = []
        for item in paginated.items:
            item_dict = item.to_dict()

            # 附加关联的标签信息
            tags = AdTrackingTags.query.filter_by(ad_tracking_id=item.id).all()
            item_dict['tag_ids'] = [tag.tag_id for tag in tags]

            results.append(item_dict)

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': results,
                'total': paginated.total,
                'page': page,
                'page_size': page_size,
                'total_pages': paginated.pages
            }
        })

    except ValueError as e:
        return jsonify({'err_code': 1, 'err_msg': f'参数错误: {str(e)}'})
    except Exception as e:
        logger.error(f"Failed to get ad tracking list: {str(e)}", exc_info=True)
        return jsonify({'err_code': 1, 'err_msg': f'获取列表失败: {str(e)}'})


@api.route('/ad-tracking/<int:tracking_id>', methods=['GET'])
def get_ad_tracking_detail(tracking_id):
    """获取广告追踪详情"""
    try:
        tracking = AdTracking.query.get_or_404(tracking_id)

        detail = tracking.to_dict()

        # 附加关联的标签
        tags = AdTrackingTags.query.filter_by(ad_tracking_id=tracking_id).all()
        detail['tag_ids'] = [tag.tag_id for tag in tags]

        # 附加用户信息（如果有）
        if tracking.user_id:
            user_info = TgGroupUserInfo.query.filter_by(user_id=tracking.user_id).first()
            if user_info:
                detail['user_info'] = {
                    'user_id': user_info.user_id,
                    'nickname': user_info.nickname,
                    'username': user_info.username,
                    'description': user_info.desc,
                    'avatar_url': user_info.avatar_path
                }

        # 附加群组信息（如果有）
        if tracking.chat_id:
            group = TgGroup.query.filter_by(chat_id=tracking.chat_id).first()
            if group:
                detail['group_info'] = {
                    'chat_id': group.chat_id,
                    'group_name': group.name,
                    'group_title': group.title,
                    'description': group.desc,
                    'avatar_url': group.avatar_path
                }

        # 附加原始文本内容（根据来源类型）
        detail['source_text'] = None
        detail['source_timestamp'] = None

        if tracking.source_type == 'chat' and tracking.source_id:
            # 聊天消息：source_id 是消息ID
            try:
                message = TgGroupChatHistory.query.filter_by(
                    id=int(tracking.source_id)
                ).first()
                if message:
                    detail['source_text'] = message.message
                    detail['source_timestamp'] = message.postal_time.isoformat() if message.postal_time else None
            except (ValueError, TypeError) as e:
                # source_id 无法转换为整数，可能是测试数据或数据错误
                logger.warning(f"Invalid source_id for chat record: {tracking.source_id}")

        elif tracking.source_type == 'user_desc' and tracking.user_id:
            # 用户简介：source_id 是用户ID
            user_info = TgGroupUserInfo.query.filter_by(user_id=tracking.user_id).first()
            if user_info:
                detail['source_text'] = user_info.desc
                detail['source_timestamp'] = user_info.updated_at.isoformat() if user_info.updated_at else None

        elif tracking.source_type == 'group_intro' and tracking.chat_id:
            # 群组简介：source_id 是群组ID
            group = TgGroup.query.filter_by(chat_id=tracking.chat_id).first()
            if group:
                detail['source_text'] = group.desc
                detail['source_timestamp'] = group.updated_at.isoformat() if group.updated_at else None

        return jsonify({
            'err_code': 0,
            'payload': detail
        })

    except Exception as e:
        logger.error(f"Failed to get ad tracking detail {tracking_id}: {str(e)}", exc_info=True)
        return jsonify({'err_code': 1, 'err_msg': f'获取详情失败: {str(e)}'})


@api.route('/ad-tracking/<int:tracking_id>', methods=['DELETE'])
def delete_ad_tracking(tracking_id):
    """删除广告追踪记录"""
    try:
        tracking = AdTracking.query.get_or_404(tracking_id)

        # 删除关联的标签
        AdTrackingTags.query.filter_by(ad_tracking_id=tracking_id).delete()

        # 删除追踪记录
        db.session.delete(tracking)
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'payload': {'message': '删除成功'}
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete ad tracking {tracking_id}: {str(e)}", exc_info=True)
        return jsonify({'err_code': 1, 'err_msg': f'删除失败: {str(e)}'})


@api.route('/ad-tracking/stats', methods=['GET'])
def get_ad_tracking_stats():
    """
    获取广告追踪统计信息

    Query Parameters:
        - start_date: 开始日期（YYYY-MM-DD）
        - end_date: 结束日期（YYYY-MM-DD）
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 构建基础查询
        base_query = AdTracking.query

        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            base_query = base_query.filter(AdTracking.first_seen >= start_datetime)

        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            base_query = base_query.filter(AdTracking.first_seen <= end_datetime)

        # 按内容类型统计
        content_type_stats = db.session.query(
            AdTracking.content_type,
            func.count(AdTracking.id).label('count'),
            func.sum(AdTracking.occurrence_count).label('total_occurrences')
        ).filter(
            base_query.whereclause if base_query.whereclause is not None else True
        ).group_by(AdTracking.content_type).all()

        # 按来源类型统计
        source_type_stats = db.session.query(
            AdTracking.source_type,
            func.count(AdTracking.id).label('count')
        ).filter(
            base_query.whereclause if base_query.whereclause is not None else True
        ).group_by(AdTracking.source_type).all()

        # 按群组统计（Top 10）
        chat_stats = db.session.query(
            AdTracking.chat_id,
            func.count(AdTracking.id).label('count')
        ).filter(
            and_(
                AdTracking.chat_id.isnot(None),
                AdTracking.chat_id != '',
                base_query.whereclause if base_query.whereclause is not None else True
            )
        ).group_by(AdTracking.chat_id).order_by(desc('count')).limit(10).all()

        # 附加群组名称
        chat_stats_with_names = []
        for stat in chat_stats:
            group = TgGroup.query.filter_by(chat_id=stat.chat_id).first()
            chat_stats_with_names.append({
                'chat_id': stat.chat_id,
                'count': stat.count,
                'group_name': group.name if group else None
            })

        # 按用户统计（Top 10）
        user_stats = db.session.query(
            AdTracking.user_id,
            func.count(AdTracking.id).label('count')
        ).filter(
            and_(
                AdTracking.user_id.isnot(None),
                AdTracking.user_id != '',
                base_query.whereclause if base_query.whereclause is not None else True
            )
        ).group_by(AdTracking.user_id).order_by(desc('count')).limit(10).all()

        # 附加用户昵称
        user_stats_with_names = []
        for stat in user_stats:
            user_info = TgGroupUserInfo.query.filter_by(user_id=stat.user_id).first()
            user_stats_with_names.append({
                'user_id': stat.user_id,
                'count': stat.count,
                'nickname': user_info.nickname if user_info else None
            })

        # 总体统计
        total_records = base_query.count()
        total_occurrences = db.session.query(
            func.sum(AdTracking.occurrence_count)
        ).filter(
            base_query.whereclause if base_query.whereclause is not None else True
        ).scalar() or 0

        unique_users = db.session.query(
            func.count(func.distinct(AdTracking.user_id))
        ).filter(
            and_(
                AdTracking.user_id.isnot(None),
                AdTracking.user_id != '',
                base_query.whereclause if base_query.whereclause is not None else True
            )
        ).scalar() or 0

        unique_chats = db.session.query(
            func.count(func.distinct(AdTracking.chat_id))
        ).filter(
            and_(
                AdTracking.chat_id.isnot(None),
                AdTracking.chat_id != '',
                base_query.whereclause if base_query.whereclause is not None else True
            )
        ).scalar() or 0

        # 统计商家数量
        unique_merchants = db.session.query(
            func.count(func.distinct(AdTracking.merchant_name))
        ).filter(
            and_(
                AdTracking.merchant_name.isnot(None),
                AdTracking.merchant_name != '',
                base_query.whereclause if base_query.whereclause is not None else True
            )
        ).scalar() or 0

        # 按商家统计（Top 10）
        merchant_stats = db.session.query(
            AdTracking.merchant_name,
            func.count(AdTracking.id).label('count'),
            func.sum(AdTracking.occurrence_count).label('total_occurrences')
        ).filter(
            and_(
                AdTracking.merchant_name.isnot(None),
                AdTracking.merchant_name != '',
                base_query.whereclause if base_query.whereclause is not None else True
            )
        ).group_by(AdTracking.merchant_name).order_by(desc('total_occurrences')).limit(10).all()

        return jsonify({
            'err_code': 0,
            'payload': {
                'summary': {
                    'total_records': total_records,
                    'total_occurrences': int(total_occurrences),
                    'unique_users': unique_users,
                    'unique_chats': unique_chats,
                    'unique_merchants': unique_merchants
                },
                'content_type_stats': [
                    {
                        'content_type': stat.content_type,
                        'count': stat.count,
                        'total_occurrences': stat.total_occurrences or 0
                    } for stat in content_type_stats
                ],
                'source_type_stats': [
                    {
                        'source_type': stat.source_type,
                        'count': stat.count
                    } for stat in source_type_stats
                ],
                'top_chats': chat_stats_with_names,
                'top_users': user_stats_with_names,
                'top_merchants': [
                    {
                        'merchant_name': stat.merchant_name,
                        'count': stat.count,
                        'total_occurrences': stat.total_occurrences or 0
                    } for stat in merchant_stats
                ]
            }
        })

    except ValueError as e:
        return jsonify({'err_code': 1, 'err_msg': f'参数错误: {str(e)}'})
    except Exception as e:
        logger.error(f"Failed to get ad tracking stats: {str(e)}", exc_info=True)
        return jsonify({'err_code': 1, 'err_msg': f'获取统计失败: {str(e)}'})


@api.route('/ad-tracking/task/execute', methods=['POST'])
def execute_ad_tracking_task():
    """
    执行广告追踪任务

    Request Body:
        {
            "task_type": "daily" | "historical" | "chat_record" | "user_info" | "group_info",
            "target_date": "YYYY-MM-DD" (仅daily任务),
            "batch_size": int (仅historical任务),
            "max_batches": int (仅historical任务),
            "record_id": int (仅chat_record任务),
            "user_id": str (仅user_info任务),
            "chat_id": str (仅group_info任务)
        }
    """
    try:
        data = request.get_json() or {}
        task_type = data.get('task_type', 'daily')

        if task_type not in ['daily', 'historical', 'chat_record', 'user_info', 'group_info']:
            return jsonify({'err_code': 1, 'err_msg': '无效的任务类型'})

        # 动态导入任务以避免循环导入
        from jd.tasks.ad_tracking_task import (
            daily_ad_tracking_task,
            historical_ad_tracking_batch_task,
            process_chat_record_task,
            process_user_info_task,
            process_group_info_task
        )

        # 根据任务类型执行
        if task_type == 'daily':
            target_date = data.get('target_date')
            task = daily_ad_tracking_task.delay(target_date)
        elif task_type == 'historical':
            batch_size = data.get('batch_size', 1000)
            max_batches = data.get('max_batches')
            task = historical_ad_tracking_batch_task.delay(batch_size, max_batches)
        elif task_type == 'chat_record':
            record_id = data.get('record_id')
            if not record_id:
                return jsonify({'err_code': 1, 'err_msg': 'record_id参数必填'})
            task = process_chat_record_task.delay(record_id)
        elif task_type == 'user_info':
            user_id = data.get('user_id')
            if not user_id:
                return jsonify({'err_code': 1, 'err_msg': 'user_id参数必填'})
            task = process_user_info_task.delay(user_id)
        elif task_type == 'group_info':
            chat_id = data.get('chat_id')
            if not chat_id:
                return jsonify({'err_code': 1, 'err_msg': 'chat_id参数必填'})
            task = process_group_info_task.delay(chat_id)

        return jsonify({
            'err_code': 0,
            'payload': {
                'task_id': task.id,
                'task_type': task_type,
                'status': 'submitted'
            }
        })

    except Exception as e:
        logger.error(f"Failed to execute ad tracking task: {str(e)}", exc_info=True)
        return jsonify({'err_code': 1, 'err_msg': f'任务提交失败: {str(e)}'})


@api.route('/ad-tracking/task/status/<task_id>', methods=['GET'])
def get_ad_tracking_task_status(task_id):
    """获取广告追踪任务状态"""
    try:
        from scripts.worker import celery
        task = celery.AsyncResult(task_id)

        return jsonify({
            'err_code': 0,
            'payload': {
                'task_id': task_id,
                'status': task.status,
                'result': task.result if task.ready() else None,
                'info': task.info
            }
        })

    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}", exc_info=True)
        return jsonify({'err_code': 1, 'err_msg': f'获取任务状态失败: {str(e)}'})


@api.route('/ad-tracking/search-by-domain', methods=['GET'])
def search_by_domain():
    """
    按域名搜索广告追踪记录

    Query Parameters:
        - domain: 域名
        - page: 页码
        - page_size: 每页记录数
    """
    try:
        domain = request.args.get('domain')
        if not domain:
            return jsonify({'err_code': 1, 'err_msg': '域名参数必填'})

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        page_size = min(page_size, 100)

        # 搜索extra_info中包含该域名的记录
        query = AdTracking.query.filter(
            AdTracking.content_type == 'url'
        ).filter(
            func.json_extract(AdTracking.extra_info, '$.domain') == domain
        ).order_by(AdTracking.last_seen.desc())

        paginated = query.paginate(page=page, per_page=page_size, error_out=False)

        results = [item.to_dict() for item in paginated.items]

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': results,
                'total': paginated.total,
                'page': page,
                'page_size': page_size,
                'domain': domain
            }
        })

    except Exception as e:
        logger.error(f"Failed to search by domain: {str(e)}", exc_info=True)
        return jsonify({'err_code': 1, 'err_msg': f'搜索失败: {str(e)}'})


@api.route('/ad-tracking/tags/<int:tracking_id>', methods=['POST'])
def add_tags_to_tracking(tracking_id):
    """
    为广告追踪记录添加标签

    Request Body:
        {
            "tag_ids": [1, 2, 3]
        }
    """
    try:
        data = request.get_json() or {}
        tag_ids = data.get('tag_ids', [])

        if not tag_ids or not isinstance(tag_ids, list):
            return jsonify({'err_code': 1, 'err_msg': '标签ID列表必填'})

        tracking = AdTracking.query.get_or_404(tracking_id)

        added_count = 0
        for tag_id in tag_ids:
            # 检查是否已存在
            existing = AdTrackingTags.query.filter_by(
                ad_tracking_id=tracking_id,
                tag_id=tag_id
            ).first()

            if not existing:
                tag_relation = AdTrackingTags(
                    ad_tracking_id=tracking_id,
                    tag_id=tag_id
                )
                db.session.add(tag_relation)
                added_count += 1

        db.session.commit()

        return jsonify({
            'err_code': 0,
            'payload': {
                'message': f'成功添加 {added_count} 个标签',
                'added_count': added_count
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to add tags to tracking {tracking_id}: {str(e)}", exc_info=True)
        return jsonify({'err_code': 1, 'err_msg': f'添加标签失败: {str(e)}'})


@api.route('/ad-tracking/tags/<int:tracking_id>/<int:tag_id>', methods=['DELETE'])
def remove_tag_from_tracking(tracking_id, tag_id):
    """删除广告追踪记录的标签"""
    try:
        tag_relation = AdTrackingTags.query.filter_by(
            ad_tracking_id=tracking_id,
            tag_id=tag_id
        ).first()

        if not tag_relation:
            return jsonify({'err_code': 1, 'err_msg': '标签关联不存在'})

        db.session.delete(tag_relation)
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'payload': {'message': '删除成功'}
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to remove tag from tracking: {str(e)}", exc_info=True)
        return jsonify({'err_code': 1, 'err_msg': f'删除标签失败: {str(e)}'})


@api.route('/ad-tracking/<int:tracking_id>/merchant-name', methods=['PUT'])
def update_merchant_name(tracking_id):
    """
    更新广告追踪记录的商家名称

    Request Body:
        - merchant_name: 商家名称（可为空字符串清空）
    """
    try:
        tracking = AdTracking.query.get_or_404(tracking_id)

        data = request.get_json()
        merchant_name = data.get('merchant_name', '').strip()

        # 允许设置为None/空字符串以清空
        tracking.merchant_name = merchant_name if merchant_name else None
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'payload': {
                'message': '商家名称已更新',
                'merchant_name': tracking.merchant_name
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update merchant name: {str(e)}", exc_info=True)
        return jsonify({'err_code': 1, 'err_msg': f'更新商家名称失败: {str(e)}'})

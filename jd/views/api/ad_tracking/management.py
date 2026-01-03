from flask import request, jsonify, g
from jd import db
from jd.views.api import api
from jd.models.ad_tracking_processing_batch import AdTrackingProcessingBatch
from jd.models.tg_group import TgGroup
from jd.models.tag_keyword_mapping import TagKeywordMapping
from jd.models.result_tag import ResultTag
from celery.result import AsyncResult


@api.route('/ad-tracking/channels', methods=['GET'], need_login=False)
def get_channels_for_processing():
    """获取可用于处理的频道列表"""
    try:
        # 获取查询参数
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        search = request.args.get('search', '')

        # 查询频道
        query = TgGroup.query

        # 过滤已停用的频道（除非明确要求包含）
        if not include_inactive:
            query = query.filter_by(status=1)  # 假设status=1表示活跃

        # 搜索过滤
        if search:
            query = query.filter(
                TgGroup.name.ilike(f'%{search}%')
            )

        # 获取频道列表
        channels = query.order_by(TgGroup.created_at.desc()).all()

        # 构建响应数据
        channels_data = []
        for channel in channels:
            channels_data.append({
                'id': channel.id,
                'name': channel.name,
                'chat_id': channel.chat_id,
                'group_type': channel.group_type,
                'status': channel.status,
                'title': channel.title,
                'last_active': channel.updated_at.strftime('%Y-%m-%d %H:%M:%S') if channel.updated_at else None,
                'description': channel.desc
            })

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': channels_data,
                'total': len(channels_data)
            }
        })

    except Exception as e:
        return jsonify({
            'err_code': 500,
            'err_msg': f'获取频道列表失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/tags', methods=['GET'], need_login=False)
def get_tags_for_processing():
    """获取可用的标签列表（去重，返回唯一标签）"""
    try:
        # 获取查询参数
        show_inactive = request.args.get('show_inactive', 'false').lower() == 'true'
        search = request.args.get('search', '')

        # 获取所有活跃的 ResultTag（标签主表）
        tag_query = db.session.query(ResultTag)

        # 搜索过滤
        if search:
            tag_query = tag_query.filter(
                ResultTag.title.ilike(f'%{search}%')
            )

        tags = tag_query.order_by(ResultTag.id).all()

        # 构建响应数据：返回唯一的标签（去重）
        tags_data = []

        for tag in tags:
            # 计算该标签对应的关键词数量
            keyword_count = db.session.query(TagKeywordMapping).filter_by(
                tag_id=tag.id
            ).count()

            tags_data.append({
                'id': tag.id,  # 使用 ResultTag 的 ID 作为标签ID
                'tag_name': tag.title,  # 标签名称
                'keyword_count': keyword_count,  # 该标签关联的关键词数量
                'color': tag.color if hasattr(tag, 'color') else '#409eff',
                'is_active': True  # ResultTag 没有 is_active 字段，但标签通常是活跃的
            })

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': tags_data,
                'total': len(tags_data)
            }
        })

    except Exception as e:
        return jsonify({
            'err_code': 500,
            'err_msg': f'获取标签列表失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/process', methods=['POST'], need_login=False)
def start_channel_processing():
    """开始处理频道"""
    try:
        data = request.get_json() or {}
        channel_id = data.get('channel_id')
        selected_tag_ids = data.get('selected_tag_ids', [])

        if not channel_id:
            return jsonify({
                'err_code': 400,
                'err_msg': '请提供频道ID'
            }), 400

        # 允许不选择标签，selected_tag_ids可以为空

        # 验证频道是否存在
        channel = TgGroup.query.get(channel_id)
        if not channel:
            return jsonify({
                'err_code': 404,
                'err_msg': '频道不存在'
            }), 404

        # 检查是否已有正在处理的任务
        existing_batch = AdTrackingProcessingBatch.query.filter_by(
            channel_id=channel_id,
            status=AdTrackingProcessingBatch.Status.PROCESSING
        ).first()

        if existing_batch:
            return jsonify({
                'err_code': 409,
                'err_msg': f'频道 "{channel.name}" 正在处理中，批次ID: {existing_batch.id}'
            }), 409

        # 创建处理批次
        batch = AdTrackingProcessingBatch.create_batch(channel_id, selected_tag_ids)

        # 启动Celery任务，传递batch_id
        from jd.tasks.ad_tracking import process_channel_for_ad_tracking

        task = process_channel_for_ad_tracking.delay(channel_id, selected_tag_ids, batch.id)

        # 更新批次任务ID（可选）
        batch.task_id = task.id
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': {
                    'batch_id': batch.id,
                    'task_id': task.id,
                    'status': batch.status,
                    'message': f'已开始处理频道 "{channel.name}"'
                }
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'启动处理失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/process/<batch_id>', methods=['GET'], need_login=False)
def get_processing_status(batch_id):
    """获取处理状态"""
    try:
        batch = AdTrackingProcessingBatch.query.get(batch_id)
        if not batch:
            return jsonify({
                'err_code': 404,
                'err_msg': '处理批次不存在'
            }), 404

        # 获取任务状态（如果有任务ID）
        task_info = None
        if batch.task_id:
            try:
                task_result = AsyncResult(batch.task_id)
                task_info = {
                    'task_id': batch.task_id,
                    'state': task_result.state,
                    'info': task_result.info
                }
            except Exception:
                task_info = {
                    'task_id': batch.task_id,
                    'state': 'unknown',
                    'info': None
                }

        # 构建响应
        status_data = batch.to_dict()
        status_data['task_info'] = task_info

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': status_data
            }
        })

    except Exception as e:
        return jsonify({
            'err_code': 500,
            'err_msg': f'获取处理状态失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/process/<batch_id>/cancel', methods=['POST'], need_login=False)
def cancel_processing(batch_id):
    """取消处理任务"""
    try:
        batch = AdTrackingProcessingBatch.query.get(batch_id)
        if not batch:
            return jsonify({
                'err_code': 404,
                'err_msg': '处理批次不存在'
            }), 404

        # 只有正在处理的任务可以取消
        if batch.status != AdTrackingProcessingBatch.Status.PROCESSING:
            return jsonify({
                'err_code': 400,
                'err_msg': f'无法取消状态为 {batch.status} 的任务'
            }), 400

        # 取消Celery任务（如果有）
        if batch.task_id:
            from celery.control import revoke
            try:
                revoke(batch.task_id, terminate=True)
            except Exception:
                pass  # 忽略取消任务时的错误

        # 标记为失败
        batch.mark_as_failed("用户取消")

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': {
                    'message': '任务已取消'
                }
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'取消任务失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/process/retry/<batch_id>', methods=['POST'], need_login=False)
def retry_processing(batch_id):
    """重试处理任务"""
    try:
        batch = AdTrackingProcessingBatch.query.get(batch_id)
        if not batch:
            return jsonify({
                'err_code': 404,
                'err_msg': '处理批次不存在'
            }), 404

        # 只有失败或完成的任务可以重试
        if batch.status not in [AdTrackingProcessingBatch.Status.FAILED, AdTrackingProcessingBatch.Status.COMPLETED]:
            return jsonify({
                'err_code': 400,
                'err_msg': f'无法重试状态为 {batch.status} 的任务'
            }), 400

        # 重置批次状态
        batch.reset()

        # 启动Celery任务，传递batch_id
        from jd.tasks.ad_tracking import process_channel_for_ad_tracking

        task = process_channel_for_ad_tracking.delay(batch.channel_id, batch.get_selected_tag_ids_list(), batch.id)

        # 更新批次任务ID
        batch.task_id = task.id
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': {
                    'batch_id': batch.id,
                    'task_id': task.id,
                    'status': batch.status,
                    'message': '任务已重新开始'
                }
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'重试任务失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/process/history', methods=['GET'], need_login=False)
def get_processing_history():
    """获取处理历史"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        channel_id = request.args.get('channel_id', type=int)
        status = request.args.get('status')

        # 限制每页最大数量
        page_size = min(page_size, 100)

        # 构建查询
        query = AdTrackingProcessingBatch.query

        # 条件过滤
        if channel_id:
            query = query.filter_by(channel_id=channel_id)

        if status:
            query = query.filter_by(status=status)

        # 按创建时间倒序排序
        query = query.order_by(AdTrackingProcessingBatch.created_at.desc())

        # 分页查询
        paginated = query.paginate(
            page=page,
            per_page=page_size,
            error_out=False
        )

        # 构建响应
        return jsonify({
            'err_code': 0,
            'payload': {
                'data': [batch.to_dict() for batch in paginated.items],
                'total': paginated.total,
                'page': page,
                'page_size': page_size,
                'total_pages': paginated.pages
            }
        })

    except Exception as e:
        return jsonify({
            'err_code': 500,
            'err_msg': f'获取处理历史失败: {str(e)}'
        }), 500
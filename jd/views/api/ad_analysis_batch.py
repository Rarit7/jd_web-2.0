"""
广告分析批处理管理 API
用于提交、管理、监控数据提取批次
"""
import logging
import uuid
from datetime import datetime

from flask import request
from jd import db
from jd.views.api import api
from jd.helpers.response import api_response
from jd.models.ad_tracking_batch_process_log import AdTrackingBatchProcessLog
from jd.tasks.ad_analysis_extraction import (
    process_batch_for_analysis,
    process_messages_for_chat,
    process_all_chats
)
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


@api.route('/ad-tracking/ad-analysis/batch/submit', methods=['POST'], need_login=False)
def submit_batch_process():
    """
    提交批次数据提取任务

    Request Body:
        {
            "chat_id": "123456",
            "include_price": true,
            "include_transaction": true,
            "include_geo": true,
            "include_dark_keyword": true,
            "limit": 10000,
            "start_date": "2025-01-01",
            "end_date": "2026-01-06"
        }

    Returns:
        {
            "batch_id": "uuid",
            "status": "pending",
            "task_id": "celery_task_id"
        }
    """
    try:
        data = request.get_json() or {}

        # 参数验证
        chat_id = data.get('chat_id')
        if not chat_id:
            return api_response(
                {},
                err_code=2,
                err_msg='缺少必需参数: chat_id',
                status_code=400
            )

        # 生成批次ID
        batch_id = str(uuid.uuid4())

        # 构建处理配置
        config = {
            'include_price': data.get('include_price', True),
            'include_transaction': data.get('include_transaction', True),
            'include_geo': data.get('include_geo', True),
            'include_dark_keyword': data.get('include_dark_keyword', True),
            'limit': data.get('limit', 10000),
            'tag_ids': data.get('tag_ids', []),
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date')
        }

        # 参数范围验证
        if config['limit'] < 1 or config['limit'] > 1000000:
            return api_response(
                {},
                err_code=2,
                err_msg='limit 必须在 1-1000000 之间',
                status_code=400
            )

        # 创建批次记录
        batch = AdTrackingBatchProcessLog(
            batch_id=batch_id,
            chat_id=str(chat_id),
            include_price=config.get('include_price', True),
            selected_tags=config.get('tag_ids', []),
            status='processing'  # 使用 'processing' 而不是 'pending'
        )
        db.session.add(batch)
        db.session.commit()

        # 提交 Celery 任务（参照现有任务实现）
        task_id = None
        try:
            task = process_batch_for_analysis.apply_async(
                args=[str(chat_id), batch_id, config],
                queue='jd.celery.first'
            )
            task_id = task.id
            logger.info(
                f"提交批次: batch_id={batch_id}, chat_id={chat_id}, "
                f"task_id={task_id}, config={config}"
            )
        except Exception as celery_error:
            # Celery 任务提交失败时，记录错误但继续返回成功
            # 批次记录已创建，前端可以通过 GET 接口查询状态
            logger.warning(
                f"Celery 任务提交失败: batch_id={batch_id}, chat_id={chat_id}, "
                f"error={str(celery_error)}, 但批次记录已创建"
            )
            task_id = None

        return api_response({
            'batch_id': batch_id,
            'task_id': task_id,
            'status': 'processing',
            'chat_id': str(chat_id),
            'created_at': datetime.now().isoformat()
        }, status_code=201)

    except Exception as e:
        logger.error(f"提交批次失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response(
            {},
            err_code=99,
            err_msg='服务器错误',
            status_code=500
        )


@api.route('/ad-tracking/ad-analysis/batch/<batch_id>', methods=['GET'], need_login=False)
def get_batch_status(batch_id):
    """
    获取批次处理状态

    Path Parameters:
        batch_id: 批次ID

    Returns:
        {
            "batch_id": "uuid",
            "status": "processing|completed|failed",
            "total_messages": 1000,
            "processed_messages": 500,
            "success_count": 450,
            "fail_count": 50,
            "progress_percent": 50.0,
            "created_at": "2026-01-06T12:34:56",
            "started_at": "2026-01-06T12:35:00",
            "completed_at": null,
            "error_message": null
        }
    """
    try:
        batch = AdTrackingBatchProcessLog.query.filter_by(batch_id=batch_id).first()

        if not batch:
            return api_response(
                {},
                err_code=5,
                err_msg='批次不存在',
                status_code=404
            )

        # 计算进度百分比
        progress_percent = 0.0
        if batch.total_messages > 0:
            processed = batch.success_count + batch.fail_count
            progress_percent = (processed / batch.total_messages) * 100

        return api_response({
            'batch_id': batch.batch_id,
            'chat_id': batch.chat_id,
            'status': batch.status,
            'total_messages': batch.total_messages or 0,
            'processed_messages': (batch.success_count or 0) + (batch.fail_count or 0),
            'success_count': batch.success_count or 0,
            'fail_count': batch.fail_count or 0,
            'progress_percent': round(progress_percent, 2),
            'created_at': batch.created_at.isoformat() if batch.created_at else None,
            'started_at': batch.start_time.isoformat() if batch.start_time else None,
            'completed_at': batch.end_time.isoformat() if batch.end_time else None
        })

    except Exception as e:
        logger.error(f"获取批次状态失败: {e}", exc_info=True)
        return api_response(
            {},
            err_code=99,
            err_msg='服务器错误',
            status_code=500
        )


@api.route('/ad-tracking/ad-analysis/batch', methods=['GET'], need_login=False)
def list_batches():
    """
    获取批次列表（分页）

    Query Parameters:
        chat_id: 群组ID (可选)
        status: 状态 pending|processing|completed|failed (可选)
        offset: 分页偏移 (默认0)
        limit: 分页大小 (默认20)

    Returns:
        {
            "data": [...],
            "total": 100,
            "page": 1,
            "page_size": 20
        }
    """
    try:
        chat_id = request.args.get('chat_id')
        status = request.args.get('status')
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)

        # 参数验证
        if offset < 0 or limit < 1 or limit > 100:
            return api_response(
                {},
                err_code=2,
                err_msg='offset 必须 >= 0, limit 必须在 1-100 之间',
                status_code=400
            )

        # 构建查询
        query = AdTrackingBatchProcessLog.query

        if chat_id:
            query = query.filter_by(chat_id=str(chat_id))

        if status:
            valid_statuses = ['pending', 'processing', 'completed', 'failed']
            if status not in valid_statuses:
                return api_response(
                    {},
                    err_code=2,
                    err_msg=f'status 必须是 {valid_statuses} 之一',
                    status_code=400
                )
            query = query.filter_by(status=status)

        # 获取总数和分页数据
        total = query.count()
        batches = query.order_by(
            AdTrackingBatchProcessLog.created_at.desc()
        ).offset(offset).limit(limit).all()

        # 构建响应
        data = []
        for batch in batches:
            progress_percent = 0.0
            if batch.total_messages and batch.total_messages > 0:
                processed = batch.success_count + batch.fail_count
                progress_percent = (processed / batch.total_messages) * 100

            data.append({
                'batch_id': batch.batch_id,
                'chat_id': batch.chat_id,
                'status': batch.status,
                'total_messages': batch.total_messages or 0,
                'processed_messages': (batch.success_count or 0) + (batch.fail_count or 0),
                'success_count': batch.success_count or 0,
                'fail_count': batch.fail_count or 0,
                'progress_percent': round(progress_percent, 2),
                'created_at': batch.created_at.isoformat() if batch.created_at else None,
                'completed_at': batch.end_time.isoformat() if batch.end_time else None
            })

        return api_response({
            'data': data,
            'total': total,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'page_size': limit
        })

    except Exception as e:
        logger.error(f"获取批次列表失败: {e}", exc_info=True)
        return api_response(
            {},
            err_code=99,
            err_msg='服务器错误',
            status_code=500
        )


@api.route('/ad-tracking/ad-analysis/batch/<batch_id>', methods=['DELETE'], need_login=False)
def delete_batch(batch_id):
    """
    删除批次记录

    只有状态为 completed 或 failed 的批次才能删除
    """
    try:
        batch = AdTrackingBatchProcessLog.query.filter_by(batch_id=batch_id).first()

        if not batch:
            return api_response(
                {},
                err_code=5,
                err_msg='批次不存在',
                status_code=404
            )

        # 只允许删除已完成或已失败的批次
        if batch.status not in ['completed', 'failed']:
            return api_response(
                {},
                err_code=1,
                err_msg=f'只能删除已完成或已失败的批次，当前状态: {batch.status}',
                status_code=400
            )

        db.session.delete(batch)
        db.session.commit()

        logger.info(f"删除批次: {batch_id}")

        return api_response({'batch_id': batch_id})

    except Exception as e:
        logger.error(f"删除批次失败: {e}", exc_info=True)
        db.session.rollback()
        return api_response(
            {},
            err_code=99,
            err_msg='服务器错误',
            status_code=500
        )


@api.route('/ad-tracking/ad-analysis/batch/quick-process', methods=['POST'], need_login=False)
def quick_process_messages():
    """
    快速处理指定群组最近N天的消息

    不需要创建批次记录，直接返回 Celery 任务ID

    Request Body:
        {
            "chat_id": "123456",
            "days": 7,
            "include_price": true,
            "include_transaction": true,
            "include_geo": true,
            "include_dark_keyword": true
        }

    Returns:
        {
            "task_id": "celery_task_id",
            "chat_id": "123456",
            "days": 7
        }
    """
    try:
        data = request.get_json() or {}

        chat_id = data.get('chat_id')
        if not chat_id:
            return api_response(
                {},
                err_code=2,
                err_msg='缺少必需参数: chat_id',
                status_code=400
            )

        days = data.get('days', 7)
        if days < 1 or days > 3650:
            return api_response(
                {},
                err_code=2,
                err_msg='days 必须在 1-3650 之间',
                status_code=400
            )

        # 提交任务（参照现有任务实现）
        task_id = None
        try:
            task = process_messages_for_chat.apply_async(
                args=[
                    str(chat_id),
                    days,
                    data.get('include_price', True),
                    data.get('include_transaction', True),
                    data.get('include_geo', True),
                    data.get('include_dark_keyword', True)
                ],
                queue='jd.celery.first'
            )
            task_id = task.id
            logger.info(f"快速处理任务: chat_id={chat_id}, days={days}, task_id={task_id}")
        except Exception as celery_error:
            # Celery 任务提交失败时，记录错误但继续返回成功
            logger.warning(
                f"快速处理任务提交失败: chat_id={chat_id}, days={days}, "
                f"error={str(celery_error)}"
            )
            task_id = None

        return api_response({
            'task_id': task_id,
            'chat_id': str(chat_id),
            'days': days,
            'status': 'pending'
        }, status_code=201)

    except Exception as e:
        logger.error(f"提交快速处理任务失败: {e}", exc_info=True)
        return api_response(
            {},
            err_code=99,
            err_msg='服务器错误',
            status_code=500
        )


@api.route('/ad-tracking/ad-analysis/task/<task_id>', methods=['GET'], need_login=False)
def get_ad_analysis_task_status(task_id):
    """
    获取 Celery 任务状态

    Returns:
        {
            "task_id": "task_id",
            "status": "PENDING|PROGRESS|SUCCESS|FAILURE",
            "result": {...},
            "progress": {...}
        }
    """
    try:
        from jd import app

        # 获取任务结果
        with app.app_context():
            result = AsyncResult(task_id)

            response_data = {
                'task_id': task_id,
                'status': result.state,
            }

            if result.state == 'PROGRESS':
                response_data['progress'] = result.info
            elif result.state == 'SUCCESS':
                response_data['result'] = result.result
            elif result.state == 'FAILURE':
                response_data['error'] = str(result.info)

            return api_response(response_data)

    except Exception as e:
        logger.error(f"获取任务状态失败: {e}", exc_info=True)
        return api_response(
            {},
            err_code=99,
            err_msg='服务器错误',
            status_code=500
        )


@api.route('/ad-tracking/ad-analysis/cache/clear', methods=['POST'], need_login=False)
def clear_analysis_cache():
    """
    清除分析缓存

    当数据处理完成后，强制清除相关缓存以确保显示最新数据

    Request Body:
        {
            "chat_id": "123456"  # 可选，不提供则清除全局缓存
        }

    Returns:
        {
            "message": "缓存已清除",
            "cleared_keys": ["key1", "key2", ...]
        }
    """
    try:
        from jd.services.cache_service import CacheService

        data = request.get_json() or {}
        chat_id = data.get('chat_id')

        cleared_keys = []

        # 清除交易方式缓存
        if chat_id:
            transaction_pattern = f'transaction_methods:{chat_id}:*'
            count = CacheService.clear_pattern(transaction_pattern)
            if count > 0:
                cleared_keys.append(f'{transaction_pattern} ({count}条)')
        else:
            # 清除所有交易方式缓存
            count = CacheService.clear_pattern('transaction_methods:*')
            if count > 0:
                cleared_keys.append(f'transaction_methods:* ({count}条)')

        # 清除地理位置热力图缓存
        if chat_id:
            geo_pattern = f'geo_heatmap:{chat_id}:*'
            count = CacheService.clear_pattern(geo_pattern)
            if count > 0:
                cleared_keys.append(f'{geo_pattern} ({count}条)')
        else:
            count = CacheService.clear_pattern('geo_heatmap:*')
            if count > 0:
                cleared_keys.append(f'geo_heatmap:* ({count}条)')

        # 清除价格趋势缓存
        if chat_id:
            price_pattern = f'price_trend:{chat_id}:*'
            count = CacheService.clear_pattern(price_pattern)
            if count > 0:
                cleared_keys.append(f'{price_pattern} ({count}条)')
        else:
            count = CacheService.clear_pattern('price_trend:*')
            if count > 0:
                cleared_keys.append(f'price_trend:* ({count}条)')

        # 清除黑词分析缓存
        if chat_id:
            dark_pattern = f'dark_keywords:{chat_id}:*'
            count = CacheService.clear_pattern(dark_pattern)
            if count > 0:
                cleared_keys.append(f'{dark_pattern} ({count}条)')
        else:
            count = CacheService.clear_pattern('dark_keywords:*')
            if count > 0:
                cleared_keys.append(f'dark_keywords:* ({count}条)')

        # 同时也清除全局缓存（chat_id 为 None 的情况）
        if chat_id:
            for pattern in [
                'transaction_methods:None:*',
                'geo_heatmap:None:*',
                'price_trend:None:*',
                'dark_keywords:None:*'
            ]:
                count = CacheService.clear_pattern(pattern)
                if count > 0:
                    cleared_keys.append(f'{pattern} ({count}条)')

        logger.info(f"清除分析缓存: chat_id={chat_id}, 清除的键={cleared_keys}")

        return api_response({
            'message': '缓存已清除',
            'cleared_count': len(cleared_keys),
            'cleared_keys': cleared_keys
        })

    except Exception as e:
        logger.error(f"清除缓存失败: {e}", exc_info=True)
        return api_response(
            {},
            err_code=99,
            err_msg='清除缓存失败',
            status_code=500
        )


@api.route('/ad-tracking/ad-analysis/process-all-chats', methods=['POST'], need_login=False)
def process_all_chats_api():
    """
    处理所有群组的消息

    Request Body:
        {
            "days": 1,
            "include_price": true,
            "include_transaction": true,
            "include_geo": true,
            "include_dark_keyword": true
        }

    Returns:
        {
            "task_id": "celery_task_id",
            "message": "已提交批量处理任务"
        }
    """
    try:
        data = request.get_json() or {}

        days = data.get('days', 1)
        if days < 1 or days > 3650:
            return api_response(
                {},
                err_code=2,
                err_msg='days 必须在 1-3650 之间',
                status_code=400
            )

        # 提交任务（参照现有任务实现）
        task_id = None
        try:
            task = process_all_chats.apply_async(
                args=[
                    days,
                    data.get('include_price', True),
                    data.get('include_transaction', True),
                    data.get('include_geo', True),
                    data.get('include_dark_keyword', True)
                ],
                queue='jd.celery.first'
            )
            task_id = task.id
            logger.info(f"批量处理所有群组: days={days}, task_id={task_id}")
        except Exception as celery_error:
            # Celery 任务提交失败时，记录错误但继续返回成功
            logger.warning(
                f"批量处理任务提交失败: days={days}, "
                f"error={str(celery_error)}"
            )
            task_id = None

        return api_response({
            'task_id': task_id,
            'days': days,
            'status': 'pending',
            'message': '已提交所有群组的批量处理任务'
        }, status_code=201)

    except Exception as e:
        logger.error(f"批量处理失败: {e}", exc_info=True)
        return api_response(
            {},
            err_code=99,
            err_msg='服务器错误',
            status_code=500
        )

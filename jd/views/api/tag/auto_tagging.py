from flask import request, jsonify
from sqlalchemy.exc import IntegrityError

from jd import db
from jd.helpers.user import current_user_id
from jd.models.tag_keyword_mapping import TagKeywordMapping
from jd.models.auto_tag_log import AutoTagLog
from jd.services.auto_tagging_service import AutoTaggingService
from jd.views.api import api


@api.route('/tag/tag-keywords', methods=['POST'])
def create_tag_keyword():
    """创建标签关键词映射"""
    data = request.get_json()

    # 参数验证
    if not data.get('tag_id') or not data.get('keyword'):
        return jsonify({'err_code': 1, 'err_msg': '标签ID和关键词不能为空'})

    # 关键词长度验证
    keyword = data['keyword'].strip()
    if len(keyword) > 255:
        return jsonify({'err_code': 1, 'err_msg': '关键词长度不能超过255个字符'})

    mapping = TagKeywordMapping(
        tag_id=data['tag_id'],
        keyword=keyword,
        auto_focus=data.get('auto_focus', False),
        is_active=data.get('is_active', True)
    )

    try:
        db.session.add(mapping)
        db.session.commit()
        return jsonify({'err_code': 0, 'payload': mapping.to_dict()})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'err_code': 1, 'err_msg': '关键词映射已存在'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'err_code': 1, 'err_msg': f'创建失败: {str(e)}'})


@api.route('/tag/tag-keywords/<int:tag_id>', methods=['GET'])
def get_tag_keywords(tag_id):
    """获取标签的所有关键词"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    is_active = request.args.get('is_active', type=bool)

    query = TagKeywordMapping.query.filter_by(tag_id=tag_id)

    if is_active is not None:
        query = query.filter_by(is_active=is_active)

    query = query.order_by(TagKeywordMapping.created_at.desc())

    paginated = query.paginate(
        page=page, per_page=page_size, error_out=False
    )

    return jsonify({
        'err_code': 0,
        'payload': {
            'data': [m.to_dict() for m in paginated.items],
            'total': paginated.total,
            'page': page,
            'page_size': page_size
        }
    })


@api.route('/tag/tag-keywords/<int:keyword_id>', methods=['PUT'])
def update_tag_keyword(keyword_id):
    """更新标签关键词映射"""
    data = request.get_json()

    mapping = TagKeywordMapping.query.get_or_404(keyword_id)

    if 'keyword' in data:
        keyword = data['keyword'].strip()
        if len(keyword) > 255:
            return jsonify({'err_code': 1, 'err_msg': '关键词长度不能超过255个字符'})
        mapping.keyword = keyword

    if 'auto_focus' in data:
        mapping.auto_focus = bool(data['auto_focus'])

    if 'is_active' in data:
        mapping.is_active = bool(data['is_active'])

    try:
        db.session.commit()
        return jsonify({'err_code': 0, 'payload': mapping.to_dict()})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'err_code': 1, 'err_msg': '关键词映射已存在'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'err_code': 1, 'err_msg': f'更新失败: {str(e)}'})


@api.route('/tag/tag-keywords/<int:keyword_id>', methods=['DELETE'])
def delete_tag_keyword(keyword_id):
    """删除标签关键词映射"""
    mapping = TagKeywordMapping.query.get_or_404(keyword_id)

    try:
        db.session.delete(mapping)
        db.session.commit()
        return jsonify({'err_code': 0, 'payload': {'message': '删除成功'}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'err_code': 1, 'err_msg': f'删除失败: {str(e)}'})


@api.route('/tag/tag-keywords/batch', methods=['POST'])
def batch_create_tag_keywords():
    """批量创建标签关键词映射"""
    data = request.get_json()

    if not data.get('tag_id') or not data.get('keywords'):
        return jsonify({'err_code': 1, 'err_msg': '标签ID和关键词列表不能为空'})

    tag_id = data['tag_id']
    keywords = data['keywords']  # 关键词列表
    auto_focus = data.get('auto_focus', False)

    if not isinstance(keywords, list):
        return jsonify({'err_code': 1, 'err_msg': '关键词必须是列表格式'})

    success_count = 0
    failed_keywords = []

    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword or len(keyword) > 255:
            failed_keywords.append({'keyword': keyword, 'reason': '关键词为空或长度超限'})
            continue

        # 检查是否已存在
        existing = TagKeywordMapping.query.filter_by(
            tag_id=tag_id, keyword=keyword
        ).first()

        if existing:
            failed_keywords.append({'keyword': keyword, 'reason': '关键词映射已存在'})
            continue

        mapping = TagKeywordMapping(
            tag_id=tag_id,
            keyword=keyword,
            auto_focus=auto_focus
        )

        try:
            db.session.add(mapping)
            success_count += 1
        except Exception as e:
            failed_keywords.append({'keyword': keyword, 'reason': str(e)})

    try:
        db.session.commit()
        return jsonify({
            'err_code': 0,
            'payload': {
                'success_count': success_count,
                'failed_keywords': failed_keywords,
                'total_keywords': len(keywords)
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'err_code': 1, 'err_msg': f'批量创建失败: {str(e)}'})


@api.route('/tag/auto-tagging/execute', methods=['POST'])
def trigger_auto_tagging():
    """手动触发自动标签任务"""
    data = request.get_json() or {}
    task_type = data.get('type', 'daily')

    if task_type not in ['daily', 'historical']:
        return jsonify({'err_code': 1, 'err_msg': '无效的任务类型'})

    try:
        # Import tasks dynamically to avoid circular import
        from jd.tasks.auto_tagging_tasks import daily_auto_tagging_task, historical_auto_tagging_task

        if task_type == 'historical':
            task = historical_auto_tagging_task.delay()
        else:
            task = daily_auto_tagging_task.delay()

        return jsonify({
            'err_code': 0,
            'payload': {
                'task_id': task.id,
                'task_type': task_type,
                'status': 'submitted'
            }
        })
    except Exception as e:
        return jsonify({'err_code': 1, 'err_msg': f'任务提交失败: {str(e)}'})


@api.route('/tag/auto-tagging/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取自动标签任务状态"""
    try:
        # Import celery dynamically to avoid circular import
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
        return jsonify({'err_code': 1, 'err_msg': f'获取任务状态失败: {str(e)}'})


@api.route('/tag/auto-tagging/logs', methods=['GET'])
def get_auto_tag_logs():
    """获取自动标签日志"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    tag_id = request.args.get('tag_id', type=int)
    user_id = request.args.get('user_id')
    source_type = request.args.get('source_type')

    query = AutoTagLog.query

    if tag_id:
        query = query.filter_by(tag_id=tag_id)
    if user_id:
        query = query.filter_by(tg_user_id=user_id)
    if source_type:
        query = query.filter_by(source_type=source_type)

    query = query.order_by(AutoTagLog.created_at.desc())

    paginated = query.paginate(
        page=page, per_page=page_size, error_out=False
    )

    return jsonify({
        'err_code': 0,
        'payload': {
            'data': [log.to_dict() for log in paginated.items],
            'total': paginated.total,
            'page': page,
            'page_size': page_size
        }
    })


@api.route('/tag/auto-tagging/stats', methods=['GET'])
def get_auto_tagging_stats():
    """获取自动标签统计信息"""
    try:
        # 按标签统计
        tag_stats = db.session.query(
            AutoTagLog.tag_id,
            db.func.count(AutoTagLog.id).label('tag_count'),
            db.func.count(db.distinct(AutoTagLog.tg_user_id)).label('user_count')
        ).group_by(AutoTagLog.tag_id).all()

        # 按来源类型统计
        source_stats = db.session.query(
            AutoTagLog.source_type,
            db.func.count(AutoTagLog.id).label('count')
        ).group_by(AutoTagLog.source_type).all()

        # 按关键词统计
        keyword_stats = db.session.query(
            AutoTagLog.keyword,
            db.func.count(AutoTagLog.id).label('count')
        ).group_by(AutoTagLog.keyword).order_by(db.text('count DESC')).limit(20).all()

        # 总体统计
        total_logs = AutoTagLog.query.count()
        unique_users = db.session.query(db.distinct(AutoTagLog.tg_user_id)).count()
        unique_tags = db.session.query(db.distinct(AutoTagLog.tag_id)).count()

        return jsonify({
            'err_code': 0,
            'payload': {
                'summary': {
                    'total_logs': total_logs,
                    'unique_users': unique_users,
                    'unique_tags': unique_tags
                },
                'tag_stats': [
                    {
                        'tag_id': stat.tag_id,
                        'tag_count': stat.tag_count,
                        'user_count': stat.user_count
                    } for stat in tag_stats
                ],
                'source_stats': [
                    {
                        'source_type': stat.source_type,
                        'count': stat.count
                    } for stat in source_stats
                ],
                'keyword_stats': [
                    {
                        'keyword': stat.keyword,
                        'count': stat.count
                    } for stat in keyword_stats
                ]
            }
        })
    except Exception as e:
        return jsonify({'err_code': 1, 'err_msg': f'获取统计信息失败: {str(e)}'})


@api.route('/tag/auto-tagging/preview', methods=['POST'])
def preview_auto_tagging():
    """预览自动标签效果（不实际应用）"""
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({'err_code': 1, 'err_msg': '文本内容不能为空'})

    try:
        # 模拟处理文本，但不保存到数据库
        matched_tags = AutoTaggingService.process_text_for_tags(
            text, 'preview_user', 'preview', 'preview_id'
        )

        # 获取标签详细信息
        tag_details = []
        for tag_info in matched_tags:
            tag_details.append({
                'tag_id': tag_info['tag_id'],
                'keyword': tag_info['keyword'],
                'auto_focus': tag_info['auto_focus']
            })

        return jsonify({
            'err_code': 0,
            'payload': {
                'matched_count': len(matched_tags),
                'matched_tags': tag_details,
                'preview_text': text
            }
        })
    except Exception as e:
        return jsonify({'err_code': 1, 'err_msg': f'预览失败: {str(e)}'})
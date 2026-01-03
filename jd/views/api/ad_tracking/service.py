"""
广告追踪系统服务 API 端点
"""
from flask import request, jsonify
from jd import db
from jd.views.api import api
from jd.models.ad_tracking_record import AdTrackingRecord
from sqlalchemy import desc


@api.route('/ad-tracking/service/related-records/<int:record_id>', methods=['GET'])
def get_related_records(record_id):
    """
    获取相关的广告记录（基于触发关键词）

    Query Parameters:
        - limit: 返回记录的最大数量，默认5
    """
    try:
        # 获取原始记录
        record = AdTrackingRecord.query.get_or_404(record_id)

        # 获取limit参数
        limit = request.args.get('limit', 5, type=int)
        limit = min(limit, 100)  # 限制最大100条

        # 如果没有触发关键词，返回空列表
        if not record.trigger_keyword:
            return jsonify({
                'err_code': 0,
                'payload': {
                    'data': [],
                    'total': 0
                }
            })

        # 查询其他相同关键词的记录（不包括自己）
        related_records = AdTrackingRecord.query.filter(
            AdTrackingRecord.trigger_keyword == record.trigger_keyword,
            AdTrackingRecord.id != record_id
        ).order_by(
            desc(AdTrackingRecord.send_time)
        ).limit(limit).all()

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': [r.to_dict() for r in related_records],
                'total': len(related_records)
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'获取相关记录失败: {str(e)}'
        }), 500

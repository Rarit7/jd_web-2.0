from flask import request, jsonify, g
from jd import db
from jd.views.api import api
from jd.models.ad_tracking_record import AdTrackingRecord
from jd.models.ad_tracking_processing_batch import AdTrackingProcessingBatch
from jd.models.tg_group import TgGroup
from jd.models.tag_keyword_mapping import TagKeywordMapping
from sqlalchemy import or_, and_, desc
from jd.views import get_or_exception


@api.route('/ad-tracking/records', methods=['GET'])
def get_ad_tracking_records():
    """获取广告记录列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        channel_id = request.args.get('channel_id', type=int)
        trigger_keyword = request.args.get('trigger_keyword', '')
        trigger_tag_id = request.args.get('trigger_tag_id', type=int)
        process_batch_id = request.args.get('process_batch_id', '')
        is_processed = request.args.get('is_processed', type=bool)

        # 限制每页最大数量
        page_size = min(page_size, 100)

        # 构建查询
        query = AdTrackingRecord.query

        # 条件过滤
        if channel_id:
            query = query.filter_by(channel_id=channel_id)

        if trigger_keyword:
            query = query.filter(
                AdTrackingRecord.trigger_keyword.ilike(f'%{trigger_keyword}%')
            )

        if trigger_tag_id:
            query = query.filter_by(trigger_tag_id=trigger_tag_id)

        if process_batch_id:
            query = query.filter_by(process_batch_id=process_batch_id)

        if is_processed is not None:
            query = query.filter_by(is_processed=is_processed)

        # 按发送时间倒序排序
        query = query.order_by(desc(AdTrackingRecord.send_time))

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
                'data': [record.to_detail_dict() for record in paginated.items],
                'total': paginated.total,
                'page': page,
                'page_size': page_size,
                'total_pages': paginated.pages
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'获取广告记录失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/records/<int:record_id>', methods=['GET'])
def get_ad_tracking_record_detail(record_id):
    """获取广告记录详情"""
    try:
        record = AdTrackingRecord.query.get_or_404(record_id)

        # 获取相关的处理批次信息
        batch_info = None
        if record.process_batch_id:
            batch = AdTrackingProcessingBatch.query.get(record.process_batch_id)
            if batch:
                batch_info = batch.to_dict()

        # 构建详细响应
        detail_data = record.to_detail_dict()
        detail_data['batch_info'] = batch_info

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': detail_data
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'获取广告记录详情失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/records/<int:record_id>', methods=['PATCH'])
def update_ad_tracking_record(record_id):
    """更新广告记录"""
    try:
        record = AdTrackingRecord.query.get_or_404(record_id)

        # 获取请求数据
        data = request.get_json() or {}

        # 更新允许的字段
        if 'is_processed' in data:
            record.is_processed = bool(data.get('is_processed'))

        if 'process_batch_id' in data:
            record.process_batch_id = data.get('process_batch_id')

        if 'trigger_keyword' in data:
            record.trigger_keyword = data.get('trigger_keyword')

        # 保存更改
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': record.to_detail_dict()
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'更新广告记录失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/records/<int:record_id>', methods=['DELETE'])
def delete_ad_tracking_record(record_id):
    """删除广告记录"""
    try:
        record = AdTrackingRecord.query.get_or_404(record_id)

        # 删除记录
        db.session.delete(record)
        db.session.commit()

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': {'message': '删除成功'}
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'删除广告记录失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/records/batch/delete', methods=['POST'])
def batch_delete_ad_tracking_records():
    """批量删除广告记录"""
    try:
        data = request.get_json() or {}
        record_ids = data.get('record_ids', [])

        if not record_ids:
            return jsonify({
                'err_code': 400,
                'err_msg': '请提供要删除的记录ID列表'
            }), 400

        # 批量删除
        deleted_count = AdTrackingRecord.query.filter(
            AdTrackingRecord.id.in_(record_ids)
        ).delete(synchronize_session=False)

        db.session.commit()

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': {
                    'deleted_count': deleted_count,
                    'message': f'成功删除 {deleted_count} 条记录'
                }
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'批量删除失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/records/search', methods=['GET'])
def search_ad_tracking_records():
    """搜索广告记录"""
    try:
        keyword = request.args.get('keyword', '')
        search_type = request.args.get('search_type', 'all')  # all, message, channel, keyword
        limit = request.args.get('limit', 50, type=int)

        if not keyword:
            return jsonify({
                'err_code': 400,
                'err_msg': '请提供搜索关键词'
            }), 400

        query = AdTrackingRecord.query

        # 根据搜索类型构建条件
        if search_type == 'message':
            query = query.filter(
                AdTrackingRecord.message_text.ilike(f'%{keyword}%')
            )
        elif search_type == 'channel':
            query = query.filter(
                AdTrackingRecord.channel_name.ilike(f'%{keyword}%')
            )
        elif search_type == 'keyword':
            query = query.filter(
                AdTrackingRecord.trigger_keyword.ilike(f'%{keyword}%')
            )
        else:  # all
            query = query.filter(
                or_(
                    AdTrackingRecord.message_text.ilike(f'%{keyword}%'),
                    AdTrackingRecord.channel_name.ilike(f'%{keyword}%'),
                    AdTrackingRecord.trigger_keyword.ilike(f'%{keyword}%')
                )
            )

        # 限制结果数量
        results = query.limit(limit).all()

        return jsonify({
            'err_code': 0,
            'payload': {
                'data': [record.to_dict() for record in results],
                'total': len(results)
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'搜索失败: {str(e)}'
        }), 500


@api.route('/ad-tracking/records/export', methods=['GET'])
def export_ad_tracking_records():
    """导出广告记录"""
    try:
        # 获取导出参数
        format_type = request.args.get('format', 'excel')  # excel, csv
        channel_id = request.args.get('channel_id', type=int)
        trigger_keyword = request.args.get('trigger_keyword', '')
        trigger_tag_id = request.args.get('trigger_tag_id', type=int)
        is_processed = request.args.get('is_processed', type=bool)

        # 构建查询
        query = AdTrackingRecord.query

        if channel_id:
            query = query.filter_by(channel_id=channel_id)

        if trigger_keyword:
            query = query.filter(
                AdTrackingRecord.trigger_keyword.ilike(f'%{trigger_keyword}%')
            )

        if trigger_tag_id:
            query = query.filter_by(trigger_tag_id=trigger_tag_id)

        if is_processed is not None:
            query = query.filter_by(is_processed=is_processed)

        # 获取所有记录
        records = query.order_by(desc(AdTrackingRecord.send_time)).all()

        if format_type == 'csv':
            return _export_csv(records)
        else:  # excel
            return _export_excel(records)

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'err_code': 500,
            'err_msg': f'导出失败: {str(e)}'
        }), 500


def _export_csv(records):
    """导出CSV格式"""
    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    headers = [
        '记录ID', '频道ID', '频道名称', '消息ID', '发送者ID',
        '消息内容', '图片URL', '发送时间', '触发关键词',
        '触发标签ID', '处理批次ID', '是否已处理'
    ]
    writer.writerow(headers)

    # 写入数据
    for record in records:
        writer.writerow([
            record.id,
            record.channel_id,
            record.channel_name,
            record.message_id,
            record.sender_id,
            record.message_text or '',
            record.image_url,
            record.send_time.strftime('%Y-%m-%d %H:%M:%S') if record.send_time else '',
            record.trigger_keyword,
            record.trigger_tag_id,
            record.process_batch_id or '',
            '是' if record.is_processed else '否'
        ])

    output.seek(0)

    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=ad_tracking_records.csv'

    return response


def _export_excel(records):
    """导出Excel格式"""
    from io import BytesIO
    import xlsxwriter

    output = BytesIO()

    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('广告记录')

    # 定义列格式
    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'fg_color': '#D7E4BC'
    })

    # 写入表头
    headers = [
        '记录ID', '频道ID', '频道名称', '消息ID', '发送者ID',
        '消息内容', '图片URL', '发送时间', '触发关键词',
        '触发标签ID', '处理批次ID', '是否已处理'
    ]

    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
        worksheet.set_column(col, col, 20)

    # 写入数据
    for row, record in enumerate(records, 1):
        worksheet.write(row, 0, record.id)
        worksheet.write(row, 1, record.channel_id)
        worksheet.write(row, 2, record.channel_name)
        worksheet.write(row, 3, record.message_id)
        worksheet.write(row, 4, record.sender_id)
        worksheet.write(row, 5, record.message_text or '')
        worksheet.write(row, 6, record.image_url)
        worksheet.write(row, 7, record.send_time.strftime('%Y-%m-%d %H:%M:%S') if record.send_time else '')
        worksheet.write(row, 8, record.trigger_keyword)
        worksheet.write(row, 9, record.trigger_tag_id)
        worksheet.write(row, 10, record.process_batch_id or '')
        worksheet.write(row, 11, '已处理' if record.is_processed else '未处理')

    worksheet.set_column(5, 5, 40)  # 消息内容列

    workbook.close()
    output.seek(0)

    from flask import make_response
    response = make_response(output.read())
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename=ad_tracking_records.xlsx'

    return response
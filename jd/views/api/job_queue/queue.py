from flask import request
from jd.views.api import ApiBlueprint
from jd.models.job_queue_log import JobQueueLog
from jd import db
import datetime

queue_bp = ApiBlueprint('job_queue', __name__)


@queue_bp.route('/list', methods=['GET'], need_login=False)
def get_job_queue_list():
    """获取任务队列列表"""
    try:
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 获取筛选参数
        status = request.args.get('status')
        name = request.args.get('name')
        
        # 构建查询
        query = JobQueueLog.query
        
        # 应用筛选条件
        if status is not None:
            try:
                status_int = int(status)
                query = query.filter(JobQueueLog.status == status_int)
            except ValueError:
                pass
                
        if name:
            query = query.filter(JobQueueLog.name.contains(name))
        
        # 按创建时间倒序排列
        query = query.order_by(JobQueueLog.created_at.desc())
        
        # 分页
        pagination = query.paginate(
            page=page, 
            per_page=page_size, 
            error_out=False
        )
        
        # 格式化数据
        items = []
        for job in pagination.items:
            items.append({
                'id': job.id,
                'name': job.name,
                'description': job.description,
                'resource_id': job.resource_id,
                'session_name': job.session_name,
                'status': job.status,
                'result': job.result,
                'created_at': job.created_at.strftime('%Y-%m-%d %H:%M:%S') if job.created_at else None,
                'updated_at': job.updated_at.strftime('%Y-%m-%d %H:%M:%S') if job.updated_at else None
            })
        
        return {
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'items': items,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        }
        
    except Exception as e:
        return {
            'err_code': 1,
            'err_msg': f'获取任务队列列表失败: {str(e)}',
            'payload': {}
        }


@queue_bp.route('/<int:job_id>/complete', methods=['PUT'], need_login=False)
def mark_job_complete(job_id):
    """标记任务为完成"""
    try:
        job = JobQueueLog.query.get(job_id)
        if not job:
            return {
                'err_code': 1,
                'err_msg': '任务不存在',
                'payload': {}
            }
        
        # 更新状态为已完成
        job.status = JobQueueLog.StatusType.FINISHED
        job.updated_at = datetime.datetime.now()
        
        db.session.commit()
        
        return {
            'err_code': 0,
            'err_msg': '任务已标记为完成',
            'payload': {
                'id': job.id,
                'status': job.status,
                'updated_at': job.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'err_code': 1,
            'err_msg': f'标记任务完成失败: {str(e)}',
            'payload': {}
        }


@queue_bp.route('/stats', methods=['GET'])
def get_job_stats():
    """获取任务统计信息"""
    try:
        # 统计各状态任务数量
        stats = {
            'pending': JobQueueLog.query.filter_by(status=JobQueueLog.StatusType.NOT_START).count(),
            'running': JobQueueLog.query.filter_by(status=JobQueueLog.StatusType.RUNNING).count(), 
            'completed': JobQueueLog.query.filter_by(status=JobQueueLog.StatusType.FINISHED).count(),
            'total': JobQueueLog.query.count()
        }
        
        return {
            'err_code': 0,
            'err_msg': '',
            'payload': stats
        }
        
    except Exception as e:
        return {
            'err_code': 1,
            'err_msg': f'获取统计信息失败: {str(e)}',
            'payload': {}
        }
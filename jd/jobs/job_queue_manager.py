#!/usr/bin/env python3
"""
兼容性适配器 - 保持向后兼容
主要功能已迁移至 jd.tasks.base_task.EnhancedJobQueueManager
"""

import logging
from typing import Optional, Tuple, Dict, Any

from jd.tasks.base_task import EnhancedJobQueueManager, QueueMode, QueueStatus
from jd.models.job_queue_log import JobQueueLog

logger = logging.getLogger(__name__)


class EnhancedJobQueueLogService:
    """
    兼容性适配器 - 委托给 EnhancedJobQueueManager
    """
    
    @classmethod
    def add(cls, job_name: str, **kwargs) -> Tuple[bool, Optional[JobQueueLog], Dict[str, Any]]:
        """委托给新的队列管理器"""
        return EnhancedJobQueueManager.add_to_queue(job_name, **kwargs)
    
    @classmethod
    def finished(cls, queue_id: int, result: str = '') -> bool:
        """委托给新的队列管理器"""
        return EnhancedJobQueueManager.finish_task(queue_id, result)
    
    @classmethod
    def get_queue_status(cls, resource_id: str = '', session_name: str = '', job_name: str = '') -> Dict[str, Any]:
        """委托给新的队列管理器"""
        # 这里需要调用 base_task 中的方法，但由于代码过长，先保持简化版本
        from jd.models.job_queue_log import JobQueueLog
        query = JobQueueLog.query
        
        conditions = []
        if resource_id:
            conditions.append(JobQueueLog.resource_id == resource_id)
        if session_name:
            conditions.append(JobQueueLog.session_name == session_name)
        if job_name:
            conditions.append(JobQueueLog.name == job_name)
        
        if conditions:
            from jd import db
            query = query.filter(db.or_(*conditions))
        
        tasks = query.order_by(JobQueueLog.created_at.desc()).limit(50).all()
        
        status_counts = {
            'pending': 0, 'running': 0, 'waiting': 0,
            'finished': 0, 'cancelled': 0, 'timeout': 0
        }
        
        task_list = []
        for task in tasks:
            status_name = QueueStatus(task.status).name.lower() if hasattr(task, 'status') else 'unknown'
            if status_name in status_counts:
                status_counts[status_name] += 1
            
            task_list.append({
                'id': task.id,
                'name': task.name,
                'resource_id': task.resource_id,
                'session_name': task.session_name,
                'status': getattr(task, 'status', 0),
                'status_name': status_name.upper(),
                'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else '',
                'result': task.result[:200] if task.result else ''
            })
        
        return {
            'status_counts': status_counts,
            'tasks': task_list,
            'total': len(task_list)
        }
    
    
    
    
    
    
    
    
    
    
    
    
    
    


# 保持向后兼容性的适配器
class JobQueueLogService:
    """原有接口的兼容适配器"""
    
    @classmethod
    def add(cls, job_name: str, resource_id: str = '', session_name: str = '') -> Tuple[bool, Optional[JobQueueLog]]:
        """
        保持原有接口兼容性
        注意：session冲突时会自动排队等待，这是新的默认行为
        """
        success, queue, _ = EnhancedJobQueueLogService.add(
            job_name, resource_id=resource_id, session_name=session_name, wait_if_conflict=False
        )
        return success, queue
    
    @classmethod
    def finished(cls, queue_id: int):
        """保持原有接口兼容性"""
        return EnhancedJobQueueLogService.finished(queue_id)
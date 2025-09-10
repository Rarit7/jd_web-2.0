import asyncio
import logging
import time
from functools import wraps
from typing import Optional

from jd import db
from jd.models.job_queue_log import JobQueueLog
from jd.tasks.base_task import QueueStatus

logger = logging.getLogger(__name__)


def with_session_lock(max_retries=5, check_interval=60):
    """
    为直接的 Celery 任务添加简单的 session 锁检查装饰器
    
    Args:
        max_retries: 最大重试次数（默认5次）
        check_interval: 检查间隔（秒，默认60秒）
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 提取 sessionname 参数
            sessionname = None
            if 'sessionname' in kwargs:
                sessionname = kwargs['sessionname']
            elif len(args) >= 5 and isinstance(args[4], str):  # 假设 sessionname 是第5个参数
                sessionname = args[4]
            
            if not sessionname:
                # 没有 session 参数，直接执行
                return await func(*args, **kwargs)
            
            # 使用固定间隔策略检查 session 是否被占用
            for check_count in range(max_retries + 1):  # +1 是为了包含第0次检查
                running_task = JobQueueLog.query.filter_by(
                    session_name=sessionname,
                    status=QueueStatus.RUNNING.value
                ).first()
                
                if not running_task:
                    # session 可用，执行任务
                    if check_count > 0:
                        total_wait_time = check_count * check_interval
                        logger.info(f"Session {sessionname} 可用，开始执行任务 (等待了 {total_wait_time/60:.1f}分钟)")
                    else:
                        logger.debug(f"Session {sessionname} 可用，开始执行任务")
                    return await func(*args, **kwargs)
                
                # 如果还没有达到最大重试次数，等待后重试
                if check_count < max_retries:
                    if check_count == 0:
                        logger.info(f"Session {sessionname} 被任务 {running_task.name} 占用，等待 {check_interval}s 后重试")
                    else:
                        elapsed_minutes = check_count * check_interval / 60
                        logger.debug(f"Session {sessionname} 仍被占用，继续等待... (已等待 {elapsed_minutes:.1f}分钟)")
                    
                    await asyncio.sleep(check_interval)
            
            # 超过最大重试次数返回错误
            total_wait_time = max_retries * check_interval
            error_msg = f"等待 Session {sessionname} 超时（{max_retries}次重试，共{total_wait_time/60:.0f}分钟），任务取消"
            logger.error(error_msg)
            return error_msg
            
        return wrapper
    return decorator
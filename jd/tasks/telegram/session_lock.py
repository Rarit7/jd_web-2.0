import asyncio
import logging
import time
from functools import wraps
from typing import Optional

from jd import db
from jd.models.job_queue_log import JobQueueLog
from jd.tasks.base_task import QueueStatus

logger = logging.getLogger(__name__)


def with_session_lock(max_wait_seconds=300, base_check_interval=10):
    """
    为直接的 Celery 任务添加简单的 session 锁检查装饰器
    
    Args:
        max_wait_seconds: 最大等待时间（秒）
        base_check_interval: 基础检查间隔（秒），将使用指数退避策略
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
            
            # 使用指数退避策略检查 session 是否被占用
            wait_time = 0
            check_count = 0
            
            while wait_time < max_wait_seconds:
                running_task = JobQueueLog.query.filter_by(
                    session_name=sessionname,
                    status=QueueStatus.RUNNING.value
                ).first()
                
                if not running_task:
                    # session 可用，执行任务
                    if check_count > 0:
                        logger.info(f"Session {sessionname} 可用，开始执行任务 (等待了 {wait_time}s)")
                    else:
                        logger.debug(f"Session {sessionname} 可用，开始执行任务")
                    return await func(*args, **kwargs)
                
                # 计算下一次检查的等待时间（指数退避，但有上限）
                current_interval = min(base_check_interval * (1.5 ** check_count), 60)  # 最大60秒间隔
                
                if check_count == 0:
                    logger.info(f"Session {sessionname} 被任务 {running_task.name} 占用，等待 {current_interval:.1f}s 后重试")
                elif check_count % 3 == 0:  # 每3次检查打印一次日志
                    logger.debug(f"Session {sessionname} 仍被占用，继续等待... (已等待 {wait_time}s)")
                
                await asyncio.sleep(current_interval)
                wait_time += current_interval
                check_count += 1
            
            # 超时返回错误
            error_msg = f"等待 Session {sessionname} 超时（{max_wait_seconds}s，检查了{check_count}次），任务取消"
            logger.error(error_msg)
            return error_msg
            
        return wrapper
    return decorator
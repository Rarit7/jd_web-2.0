import logging
from typing import Dict, Any

from jd.jobs.tg_chat_history import ExsitedGroupHistoryFetcher
from jd.tasks.base_task import AsyncBaseTask
from jCelery import celery

logger = logging.getLogger(__name__)


class TgHistoryTask(AsyncBaseTask):
    """Telegram群组聊天历史获取任务"""
    
    def __init__(self, session_name: str = None):
        # 这个任务是全局性的历史获取，不针对特定资源
        # 使用虚拟的全局session名称，因为我们会自定义冲突检测逻辑
        super().__init__(resource_id='', session_id='global_history')
        # 保存实际要使用的session名称，用于实际的Telegram连接
        self.actual_session_name = session_name or 'default2'
        # 设置冲突处理策略：当有任何Telegram任务运行时都要排队等待
        self.wait_if_conflict = True
    
    def get_job_name(self) -> str:
        return 'update_group_history'
    
    def start_task(self) -> Dict[str, Any]:
        """
        重写启动任务方法，添加自定义的全局Telegram任务冲突检测和等待机制
        """
        import time
        import asyncio
        
        logger.info(f'启动任务: {self.job_name}')
        
        # 如果设置了等待冲突，实现主动等待逻辑
        if self.wait_if_conflict:
            max_wait_minutes = 30  # 最多等待30分钟
            check_interval = 60    # 每60秒检查一次
            total_wait_time = 0
            
            while total_wait_time < max_wait_minutes * 60:
                telegram_conflict = self._check_telegram_tasks_conflict()
                if not telegram_conflict['has_conflict']:
                    # 没有冲突，可以执行
                    if total_wait_time > 0:
                        logger.info(f'等待 {total_wait_time/60:.1f} 分钟后，Telegram任务队列已清空，开始执行')
                    break
                
                if total_wait_time == 0:
                    logger.info(f'检测到Telegram任务冲突: {telegram_conflict["message"]}，开始等待')
                elif total_wait_time % (5 * 60) == 0:  # 每5分钟打印一次状态
                    logger.info(f'继续等待Telegram任务完成... (已等待 {total_wait_time/60:.1f} 分钟)')
                
                time.sleep(check_interval)
                total_wait_time += check_interval
            
            # 检查是否超时
            if total_wait_time >= max_wait_minutes * 60:
                final_conflict = self._check_telegram_tasks_conflict()
                if final_conflict['has_conflict']:
                    error_msg = f'等待Telegram任务完成超时 ({max_wait_minutes}分钟)，当前冲突: {final_conflict["message"]}'
                    logger.error(error_msg)
                    return {
                        'err_code': 1,
                        'err_msg': error_msg,
                        'task_timeout': True,
                        'conflict_info': final_conflict
                    }
        else:
            # 不等待，直接检查冲突
            telegram_conflict = self._check_telegram_tasks_conflict()
            if telegram_conflict['has_conflict']:
                logger.warning(f'Telegram任务冲突: {telegram_conflict["message"]}，跳过执行')
                return {
                    'err_code': 1,
                    'err_msg': '存在运行中的Telegram任务，TgHistoryTask跳过执行',
                    'task_skipped': True,
                    'conflict_info': telegram_conflict
                }
        
        # 没有冲突，正常执行任务
        # 使用实际的session名称执行任务
        original_session_id = self.session_id
        self.session_id = self.actual_session_name
        
        try:
            return super().start_task()
        finally:
            self.session_id = original_session_id
    
    def _check_telegram_tasks_conflict(self) -> Dict[str, Any]:
        """
        检查是否有任何Telegram相关任务在运行
        
        Returns:
            Dict: 包含冲突信息的字典
        """
        from jd import db
        from jd.models.job_queue_log import JobQueueLog
        from jd.tasks.base_task import QueueStatus
        
        # 定义Telegram相关的任务名称模式
        telegram_task_patterns = [
            'fetch_new_group_history',
            'update_group_history', 
            'fetch_account_group_info',
            'tg_',
            'telegram'
        ]
        
        # 查找所有运行中的任务
        running_tasks = JobQueueLog.query.filter_by(status=QueueStatus.RUNNING.value).all()
        
        for task in running_tasks:
            # 跳过自己（如果已经在运行）
            if task.name == self.get_job_name():
                continue
                
            # 检查是否是Telegram相关任务
            task_name_lower = task.name.lower()
            is_telegram_task = any(pattern.lower() in task_name_lower for pattern in telegram_task_patterns)
            
            if is_telegram_task:
                return {
                    'has_conflict': True,
                    'type': 'telegram_global',
                    'task': task,
                    'message': f'Telegram任务 {task.name} (ID:{task.id}) 正在运行'
                }
        
        return {'has_conflict': False}
    
    def generate_result_summary(self, result: Dict[str, Any]) -> str:
        """生成update_group_history任务的友好结果摘要"""
        if not result:
            return "任务完成，无结果数据"
            
        err_code = result.get('err_code', 0)
        if err_code != 0:
            return f"任务失败: {result.get('err_msg', '未知错误')}"
        
        payload = result.get('payload', {})
        if not payload:
            return "任务成功"
        
        # 提取统计信息
        stats = payload.get('statistics', {})
        duration = payload.get('duration_seconds', 0)
        
        # 格式化持续时间
        if duration > 0:
            if duration >= 60:
                duration_text = f"{duration/60:.1f}分钟"
            else:
                duration_text = f"{duration:.1f}秒"
        else:
            duration_text = "未知"
        
        # 提取群组和消息统计
        total_groups = stats.get('total_groups', 0)
        success_count = stats.get('success_count', 0)
        error_count = stats.get('error_count', 0)
        
        # 计算新增消息数（需要从processed_groups中提取）
        processed_groups = stats.get('processed_groups', [])
        total_new_messages = 0
        for group in processed_groups:
            if isinstance(group, dict):
                total_new_messages += group.get('new_messages_count', 0)
        
        # 构建结果摘要
        if total_groups > 0:
            result_parts = [f"任务成功，处理群 {success_count}/{total_groups} 个"]
            
            if total_new_messages > 0:
                result_parts.append(f"新增 {total_new_messages} 条消息记录")
            else:
                result_parts.append("无新消息")
            
            if error_count > 0:
                result_parts.append(f"{error_count} 个群组处理失败")
                
            result_parts.append(f"耗时 {duration_text}")
            
            return "，".join(result_parts)
        else:
            return f"任务成功，无群组处理，耗时 {duration_text}"
    
    async def execute_async_task(self) -> Dict[str, Any]:
        """执行Telegram历史获取任务"""
        import datetime
        from zoneinfo import ZoneInfo
        
        start_time = datetime.datetime.now(ZoneInfo('UTC'))
        logger.info('开始Telegram聊天实时获取任务...')
        
        fetcher = ExsitedGroupHistoryFetcher()
        try:
            # process_all_groups会根据每个群组自动选择合适的session并初始化
            # 执行历史获取任务，现在返回详细统计信息
            success, stats = await fetcher.process_all_groups()
            end_time = datetime.datetime.now(ZoneInfo('UTC'))
            
            if success:
                logger.info('Telegram聊天历史获取任务完成')
                return {
                    'err_code': 0,
                    'err_msg': '',
                    'payload': {
                        'status': 'completed',
                        'success': True,
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat(),
                        'duration_seconds': (end_time - start_time).total_seconds(),
                        'session_name': self.session_id,
                        'statistics': stats
                    }
                }
            else:
                logger.warning('Telegram聊天历史获取任务未成功完成')
                return {
                    'err_code': 1,
                    'err_msg': 'Telegram聊天历史获取任务未成功完成',
                    'payload': {
                        'status': 'failed',
                        'success': False,
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat(),
                        'duration_seconds': (end_time - start_time).total_seconds(),
                        'session_name': self.session_id,
                        'statistics': stats
                    }
                }
                
        except Exception as e:
            end_time = datetime.datetime.now(ZoneInfo('UTC'))
            error_msg = f'异步任务执行错误: {e}'
            logger.error(error_msg)
            return {
                'err_code': 1,
                'err_msg': error_msg,
                'payload': {
                    'status': 'error',
                    'success': False,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': (end_time - start_time).total_seconds(),
                    'session_name': self.session_id,
                    'exception': str(e),
                    'statistics': None
                }
            }
        finally:
            # 确保Telegram服务被关闭
            if fetcher:
                await fetcher.close_telegram_service()


@celery.task
def fetch_tg_history_job(session_name: str = None):
    """使用重构后的ExsitedGroupHistoryFetcher获取Telegram群组聊天历史
    
    Args:
        session_name: 可选的session名称，用于区分不同的历史获取任务
    """
    task = TgHistoryTask(session_name=session_name)
    return task.start_task()



if __name__ == '__main__':
    # 直接运行脚本进行测试
    from jd import app
    app.ready(db_switch=True, web_switch=False, worker_switch=True)
    fetch_tg_history_job()

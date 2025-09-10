import datetime
import logging
from typing import Dict, Any
from zoneinfo import ZoneInfo

from jCelery import celery
from jd.jobs.tg_new_history import NewJoinedGroupHistoryFetcher
from jd.jobs.tg_group_info import TgGroupInfoManager
from jd.tasks.base_task import AsyncBaseTask, QueueStatus

logger = logging.getLogger(__name__)

class NewGroupHistoryTask(AsyncBaseTask):
    """新加入群组历史获取任务"""
    
    def __init__(self, group_name: str, chat_id: int, session_name: str = None):
        super().__init__(resource_id=str(chat_id), session_id=session_name)
        self.group_name = group_name
        self.chat_id = chat_id
        
        # 设置冲突处理策略：session冲突时排队等待，避免session争抢
        self.wait_if_conflict = True
    
    def get_job_name(self) -> str:
        return 'fetch_new_group_history'
    
    def _check_custom_conflict(self) -> Dict[str, Any]:
        """
        自定义冲突检查逻辑：
        1. 如果存在相同chat_id的任务在运行，直接标记为完成
        2. 如果不同chat_id但相同session，根据session决定是排队还是立即执行
        
        Returns:
            Dict: 包含冲突处理结果的字典
        """
        from jd import db
        from jd.models.job_queue_log import JobQueueLog
        
        # 检查相同chat_id的任务
        same_chat_task = JobQueueLog.query.filter_by(
            name=self.get_job_name(),
            resource_id=str(self.chat_id),
            status=QueueStatus.RUNNING.value
        ).first()
        
        if same_chat_task:
            # 相同chat_id的任务在运行，直接标记为完成
            logger.info(f'检测到相同chat_id {self.chat_id} 的任务正在运行，直接返回完成状态')
            return {
                'action': 'skip',
                'reason': 'same_chat_id',
                'message': f'群组 {self.chat_id} 的历史获取任务已在运行中',
                'result': {
                    'err_code': 0,
                    'err_msg': '',
                    'payload': {
                        'success': True,
                        'message': f'群组 {self.group_name} (chat_id: {self.chat_id}) 历史获取任务已在运行中，跳过重复执行',
                        'skipped': True,
                        'chat_id': self.chat_id,
                        'group_name': self.group_name,
                        'session_name': self.session_id
                    }
                }
            }
        
        # 检查相同session的任务（不同chat_id）
        if self.session_id:
            same_session_task = JobQueueLog.query.filter(
                JobQueueLog.name == self.get_job_name(),
                JobQueueLog.session_name == self.session_id,
                JobQueueLog.resource_id != str(self.chat_id),
                JobQueueLog.status == QueueStatus.RUNNING.value
            ).first()
            
            if same_session_task:
                # 相同session但不同chat_id，决定是否排队
                # 默认策略：如果是同一个session，则排队等待避免session冲突
                logger.info(f'检测到相同session {self.session_id} 的任务正在运行（chat_id: {same_session_task.resource_id}），将排队等待')
                return {
                    'action': 'queue',
                    'reason': 'same_session',
                    'message': f'Session {self.session_id} 有任务在运行，排队等待'
                }
        
        # 无冲突，可以立即执行
        return {
            'action': 'execute',
            'reason': 'no_conflict',
            'message': '无冲突，立即执行'
        }
    
    def start_task(self) -> Dict[str, Any]:
        """
        重写start_task方法以实现自定义冲突处理逻辑
        """
        logger.info(f'启动任务: {self.job_name}')
        
        # 先进行自定义冲突检查
        conflict_check = self._check_custom_conflict()
        
        if conflict_check['action'] == 'skip':
            # 直接返回跳过结果，不创建队列记录
            return conflict_check['result']
        elif conflict_check['action'] == 'queue':
            # 设置为排队模式
            self.wait_if_conflict = True
        else:
            # 立即执行模式
            self.wait_if_conflict = False
        
        # 调用父类的start_task方法
        return super().start_task()
    
    async def execute_async_task(self) -> Dict[str, Any]:
        """执行新群组历史获取任务"""
        logger.info(f'手动开启指定群组历史记录爬取: {self.group_name} (chat_id: {self.chat_id})')
        
        # 获取群组关联的session列表
        session_list = TgGroupInfoManager.get_group_user_session(self.chat_id)
        
        if not session_list:
            # 如果没有关联的session，使用默认session
            session_list = [self.session_id] if self.session_id else ['']
            logger.warning(f'群组 {self.group_name} 没有关联的session，使用默认session或指定session')
        
        logger.info(f'群组 {self.chat_id} 可用session列表: {session_list}')
        
        fetcher = NewJoinedGroupHistoryFetcher()
        
        # 使用session列表初始化，让init_tg_with_retry自动处理重试逻辑
        try:
            init_success = await fetcher.init_telegram_service(session_list)
            if not init_success:
                error_msg = f'所有session初始化失败: {session_list}'
                logger.error(error_msg)
                return {
                    'err_code': 1,
                    'err_msg': error_msg,
                    'payload': {
                        'success': False,
                        'chat_id': self.chat_id,
                        'attempted_sessions': session_list
                    }
                }
            else:
                # 更新实际使用的session名称
                used_session = self.session_id or (session_list[0] if session_list else 'default')
                self.update_queue_log(session_name=used_session)
        except Exception as e:
            error_msg = f'初始化Telegram服务时发生错误: {e}'
            logger.error(error_msg)
            return {
                'err_code': 1,
                'err_msg': error_msg,
                'payload': {
                    'success': False,
                    'chat_id': self.chat_id
                }
            }
        
        try:
            # Process specific group
            async with fetcher.tg.client:
                success = await fetcher.process_specific_group(self.group_name, self.chat_id)
            
            if success:
                results = {
                    'err_code': 0,
                    'err_msg': '',
                    'payload': {
                        'success': True,
                        'group_name': self.group_name,
                        'chat_id': self.chat_id,
                        'used_session': used_session,
                        'attempts': 1,
                        'start_time': datetime.datetime.now(ZoneInfo('UTC')).isoformat(),
                        'end_time': datetime.datetime.now(ZoneInfo('UTC')).isoformat()
                    }
                }
                logger.info(f'群组 {self.group_name} 历史记录回溯成功，使用session: {used_session}')
                return results
            else:
                error_msg = f'获取群组 {self.group_name} (chat_id: {self.chat_id}) 聊天记录失败'
                logger.warning(error_msg)
                return {
                    'err_code': 1,
                    'err_msg': error_msg,
                    'payload': {
                        'success': False,
                        'group_name': self.group_name,
                        'chat_id': self.chat_id,
                        'used_session': used_session
                    }
                }
                    
        except Exception as e:
            error_msg = f'处理群组 (chat_id: {self.chat_id}) 时发生错误: {e}'
            logger.error(error_msg)
            return {
                'err_code': 1,
                'err_msg': error_msg,
                'payload': {
                    'success': False,
                    'chat_id': self.chat_id,
                    'exception': str(e)
                }
            }
        finally:
            # 关闭Telegram服务
            try:
                await fetcher.close_telegram_service()
            except Exception as e:
                logger.error(f'关闭 Telegram 服务时发生错误: {e}')


def start_group_history_fetch(group_name: str, chat_id: int, session_name: str = None) -> Dict[str, Any]:
    """
    启动群组历史获取任务（使用改进的任务队列管理）
    
    此函数提供同步调用接口，内部使用Celery异步任务
    """
    # 验证必需参数
    if not group_name or not chat_id:
        return {
            'err_code': 1,
            'err_msg': '缺少必需参数：group_name 和 chat_id 不能为空',
        }
    
    try:
        # 使用改进的任务队列管理触发Celery任务
        result = run_new_group_history_fetch.delay(group_name, chat_id, session_name)
        
        return {
            'err_code': 0,
            'err_msg': '',
            'payload': {
                'result': str(result),
                'message': f'群组 {group_name} 的历史获取任务已启动（使用改进的队列管理）',
                'chat_id': chat_id,
                'session_name': session_name
            }
        }
    except Exception as e:
        return {
            'err_code': 1, 
            'err_msg': f'启动历史获取任务失败: {str(e)}',
            'chat_id': chat_id,
            'group_name': group_name
        }

@celery.task
def run_new_group_history_fetch(group_name: str, chat_id: int, session_name: str = None) -> Dict[str, Any]:
    """
    执行新群组历史获取任务（使用改进的任务队列管理）
    
    冲突处理策略：
    1. 相同 chat_id 的任务在运行 → 直接返回完成状态（避免重复处理）
    2. 相同 session_name 但不同 chat_id → 排队等待（避免session冲突）
    3. 不同 chat_id 且不同 session_name → 立即执行（并行处理）
    
    Args:
        group_name: 群组名称
        chat_id: 群组chat_id
        session_name: TG会话名称（可选）
        
    Returns:
        Dict[str, Any]: 任务执行结果
        
    Examples:
        # 获取群组历史
        result = run_new_group_history_fetch('GroupName', -1001234567890, 'session1')
        
        # 并行处理不同群组和session
        result1 = run_new_group_history_fetch('Group1', -1001234567890, 'session1')
        result2 = run_new_group_history_fetch('Group2', -1001234567891, 'session2')  # 并行执行
        
        # 相同chat_id会被跳过
        result3 = run_new_group_history_fetch('Group1', -1001234567890, 'session2')  # 如果result1还在运行，会跳过
        
        # 相同session会排队
        result4 = run_new_group_history_fetch('Group3', -1001234567892, 'session1')  # 会等待result1完成
    """
    task = NewGroupHistoryTask(group_name, chat_id, session_name)
    return task.start_task()


# 为了向后兼容，增加一个更直观的接口
@celery.task
def fetch_new_joined_group_history(chat_id: int, session_name: str, group_name: str = None) -> Dict[str, Any]:
    """
    获取新加入群组的历史记录（简化接口）
    
    Args:
        chat_id: 群组chat_id
        session_name: TG会话名称
        group_name: 群组名称（可选，用于日志显示）
        
    Returns:
        Dict[str, Any]: 任务执行结果
    """
    display_name = group_name or f'Group_{chat_id}'
    return run_new_group_history_fetch(display_name, chat_id, session_name)


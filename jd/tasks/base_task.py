import logging
import asyncio
import datetime
import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List

from jd import db
from jd.models.job_queue_log import JobQueueLog
from config import TASK_DEFAULT_TIMEOUTS, TASK_MAX_WAIT_TIME

logger = logging.getLogger(__name__)


class QueueMode(Enum):
    """队列模式枚举"""
    IMMEDIATE_RETURN = "immediate"  # 立即返回模式（原有行为）
    WAIT_IN_QUEUE = "queue"        # 排队等待模式


class QueueStatus(Enum):
    """增强的队列状态"""
    PENDING = 0      # 待处理（原 NOT_START）
    RUNNING = 1      # 运行中（原 RUNNING）
    FINISHED = 2     # 已完成（原 FINISHED）
    WAITING = 3      # 等待中（新增）
    CANCELLED = 4    # 已取消（新增）
    TIMEOUT = 5      # 超时（新增）


class EnhancedJobQueueManager:
    """增强版任务队列管理器（集成到BaseTask中）"""
    
    
    @classmethod
    def add_to_queue(cls, job_name: str, **kwargs) -> Tuple[bool, Optional[JobQueueLog], Dict[str, Any]]:
        """添加新的任务队列记录（增强版）"""
        
        # 提取标准参数
        resource_id = kwargs.get('resource_id', '') or kwargs.get('chat_id', '') or kwargs.get('account_id', '') or kwargs.get('file_id', '') or kwargs.get('user_id', '') or kwargs.get('batch_id', '')
        session_name = kwargs.get('session_name', '')
        wait_if_conflict = kwargs.get('wait_if_conflict', False)
        priority = kwargs.get('priority', 0)
        timeout_seconds = kwargs.get('timeout_seconds', None)
        
        extra_info = {
            'queue_position': 0,
            'estimated_wait_time': 0,
            'conflict_type': None,
            'mode': QueueMode.WAIT_IN_QUEUE.value if wait_if_conflict else QueueMode.IMMEDIATE_RETURN.value
        }
        
        # 清理超时任务
        cls._cleanup_timeout_tasks()
        
        # 检查资源冲突
        conflict_info = cls._check_conflicts(job_name, resource_id, session_name)
        
        if conflict_info['has_conflict']:
            extra_info['conflict_type'] = conflict_info['type']
            
            # 优先遵循wait_if_conflict的设置
            should_wait = wait_if_conflict
            
            if not should_wait:
                # 立即返回模式：直接返回失败
                logger.warning(f'任务冲突 - {conflict_info["message"]}，立即返回')
                return False, None, extra_info
            else:
                # 排队等待模式：创建等待队列
                logger.info(f'任务冲突 - {conflict_info["message"]}，加入等待队列')
                return cls._create_waiting_task(
                    job_name, resource_id, session_name, priority, 
                    timeout_seconds, conflict_info, extra_info, kwargs
                )
        
        # 无冲突，直接创建运行任务
        return cls._create_running_task(
            job_name, resource_id, session_name, priority, 
            timeout_seconds, extra_info, kwargs
        )
    
    @classmethod
    def _check_conflicts(cls, job_name: str, resource_id: str, session_name: str) -> Dict[str, Any]:
        """检查任务冲突"""
        
        # 检查资源ID冲突
        if resource_id:
            running_resource_task = JobQueueLog.query.filter_by(
                resource_id=resource_id,
                status=QueueStatus.RUNNING.value
            ).first()
            if running_resource_task:
                resource_type = cls._get_resource_type_display(job_name, resource_id)
                return {
                    'has_conflict': True,
                    'type': 'resource',
                    'task': running_resource_task,
                    'message': f'{resource_type} {resource_id} 已有正在运行的任务: {running_resource_task.name}'
                }
        
        # 检查Session冲突
        if session_name:
            running_session_task = JobQueueLog.query.filter_by(
                session_name=session_name,
                status=QueueStatus.RUNNING.value
            ).first()
            if running_session_task:
                return {
                    'has_conflict': True,
                    'type': 'session',
                    'task': running_session_task,
                    'message': f'Session {session_name} 已有正在运行的任务: {running_session_task.name}'
                }
        
        return {'has_conflict': False}
    
    @classmethod
    def _get_resource_type_display(cls, job_name: str, resource_id: str) -> str:
        """根据任务名称智能显示资源类型"""
        if 'tg' in job_name.lower() or 'telegram' in job_name.lower() or 'group_history' in job_name:
            return 'chat_id'
        elif 'account' in job_name.lower():
            return 'account_id'
        elif 'file' in job_name.lower() or 'download' in job_name.lower():
            return 'file_id'
        elif 'batch' in job_name.lower() or 'import' in job_name.lower():
            return 'batch_id'
        elif 'user' in job_name.lower():
            return 'user_id'
        else:
            return 'resource_id'
    
    @classmethod
    def _create_waiting_task(cls, job_name: str, resource_id: str, session_name: str,
                           priority: int, timeout_seconds: Optional[int],
                           conflict_info: Dict, extra_info: Dict, kwargs: Dict) -> Tuple[bool, JobQueueLog, Dict]:
        """创建等待中的任务"""
        
        # 计算队列位置和预估等待时间
        queue_position = cls._calculate_queue_position(job_name, resource_id, session_name, priority)
        estimated_wait = cls._estimate_wait_time(conflict_info['task'], queue_position)
        
        extra_info.update({
            'queue_position': queue_position,
            'estimated_wait_time': estimated_wait
        })
        
        # 检查是否超过最大等待时间
        if estimated_wait > TASK_MAX_WAIT_TIME:
            logger.warning(f'预估等待时间 {estimated_wait}秒 超过最大限制 {TASK_MAX_WAIT_TIME}秒')
            return False, None, extra_info
        
        # 创建等待任务
        description = cls._generate_job_description(job_name, resource_id, session_name)
        
        # 分离扩展参数
        excluded_fields = ['resource_id', 'chat_id', 'account_id', 'file_id', 'user_id', 'batch_id', 
                          'session_name', 'wait_if_conflict', 'priority', 'timeout_seconds']
        extra_params = {k: v for k, v in kwargs.items() if k not in excluded_fields}
        
        waiting_task = JobQueueLog(
            name=job_name,
            description=f'{description} [等待队列位置: {queue_position}]',
            resource_id=resource_id,
            session_name=session_name,
            status=QueueStatus.WAITING.value,
            priority=priority,
            timeout_at=datetime.datetime.now() + datetime.timedelta(
                seconds=timeout_seconds or TASK_DEFAULT_TIMEOUTS.get(job_name, TASK_DEFAULT_TIMEOUTS['default'])
            ),
            extra_params=json.dumps(extra_params) if extra_params else ''
        )
        
        db.session.add(waiting_task)
        db.session.flush()
        
        logger.info(f'创建等待任务: {job_name}, 队列位置: {queue_position}, '
                   f'预估等待: {estimated_wait}秒, queue_id: {waiting_task.id}')
        
        return True, waiting_task, extra_info
    
    @classmethod
    def _create_running_task(cls, job_name: str, resource_id: str, session_name: str,
                           priority: int, timeout_seconds: Optional[int],
                           extra_info: Dict, kwargs: Dict) -> Tuple[bool, JobQueueLog, Dict]:
        """创建正在运行的任务"""
        
        description = cls._generate_job_description(job_name, resource_id, session_name)
        
        # 分离扩展参数
        excluded_fields = ['resource_id', 'chat_id', 'account_id', 'file_id', 'user_id', 'batch_id', 
                          'session_name', 'wait_if_conflict', 'priority', 'timeout_seconds']
        extra_params = {k: v for k, v in kwargs.items() if k not in excluded_fields}
        
        running_task = JobQueueLog(
            name=job_name,
            description=description,
            resource_id=resource_id,
            session_name=session_name,
            status=QueueStatus.RUNNING.value,
            priority=priority,
            timeout_at=datetime.datetime.now() + datetime.timedelta(
                seconds=timeout_seconds or TASK_DEFAULT_TIMEOUTS.get(job_name, TASK_DEFAULT_TIMEOUTS['default'])
            ),
            extra_params=json.dumps(extra_params) if extra_params else ''
        )
        
        db.session.add(running_task)
        db.session.flush()
        
        logger.info(f'创建运行任务: {job_name}, resource_id: {resource_id}, '
                   f'session: {session_name}, queue_id: {running_task.id}')
        
        return True, running_task, extra_info
    
    @classmethod
    def _calculate_queue_position(cls, job_name: str, resource_id: str, 
                                session_name: str, priority: int) -> int:
        """计算队列位置"""
        
        waiting_count = 0
        
        if resource_id:
            waiting_count += JobQueueLog.query.filter_by(
                resource_id=resource_id,
                status=QueueStatus.WAITING.value
            ).count()
        
        if session_name:
            session_waiting = JobQueueLog.query.filter_by(
                session_name=session_name,
                status=QueueStatus.WAITING.value
            ).count()
            waiting_count = max(waiting_count, session_waiting)
        
        # 考虑优先级
        higher_priority_count = JobQueueLog.query.filter(
            JobQueueLog.name == job_name,
            JobQueueLog.status == QueueStatus.WAITING.value,
            JobQueueLog.priority > priority
        ).count()
        
        return waiting_count + higher_priority_count + 1
    
    @classmethod
    def _estimate_wait_time(cls, blocking_task: JobQueueLog, queue_position: int) -> int:
        """预估等待时间"""
        
        task_runtime = (datetime.datetime.now() - blocking_task.created_at).total_seconds()
        job_avg_time = TASK_DEFAULT_TIMEOUTS.get(blocking_task.name, TASK_DEFAULT_TIMEOUTS['default']) // 2
        
        remaining_time = max(job_avg_time - task_runtime, 60)  # 至少1分钟
        queue_wait_time = remaining_time + (queue_position - 1) * job_avg_time
        
        return int(queue_wait_time)
    
    @classmethod
    def finish_task(cls, queue_id: int, result: str = '') -> bool:
        """完成任务并自动处理等待队列"""
        try:
            updated_count = JobQueueLog.query.filter_by(
                id=queue_id,
                status=QueueStatus.RUNNING.value
            ).update({
                'status': QueueStatus.FINISHED.value,
                'result': result,
                'updated_at': datetime.datetime.now()
            })
            
            if updated_count > 0:
                finished_task = JobQueueLog.query.get(queue_id)
                logger.info(f'任务队列 {queue_id} 已标记为完成')
                
                # 自动处理等待队列
                cls._process_waiting_queue(finished_task)
                
                db.session.commit()
                return True
            else:
                logger.warning(f'任务队列 {queue_id} 未找到或状态不是RUNNING')
                return False
                
        except Exception as e:
            logger.error(f'标记任务完成失败: {e}')
            db.session.rollback()
            raise
    
    @classmethod
    def _process_waiting_queue(cls, finished_task: JobQueueLog):
        """处理等待队列，启动下一个可执行的任务"""
        
        # 查找可以启动的等待任务
        next_tasks = cls._find_next_executable_tasks(finished_task)
        
        for task in next_tasks:
            JobQueueLog.query.filter_by(id=task.id).update({
                'status': QueueStatus.RUNNING.value,
                'updated_at': datetime.datetime.now(),
                'description': task.description.replace('[等待队列位置: ', '[已启动 原位置: ')
            })
            
            logger.info(f'启动等待任务: {task.name} (queue_id: {task.id})')
    
    @classmethod
    def _find_next_executable_tasks(cls, finished_task: JobQueueLog) -> List[JobQueueLog]:
        """查找下一个可执行的等待任务"""
        
        executable_tasks = []
        
        # 按优先级和创建时间排序查找等待任务
        waiting_tasks = JobQueueLog.query.filter_by(
            status=QueueStatus.WAITING.value
        ).order_by(
            JobQueueLog.priority.desc(),
            JobQueueLog.created_at.asc()
        ).all()
        
        for task in waiting_tasks:
            if cls._can_task_start(task, finished_task):
                executable_tasks.append(task)
                break  # 每次只启动一个任务，避免资源冲突
        
        return executable_tasks
    
    @classmethod
    def _can_task_start(cls, waiting_task: JobQueueLog, finished_task: JobQueueLog) -> bool:
        """判断等待任务是否可以启动"""
        
        # 检查资源释放
        if (waiting_task.resource_id and 
            waiting_task.resource_id == finished_task.resource_id):
            return True
        
        # 检查session释放
        if (waiting_task.session_name and 
            waiting_task.session_name == finished_task.session_name):
            return True
        
        # 检查同名任务释放
        if waiting_task.name == finished_task.name:
            return True
        
        return False
    
    @classmethod
    def _cleanup_timeout_tasks(cls):
        """清理超时任务"""
        
        now = datetime.datetime.now()
        
        # 查找超时的运行任务
        timeout_running_tasks = JobQueueLog.query.filter(
            JobQueueLog.status == QueueStatus.RUNNING.value,
            JobQueueLog.timeout_at < now
        ).all()
        
        for task in timeout_running_tasks:
            logger.warning(f'任务超时，自动标记完成: {task.name} (queue_id: {task.id})')
            JobQueueLog.query.filter_by(id=task.id).update({
                'status': QueueStatus.TIMEOUT.value,
                'updated_at': now,
                'result': f'任务超时自动结束 (超时时间: {task.timeout_at})'
            })
        
        # 查找超时的等待任务
        timeout_waiting_tasks = JobQueueLog.query.filter(
            JobQueueLog.status == QueueStatus.WAITING.value,
            JobQueueLog.timeout_at < now
        ).all()
        
        for task in timeout_waiting_tasks:
            logger.warning(f'等待任务超时，自动取消: {task.name} (queue_id: {task.id})')
            JobQueueLog.query.filter_by(id=task.id).update({
                'status': QueueStatus.CANCELLED.value,
                'updated_at': now,
                'result': f'等待超时自动取消 (超时时间: {task.timeout_at})'
            })
        
        if timeout_running_tasks or timeout_waiting_tasks:
            db.session.commit()
    
    @classmethod
    def _generate_job_description(cls, job_name: str, resource_id: str = '', session_name: str = '') -> str:
        """生成任务描述"""
        from jd import app
        
        info_parts = []
        if resource_id:
            info_parts.append(f'资源:{resource_id}')
        if session_name:
            info_parts.append(f'连接:{session_name}')
        
        info_str = '|'.join(info_parts) if info_parts else ''
        
        # 任务描述映射
        descriptions = {
            'fetch_new_group_history': f'群聊历史回溯任务|回溯天数{app.config.get("TG_HISTORY_DAYS", 30)}',
            'update_group_history': '群聊增量获取任务',
            'fetch_account_group_info': '同步账号任务',
            'manual_download_file': '手动下载任务',
            'send_tg_data': '文件FTP传输任务'
        }
        
        base_desc = descriptions.get(job_name, job_name)
        return f'{base_desc}|{info_str}' if info_str else base_desc


class BaseTask(ABC):
    """
    任务基类，提供通用的任务管理功能
    
    功能包括：
    - 接收 resource_id 和 session_id 参数
    - 写入和更新 job_queue_log 数据表
    - 运行任务的模板方法
    - 手动停止任务的能力
    """
    
    def __init__(self, resource_id: Optional[str] = None, session_id: Optional[str] = None):
        """
        初始化任务基类
        
        Args:
            resource_id: 资源ID，可以是chat_id、account_id等
            session_id: 会话ID，用于标识连接名称
        """
        self.resource_id = resource_id or ''
        self.session_id = session_id or ''
        self.queue = None
        self.job_name = self.get_job_name()
        self.is_stopped = False
        self.task_result = None  # 存储任务执行结果
        
    @abstractmethod
    def get_job_name(self) -> str:
        """
        获取任务名称，子类必须实现
        
        Returns:
            str: 任务名称
        """
        pass
    
    @abstractmethod
    def execute_task(self) -> Dict[str, Any]:
        """
        执行具体的任务逻辑，子类必须实现
        
        Returns:
            Dict[str, Any]: 任务执行结果
        """
        pass
    
    def start_task(self) -> Dict[str, Any]:
        """
        启动任务的模板方法
        
        Returns:
            Dict[str, Any]: 任务执行结果
        """
        logger.info(f'启动任务: {self.job_name}')
        
        # 使用增强版队列管理器检查任务冲突并创建队列记录
        flag, queue, extra_info = EnhancedJobQueueManager.add_to_queue(
            self.job_name, 
            resource_id=self.resource_id,
            session_name=self.session_id,
            wait_if_conflict=getattr(self, 'wait_if_conflict', False)
        )
        db.session.commit()
        
        if not flag:
            conflict_msg = f'任务冲突: {extra_info.get("conflict_type", "unknown")}'
            if extra_info.get('mode') == QueueMode.WAIT_IN_QUEUE.value:
                conflict_msg += f', 预估等待: {extra_info.get("estimated_wait_time", 0)}秒'
            
            logger.info(f'任务 {self.job_name} {conflict_msg}')
            return {
                'err_code': 1,
                'err_msg': '任务已在运行中或加入等待队列失败',
                'task_running': True,
                'extra_info': extra_info
            }
        
        # 如果是等待状态，返回等待信息
        if queue and queue.status == QueueStatus.WAITING.value:
            logger.info(f'任务 {self.job_name} 已加入等待队列，位置: {extra_info.get("queue_position", 0)}')
            return {
                'err_code': 0,
                'err_msg': '任务已加入等待队列',
                'task_waiting': True,
                'queue_id': queue.id,
                'extra_info': extra_info
            }
        
        self.queue = queue
        
        try:
            # 执行具体的任务逻辑
            result = self.execute_task()
            self.task_result = result  # 保存任务执行结果
            
            # 如果任务成功完成，记录结果
            if isinstance(result, dict) and result.get('err_code', 0) == 0:
                logger.info(f'任务 {self.job_name} 执行成功')
            else:
                logger.warning(f'任务 {self.job_name} 执行失败或有警告: {result}')
            
            return result
            
        except Exception as e:
            error_msg = f'任务 {self.job_name} 执行时发生异常: {str(e)}'
            logger.error(error_msg)
            self.task_result = {
                'err_code': 1,
                'err_msg': error_msg,
                'exception': str(e)
            }
            return self.task_result
        finally:
            self._finish_task()
    
    def stop_task(self) -> bool:
        """
        手动停止任务
        
        Returns:
            bool: 停止是否成功
        """
        try:
            logger.info(f'手动停止任务: {self.job_name}')
            self.is_stopped = True
            
            # 设置手动停止的结果
            self.task_result = {
                'err_code': 1,
                'err_msg': '任务被手动停止',
                'stopped_manually': True
            }
            
            if self.queue:
                self._finish_task()
                
            return True
        except Exception as e:
            logger.error(f'停止任务失败: {e}')
            return False
    
    @staticmethod
    def _json_serializer(obj):
        """JSON序列化器，处理datetime等不可序列化的对象"""
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.time):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def generate_result_summary(self, result: Dict[str, Any]) -> str:
        """
        生成任务结果的友好摘要文本，子类可重写以自定义格式
        
        Args:
            result: 任务执行结果字典
            
        Returns:
            str: 友好的结果摘要文本
        """
        if not result:
            return "任务完成，无结果数据"
            
        err_code = result.get('err_code', 0)
        if err_code != 0:
            return f"任务失败: {result.get('err_msg', '未知错误')}"
        
        payload = result.get('payload', {})
        if payload:
            duration = payload.get('duration_seconds', 0)
            duration_text = f"{duration:.1f}秒" if duration > 0 else "未知"
            return f"任务成功，耗时 {duration_text}"
        
        return "任务成功"

    def _finish_task(self):
        """标记任务完成并清理数据库会话"""
        if not self.queue:
            return
            
        try:
            # 生成友好的结果摘要和详细的JSON数据
            result_summary = ''
            result_json = ''
            
            if self.task_result:
                # 生成友好摘要
                result_summary = self.generate_result_summary(self.task_result)
                
                # 生成详细JSON（保持原有逻辑）
                try:
                    result_json = json.dumps(self.task_result, ensure_ascii=False, default=self._json_serializer)
                except Exception as json_e:
                    logger.warning(f'任务结果JSON序列化失败: {json_e}, 使用字符串表示')
                    result_json = str(self.task_result)
            
            # 将友好摘要存储到result字段，详细数据可能需要额外处理
            EnhancedJobQueueManager.finish_task(self.queue.id, result_summary)
            logger.info(f'任务 {self.job_name} (queue_id: {self.queue.id}) 已标记为完成，result已保存')
        except Exception as e:
            logger.error(f'任务完成标记失败: {e}')
            db.session.rollback()
        finally:
            db.session.remove()
    
    def update_queue_log(self, **kwargs):
        """
        更新队列日志的额外信息
        
        Args:
            **kwargs: 要更新的字段，如session_name, result等
        """
        if not self.queue:
            logger.warning('队列对象不存在，无法更新日志')
            return
            
        try:
            from jd.models.job_queue_log import JobQueueLog
            JobQueueLog.query.filter_by(id=self.queue.id).update(kwargs)
            db.session.commit()
            logger.debug(f'更新任务队列 {self.queue.id} 信息: {kwargs}')
        except Exception as e:
            logger.error(f'更新队列日志失败: {e}')
            db.session.rollback()
    
    def check_should_stop(self) -> bool:
        """
        检查任务是否应该停止
        
        Returns:
            bool: 是否应该停止
        """
        return self.is_stopped


class AsyncBaseTask(BaseTask):
    """
    异步任务基类，适用于需要异步操作的任务
    """
    
    @abstractmethod
    async def execute_async_task(self) -> Dict[str, Any]:
        """
        执行异步任务逻辑，子类必须实现
        
        Returns:
            Dict[str, Any]: 任务执行结果
        """
        pass
    
    def execute_task(self) -> Dict[str, Any]:
        """
        同步包装异步任务执行
        
        Returns:
            Dict[str, Any]: 任务执行结果
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(self.execute_async_task())
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f'异步任务执行错误: {e}')
            raise
#!/usr/bin/env python3
"""
tg_history_job.py 的单元测试

测试改进后的任务队列管理功能：
- AsyncBaseTask 架构集成
- 全局历史获取任务
- Session 管理和冲突处理
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # 导入待测试的模块
    from jd.tasks.first.tg_history_job import TgHistoryTask, fetch_tg_history_job
    from jd.tasks.base_task import QueueStatus
except ImportError as e:
    print(f"导入错误: {e}")
    # 创建 Mock 类以便测试可以运行
    class TgHistoryTask:
        def __init__(self, session_name=None): self.session_name = session_name
    def fetch_tg_history_job(session_name=None): return {}
    class QueueStatus:
        RUNNING = Mock()
        RUNNING.value = 1


class TestTgHistoryTask(unittest.TestCase):
    """TgHistoryTask 单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.task_default = TgHistoryTask()
        self.task_custom = TgHistoryTask('custom_session')
    
    def test_task_initialization_default(self):
        """测试默认任务初始化"""
        self.assertEqual(self.task_default.resource_id, '')
        self.assertEqual(self.task_default.session_id, 'global_history')
        self.assertEqual(self.task_default.get_job_name(), 'update_group_history')
        self.assertFalse(self.task_default.wait_if_conflict)  # 立即返回模式
    
    def test_task_initialization_custom_session(self):
        """测试自定义 session 任务初始化"""
        self.assertEqual(self.task_custom.resource_id, '')
        self.assertEqual(self.task_custom.session_id, 'custom_session')
        self.assertEqual(self.task_custom.get_job_name(), 'update_group_history')
        self.assertFalse(self.task_custom.wait_if_conflict)
    
    def test_job_name(self):
        """测试任务名称"""
        self.assertEqual(self.task_default.get_job_name(), 'update_group_history')
        self.assertEqual(self.task_custom.get_job_name(), 'update_group_history')
    
    @patch('jd.tasks.first.tg_history_job.ExsitedGroupHistoryFetcher')
    async def test_execute_async_task_success(self, mock_fetcher_class):
        """测试异步任务执行成功"""
        # Mock ExsitedGroupHistoryFetcher
        mock_fetcher = AsyncMock()
        mock_fetcher.process_all_groups.return_value = True
        mock_fetcher.close_telegram_service.return_value = None
        mock_fetcher_class.return_value = mock_fetcher
        
        result = await self.task_default.execute_async_task()
        
        # 验证结果
        self.assertEqual(result['err_code'], 0)
        self.assertEqual(result['err_msg'], '')
        self.assertTrue(result['payload']['success'])
        self.assertEqual(result['payload']['status'], 'completed')
        
        # 验证方法调用
        mock_fetcher.process_all_groups.assert_called_once()
        mock_fetcher.close_telegram_service.assert_called_once()
    
    @patch('jd.tasks.first.tg_history_job.ExsitedGroupHistoryFetcher')
    async def test_execute_async_task_failure(self, mock_fetcher_class):
        """测试异步任务执行失败"""
        # Mock ExsitedGroupHistoryFetcher 返回失败
        mock_fetcher = AsyncMock()
        mock_fetcher.process_all_groups.return_value = False
        mock_fetcher.close_telegram_service.return_value = None
        mock_fetcher_class.return_value = mock_fetcher
        
        result = await self.task_default.execute_async_task()
        
        # 验证结果
        self.assertEqual(result['err_code'], 1)
        self.assertEqual(result['err_msg'], 'Telegram聊天历史获取任务未成功完成')
        self.assertFalse(result['payload']['success'])
        self.assertEqual(result['payload']['status'], 'failed')
        
        # 验证方法调用
        mock_fetcher.process_all_groups.assert_called_once()
        mock_fetcher.close_telegram_service.assert_called_once()
    
    @patch('jd.tasks.first.tg_history_job.ExsitedGroupHistoryFetcher')
    async def test_execute_async_task_exception(self, mock_fetcher_class):
        """测试异步任务执行过程中异常"""
        # Mock ExsitedGroupHistoryFetcher 抛出异常
        mock_fetcher = AsyncMock()
        mock_fetcher.process_all_groups.side_effect = Exception("网络连接错误")
        mock_fetcher.close_telegram_service.return_value = None
        mock_fetcher_class.return_value = mock_fetcher
        
        result = await self.task_default.execute_async_task()
        
        # 验证结果
        self.assertEqual(result['err_code'], 1)
        self.assertIn('异步任务执行错误', result['err_msg'])
        self.assertFalse(result['payload']['success'])
        self.assertEqual(result['payload']['status'], 'error')
        self.assertEqual(result['payload']['exception'], "网络连接错误")
        
        # 验证清理方法仍然被调用
        mock_fetcher.close_telegram_service.assert_called_once()
    
    @patch('jd.tasks.first.tg_history_job.ExsitedGroupHistoryFetcher')
    async def test_execute_async_task_cleanup_on_exception(self, mock_fetcher_class):
        """测试异常情况下的资源清理"""
        # Mock ExsitedGroupHistoryFetcher
        mock_fetcher = AsyncMock()
        mock_fetcher.process_all_groups.side_effect = Exception("处理错误")
        mock_fetcher.close_telegram_service.side_effect = Exception("清理错误")
        mock_fetcher_class.return_value = mock_fetcher
        
        result = await self.task_default.execute_async_task()
        
        # 验证即使清理失败，任务也能正常返回错误结果
        self.assertEqual(result['err_code'], 1)
        self.assertIn('异步任务执行错误', result['err_msg'])
        
        # 验证清理方法被调用
        mock_fetcher.close_telegram_service.assert_called_once()


class TestFetchTgHistoryJobCeleryTask(unittest.TestCase):
    """fetch_tg_history_job Celery 任务测试"""
    
    @patch('jd.tasks.first.tg_history_job.TgHistoryTask')
    def test_celery_task_default_call(self, mock_task_class):
        """测试默认 Celery 任务调用"""
        # Mock 任务实例
        mock_task_instance = Mock()
        mock_task_instance.start_task.return_value = {
            'err_code': 0,
            'payload': {'success': True, 'status': 'completed'}
        }
        mock_task_class.return_value = mock_task_instance
        
        # 调用 Celery 任务
        result = fetch_tg_history_job()
        
        # 验证
        mock_task_class.assert_called_once_with(None)  # 默认 session_name 为 None
        mock_task_instance.start_task.assert_called_once()
        self.assertEqual(result['err_code'], 0)
        self.assertTrue(result['payload']['success'])
    
    @patch('jd.tasks.first.tg_history_job.TgHistoryTask')
    def test_celery_task_custom_session_call(self, mock_task_class):
        """测试自定义 session 的 Celery 任务调用"""
        # Mock 任务实例
        mock_task_instance = Mock()
        mock_task_instance.start_task.return_value = {
            'err_code': 0,
            'payload': {'success': True, 'status': 'completed'}
        }
        mock_task_class.return_value = mock_task_instance
        
        # 调用带自定义 session 的 Celery 任务
        result = fetch_tg_history_job('my_custom_session')
        
        # 验证
        mock_task_class.assert_called_once_with('my_custom_session')
        mock_task_instance.start_task.assert_called_once()
        self.assertEqual(result['err_code'], 0)


class TestTaskConflictHandling(unittest.TestCase):
    """测试任务冲突处理逻辑"""
    
    @patch('jd.tasks.base_task.EnhancedJobQueueManager.add_to_queue')
    @patch('jd.tasks.base_task.db')
    def test_immediate_return_on_conflict(self, mock_db, mock_add_to_queue):
        """测试冲突时立即返回的行为"""
        # Mock 队列管理器返回冲突
        mock_add_to_queue.return_value = (False, None, {
            'conflict_type': 'job_name',  # 同名任务冲突
            'mode': 'immediate'
        })
        
        task = TgHistoryTask('test_session')
        result = task.start_task()
        
        # 验证立即返回冲突信息
        self.assertEqual(result['err_code'], 1)
        self.assertIn('任务冲突', result['err_msg'])
        self.assertTrue(result['task_running'])
        self.assertIn('extra_info', result)
    
    @patch('jd.tasks.base_task.EnhancedJobQueueManager.add_to_queue')
    @patch('jd.tasks.base_task.db')
    def test_session_based_conflict_detection(self, mock_db, mock_add_to_queue):
        """测试基于 session 的冲突检测"""
        # Mock 不同 session 的任务可以并行运行
        mock_queue = Mock()
        mock_queue.status = QueueStatus.RUNNING.value
        mock_queue.id = 1
        
        mock_add_to_queue.return_value = (True, mock_queue, {
            'mode': 'immediate',
            'conflict_type': None
        })
        
        task = TgHistoryTask('unique_session')
        
        # Mock execute_task 方法
        with patch.object(task, 'execute_task') as mock_execute:
            mock_execute.return_value = {
                'err_code': 0,
                'payload': {'success': True, 'status': 'completed'}
            }
            
            result = task.start_task()
            
            # 验证正常执行
            mock_execute.assert_called_once()
            self.assertEqual(result['err_code'], 0)
            self.assertTrue(result['payload']['success'])


class TestAsyncTaskExecution(unittest.TestCase):
    """测试异步任务执行"""
    
    def test_sync_wrapper_calls_async(self):
        """测试同步包装器正确调用异步方法"""
        task = TgHistoryTask('test_session')
        
        # Mock execute_async_task 方法
        async def mock_async_execute():
            return {
                'err_code': 0,
                'payload': {'success': True, 'status': 'completed'}
            }
        
        with patch.object(task, 'execute_async_task', side_effect=mock_async_execute):
            result = task.execute_task()
            
            # 验证同步包装器工作正常
            self.assertEqual(result['err_code'], 0)
            self.assertTrue(result['payload']['success'])
    
    def test_sync_wrapper_handles_async_exception(self):
        """测试同步包装器处理异步异常"""
        task = TgHistoryTask('test_session')
        
        # Mock execute_async_task 抛出异常
        async def mock_async_execute():
            raise Exception("异步执行错误")
        
        with patch.object(task, 'execute_async_task', side_effect=mock_async_execute):
            # 异常应该被 execute_task 捕获并重新抛出
            with self.assertRaises(Exception) as cm:
                task.execute_task()
            
            self.assertIn("异步执行错误", str(cm.exception))


class TestTaskIntegration(unittest.TestCase):
    """测试任务集成功能"""
    
    @patch('jd.tasks.first.tg_history_job.ExsitedGroupHistoryFetcher')
    @patch('jd.tasks.base_task.EnhancedJobQueueManager.add_to_queue')
    @patch('jd.tasks.base_task.EnhancedJobQueueManager.finish_task')
    @patch('jd.tasks.base_task.db')
    def test_full_task_execution_flow(self, mock_db, mock_finish_task, mock_add_to_queue, mock_fetcher_class):
        """测试完整的任务执行流程"""
        # Mock 队列管理
        mock_queue = Mock()
        mock_queue.status = QueueStatus.RUNNING.value
        mock_queue.id = 1
        mock_add_to_queue.return_value = (True, mock_queue, {'mode': 'immediate'})
        
        # Mock ExsitedGroupHistoryFetcher
        mock_fetcher = AsyncMock()
        mock_fetcher.process_all_groups.return_value = True
        mock_fetcher.close_telegram_service.return_value = None
        mock_fetcher_class.return_value = mock_fetcher
        
        # 执行任务
        task = TgHistoryTask('integration_test_session')
        result = task.start_task()
        
        # 验证流程
        mock_add_to_queue.assert_called_once()
        mock_finish_task.assert_called_once_with(1)
        
        # 验证结果
        self.assertEqual(result['err_code'], 0)
        self.assertTrue(result['payload']['success'])
        self.assertEqual(result['payload']['status'], 'completed')
    
    def test_session_naming_logic(self):
        """测试 session 命名逻辑"""
        # 测试默认 session
        task1 = TgHistoryTask()
        self.assertEqual(task1.session_id, 'global_history')
        
        # 测试自定义 session
        task2 = TgHistoryTask('custom_session')
        self.assertEqual(task2.session_id, 'custom_session')
        
        # 测试空字符串 session
        task3 = TgHistoryTask('')
        self.assertEqual(task3.session_id, 'global_history')  # 空字符串应该使用默认值


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
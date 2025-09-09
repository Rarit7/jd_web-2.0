#!/usr/bin/env python3
"""
tg_fetch_group_info.py 的单元测试

测试改进后的任务队列管理功能：
- BaseTask 架构集成
- 冲突处理策略（相同 account_id 直接返回）
- 队列管理和状态处理
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # 导入待测试的模块
    from jd.tasks.telegram.tg_fetch_group_info import FetchAccountGroupInfoTask, fetch_account_group_info
    from jd.tasks.base_task import QueueStatus
except ImportError as e:
    print(f"导入错误: {e}")
    # 创建 Mock 类以便测试可以运行
    class FetchAccountGroupInfoTask:
        def __init__(self, account_id): self.account_id = account_id
    def fetch_account_group_info(account_id): return {}
    class QueueStatus:
        RUNNING = Mock()
        RUNNING.value = 1


class TestFetchAccountGroupInfoTask(unittest.TestCase):
    """FetchAccountGroupInfoTask 单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.account_id = 123
        self.task = FetchAccountGroupInfoTask(self.account_id)
    
    def test_task_initialization(self):
        """测试任务初始化"""
        self.assertEqual(self.task.account_id, 123)
        self.assertEqual(self.task.resource_id, "123")
        self.assertEqual(self.task.get_job_name(), "fetch_account_group_info")
        self.assertFalse(self.task.wait_if_conflict)  # 立即返回模式
    
    def test_job_name(self):
        """测试任务名称"""
        self.assertEqual(self.task.get_job_name(), "fetch_account_group_info")
    
    @patch('jd.tasks.telegram.tg_fetch_group_info.TgAccount')
    @patch('jd.tasks.telegram.tg_fetch_group_info.asyncio.run')
    @patch('jd.tasks.telegram.tg_fetch_group_info.TgGroupInfoManager.sync_group_info_by_account')
    def test_execute_task_success(self, mock_sync_method, mock_asyncio_run, mock_tg_account):
        """测试任务执行成功"""
        # Mock TgAccount
        mock_account = Mock()
        mock_account.id = 123
        mock_account.name = "test_account"
        mock_account.user_id = "test_user_123"
        mock_account.status = "JOIN_SUCCESS"  # Mock JOIN_SUCCESS 状态
        
        mock_tg_account.query.filter.return_value.first.return_value = mock_account
        mock_tg_account.StatusType.JOIN_SUCCESS = "JOIN_SUCCESS"
        
        # Mock 同步结果
        sync_result = {
            'success': True,
            'message': '同步成功',
            'processed_groups': ['-1001234567890']
        }
        mock_asyncio_run.return_value = sync_result
        
        # Mock 辅助函数
        with patch('jd.tasks.telegram.tg_fetch_group_info._sync_account_group_sessions') as mock_sync_sessions, \
             patch('jd.tasks.telegram.tg_fetch_group_info._fill_missing_account_ids') as mock_fill_ids:
            
            mock_sync_sessions.return_value = {'new_sessions': 1}
            mock_fill_ids.return_value = {'filled_groups': 1}
            
            result = self.task.execute_task()
            
            # 验证结果
            self.assertEqual(result['err_code'], 0)
            self.assertEqual(result['err_msg'], '')
            self.assertTrue(result['success'])
            self.assertEqual(result['account_id'], 123)
            self.assertEqual(result['account_name'], "test_account")
            self.assertEqual(result['account_user_id'], "test_user_123")
    
    @patch('jd.tasks.telegram.tg_fetch_group_info.TgAccount')
    def test_execute_task_account_not_found(self, mock_tg_account):
        """测试账户不存在的情况"""
        # Mock 账户不存在
        mock_tg_account.query.filter.return_value.first.return_value = None
        
        result = self.task.execute_task()
        
        # 验证结果
        self.assertEqual(result['err_code'], 1)
        self.assertEqual(result['err_msg'], "账户 123 不存在")
        self.assertFalse(result['success'])
        self.assertEqual(result['account_id'], 123)
    
    @patch('jd.tasks.telegram.tg_fetch_group_info.TgAccount')
    def test_execute_task_account_status_invalid(self, mock_tg_account):
        """测试账户状态异常的情况"""
        # Mock 状态异常的账户
        mock_account = Mock()
        mock_account.id = 123
        mock_account.name = "test_account"
        mock_account.status = "FAILED"  # 异常状态
        
        mock_tg_account.query.filter.return_value.first.return_value = mock_account
        mock_tg_account.StatusType.JOIN_SUCCESS = "JOIN_SUCCESS"
        
        result = self.task.execute_task()
        
        # 验证结果
        self.assertEqual(result['err_code'], 1)
        self.assertIn("状态异常", result['err_msg'])
        self.assertFalse(result['success'])
        self.assertEqual(result['account_id'], 123)
    
    @patch('jd.tasks.telegram.tg_fetch_group_info.TgAccount')
    def test_execute_task_exception(self, mock_tg_account):
        """测试执行过程中异常的情况"""
        # Mock 异常
        mock_tg_account.query.filter.side_effect = Exception("数据库连接错误")
        
        result = self.task.execute_task()
        
        # 验证结果
        self.assertEqual(result['err_code'], 1)
        self.assertIn("异常", result['err_msg'])
        self.assertFalse(result['success'])
        self.assertEqual(result['account_id'], 123)


class TestFetchAccountGroupInfoCeleryTask(unittest.TestCase):
    """fetch_account_group_info Celery 任务测试"""
    
    @patch('jd.tasks.telegram.tg_fetch_group_info.FetchAccountGroupInfoTask')
    def test_celery_task_call(self, mock_task_class):
        """测试 Celery 任务调用"""
        # Mock 任务实例
        mock_task_instance = Mock()
        mock_task_instance.start_task.return_value = {
            'err_code': 0,
            'success': True,
            'account_id': 123
        }
        mock_task_class.return_value = mock_task_instance
        
        # 调用 Celery 任务
        result = fetch_account_group_info(123)
        
        # 验证
        mock_task_class.assert_called_once_with(123)
        mock_task_instance.start_task.assert_called_once()
        self.assertEqual(result['err_code'], 0)
        self.assertEqual(result['account_id'], 123)


class TestTaskConflictHandling(unittest.TestCase):
    """测试任务冲突处理逻辑"""
    
    @patch('jd.tasks.base_task.EnhancedJobQueueManager.add_to_queue')
    @patch('jd.tasks.base_task.db')
    def test_immediate_return_on_conflict(self, mock_db, mock_add_to_queue):
        """测试冲突时立即返回的行为"""
        # Mock 队列管理器返回冲突
        mock_add_to_queue.return_value = (False, None, {
            'conflict_type': 'resource',
            'mode': 'immediate'
        })
        
        task = FetchAccountGroupInfoTask(123)
        result = task.start_task()
        
        # 验证立即返回冲突信息
        self.assertEqual(result['err_code'], 1)
        self.assertIn('任务冲突', result['err_msg'])
        self.assertTrue(result['task_running'])
        self.assertIn('extra_info', result)
    
    @patch('jd.tasks.base_task.EnhancedJobQueueManager.add_to_queue')
    @patch('jd.tasks.base_task.db')
    def test_no_conflict_execution(self, mock_db, mock_add_to_queue):
        """测试无冲突时正常执行"""
        # Mock 队列记录
        mock_queue = Mock()
        mock_queue.status = QueueStatus.RUNNING.value
        mock_queue.id = 1
        
        # Mock 无冲突
        mock_add_to_queue.return_value = (True, mock_queue, {
            'mode': 'immediate',
            'conflict_type': None
        })
        
        task = FetchAccountGroupInfoTask(123)
        
        # Mock execute_task 方法
        with patch.object(task, 'execute_task') as mock_execute:
            mock_execute.return_value = {
                'err_code': 0,
                'success': True,
                'account_id': 123
            }
            
            result = task.start_task()
            
            # 验证正常执行
            mock_execute.assert_called_once()
            self.assertEqual(result['err_code'], 0)
            self.assertTrue(result['success'])


class TestTaskIntegration(unittest.TestCase):
    """测试任务集成功能"""
    
    @patch('jd.tasks.telegram.tg_fetch_group_info.TgAccount')
    @patch('jd.tasks.telegram.tg_fetch_group_info.asyncio.run')
    @patch('jd.tasks.telegram.tg_fetch_group_info._sync_account_group_sessions')
    @patch('jd.tasks.telegram.tg_fetch_group_info._fill_missing_account_ids')
    @patch('jd.tasks.base_task.EnhancedJobQueueManager.add_to_queue')
    @patch('jd.tasks.base_task.EnhancedJobQueueManager.finish_task')
    @patch('jd.tasks.base_task.db')
    def test_full_task_execution_flow(self, mock_db, mock_finish_task, mock_add_to_queue,
                                    mock_fill_ids, mock_sync_sessions, mock_asyncio_run, mock_tg_account):
        """测试完整的任务执行流程"""
        # Mock 账户
        mock_account = Mock()
        mock_account.id = 123
        mock_account.name = "test_account"
        mock_account.user_id = "test_user_123"
        mock_account.status = "JOIN_SUCCESS"
        
        mock_tg_account.query.filter.return_value.first.return_value = mock_account
        mock_tg_account.StatusType.JOIN_SUCCESS = "JOIN_SUCCESS"
        
        # Mock 队列管理
        mock_queue = Mock()
        mock_queue.status = QueueStatus.RUNNING.value
        mock_queue.id = 1
        mock_add_to_queue.return_value = (True, mock_queue, {'mode': 'immediate'})
        
        # Mock 同步结果
        mock_asyncio_run.return_value = {
            'success': True,
            'message': '同步成功',
            'processed_groups': ['-1001234567890']
        }
        
        # Mock 辅助函数
        mock_sync_sessions.return_value = {'new_sessions': 1}
        mock_fill_ids.return_value = {'filled_groups': 1}
        
        # 执行任务
        task = FetchAccountGroupInfoTask(123)
        result = task.start_task()
        
        # 验证流程
        mock_add_to_queue.assert_called_once()
        mock_asyncio_run.assert_called_once()
        mock_sync_sessions.assert_called_once()
        mock_fill_ids.assert_called_once()
        mock_finish_task.assert_called_once_with(1)
        
        # 验证结果
        self.assertEqual(result['err_code'], 0)
        self.assertTrue(result['success'])
        self.assertEqual(result['account_id'], 123)
        self.assertEqual(result['account_name'], "test_account")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
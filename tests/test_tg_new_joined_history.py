#!/usr/bin/env python3
"""
tg_new_joined_history.py 的单元测试

测试改进后的任务队列管理功能：
- AsyncBaseTask 架构集成
- 自定义冲突处理策略
- 智能队列管理（相同 chat_id 跳过，相同 session 排队）
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
    from jd.tasks.first.tg_new_joined_history import (
        NewGroupHistoryTask, 
        run_new_group_history_fetch, 
        fetch_new_joined_group_history,
        start_group_history_fetch
    )
    from jd.tasks.base_task import QueueStatus
except ImportError as e:
    print(f"导入错误: {e}")
    # 创建 Mock 类以便测试可以运行
    class NewGroupHistoryTask:
        def __init__(self, group_name, chat_id, session_name=None): 
            self.group_name = group_name
            self.chat_id = chat_id
    def run_new_group_history_fetch(group_name, chat_id, session_name=None): return {}
    def fetch_new_joined_group_history(chat_id, session_name, group_name=None): return {}
    def start_group_history_fetch(group_name, chat_id, session_name=None): return {}
    class QueueStatus:
        RUNNING = Mock()
        RUNNING.value = 1


class TestNewGroupHistoryTask(unittest.TestCase):
    """NewGroupHistoryTask 单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.group_name = "TestGroup"
        self.chat_id = -1001234567890
        self.session_name = "test_session"
        self.task = NewGroupHistoryTask(self.group_name, self.chat_id, self.session_name)
    
    def test_task_initialization(self):
        """测试任务初始化"""
        self.assertEqual(self.task.group_name, "TestGroup")
        self.assertEqual(self.task.chat_id, -1001234567890)
        self.assertEqual(self.task.resource_id, "-1001234567890")  # chat_id 作为 resource_id
        self.assertEqual(self.task.session_id, "test_session")
        self.assertEqual(self.task.get_job_name(), "fetch_new_group_history")
        self.assertFalse(self.task.wait_if_conflict)  # 初始为 False，会根据冲突类型动态调整
    
    def test_job_name(self):
        """测试任务名称"""
        self.assertEqual(self.task.get_job_name(), "fetch_new_group_history")
    
    @patch('jd.tasks.first.tg_new_joined_history.JobQueueLog')
    @patch('jd.tasks.first.tg_new_joined_history.db')
    def test_check_custom_conflict_same_chat_id(self, mock_db, mock_job_queue_log):
        """测试相同 chat_id 的冲突检测"""
        # Mock 存在相同 chat_id 的运行任务
        mock_task = Mock()
        mock_task.resource_id = "-1001234567890"
        mock_job_queue_log.query.filter_by.return_value.first.return_value = mock_task
        
        result = self.task._check_custom_conflict()
        
        # 验证返回跳过动作
        self.assertEqual(result['action'], 'skip')
        self.assertEqual(result['reason'], 'same_chat_id')
        self.assertIn('已在运行中', result['message'])
        self.assertEqual(result['result']['err_code'], 0)
        self.assertTrue(result['result']['payload']['success'])
        self.assertTrue(result['result']['payload']['skipped'])
    
    @patch('jd.tasks.first.tg_new_joined_history.JobQueueLog')
    @patch('jd.tasks.first.tg_new_joined_history.db')
    def test_check_custom_conflict_same_session(self, mock_db, mock_job_queue_log):
        """测试相同 session 的冲突检测"""
        # Mock 不存在相同 chat_id 的任务
        mock_job_queue_log.query.filter_by.return_value.first.return_value = None
        
        # Mock 存在相同 session 但不同 chat_id 的任务
        mock_session_task = Mock()
        mock_session_task.resource_id = "-1001234567891"  # 不同的 chat_id
        mock_job_queue_log.query.filter.return_value.first.return_value = mock_session_task
        
        result = self.task._check_custom_conflict()
        
        # 验证返回排队动作
        self.assertEqual(result['action'], 'queue')
        self.assertEqual(result['reason'], 'same_session')
        self.assertIn('排队等待', result['message'])
    
    @patch('jd.tasks.first.tg_new_joined_history.JobQueueLog')
    @patch('jd.tasks.first.tg_new_joined_history.db')
    def test_check_custom_conflict_no_conflict(self, mock_db, mock_job_queue_log):
        """测试无冲突情况"""
        # Mock 没有冲突任务
        mock_job_queue_log.query.filter_by.return_value.first.return_value = None
        mock_job_queue_log.query.filter.return_value.first.return_value = None
        
        result = self.task._check_custom_conflict()
        
        # 验证返回执行动作
        self.assertEqual(result['action'], 'execute')
        self.assertEqual(result['reason'], 'no_conflict')
        self.assertIn('立即执行', result['message'])
    
    @patch('jd.tasks.first.tg_new_joined_history.JobQueueLog')
    @patch('jd.tasks.first.tg_new_joined_history.db')
    def test_check_custom_conflict_no_session(self, mock_db, mock_job_queue_log):
        """测试无 session 的情况"""
        # 创建没有 session 的任务
        task_no_session = NewGroupHistoryTask("TestGroup", -1001234567890, None)
        
        # Mock 没有相同 chat_id 的任务
        mock_job_queue_log.query.filter_by.return_value.first.return_value = None
        
        result = task_no_session._check_custom_conflict()
        
        # 验证直接返回执行（因为没有 session 需要检查）
        self.assertEqual(result['action'], 'execute')
        self.assertEqual(result['reason'], 'no_conflict')
    
    @patch.object(NewGroupHistoryTask, '_check_custom_conflict')
    @patch('jd.tasks.base_task.AsyncBaseTask.start_task')
    def test_start_task_skip_scenario(self, mock_super_start, mock_conflict_check):
        """测试跳过场景的 start_task"""
        # Mock 冲突检查返回跳过
        skip_result = {
            'action': 'skip',
            'result': {
                'err_code': 0,
                'payload': {'success': True, 'skipped': True}
            }
        }
        mock_conflict_check.return_value = skip_result
        
        result = self.task.start_task()
        
        # 验证直接返回跳过结果，不调用父类方法
        self.assertEqual(result, skip_result['result'])
        mock_super_start.assert_not_called()
    
    @patch.object(NewGroupHistoryTask, '_check_custom_conflict')
    @patch('jd.tasks.base_task.AsyncBaseTask.start_task')
    def test_start_task_queue_scenario(self, mock_super_start, mock_conflict_check):
        """测试排队场景的 start_task"""
        # Mock 冲突检查返回排队
        mock_conflict_check.return_value = {'action': 'queue'}
        mock_super_start.return_value = {'err_code': 0, 'queue_waiting': True}
        
        result = self.task.start_task()
        
        # 验证设置为排队模式并调用父类方法
        self.assertTrue(self.task.wait_if_conflict)
        mock_super_start.assert_called_once()
    
    @patch.object(NewGroupHistoryTask, '_check_custom_conflict')
    @patch('jd.tasks.base_task.AsyncBaseTask.start_task')
    def test_start_task_execute_scenario(self, mock_super_start, mock_conflict_check):
        """测试立即执行场景的 start_task"""
        # Mock 冲突检查返回执行
        mock_conflict_check.return_value = {'action': 'execute'}
        mock_super_start.return_value = {'err_code': 0, 'payload': {'success': True}}
        
        result = self.task.start_task()
        
        # 验证设置为立即执行模式并调用父类方法
        self.assertFalse(self.task.wait_if_conflict)
        mock_super_start.assert_called_once()
    
    @patch('jd.tasks.first.tg_new_joined_history.NewJoinedGroupHistoryFetcher')
    @patch('jd.tasks.first.tg_new_joined_history.TgGroupInfoManager.get_group_user_session')
    async def test_execute_async_task_success(self, mock_get_session, mock_fetcher_class):
        """测试异步任务执行成功"""
        # Mock session 列表
        mock_get_session.return_value = ['session1', 'session2']
        
        # Mock NewJoinedGroupHistoryFetcher
        mock_fetcher = AsyncMock()
        mock_fetcher.init_telegram_service.return_value = True
        mock_fetcher.tg.client = AsyncMock()
        mock_fetcher.process_specific_group.return_value = True
        mock_fetcher.close_telegram_service.return_value = None
        mock_fetcher_class.return_value = mock_fetcher
        
        result = await self.task.execute_async_task()
        
        # 验证结果
        self.assertEqual(result['err_code'], 0)
        self.assertEqual(result['err_msg'], '')
        self.assertTrue(result['payload']['success'])
        self.assertEqual(result['payload']['group_name'], "TestGroup")
        self.assertEqual(result['payload']['chat_id'], -1001234567890)
        
        # 验证方法调用
        mock_fetcher.init_telegram_service.assert_called_once_with(['session1', 'session2'])
        mock_fetcher.process_specific_group.assert_called_once_with("TestGroup", -1001234567890)
        mock_fetcher.close_telegram_service.assert_called_once()
    
    @patch('jd.tasks.first.tg_new_joined_history.NewJoinedGroupHistoryFetcher')
    @patch('jd.tasks.first.tg_new_joined_history.TgGroupInfoManager.get_group_user_session')
    async def test_execute_async_task_init_failure(self, mock_get_session, mock_fetcher_class):
        """测试 Telegram 服务初始化失败"""
        # Mock session 列表
        mock_get_session.return_value = ['session1']
        
        # Mock 初始化失败
        mock_fetcher = AsyncMock()
        mock_fetcher.init_telegram_service.return_value = False
        mock_fetcher_class.return_value = mock_fetcher
        
        result = await self.task.execute_async_task()
        
        # 验证结果
        self.assertEqual(result['err_code'], 1)
        self.assertIn('所有session初始化失败', result['err_msg'])
        self.assertFalse(result['payload']['success'])
        self.assertEqual(result['payload']['chat_id'], -1001234567890)
    
    @patch('jd.tasks.first.tg_new_joined_history.NewJoinedGroupHistoryFetcher')
    @patch('jd.tasks.first.tg_new_joined_history.TgGroupInfoManager.get_group_user_session')
    async def test_execute_async_task_process_failure(self, mock_get_session, mock_fetcher_class):
        """测试群组处理失败"""
        # Mock session 列表
        mock_get_session.return_value = ['session1']
        
        # Mock 处理失败
        mock_fetcher = AsyncMock()
        mock_fetcher.init_telegram_service.return_value = True
        mock_fetcher.tg.client = AsyncMock()
        mock_fetcher.process_specific_group.return_value = False
        mock_fetcher.close_telegram_service.return_value = None
        mock_fetcher_class.return_value = mock_fetcher
        
        result = await self.task.execute_async_task()
        
        # 验证结果
        self.assertEqual(result['err_code'], 1)
        self.assertIn('获取群组', result['err_msg'])
        self.assertIn('聊天记录失败', result['err_msg'])
        self.assertFalse(result['payload']['success'])
    
    @patch('jd.tasks.first.tg_new_joined_history.NewJoinedGroupHistoryFetcher')
    @patch('jd.tasks.first.tg_new_joined_history.TgGroupInfoManager.get_group_user_session')
    async def test_execute_async_task_exception(self, mock_get_session, mock_fetcher_class):
        """测试异步任务执行过程中异常"""
        # Mock session 列表
        mock_get_session.return_value = ['session1']
        
        # Mock 异常
        mock_fetcher = AsyncMock()
        mock_fetcher.init_telegram_service.side_effect = Exception("连接错误")
        mock_fetcher_class.return_value = mock_fetcher
        
        result = await self.task.execute_async_task()
        
        # 验证结果
        self.assertEqual(result['err_code'], 1)
        self.assertIn('初始化Telegram服务时发生错误', result['err_msg'])
        self.assertFalse(result['payload']['success'])


class TestCeleryTaskFunctions(unittest.TestCase):
    """测试 Celery 任务函数"""
    
    @patch('jd.tasks.first.tg_new_joined_history.NewGroupHistoryTask')
    def test_run_new_group_history_fetch(self, mock_task_class):
        """测试 run_new_group_history_fetch 函数"""
        # Mock 任务实例
        mock_task_instance = Mock()
        mock_task_instance.start_task.return_value = {
            'err_code': 0,
            'payload': {'success': True}
        }
        mock_task_class.return_value = mock_task_instance
        
        # 调用函数
        result = run_new_group_history_fetch("TestGroup", -1001234567890, "session1")
        
        # 验证
        mock_task_class.assert_called_once_with("TestGroup", -1001234567890, "session1")
        mock_task_instance.start_task.assert_called_once()
        self.assertEqual(result['err_code'], 0)
        self.assertTrue(result['payload']['success'])
    
    @patch('jd.tasks.first.tg_new_joined_history.run_new_group_history_fetch')
    def test_fetch_new_joined_group_history(self, mock_run_fetch):
        """测试 fetch_new_joined_group_history 函数"""
        # Mock 返回结果
        mock_run_fetch.return_value = {
            'err_code': 0,
            'payload': {'success': True}
        }
        
        # 测试带群组名称的调用
        result = fetch_new_joined_group_history(-1001234567890, "session1", "MyGroup")
        mock_run_fetch.assert_called_with("MyGroup", -1001234567890, "session1")
        
        # 测试不带群组名称的调用
        result = fetch_new_joined_group_history(-1001234567891, "session2")
        mock_run_fetch.assert_called_with("Group_-1001234567891", -1001234567891, "session2")
    
    @patch('jd.tasks.first.tg_new_joined_history.run_new_group_history_fetch')
    def test_start_group_history_fetch_success(self, mock_run_fetch):
        """测试 start_group_history_fetch 成功情况"""
        # Mock Celery 任务
        mock_task_result = Mock()
        str(mock_task_result) == "task-id-123"
        mock_run_fetch.delay.return_value = mock_task_result
        
        result = start_group_history_fetch("TestGroup", -1001234567890, "session1")
        
        # 验证
        self.assertEqual(result['err_code'], 0)
        self.assertEqual(result['err_msg'], '')
        self.assertIn('已启动', result['payload']['message'])
        self.assertEqual(result['payload']['chat_id'], -1001234567890)
        mock_run_fetch.delay.assert_called_once_with("TestGroup", -1001234567890, "session1")
    
    def test_start_group_history_fetch_missing_params(self):
        """测试 start_group_history_fetch 缺少参数的情况"""
        # 测试缺少 group_name
        result = start_group_history_fetch("", -1001234567890)
        self.assertEqual(result['err_code'], 1)
        self.assertIn('缺少必需参数', result['err_msg'])
        
        # 测试缺少 chat_id
        result = start_group_history_fetch("TestGroup", None)
        self.assertEqual(result['err_code'], 1)
        self.assertIn('缺少必需参数', result['err_msg'])
    
    @patch('jd.tasks.first.tg_new_joined_history.run_new_group_history_fetch')
    def test_start_group_history_fetch_exception(self, mock_run_fetch):
        """测试 start_group_history_fetch 异常情况"""
        # Mock 异常
        mock_run_fetch.delay.side_effect = Exception("Celery连接错误")
        
        result = start_group_history_fetch("TestGroup", -1001234567890)
        
        # 验证
        self.assertEqual(result['err_code'], 1)
        self.assertIn('启动历史获取任务失败', result['err_msg'])
        self.assertEqual(result['chat_id'], -1001234567890)
        self.assertEqual(result['group_name'], "TestGroup")


class TestTaskIntegration(unittest.TestCase):
    """测试任务集成功能"""
    
    @patch('jd.tasks.first.tg_new_joined_history.NewJoinedGroupHistoryFetcher')
    @patch('jd.tasks.first.tg_new_joined_history.TgGroupInfoManager.get_group_user_session')
    @patch('jd.tasks.first.tg_new_joined_history.JobQueueLog')
    @patch('jd.tasks.base_task.EnhancedJobQueueManager.add_to_queue')
    @patch('jd.tasks.base_task.EnhancedJobQueueManager.finish_task')
    @patch('jd.tasks.base_task.db')
    def test_full_task_execution_flow_no_conflict(self, mock_db, mock_finish_task, mock_add_to_queue,
                                                 mock_job_queue_log, mock_get_session, mock_fetcher_class):
        """测试完整的任务执行流程 - 无冲突场景"""
        # Mock 无冲突检查
        mock_job_queue_log.query.filter_by.return_value.first.return_value = None
        mock_job_queue_log.query.filter.return_value.first.return_value = None
        
        # Mock 队列管理
        mock_queue = Mock()
        mock_queue.status = QueueStatus.RUNNING.value
        mock_queue.id = 1
        mock_add_to_queue.return_value = (True, mock_queue, {'mode': 'immediate'})
        
        # Mock session 和 fetcher
        mock_get_session.return_value = ['session1']
        mock_fetcher = AsyncMock()
        mock_fetcher.init_telegram_service.return_value = True
        mock_fetcher.tg.client = AsyncMock()
        mock_fetcher.process_specific_group.return_value = True
        mock_fetcher.close_telegram_service.return_value = None
        mock_fetcher_class.return_value = mock_fetcher
        
        # 执行任务
        task = NewGroupHistoryTask("TestGroup", -1001234567890, "session1")
        result = task.start_task()
        
        # 验证流程
        mock_add_to_queue.assert_called_once()
        mock_finish_task.assert_called_once_with(1)
        
        # 验证结果
        self.assertEqual(result['err_code'], 0)
        self.assertTrue(result['payload']['success'])
    
    @patch('jd.tasks.first.tg_new_joined_history.JobQueueLog')
    @patch('jd.tasks.first.tg_new_joined_history.db')
    def test_full_task_execution_flow_skip_conflict(self, mock_db, mock_job_queue_log):
        """测试完整的任务执行流程 - 跳过冲突场景"""
        # Mock 相同 chat_id 的冲突
        mock_running_task = Mock()
        mock_running_task.resource_id = "-1001234567890"
        mock_job_queue_log.query.filter_by.return_value.first.return_value = mock_running_task
        
        # 执行任务
        task = NewGroupHistoryTask("TestGroup", -1001234567890, "session1")
        result = task.start_task()
        
        # 验证跳过结果
        self.assertEqual(result['err_code'], 0)
        self.assertTrue(result['payload']['success'])
        self.assertTrue(result['payload']['skipped'])
        self.assertEqual(result['payload']['chat_id'], -1001234567890)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
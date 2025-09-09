import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jd.jobs.tg_group_info import TgGroupInfoManager
from jd.models.tg_group import TgGroup
from jd.models.tg_group_status import TgGroupStatus
from jd.models.tg_group_info_change import TgGroupInfoChange


class TestTgGroupInfoManager(unittest.TestCase):
    """TgGroupInfoManager的Mock测试"""

    def setUp(self):
        """测试前准备"""
        self.sample_group_data = {
            'id': 123456789,
            'title': '测试群组',
            'username': 'test_group',
            'channel_description': '这是一个测试群组',
            'photo_path': 'images/avatar/test.jpg',
            'member_count': 100,
            'megagroup': 'group',
            'account_id': 'test_account'
        }
        
        self.mock_tg_client = Mock()
        self.mock_db_session = Mock()

    @patch('jd.jobs.tg_group_info.db.session')
    @patch('jd.jobs.tg_group_info.asyncio.new_event_loop')
    async def test_sync_all_group_info_success(self, mock_loop_factory, mock_db_session):
        """测试成功同步所有群组信息"""
        # Mock异步群组数据
        mock_group_list = [
            {'result': 'success', 'data': self.sample_group_data},
            {'result': 'success', 'data': {
                'id': 987654321,
                'title': '另一个测试群组',
                'username': 'another_test_group',
                'channel_description': '另一个测试群组描述',
                'photo_path': '',
                'member_count': 50,
                'megagroup': 'channel'
            }}
        ]
        
        # Mock事件循环
        mock_loop = Mock()
        mock_loop_factory.return_value = mock_loop
        mock_loop.run_until_complete.return_value = [item['data'] for item in mock_group_list]
        
        # Mock TgGroupInfoManager._process_single_group
        with patch.object(TgGroupInfoManager, '_process_single_group') as mock_process:
            mock_process.side_effect = [
                {'is_new': True, 'member_changes': 1, 'info_changes': 0},
                {'is_new': False, 'member_changes': 0, 'info_changes': 2}
            ]
            
            # 执行测试
            result = TgGroupInfoManager.sync_all_group_info(self.mock_tg_client)
            
            # 验证结果
            self.assertTrue(result['success'])
            self.assertEqual(result['stats']['total_groups'], 2)
            self.assertEqual(result['stats']['new_groups'], 1)
            self.assertEqual(result['stats']['updated_groups'], 1)
            self.assertEqual(result['stats']['member_changes'], 1)
            self.assertEqual(result['stats']['info_changes'], 2)
            
            # 验证调用次数
            self.assertEqual(mock_process.call_count, 2)

    @patch('jd.jobs.tg_group_info.db.session')
    def test_process_single_group_existing_group(self, mock_db_session):
        """测试处理现有群组"""
        # Mock现有群组
        mock_existing_group = Mock()
        mock_existing_group.chat_id = str(self.sample_group_data['id'])
        mock_db_session.query().filter_by().first.return_value = mock_existing_group
        
        with patch.object(TgGroupInfoManager, '_update_existing_group', return_value=2) as mock_update_existing, \
             patch.object(TgGroupInfoManager, '_update_group_status', return_value=1) as mock_update_status:
            
            result = TgGroupInfoManager._process_single_group(self.sample_group_data)
            
            self.assertFalse(result['is_new'])
            self.assertEqual(result['member_changes'], 1)
            self.assertEqual(result['info_changes'], 2)
            
            mock_update_existing.assert_called_once_with(mock_existing_group, self.sample_group_data)
            mock_update_status.assert_called_once_with(self.sample_group_data)

    @patch('jd.jobs.tg_group_info.db.session')
    def test_process_single_group_new_group(self, mock_db_session):
        """测试处理新群组"""
        # Mock不存在的群组
        mock_db_session.query().filter_by().first.return_value = None
        
        with patch.object(TgGroupInfoManager, '_create_new_group') as mock_create_new, \
             patch.object(TgGroupInfoManager, '_update_group_status', return_value=1) as mock_update_status:
            
            result = TgGroupInfoManager._process_single_group(self.sample_group_data)
            
            self.assertTrue(result['is_new'])
            self.assertEqual(result['member_changes'], 1)
            self.assertEqual(result['info_changes'], 0)
            
            mock_create_new.assert_called_once_with(self.sample_group_data)
            mock_update_status.assert_called_once_with(self.sample_group_data)

    @patch('jd.jobs.tg_group_info.db.session')
    def test_update_existing_group_with_changes(self, mock_db_session):
        """测试更新现有群组（有变化）"""
        # Mock现有群组
        mock_existing_group = Mock()
        mock_existing_group.chat_id = str(self.sample_group_data['id'])
        mock_existing_group.name = 'old_name'
        mock_existing_group.desc = 'old_desc'
        mock_existing_group.title = 'old_title'
        mock_existing_group.avatar_path = 'old_avatar.jpg'
        
        with patch.object(TgGroupInfoManager, '_record_group_info_change') as mock_record_change:
            changes_count = TgGroupInfoManager._update_existing_group(mock_existing_group, self.sample_group_data)
            
            # 验证变化次数
            self.assertEqual(changes_count, 4)  # 4个字段都有变化
            
            # 验证记录变化的调用
            self.assertEqual(mock_record_change.call_count, 4)
            mock_db_session.commit.assert_called_once()

    @patch('jd.jobs.tg_group_info.db.session')
    def test_update_existing_group_no_changes(self, mock_db_session):
        """测试更新现有群组（无变化）"""
        # Mock现有群组（值与新数据相同）
        mock_existing_group = Mock()
        mock_existing_group.chat_id = str(self.sample_group_data['id'])
        mock_existing_group.name = self.sample_group_data['username']
        mock_existing_group.desc = self.sample_group_data['channel_description']
        mock_existing_group.title = self.sample_group_data['title']
        mock_existing_group.avatar_path = self.sample_group_data['photo_path']
        
        with patch.object(TgGroupInfoManager, '_record_group_info_change') as mock_record_change:
            changes_count = TgGroupInfoManager._update_existing_group(mock_existing_group, self.sample_group_data)
            
            # 验证无变化
            self.assertEqual(changes_count, 0)
            mock_record_change.assert_not_called()
            mock_db_session.commit.assert_not_called()

    @patch('jd.jobs.tg_group_info.db.session')
    def test_create_new_group(self, mock_db_session):
        """测试创建新群组"""
        with patch('jd.jobs.tg_group_info.TgGroup') as mock_tg_group_class:
            mock_group = Mock()
            mock_tg_group_class.return_value = mock_group
            mock_group.title = self.sample_group_data['title']
            
            TgGroupInfoManager._create_new_group(self.sample_group_data)
            
            # 验证TgGroup被正确创建
            mock_tg_group_class.assert_called_once()
            call_args = mock_tg_group_class.call_args[1]  # 获取关键字参数
            self.assertEqual(call_args['chat_id'], str(self.sample_group_data['id']))
            self.assertEqual(call_args['name'], self.sample_group_data['username'])
            self.assertEqual(call_args['title'], self.sample_group_data['title'])
            
            # 验证数据库操作
            mock_db_session.add.assert_called_once_with(mock_group)
            mock_db_session.commit.assert_called_once()

    @patch('jd.jobs.tg_group_info.db.session')
    def test_update_group_status_existing_with_member_change(self, mock_db_session):
        """测试更新群组状态（现有记录，成员数有变化）"""
        # Mock现有状态记录
        mock_existing_status = Mock()
        mock_existing_status.members_now = 80
        mock_db_session.query().filter_by().first.return_value = mock_existing_status
        
        with patch.object(TgGroupInfoManager, '_update_message_stats') as mock_update_stats:
            result = TgGroupInfoManager._update_group_status(self.sample_group_data)
            
            # 验证返回值表示有变化
            self.assertEqual(result, 1)
            
            # 验证成员数更新
            self.assertEqual(mock_existing_status.members_previous, 80)
            self.assertEqual(mock_existing_status.members_now, 100)
            
            # 验证其他操作
            mock_update_stats.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @patch('jd.jobs.tg_group_info.db.session')
    def test_update_group_status_existing_no_member_change(self, mock_db_session):
        """测试更新群组状态（现有记录，成员数无变化）"""
        # Mock现有状态记录（成员数相同）
        mock_existing_status = Mock()
        mock_existing_status.members_now = 100  # 与sample_group_data中的相同
        mock_db_session.query().filter_by().first.return_value = mock_existing_status
        
        with patch.object(TgGroupInfoManager, '_update_message_stats') as mock_update_stats:
            result = TgGroupInfoManager._update_group_status(self.sample_group_data)
            
            # 验证返回值表示无变化
            self.assertEqual(result, 0)
            
            # 验证成员数仍然被更新（按照需求）
            self.assertEqual(mock_existing_status.members_previous, 100)
            self.assertEqual(mock_existing_status.members_now, 100)
            
            # 验证其他操作仍然执行
            mock_update_stats.assert_called_once()
            mock_db_session.commit.assert_called_once()

    @patch('jd.jobs.tg_group_info.db.session')
    def test_update_group_status_new_record(self, mock_db_session):
        """测试更新群组状态（新记录）"""
        # Mock不存在的状态记录
        mock_db_session.query().filter_by().first.return_value = None
        
        with patch('jd.jobs.tg_group_info.TgGroupStatus') as mock_status_class, \
             patch.object(TgGroupInfoManager, '_update_message_stats') as mock_update_stats:
            
            mock_new_status = Mock()
            mock_status_class.return_value = mock_new_status
            
            result = TgGroupInfoManager._update_group_status(self.sample_group_data)
            
            # 验证返回值表示是新记录
            self.assertEqual(result, 1)
            
            # 验证TgGroupStatus被正确创建
            mock_status_class.assert_called_once()
            call_args = mock_status_class.call_args[1]
            self.assertEqual(call_args['chat_id'], str(self.sample_group_data['id']))
            self.assertEqual(call_args['members_now'], 100)
            self.assertEqual(call_args['members_previous'], 0)
            
            # 验证数据库操作
            mock_update_stats.assert_called_once()
            mock_db_session.add.assert_called_once_with(mock_new_status)
            mock_db_session.commit.assert_called_once()

    @patch('jd.jobs.tg_group_info.db.session')
    def test_record_group_info_change(self, mock_db_session):
        """测试记录群组信息变化"""
        with patch('jd.jobs.tg_group_info.TgGroupInfoChange') as mock_change_class, \
             patch('jd.jobs.tg_group_info.datetime') as mock_datetime:
            
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            
            mock_change_record = Mock()
            mock_change_class.return_value = mock_change_record
            
            TgGroupInfoManager._record_group_info_change(
                chat_id='123456789',
                changed_field=TgGroupInfoChange.ChangedFieldType.DISPLAY_NAME,
                old_value='old_title',
                new_value='new_title'
            )
            
            # 验证TgGroupInfoChange被正确创建
            mock_change_class.assert_called_once_with(
                chat_id='123456789',
                changed_fields=TgGroupInfoChange.ChangedFieldType.DISPLAY_NAME,
                original_value='old_title',
                new_value='new_title',
                update_time=mock_now
            )
            
            # 验证数据库操作
            mock_db_session.add.assert_called_once_with(mock_change_record)
            mock_db_session.commit.assert_called_once()

    @patch('jd.jobs.tg_group_info.db.session')
    def test_record_group_info_change_with_error(self, mock_db_session):
        """测试记录群组信息变化时发生错误"""
        with patch('jd.jobs.tg_group_info.TgGroupInfoChange') as mock_change_class:
            # Mock数据库操作抛出异常
            mock_db_session.add.side_effect = Exception("Database error")
            
            mock_change_record = Mock()
            mock_change_class.return_value = mock_change_record
            
            # 测试不应该抛出异常
            try:
                TgGroupInfoManager._record_group_info_change(
                    chat_id='123456789',
                    changed_field=TgGroupInfoChange.ChangedFieldType.DISPLAY_NAME,
                    old_value='old_title',
                    new_value='new_title'
                )
            except Exception:
                self.fail("_record_group_info_change should handle exceptions gracefully")
            
            # 验证回滚被调用
            mock_db_session.rollback.assert_called_once()

    @patch('jd.jobs.tg_group_info.TgService.init_tg')
    def test_sync_group_info_by_account_success(self, mock_init_tg):
        """测试根据账户ID同步群组信息（成功）"""
        # Mock TG服务
        mock_tg_service = Mock()
        mock_init_tg.return_value = mock_tg_service
        
        # Mock同步结果
        expected_result = {
            'success': True,
            'message': '同步完成',
            'stats': {'total_groups': 1}
        }
        
        with patch.object(TgGroupInfoManager, 'sync_all_group_info', return_value=expected_result) as mock_sync:
            result = TgGroupInfoManager.sync_group_info_by_account(123)
            
            # 验证结果
            self.assertEqual(result, expected_result)
            
            # 验证TG服务被正确初始化和关闭
            mock_init_tg.assert_called_once_with('group_sync')
            mock_sync.assert_called_once_with(mock_tg_service)
            mock_tg_service.close_client.assert_called_once()

    @patch('jd.jobs.tg_group_info.TgService.init_tg')
    def test_sync_group_info_by_account_tg_init_failed(self, mock_init_tg):
        """测试根据账户ID同步群组信息（TG服务初始化失败）"""
        # Mock TG服务初始化失败
        mock_init_tg.return_value = None
        
        result = TgGroupInfoManager.sync_group_info_by_account(123)
        
        # 验证失败结果
        self.assertFalse(result['success'])
        self.assertIn('TG服务初始化失败', result['message'])

    @patch('jd.jobs.tg_group_info.TgService.init_tg')
    def test_sync_group_info_by_account_exception(self, mock_init_tg):
        """测试根据账户ID同步群组信息（发生异常）"""
        # Mock TG服务初始化时抛出异常
        mock_init_tg.side_effect = Exception("Init error")
        
        result = TgGroupInfoManager.sync_group_info_by_account(123)
        
        # 验证异常被正确处理
        self.assertFalse(result['success'])
        self.assertIn('同步失败', result['message'])
        self.assertIn('Init error', result['message'])


class TestTgGroupInfoManagerIntegration(unittest.TestCase):
    """集成测试（需要真实数据库连接时使用）"""
    
    def setUp(self):
        """集成测试前准备"""
        # 这里可以设置测试数据库连接
        pass
    
    def test_end_to_end_sync(self):
        """端到端同步测试"""
        # 这里可以添加真实的端到端测试
        # 需要真实的数据库和TG客户端连接
        pass


def run_mock_test():
    """运行mock测试的便捷函数"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTests(loader.loadTestsFromTestCase(TestTgGroupInfoManager))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印测试结果总结
    print(f"\n测试总结:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\n失败的测试:")
        for test, error in result.failures:
            print(f"- {test}: {error}")
    
    if result.errors:
        print(f"\n错误的测试:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_mock_test()
    print(f"\n测试{'成功' if success else '失败'}")
    exit(0 if success else 1)
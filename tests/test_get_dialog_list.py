import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jd.services.spider.telegram_spider import TelegramAPIs
from telethon.tl.types import Channel, Chat


class TestGetDialogList(unittest.TestCase):
    """测试TelegramAPIs.get_dialog_list方法"""

    def setUp(self):
        """测试前准备"""
        self.api = TelegramAPIs()
        
        # Mock client
        self.mock_client = AsyncMock()
        self.api.client = self.mock_client
        
        # 示例频道数据
        self.sample_channel_data = {
            'id': 123456789,
            'title': '测试频道',
            'username': 'test_channel',
            'date': datetime(2023, 1, 1, 12, 0, 0)
        }
        
        # 示例群组数据  
        self.sample_chat_data = {
            'id': 987654321,
            'title': '测试群组',
            'date': datetime(2023, 1, 1, 12, 0, 0)
        }

    def create_mock_dialog(self, entity_type='channel', entity_data=None, unread_count=5):
        """创建模拟对话对象"""
        mock_dialog = Mock()
        mock_dialog.unread_count = unread_count
        
        if entity_type == 'channel':
            entity_data = entity_data or self.sample_channel_data
            mock_entity = Mock(spec=Channel)
            mock_entity.id = entity_data['id']
            mock_entity.title = entity_data['title']
            mock_entity.username = entity_data.get('username')
            mock_entity.date = entity_data['date']
        elif entity_type == 'chat':
            entity_data = entity_data or self.sample_chat_data
            mock_entity = Mock(spec=Chat)
            mock_entity.id = entity_data['id']
            mock_entity.title = entity_data['title']
            mock_entity.date = entity_data['date']
        else:
            # 个人对话或其他类型，不包含title属性
            mock_entity = Mock()
            if hasattr(mock_entity, 'title'):
                delattr(mock_entity, 'title')
        
        mock_dialog.entity = mock_entity
        return mock_dialog

    def create_mock_channel_full(self, megagroup=False, member_count=100, description='测试描述'):
        """创建模拟频道完整信息"""
        mock_channel_full = Mock()
        mock_channel_full.full_chat.participants_count = member_count
        mock_channel_full.full_chat.about = description
        
        # 模拟频道信息
        mock_chat = Mock()
        mock_chat.megagroup = megagroup
        mock_chat.username = 'test_channel' if not megagroup else None
        mock_channel_full.chats = [mock_chat]
        
        return mock_channel_full

    def create_mock_chat_full(self, member_count=50, description='群组描述'):
        """创建模拟群组完整信息"""
        mock_chat_full = Mock()
        mock_chat_full.full_chat.about = description
        
        # 模拟群组信息
        mock_chat = Mock()
        mock_chat.participants_count = member_count
        mock_chat_full.chats = [mock_chat]
        
        return mock_chat_full

    @patch('jd.services.spider.telegram_spider.app.static_folder', '/fake/static')
    @patch('os.path.join')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._ensure_directory')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._download_avatar')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._process_channel_username')
    async def test_get_dialog_list_channel_success(self, mock_process_username, mock_download_avatar,
                                                  mock_ensure_directory, mock_path_join):
        """测试获取频道对话列表（成功）"""
        # 设置模拟返回值
        mock_path_join.return_value = '/fake/static/images/avatar'
        mock_process_username.return_value = 'test_channel'
        mock_download_avatar.return_value = 'avatar_path.jpg'
        
        # 创建模拟对话
        mock_dialog = self.create_mock_dialog('channel')
        mock_channel_full = self.create_mock_channel_full(megagroup=False)
        
        # 设置客户端返回值
        self.mock_client.iter_dialogs.return_value.__aiter__ = AsyncMock(return_value=[mock_dialog])
        self.mock_client.return_value = mock_channel_full
        
        # 执行测试
        results = []
        async for result in self.api.get_dialog_list():
            results.append(result)
        
        # 验证结果
        self.assertEqual(len(results), 1)
        result = results[0]
        
        self.assertEqual(result['result'], 'success')
        self.assertEqual(result['reason'], 'ok')
        
        data = result['data']
        self.assertEqual(data['id'], 123456789)
        self.assertEqual(data['title'], '测试频道')
        self.assertEqual(data['username'], 'test_channel')
        self.assertEqual(data['megagroup'], 'channel')
        self.assertEqual(data['member_count'], 100)
        self.assertEqual(data['channel_description'], '测试描述')
        self.assertEqual(data['is_public'], 1)
        self.assertEqual(data['unread_count'], 5)
        self.assertEqual(data['group_type'], 'channel')
        self.assertEqual(data['photo_path'], 'avatar_path.jpg')
        
        # 验证方法调用
        mock_ensure_directory.assert_called_once()
        mock_process_username.assert_called_once()
        mock_download_avatar.assert_called_once()

    @patch('jd.services.spider.telegram_spider.app.static_folder', '/fake/static')
    @patch('os.path.join')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._ensure_directory')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._download_avatar')
    async def test_get_dialog_list_chat_success(self, mock_download_avatar, mock_ensure_directory, mock_path_join):
        """测试获取群组对话列表（成功）"""
        # 设置模拟返回值
        mock_path_join.return_value = '/fake/static/images/avatar'
        mock_download_avatar.return_value = 'chat_avatar.jpg'
        
        # 创建模拟对话
        mock_dialog = self.create_mock_dialog('chat')
        mock_chat_full = self.create_mock_chat_full()
        
        # 设置客户端返回值
        self.mock_client.iter_dialogs.return_value.__aiter__ = AsyncMock(return_value=[mock_dialog])
        self.mock_client.return_value = mock_chat_full
        
        # 执行测试
        results = []
        async for result in self.api.get_dialog_list():
            results.append(result)
        
        # 验证结果
        self.assertEqual(len(results), 1)
        result = results[0]
        
        self.assertEqual(result['result'], 'success')
        data = result['data']
        self.assertEqual(data['id'], 987654321)
        self.assertEqual(data['title'], '测试群组')
        self.assertIsNone(data['username'])
        self.assertEqual(data['megagroup'], 'group')
        self.assertEqual(data['member_count'], 50)
        self.assertEqual(data['is_public'], 0)  # 无username，非公开
        self.assertEqual(data['group_type'], 'chat')

    @patch('jd.services.spider.telegram_spider.app.static_folder', '/fake/static')
    @patch('os.path.join')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._ensure_directory')
    async def test_get_dialog_list_skip_personal_chats(self, mock_ensure_directory, mock_path_join):
        """测试跳过个人对话"""
        mock_path_join.return_value = '/fake/static/images/avatar'
        
        # 创建个人对话（没有title属性）
        mock_dialog = self.create_mock_dialog('user')
        
        # 设置客户端返回值
        self.mock_client.iter_dialogs.return_value.__aiter__ = AsyncMock(return_value=[mock_dialog])
        
        # 执行测试
        results = []
        async for result in self.api.get_dialog_list():
            results.append(result)
        
        # 验证结果：应该返回一个空的成功响应
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result['result'], 'success')
        self.assertEqual(result['data'], {})

    @patch('jd.services.spider.telegram_spider.app.static_folder', '/fake/static')
    @patch('os.path.join')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._ensure_directory')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._download_avatar')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._process_channel_username')
    async def test_get_dialog_list_mixed_types(self, mock_process_username, mock_download_avatar,
                                              mock_ensure_directory, mock_path_join):
        """测试混合类型对话列表"""
        mock_path_join.return_value = '/fake/static/images/avatar'
        mock_process_username.return_value = 'test_channel'
        mock_download_avatar.return_value = 'avatar.jpg'
        
        # 创建不同类型的对话
        channel_dialog = self.create_mock_dialog('channel')
        chat_dialog = self.create_mock_dialog('chat')
        user_dialog = self.create_mock_dialog('user')  # 个人对话，应该被跳过
        
        mock_channel_full = self.create_mock_channel_full()
        mock_chat_full = self.create_mock_chat_full()
        
        # 设置客户端返回值
        self.mock_client.iter_dialogs.return_value.__aiter__ = AsyncMock(
            return_value=[channel_dialog, chat_dialog, user_dialog]
        )
        
        # 为不同调用设置不同返回值
        self.mock_client.side_effect = [mock_channel_full, mock_chat_full]
        
        # 执行测试
        results = []
        async for result in self.api.get_dialog_list():
            results.append(result)
        
        # 验证结果：应该有3个结果（2个有效对话 + 1个跳过的个人对话）
        self.assertEqual(len(results), 3)
        
        # 验证频道
        channel_result = results[0]
        self.assertEqual(channel_result['data']['group_type'], 'channel')
        
        # 验证群组
        chat_result = results[1]
        self.assertEqual(chat_result['data']['group_type'], 'chat')
        
        # 验证个人对话被跳过
        user_result = results[2]
        self.assertEqual(user_result['data'], {})

    @patch('jd.services.spider.telegram_spider.app.static_folder', '/fake/static')
    @patch('os.path.join')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._ensure_directory')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._download_avatar')
    @patch('jd.services.spider.telegram_spider.TelegramAPIs._process_channel_username')
    async def test_get_dialog_list_supergroup(self, mock_process_username, mock_download_avatar,
                                             mock_ensure_directory, mock_path_join):
        """测试超级群组（megagroup=True的频道）"""
        mock_path_join.return_value = '/fake/static/images/avatar'
        mock_process_username.return_value = 'supergroup'
        mock_download_avatar.return_value = 'supergroup.jpg'
        
        # 创建超级群组（megagroup=True的频道）
        mock_dialog = self.create_mock_dialog('channel')
        mock_channel_full = self.create_mock_channel_full(megagroup=True)
        
        self.mock_client.iter_dialogs.return_value.__aiter__ = AsyncMock(return_value=[mock_dialog])
        self.mock_client.return_value = mock_channel_full
        
        # 执行测试
        results = []
        async for result in self.api.get_dialog_list():
            results.append(result)
        
        # 验证结果
        self.assertEqual(len(results), 1)
        data = results[0]['data']
        self.assertEqual(data['megagroup'], 'group')  # megagroup=True应该显示为'group'
        self.assertEqual(data['group_type'], 'group')
        self.assertEqual(data['is_public'], 0)  # 超级群组通常没有username

    def test_sync_method(self):
        """测试同步方法包装器"""
        # 由于get_dialog_list是异步方法，可能需要同步包装器
        # 这里测试如果存在同步版本的话
        
        # 创建事件循环来运行异步测试
        async def run_test():
            # 这里可以运行上面的任何一个异步测试
            pass
        
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_test())
        finally:
            loop.close()

    def test_error_handling(self):
        """测试错误处理"""
        # 可以添加测试异常情况的测试用例
        pass


def run_dialog_list_tests():
    """运行get_dialog_list测试的便捷函数"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTests(loader.loadTestsFromTestCase(TestGetDialogList))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印测试结果总结
    print(f"\nget_dialog_list 测试总结:")
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
    success = run_dialog_list_tests()
    print(f"\n测试{'成功' if success else '失败'}")
    exit(0 if success else 1)
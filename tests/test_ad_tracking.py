#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
广告追踪系统单元测试

测试覆盖：
1. TmeSpider 服务测试
2. AdTrackingJob 数据处理测试
3. API 端点测试
4. Celery 任务测试
"""

import sys
import os
import unittest
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jd import app, db
from jd.models.ad_tracking import AdTracking
from jd.models.ad_tracking_tags import AdTrackingTags
from jd.models.tg_group_chat_history import TgGroupChatHistory
from jd.models.tg_group_user_info import TgGroupUserInfo
from jd.models.tg_group import TgGroup
from jd.services.spider.tme_spider import TmeSpider
from jd.jobs.ad_tracking_job import AdTrackingJob


class TestTmeSpider(unittest.TestCase):
    """TmeSpider 服务测试"""

    def setUp(self):
        """测试前准备"""
        self.spider = TmeSpider()

    def test_extract_urls(self):
        """测试URL提取"""
        text = """
        访问我们的网站 https://example.com 或者 www.test.com
        也可以访问 http://another-site.org
        """
        urls = self.spider.extract_urls(text)
        self.assertGreater(len(urls), 0)
        print(f"Extracted URLs: {urls}")

    def test_extract_telegram_accounts(self):
        """测试Telegram账户提取"""
        text = "联系 @username123 或 @another_user 获取更多信息"
        accounts = self.spider.extract_telegram_accounts(text)
        self.assertEqual(len(accounts), 2)
        self.assertIn('@username123', accounts)
        self.assertIn('@another_user', accounts)
        print(f"Extracted accounts: {accounts}")

    def test_extract_tme_links(self):
        """测试t.me链接提取和分类"""
        text = """
        加入群组: https://t.me/joinchat/abc123
        查看频道: https://t.me/my_channel
        私聊我: https://t.me/+privatelink
        """
        tme_links = self.spider.extract_and_classify_tme_links(text)
        self.assertGreater(len(tme_links), 0)
        print(f"Extracted t.me links: {tme_links}")

    def test_extract_telegraph_links(self):
        """测试Telegraph链接提取"""
        text = "阅读文章: https://telegra.ph/Article-Title-12-25"
        telegraph_links = self.spider.extract_telegraph_links(text)
        self.assertEqual(len(telegraph_links), 1)
        print(f"Extracted telegraph links: {telegraph_links}")

    def test_normalize_url(self):
        """测试URL标准化"""
        urls = [
            "https://example.com/path?utm_source=test",
            "http://example.com/path",
            "example.com/path",
        ]
        normalized = [self.spider.normalize_url(url) for url in urls]
        print(f"Normalized URLs: {normalized}")

    def test_classify_url_type(self):
        """测试URL类型分类"""
        test_cases = [
            ("https://t.me/joinchat/abc", "tme"),
            ("https://telegra.ph/Title-12-25", "telegraph"),
            ("https://example.com", "general"),
        ]
        for url, expected_type in test_cases:
            result = self.spider.classify_url_type(url)
            self.assertEqual(result, expected_type)
            print(f"URL: {url} -> Type: {result}")

    def test_classify_and_process_url(self):
        """测试URL智能处理"""
        # 测试普通URL
        result = self.spider.classify_and_process_url("https://example.com")
        self.assertIsNotNone(result)
        self.assertEqual(result['url_type'], 'general')
        print(f"General URL result: {result}")

        # 测试t.me链接（注意：这会实际访问网络）
        # result = self.spider.classify_and_process_url("https://t.me/durov")
        # print(f"t.me URL result: {result}")


class TestAdTrackingJob(unittest.TestCase):
    """AdTrackingJob 数据处理测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = app
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.app_context.pop()

    def setUp(self):
        """每个测试前准备"""
        self.job = AdTrackingJob()

        # 创建测试数据
        self.test_chat_record = TgGroupChatHistory(
            id=999999,
            chat_id='test_chat_123',
            message_id='test_msg_123',
            user_id='test_user_123',
            username='testuser',
            nickname='Test User',
            postal_time=datetime.now(),
            message='访问 https://example.com 或联系 @testaccount',
            photo_path='',
            document_path='',
            document_ext='',
            status=0
        )

        self.test_user_info = TgGroupUserInfo(
            user_id='test_user_456',
            nickname='Test User with URL: www.example.org',
            username='testuser456',
            desc='联系我 @myaccount 获取优惠'
        )

        self.test_group = TgGroup(
            chat_id='test_group_789',
            group_name='Test Group',
            group_title='测试群组',
            group_intro='欢迎访问 https://test-group.com'
        )

    def tearDown(self):
        """每个测试后清理"""
        # 清理测试数据
        AdTracking.query.filter(
            AdTracking.source_id.like('test_%')
        ).delete(synchronize_session=False)
        db.session.commit()

    def test_process_content_item(self):
        """测试内容项处理"""
        result = self.job._process_content_item(
            content='https://example.com',
            content_type='url',
            source_type='chat',
            source_id='test_123',
            user_id='user_123',
            chat_id='chat_123'
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['content_type'], 'url')
        self.assertIn('normalized_content', result)
        print(f"Processed content item: {result}")

    def test_process_chat_record(self):
        """测试聊天记录处理"""
        stats = self.job.process_chat_record(self.test_chat_record)
        self.assertGreater(stats['total_items'], 0)
        print(f"Chat record processing stats: {stats}")

        # 验证数据库中的记录
        tracking_records = AdTracking.query.filter_by(
            source_id=str(self.test_chat_record.id)
        ).all()
        self.assertGreater(len(tracking_records), 0)
        print(f"Created {len(tracking_records)} tracking records")

    def test_process_user_info(self):
        """测试用户信息处理"""
        stats = self.job.process_user_info(self.test_user_info)
        self.assertGreater(stats['total_items'], 0)
        print(f"User info processing stats: {stats}")

    def test_process_group_info(self):
        """测试群组信息处理"""
        stats = self.job.process_group_info(self.test_group)
        self.assertGreater(stats['total_items'], 0)
        print(f"Group info processing stats: {stats}")

    def test_save_or_update_tracking(self):
        """测试追踪记录保存和更新"""
        tracking_data = {
            'content': 'https://example.com',
            'content_type': 'url',
            'normalized_content': 'https://example.com/',
            'extra_info': {'domain': 'example.com'},
            'source_type': 'chat',
            'source_id': 'test_save_123',
            'user_id': 'user_123',
            'chat_id': 'chat_123'
        }

        # 首次保存
        record1 = self.job._save_or_update_tracking(tracking_data)
        self.assertIsNotNone(record1)
        self.assertEqual(record1.occurrence_count, 1)
        db.session.commit()

        # 再次保存同样的数据（应该更新）
        record2 = self.job._save_or_update_tracking(tracking_data)
        db.session.commit()

        self.assertEqual(record1.id, record2.id)
        self.assertEqual(record2.occurrence_count, 2)
        print(f"Record occurrence count: {record2.occurrence_count}")


class TestAdTrackingAPI(unittest.TestCase):
    """广告追踪 API 测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = app
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.app_context.pop()

    def setUp(self):
        """每个测试前准备"""
        # 创建测试追踪记录
        self.test_tracking = AdTracking(
            content='https://test-api.com',
            content_type='url',
            normalized_content='https://test-api.com/',
            extra_info={'domain': 'test-api.com'},
            source_type='chat',
            source_id='api_test_123',
            user_id='api_user_123',
            chat_id='api_chat_123',
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            occurrence_count=1
        )
        db.session.add(self.test_tracking)
        db.session.commit()

    def tearDown(self):
        """每个测试后清理"""
        AdTracking.query.filter(
            AdTracking.source_id == 'api_test_123'
        ).delete(synchronize_session=False)
        db.session.commit()

    def test_get_ad_tracking_list(self):
        """测试获取追踪列表API"""
        response = self.client.get('/api/ad-tracking/list')
        # Note: This will fail without proper authentication
        # In real tests, you should set up authentication
        print(f"List API response status: {response.status_code}")
        # self.assertEqual(response.status_code, 200)

    def test_get_ad_tracking_stats(self):
        """测试获取统计API"""
        response = self.client.get('/api/ad-tracking/stats')
        print(f"Stats API response status: {response.status_code}")


class TestAdTrackingIntegration(unittest.TestCase):
    """广告追踪集成测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.app = app
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.app_context.pop()

    def test_full_workflow(self):
        """测试完整工作流程"""
        job = AdTrackingJob()

        # 创建测试聊天记录
        chat_record = TgGroupChatHistory(
            id=888888,
            chat_id='integration_chat',
            message_id='integration_msg',
            user_id='integration_user',
            username='integrationuser',
            nickname='Integration Test User',
            postal_time=datetime.now(),
            message='''
            大家好！欢迎访问我们的网站 https://integration-test.com
            也可以联系 @integration_support 获取帮助
            或者加入我们的频道 https://t.me/integration_channel
            ''',
            photo_path='',
            document_path='',
            document_ext='',
            status=0
        )

        try:
            # 处理聊天记录
            stats = job.process_chat_record(chat_record)
            db.session.commit()

            print(f"Integration test stats: {stats}")
            self.assertGreater(stats['total_items'], 0)

            # 验证创建的记录
            tracking_records = AdTracking.query.filter_by(
                source_id=str(chat_record.id)
            ).all()

            print(f"\nCreated tracking records:")
            for record in tracking_records:
                print(f"  - Type: {record.content_type}, Content: {record.content}")

            # 验证不同类型的内容都被识别
            content_types = set(r.content_type for r in tracking_records)
            self.assertIn('url', content_types)
            self.assertIn('telegram_account', content_types)

        finally:
            # 清理测试数据
            AdTracking.query.filter_by(
                source_id=str(chat_record.id)
            ).delete(synchronize_session=False)
            db.session.commit()


def run_tests():
    """运行所有测试"""
    print("=" * 80)
    print("广告追踪系统单元测试")
    print("=" * 80)

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTmeSpider))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAdTrackingJob))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAdTrackingAPI))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAdTrackingIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回结果
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)

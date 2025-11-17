#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TmeSpider.analyze_url() 单元测试（使用模拟）

验证新增的综合 URL 分析方法的结构和集成
"""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, '.')

# 初始化应用
from jd import Application
app = Application()
app.ready()

from jd.services.spider.tme_spider import TmeSpider


class TestAnalyzeUrlStructure:
    """TmeSpider.analyze_url() 结构测试"""

    @pytest.fixture
    def spider(self):
        """创建 spider 实例"""
        return TmeSpider()

    def test_analyze_url_method_exists(self, spider):
        """测试 analyze_url() 方法存在"""
        assert hasattr(spider, 'analyze_url')
        assert callable(getattr(spider, 'analyze_url'))
        print("✓ analyze_url() 方法存在")

    def test_analyze_url_returns_dict(self, spider):
        """测试 analyze_url() 返回字典"""
        with patch.object(spider, 'get_website_basic_info', return_value={'error': 'mock'}):
            with patch.object(spider, 'check_phishing_url', return_value={}):
                with patch.object(spider, '_get_certificate_info', return_value={}):
                    result = spider.analyze_url('https://example.com')
                    assert isinstance(result, dict)
                    print("✓ analyze_url() 返回字典类型")

    def test_analyze_url_required_fields(self, spider):
        """测试 analyze_url() 包含所有必需字段"""
        with patch.object(spider, 'get_website_basic_info', return_value={}):
            with patch.object(spider, 'check_phishing_url', return_value={}):
                with patch.object(spider, '_get_certificate_info', return_value={}):
                    result = spider.analyze_url('https://example.com')

                    required_fields = [
                        'title', 'status_code', 'content_type', 'server',
                        'ip_address', 'ip_location', 'is_short_url',
                        'redirect_chain_length', 'phishing', 'certificate'
                    ]

                    for field in required_fields:
                        assert field in result, f"缺少字段: {field}"

                    print("✓ analyze_url() 包含所有必需字段")
                    print(f"  字段数: {len(result)}")

    def test_analyze_url_field_types(self, spider):
        """测试 analyze_url() 字段类型"""
        mock_basic_info = {
            'title': 'Example Title',
            'status_code': 200,
            'content_type': 'text/html',
            'ip_address': '93.184.216.34',
            'ip_location': {'country': 'US'},
            'is_short_url': False,
            'redirect_chain_length': 0
        }

        with patch.object(spider, 'get_website_basic_info', return_value=mock_basic_info):
            with patch.object(spider, 'check_phishing_url', return_value={}):
                with patch.object(spider, '_get_certificate_info', return_value={}):
                    result = spider.analyze_url('https://example.com')

                    assert isinstance(result['title'], str) or result['title'] is None
                    assert isinstance(result['status_code'], int) or result['status_code'] is None
                    assert isinstance(result['content_type'], str)
                    assert isinstance(result['server'], str)
                    assert isinstance(result['ip_address'], str) or result['ip_address'] is None
                    assert isinstance(result['ip_location'], dict)
                    assert isinstance(result['is_short_url'], bool)
                    assert isinstance(result['redirect_chain_length'], int)
                    assert isinstance(result['phishing'], dict)
                    assert isinstance(result['certificate'], dict)

                    print("✓ analyze_url() 字段类型正确")

    def test_analyze_url_merges_basic_info(self, spider):
        """测试 analyze_url() 合并基本信息"""
        mock_basic_info = {
            'title': 'Example Title',
            'status_code': 200,
            'content_type': 'text/html',
            'ip_address': '93.184.216.34',
            'ip_location': {'country': 'US'},
            'is_short_url': False,
            'redirect_chain_length': 0
        }

        with patch.object(spider, 'get_website_basic_info', return_value=mock_basic_info):
            with patch.object(spider, 'check_phishing_url', return_value={}):
                with patch.object(spider, '_get_certificate_info', return_value={}):
                    result = spider.analyze_url('https://example.com')

                    # 验证基本信息被正确合并
                    assert result['title'] == 'Example Title'
                    assert result['status_code'] == 200
                    assert result['content_type'] == 'text/html'
                    assert result['ip_address'] == '93.184.216.34'
                    assert result['ip_location'] == {'country': 'US'}
                    assert result['is_short_url'] is False
                    assert result['redirect_chain_length'] == 0

                    print("✓ analyze_url() 正确合并基本信息")

    def test_analyze_url_includes_phishing_info(self, spider):
        """测试 analyze_url() 包含钓鱼信息"""
        mock_phishing_info = {
            'is_phishing': False,
            'threat_types': []
        }

        with patch.object(spider, 'get_website_basic_info', return_value={}):
            with patch.object(spider, 'check_phishing_url', return_value=mock_phishing_info):
                with patch.object(spider, '_get_certificate_info', return_value={}):
                    result = spider.analyze_url('https://example.com')

                    assert result['phishing'] == mock_phishing_info
                    print("✓ analyze_url() 正确包含钓鱼信息")

    def test_analyze_url_includes_certificate_info(self, spider):
        """测试 analyze_url() 包含证书信息"""
        mock_cert_info = {
            'issuer': 'Let\'s Encrypt',
            'valid_from': '2024-01-01',
            'valid_to': '2025-01-01'
        }

        with patch.object(spider, 'get_website_basic_info', return_value={}):
            with patch.object(spider, 'check_phishing_url', return_value={}):
                with patch.object(spider, '_get_certificate_info', return_value=mock_cert_info):
                    result = spider.analyze_url('https://example.com')

                    assert result['certificate'] == mock_cert_info
                    print("✓ analyze_url() 正确包含证书信息")

    def test_analyze_url_handles_error_from_basic_info(self, spider):
        """测试 analyze_url() 处理基本信息错误"""
        mock_error_info = {
            'error': 'network_error',
            'domain': 'example.com'
        }

        with patch.object(spider, 'get_website_basic_info', return_value=mock_error_info):
            with patch.object(spider, 'check_phishing_url', return_value={}):
                with patch.object(spider, '_get_certificate_info', return_value={}):
                    result = spider.analyze_url('https://example.com')

                    # 应该包含错误信息
                    assert 'error' in result
                    assert result['error'] == 'network_error'
                    print("✓ analyze_url() 正确处理基本信息错误")

    def test_get_certificate_info_method_exists(self, spider):
        """测试 _get_certificate_info() 方法存在"""
        assert hasattr(spider, '_get_certificate_info')
        assert callable(getattr(spider, '_get_certificate_info'))
        print("✓ _get_certificate_info() 方法存在")


class TestAnalyzeUrlIntegration:
    """TmeSpider.analyze_url() 集成测试"""

    @pytest.fixture
    def spider(self):
        """创建 spider 实例"""
        return TmeSpider()

    def test_analyze_url_compatible_with_ad_tracking_job(self, spider):
        """测试 analyze_url() 与 ad_tracking_job 兼容"""
        # 模拟 ad_tracking_job 调用 spider.analyze_url() 的场景

        mock_basic_info = {
            'title': 'Example',
            'status_code': 200,
            'content_type': 'text/html',
            'ip_address': '93.184.216.34',
            'ip_location': {'country': 'US'},
            'is_short_url': False,
            'redirect_chain_length': 0
        }

        with patch.object(spider, 'get_website_basic_info', return_value=mock_basic_info):
            with patch.object(spider, 'check_phishing_url', return_value={}):
                with patch.object(spider, '_get_certificate_info', return_value={}):
                    website_info = spider.analyze_url('https://example.com')

                    # 这是 ad_tracking_job 期望的用法
                    assert website_info and not website_info.get('error')

                    # ad_tracking_job 会提取这些字段
                    result_mapping = {
                        'title': website_info.get('title', ''),
                        'status_code': website_info.get('status_code'),
                        'content_type': website_info.get('content_type', ''),
                        'server': website_info.get('server', ''),
                        'ip_address': website_info.get('ip_address', ''),
                        'ip_location': website_info.get('ip_location', {}),
                        'is_short_url': website_info.get('is_short_url', False),
                        'redirect_chain_length': website_info.get('redirect_chain_length', 0),
                        'phishing': website_info.get('phishing', {}),
                        'certificate': website_info.get('certificate', {})
                    }

                    # 验证所有必需字段都可以被提取
                    for field, value in result_mapping.items():
                        assert field in website_info
                        assert value is not None or website_info.get(field) is not None

                    print("✓ analyze_url() 与 ad_tracking_job 完全兼容")


# 命令行测试入口
if __name__ == '__main__':
    # 使用 pytest 运行测试
    pytest.main([__file__, '-v', '-s'])

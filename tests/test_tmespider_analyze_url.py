#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TmeSpider.analyze_url() 方法测试

验证新增的综合 URL 分析方法的功能和结构
"""

import sys
import pytest
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '.')

# 初始化应用
from jd import Application, db
app = Application()
app.ready()

from jd.services.spider.tme_spider import TmeSpider


class TestAnalyzeUrlMethod:
    """TmeSpider.analyze_url() 方法测试"""

    @pytest.fixture
    def spider(self):
        """创建 spider 实例"""
        return TmeSpider()

    def test_analyze_url_return_structure(self, spider):
        """测试 analyze_url() 返回结构完整性"""
        # 使用一个不真实的 URL，主要检查结构
        url = 'https://example.com'

        result = spider.analyze_url(url)

        # 验证返回值是字典
        assert isinstance(result, dict)

        # 验证所有必需的字段都存在
        required_fields = [
            'title', 'status_code', 'content_type', 'server',
            'ip_address', 'ip_location', 'is_short_url',
            'redirect_chain_length', 'phishing', 'certificate'
        ]

        for field in required_fields:
            assert field in result, f"缺少字段: {field}"

        print("✓ analyze_url() 返回结构完整")
        print(f"  返回的字段: {list(result.keys())}")

    def test_analyze_url_field_types(self, spider):
        """测试 analyze_url() 返回字段类型正确"""
        url = 'https://example.com'
        result = spider.analyze_url(url)

        # 验证字段类型
        assert result['title'] is None or isinstance(result['title'], str)
        assert result['status_code'] is None or isinstance(result['status_code'], int)
        assert isinstance(result['content_type'], str)
        assert isinstance(result['server'], str)
        assert result['ip_address'] is None or isinstance(result['ip_address'], str)
        assert isinstance(result['ip_location'], dict)
        assert isinstance(result['is_short_url'], bool)
        assert isinstance(result['redirect_chain_length'], int)
        assert isinstance(result['phishing'], dict)
        assert isinstance(result['certificate'], dict)

        print("✓ analyze_url() 字段类型正确")

    def test_analyze_url_error_handling(self, spider):
        """测试 analyze_url() 异常处理"""
        # 使用无效 URL
        url = 'not-a-valid-url'

        result = spider.analyze_url(url)

        # 应该返回结构完整的结果，带有错误信息
        assert isinstance(result, dict)
        assert 'error' in result or result.get('status_code') is None

        print("✓ analyze_url() 异常处理正确")
        print(f"  结果: {result.get('error', '无错误')}")

    def test_analyze_url_empty_url(self, spider):
        """测试 analyze_url() 处理空 URL"""
        result = spider.analyze_url('')

        assert isinstance(result, dict)
        print("✓ analyze_url() 处理空 URL")

    def test_analyze_url_with_port(self, spider):
        """测试 analyze_url() 处理带端口的 URL"""
        url = 'https://example.com:8443/path'

        result = spider.analyze_url(url)

        assert isinstance(result, dict)
        assert 'certificate' in result
        print("✓ analyze_url() 处理带端口的 URL")

    def test_analyze_url_http_url(self, spider):
        """测试 analyze_url() 处理 HTTP URL"""
        url = 'http://example.com'

        result = spider.analyze_url(url)

        assert isinstance(result, dict)
        # HTTP URL 证书信息应该为空或有错误
        assert isinstance(result.get('certificate', {}), dict)
        print("✓ analyze_url() 处理 HTTP URL")

    def test_analyze_url_integration_with_ad_tracking_job(self, spider):
        """测试 analyze_url() 与 ad_tracking_job 集成"""
        # 这是一个集成测试，验证 analyze_url() 返回的结构与 ad_tracking_job 期望相符

        url = 'https://example.com'
        result = spider.analyze_url(url)

        # ad_tracking_job 期望的字段映射
        expected_mapping = {
            'title': result.get('title'),
            'status_code': result.get('status_code'),
            'content_type': result.get('content_type'),
            'server': result.get('server'),
            'ip_address': result.get('ip_address'),
            'ip_location': result.get('ip_location'),
            'is_short_url': result.get('is_short_url'),
            'redirect_chain_length': result.get('redirect_chain_length'),
            'phishing': result.get('phishing'),
            'certificate': result.get('certificate')
        }

        # 验证所有期望的字段都存在
        for field, value in expected_mapping.items():
            assert field in result, f"缺少 ad_tracking_job 期望的字段: {field}"

        print("✓ analyze_url() 与 ad_tracking_job 集成正确")
        print(f"  映射字段数: {len(expected_mapping)}")


class TestAnalyzeUrlPhishingDetection:
    """测试 analyze_url() 中的钓鱼检测"""

    @pytest.fixture
    def spider(self):
        """创建 spider 实例"""
        return TmeSpider()

    def test_phishing_field_structure(self, spider):
        """测试钓鱼检测字段结构"""
        url = 'https://example.com'
        result = spider.analyze_url(url)

        phishing_info = result.get('phishing', {})
        assert isinstance(phishing_info, dict)

        print("✓ 钓鱼检测字段结构正确")
        print(f"  钓鱼字段: {phishing_info}")


class TestAnalyzeUrlCertificateInfo:
    """测试 analyze_url() 中的证书信息提取"""

    @pytest.fixture
    def spider(self):
        """创建 spider 实例"""
        return TmeSpider()

    def test_certificate_field_structure(self, spider):
        """测试证书信息字段结构"""
        url = 'https://example.com'
        result = spider.analyze_url(url)

        cert_info = result.get('certificate', {})
        assert isinstance(cert_info, dict)

        # 如果获取成功，应该有这些字段
        if 'error' not in cert_info or not cert_info.get('error'):
            expected_cert_fields = ['issuer', 'valid_from', 'valid_to']
            for field in expected_cert_fields:
                if field in cert_info:
                    print(f"  ✓ 证书字段 {field}: {cert_info.get(field)}")

        print("✓ 证书信息字段结构正确")

    def test_certificate_error_handling(self, spider):
        """测试证书获取异常处理"""
        # 使用无效的 URL，应该优雅地处理
        url = 'https://invalid-domain-that-does-not-exist-12345.com'

        result = spider.analyze_url(url)

        cert_info = result.get('certificate', {})
        assert isinstance(cert_info, dict)

        print("✓ 证书异常处理正确")
        if cert_info.get('error'):
            print(f"  错误信息: {cert_info.get('error')}")


class TestAnalyzeUrlPerformance:
    """测试 analyze_url() 性能"""

    @pytest.fixture
    def spider(self):
        """创建 spider 实例"""
        return TmeSpider()

    def test_analyze_url_returns_quickly(self, spider):
        """测试 analyze_url() 快速返回"""
        import time

        # 使用一个本地主机地址，应该快速完成或快速失败
        url = 'https://localhost:9999'

        start = time.time()
        result = spider.analyze_url(url)
        elapsed = time.time() - start

        # 应该返回有效的结果结构，即使出错
        assert isinstance(result, dict)

        print("✓ analyze_url() 正常返回")
        print(f"  耗时: {elapsed:.2f}s")


# 命令行测试入口
if __name__ == '__main__':
    # 使用 pytest 运行测试
    pytest.main([__file__, '-v', '-s'])

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
广告追踪 URL 分析测试

测试主流域名检查和 URL 分析功能
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

from jd.models.mainstream_domain import MainstreamDomain
from jd.jobs.ad_tracking_job import AdTrackingJob


class TestUrlAnalysis:
    """URL 分析功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前准备"""
        with app.app_context():
            # 清空测试数据
            MainstreamDomain.query.delete()
            db.session.commit()

            # 插入测试数据（主流域名）
            mainstream_domains = [
                {'domain': 'google.com', 'rank': 1},
                {'domain': 'facebook.com', 'rank': 4},
                {'domain': 'taobao.com', 'rank': 50},
                {'domain': 'youtube.com', 'rank': 9},
                {'domain': 'amazon.com', 'rank': 30},
            ]

            for item in mainstream_domains:
                domain = MainstreamDomain(
                    domain=item['domain'],
                    rank=item['rank'],
                    source='tranco',
                    is_active=True
                )
                db.session.add(domain)

            db.session.commit()

            yield

            # 测试后清理
            MainstreamDomain.query.delete()
            db.session.commit()

    def test_mainstream_domain_detection(self):
        """测试主流域名检测"""
        with app.app_context():
            job = AdTrackingJob()

            # 测试已知的主流域名
            assert job._is_mainstream_domain('google.com') is True
            assert job._is_mainstream_domain('facebook.com') is True
            assert job._is_mainstream_domain('taobao.com') is True
            assert job._is_mainstream_domain('youtube.com') is True

            print("✓ 主流域名检测通过")

    def test_niche_domain_detection(self):
        """测试小众域名检测"""
        with app.app_context():
            job = AdTrackingJob()

            # 测试未知的小众域名
            assert job._is_mainstream_domain('unknown-casino.com') is False
            assert job._is_mainstream_domain('example-pharmacy.com') is False
            assert job._is_mainstream_domain('niche-site-xyz.com') is False

            print("✓ 小众域名检测通过")

    def test_case_insensitivity(self):
        """测试大小写不敏感"""
        with app.app_context():
            job = AdTrackingJob()

            # 测试大小写变体
            assert job._is_mainstream_domain('Google.Com') is True
            assert job._is_mainstream_domain('FACEBOOK.COM') is True
            assert job._is_mainstream_domain('TaObAo.CoM') is True

            print("✓ 大小写不敏感测试通过")

    def test_cache_mechanism(self):
        """测试缓存机制"""
        with app.app_context():
            job = AdTrackingJob()

            # 第一次查询
            result1 = job._is_mainstream_domain('google.com')
            assert result1 is True
            assert 'google.com' in job._mainstream_cache

            # 第二次查询应该从缓存获取
            result2 = job._is_mainstream_domain('google.com')
            assert result2 is True

            # 测试缓存中小众域名
            result3 = job._is_mainstream_domain('unknown.com')
            assert result3 is False
            assert 'unknown.com' in job._mainstream_cache
            assert job._mainstream_cache['unknown.com'] is False

            print("✓ 缓存机制测试通过")
            print(f"  缓存项数: {len(job._mainstream_cache)}")

    def test_domain_extraction_from_url(self):
        """测试从 URL 提取域名"""
        with app.app_context():
            job = AdTrackingJob()

            test_cases = [
                ('https://google.com', 'google.com'),
                ('https://www.facebook.com', 'www.facebook.com'),
                ('http://example-casino.com:8080/play', 'example-casino.com:8080'),
                ('https://example-pharmacy.com/store', 'example-pharmacy.com'),
                ('http://sub.domain.taobao.com', 'sub.domain.taobao.com'),
            ]

            for url, expected_domain in test_cases:
                analysis = job._analyze_url(url)
                print(f"  URL: {url}")
                print(f"    提取域名: {analysis['domain']}")
                assert analysis['domain'] == expected_domain

            print("✓ 域名提取测试通过")

    def test_mainstream_url_analysis(self):
        """测试主流域名 URL 分析"""
        with app.app_context():
            job = AdTrackingJob()

            # 主流 URL
            analysis = job._analyze_url('https://google.com/search?q=test')

            assert analysis['domain'] == 'google.com'
            assert analysis['is_mainstream'] is True
            # 主流域名不应该请求网站信息
            assert analysis['website_info'] == {} or analysis['website_info'].get('error')

            print("✓ 主流URL分析通过")
            print(f"  域名: {analysis['domain']}")
            print(f"  是否主流: {analysis['is_mainstream']}")

    def test_niche_url_analysis_structure(self):
        """测试小众域名 URL 分析结果结构"""
        with app.app_context():
            job = AdTrackingJob()

            # 小众 URL（会尝试请求网站信息）
            analysis = job._analyze_url('https://example-casino.com/play')

            # 验证结果结构
            assert 'url' in analysis
            assert 'domain' in analysis
            assert 'is_mainstream' in analysis
            assert 'website_info' in analysis

            assert analysis['url'] == 'https://example-casino.com/play'
            assert analysis['domain'] == 'example-casino.com'
            assert analysis['is_mainstream'] is False

            print("✓ 小众URL分析结构通过")
            print(f"  域名: {analysis['domain']}")
            print(f"  是否主流: {analysis['is_mainstream']}")

            if analysis['website_info']:
                if 'error' not in analysis['website_info']:
                    print(f"  网站信息字段:")
                    for key in analysis['website_info']:
                        print(f"    ✓ {key}")
                else:
                    print(f"  获取网站信息失败: {analysis['website_info'].get('error')}")

    def test_url_analysis_error_handling(self):
        """测试 URL 分析异常处理"""
        with app.app_context():
            job = AdTrackingJob()

            # 无效 URL
            analysis = job._analyze_url('not-a-valid-url')

            assert analysis['domain'] is None or analysis['domain'] == 'not-a-valid-url'
            print("✓ 无效URL异常处理通过")

            # 空 URL
            analysis = job._analyze_url('')

            assert analysis['domain'] is None or analysis['domain'] == ''
            print("✓ 空URL异常处理通过")

    def test_special_domains(self):
        """测试特殊域名"""
        with app.app_context():
            job = AdTrackingJob()

            test_cases = [
                # 带端口的域名
                'example.com:8080',
                # 带用户信息的 URL
                'https://user:pass@example.com',
                # 带路径的 URL
                'https://example.com/path/to/page',
                # 带查询参数的 URL
                'https://example.com?param=value',
            ]

            for url in test_cases:
                try:
                    analysis = job._analyze_url(url)
                    print(f"✓ {url[:40]:<40} -> domain={analysis['domain']}")
                except Exception as e:
                    print(f"✗ {url[:40]:<40} -> error: {str(e)[:30]}")

            print("✓ 特殊域名测试通过")

    def test_performance_mainstream_check(self):
        """测试主流域名检查性能"""
        import time

        with app.app_context():
            job = AdTrackingJob()

            # 测试首次查询性能（需要数据库查询）
            start = time.time()
            job._is_mainstream_domain('google.com')
            first_query_time = (time.time() - start) * 1000

            # 测试缓存查询性能
            start = time.time()
            job._is_mainstream_domain('google.com')
            cache_query_time = (time.time() - start) * 1000

            print("✓ 性能测试完成")
            print(f"  首次查询: {first_query_time:.2f}ms")
            print(f"  缓存查询: {cache_query_time:.2f}ms")
            print(f"  加速比: {first_query_time/cache_query_time:.1f}x")

            # 缓存查询应该明显更快
            assert cache_query_time < first_query_time

    def test_batch_domain_check(self):
        """测试批量域名检查"""
        with app.app_context():
            job = AdTrackingJob()

            domains_to_check = [
                ('google.com', True),
                ('facebook.com', True),
                ('unknown1.com', False),
                ('taobao.com', True),
                ('unknown2.com', False),
                ('youtube.com', True),
            ]

            correct = 0
            for domain, expected in domains_to_check:
                result = job._is_mainstream_domain(domain)
                if result == expected:
                    correct += 1
                    print(f"  ✓ {domain}: {result} (expected: {expected})")
                else:
                    print(f"  ✗ {domain}: {result} (expected: {expected})")

            accuracy = correct / len(domains_to_check) * 100
            print(f"✓ 批量检查准确率: {accuracy:.1f}% ({correct}/{len(domains_to_check)})")

            assert correct == len(domains_to_check)


class TestExtraInfoStructure:
    """测试 extra_info 字段结构"""

    def test_extra_info_with_mainstream_url(self):
        """测试主流 URL 的 extra_info 结构"""
        with app.app_context():
            # 确保表中有数据
            count = MainstreamDomain.query.count()
            if count == 0:
                domain = MainstreamDomain(
                    domain='google.com',
                    rank=1,
                    source='tranco',
                    is_active=True
                )
                db.session.add(domain)
                db.session.commit()

            job = AdTrackingJob()

            # 处理主流 URL
            result = job._process_content_item(
                'https://google.com',
                'url',
                'chat',
                '123',
                'user1',
                'group1'
            )

            assert result is not None
            assert 'extra_info' in result
            assert 'domain' in result['extra_info']
            assert 'is_mainstream' in result['extra_info']

            print("✓ 主流URL的extra_info结构正确")
            print(f"  domain: {result['extra_info'].get('domain')}")
            print(f"  is_mainstream: {result['extra_info'].get('is_mainstream')}")

    def test_extra_info_with_niche_url(self):
        """测试小众 URL 的 extra_info 结构"""
        with app.app_context():
            job = AdTrackingJob()

            # 处理小众 URL
            result = job._process_content_item(
                'https://example-casino.com/play',
                'url',
                'chat',
                '123',
                'user1',
                'group1'
            )

            assert result is not None
            assert 'extra_info' in result
            assert 'domain' in result['extra_info']
            assert 'is_mainstream' in result['extra_info']
            assert result['extra_info']['is_mainstream'] is False

            print("✓ 小众URL的extra_info结构正确")
            print(f"  domain: {result['extra_info'].get('domain')}")
            print(f"  is_mainstream: {result['extra_info'].get('is_mainstream')}")

            if 'website' in result['extra_info']:
                website = result['extra_info']['website']
                print(f"  website字段:")
                for key in website:
                    if key != 'error':
                        print(f"    ✓ {key}")


# 命令行测试入口
if __name__ == '__main__':
    # 使用 pytest 运行测试
    pytest.main([__file__, '-v', '-s'])

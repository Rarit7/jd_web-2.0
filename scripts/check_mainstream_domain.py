#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主流域名检查工具

快速检查一个或多个域名是否在白名单中
使用方法:
    python scripts/check_mainstream_domain.py google.com
    python scripts/check_mainstream_domain.py google.com facebook.com example.com
    python scripts/check_mainstream_domain.py < domains.txt
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, '.')


def check_domain(domain):
    """
    检查单个域名

    Args:
        domain: 域名

    Returns:
        True 如果是主流域名，False 否则
    """
    from web import app
    from jd.models.mainstream_domain import MainstreamDomain

    with app.app_context():
        result = MainstreamDomain.query.filter_by(
            domain=domain.lower().strip(),
            is_active=True
        ).first()
        return result is not None


def check_batch(domains):
    """
    批量检查域名

    Args:
        domains: 域名列表

    Returns:
        检查结果字典
    """
    from web import app
    from jd.models.mainstream_domain import MainstreamDomain

    with app.app_context():
        # 批量查询
        results = MainstreamDomain.query.filter(
            MainstreamDomain.domain.in_(domains),
            MainstreamDomain.is_active == True
        ).all()

        mainstream_set = {r.domain for r in results}
        return {domain: domain in mainstream_set for domain in domains}


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='检查域名是否为主流网站')
    parser.add_argument('domains', nargs='*', help='要检查的域名列表')
    parser.add_argument('--batch', action='store_true', help='批量模式（从stdin读取域名）')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')

    args = parser.parse_args()

    if args.stats:
        # 显示统计信息
        from web import app
        from jd.models.mainstream_domain import MainstreamDomain

        with app.app_context():
            total = MainstreamDomain.query.count()
            active = MainstreamDomain.query.filter_by(is_active=True).count()

            print(f"主流域名白名单统计:")
            print(f"  总数: {total:,}")
            print(f"  启用: {active:,}")
            return

    if args.batch or not args.domains:
        # 从stdin读取域名
        domains = []
        try:
            for line in sys.stdin:
                domain = line.strip()
                if domain:
                    domains.append(domain)
        except KeyboardInterrupt:
            print()
            return

        if not domains:
            print("未提供域名")
            return

        results = check_batch(domains)
        for domain, is_mainstream in results.items():
            status = "✓ 主流" if is_mainstream else "✗ 小众"
            print(f"{domain:40} {status}")

    else:
        # 检查命令行提供的域名
        for domain in args.domains:
            is_mainstream = check_domain(domain)
            status = "✓ 主流" if is_mainstream else "✗ 小众"
            print(f"{domain:40} {status}")


if __name__ == "__main__":
    main()

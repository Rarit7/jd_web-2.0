#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tranco 主流域名导入脚本

一次性从 Tranco 导入主流域名到数据库
使用方法:
    python scripts/import_tranco_mainstream.py -n 10000
    python scripts/import_tranco_mainstream.py -n 20000
    python scripts/import_tranco_mainstream.py --skip-download  # 仅验证
"""

import sys
import time
import logging
import requests
import zipfile
from io import BytesIO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, '.')


def download_tranco_list(top_n=10000):
    """
    下载 Tranco 列表

    Args:
        top_n: 取前N个域名作为主流白名单，推荐 10000-20000

    Returns:
        域名列表，每个元素为 {'rank': int, 'domain': str}
    """
    logger.info(f"正在下载 Tranco Top {top_n:,} 列表...")
    url = 'https://tranco-list.eu/top-1m.csv.zip'

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"❌ 下载失败: {e}")
        return None

    # 解压
    try:
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            csv_filename = z.namelist()[0]
            csv_content = z.read(csv_filename).decode('utf-8')
    except Exception as e:
        logger.error(f"❌ 解压失败: {e}")
        return None

    # 解析前 N 条
    domains = []
    for i, line in enumerate(csv_content.split('\n')):
        if i >= top_n:
            break
        if ',' in line:
            try:
                rank, domain = line.strip().split(',', 1)
                domain = domain.lower().strip()
                if domain:
                    domains.append({
                        'rank': int(rank),
                        'domain': domain
                    })
            except ValueError:
                logger.warning(f"解析行 {i+1} 失败: {line}")
                continue

    logger.info(f"✓ 成功解析 {len(domains):,} 个域名")
    return domains


def import_to_database(domains, batch_size=1000):
    """
    批量导入到数据库

    Args:
        domains: 域名列表
        batch_size: 批量提交大小
    """
    from web import app
    from jd.models.mainstream_domain import MainstreamDomain
    from jd import db

    with app.app_context():
        logger.info(f"开始导入到数据库...")

        # 清空现有数据（Tranco 来源）
        logger.info("清空现有 Tranco 数据...")
        try:
            deleted = MainstreamDomain.query.filter_by(source='tranco').delete()
            db.session.commit()
            logger.info(f"已清空 {deleted} 条旧数据")
        except Exception as e:
            logger.warning(f"清空数据时出错: {e}")
            db.session.rollback()

        # 批量插入
        total = len(domains)
        for i in range(0, total, batch_size):
            batch = domains[i:i+batch_size]

            try:
                for item in batch:
                    domain_obj = MainstreamDomain(
                        domain=item['domain'],
                        rank=item['rank'],
                        source='tranco',
                        is_active=True
                    )
                    db.session.add(domain_obj)

                db.session.commit()
                progress = min(i + batch_size, total)
                percent = 100 * progress / total
                logger.info(f"  已导入 {progress:,}/{total:,} ({percent:.1f}%)")

            except Exception as e:
                logger.error(f"批量导入失败 ({i}-{i+batch_size}): {e}")
                db.session.rollback()
                return False

        logger.info(f"✓ 导入完成！")
        return True


def verify_import():
    """验证导入结果"""
    from web import app
    from jd.models.mainstream_domain import MainstreamDomain

    with app.app_context():
        logger.info("\n验证导入结果...")

        try:
            total = MainstreamDomain.query.count()
            logger.info(f"  总记录数: {total:,}")

            tranco_count = MainstreamDomain.query.filter_by(source='tranco').count()
            logger.info(f"  Tranco来源: {tranco_count:,}")

            active_count = MainstreamDomain.query.filter_by(is_active=True).count()
            logger.info(f"  启用中: {active_count:,}")

            # 测试查询性能
            test_domains = ['google.com', 'facebook.com', 'unknown-domain-xyz.com']
            logger.info("\n查询性能测试:")

            for domain in test_domains:
                start = time.time()
                result = MainstreamDomain.query.filter_by(
                    domain=domain, is_active=True
                ).first()
                elapsed = (time.time() - start) * 1000

                status = "✓ 找到" if result else "✗ 未找到"
                logger.info(f"  {domain:30} {status:10} ({elapsed:.2f}ms)")

            return True

        except Exception as e:
            logger.error(f"验证失败: {e}")
            return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='导入 Tranco 主流域名列表')
    parser.add_argument('-n', '--top-n', type=int, default=10000,
                       help='导入前N个域名 (默认: 10000, 推荐: 10000-20000)')
    parser.add_argument('--skip-download', action='store_true',
                       help='跳过下载，仅验证现有数据')

    args = parser.parse_args()

    print("=" * 70)
    print("Tranco 主流域名导入工具")
    print("=" * 70)

    if not args.skip_download:
        # 下载并导入
        domains = download_tranco_list(args.top_n)
        if not domains:
            logger.error("❌ 导入失败：无法下载 Tranco 列表")
            sys.exit(1)

        if not import_to_database(domains):
            logger.error("❌ 导入失败：数据库操作出错")
            sys.exit(1)
    else:
        logger.info("跳过下载，仅执行验证...")

    # 验证
    if not verify_import():
        logger.error("❌ 验证失败")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("✓ 完成！")
    print("=" * 70)
    logger.info("Tranco 主流域名已成功导入到数据库")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速运行历史数据回填脚本
"""

import sys
from datetime import datetime, timedelta, date

# 初始化 Flask 应用
from jd import db, app
app.ready(db_switch=True, web_switch=False, worker_switch=False)

from sqlalchemy import func

# 进入应用上下文
app_context = app.app_context()
app_context.push()
from jd.models.ad_tracking_dark_keyword import AdTrackingDarkKeyword
from jd.models.ad_tracking_transaction_method import AdTrackingTransactionMethod
from jd.models.ad_tracking_price import AdTrackingPrice
from jd.models.ad_tracking_geo_location import AdTrackingGeoLocation
from jd.services.daily_stats_computation_service import DailyStatsComputationService
from jd.models.ad_tracking_daily_stats import (
    AdTrackingDarkKeywordDailyStats,
    AdTrackingTransactionMethodDailyStats,
    AdTrackingPriceDailyStats,
    AdTrackingGeoLocationDailyStats
)

print("=" * 80)
print("广告分析每日统计数据回填工具")
print("=" * 80)

# 检测数据范围
print("\n[1/5] 检测源表数据范围...")
min_dates = []
max_dates = []

result = db.session.query(
    func.min(AdTrackingDarkKeyword.msg_date),
    func.max(AdTrackingDarkKeyword.msg_date)
).first()
if result[0]:
    min_dates.append(result[0])
    max_dates.append(result[1])
    print(f"  ✓ 黑词表: {result[0]} ~ {result[1]}")

result = db.session.query(
    func.min(AdTrackingTransactionMethod.msg_date),
    func.max(AdTrackingTransactionMethod.msg_date)
).first()
if result[0]:
    min_dates.append(result[0])
    max_dates.append(result[1])
    print(f"  ✓ 交易方式表: {result[0]} ~ {result[1]}")

result = db.session.query(
    func.min(AdTrackingPrice.msg_date),
    func.max(AdTrackingPrice.msg_date)
).first()
if result[0]:
    min_dates.append(result[0])
    max_dates.append(result[1])
    print(f"  ✓ 价格表: {result[0]} ~ {result[1]}")

result = db.session.query(
    func.min(AdTrackingGeoLocation.msg_date),
    func.max(AdTrackingGeoLocation.msg_date)
).first()
if result[0]:
    min_dates.append(result[0])
    max_dates.append(result[1])
    print(f"  ✓ 地理位置表: {result[0]} ~ {result[1]}")

if not min_dates:
    print("  ✗ 源表中没有数据！")
    sys.exit(1)

start_date = min(min_dates)
end_date = max(max_dates)

print(f"\n📊 总体数据范围: {start_date} ~ {end_date}")
total_days = (end_date - start_date).days + 1
print(f"📅 总计 {total_days} 天的数据需要回填\n")

# 开始回填
print("[2/5] 开始回填黑词统计...")
current_date = start_date
dark_count = 0
while current_date <= end_date:
    dark_stats = DailyStatsComputationService.compute_dark_keyword_stats(current_date)
    inserted, updated = DailyStatsComputationService.upsert_stats(
        dark_stats, AdTrackingDarkKeywordDailyStats
    )
    dark_count += len(dark_stats)
    current_date += timedelta(days=1)
    if (current_date - start_date).days % 10 == 0:
        print(f"  进度: {(current_date - start_date).days}/{total_days} 天")

db.session.commit()
print(f"  ✓ 黑词统计完成: 共 {dark_count} 条记录\n")

# 交易方式统计
print("[3/5] 开始回填交易方式统计...")
current_date = start_date
trans_count = 0
while current_date <= end_date:
    trans_stats = DailyStatsComputationService.compute_transaction_method_stats(current_date)
    inserted, updated = DailyStatsComputationService.upsert_stats(
        trans_stats, AdTrackingTransactionMethodDailyStats
    )
    trans_count += len(trans_stats)
    current_date += timedelta(days=1)
    if (current_date - start_date).days % 10 == 0:
        print(f"  进度: {(current_date - start_date).days}/{total_days} 天")

db.session.commit()
print(f"  ✓ 交易方式统计完成: 共 {trans_count} 条记录\n")

# 价格统计
print("[4/5] 开始回填价格统计...")
current_date = start_date
price_count = 0
while current_date <= end_date:
    price_stats = DailyStatsComputationService.compute_price_stats(current_date)
    inserted, updated = DailyStatsComputationService.upsert_stats(
        price_stats, AdTrackingPriceDailyStats
    )
    price_count += len(price_stats)
    current_date += timedelta(days=1)
    if (current_date - start_date).days % 10 == 0:
        print(f"  进度: {(current_date - start_date).days}/{total_days} 天")

db.session.commit()
print(f"  ✓ 价格统计完成: 共 {price_count} 条记录\n")

# 地理位置统计
print("[5/5] 开始回填地理位置统计...")
current_date = start_date
geo_count = 0
while current_date <= end_date:
    geo_stats = DailyStatsComputationService.compute_geo_location_stats(current_date)
    inserted, updated = DailyStatsComputationService.upsert_stats(
        geo_stats, AdTrackingGeoLocationDailyStats
    )
    geo_count += len(geo_stats)
    current_date += timedelta(days=1)
    if (current_date - start_date).days % 10 == 0:
        print(f"  进度: {(current_date - start_date).days}/{total_days} 天")

db.session.commit()
print(f"  ✓ 地理位置统计完成: 共 {geo_count} 条记录\n")

# 验证
print("=" * 80)
print("📊 回填完成！统计结果：")
print("=" * 80)

dark_verify = db.session.query(func.count()).select_from(AdTrackingDarkKeywordDailyStats).scalar()
trans_verify = db.session.query(func.count()).select_from(AdTrackingTransactionMethodDailyStats).scalar()
price_verify = db.session.query(func.count()).select_from(AdTrackingPriceDailyStats).scalar()
geo_verify = db.session.query(func.count()).select_from(AdTrackingGeoLocationDailyStats).scalar()

print(f"✓ 黑词统计表: {dark_verify} 条记录")
print(f"✓ 交易方式统计表: {trans_verify} 条记录")
print(f"✓ 价格统计表: {price_verify} 条记录")
print(f"✓ 地理位置统计表: {geo_verify} 条记录")
print(f"\n总计: {dark_verify + trans_verify + price_verify + geo_verify} 条记录")
print("\n✅ 回填脚本执行完成！")

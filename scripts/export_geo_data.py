#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导出地理位置主数据到 SQL 文件
"""
import sys
sys.path.insert(0, '/home/ls/workspace/sdjd/jd_web-2.0')

from jd import app
from jd.models.ad_tracking_geo_location_master import AdTrackingGeoLocationMaster

app.ready(db_switch=True, web_switch=False, worker_switch=False)

with app.app_context():
    # 获取所有地理位置数据
    locations = AdTrackingGeoLocationMaster.query.order_by(AdTrackingGeoLocationMaster.id).all()

    # 打开SQL文件追加数据
    with open('/home/ls/workspace/sdjd/jd_web-2.0/dbrt/ad_tracking_config_data_export_20260107.sql', 'a', encoding='utf-8') as f:
        f.write('-- 地理位置数据 (共 {} 条记录)\n'.format(len(locations)))
        f.write('-- 省份(level=1): 34条, 城市(level=2): 2355条, 区县(level=3): 0条\n\n')

        # 写入INSERT语句
        f.write('INSERT INTO ad_tracking_geo_location_master (id, level, name, parent_id, code, latitude, longitude, aliases, short_name, description, is_active, created_at, updated_at) VALUES\n')

        values = []
        for loc in locations:
            # 处理每个字段
            code_val = "'{}'".format(loc.code) if loc.code else 'NULL'
            lat_val = str(float(loc.latitude)) if loc.latitude else 'NULL'
            lon_val = str(float(loc.longitude)) if loc.longitude else 'NULL'
            aliases_val = "'{}'".format(loc.aliases.replace("'", "''") if "'" in loc.aliases else loc.aliases) if loc.aliases else 'NULL'
            short_name_val = "'{}'".format(loc.short_name) if loc.short_name else 'NULL'
            desc_val = "'{}'".format(loc.description.replace("'", "''") if "'" in (loc.description or '') else (loc.description or '')) if loc.description else 'NULL'

            values.append("({}, {}, '{}', {}, {}, {}, {}, {}, {}, {}, {}, NOW(), NOW())".format(
                loc.id,
                loc.level,
                loc.name,
                loc.parent_id if loc.parent_id else 'NULL',
                code_val,
                lat_val,
                lon_val,
                aliases_val,
                short_name_val,
                desc_val,
                1 if loc.is_active else 0
            ))

        # 每200条记录分一组
        chunk_size = 200
        for i in range(0, len(values), chunk_size):
            chunk = values[i:i+chunk_size]
            f.write(',\n'.join(chunk))
            if i + chunk_size < len(values):
                f.write(',\n')
            else:
                f.write(';\n')

    print('已导出 {} 条地理位置记录'.format(len(locations)))
    print('文件: /home/ls/workspace/sdjd/jd_web-2.0/dbrt/ad_tracking_config_data_export_20260107.sql')

print('\n地理位置数据导出完成！')

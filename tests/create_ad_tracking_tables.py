#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建广告追踪相关数据表
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jd import Application, db

# 创建并初始化应用
app = Application()
app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)

with app.app_context():
    # 读取DDL文件
    ddl_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dbrt', 'ad_tracking_ddl.sql')

    with open(ddl_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 分割SQL语句（按分号）
    statements = []
    current_statement = []

    for line in sql_content.split('\n'):
        # 跳过注释和空行
        line = line.strip()
        if not line or line.startswith('--'):
            continue

        current_statement.append(line)

        # 如果行以分号结尾，这是一个完整的语句
        if line.endswith(';'):
            statements.append(' '.join(current_statement))
            current_statement = []

    # 执行每个语句
    print(f"开始创建广告追踪相关表...")

    for i, statement in enumerate(statements, 1):
        if not statement.strip():
            continue

        try:
            # 提取表名（如果是CREATE TABLE语句）
            if 'CREATE TABLE' in statement.upper():
                table_name = statement.split('`')[1]
                print(f"{i}. 创建表: {table_name} ...", end=' ')
            else:
                print(f"{i}. 执行语句 ...", end=' ')

            db.session.execute(db.text(statement))
            db.session.commit()
            print("✓")

        except Exception as e:
            error_msg = str(e)
            if 'already exists' in error_msg or '1050' in error_msg:
                print("(已存在，跳过)")
            else:
                print(f"✗ 错误: {e}")
                db.session.rollback()

    print("\n✓ 表创建完成！")

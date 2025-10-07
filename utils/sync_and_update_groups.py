#!/usr/bin/env python3
"""
同步session中的群组信息并更新已加入状态

使用方式：
    python utils/sync_and_update_groups.py
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jd import app, db
from jd.models.tg_group import TgGroup
from jd.jobs.tg_group_info import TgGroupInfoManager

print("="*60)
print("开始同步群组信息并更新状态")
print("="*60)

async def main():
    # 初始化应用
    app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)

    with app.app_context():
        try:
            print("\n正在通过session 'default2' 同步群组信息...")

            # 调用已有的同步功能
            result = await TgGroupInfoManager.sync_group_info_by_account('default2')

            print(f"\n同步结果:")
            print(f"  成功: {result.get('success')}")
            print(f"  消息: {result.get('message')}")
            print(f"  统计信息: {result.get('stats')}")

            # 获取同步到的群组ID列表
            processed_groups = result.get('processed_groups', [])
            if processed_groups:
                print(f"\n已处理 {len(processed_groups)} 个群组")

                # 查询这些群组的状态
                groups = TgGroup.query.filter(
                    TgGroup.chat_id.in_(processed_groups)
                ).all()

                print(f"\n状态统计:")
                status_counts = {}
                for group in groups:
                    status_counts[group.status] = status_counts.get(group.status, 0) + 1

                for status, count in status_counts.items():
                    print(f"  {status}: {count}")

            print("\n" + "="*60)
            print("同步完成")
            print("="*60)

        except Exception as e:
            print(f"执行失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
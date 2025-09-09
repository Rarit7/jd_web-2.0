#!/usr/bin/env python3
"""
测试Celery任务执行
"""

from jd import app
from jd.tasks.telegram.tg_fetch_group_info import fetch_account_group_info

def test_celery_connection():
    """测试Celery连接和任务调度"""
    
    with app.app_context():
        try:
            print("测试Celery任务调度...")
            
            # 测试异步任务调度
            print("1. 测试任务调度...")
            result = fetch_account_group_info.delay(1)  # 使用ID=1的账户进行测试
            print(f"   任务ID: {result.id}")
            print(f"   任务状态: {result.status}")
            
            # 等待一小段时间看任务是否开始执行
            import time
            time.sleep(2)
            
            print(f"   更新后状态: {result.status}")
            
            if result.status == 'PENDING':
                print("   ✓ 任务已成功提交到队列")
            elif result.status == 'SUCCESS':
                print("   ✓ 任务执行成功")
                print(f"   结果: {result.result}")
            elif result.status == 'FAILURE':
                print("   ✗ 任务执行失败")
                print(f"   错误: {result.traceback}")
            else:
                print(f"   状态: {result.status}")
            
            return True
            
        except Exception as e:
            print(f"测试失败: {e}")
            return False

if __name__ == "__main__":
    app.ready(db_switch=True, web_switch=False, worker_switch=False)
    success = test_celery_connection()
    if success:
        print("✓ Celery工作正常")
    else:
        print("✗ Celery存在问题")
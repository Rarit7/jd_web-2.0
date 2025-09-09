#!/usr/bin/env python3
"""
测试修复后的群组信息获取功能
"""

from jd import app
from jd.tasks.telegram.tg_fetch_group_info import fetch_account_group_info

def test_group_info_fetch():
    """测试群组信息获取任务"""
    
    with app.app_context():
        try:
            print("测试群组信息获取任务...")
            
            # 使用存在的账户ID=11进行测试
            account_id = 11
            print(f"测试账户ID: {account_id}")
            
            # 提交任务
            result = fetch_account_group_info.delay(account_id)
            print(f"任务ID: {result.id}")
            print(f"任务状态: {result.status}")
            
            # 等待任务执行
            import time
            print("等待任务执行...")
            
            for i in range(30):  # 等待最多30秒
                time.sleep(1)
                status = result.status
                print(f"第{i+1}秒 - 状态: {status}")
                
                if status == 'SUCCESS':
                    print("✓ 任务执行成功!")
                    print(f"结果: {result.result}")
                    break
                elif status == 'FAILURE':
                    print("✗ 任务执行失败!")
                    print(f"错误: {result.traceback}")
                    break
                elif status != 'PENDING':
                    print(f"任务状态: {status}")
            
            return True
            
        except Exception as e:
            print(f"测试失败: {e}")
            return False

if __name__ == "__main__":
    app.ready(db_switch=True, web_switch=False, worker_switch=False)
    test_group_info_fetch()
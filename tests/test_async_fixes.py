#!/usr/bin/env python3
"""
测试异步修复是否有效
"""

from jd import app
from jd.tasks.first.tg_new_joined_history import run_new_group_history_fetch

def test_async_fixes():
    """测试异步修复"""
    
    with app.app_context():
        try:
            print("测试 fetch_new_group_history 异步修复...")
            
            # 使用一个真实的chat_id进行测试
            chat_id = 1967795413  # 从错误日志中看到的chat_id
            group_name = "测试群组"
            session_name = "111"  # 使用已知的session
            
            # 提交任务
            result = run_new_group_history_fetch.delay(group_name, chat_id, session_name)
            print(f"任务ID: {result.id}")
            print(f"任务状态: {result.status}")
            
            # 等待一小段时间
            import time
            for i in range(10):
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
            
            return True
            
        except Exception as e:
            print(f"测试失败: {e}")
            return False

if __name__ == "__main__":
    app.ready(db_switch=True, web_switch=False, worker_switch=False)
    test_async_fixes()
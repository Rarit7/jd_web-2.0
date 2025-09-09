#!/usr/bin/env python3
"""
测试session排队功能
"""

from jd.jobs.job_queue_manager import EnhancedJobQueueLogService, JobQueueLogService
from jd import app, db

def test_session_queue_new_api():
    """测试新API的session排队功能"""
    
    with app.app_context():
        print("=== 测试增强API的session排队功能 ===")
        
        # 清理可能存在的测试任务
        cleanup_test_tasks()
        
        # 测试1: 第一个任务正常运行
        print("\n1. 创建第一个session任务（应该正常运行）")
        success1, queue1, info1 = EnhancedJobQueueLogService.add(
            'fetch_account_group_info',
            resource_id='account_001',
            session_name='tg_session_alpha',
            sync_groups=True
        )
        db.session.commit()
        
        if success1:
            print(f"  ✓ 任务创建成功: ID={queue1.id}, 状态={queue1.status}")
            print(f"  ✓ session_name: {queue1.session_name}")
        
        # 测试2: 相同session的第二个任务应该排队
        print("\n2. 创建相同session的第二个任务（应该自动排队）")
        success2, queue2, info2 = EnhancedJobQueueLogService.add(
            'sync_user_contacts',
            resource_id='account_002',
            session_name='tg_session_alpha',  # 相同session
            sync_contacts=True
        )
        db.session.commit()
        
        if success2:
            print(f"  ✓ 任务自动排队: ID={queue2.id}, 状态={queue2.status}")
            print(f"  ✓ 队列位置: {info2.get('queue_position')}")
            print(f"  ✓ 预估等待时间: {info2.get('estimated_wait_time')}秒")
        else:
            print(f"  ✗ 任务创建失败: {info2}")
        
        # 测试3: 不同session的任务可以并行运行
        print("\n3. 创建不同session的任务（应该并行运行）")
        success3, queue3, info3 = EnhancedJobQueueLogService.add(
            'fetch_account_group_info',
            resource_id='account_003', 
            session_name='tg_session_beta',  # 不同session
            sync_groups=True
        )
        db.session.commit()
        
        if success3:
            print(f"  ✓ 任务正常运行: ID={queue3.id}, 状态={queue3.status}")
            print(f"  ✓ session_name: {queue3.session_name}")
        
        # 测试4: 完成第一个任务，观察等待队列的自动启动
        print("\n4. 完成第一个任务，观察等待队列自动启动")
        if queue1:
            EnhancedJobQueueLogService.finished(queue1.id, "账户信息同步完成")
            print(f"  ✓ 任务 {queue1.id} 已完成")
            
            # 检查等待任务是否自动启动
            if queue2:
                fresh_queue2 = db.session.get(type(queue2), queue2.id)
                print(f"  ✓ 等待任务 {queue2.id} 当前状态: {fresh_queue2.status}")
        
        return [queue1, queue2, queue3]

def test_session_queue_legacy_api():
    """测试原有API的session排队功能"""
    
    with app.app_context():
        print("\n=== 测试原有API的session排队功能 ===")
        
        # 测试1: 原有API创建session任务
        print("\n1. 使用原有API创建session任务")
        success1, queue1 = JobQueueLogService.add(
            'fetch_account_group_info',
            resource_id='legacy_account_001',
            session_name='legacy_session_alpha'
        )
        db.session.commit()
        
        if success1:
            print(f"  ✓ 原有API任务创建成功: ID={queue1.id}")
            print(f"  ✓ 状态: {queue1.status} (1=RUNNING)")
        
        # 测试2: 相同session的第二个任务应该自动排队
        print("\n2. 相同session的第二个任务（应该自动排队）")
        success2, queue2 = JobQueueLogService.add(
            'sync_user_contacts',
            resource_id='legacy_account_002',
            session_name='legacy_session_alpha'  # 相同session
        )
        db.session.commit()
        
        if success2:
            print(f"  ✓ 任务自动排队: ID={queue2.id}")
            print(f"  ✓ 状态: {queue2.status} (3=WAITING)")
        else:
            print(f"  ✗ 任务未能创建: {success2}")
        
        return [queue1, queue2]

def test_mixed_conflicts():
    """测试混合冲突场景"""
    
    with app.app_context():
        print("\n=== 测试混合冲突场景 ===")
        
        # 测试1: resource_id冲突仍然立即返回
        print("\n1. 测试resource_id冲突（应该立即返回失败）")
        success1, queue1, info1 = EnhancedJobQueueLogService.add(
            'process_account_data',
            resource_id='account_001',  # 与前面的任务冲突
            session_name='different_session',
            wait_if_conflict=False
        )
        db.session.commit()
        
        print(f"  resource_id冲突结果: success={success1}")
        if not success1:
            print(f"  冲突类型: {info1.get('conflict_type')}")
        
        # 测试2: session冲突会自动排队
        print("\n2. 测试session冲突（应该自动排队）")
        success2, queue2, info2 = EnhancedJobQueueLogService.add(
            'another_task',
            resource_id='different_account',
            session_name='tg_session_beta',  # 与前面的任务session冲突
            wait_if_conflict=False  # 即使设置为False，session冲突也会排队
        )
        db.session.commit()
        
        print(f"  session冲突结果: success={success2}")
        if success2 and queue2:
            print(f"  任务状态: {queue2.status} (应该是3=WAITING)")
            print(f"  队列位置: {info2.get('queue_position')}")

def cleanup_test_tasks():
    """清理测试任务"""
    
    from jd.jobs.job_queue_manager import QueueStatus
    
    test_job_names = ['fetch_account_group_info', 'sync_user_contacts', 'process_account_data', 'another_task']
    
    for job_name in test_job_names:
        tasks = EnhancedJobQueueLogService.find_tasks_with_params(
            job_name=job_name,
            status=QueueStatus.RUNNING.value
        )
        for task in tasks:
            EnhancedJobQueueLogService.finished(task.id, "清理测试")
    
    db.session.commit()

def show_queue_status():
    """显示队列状态"""
    
    with app.app_context():
        print("\n=== 当前队列状态 ===")
        
        status = EnhancedJobQueueLogService.get_queue_status()
        print(f"队列统计: {status['status_counts']}")
        
        if status['tasks']:
            print("\n最近任务:")
            for task in status['tasks'][:5]:
                print(f"  任务 {task['id']}: {task['name']}")
                print(f"    资源: {task['resource_display']}")
                print(f"    Session: {task['session_name']}")
                print(f"    状态: {task['status_name']}")
                print()

if __name__ == "__main__":
    app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)
    
    # 运行测试
    new_api_tasks = test_session_queue_new_api()
    legacy_api_tasks = test_session_queue_legacy_api() 
    test_mixed_conflicts()
    
    show_queue_status()
    
    # 清理所有测试任务
    print("\n=== 清理测试任务 ===")
    all_tasks = new_api_tasks + legacy_api_tasks
    for task in all_tasks:
        if task:
            try:
                fresh_task = db.session.get(type(task), task.id)
                if fresh_task and fresh_task.status in [1, 3]:  # RUNNING or WAITING
                    EnhancedJobQueueLogService.finished(fresh_task.id, "测试完成")
                    print(f"任务 {fresh_task.id} 已标记完成")
            except:
                pass
    
    print("\n=== Session排队测试完成 ===")
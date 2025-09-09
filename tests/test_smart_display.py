#!/usr/bin/env python3
"""
测试智能显示功能
"""

from jd.jobs.job_queue_manager import EnhancedJobQueueLogService
from jd import app, db

def test_smart_resource_display():
    """测试智能资源显示"""
    
    with app.app_context():
        print("=== 测试智能资源显示 ===")
        
        # 清理可能存在的测试任务
        cleanup_existing_tasks()
        
        # 测试1: TG任务 - 应显示为chat_id
        print("\n1. 创建TG任务")
        success1, queue1, _ = EnhancedJobQueueLogService.add(
            'fetch_tg_group_history',
            chat_id='-1001234567890',  # 会自动映射到resource_id
            session_name='tg_session',
            history_days=30
        )
        db.session.commit()
        
        if success1:
            print(f"  ✓ 任务创建: {queue1.name}")
            print(f"  ✓ resource_id: {queue1.resource_id}")
        
        # 测试2: 账户任务 - 应显示为account_id
        print("\n2. 创建账户任务")  
        success2, queue2, _ = EnhancedJobQueueLogService.add(
            'sync_account_info',
            account_id='acc_12345',
            session_name='account_session',
            sync_groups=True
        )
        db.session.commit()
        
        if success2:
            print(f"  ✓ 任务创建: {queue2.name}")
            print(f"  ✓ resource_id: {queue2.resource_id}")
        
        # 测试3: 文件任务 - 应显示为file_id
        print("\n3. 创建文件任务")
        success3, queue3, _ = EnhancedJobQueueLogService.add(
            'download_file',
            file_id='file_67890',
            session_name='download_session',
            file_type='pdf'
        )
        db.session.commit()
        
        if success3:
            print(f"  ✓ 任务创建: {queue3.name}")
            print(f"  ✓ resource_id: {queue3.resource_id}")
        
        # 测试4: 批次任务 - 应显示为batch_id
        print("\n4. 创建批次任务")
        success4, queue4, _ = EnhancedJobQueueLogService.add(
            'batch_import_task',
            batch_id='batch_2024_001',
            records_count=1000
        )
        db.session.commit()
        
        if success4:
            print(f"  ✓ 任务创建: {queue4.name}")
            print(f"  ✓ resource_id: {queue4.resource_id}")
        
        return [queue1, queue2, queue3, queue4]

def test_intelligent_conflict_messages():
    """测试智能冲突消息"""
    
    with app.app_context():
        print("\n=== 测试智能冲突消息 ===")
        
        # 测试1: TG任务冲突
        print("\n1. 测试TG任务冲突")
        success1, _, info1 = EnhancedJobQueueLogService.add(
            'fetch_tg_group_history',
            chat_id='-1001234567890',  # 相同chat_id 
            wait_if_conflict=False
        )
        print(f"  冲突检测: success={success1}")
        print(f"  冲突类型: {info1.get('conflict_type')}")
        
        # 测试2: 账户任务冲突
        print("\n2. 测试账户任务冲突")
        success2, _, info2 = EnhancedJobQueueLogService.add(
            'sync_account_info',
            account_id='acc_12345',
            wait_if_conflict=False
        )
        print(f"  冲突检测: success={success2}")
        print(f"  冲突类型: {info2.get('conflict_type')}")

def test_queue_status_smart_display():
    """测试队列状态智能显示"""
    
    with app.app_context():
        print("\n=== 测试队列状态智能显示 ===")
        
        status = EnhancedJobQueueLogService.get_queue_status()
        
        print(f"任务统计: {status['status_counts']}")
        print(f"任务总数: {status['total']}")
        
        if status['tasks']:
            print("\n最新任务显示:")
            for task in status['tasks'][:4]:  # 显示前4个任务
                print(f"  任务 {task['id']}: {task['name']}")
                print(f"    资源显示: {task['resource_display']}")
                print(f"    状态: {task['status_name']}")
                if task['extra_params']:
                    print(f"    扩展参数: {task['extra_params']}")
                print()

def cleanup_existing_tasks():
    """清理已存在的测试任务"""
    
    from jd.jobs.job_queue_manager import QueueStatus
    
    test_job_names = ['fetch_tg_group_history', 'sync_account_info', 'download_file', 'batch_import_task']
    
    for job_name in test_job_names:
        tasks = EnhancedJobQueueLogService.find_tasks_with_params(
            job_name=job_name,
            status=QueueStatus.RUNNING.value
        )
        for task in tasks:
            EnhancedJobQueueLogService.finished(task.id, "清理测试")
    
    db.session.commit()

if __name__ == "__main__":
    app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)
    
    # 运行测试
    created_tasks = test_smart_resource_display()
    test_intelligent_conflict_messages()
    test_queue_status_smart_display()
    
    # 清理测试任务
    print("\n=== 清理测试任务 ===")
    for task in created_tasks:
        if task:
            fresh_task = db.session.get(type(task), task.id)
            if fresh_task and fresh_task.status == 1:  # RUNNING状态
                EnhancedJobQueueLogService.finished(fresh_task.id, "测试完成")
                print(f"任务 {fresh_task.id} 已标记完成")
    
    print("\n=== 智能显示测试完成 ===")
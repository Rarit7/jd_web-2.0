#!/usr/bin/env python3
"""
测试真实的TG任务session排队
"""

from jd import app, db
from jd.jobs.job_queue_manager import EnhancedJobQueueLogService

def test_real_tg_scenario():
    """测试真实的TG任务场景"""
    
    print("=== 测试真实TG任务session排队场景 ===")
    
    # 场景：同一个TG账户session需要执行多个任务
    session_name = 'tg_account_session_001'
    
    # 任务1: 获取账户群组信息
    print("\n1. 创建TG账户群组信息获取任务")
    success1, queue1, info1 = EnhancedJobQueueLogService.add(
        'fetch_account_group_info',
        account_id='tg_acc_12345',
        session_name=session_name,
        sync_groups=True
    )
    db.session.commit()
    
    print(f"  账户群组任务: success={success1}")
    if success1:
        print(f"    ID={queue1.id}, 状态={queue1.status}")
        resource_type = EnhancedJobQueueLogService._get_resource_type_display(queue1.name, queue1.resource_id)
        print(f"    资源显示: {resource_type}:{queue1.resource_id}")
    
    # 任务2: 获取群组历史（相同session，应该排队）
    print("\n2. 创建TG群组历史获取任务（相同session）")
    success2, queue2, info2 = EnhancedJobQueueLogService.add(
        'fetch_tg_group_history',
        chat_id='-1001234567890',
        session_name=session_name,  # 相同session
        history_days=30
    )
    db.session.commit()
    
    print(f"  群组历史任务: success={success2}")
    if success2:
        print(f"    ID={queue2.id}, 状态={queue2.status}")
        resource_type = EnhancedJobQueueLogService._get_resource_type_display(queue2.name, queue2.resource_id)
        print(f"    资源显示: {resource_type}:{queue2.resource_id}")
        print(f"    队列位置: {info2.get('queue_position')}")
        print(f"    冲突类型: {info2.get('conflict_type')}")
    
    # 任务3: 同步用户联系人（相同session，应该继续排队）
    print("\n3. 创建用户联系人同步任务（相同session）")
    success3, queue3, info3 = EnhancedJobQueueLogService.add(
        'sync_user_contacts',
        user_id='user_67890',
        session_name=session_name,  # 相同session
        sync_contacts=True
    )
    db.session.commit()
    
    print(f"  联系人同步任务: success={success3}")
    if success3:
        print(f"    ID={queue3.id}, 状态={queue3.status}")
        resource_type = EnhancedJobQueueLogService._get_resource_type_display(queue3.name, queue3.resource_id)
        print(f"    资源显示: {resource_type}:{queue3.resource_id}")
        print(f"    队列位置: {info3.get('queue_position')}")
    
    # 任务4: 不同session的并行任务
    print("\n4. 创建不同session的并行任务")
    success4, queue4, info4 = EnhancedJobQueueLogService.add(
        'fetch_account_group_info',
        account_id='tg_acc_54321',
        session_name='tg_account_session_002',  # 不同session
        sync_groups=True
    )
    db.session.commit()
    
    print(f"  并行账户任务: success={success4}")
    if success4:
        print(f"    ID={queue4.id}, 状态={queue4.status}")
        resource_type = EnhancedJobQueueLogService._get_resource_type_display(queue4.name, queue4.resource_id)
        print(f"    资源显示: {resource_type}:{queue4.resource_id}")
    
    # 查看队列状态
    print("\n=== 当前队列状态 ===")
    status = EnhancedJobQueueLogService.get_queue_status()
    print(f"运行中任务数: {status['status_counts'].get('running', 0)}")
    print(f"等待中任务数: {status['status_counts'].get('waiting', 0)}")
    
    # 显示相关任务
    print("\n相关任务:")
    for task in status['tasks'][:6]:
        if task['session_name'] in [session_name, 'tg_account_session_002']:
            print(f"  任务 {task['id']}: {task['name']}")
            print(f"    资源: {task['resource_display']}")
            print(f"    Session: {task['session_name']}")
            print(f"    状态: {task['status_name']}")
            print()
    
    return [queue1, queue2, queue3, queue4]

if __name__ == "__main__":
    app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)
    
    with app.app_context():
        tasks = test_real_tg_scenario()
        
        # 清理测试任务
        print("=== 清理测试任务 ===")
        for task in tasks:
            if task:
                try:
                    EnhancedJobQueueLogService.finished(task.id, "测试完成")
                    print(f"完成任务: {task.id}")
                except:
                    pass
        
        db.session.commit()
        print("\n真实TG场景测试完成")
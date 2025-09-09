#!/usr/bin/env python3
"""
测试具体业务ID字段功能
"""

from jd.jobs.job_queue_manager import EnhancedJobQueueLogService
from jd import app, db

def test_specific_id_fields():
    """测试具体业务ID字段"""
    
    with app.app_context():
        print("=== 测试具体业务ID字段 ===")
        
        # 清理可能存在的测试任务
        cleanup_test_tasks()
        
        # 测试1: TG群组历史获取任务 (使用chat_id)
        print("\n1. 测试TG群组历史获取任务 (chat_id)")
        success1, queue1, info1 = EnhancedJobQueueLogService.add(
            'fetch_tg_group_history',
            chat_id='-1001234567890',
            session_name='tg_session_001',
            history_days=30,
            include_media=True
        )
        db.session.commit()
        
        if success1:
            print(f"  ✓ 任务创建成功: ID={queue1.id}")
            print(f"  ✓ chat_id: {queue1.chat_id}")
            print(f"  ✓ 扩展参数: {queue1.extra_params}")
        
        # 测试2: 账户同步任务 (使用account_id)
        print("\n2. 测试账户同步任务 (account_id)")
        success2, queue2, info2 = EnhancedJobQueueLogService.add(
            'sync_account_info',
            account_id='acc_12345',
            session_name='account_session',
            sync_groups=True,
            sync_contacts=False
        )
        db.session.commit()
        
        if success2:
            print(f"  ✓ 任务创建成功: ID={queue2.id}")
            print(f"  ✓ account_id: {queue2.account_id}")
            print(f"  ✓ 扩展参数: {queue2.extra_params}")
        
        # 测试3: 文件下载任务 (使用file_id)
        print("\n3. 测试文件下载任务 (file_id)")
        success3, queue3, info3 = EnhancedJobQueueLogService.add(
            'download_file',
            file_id='file_67890',
            session_name='download_session',
            file_size='10MB',
            file_type='document'
        )
        db.session.commit()
        
        if success3:
            print(f"  ✓ 任务创建成功: ID={queue3.id}")
            print(f"  ✓ file_id: {queue3.file_id}")
            print(f"  ✓ 扩展参数: {queue3.extra_params}")
        
        # 测试4: 批次处理任务 (使用batch_id + user_id)
        print("\n4. 测试批次处理任务 (batch_id + user_id)")
        success4, queue4, info4 = EnhancedJobQueueLogService.add(
            'batch_import_task',
            batch_id='batch_2024_001',
            user_id='user_999',
            records_count=1000,
            source='csv_upload'
        )
        db.session.commit()
        
        if success4:
            print(f"  ✓ 任务创建成功: ID={queue4.id}")
            print(f"  ✓ batch_id: {queue4.batch_id}")
            print(f"  ✓ user_id: {queue4.user_id}")
            print(f"  ✓ 扩展参数: {queue4.extra_params}")
        
        return [queue1, queue2, queue3, queue4]

def test_conflict_detection():
    """测试基于具体字段的冲突检测"""
    
    with app.app_context():
        print("\n=== 测试冲突检测 ===")
        
        # 测试1: chat_id冲突
        print("\n1. 测试chat_id冲突")
        success1, queue1, info1 = EnhancedJobQueueLogService.add(
            'fetch_tg_group_history',
            chat_id='-1001234567890',  # 相同chat_id
            session_name='different_session',
            wait_if_conflict=False
        )
        db.session.commit()
        
        print(f"  相同chat_id任务: success={success1}")
        if not success1:
            print(f"  冲突类型: {info1.get('conflict_type')}")
        
        # 测试2: account_id冲突 
        print("\n2. 测试account_id冲突")
        success2, queue2, info2 = EnhancedJobQueueLogService.add(
            'sync_account_info',
            account_id='acc_12345',  # 相同account_id
            session_name='different_session',
            wait_if_conflict=False
        )
        db.session.commit()
        
        print(f"  相同account_id任务: success={success2}")
        if not success2:
            print(f"  冲突类型: {info2.get('conflict_type')}")
        
        # 测试3: file_id冲突
        print("\n3. 测试file_id冲突")
        success3, queue3, info3 = EnhancedJobQueueLogService.add(
            'download_file',
            file_id='file_67890',  # 相同file_id
            session_name='different_session',
            wait_if_conflict=False
        )
        db.session.commit()
        
        print(f"  相同file_id任务: success={success3}")
        if not success3:
            print(f"  冲突类型: {info3.get('conflict_type')}")

def test_search_by_business_ids():
    """测试基于业务ID的搜索"""
    
    with app.app_context():
        print("\n=== 测试基于业务ID的搜索 ===")
        
        # 搜索1: 按chat_id查找
        print("\n1. 按chat_id查找任务")
        chat_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            chat_id='-1001234567890'
        )
        print(f"  找到 {len(chat_tasks)} 个chat_id=-1001234567890的任务")
        for task in chat_tasks:
            print(f"    - 任务: {task.name}, ID: {task.id}")
        
        # 搜索2: 按account_id查找
        print("\n2. 按account_id查找任务")
        account_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            account_id='acc_12345'
        )
        print(f"  找到 {len(account_tasks)} 个account_id=acc_12345的任务")
        
        # 搜索3: 按file_id查找
        print("\n3. 按file_id查找任务")
        file_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            file_id='file_67890'
        )
        print(f"  找到 {len(file_tasks)} 个file_id=file_67890的任务")
        
        # 搜索4: 按batch_id和user_id组合查找
        print("\n4. 按batch_id和user_id组合查找任务")
        batch_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            batch_id='batch_2024_001',
            user_id='user_999'
        )
        print(f"  找到 {len(batch_tasks)} 个匹配的批次任务")
        
        # 搜索5: 混合业务ID和扩展参数搜索
        print("\n5. 混合搜索: file_id + file_type")
        mixed_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            file_id='file_67890',
            file_type='document'
        )
        print(f"  找到 {len(mixed_tasks)} 个匹配的文件任务")

def test_queue_status_display():
    """测试队列状态显示"""
    
    with app.app_context():
        print("\n=== 测试队列状态显示 ===")
        
        # 获取队列状态
        status = EnhancedJobQueueLogService.get_queue_status()
        
        print(f"队列统计: {status['status_counts']}")
        print(f"任务总数: {status['total']}")
        
        if status['tasks']:
            print("\n最近任务列表:")
            for task in status['tasks'][:5]:  # 显示前5个任务
                print(f"  任务 {task['id']}: {task['name']}")
                print(f"    业务ID: {task['business_ids']}")
                print(f"    状态: {task['status_name']}")
                if task['extra_params']:
                    print(f"    扩展参数: {task['extra_params']}")
                print()

def cleanup_test_tasks():
    """清理测试任务"""
    
    test_job_names = ['fetch_tg_group_history', 'sync_account_info', 'download_file', 'batch_import_task']
    
    from jd.jobs.job_queue_manager import QueueStatus
    
    for job_name in test_job_names:
        tasks = EnhancedJobQueueLogService.find_tasks_with_params(
            job_name=job_name,
            status=QueueStatus.RUNNING.value
        )
        for task in tasks:
            EnhancedJobQueueLogService.finished(task.id, "清理测试任务")
    
    db.session.commit()

if __name__ == "__main__":
    app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)
    
    # 运行测试
    created_tasks = test_specific_id_fields()
    test_conflict_detection()
    test_search_by_business_ids()
    test_queue_status_display()
    
    # 清理测试任务
    print("\n=== 清理测试任务 ===")
    for task in created_tasks:
        if task:
            # 重新查询任务状态，避免会话分离问题
            fresh_task = db.session.get(type(task), task.id)
            if fresh_task and fresh_task.status == 1:  # RUNNING状态
                EnhancedJobQueueLogService.finished(fresh_task.id, "测试完成")
                print(f"任务 {fresh_task.id} 已标记完成")
    
    print("\n=== 所有测试完成 ===")
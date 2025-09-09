#!/usr/bin/env python3
"""
测试增强的参数功能
"""

from jd.jobs.job_queue_manager import EnhancedJobQueueLogService
from jd import app, db

def test_kwargs_functionality():
    """测试kwargs参数功能"""
    
    with app.app_context():
        print("=== 测试kwargs参数功能 ===")
        
        # 测试1: 使用扩展参数创建任务
        success1, queue1, info1 = EnhancedJobQueueLogService.add(
            'test_custom_task',
            resource_id='test_123',
            session_name='session_alpha',
            custom_param1='value1',
            user_id=12345,
            batch_id='batch_001',
            operation_type='import'
        )
        db.session.commit()
        
        print(f"任务1创建: success={success1}, queue_id={queue1.id if queue1 else None}")
        if queue1:
            print(f"扩展参数: {queue1.extra_params}")
        
        # 测试2: 创建另一个带不同参数的任务
        success2, queue2, info2 = EnhancedJobQueueLogService.add(
            'test_custom_task',
            resource_id='test_456', 
            session_name='session_beta',
            custom_param1='value2',
            user_id=67890,
            batch_id='batch_002',
            operation_type='export'
        )
        db.session.commit()
        
        print(f"任务2创建: success={success2}, queue_id={queue2.id if queue2 else None}")
        if queue2:
            print(f"扩展参数: {queue2.extra_params}")
        
        return queue1, queue2

def test_search_functionality():
    """测试查找功能"""
    
    with app.app_context():
        print("\n=== 测试查找功能 ===")
        
        # 查找1: 按标准字段查找
        print("\n1. 按job_name查找正在运行的任务:")
        tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            job_name='test_custom_task'
        )
        print(f"找到 {len(tasks)} 个任务")
        for task in tasks:
            print(f"  - 任务ID: {task.id}, resource_id: {task.resource_id}")
        
        # 查找2: 按扩展参数查找
        print("\n2. 按user_id查找正在运行的任务:")
        tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            user_id=12345
        )
        print(f"找到 {len(tasks)} 个任务")
        for task in tasks:
            print(f"  - 任务ID: {task.id}, resource_id: {task.resource_id}, extra_params: {task.extra_params}")
        
        # 查找3: 按多个参数查找
        print("\n3. 按operation_type和batch_id查找:")
        tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            operation_type='import',
            batch_id='batch_001'
        )
        print(f"找到 {len(tasks)} 个任务")
        for task in tasks:
            print(f"  - 任务ID: {task.id}, resource_id: {task.resource_id}")
        
        # 查找4: 混合标准字段和扩展参数
        print("\n4. 按resource_id和user_id查找:")
        tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            resource_id='test_123',
            user_id=12345
        )
        print(f"找到 {len(tasks)} 个任务")
        
        # 查找5: 不限状态的查找
        print("\n5. 查找所有状态的batch_002任务:")
        tasks = EnhancedJobQueueLogService.find_tasks_with_params(
            batch_id='batch_002'
        )
        print(f"找到 {len(tasks)} 个任务")
        
        # 查找6: 指定状态的查找
        print("\n6. 查找RUNNING状态的export任务:")
        from jd.jobs.job_queue_manager import QueueStatus
        tasks = EnhancedJobQueueLogService.find_tasks_with_params(
            status=QueueStatus.RUNNING.value,
            operation_type='export'
        )
        print(f"找到 {len(tasks)} 个任务")

def cleanup_test_tasks():
    """清理测试任务"""
    
    with app.app_context():
        print("\n=== 清理测试任务 ===")
        
        # 查找所有测试任务并标记完成
        tasks = EnhancedJobQueueLogService.find_tasks_with_params(
            job_name='test_custom_task'
        )
        
        for task in tasks:
            if task.status == 1:  # RUNNING状态
                EnhancedJobQueueLogService.finished(task.id, "测试完成")
                print(f"任务 {task.id} 已标记完成")

if __name__ == "__main__":
    app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)
    
    # 运行测试
    queue1, queue2 = test_kwargs_functionality()
    test_search_functionality()
    cleanup_test_tasks()
    
    print("\n=== 测试完成 ===")
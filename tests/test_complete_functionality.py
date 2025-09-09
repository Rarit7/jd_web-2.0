#!/usr/bin/env python3
"""
完整功能测试：kwargs参数和查找功能
"""

from jd.jobs.job_queue_manager import EnhancedJobQueueLogService, QueueStatus
from jd import app, db

def test_comprehensive_functionality():
    """综合测试所有新功能"""
    
    with app.app_context():
        print("=== 综合功能测试 ===")
        
        # 先清理可能存在的测试任务
        cleanup_existing_test_tasks()
        
        # 测试1: 创建多个带不同扩展参数的任务
        print("\n1. 创建多个任务，每个都有不同的扩展参数:")
        
        tasks_created = []
        
        # 任务A: 数据导入任务
        success_a, queue_a, _ = EnhancedJobQueueLogService.add(
            'data_import_task',
            resource_id='dataset_001',
            session_name='import_session',
            user_id=1001,
            department='engineering',
            data_source='mysql',
            batch_size=1000,
            retry_count=3
        )
        db.session.commit()
        if success_a and queue_a:
            tasks_created.append(queue_a)
            print(f"  任务A创建成功: ID={queue_a.id}, 扩展参数={queue_a.extra_params}")
        
        # 任务B: 报表生成任务
        success_b, queue_b, _ = EnhancedJobQueueLogService.add(
            'report_generation',
            resource_id='report_001',
            session_name='report_session',
            user_id=1002,
            department='analytics',
            report_type='monthly',
            output_format='pdf',
            include_charts=True
        )
        db.session.commit()
        if success_b and queue_b:
            tasks_created.append(queue_b)
            print(f"  任务B创建成功: ID={queue_b.id}, 扩展参数={queue_b.extra_params}")
        
        # 任务C: 文件处理任务
        success_c, queue_c, _ = EnhancedJobQueueLogService.add(
            'file_processing',
            resource_id='file_batch_001',
            session_name='file_session',
            user_id=1003,
            department='operations',
            file_type='image',
            quality='high',
            compression=False,
            watermark=True
        )
        db.session.commit()
        if success_c and queue_c:
            tasks_created.append(queue_c)
            print(f"  任务C创建成功: ID={queue_c.id}, 扩展参数={queue_c.extra_params}")
        
        print(f"\n总共创建了 {len(tasks_created)} 个任务")
        
        # 测试2: 各种查找场景
        print("\n2. 测试不同的查找场景:")
        
        # 场景1: 按部门查找
        print("\n  场景1: 查找engineering部门的任务")
        eng_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            department='engineering'
        )
        print(f"    找到 {len(eng_tasks)} 个任务")
        for task in eng_tasks:
            print(f"    - ID: {task.id}, job: {task.name}, resource: {task.resource_id}")
        
        # 场景2: 按用户ID查找
        print("\n  场景2: 查找用户1002的任务")
        user_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            user_id=1002
        )
        print(f"    找到 {len(user_tasks)} 个任务")
        for task in user_tasks:
            print(f"    - ID: {task.id}, job: {task.name}")
        
        # 场景3: 按文件类型查找
        print("\n  场景3: 查找文件类型为image的任务")
        file_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            file_type='image'
        )
        print(f"    找到 {len(file_tasks)} 个任务")
        
        # 场景4: 组合条件查找
        print("\n  场景4: 查找有水印且压缩关闭的任务")
        combo_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            watermark=True,
            compression=False
        )
        print(f"    找到 {len(combo_tasks)} 个任务")
        
        # 场景5: 混合标准和扩展参数
        print("\n  场景5: 查找特定资源且为高质量的任务")
        mixed_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            resource_id='file_batch_001',
            quality='high'
        )
        print(f"    找到 {len(mixed_tasks)} 个任务")
        
        # 测试3: 不同状态的查找
        print("\n3. 测试不同状态的查找:")
        
        # 完成一个任务
        if tasks_created:
            first_task = tasks_created[0]
            EnhancedJobQueueLogService.finished(first_task.id, "测试完成")
            print(f"  任务 {first_task.id} 已标记完成")
        
        # 查找已完成的任务
        finished_tasks = EnhancedJobQueueLogService.find_tasks_with_params(
            status=QueueStatus.FINISHED.value,
            department='engineering'
        )
        print(f"  找到 {len(finished_tasks)} 个已完成的engineering任务")
        
        # 查找仍在运行的任务
        running_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params()
        print(f"  当前有 {len(running_tasks)} 个正在运行的任务")
        
        # 测试4: 边界情况
        print("\n4. 测试边界情况:")
        
        # 查找不存在的参数
        no_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            non_existent_param='value'
        )
        print(f"  查找不存在参数: 找到 {len(no_tasks)} 个任务")
        
        # 查找空值参数
        empty_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
            department=''
        )
        print(f"  查找空值参数: 找到 {len(empty_tasks)} 个任务")
        
        return tasks_created

def cleanup_existing_test_tasks():
    """清理已存在的测试任务"""
    
    # 查找并完成可能存在的测试任务
    test_job_names = ['data_import_task', 'report_generation', 'file_processing', 'test_custom_task']
    
    for job_name in test_job_names:
        tasks = EnhancedJobQueueLogService.find_tasks_with_params(
            job_name=job_name,
            status=QueueStatus.RUNNING.value
        )
        for task in tasks:
            EnhancedJobQueueLogService.finished(task.id, "清理测试任务")
    
    db.session.commit()

def cleanup_test_tasks(tasks_created):
    """清理本次测试创建的任务"""
    
    with app.app_context():
        print("\n=== 清理测试任务 ===")
        
        for task in tasks_created:
            if task.status == QueueStatus.RUNNING.value:
                EnhancedJobQueueLogService.finished(task.id, "测试完成")
                print(f"任务 {task.id} 已标记完成")
        
        db.session.commit()

def demo_usage_examples():
    """展示实际使用示例"""
    
    with app.app_context():
        print("\n=== 实际使用示例 ===")
        
        # 示例1: TG群组历史获取任务
        print("\n示例1: 创建TG群组历史获取任务")
        success, queue, info = EnhancedJobQueueLogService.add(
            'fetch_tg_group_history',
            resource_id='-1001234567890',  # chat_id
            session_name='tg_session_001',
            chat_type='supergroup',
            history_days=30,
            include_media=True,
            user_requested=True,
            requester_id=123
        )
        db.session.commit()
        
        if success:
            print(f"  任务创建成功: {queue.id}")
            
            # 查找特定用户请求的任务
            user_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
                user_requested=True,
                requester_id=123
            )
            print(f"  用户123请求的任务: {len(user_tasks)} 个")
            
            # 查找包含媒体文件的历史获取任务
            media_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
                job_name='fetch_tg_group_history',
                include_media=True
            )
            print(f"  包含媒体的历史任务: {len(media_tasks)} 个")
            
            # 完成任务
            EnhancedJobQueueLogService.finished(queue.id, "历史获取完成")
        
        # 示例2: 文件下载任务
        print("\n示例2: 创建文件下载任务")
        success, queue, info = EnhancedJobQueueLogService.add(
            'download_file',
            resource_id='file_12345',
            session_name='download_session',
            file_url='https://example.com/file.pdf',
            destination_path='/downloads/',
            max_retry=3,
            timeout=3600,
            notify_completion=True,
            notification_email='user@example.com'
        )
        db.session.commit()
        
        if success:
            print(f"  下载任务创建成功: {queue.id}")
            
            # 查找需要通知完成的任务
            notify_tasks = EnhancedJobQueueLogService.find_running_tasks_with_params(
                notify_completion=True
            )
            print(f"  需要通知完成的任务: {len(notify_tasks)} 个")
            
            # 完成任务
            EnhancedJobQueueLogService.finished(queue.id, "下载完成")

if __name__ == "__main__":
    app.ready(db_switch=True, web_switch=False, worker_switch=False, socketio_switch=False)
    
    # 运行综合测试
    tasks = test_comprehensive_functionality()
    
    # 展示使用示例
    demo_usage_examples()
    
    # 清理测试任务
    cleanup_test_tasks(tasks)
    
    print("\n=== 所有测试完成 ===")
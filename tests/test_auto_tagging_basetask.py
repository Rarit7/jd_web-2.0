"""
自动标签 BaseTask 集成测试

测试自动标签任务与 BaseTask 系统的集成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jd import app, db
from jd.tasks.auto_tagging_task import AutoTaggingTask
from jd.tasks.base_task import QueueStatus
from jd.models.job_queue_log import JobQueueLog


def test_task_instantiation():
    """测试任务实例化"""
    print("\n=== 测试 1: 任务实例化 ===")

    # 测试每日任务
    daily_task = AutoTaggingTask(task_type='daily')
    assert daily_task.get_job_name() == 'auto_tagging_task'
    assert daily_task.resource_id == 'auto_tagging_daily'
    assert daily_task.task_type == 'daily'
    print("✓ 每日任务实例化成功")

    # 测试历史任务
    historical_task = AutoTaggingTask(task_type='historical', wait_if_conflict=False)
    assert historical_task.resource_id == 'auto_tagging_historical'
    assert historical_task.wait_if_conflict == False
    print("✓ 历史任务实例化成功")

    # 测试日期范围任务
    date_range_task = AutoTaggingTask(
        task_type='date_range',
        start_date='2025-10-01T00:00:00',
        end_date='2025-10-07T23:59:59'
    )
    assert date_range_task.task_type == 'date_range'
    assert date_range_task.start_date == '2025-10-01T00:00:00'
    print("✓ 日期范围任务实例化成功")


def test_result_summary_generation():
    """测试结果摘要生成"""
    print("\n=== 测试 2: 结果摘要生成 ===")

    task = AutoTaggingTask(task_type='daily')

    # 测试成功结果
    success_result = {
        'err_code': 0,
        'payload': {
            'task_type': 'daily',
            'chat_stats': {'total_processed': 150, 'total_tags_applied': 20},
            'user_stats': {'total_processed': 75, 'total_tags_applied': 12},
            'duration_seconds': 15.3,
            'date_range': {'date': '2025-10-07'}
        }
    }

    summary = task.generate_result_summary(success_result)
    assert 'daily' in summary
    assert '150' in summary
    assert '20' in summary
    assert '75' in summary
    assert '12' in summary
    assert '15.3' in summary
    print(f"✓ 成功结果摘要: {summary}")

    # 测试失败结果
    error_result = {
        'err_code': 1,
        'err_msg': '数据库连接失败'
    }

    error_summary = task.generate_result_summary(error_result)
    assert '失败' in error_summary
    assert '数据库连接失败' in error_summary
    print(f"✓ 失败结果摘要: {error_summary}")


def test_task_conflict_detection():
    """测试任务冲突检测（需要数据库）"""
    print("\n=== 测试 3: 任务冲突检测 ===")

    with app.app_context():
        # 清理旧的测试任务
        JobQueueLog.query.filter_by(
            name='auto_tagging_task',
            resource_id='auto_tagging_daily'
        ).delete()
        db.session.commit()

        # 创建第一个任务（应该成功）
        task1 = AutoTaggingTask(task_type='daily', wait_if_conflict=False)

        # 模拟任务启动（仅创建队列记录，不执行）
        from jd.tasks.base_task import EnhancedJobQueueManager
        flag1, queue1, extra1 = EnhancedJobQueueManager.add_to_queue(
            task1.job_name,
            resource_id=task1.resource_id,
            wait_if_conflict=False
        )
        db.session.commit()

        assert flag1 == True
        assert queue1 is not None
        assert queue1.status == QueueStatus.RUNNING.value
        print(f"✓ 第一个任务创建成功，queue_id={queue1.id}")

        # 创建第二个相同类型的任务（应该冲突）
        task2 = AutoTaggingTask(task_type='daily', wait_if_conflict=False)
        flag2, queue2, extra2 = EnhancedJobQueueManager.add_to_queue(
            task2.job_name,
            resource_id=task2.resource_id,
            wait_if_conflict=False
        )

        assert flag2 == False  # 应该失败
        assert extra2.get('conflict_type') == 'resource'
        print("✓ 任务冲突检测正常工作")

        # 创建第三个任务（等待模式）
        task3 = AutoTaggingTask(task_type='daily', wait_if_conflict=True)
        flag3, queue3, extra3 = EnhancedJobQueueManager.add_to_queue(
            task3.job_name,
            resource_id=task3.resource_id,
            wait_if_conflict=True
        )
        db.session.commit()

        assert flag3 == True
        assert queue3.status == QueueStatus.WAITING.value
        print(f"✓ 等待队列创建成功，queue_id={queue3.id}，位置={extra3.get('queue_position', 0)}")

        # 完成第一个任务
        EnhancedJobQueueManager.finish_task(queue1.id, "测试完成")
        db.session.commit()

        # 检查第三个任务是否自动启动
        db.session.refresh(queue3)
        assert queue3.status == QueueStatus.RUNNING.value
        print("✓ 等待任务自动启动成功")

        # 清理
        JobQueueLog.query.filter_by(name='auto_tagging_task').delete()
        db.session.commit()


def test_api_integration():
    """测试 API 集成（需要 Flask 应用）"""
    print("\n=== 测试 4: API 集成 ===")

    with app.app_context():
        with app.test_client() as client:
            # 清理旧任务
            JobQueueLog.query.filter_by(name='auto_tagging_task').delete()
            db.session.commit()

            # 测试触发每日任务 API
            response = client.post(
                '/api/tag/auto-tagging/execute',
                json={'type': 'daily', 'wait_if_conflict': False},
                headers={'Content-Type': 'application/json'}
            )

            assert response.status_code == 200
            data = response.get_json()
            print(f"API 响应: {data}")

            # 根据响应判断（可能成功也可能因为没有数据而返回错误）
            if data.get('err_code') == 0:
                print("✓ API 调用成功")
                task_id = data['payload'].get('task_id')
                queue_id = data['payload'].get('queue_id')

                # 测试任务状态查询 API
                if task_id:
                    status_response = client.get(f'/api/tag/auto-tagging/task-status/{task_id}')
                    assert status_response.status_code == 200
                    status_data = status_response.get_json()
                    print(f"✓ 任务状态查询成功: {status_data['payload'].get('status')}")

                    # 测试停止任务 API
                    if queue_id:
                        stop_response = client.post(f'/api/tag/auto-tagging/task-stop/{task_id}')
                        assert stop_response.status_code == 200
                        print("✓ 停止任务 API 正常工作")
            else:
                print(f"⚠ API 返回错误（可能是预期的）: {data.get('err_msg')}")

            # 清理
            JobQueueLog.query.filter_by(name='auto_tagging_task').delete()
            db.session.commit()


if __name__ == '__main__':
    print("=" * 60)
    print("自动标签 BaseTask 集成测试")
    print("=" * 60)

    try:
        # 基础测试（不需要数据库）
        test_task_instantiation()
        test_result_summary_generation()

        # 数据库测试
        test_task_conflict_detection()

        # API 测试
        test_api_integration()

        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

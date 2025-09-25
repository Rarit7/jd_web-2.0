from datetime import timedelta

from celery.schedules import crontab

broker_url = 'redis://127.0.0.1:6379/0'
result_backend = 'redis://127.0.0.1:6379/1'

# 时区配置
timezone = 'Asia/Shanghai'
enable_utc = True
# 三个队列
task_routes = {
    'jd.tasks.first.*': {'queue': 'jd.celery.first'},  # 优先级高队列
    'jd.tasks.telegram.*': {'queue': 'jd.celery.telegram'},  # tg队列
}
# 默认队列
task_default_queue = 'jd.tasks.first'

beat_schedule = {
    # 'chemical_data_get_job': {
    #     'task': 'jd.tasks.first.spider_chemical.chemical_data_get_job',
    #     'schedule': timedelta(days=1),
    # },

    # Telegram群聊历史增量获取任务 - 每10分钟执行一次（协程模式）
    'tg_chat_history_job': {
        'task': 'jd.tasks.first.tg_history_job.fetch_tg_history_job',
        'schedule': timedelta(minutes=10),
        'options': {
            'expires': 3600,  # 任务1小时后过期
        }
    },

    # 'tg_account_history_job': {
    #     'task': 'jd.tasks.first.tg_history_job.fetch_account_history_job',
    #     'schedule': timedelta(minutes=45),
    # },
    # 'send_file_job': {
    #     'task': 'jd.tasks.first.send_file_job.send_file_job',
    #     'schedule': crontab(minute=0, hour='*'),
    # }

    # 每日备份群组统计数据任务 - 每天凌晨00:00执行
    'daily_backup_group_stats': {
        'task': 'jd.tasks.telegram.tg_daily_backup.daily_backup_group_stats',
        'schedule': crontab(minute=0, hour=0),  # 每天00:00执行
        'options': {
            'expires': 3600,  # 任务1小时后过期
        }
    },
}

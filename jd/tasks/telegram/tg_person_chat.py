"""
Telegram私人聊天记录获取任务
这是一个任务注册模块，实际实现在 jd.jobs.tg_person_dialog
"""

# 导入任务以便 Celery 自动发现
from jd.jobs.tg_person_dialog import fetch_person_chat_history

__all__ = ['fetch_person_chat_history']

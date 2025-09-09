from jd.views.api import api
from .queue import queue_bp

# 注册job_queue相关路由
api.register_blueprint(queue_bp, url_prefix='/job-queue')
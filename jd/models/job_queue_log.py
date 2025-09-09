from jd import db


class JobQueueLog(db.Model):
    __tablename__ = 'job_queue_log'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(126), nullable=False, unique=False, default='', comment='job name')
    description = db.Column(db.String(255), nullable=True, default='', comment='job description')
    resource_id = db.Column(db.String(100), nullable=True, default='', comment='资源ID，根据任务类型可以是chat_id、account_id、file_id等')
    session_name = db.Column(db.String(100), nullable=True, default='', comment='使用的连接名称')
    status = db.Column(db.Integer, nullable=False, default=0, comment='状态 0-待处理 1-处理中 2-已处理')
    priority = db.Column(db.Integer, nullable=False, default=0, comment='任务优先级 0-10')
    timeout_at = db.Column(db.DateTime, nullable=True, comment='任务超时时间')
    extra_params = db.Column(db.Text, nullable=True, default='', comment='扩展参数JSON')
    result = db.Column(db.Text, nullable=True, default='', comment='任务执行结果')
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    class StatusType:
        NOT_START = 0
        RUNNING = 1
        FINISHED = 2
        WAITING = 3
        CANCELLED = 4
        TIMEOUT = 5

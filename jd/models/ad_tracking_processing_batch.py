from jd import db
from jd.models.base import BaseModel
import json
from datetime import datetime


class AdTrackingProcessingBatch(BaseModel):
    """广告追踪处理批次模型"""

    __tablename__ = 'ad_tracking_processing_batches'

    # 基础字段
    id = db.Column(db.String(50), primary_key=True, comment='批次ID')
    channel_id = db.Column(db.BigInteger, nullable=False, comment='处理频道ID')
    selected_tag_ids = db.Column(db.JSON, comment='选中的标签ID列表')
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed'),
                       default='pending', comment='处理状态')

    # 进度字段
    total_messages = db.Column(db.Integer, default=0, comment='总消息数')
    processed_messages = db.Column(db.Integer, default=0, comment='已处理消息数')
    created_messages = db.Column(db.Integer, default=0, comment='创建的广告记录数')

    # 时间字段
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 错误信息
    error_message = db.Column(db.Text, comment='错误信息')

    # Celery任务信息
    task_id = db.Column(db.String(200), comment='Celery任务ID')

    # 状态常量
    class Status:
        PENDING = 'pending'
        PROCESSING = 'processing'
        COMPLETED = 'completed'
        FAILED = 'failed'

    def to_dict(self):
        """转换为字典格式，用于API响应"""
        return {
            'id': self.id,
            'channel_id': self.channel_id,
            'selected_tag_ids': self.selected_tag_ids,
            'status': self.status,
            'total_messages': self.total_messages,
            'processed_messages': self.processed_messages,
            'created_messages': self.created_messages,
            'progress': self.get_progress(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'error_message': self.error_message,
            'task_id': self.task_id
        }

    def get_progress(self):
        """获取处理进度百分比"""
        total = self.total_messages or 0
        processed = self.processed_messages or 0
        if total == 0:
            return 0
        return int((processed / total) * 100)

    def get_selected_tag_ids_list(self):
        """获取标签ID列表"""
        if not self.selected_tag_ids:
            return []
        try:
            if isinstance(self.selected_tag_ids, str):
                return json.loads(self.selected_tag_ids)
            return self.selected_tag_ids
        except (json.JSONDecodeError, TypeError):
            return []

    def update_progress(self, processed_count, created_count=0):
        """更新处理进度"""
        self.processed_messages = processed_count
        self.created_messages = created_count
        if processed_count >= self.total_messages and self.total_messages > 0:
            self.status = self.Status.COMPLETED
            self.completed_at = datetime.now()
        db.session.commit()

    def mark_as_started(self):
        """标记为开始处理"""
        self.status = self.Status.PROCESSING
        self.started_at = datetime.now()
        db.session.commit()

    def mark_as_completed(self):
        """标记为已完成"""
        self.status = self.Status.COMPLETED
        self.completed_at = datetime.now()
        db.session.commit()

    def mark_as_failed(self, error_message):
        """标记为失败"""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()
        db.session.commit()

    def set_selected_tag_ids(self, tag_ids):
        """设置选中的标签ID列表"""
        self.selected_tag_ids = json.dumps(tag_ids)
        db.session.commit()

    @classmethod
    def create_batch(cls, channel_id, tag_ids):
        """创建新的处理批次"""
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        batch = cls(
            id=batch_id,
            channel_id=channel_id,
            selected_tag_ids=json.dumps(tag_ids)
        )
        db.session.add(batch)
        db.session.commit()
        return batch

    @classmethod
    def get_by_channel_id(cls, channel_id, status=None):
        """根据频道ID获取批次"""
        query = cls.query.filter_by(channel_id=channel_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_status(cls, status):
        """根据状态获取批次"""
        return cls.query.filter_by(status=status).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_pending_batches(cls):
        """获取待处理的批次"""
        return cls.query.filter_by(status=cls.Status.PENDING).order_by(cls.created_at.asc()).all()

    @classmethod
    def get_processing_batches(cls):
        """正在处理的批次"""
        return cls.query.filter_by(status=cls.Status.PROCESSING).order_by(cls.created_at.asc()).all()

    def reset(self):
        """重置批次状态（用于重新处理）"""
        self.status = self.Status.PENDING
        self.total_messages = 0
        self.processed_messages = 0
        self.created_messages = 0
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        db.session.commit()
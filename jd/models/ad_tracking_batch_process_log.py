from jd import db
from jd.models.base import BaseModel
from datetime import datetime
import json


class AdTrackingBatchProcessLog(BaseModel):
    """广告追踪-批次处理日志

    用途：记录管理页面手动处理的批次信息
    用于跟踪和重现处理历史
    """
    __tablename__ = 'ad_tracking_batch_process_log'

    # 主键
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')

    # 批次和关联信息
    batch_id = db.Column(db.String(36), nullable=False, unique=True, comment='批次ID（UUID）')
    chat_id = db.Column(db.String(128), nullable=False, comment='群组ID')

    # 处理配置
    selected_tags = db.Column(db.JSON, nullable=True, comment='选中的标签（JSON数组）')
    selected_geo_tag = db.Column(db.Integer, nullable=True, comment='选中的地理位置标签ID')
    selected_method_tag = db.Column(db.Integer, nullable=True, comment='选中的交易方式标签ID')
    include_price = db.Column(db.Boolean, default=False, comment='是否包含价格提取')

    # 处理统计
    total_messages = db.Column(db.Integer, default=0, comment='总消息数')
    success_count = db.Column(db.Integer, default=0, comment='成功处理数')
    fail_count = db.Column(db.Integer, default=0, comment='失败处理数')
    progress = db.Column(db.Integer, default=0, comment='处理进度（百分比）')

    # 状态和时间
    status = db.Column(
        db.Enum('processing', 'success', 'failed'),
        default='processing',
        comment='处理状态'
    )
    start_time = db.Column(db.DateTime, nullable=True, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=True, comment='结束时间')

    # 时间戳
    created_at = db.Column(db.DateTime, default=db.func.now(), comment='创建时间')
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), comment='更新时间')

    # 索引定义
    __table_args__ = (
        db.Index('idx_batch_id', 'batch_id'),
        db.Index('idx_chat_id', 'chat_id'),
        db.Index('idx_status', 'status'),
        db.Index('idx_created_at', 'created_at'),
    )

    # 状态常量
    class Status:
        """处理状态常量"""
        PROCESSING = 'processing'  # 处理中
        SUCCESS = 'success'  # 处理成功
        FAILED = 'failed'  # 处理失败

    def to_dict(self):
        """转换为字典格式，用于JSON序列化"""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'chat_id': self.chat_id,
            'selected_tags': self.selected_tags,
            'selected_geo_tag': self.selected_geo_tag,
            'selected_method_tag': self.selected_method_tag,
            'include_price': self.include_price,
            'total_messages': self.total_messages,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'progress': self.progress,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_detail_dict(self):
        """获取详细信息字典"""
        base_dict = self.to_dict()
        base_dict['duration_seconds'] = self.get_duration_seconds()
        base_dict['error_count'] = self.fail_count
        base_dict['success_rate'] = self.get_success_rate()
        return base_dict

    def start_processing(self):
        """标记批次开始处理"""
        self.status = self.Status.PROCESSING
        self.start_time = datetime.now()
        self.progress = 0
        db.session.commit()

    def update_progress(self, success_count, fail_count, total_count=None):
        """更新处理进度

        Args:
            success_count: 成功处理数
            fail_count: 失败处理数
            total_count: 总数（可选，如果不提供则使用self.total_messages）
        """
        self.success_count = success_count
        self.fail_count = fail_count
        if total_count is not None:
            self.total_messages = total_count

        if self.total_messages > 0:
            self.progress = int((success_count + fail_count) / self.total_messages * 100)

        db.session.commit()

    def mark_as_completed(self):
        """标记批次处理完成"""
        self.status = self.Status.SUCCESS
        self.end_time = datetime.now()
        self.progress = 100
        db.session.commit()

    def mark_as_failed(self, reason=None):
        """标记批次处理失败

        Args:
            reason: 失败原因（可选）
        """
        self.status = self.Status.FAILED
        self.end_time = datetime.now()
        if reason:
            # 可以存储到selected_tags或其他字段
            self.selected_tags = self.selected_tags or {}
            if isinstance(self.selected_tags, str):
                self.selected_tags = json.loads(self.selected_tags)
            self.selected_tags['error_reason'] = reason
        db.session.commit()

    def get_duration_seconds(self):
        """获取处理耗时（秒）"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds())
        return None

    def get_success_rate(self):
        """获取成功率（百分比）"""
        if self.total_messages > 0:
            return round(self.success_count / self.total_messages * 100, 2)
        return 0.0

    @classmethod
    def get_by_batch_id(cls, batch_id):
        """按批次ID查询"""
        return cls.query.filter_by(batch_id=batch_id).first()

    @classmethod
    def get_by_chat_id(cls, chat_id, status=None, limit=100):
        """按群组ID查询

        Args:
            chat_id: 群组ID
            status: 可选的状态筛选
            limit: 结果限制数
        """
        query = cls.query.filter_by(chat_id=chat_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_processing_batches(cls):
        """获取所有处理中的批次"""
        return cls.query.filter_by(status=cls.Status.PROCESSING).all()

    @classmethod
    def get_recent_batches(cls, days=7, limit=100):
        """获取最近N天内的批次"""
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        return cls.query.filter(
            cls.created_at >= start_date
        ).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_statistics_by_chat(cls, chat_id):
        """获取指定群组的处理统计"""
        from sqlalchemy import func
        total = cls.query.filter_by(chat_id=chat_id).count()
        success = cls.query.filter_by(chat_id=chat_id, status=cls.Status.SUCCESS).count()
        failed = cls.query.filter_by(chat_id=chat_id, status=cls.Status.FAILED).count()
        processing = cls.query.filter_by(chat_id=chat_id, status=cls.Status.PROCESSING).count()

        total_messages = cls.query.filter_by(chat_id=chat_id).with_entities(
            func.sum(cls.total_messages)
        ).scalar() or 0

        total_success = cls.query.filter_by(chat_id=chat_id).with_entities(
            func.sum(cls.success_count)
        ).scalar() or 0

        return {
            'chat_id': chat_id,
            'total_batches': total,
            'success_batches': success,
            'failed_batches': failed,
            'processing_batches': processing,
            'total_messages_processed': total_messages,
            'total_messages_success': total_success,
        }

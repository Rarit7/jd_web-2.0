"""
统一日志配置模块
提供结构化、高性能的日志管理方案
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Dict, Any
import json


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'process_id': os.getpid(),
            'thread_id': record.thread,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        # 添加自定义字段
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
            
        return json.dumps(log_data, ensure_ascii=False)


class TelegramLogFilter(logging.Filter):
    """Telegram相关日志过滤器"""
    
    def filter(self, record):
        # 过滤Telethon的冗余日志
        if record.name.startswith('telethon'):
            return record.levelno >= logging.WARNING
        return True


class PerformanceLogFilter(logging.Filter):
    """性能相关日志过滤器"""
    
    def __init__(self, min_duration_ms=100):
        super().__init__()
        self.min_duration_ms = min_duration_ms
    
    def filter(self, record):
        # 只记录超过指定时间的性能日志
        if hasattr(record, 'duration_ms'):
            return record.duration_ms >= self.min_duration_ms
        return True


def setup_logging(app_config: Dict[str, Any]) -> None:
    """
    设置统一的日志配置
    
    Args:
        app_config: Flask应用配置
    """
    # 获取配置
    log_level = app_config.get('LOG_LEVEL', 'INFO')
    log_dir = app_config.get('LOG_DIR', 'logs')
    max_bytes = app_config.get('LOG_MAX_BYTES', 50 * 1024 * 1024)  # 50MB
    backup_count = app_config.get('LOG_BACKUP_COUNT', 5)
    enable_structured = app_config.get('LOG_STRUCTURED', True)
    
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 清除现有处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 设置根日志级别
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    if enable_structured:
        console_formatter = StructuredFormatter()
    else:
        console_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s:%(lineno)d: %(message)s'
        )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(TelegramLogFilter())
    root_logger.addHandler(console_handler)
    
    # 应用日志文件处理器
    app_log_file = os.path.join(log_dir, 'app.log')
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    app_handler.setFormatter(console_formatter)
    app_handler.addFilter(TelegramLogFilter())
    root_logger.addHandler(app_handler)
    
    # 错误日志文件处理器（只记录ERROR及以上）
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(console_formatter)
    root_logger.addHandler(error_handler)
    
    # Telegram专用日志处理器
    tg_log_file = os.path.join(log_dir, 'telegram.log')
    tg_handler = logging.handlers.RotatingFileHandler(
        tg_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    tg_handler.setFormatter(console_formatter)
    
    # 只有Telegram相关的logger才使用这个handler
    tg_logger = logging.getLogger('jd.jobs.tg')
    tg_logger.addHandler(tg_handler)
    tg_logger.propagate = False  # 不传播到root logger
    
    # 性能日志处理器
    perf_log_file = os.path.join(log_dir, 'performance.log')
    perf_handler = logging.handlers.RotatingFileHandler(
        perf_log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    perf_handler.setFormatter(console_formatter)
    perf_handler.addFilter(PerformanceLogFilter())
    
    perf_logger = logging.getLogger('performance')
    perf_logger.addHandler(perf_handler)
    perf_logger.propagate = False
    
    # 设置第三方库日志级别
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def get_logger(name: str, extra_fields: Dict[str, Any] = None) -> logging.Logger:
    """
    获取配置好的logger实例
    
    Args:
        name: logger名称
        extra_fields: 额外的结构化字段
        
    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name)
    
    if extra_fields:
        # 创建LoggerAdapter来添加额外字段
        class ExtraFieldsAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                if 'extra' not in kwargs:
                    kwargs['extra'] = {}
                kwargs['extra']['extra_fields'] = self.extra
                return msg, kwargs
        
        return ExtraFieldsAdapter(logger, extra_fields)
    
    return logger


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, logger_name: str = 'performance'):
        self.logger = logging.getLogger(logger_name)
        self.start_time = None
    
    def start(self, operation: str, **kwargs):
        """开始计时"""
        import time
        self.start_time = time.time()
        self.operation = operation
        self.context = kwargs
        
    def end(self, **extra_info):
        """结束计时并记录"""
        if self.start_time is None:
            return
            
        import time
        duration_ms = (time.time() - self.start_time) * 1000
        
        log_data = {
            'operation': self.operation,
            'duration_ms': duration_ms,
            **self.context,
            **extra_info
        }
        
        # 使用extra传递duration_ms以便过滤器使用
        self.logger.info(
            f"Performance: {self.operation} took {duration_ms:.2f}ms",
            extra={'duration_ms': duration_ms, 'extra_fields': log_data}
        )
        
        self.start_time = None


# 便捷函数
def log_performance(operation: str, **context):
    """装饰器：自动记录函数执行时间"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            perf_logger = PerformanceLogger()
            perf_logger.start(operation, function=func.__name__, **context)
            try:
                result = func(*args, **kwargs)
                perf_logger.end(success=True)
                return result
            except Exception as e:
                perf_logger.end(success=False, error=str(e))
                raise
        return wrapper
    return decorator


async def async_log_performance(operation: str, **context):
    """异步装饰器：自动记录异步函数执行时间"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            perf_logger = PerformanceLogger()
            perf_logger.start(operation, function=func.__name__, **context)
            try:
                result = await func(*args, **kwargs)
                perf_logger.end(success=True)
                return result
            except Exception as e:
                perf_logger.end(success=False, error=str(e))
                raise
        return wrapper
    return decorator
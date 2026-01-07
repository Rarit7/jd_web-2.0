"""缓存服务 - 封装 Redis 操作"""
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CacheService:
    """缓存服务 - 封装 Redis 操作"""

    _redis = None

    @classmethod
    def get_redis(cls):
        """获取 Redis 客户端"""
        if cls._redis is None:
            try:
                from redis import Redis
                from flask import current_app

                cls._redis = Redis(
                    host=current_app.config.get('REDIS_HOST', 'localhost'),
                    port=current_app.config.get('REDIS_PORT', 6379),
                    db=current_app.config.get('REDIS_DB', 0),
                    decode_responses=True
                )
                # 测试连接
                cls._redis.ping()
            except Exception as e:
                logger.warning(f"Redis 连接失败: {e}")
                cls._redis = None
        return cls._redis

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，如果不存在或出错返回 None
        """
        try:
            redis = CacheService.get_redis()
            if redis is None:
                return None

            value = redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis get 失败: key={key}, error={e}")
        return None

    @staticmethod
    def set(key: str, value: Any, ttl: int = 3600) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值（将被 JSON 序列化）
            ttl: 过期时间（秒），默认1小时

        Returns:
            bool: 是否设置成功
        """
        try:
            redis = CacheService.get_redis()
            if redis is None:
                return False

            redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.warning(f"Redis set 失败: key={key}, error={e}")
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            bool: 是否删除成功
        """
        try:
            redis = CacheService.get_redis()
            if redis is None:
                return False

            redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete 失败: key={key}, error={e}")
            return False

    @staticmethod
    def clear_pattern(pattern: str) -> int:
        """
        删除匹配模式的所有缓存

        Args:
            pattern: Redis 通配符模式

        Returns:
            int: 删除的键数量
        """
        try:
            redis = CacheService.get_redis()
            if redis is None:
                return 0

            keys = redis.keys(pattern)
            if keys:
                return redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis 清空缓存失败: pattern={pattern}, error={e}")
            return 0

    @staticmethod
    def keys(pattern: str = '*') -> list:
        """
        获取匹配模式的所有键

        Args:
            pattern: Redis 通配符模式

        Returns:
            list: 键列表
        """
        try:
            redis = CacheService.get_redis()
            if redis is None:
                return []

            return redis.keys(pattern)
        except Exception as e:
            logger.warning(f"Redis keys 失败: pattern={pattern}, error={e}")
            return []

    @staticmethod
    def exists(key: str) -> bool:
        """
        检查缓存键是否存在

        Args:
            key: 缓存键

        Returns:
            bool: 是否存在
        """
        try:
            redis = CacheService.get_redis()
            if redis is None:
                return False

            return redis.exists(key) > 0
        except Exception as e:
            logger.warning(f"Redis exists 失败: key={key}, error={e}")
            return False

    @staticmethod
    def get_ttl(key: str) -> int:
        """
        获取缓存过期时间

        Args:
            key: 缓存键

        Returns:
            int: 剩余过期时间（秒），-1表示永久存储，-2表示不存在
        """
        try:
            redis = CacheService.get_redis()
            if redis is None:
                return -2

            return redis.ttl(key)
        except Exception as e:
            logger.warning(f"Redis ttl 失败: key={key}, error={e}")
            return -2

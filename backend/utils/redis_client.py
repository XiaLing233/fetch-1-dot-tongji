"""Redis 客户端单例。可在任何地方使用，无需 Flask app context。"""

import os

import redis

_redis_client = None


def get_redis():
    """返回 Redis 客户端单例。"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=0,
        )
    return _redis_client

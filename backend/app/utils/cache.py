"""缓存工具：Redis 优先，无 Redis 时降级为内存缓存"""

import json
import hashlib
import time
import threading
from functools import wraps
from app.config import get_settings

settings = get_settings()

# 尝试连接 Redis
_redis_available = False
_redis_client = None
_memory_cache: dict = {}
_memory_ttl: dict = {}
_lock = threading.Lock()

if settings.redis_url:
    try:
        from redis import Redis
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        _redis_available = True
    except Exception:
        _redis_available = False


def _clean_expired():
    """清理过期的内存缓存"""
    now = time.time()
    with _lock:
        expired = [k for k, v in _memory_ttl.items() if v < now]
        for k in expired:
            _memory_cache.pop(k, None)
            _memory_ttl.pop(k, None)


def cache_get(key: str) -> str | None:
    """从缓存获取值"""
    if _redis_available and _redis_client:
        return _redis_client.get(key)
    else:
        _clean_expired()
        with _lock:
            if key in _memory_ttl and _memory_ttl[key] > time.time():
                return _memory_cache.get(key)
            else:
                _memory_cache.pop(key, None)
                _memory_ttl.pop(key, None)
                return None


def cache_set(key: str, value: str, ttl: int = 600):
    """设置缓存"""
    if _redis_available and _redis_client:
        _redis_client.setex(key, ttl, value)
    else:
        with _lock:
            _memory_cache[key] = value
            _memory_ttl[key] = time.time() + ttl


def cache_delete(key: str):
    """删除缓存"""
    if _redis_available and _redis_client:
        _redis_client.delete(key)
    else:
        with _lock:
            _memory_cache.pop(key, None)
            _memory_ttl.pop(key, None)


def cache_invalidate_pattern(pattern: str):
    """按模式删除缓存"""
    if _redis_available and _redis_client:
        keys = _redis_client.keys(pattern)
        if keys:
            _redis_client.delete(*keys)
    else:
        _clean_expired()


def cache_result(ttl: int = 600, prefix: str = "cache"):
    """缓存函数结果的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [prefix, func.__name__]
            key_parts.append(hashlib.md5(
                json.dumps({"args": str(args), "kwargs": str(kwargs)}, sort_keys=True).encode()
            ).hexdigest())
            cache_key = ":".join(key_parts)

            cached = cache_get(cache_key)
            if cached:
                return json.loads(cached)

            result = func(*args, **kwargs)
            cache_set(cache_key, json.dumps(result, ensure_ascii=False), ttl)
            return result

        return wrapper

    return decorator

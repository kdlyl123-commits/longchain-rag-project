"""API 限流中间件（基于 Redis 滑动窗口，本地模式自动降级）"""

import time
import hashlib
from fastapi import Request, HTTPException, status
from app.config import get_settings

settings = get_settings()

# Redis 延迟初始化（避免本地无 Redis 时模块导入失败）
_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None and settings.redis_url:
        try:
            from redis import Redis
            _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            _redis_client = False  # 标记为不可用
    return _redis_client if _redis_client and _redis_client is not False else None


class RateLimiter:
    """滑动窗口限流器"""

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check(self, request: Request, user_id: int | str) -> bool:
        """检查是否超过限流阈值"""
        r = _get_redis()
        if not r:
            return True  # 无 Redis 时长允许通过

        key = f"rate:{user_id}"
        now = time.time()
        window_start = now - self.window_seconds

        r.zremrangebyscore(key, 0, window_start)
        count = r.zcard(key)
        if count >= self.max_requests:
            return False

        r.zadd(key, {str(now): now})
        r.expire(key, self.window_seconds + 10)
        return True


rate_limiter = RateLimiter(max_requests=60, window_seconds=60)


async def check_rate_limit(request: Request):
    """FastAPI 依赖：基于 IP 哈希的限流检查"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    # SHA256 哈希保护隐私（仅防日志泄露，不防 Redis 访问）
    user_key = hashlib.sha256(client_ip.encode()).hexdigest()[:24]

    if not await rate_limiter.check(request, user_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
        )

"""API 限流中间件（基于 Redis 滑动窗口）"""

import time
import hashlib
from fastapi import Request, HTTPException, status
from redis import Redis
from app.config import get_settings

settings = get_settings()
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


class RateLimiter:
    """滑动窗口限流器"""

    def __init__(
        self,
        max_requests: int = 60,  # 每分钟最大请求数
        window_seconds: int = 60,  # 窗口大小（秒）
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check(self, request: Request, user_id: int | str) -> bool:
        """检查是否超过限流阈值"""
        key = f"rate:{user_id}"
        now = time.time()
        window_start = now - self.window_seconds

        # 移除窗口外的记录
        redis_client.zremrangebyscore(key, 0, window_start)

        # 统计窗口内请求数
        count = redis_client.zcard(key)

        if count >= self.max_requests:
            return False

        # 记录当前请求
        redis_client.zadd(key, {str(now): now})
        redis_client.expire(key, self.window_seconds + 10)

        return True


# 全局限流器实例
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)


async def check_rate_limit(request: Request):
    """FastAPI 依赖：检查 API 限流"""
    # 获取用户标识（优先使用登录用户，否则用 IP）
    user_id = None
    try:
        # 尝试从 Authorization header 获取用户
        from app.middleware.auth import get_current_user
        # 这里从 request 中提取 token 较为复杂，简单起见用 IP
    except Exception:
        pass

    # 使用 IP 作为标识
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    # 对 IP 做 hash 避免存储原始 IP
    user_key = hashlib.md5(client_ip.encode()).hexdigest()[:12]

    if not await rate_limiter.check(request, user_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
        )

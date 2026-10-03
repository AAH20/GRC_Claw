"""Rate limiting module."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status


class RateLimiter:
    """In-memory rate limiter using sliding window algorithm."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ) -> None:
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def check_rate_limit(self, request: Request) -> None:
        """Check if the request is within rate limits."""
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        # Clean old requests
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > window_start
        ]

        # Check burst
        if len(self._requests[client_ip]) >= self.burst_size:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"},
            )

        # Check rate per minute
        if len(self._requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"},
            )

        self._requests[client_ip].append(now)


class RedisRateLimiter:
    """Redis-based distributed rate limiter."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        requests_per_minute: int = 60,
    ) -> None:
        self.redis_url = redis_url
        self.requests_per_minute = requests_per_minute

    async def check_rate_limit(self, request: Request) -> None:
        """Check rate limit using Redis."""
        import redis.asyncio as redis

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"

        r = await redis.from_url(self.redis_url)
        try:
            pipe = r.pipeline()
            now = time.time()
            window_start = now - 60

            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, 60)

            results = await pipe.execute()
            request_count = results[1]

            if request_count >= self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": "60"},
                )
        finally:
            await r.close()


rate_limiter = RateLimiter()

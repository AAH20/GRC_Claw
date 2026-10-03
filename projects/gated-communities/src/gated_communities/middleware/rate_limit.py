"""
Rate limiting middleware for gated communities.

Implements:
- RateLimitMiddleware: ASGI middleware using token bucket algorithm with Redis.
- rate_limit(requests, window): Decorator for endpoint-level rate limits.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, Optional

import redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket rate limiter backed by Redis for distributed rate limiting."""

    def __init__(
        self,
        redis_client: redis.Redis,
        key_prefix: str = "rate_limit",
        capacity: int = 100,
        refill_rate: float = 1.0,
    ):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.capacity = capacity
        self.refill_rate = refill_rate

    def _key(self, identifier: str) -> str:
        return f"{self.key_prefix}:{identifier}"

    def is_allowed(self, identifier: str, tokens: int = 1) -> bool:
        """Check if request is allowed under the rate limit."""
        key = self._key(identifier)
        now = time.time()

        pipe = self.redis.pipeline()
        pipe.hgetall(key)
        result = pipe.execute()

        bucket = result[0]
        if not bucket:
            # Initialize new bucket
            pipe.hset(key, mapping={
                "tokens": self.capacity - tokens,
                "last_refill": now,
            })
            pipe.expire(key, int(self.capacity / self.refill_rate) + 1)
            pipe.execute()
            return True

        current_tokens = float(bucket.get(b"tokens", self.capacity))
        last_refill = float(bucket.get(b"last_refill", now))

        # Calculate tokens to add based on time elapsed
        elapsed = now - last_refill
        tokens_to_add = elapsed * self.refill_rate
        new_tokens = min(self.capacity, current_tokens + tokens_to_add)

        if new_tokens >= tokens:
            pipe.hset(key, mapping={
                "tokens": new_tokens - tokens,
                "last_refill": now,
            })
            pipe.expire(key, int(self.capacity / self.refill_rate) + 1)
            pipe.execute()
            return True
        else:
            pipe.hset(key, mapping={
                "tokens": new_tokens,
                "last_refill": now,
            })
            pipe.execute()
            return False

    def get_remaining(self, identifier: str) -> int:
        """Get remaining tokens for an identifier."""
        key = self._key(identifier)
        bucket = self.redis.hgetall(key)
        if not bucket:
            return self.capacity
        return int(float(bucket.get(b"tokens", self.capacity)))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm with Redis."""

    def __init__(
        self,
        app: Any,
        redis_url: str = "redis://localhost:6379/0",
        requests_per_minute: int = 100,
        burst_size: int = 10,
    ) -> None:
        super().__init__(app)
        self.redis = redis.from_url(redis_url, decode_responses=False)
        self.bucket = TokenBucket(
            redis_client=self.redis,
            capacity=burst_size,
            refill_rate=requests_per_minute / 60.0,
        )
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        if not self.bucket.is_allowed(client_ip):
            logger.warning("rate_limit_exceeded", extra={"client_ip": client_ip})
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.bucket.get_remaining(client_ip)
        )
        return response


def rate_limit(requests: int, window: int):
    """
    Decorator for endpoint-level rate limiting.

    Args:
        requests: Maximum number of requests allowed.
        window: Time window in seconds.

    Usage:
        @rate_limit(requests=10, window=60)
        async def my_endpoint(request: Request):
            ...
    """

    def decorator(func: Callable) -> Callable:
        _redis: Optional[redis.Redis] = None

        def _get_redis() -> redis.Redis:
            nonlocal _redis
            if _redis is None:
                _redis = redis.from_url(
                    "redis://localhost:6379/0", decode_responses=False
                )
            return _redis

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract request from args (FastAPI/Starlette style)
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                return await func(*args, **kwargs)

            # Build identifier
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                identifier = forwarded.split(",")[0].strip()
            elif request.client:
                identifier = request.client.host
            else:
                identifier = "unknown"

            # Include function name in key for per-endpoint limits
            key = f"endpoint:{func.__module__}.{func.__qualname__}:{identifier}"

            # Token bucket logic
            r = _get_redis()
            bucket = TokenBucket(
                redis_client=r,
                key_prefix=key,
                capacity=requests,
                refill_rate=requests / window,
            )

            if not bucket.is_allowed(identifier):
                return Response(
                    content='{"detail": "Rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": str(window)},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator

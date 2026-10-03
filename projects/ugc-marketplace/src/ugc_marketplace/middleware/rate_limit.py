"""Rate limiting middleware for UGC Marketplace."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis-backed distributed rate limiting.

    Falls back to in-memory rate limiting if Redis is unavailable.
    """

    def __init__(
        self,
        app: Any,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        redis_url: str | None = None,
    ) -> None:
        """Initialize rate limit middleware.

        Args:
            app: The ASGI application.
            requests_per_minute: Maximum requests per minute per client.
            burst_size: Maximum burst size for token bucket.
            redis_url: Optional Redis URL for distributed rate limiting.
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.redis_url = redis_url
        self._memory_store: dict[str, list[float]] = defaultdict(list)
        self._redis_client: Any = None

    async def _get_redis(self) -> Any:
        """Get or create Redis client.

        Returns:
            Redis client or None if unavailable.
        """
        if self._redis_client is None and self.redis_url:
            try:
                import redis.asyncio as redis

                self._redis_client = redis.from_url(self.redis_url)
            except Exception:
                logger.warning("Redis unavailable, using in-memory rate limiting")
                return None
        return self._redis_client

    def _get_client_key(self, request: Request) -> str:
        """Get client identifier from request.

        Args:
            request: The incoming request.

        Returns:
            Client identifier string.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def _is_rate_limited(self, key: str) -> tuple[bool, dict[str, Any]]:
        """Check if request should be rate limited.

        Args:
            key: Client identifier.

        Returns:
            Tuple of (is_limited, rate_limit_info).
        """
        now = time.time()
        window_start = now - 60

        # Try Redis first
        redis_client = await self._get_redis()
        if redis_client:
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, 60)
            results = await pipe.execute()
            request_count = results[1]

            if request_count > self.requests_per_minute:
                return True, {
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + 60)),
                }
            return False, {
                "X-RateLimit-Limit": str(self.requests_per_minute),
                "X-RateLimit-Remaining": str(self.requests_per_minute - request_count),
                "X-RateLimit-Reset": str(int(now + 60)),
            }

        # Fallback to in-memory
        requests = self._memory_store[key]
        # Remove old requests
        self._memory_store[key] = [t for t in requests if t > window_start]

        if len(self._memory_store[key]) >= self.requests_per_minute:
            return True, {
                "X-RateLimit-Limit": str(self.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(now + 60)),
            }

        self._memory_store[key].append(now)
        remaining = self.requests_per_minute - len(self._memory_store[key])
        return False, {
            "X-RateLimit-Limit": str(self.requests_per_minute),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(now + 60)),
        }

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Process request with rate limiting.

        Args:
            request: The incoming request.
            call_next: The next handler in the chain.

        Returns:
            Response from next handler or rate limit error.
        """
        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/ready", "/live"):
            return await call_next(request)

        client_key = self._get_client_key(request)
        rate_limit_key = f"ratelimit:{client_key}"

        is_limited, headers = await self._is_rate_limited(rate_limit_key)

        if is_limited:
            logger.warning(
                "Rate limit exceeded",
                client=client_key,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={**headers, "Retry-After": "60"},
            )

        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response


def rate_limit(requests: int, window: int):
    """Decorator for endpoint-level rate limiting.

    Args:
        requests: Maximum number of requests allowed in the time window.
        window: Time window in seconds.

    Usage:
        @app.get("/api/resource")
        @rate_limit(requests=10, window=60)
        async def get_resource():
            return {"data": "value"}
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from fastapi import HTTPException, Request

            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")

            if request is None:
                raise ValueError("rate_limit decorator requires a Request parameter")

            redis_client = getattr(request.app.state, "redis", None)
            if redis_client is None:
                import redis.asyncio as redis

                redis_client = redis.from_url("redis://localhost:6379/0")

            client_id = _get_client_id(request)
            key = f"ratelimit:{func.__name__}:{client_id}"

            now = time.time()
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            results = await pipe.execute()
            current_count = results[1]

            if current_count >= requests:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(window)},
                )

            pipe = redis_client.pipeline()
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window)
            await pipe.execute()

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def _get_client_id(request) -> str:
    """Extract client identifier from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

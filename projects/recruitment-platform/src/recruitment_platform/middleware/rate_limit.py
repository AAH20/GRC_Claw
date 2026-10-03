"""
Rate limiting middleware for the recruitment platform.

Uses Redis for distributed rate limiting with a token bucket algorithm.
"""

import functools
import time
from typing import Any, Callable, Optional

import redis
from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TokenBucket:
    """
    Token bucket rate limiter backed by Redis.

    Each key has a bucket with a fixed capacity that refills at a constant rate.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        capacity: int,
        refill_rate: float,
        key_prefix: str = "ratelimit",
    ):
        self.redis = redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.key_prefix = key_prefix

    def _key(self, identifier: str) -> str:
        return f"{self.key_prefix}:{identifier}"

    def allow_request(self, identifier: str, tokens: int = 1) -> bool:
        """
        Check if a request is allowed under the rate limit.

        Uses a Lua script for atomic token bucket operations in Redis.
        """
        key = self._key(identifier)
        now = time.time()

        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local tokens_requested = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])

        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1])
        local last_refill = tonumber(bucket[2])

        if tokens == nil then
            tokens = capacity
            last_refill = now
        end

        -- Calculate tokens to add based on time elapsed
        local elapsed = now - last_refill
        local new_tokens = math.min(capacity, tokens + elapsed * refill_rate)

        if new_tokens >= tokens_requested then
            new_tokens = new_tokens - tokens_requested
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
            redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) + 1)
            return 1
        else
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
            redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) + 1)
            return 0
        end
        """

        result = self.redis.eval(lua_script, 1, key, self.capacity, self.refill_rate, tokens, now)
        return bool(result)

    def get_remaining(self, identifier: str) -> float:
        """Get remaining tokens for an identifier."""
        key = self._key(identifier)
        data = self.redis.hmget(key, "tokens", "last_refill")
        if data[0] is None:
            return float(self.capacity)

        tokens = float(data[0])
        last_refill = float(data[1]) if data[1] else time.time()
        elapsed = time.time() - last_refill
        return min(float(self.capacity), tokens + elapsed * self.refill_rate)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI/Starlette middleware for rate limiting using token bucket algorithm.

    Applies a global rate limit to all requests. Use the `rate_limit` decorator
    for endpoint-specific limits.
    """

    def __init__(
        self,
        app: Any,
        redis_url: str = "redis://localhost:6379/0",
        requests_per_minute: int = 60,
        key_func: Optional[Callable[[Request], str]] = None,
        exclude_paths: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.bucket = TokenBucket(
            redis_client=self.redis_client,
            capacity=requests_per_minute,
            refill_rate=requests_per_minute / 60.0,
        )
        self.key_func = key_func or self._default_key_func
        self.exclude_paths = exclude_paths or []

    @staticmethod
    def _default_key_func(request: Request) -> str:
        """Default key function uses client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        identifier = self.key_func(request)

        if not self.bucket.allow_request(identifier):
            retry_after = int(self.bucket.capacity / self.bucket.refill_rate)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        response = await call_next(request)

        # Add rate limit headers
        remaining = int(self.bucket.get_remaining(identifier))
        response.headers["X-RateLimit-Limit"] = str(self.bucket.capacity)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

        return response


def rate_limit(requests: int, window: int):
    """
    Decorator for endpoint-level rate limiting.

    Args:
        requests: Maximum number of requests allowed in the window.
        window: Time window in seconds.

    Usage:
        @app.get("/api/jobs")
        @rate_limit(requests=10, window=60)
        async def list_jobs():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract request from args/kwargs
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")

            if request is None:
                # No request object found, skip rate limiting
                return await func(*args, **kwargs)

            # Get Redis client from app state or create one
            redis_client: Optional[redis.Redis] = getattr(request.app.state, "redis", None)
            if redis_client is None:
                redis_client = redis.from_url(
                    getattr(request.app.state, "redis_url", "redis://localhost:6379/0"),
                    decode_responses=True,
                )

            # Build identifier from user or IP
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                identifier = f"user:{user_id}"
            else:
                forwarded = request.headers.get("X-Forwarded-For")
                if forwarded:
                    identifier = f"ip:{forwarded.split(',')[0].strip()}"
                else:
                    identifier = f"ip:{request.client.host if request.client else 'unknown'}"

            # Create bucket for this specific rate limit
            bucket = TokenBucket(
                redis_client=redis_client,
                capacity=requests,
                refill_rate=requests / window,
                key_prefix=f"endpoint:{func.__module__}.{func.__name__}",
            )

            if not bucket.allow_request(identifier):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Maximum {requests} requests per {window} seconds.",
                    headers={"Retry-After": str(window)},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator

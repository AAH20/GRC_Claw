"""Rate limiting middleware with token bucket and sliding window algorithms."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, Request

from app.core.config import get_settings
from app.core.exceptions import RateLimitException
from app.middleware.auth import AuthContext, get_current_auth

settings = get_settings()


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithm."""

    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"


@dataclass
class TokenBucket:
    """Token bucket state."""

    tokens: float = 0
    last_refill: float = field(default_factory=time.time)
    rate: float = 100  # tokens per second
    capacity: int = 200  # max tokens


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an endpoint."""

    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    requests_per_second: float = 100
    burst_size: int = 200
    daily_limit: int | None = None


# Endpoint-specific rate limits
ENDPOINT_RATE_LIMITS: dict[str, RateLimitConfig] = {
    "POST /v1.0/enforcement/decide": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=10000,
        burst_size=2000,
    ),
    "POST /v1.0/enforcement/decide-batch": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=1000,
        burst_size=200,
    ),
    "GET /v1.0/policies": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=1000,
        burst_size=200,
    ),
    "POST /v1.0/policies": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=100,
        burst_size=20,
    ),
    "POST /v1.0/evidence": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=5000,
        burst_size=500,
    ),
    "GET /v1.0/audit": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=500,
        burst_size=50,
    ),
    "POST /v1.0/compliance/reports": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=10,
        burst_size=20,
    ),
    "POST /v1.0/graphql": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=1000,
        burst_size=200,
    ),
}

# Tier-based rate limits
TIER_RATE_LIMITS: dict[str, RateLimitConfig] = {
    "free": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=10,
        burst_size=20,
        daily_limit=10000,
    ),
    "standard": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=100,
        burst_size=200,
        daily_limit=1000000,
    ),
    "enterprise": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=1000,
        burst_size=2000,
        daily_limit=10000000,
    ),
    "unlimited": RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        requests_per_second=100000,
        burst_size=200000,
    ),
}


class InMemoryRateLimiter:
    """In-memory rate limiter for development/single-instance use."""

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._redis: redis.Redis | None = None

    async def get_redis(self) -> redis.Redis | None:
        """Get Redis client if available."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate a rate limit key."""
        return f"ratelimit:{identifier}:{endpoint}"

    async def is_allowed(
        self,
        identifier: str,
        endpoint: str,
        config: RateLimitConfig,
    ) -> tuple[bool, dict[str, int | str]]:
        """Check if a request is allowed under the rate limit.

        Returns (allowed, rate_limit_headers).
        """
        redis_client = await self.get_redis()

        if redis_client:
            return await self._check_redis(redis_client, identifier, endpoint, config)
        else:
            return self._check_memory(identifier, endpoint, config)

    async def _check_redis(
        self,
        client: redis.Redis,
        identifier: str,
        endpoint: str,
        config: RateLimitConfig,
    ) -> tuple[bool, dict[str, int | str]]:
        """Check rate limit using Redis."""
        key = self._get_key(identifier, endpoint)
        now = time.time()

        if config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return await self._sliding_window_redis(client, key, now, config)
        else:
            return await self._token_bucket_redis(client, key, now, config)

    async def _token_bucket_redis(
        self,
        client: redis.Redis,
        key: str,
        now: float,
        config: RateLimitConfig,
    ) -> tuple[bool, dict[str, int | str]]:
        """Token bucket algorithm using Redis."""
        pipe = client.pipeline()
        pipe.hgetall(key)

        bucket_data = await pipe.hgetall(key)

        tokens = float(bucket_data.get("tokens", config.burst_size))
        last_refill = float(bucket_data.get("last_refill", now))

        # Refill tokens
        elapsed = now - last_refill
        tokens = min(config.burst_size, tokens + elapsed * config.requests_per_second)

        if tokens >= 1:
            tokens -= 1
            pipe.hset(key, mapping={"tokens": tokens, "last_refill": now})
            pipe.expire(key, 3600)
            await pipe.execute()

            remaining = int(tokens)
            reset_at = int(now + (config.burst_size - tokens) / config.requests_per_second)
            return True, {
                "X-RateLimit-Limit": str(config.burst_size),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_at),
                "X-RateLimit-Policy": config.algorithm.value,
            }
        else:
            pipe.hset(key, mapping={"tokens": tokens, "last_refill": now})
            pipe.expire(key, 3600)
            await pipe.execute()

            retry_after = int((1 - tokens) / config.requests_per_second) + 1
            raise RateLimitException(retry_after=retry_after, limit=config.burst_size)

    async def _sliding_window_redis(
        self,
        client: redis.Redis,
        key: str,
        now: float,
        config: RateLimitConfig,
    ) -> tuple[bool, dict[str, int | str]]:
        """Sliding window algorithm using Redis."""
        window_key = f"{key}:window"
        window_size = 1.0  # 1 second window

        pipe = client.pipeline()
        pipe.zremrangebyscore(window_key, 0, now - window_size)
        pipe.zcard(window_key)
        results = await pipe.execute()

        current_count = results[1]

        if current_count < config.requests_per_second:
            pipe.zadd(window_key, {str(now): now})
            pipe.expire(window_key, 60)
            await pipe.execute()

            remaining = int(config.requests_per_second - current_count - 1)
            return True, {
                "X-RateLimit-Limit": str(int(config.requests_per_second)),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(now + window_size)),
                "X-RateLimit-Policy": config.algorithm.value,
            }
        else:
            retry_after = 1
            raise RateLimitException(retry_after=retry_after, limit=int(config.requests_per_second))

    def _check_memory(
        self,
        identifier: str,
        endpoint: str,
        config: RateLimitConfig,
    ) -> tuple[bool, dict[str, int | str]]:
        """Check rate limit in memory."""
        key = self._get_key(identifier, endpoint)
        now = time.time()

        if config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return self._sliding_window_memory(key, now, config)
        else:
            return self._token_bucket_memory(key, now, config)

    def _token_bucket_memory(
        self,
        key: str,
        now: float,
        config: RateLimitConfig,
    ) -> tuple[bool, dict[str, int | str]]:
        """Token bucket algorithm in memory."""
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(
                tokens=config.burst_size,
                last_refill=now,
                rate=config.requests_per_second,
                capacity=config.burst_size,
            )
            self._buckets[key] = bucket

        # Refill tokens
        elapsed = now - bucket.last_refill
        bucket.tokens = min(bucket.capacity, bucket.tokens + elapsed * bucket.rate)
        bucket.last_refill = now

        if bucket.tokens >= 1:
            bucket.tokens -= 1
            remaining = int(bucket.tokens)
            reset_at = int(now + (bucket.capacity - bucket.tokens) / bucket.rate)
            return True, {
                "X-RateLimit-Limit": str(bucket.capacity),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_at),
                "X-RateLimit-Policy": config.algorithm.value,
            }
        else:
            retry_after = int((1 - bucket.tokens) / bucket.rate) + 1
            raise RateLimitException(retry_after=retry_after, limit=bucket.capacity)

    def _sliding_window_memory(
        self,
        key: str,
        now: float,
        config: RateLimitConfig,
    ) -> tuple[bool, dict[str, int | str]]:
        """Sliding window algorithm in memory."""
        window = self._windows[key]
        window_size = 1.0

        # Remove expired entries
        cutoff = now - window_size
        self._windows[key] = [t for t in window if t > cutoff]

        if len(self._windows[key]) < config.requests_per_second:
            self._windows[key].append(now)
            remaining = int(config.requests_per_second - len(self._windows[key]))
            return True, {
                "X-RateLimit-Limit": str(int(config.requests_per_second)),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(now + window_size)),
                "X-RateLimit-Policy": config.algorithm.value,
            }
        else:
            retry_after = 1
            raise RateLimitException(retry_after=retry_after, limit=int(config.requests_per_second))

    async def get_tier_config(self, tier: str) -> RateLimitConfig:
        """Get rate limit config for a tier."""
        return TIER_RATE_LIMITS.get(tier, TIER_RATE_LIMITS["free"])

    def get_endpoint_config(self, method: str, path: str) -> RateLimitConfig | None:
        """Get rate limit config for an endpoint."""
        key = f"{method} {path}"
        return ENDPOINT_RATE_LIMITS.get(key)


# Singleton instance
rate_limiter = InMemoryRateLimiter()


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""

    async def __call__(self, request: Request, call_next):
        """Process rate limiting for a request."""
        # Skip rate limiting for health checks and metrics
        if request.url.path in ("/health", "/ready", "/metrics"):
            return await call_next(request)

        try:
            # Get authenticated context for tenant-based limiting
            auth_context = None
            try:
                from app.middleware.auth import get_current_auth
                auth_context = await get_current_auth(request)
            except Exception:
                pass

            # Determine rate limit config
            config = rate_limiter.get_endpoint_config(request.method, request.url.path)
            if config is None:
                config = RateLimitConfig(
                    algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                    requests_per_second=settings.RATE_LIMIT_DEFAULT_RPS,
                    burst_size=settings.RATE_LIMIT_DEFAULT_BURST,
                )

            # Use tenant_id or IP as identifier
            identifier = auth_context.tenant_id if auth_context else request.client.host

            allowed, headers = await rate_limiter.is_allowed(
                identifier, f"{request.method} {request.url.path}", config
            )

            response = await call_next(request)

            # Add rate limit headers
            for key, value in headers.items():
                response.headers[key] = str(value)

            return response

        except RateLimitException as e:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": e.message,
                        "details": {
                            "limit": e.limit,
                            "remaining": 0,
                            "retry_after_seconds": e.retry_after,
                        },
                    }
                },
                headers={
                    "Retry-After": str(e.retry_after),
                    "X-RateLimit-Limit": str(e.limit),
                    "X-RateLimit-Remaining": "0",
                },
            )


async def rate_limit_dependency(
    request: Request,
    auth: Annotated[AuthContext, Depends(get_current_auth)],
) -> AuthContext:
    """Dependency for route-level rate limiting."""
    config = rate_limiter.get_endpoint_config(request.method, request.url.path)
    if config is None:
        config = RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            requests_per_second=settings.RATE_LIMIT_DEFAULT_RPS,
            burst_size=settings.RATE_LIMIT_DEFAULT_BURST,
        )

    identifier = auth.tenant_id
    await rate_limiter.is_allowed(identifier, f"{request.method} {request.url.path}", config)
    return auth

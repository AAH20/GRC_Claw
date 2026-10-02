"""
Rate limiting middleware for FastAPI/Starlette applications.

Provides both middleware and dependency-based rate limiting with support for
multiple algorithms, tier-based limits, and endpoint-specific policies.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .algorithms import RateLimiter, create_limiter
from .config import DEFAULT_ENDPOINT_LIMITS, DEFAULT_TIERS, RateLimitConfig
from .exceptions import RateLimitExceeded
from .models import RateLimitAlgorithm, RateLimitStatus

logger = logging.getLogger(__name__)


@dataclass
class RateLimitContext:
    """Context for rate limit evaluation."""
    identifier: str
    tenant_id: str | None = None
    tier: str = "free"
    endpoint: str = ""
    method: str = "GET"
    path: str = ""
    api_key: str | None = None
    user_id: str | None = None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI/Starlette middleware for rate limiting.

    Automatically applies rate limits based on:
    1. Endpoint-specific policies
    2. Tier-based limits (free, starter, professional, enterprise)
    3. Global rate limits
    4. Custom policies

    Adds standard rate limit headers to all responses:
    - X-RateLimit-Limit
    - X-RateLimit-Remaining
    - X-RateLimit-Reset
    - X-RateLimit-Policy
    """

    def __init__(
        self,
        app,
        config: RateLimitConfig | None = None,
        limiter: RateLimiter | None = None,
        get_tier: Callable[[Request], str] | None = None,
        get_identifier: Callable[[Request], str] | None = None,
        skip_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.limiter = limiter or create_limiter(
            algorithm=self.config.algorithm,
            requests_per_second=self.config.requests_per_second,
            burst_size=self.config.burst_size,
            window_size=self.config.window_size,
        )
        self.get_tier = get_tier or self._default_get_tier
        self.get_identifier = get_identifier or self._default_get_identifier
        self.skip_paths = set(skip_paths or self.config.skip_paths)

    @staticmethod
    def _default_get_tier(request: Request) -> str:
        """Extract tier from request headers or default to free."""
        return request.headers.get("X-Tier", "free")

    @staticmethod
    def _default_get_identifier(request: Request) -> str:
        """Extract identifier from request (API key, auth, or IP)."""
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key}"

        # Try authorization header
        auth = request.headers.get("Authorization")
        if auth:
            return f"auth:{auth[:20]}"

        # Fall back to IP
        client = request.client
        if client:
            return f"ip:{client.host}"

        return "unknown"

    def _should_skip(self, request: Request) -> bool:
        """Check if rate limiting should be skipped for this request."""
        path = request.url.path
        return path in self.skip_paths

    def _get_endpoint_config(self, method: str, path: str) -> RateLimitConfig | None:
        """Get endpoint-specific rate limit configuration."""
        key = f"{method} {path}"
        endpoint_conf = DEFAULT_ENDPOINT_LIMITS.get(key)
        if endpoint_conf:
            return RateLimitConfig(
                algorithm=RateLimitAlgorithm(endpoint_conf.get("algorithm", "token_bucket")),
                requests_per_second=endpoint_conf.get("requests_per_second", 100),
                burst_size=endpoint_conf.get("burst_size", 200),
            )
        return None

    def _get_tier_config(self, tier: str) -> RateLimitConfig:
        """Get rate limit configuration for a tier."""
        tier_config = DEFAULT_TIERS.get(tier)
        if tier_config:
            return tier_config.rate_limit
        return RateLimitConfig()

    def _build_key(self, context: RateLimitContext) -> str:
        """Build the rate limit key for the given context."""
        parts = [self.config.key_prefix, context.identifier]
        if context.endpoint:
            parts.append(context.endpoint)
        return ":".join(parts)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process rate limiting for the request."""
        if self._should_skip(request):
            return await call_next(request)

        try:
            # Build rate limit context
            identifier = self.get_identifier(request)
            tier = self.get_tier(request)
            endpoint = f"{request.method} {request.url.path}"

            context = RateLimitContext(
                identifier=identifier,
                tier=tier,
                endpoint=endpoint,
                method=request.method,
                path=request.url.path,
            )

            # Determine which config to use (endpoint-specific > tier > default)
            config = self._get_endpoint_config(request.method, request.url.path)
            if config is None:
                config = self._get_tier_config(tier)

            # Check rate limit
            key = self._build_key(context)
            result = self.limiter.acquire(key)

            # Process the request
            response = await call_next(request)

            # Add rate limit headers
            if self.config.enable_headers:
                response.headers["X-RateLimit-Limit"] = str(result.limit)
                response.headers["X-RateLimit-Remaining"] = str(result.remaining)
                response.headers["X-RateLimit-Reset"] = str(result.reset_at)
                response.headers["X-RateLimit-Policy"] = result.algorithm.value

            # If not allowed, return 429
            if not result.allowed:
                raise RateLimitExceeded(
                    retry_after=result.retry_after or 1,
                    limit=result.limit,
                    remaining=0,
                    policy_name=result.algorithm.value,
                )

            return response

        except RateLimitExceeded as e:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "identifier": identifier,
                    "endpoint": request.url.path,
                    "retry_after": e.retry_after,
                },
            )
            return JSONResponse(
                status_code=429,
                content=e.to_dict(),
                headers={
                    "Retry-After": str(e.retry_after),
                    "X-RateLimit-Limit": str(e.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + e.retry_after),
                },
            )
        except Exception as e:
            logger.error(f"Rate limiting error: {e}", exc_info=True)
            # Fail open - allow the request if rate limiting fails
            return await call_next(request)


async def rate_limit_dependency(
    request: Request,
    identifier: str | None = None,
    tier: str = "free",
    endpoint: str | None = None,
) -> RateLimitStatus:
    """
    FastAPI dependency for route-level rate limiting.

    Usage:
        @app.get("/endpoint")
        async def my_endpoint(
            rate: RateLimitStatus = Depends(rate_limit_dependency)
        ):
            ...
    """
    config = RateLimitConfig()
    limiter = create_limiter(
        algorithm=config.algorithm,
        requests_per_second=config.requests_per_second,
        burst_size=config.burst_size,
    )

    if identifier is None:
        identifier = request.headers.get("X-API-Key", request.client.host if request.client else "unknown")

    ep = endpoint or f"{request.method} {request.url.path}"
    key = f"{config.key_prefix}:{identifier}:{ep}"

    result = limiter.acquire(key)

    if not result.allowed:
        raise RateLimitExceeded(
            retry_after=result.retry_after or 1,
            limit=result.limit,
            remaining=0,
            policy_name=result.algorithm.value,
        )

    return RateLimitStatus(
        identifier=identifier,
        endpoint=ep,
        limit=result.limit,
        remaining=result.remaining,
        reset_at=result.reset_at,
        window=config.window_size,
        algorithm=result.algorithm,
        allowed=True,
        tier=tier,
    )

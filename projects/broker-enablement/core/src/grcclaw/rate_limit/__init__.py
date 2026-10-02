"""
GRC_Claw Rate Limiting & Quota Management System

Comprehensive rate limiting, quota enforcement, usage tracking, and billing
integration for the GRC_Claw API platform.
"""

from .algorithms import (
    RateLimiter,
    TokenBucketLimiter,
    SlidingWindowLimiter,
    LeakyBucketLimiter,
    FixedWindowLimiter,
    RateLimitResult,
)
from .middleware import RateLimitMiddleware, rate_limit_dependency
from .quota_engine import QuotaEngine, QuotaCheckResult
from .usage_tracker import UsageTracker
from .billing_hooks import BillingHookManager
from .config import RateLimitConfig, QuotaConfig, TierConfig
from .exceptions import (
    RateLimitExceeded,
    QuotaExceeded,
    QuotaNotFoundError,
    RateLimitConfigError,
)
from .models import (
    RateLimitStatus,
    QuotaStatus,
    UsageRecord,
    QuotaUsage,
    RateLimitPolicy,
)

__all__ = [
    # Algorithms
    "RateLimiter",
    "TokenBucketLimiter",
    "SlidingWindowLimiter",
    "LeakyBucketLimiter",
    "FixedWindowLimiter",
    "RateLimitResult",
    # Middleware
    "RateLimitMiddleware",
    "rate_limit_dependency",
    # Quota
    "QuotaEngine",
    "QuotaCheckResult",
    # Usage
    "UsageTracker",
    # Billing
    "BillingHookManager",
    # Config
    "RateLimitConfig",
    "QuotaConfig",
    "TierConfig",
    # Exceptions
    "RateLimitExceeded",
    "QuotaExceeded",
    "QuotaNotFoundError",
    "RateLimitConfigError",
    # Models
    "RateLimitStatus",
    "QuotaStatus",
    "UsageRecord",
    "QuotaUsage",
    "RateLimitPolicy",
]

"""
GRC_Claw Rate Limiting & Quota Management System

Comprehensive rate limiting, quota enforcement, usage tracking, and billing
integration for the GRC_Claw API platform.
"""

from .algorithms import (
    FixedWindowLimiter,
    LeakyBucketLimiter,
    RateLimiter,
    RateLimitResult,
    SlidingWindowLimiter,
    TokenBucketLimiter,
)
from .billing_hooks import BillingHookManager
from .config import QuotaConfig, RateLimitConfig, TierConfig
from .exceptions import (
    QuotaExceeded,
    QuotaNotFoundError,
    RateLimitConfigError,
    RateLimitExceeded,
)
from .middleware import RateLimitMiddleware, rate_limit_dependency
from .models import (
    QuotaStatus,
    QuotaUsage,
    RateLimitPolicy,
    RateLimitStatus,
    UsageRecord,
)
from .quota_engine import QuotaCheckResult, QuotaEngine
from .usage_tracker import UsageTracker

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

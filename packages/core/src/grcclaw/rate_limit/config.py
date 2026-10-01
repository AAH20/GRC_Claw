"""
Configuration classes for rate limiting and quota management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from .models import RateLimitAlgorithm, QuotaPeriod, QuotaType


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    requests_per_second: float = 100.0
    burst_size: int = 200
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    window_size: int = 60  # seconds
    key_prefix: str = "ratelimit"
    skip_paths: list[str] = field(default_factory=lambda: ["/health", "/ready", "/metrics"])
    enable_headers: bool = True
    enable_redis: bool = True
    redis_url: str = "redis://localhost:6379/0"
    redis_key_ttl: int = 3600
    default_tier: str = "free"
    enforce_global_limit: bool = True
    global_rps: float = 10000.0
    global_burst: int = 20000


@dataclass
class QuotaConfig:
    """Configuration for quota management."""
    default_period: QuotaPeriod = QuotaPeriod.MONTHLY
    enforce_quotas: bool = True
    allow_overage: bool = False
    overage_multiplier: float = 1.5
    warning_threshold: float = 0.8  # 80%
    critical_threshold: float = 0.95  # 95%
    track_usage: bool = True
    usage_retention_days: int = 90
    auto_reset: bool = True
    reset_hour_utc: int = 0
    notify_on_threshold: bool = True
    notify_channels: list[str] = field(default_factory=lambda: ["webhook", "email"])


@dataclass
class TierConfig:
    """Configuration for a service tier."""
    name: str
    display_name: str = ""
    description: str = ""
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    quotas: dict[str, dict] = field(default_factory=dict)
    # quotas format: {"api_calls": {"limit": 100000, "period": "monthly"}, ...}
    features: list[str] = field(default_factory=list)
    price_monthly: float = 0.0
    is_active: bool = True
    metadata: dict = field(default_factory=dict)


# Default tier configurations
DEFAULT_TIERS: dict[str, TierConfig] = {
    "free": TierConfig(
        name="free",
        display_name="Free Tier",
        description="Free tier with basic rate limits",
        rate_limit=RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            requests_per_second=10.0,
            burst_size=20,
            daily_limit=10000,
        ),
        quotas={
            "api_calls": {"limit": 10000, "period": "daily"},
            "storage_gb": {"limit": 1.0, "period": "monthly"},
            "agents": {"limit": 3, "period": "never"},
        },
        features=["basic_policies", "community_support"],
        price_monthly=0.0,
    ),
    "starter": TierConfig(
        name="starter",
        display_name="Starter Tier",
        description="Starter tier for small teams",
        rate_limit=RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            requests_per_second=50.0,
            burst_size=100,
            daily_limit=100000,
        ),
        quotas={
            "api_calls": {"limit": 100000, "period": "daily"},
            "storage_gb": {"limit": 10.0, "period": "monthly"},
            "agents": {"limit": 10, "period": "never"},
            "reports": {"limit": 100, "period": "monthly"},
        },
        features=["basic_policies", "email_support", "custom_frameworks"],
        price_monthly=49.0,
    ),
    "professional": TierConfig(
        name="professional",
        display_name="Professional Tier",
        description="Professional tier for growing organizations",
        rate_limit=RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            requests_per_second=200.0,
            burst_size=500,
            daily_limit=1000000,
        ),
        quotas={
            "api_calls": {"limit": 1000000, "period": "daily"},
            "storage_gb": {"limit": 100.0, "period": "monthly"},
            "agents": {"limit": 50, "period": "never"},
            "reports": {"limit": 1000, "period": "monthly"},
            "frameworks": {"limit": 25, "period": "never"},
        },
        features=["advanced_policies", "priority_support", "custom_frameworks", "audit_logs"],
        price_monthly=199.0,
    ),
    "enterprise": TierConfig(
        name="enterprise",
        display_name="Enterprise Tier",
        description="Enterprise tier with custom limits",
        rate_limit=RateLimitConfig(
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            requests_per_second=1000.0,
            burst_size=2000,
            daily_limit=10000000,
        ),
        quotas={
            "api_calls": {"limit": 10000000, "period": "daily"},
            "storage_gb": {"limit": 1000.0, "period": "monthly"},
            "agents": {"limit": 500, "period": "never"},
            "reports": {"limit": 10000, "period": "monthly"},
            "frameworks": {"limit": 100, "period": "never"},
        },
        features=["all_policies", "dedicated_support", "custom_frameworks", "audit_logs", "sla"],
        price_monthly=999.0,
    ),
}


# Default endpoint-specific rate limits
DEFAULT_ENDPOINT_LIMITS: dict[str, dict] = {
    "POST /v1.0/enforcement/decide": {
        "algorithm": "token_bucket",
        "requests_per_second": 10000,
        "burst_size": 2000,
    },
    "POST /v1.0/enforcement/decide-batch": {
        "algorithm": "token_bucket",
        "requests_per_second": 1000,
        "burst_size": 200,
    },
    "GET /v1.0/policies": {
        "algorithm": "token_bucket",
        "requests_per_second": 1000,
        "burst_size": 200,
    },
    "POST /v1.0/policies": {
        "algorithm": "token_bucket",
        "requests_per_second": 100,
        "burst_size": 20,
    },
    "POST /v1.0/evidence": {
        "algorithm": "token_bucket",
        "requests_per_second": 5000,
        "burst_size": 500,
    },
    "GET /v1.0/audit": {
        "algorithm": "token_bucket",
        "requests_per_second": 500,
        "burst_size": 50,
    },
    "POST /v1.0/compliance/reports": {
        "algorithm": "token_bucket",
        "requests_per_second": 10,
        "burst_size": 20,
    },
    "POST /v1.0/graphql": {
        "algorithm": "token_bucket",
        "requests_per_second": 1000,
        "burst_size": 200,
    },
}

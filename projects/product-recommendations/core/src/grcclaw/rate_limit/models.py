"""
Data models for rate limiting and quota management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, timezone
import uuid


class RateLimitAlgorithm(str, Enum):
    """Supported rate limiting algorithms."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"


class QuotaPeriod(str, Enum):
    """Quota reset periods."""
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    NEVER = "never"


class QuotaType(str, Enum):
    """Types of quotas."""
    REQUEST_COUNT = "request_count"
    BANDWIDTH = "bandwidth"
    STORAGE = "storage"
    COMPUTE = "compute"
    TOKEN_COUNT = "token_count"
    CUSTOM = "custom"


@dataclass
class RateLimitStatus:
    """Current rate limit status for a client."""
    identifier: str
    endpoint: str
    limit: int
    remaining: int
    reset_at: int
    window: int
    algorithm: RateLimitAlgorithm
    allowed: bool
    retry_after: Optional[int] = None
    policy_name: str = "default"
    tier: str = "free"


@dataclass
class QuotaStatus:
    """Current quota usage status for a tenant."""
    tenant_id: str
    quota_name: str
    quota_type: QuotaType
    period: QuotaPeriod
    limit: float
    used: float
    remaining: float
    reset_at: str
    usage_percentage: float = 0.0
    is_exceeded: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class UsageRecord:
    """A single usage event record."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    identifier: str = ""
    endpoint: str = ""
    method: str = "GET"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    quantity: float = 1.0
    unit: str = "request"
    cost: float = 0.0
    metadata: dict = field(default_factory=dict)
    rate_limited: bool = False
    quota_exceeded: bool = False
    tags: list[str] = field(default_factory=list)


@dataclass
class QuotaUsage:
    """Aggregated quota usage for a tenant."""
    tenant_id: str
    quota_name: str
    period: QuotaPeriod
    total_used: float = 0.0
    total_limit: float = 0.0
    usage_percentage: float = 0.0
    reset_at: str = ""
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    breakdown: dict = field(default_factory=dict)


@dataclass
class RateLimitPolicy:
    """A named rate limit policy."""
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "default"
    description: str = ""
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    requests_per_second: float = 100.0
    burst_size: int = 200
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    endpoints: list[str] = field(default_factory=list)
    tiers: list[str] = field(default_factory=list)
    is_active: bool = True
    priority: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)

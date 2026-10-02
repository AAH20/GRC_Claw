"""
Usage tracking for rate limiting and quota management.

Tracks API usage per tenant, endpoint, and dimension for billing,
analytics, and quota enforcement.
"""

from __future__ import annotations

import time
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from .models import UsageRecord, QuotaUsage, QuotaPeriod
from .config import QuotaConfig

logger = logging.getLogger(__name__)


@dataclass
class UsageSummary:
    """Summary of usage for a tenant over a period."""
    tenant_id: str
    period_start: str
    period_end: str
    total_requests: int = 0
    total_quantity: float = 0.0
    total_cost: float = 0.0
    by_endpoint: dict = field(default_factory=dict)
    by_dimension: dict = field(default_factory=dict)
    by_day: dict = field(default_factory=dict)
    peak_requests_per_second: float = 0.0
    average_requests_per_second: float = 0.0
    rate_limited_count: int = 0
    quota_exceeded_count: int = 0


class UsageTracker:
    """
    Tracks API usage for tenants.

    Maintains in-memory usage records with configurable retention.
    Supports aggregation by endpoint, dimension, and time period.
    """

    def __init__(self, config: Optional[QuotaConfig] = None):
        self.config = config or QuotaConfig()
        self._records: list[UsageRecord] = []
        self._lock = threading.Lock()
        self._retention_days = self.config.usage_retention_days

    def record(
        self,
        tenant_id: str,
        endpoint: str,
        method: str = "GET",
        quantity: float = 1.0,
        unit: str = "request",
        cost: float = 0.0,
        identifier: str = "",
        metadata: Optional[dict] = None,
        rate_limited: bool = False,
        quota_exceeded: bool = False,
        tags: Optional[list[str]] = None,
    ) -> UsageRecord:
        """Record a usage event."""
        record = UsageRecord(
            tenant_id=tenant_id,
            identifier=identifier or tenant_id,
            endpoint=endpoint,
            method=method,
            quantity=quantity,
            unit=unit,
            cost=cost,
            metadata=metadata or {},
            rate_limited=rate_limited,
            quota_exceeded=quota_exceeded,
            tags=tags or [],
        )

        with self._lock:
            self._records.append(record)
            self._cleanup_old_records()

        return record

    def get_usage(
        self,
        tenant_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> list[UsageRecord]:
        """Get usage records for a tenant with optional filters."""
        with self._lock:
            records = [r for r in self._records if r.tenant_id == tenant_id]

        if start_time:
            records = [r for r in records if r.timestamp >= start_time]
        if end_time:
            records = [r for r in records if r.timestamp <= end_time]
        if endpoint:
            records = [r for r in records if r.endpoint == endpoint]

        return records

    def get_summary(
        self,
        tenant_id: str,
        period: QuotaPeriod = QuotaPeriod.DAILY,
    ) -> UsageSummary:
        """Get a usage summary for a tenant over a period."""
        now = datetime.now(timezone.utc)

        if period == QuotaPeriod.HOURLY:
            start = now - timedelta(hours=1)
        elif period == QuotaPeriod.DAILY:
            start = now - timedelta(days=1)
        elif period == QuotaPeriod.WEEKLY:
            start = now - timedelta(weeks=1)
        elif period == QuotaPeriod.MONTHLY:
            start = now - timedelta(days=30)
        else:
            start = now - timedelta(days=1)

        records = self.get_usage(
            tenant_id=tenant_id,
            start_time=start.isoformat(),
            end_time=now.isoformat(),
        )

        by_endpoint: dict[str, int] = defaultdict(int)
        by_dimension: dict[str, float] = defaultdict(float)
        by_day: dict[str, int] = defaultdict(int)
        total_quantity = 0.0
        total_cost = 0.0
        rate_limited_count = 0
        quota_exceeded_count = 0

        for r in records:
            by_endpoint[r.endpoint] += 1
            by_dimension[r.unit] += r.quantity
            day = r.timestamp[:10]  # YYYY-MM-DD
            by_day[day] += 1
            total_quantity += r.quantity
            total_cost += r.cost
            if r.rate_limited:
                rate_limited_count += 1
            if r.quota_exceeded:
                quota_exceeded_count += 1

        duration_seconds = (now - start).total_seconds()
        avg_rps = len(records) / duration_seconds if duration_seconds > 0 else 0.0

        return UsageSummary(
            tenant_id=tenant_id,
            period_start=start.isoformat(),
            period_end=now.isoformat(),
            total_requests=len(records),
            total_quantity=total_quantity,
            total_cost=total_cost,
            by_endpoint=dict(by_endpoint),
            by_dimension=dict(by_dimension),
            by_day=dict(by_day),
            peak_requests_per_second=avg_rps * 2,  # Simplified peak estimate
            average_requests_per_second=avg_rps,
            rate_limited_count=rate_limited_count,
            quota_exceeded_count=quota_exceeded_count,
        )

    def get_current_usage(
        self,
        tenant_id: str,
        quota_name: str,
        period: QuotaPeriod = QuotaPeriod.MONTHLY,
    ) -> QuotaUsage:
        """Get current quota usage for a tenant."""
        now = datetime.now(timezone.utc)

        if period == QuotaPeriod.HOURLY:
            start = now - timedelta(hours=1)
        elif period == QuotaPeriod.DAILY:
            start = now - timedelta(days=1)
        elif period == QuotaPeriod.WEEKLY:
            start = now - timedelta(weeks=1)
        elif period == QuotaPeriod.MONTHLY:
            start = now - timedelta(days=30)
        else:
            start = now - timedelta(days=1)

        records = self.get_usage(
            tenant_id=tenant_id,
            start_time=start.isoformat(),
            end_time=now.isoformat(),
        )

        total_used = sum(r.quantity for r in records)

        return QuotaUsage(
            tenant_id=tenant_id,
            quota_name=quota_name,
            period=period,
            total_used=total_used,
            total_limit=0.0,  # Will be set by quota engine
            usage_percentage=0.0,
            reset_at=(now + timedelta(days=30)).isoformat(),
            last_updated=now.isoformat(),
        )

    def get_rate_limit_hits(
        self,
        tenant_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> list[UsageRecord]:
        """Get rate-limited requests for a tenant."""
        records = self.get_usage(tenant_id, start_time, end_time)
        return [r for r in records if r.rate_limited]

    def get_quota_exceeded(
        self,
        tenant_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> list[UsageRecord]:
        """Get quota-exceeded requests for a tenant."""
        records = self.get_usage(tenant_id, start_time, end_time)
        return [r for r in records if r.quota_exceeded]

    def clear(self, tenant_id: Optional[str] = None) -> None:
        """Clear usage records, optionally for a specific tenant."""
        with self._lock:
            if tenant_id:
                self._records = [r for r in self._records if r.tenant_id != tenant_id]
            else:
                self._records.clear()

    def _cleanup_old_records(self) -> None:
        """Remove records older than the retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self._retention_days)
        cutoff_str = cutoff.isoformat()
        self._records = [r for r in self._records if r.timestamp >= cutoff_str]

"""
Quota management engine for GRC_Claw.

Provides quota tracking, enforcement, and lifecycle management with support
for multiple quota types, periods, and tenant-level granularity.
"""

from __future__ import annotations

import time
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from .config import QuotaConfig, DEFAULT_TIERS
from .exceptions import QuotaExceeded, QuotaNotFoundError
from .models import QuotaPeriod, QuotaType, QuotaStatus, QuotaUsage

logger = logging.getLogger(__name__)


@dataclass
class QuotaCheckResult:
    """Result of a quota check."""
    allowed: bool
    quota_name: str
    limit: float
    used: float
    remaining: float
    reset_at: str
    usage_percentage: float
    is_exceeded: bool
    is_warning: bool
    is_critical: bool
    metadata: dict = field(default_factory=dict)


class QuotaEngine:
    """
    Quota management engine.

    Manages quotas for tenants across different dimensions and periods.
    Supports automatic reset, overage handling, and threshold notifications.
    """

    def __init__(self, config: Optional[QuotaConfig] = None):
        self.config = config or QuotaConfig()
        self._quotas: dict[str, dict] = {}
        self._usage: dict[str, dict] = defaultdict(lambda: defaultdict(float))
        self._last_reset: dict[str, str] = {}
        self._lock = threading.Lock()

    def register_quota(
        self,
        tenant_id: str,
        quota_name: str,
        quota_type: QuotaType = QuotaType.REQUEST_COUNT,
        period: QuotaPeriod = QuotaPeriod.MONTHLY,
        limit: float = 1000.0,
        metadata: Optional[dict] = None,
    ) -> None:
        """Register a new quota for a tenant."""
        key = self._make_key(tenant_id, quota_name)
        with self._lock:
            self._quotas[key] = {
                "tenant_id": tenant_id,
                "quota_name": quota_name,
                "quota_type": quota_type,
                "period": period,
                "limit": limit,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._last_reset[key] = datetime.now(timezone.utc).isoformat()

    def unregister_quota(self, tenant_id: str, quota_name: str) -> None:
        """Remove a quota."""
        key = self._make_key(tenant_id, quota_name)
        with self._lock:
            self._quotas.pop(key, None)
            self._usage.pop(key, None)
            self._last_reset.pop(key, None)

    def check_quota(
        self,
        tenant_id: str,
        quota_name: str,
        requested: float = 1.0,
    ) -> QuotaCheckResult:
        """
        Check if a request is within quota.

        Returns a QuotaCheckResult indicating whether the request is allowed
        and the current quota status.
        """
        key = self._make_key(tenant_id, quota_name)

        with self._lock:
            quota = self._quotas.get(key)
            if quota is None:
                raise QuotaNotFoundError(quota_name, tenant_id)

            # Check if quota needs reset
            self._maybe_reset(key, quota)

            used = self._usage[key]["current"]
            limit = quota["limit"]
            remaining = max(0.0, limit - used)
            usage_pct = (used / limit * 100) if limit > 0 else 0.0

            is_exceeded = used + requested > limit
            is_warning = usage_pct >= (self.config.warning_threshold * 100)
            is_critical = usage_pct >= (self.config.critical_threshold * 100)

            reset_at = self._calculate_reset_at(quota["period"])

            return QuotaCheckResult(
                allowed=not is_exceeded or self.config.allow_overage,
                quota_name=quota_name,
                limit=limit,
                used=used,
                remaining=remaining,
                reset_at=reset_at,
                usage_percentage=usage_pct,
                is_exceeded=is_exceeded,
                is_warning=is_warning,
                is_critical=is_critical,
                metadata=quota.get("metadata", {}),
            )

    def consume_quota(
        self,
        tenant_id: str,
        quota_name: str,
        quantity: float = 1.0,
    ) -> QuotaCheckResult:
        """
        Consume quota for a tenant.

        This checks the quota and if allowed, increments the usage counter.
        """
        result = self.check_quota(tenant_id, quota_name, quantity)

        if result.allowed:
            key = self._make_key(tenant_id, quota_name)
            with self._lock:
                self._usage[key]["current"] += quantity
                self._usage[key]["last_updated"] = datetime.now(timezone.utc).isoformat()

        return result

    def get_quota_status(self, tenant_id: str, quota_name: str) -> QuotaStatus:
        """Get current quota status without consuming."""
        key = self._make_key(tenant_id, quota_name)

        with self._lock:
            quota = self._quotas.get(key)
            if quota is None:
                raise QuotaNotFoundError(quota_name, tenant_id)

            self._maybe_reset(key, quota)

            used = self._usage[key]["current"]
            limit = quota["limit"]
            remaining = max(0.0, limit - used)
            usage_pct = (used / limit * 100) if limit > 0 else 0.0
            reset_at = self._calculate_reset_at(quota["period"])

            return QuotaStatus(
                tenant_id=tenant_id,
                quota_name=quota_name,
                quota_type=quota["quota_type"],
                period=quota["period"],
                limit=limit,
                used=used,
                remaining=remaining,
                reset_at=reset_at,
                usage_percentage=usage_pct,
                is_exceeded=used >= limit,
                metadata=quota.get("metadata", {}),
            )

    def get_all_quotas(self, tenant_id: str) -> list[QuotaStatus]:
        """Get all quota statuses for a tenant."""
        results = []
        with self._lock:
            for key, quota in self._quotas.items():
                if quota["tenant_id"] == tenant_id:
                    try:
                        status = self.get_quota_status(tenant_id, quota["quota_name"])
                        results.append(status)
                    except QuotaNotFoundError:
                        continue
        return results

    def reset_quota(self, tenant_id: str, quota_name: str) -> None:
        """Manually reset a quota."""
        key = self._make_key(tenant_id, quota_name)
        with self._lock:
            if key in self._usage:
                self._usage[key]["current"] = 0.0
                self._last_reset[key] = datetime.now(timezone.utc).isoformat()

    def reset_all_quotas(self, tenant_id: str) -> None:
        """Reset all quotas for a tenant."""
        with self._lock:
            for key in list(self._usage.keys()):
                if key.startswith(f"{tenant_id}:"):
                    self._usage[key]["current"] = 0.0
                    self._last_reset[key] = datetime.now(timezone.utc).isoformat()

    def update_quota_limit(
        self,
        tenant_id: str,
        quota_name: str,
        new_limit: float,
    ) -> None:
        """Update the limit for an existing quota."""
        key = self._make_key(tenant_id, quota_name)
        with self._lock:
            if key not in self._quotas:
                raise QuotaNotFoundError(quota_name, tenant_id)
            self._quotas[key]["limit"] = new_limit

    def setup_tier_quotas(self, tenant_id: str, tier: str) -> None:
        """Set up default quotas for a tenant based on their tier."""
        tier_config = DEFAULT_TIERS.get(tier)
        if tier_config is None:
            logger.warning(f"Unknown tier: {tier}")
            return

        for quota_name, quota_conf in tier_config.quotas.items():
            self.register_quota(
                tenant_id=tenant_id,
                quota_name=quota_name,
                quota_type=QuotaType.CUSTOM,
                period=QuotaPeriod(quota_conf.get("period", "monthly")),
                limit=quota_conf.get("limit", 1000),
                metadata={"tier": tier, "auto_configured": True},
            )

    def _make_key(self, tenant_id: str, quota_name: str) -> str:
        """Create a unique key for a tenant quota."""
        return f"{tenant_id}:{quota_name}"

    def _maybe_reset(self, key: str, quota: dict) -> None:
        """Check and perform quota reset if needed."""
        if not self.config.auto_reset:
            return

        period = quota["period"]
        if period == QuotaPeriod.NEVER:
            return

        last_reset = self._last_reset.get(key)
        if last_reset is None:
            self._last_reset[key] = datetime.now(timezone.utc).isoformat()
            return

        last_reset_dt = datetime.fromisoformat(last_reset)
        now = datetime.now(timezone.utc)

        should_reset = False
        if period == QuotaPeriod.MINUTELY:
            should_reset = (now - last_reset_dt) >= timedelta(minutes=1)
        elif period == QuotaPeriod.HOURLY:
            should_reset = (now - last_reset_dt) >= timedelta(hours=1)
        elif period == QuotaPeriod.DAILY:
            should_reset = (now - last_reset_dt) >= timedelta(days=1)
        elif period == QuotaPeriod.WEEKLY:
            should_reset = (now - last_reset_dt) >= timedelta(weeks=1)
        elif period == QuotaPeriod.MONTHLY:
            should_reset = (now - last_reset_dt) >= timedelta(days=30)
        elif period == QuotaPeriod.YEARLY:
            should_reset = (now - last_reset_dt) >= timedelta(days=365)

        if should_reset:
            self._usage[key]["current"] = 0.0
            self._last_reset[key] = now.isoformat()

    def _calculate_reset_at(self, period: QuotaPeriod) -> str:
        """Calculate the next reset time for a period."""
        now = datetime.now(timezone.utc)

        if period == QuotaPeriod.MINUTELY:
            reset = now + timedelta(minutes=1)
        elif period == QuotaPeriod.HOURLY:
            reset = now + timedelta(hours=1)
        elif period == QuotaPeriod.DAILY:
            reset = now + timedelta(days=1)
        elif period == QuotaPeriod.WEEKLY:
            reset = now + timedelta(weeks=1)
        elif period == QuotaPeriod.MONTHLY:
            reset = now + timedelta(days=30)
        elif period == QuotaPeriod.YEARLY:
            reset = now + timedelta(days=365)
        else:
            reset = now

        return reset.isoformat()

"""
Billing integration hooks for rate limiting and quota management.

Provides hooks for integrating with the GRC_Claw billing system,
including usage-based billing, overage charges, and invoice generation.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable
from datetime import datetime, timezone

from .models import UsageRecord, QuotaUsage, QuotaPeriod
from .config import QuotaConfig

logger = logging.getLogger(__name__)


@dataclass
class BillingEvent:
    """A billing event triggered by rate limiting or quota management."""
    event_id: str = field(default_factory=lambda: f"evt_{datetime.now(timezone.utc).timestamp()}")
    event_type: str = ""  # "rate_limit_exceeded", "quota_exceeded", "quota_warning", "overage"
    tenant_id: str = ""
    quota_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    quantity: float = 0.0
    unit: str = "request"
    cost: float = 0.0
    metadata: dict = field(default_factory=dict)
    processed: bool = False


@dataclass
class OverageCharge:
    """An overage charge for exceeding quota."""
    charge_id: str = field(default_factory=lambda: f"chg_{datetime.now(timezone.utc).timestamp()}")
    tenant_id: str = ""
    quota_name: str = ""
    overage_quantity: float = 0.0
    unit: str = "request"
    unit_price: float = 0.0
    total_cost: float = 0.0
    period: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    billed: bool = False


class BillingHook(ABC):
    """Abstract base class for billing hooks."""

    @abstractmethod
    async def on_rate_limit_exceeded(self, event: BillingEvent) -> None:
        """Called when a rate limit is exceeded."""
        pass

    @abstractmethod
    async def on_quota_exceeded(self, event: BillingEvent) -> None:
        """Called when a quota is exceeded."""
        pass

    @abstractmethod
    async def on_quota_warning(self, event: BillingEvent) -> None:
        """Called when a quota warning threshold is reached."""
        pass

    @abstractmethod
    async def on_overage(self, charge: OverageCharge) -> None:
        """Called when an overage charge is generated."""
        pass


class LoggingBillingHook(BillingHook):
    """Billing hook that logs events."""

    async def on_rate_limit_exceeded(self, event: BillingEvent) -> None:
        logger.warning(
            "Rate limit exceeded",
            extra={
                "tenant_id": event.tenant_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
            },
        )

    async def on_quota_exceeded(self, event: BillingEvent) -> None:
        logger.warning(
            "Quota exceeded",
            extra={
                "tenant_id": event.tenant_id,
                "quota_name": event.quota_name,
                "timestamp": event.timestamp,
            },
        )

    async def on_quota_warning(self, event: BillingEvent) -> None:
        logger.info(
            "Quota warning",
            extra={
                "tenant_id": event.tenant_id,
                "quota_name": event.quota_name,
                "usage_percentage": event.metadata.get("usage_percentage", 0),
            },
        )

    async def on_overage(self, charge: OverageCharge) -> None:
        logger.info(
            "Overage charge generated",
            extra={
                "tenant_id": charge.tenant_id,
                "quota_name": charge.quota_name,
                "total_cost": charge.total_cost,
            },
        )


class WebhookBillingHook(BillingHook):
    """Billing hook that sends events to a webhook."""

    def __init__(self, webhook_url: str, headers: Optional[dict] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}

    async def on_rate_limit_exceeded(self, event: BillingEvent) -> None:
        await self._send_webhook("rate_limit_exceeded", event)

    async def on_quota_exceeded(self, event: BillingEvent) -> None:
        await self._send_webhook("quota_exceeded", event)

    async def on_quota_warning(self, event: BillingEvent) -> None:
        await self._send_webhook("quota_warning", event)

    async def on_overage(self, charge: OverageCharge) -> None:
        await self._send_webhook("overage", charge)

    async def _send_webhook(self, event_type: str, data) -> None:
        """Send event to webhook."""
        import aiohttp

        payload = {
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data.__dict__ if hasattr(data, "__dict__") else str(data),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                ) as response:
                    if response.status >= 400:
                        logger.error(
                            f"Webhook billing hook failed: {response.status}",
                            extra={"event_type": event_type},
                        )
        except Exception as e:
            logger.error(f"Webhook billing hook error: {e}", exc_info=True)


class BillingHookManager:
    """
    Manages billing hooks for rate limiting and quota events.

    Dispatches events to registered hooks and manages overage charges.
    """

    def __init__(self, config: Optional[QuotaConfig] = None):
        self.config = config or QuotaConfig()
        self._hooks: list[BillingHook] = []
        self._overage_charges: list[OverageCharge] = []
        self._overage_pricing: dict[str, float] = {}

    def register_hook(self, hook: BillingHook) -> None:
        """Register a billing hook."""
        self._hooks.append(hook)

    def unregister_hook(self, hook: BillingHook) -> None:
        """Unregister a billing hook."""
        if hook in self._hooks:
            self._hooks.remove(hook)

    def set_overage_pricing(self, quota_name: str, unit_price: float) -> None:
        """Set the overage unit price for a quota."""
        self._overage_pricing[quota_name] = unit_price

    async def notify_rate_limit_exceeded(
        self,
        tenant_id: str,
        endpoint: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Notify hooks of a rate limit exceeded event."""
        event = BillingEvent(
            event_type="rate_limit_exceeded",
            tenant_id=tenant_id,
            metadata=metadata or {},
        )
        await self._dispatch("on_rate_limit_exceeded", event)

    async def notify_quota_exceeded(
        self,
        tenant_id: str,
        quota_name: str,
        used: float,
        limit: float,
        metadata: Optional[dict] = None,
    ) -> None:
        """Notify hooks of a quota exceeded event."""
        event = BillingEvent(
            event_type="quota_exceeded",
            tenant_id=tenant_id,
            quota_name=quota_name,
            metadata=metadata or {},
        )
        await self._dispatch("on_quota_exceeded", event)

        # Generate overage charge if pricing is configured
        if quota_name in self._overage_pricing:
            overage = used - limit
            if overage > 0:
                charge = OverageCharge(
                    tenant_id=tenant_id,
                    quota_name=quota_name,
                    overage_quantity=overage,
                    unit_price=self._overage_pricing[quota_name],
                    total_cost=overage * self._overage_pricing[quota_name],
                )
                self._overage_charges.append(charge)
                await self._dispatch("on_overage", charge)

    async def notify_quota_warning(
        self,
        tenant_id: str,
        quota_name: str,
        usage_percentage: float,
        metadata: Optional[dict] = None,
    ) -> None:
        """Notify hooks of a quota warning event."""
        event = BillingEvent(
            event_type="quota_warning",
            tenant_id=tenant_id,
            quota_name=quota_name,
            metadata={**(metadata or {}), "usage_percentage": usage_percentage},
        )
        await self._dispatch("on_quota_warning", event)

    async def notify_quota_critical(
        self,
        tenant_id: str,
        quota_name: str,
        usage_percentage: float,
        metadata: Optional[dict] = None,
    ) -> None:
        """Notify hooks of a quota critical event."""
        event = BillingEvent(
            event_type="quota_critical",
            tenant_id=tenant_id,
            quota_name=quota_name,
            metadata={**(metadata or {}), "usage_percentage": usage_percentage},
        )
        await self._dispatch("on_quota_warning", event)

    def get_overage_charges(
        self,
        tenant_id: Optional[str] = None,
        billed: Optional[bool] = None,
    ) -> list[OverageCharge]:
        """Get overage charges with optional filters."""
        charges = self._overage_charges
        if tenant_id:
            charges = [c for c in charges if c.tenant_id == tenant_id]
        if billed is not None:
            charges = [c for c in charges if c.billed == billed]
        return charges

    def mark_charge_billed(self, charge_id: str) -> None:
        """Mark an overage charge as billed."""
        for charge in self._overage_charges:
            if charge.charge_id == charge_id:
                charge.billed = True
                break

    async def _dispatch(self, method_name: str, data) -> None:
        """Dispatch an event to all registered hooks."""
        for hook in self._hooks:
            try:
                method = getattr(hook, method_name)
                await method(data)
            except Exception as e:
                logger.error(
                    f"Billing hook error in {method_name}: {e}",
                    exc_info=True,
                )

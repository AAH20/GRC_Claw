"""Subscription Agent for creator monetization."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class SubscriptionMetrics(BaseModel):
    """Subscription metrics for a creator."""

    total_subscribers: int = Field(default=0, ge=0)
    active_subscribers: int = Field(default=0, ge=0)
    churned_subscribers: int = Field(default=0, ge=0)
    monthly_recurring_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    average_revenue_per_user: Decimal = Field(default=Decimal("0"), ge=0)
    churn_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class SubscriptionAgent:
    """Agent responsible for managing creator subscriptions.

    Handles subscription lifecycle, metrics tracking,
    and churn analysis for creator monetization.
    """

    def __init__(self) -> None:
        """Initialize the subscription agent."""
        self._subscriptions: dict[str, dict[str, Any]] = {}
        self._counter = 0

    async def create_subscription(
        self,
        creator_id: str,
        subscriber_id: str,
        tier_id: str,
        amount: Decimal,
        currency: str = "USD",
        auto_renew: bool = True,
    ) -> dict[str, Any]:
        """Create a new subscription.

        Args:
            creator_id: Creator identifier.
            subscriber_id: Subscriber identifier.
            tier_id: Tier identifier.
            amount: Subscription amount.
            currency: Currency code.
            auto_renew: Whether subscription auto-renews.

        Returns:
            Created subscription data.

        Raises:
            ValueError: If amount is non-positive.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self._counter += 1
        sub_id = f"sub_{self._counter:06d}"
        now = datetime.now(UTC)

        subscription = {
            "subscription_id": sub_id,
            "creator_id": creator_id,
            "subscriber_id": subscriber_id,
            "tier_id": tier_id,
            "status": "active",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=30)).isoformat(),
            "auto_renew": auto_renew,
            "amount": str(amount),
            "currency": currency,
            "created_at": now.isoformat(),
        }

        self._subscriptions[sub_id] = subscription
        logger.info("Subscription created", subscription_id=sub_id, creator_id=creator_id)
        return subscription

    async def cancel_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Cancel a subscription.

        Args:
            subscription_id: Subscription identifier.

        Returns:
            Updated subscription data.

        Raises:
            ValueError: If subscription not found.
        """
        if subscription_id not in self._subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")

        sub = self._subscriptions[subscription_id]
        sub["status"] = "cancelled"
        sub["cancelled_at"] = datetime.now(UTC).isoformat()
        sub["auto_renew"] = False

        logger.info("Subscription cancelled", subscription_id=subscription_id)
        return sub

    async def renew_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Renew a subscription.

        Args:
            subscription_id: Subscription identifier.

        Returns:
            Updated subscription data.

        Raises:
            ValueError: If subscription not found.
        """
        if subscription_id not in self._subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")

        sub = self._subscriptions[subscription_id]
        current_end = datetime.fromisoformat(sub["end_date"])
        sub["end_date"] = (current_end + timedelta(days=30)).isoformat()
        sub["status"] = "active"
        sub["last_renewed_at"] = datetime.now(UTC).isoformat()

        logger.info("Subscription renewed", subscription_id=subscription_id)
        return sub

    def get_subscription(self, subscription_id: str) -> dict[str, Any] | None:
        """Get a subscription by ID.

        Args:
            subscription_id: Subscription identifier.

        Returns:
            Subscription data or None.
        """
        return self._subscriptions.get(subscription_id)

    def list_subscriptions(
        self,
        creator_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List subscriptions with optional filtering.

        Args:
            creator_id: Filter by creator.
            status: Filter by status.

        Returns:
            List of subscription data.
        """
        results = list(self._subscriptions.values())
        if creator_id:
            results = [s for s in results if s["creator_id"] == creator_id]
        if status:
            results = [s for s in results if s["status"] == status]
        return results

    def get_metrics(self, creator_id: str) -> SubscriptionMetrics:
        """Get subscription metrics for a creator.

        Args:
            creator_id: Creator identifier.

        Returns:
            Subscription metrics.
        """
        creator_subs = [s for s in self._subscriptions.values() if s["creator_id"] == creator_id]
        active = [s for s in creator_subs if s["status"] == "active"]
        cancelled = [s for s in creator_subs if s["status"] == "cancelled"]

        mrr = sum(Decimal(s["amount"]) for s in active)
        total = len(creator_subs)
        churn_rate = len(cancelled) / total if total > 0 else 0.0
        arpu = mrr / len(active) if active else Decimal("0")

        return SubscriptionMetrics(
            total_subscribers=total,
            active_subscribers=len(active),
            churned_subscribers=len(cancelled),
            monthly_recurring_revenue=mrr,
            average_revenue_per_user=arpu,
            churn_rate=churn_rate,
        )

    def get_churn_risk(self, creator_id: str) -> dict[str, Any]:
        """Get churn risk assessment for a creator.

        Args:
            creator_id: Creator identifier.

        Returns:
            Churn risk data.
        """
        metrics = self.get_metrics(creator_id)
        risk_level = "low"
        if metrics.churn_rate > 0.15:
            risk_level = "critical"
        elif metrics.churn_rate > 0.08:
            risk_level = "high"
        elif metrics.churn_rate > 0.03:
            risk_level = "medium"

        return {
            "creator_id": creator_id,
            "churn_rate": metrics.churn_rate,
            "risk_level": risk_level,
            "active_subscribers": metrics.active_subscribers,
            "recommendations": [
                "Engage with at-risk subscribers" if risk_level in ("high", "critical") else "Maintain current engagement",
            ],
        }

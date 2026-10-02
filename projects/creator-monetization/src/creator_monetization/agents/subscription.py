"""Subscription Agent - Manages creator subscriptions and subscriber lifecycle."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import structlog
from pydantic import BaseModel, Field

from creator_monetization.models.schemas import Subscription, SubscriptionStatus

logger = structlog.get_logger(__name__)


class SubscriptionMetrics(BaseModel):
    """Subscription metrics for a creator."""

    creator_id: str = Field(..., description="Creator identifier")
    total_subscribers: int = Field(default=0, ge=0)
    active_subscribers: int = Field(default=0, ge=0)
    trialing_subscribers: int = Field(default=0, ge=0)
    cancelled_subscribers: int = Field(default=0, ge=0)
    monthly_recurring_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    annual_recurring_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    average_revenue_per_user: Decimal = Field(default=Decimal("0"), ge=0)
    churn_rate: float = Field(default=0.0, ge=0, le=1)
    lifetime_value: Decimal = Field(default=Decimal("0"), ge=0)


class SubscriptionAgent:
    """Agent responsible for managing creator subscriptions.

    Handles subscription lifecycle, churn prevention,
    trial management, and subscriber analytics.
    """

    def __init__(self, trial_period_days: int = 14) -> None:
        """Initialize the subscription agent.

        Args:
            trial_period_days: Number of days for trial period.
        """
        self.trial_period_days = trial_period_days
        self._subscriptions: dict[str, Subscription] = {}
        self._creator_subscriptions: dict[str, list[str]] = {}

    async def create_subscription(self, subscription: Subscription) -> Subscription:
        """Create a new subscription.

        Args:
            subscription: The subscription to create.

        Returns:
            The created subscription.

        Raises:
            ValueError: If subscription_id already exists.
        """
        if subscription.subscription_id in self._subscriptions:
            raise ValueError(
                f"Subscription {subscription.subscription_id} already exists"
            )

        logger.info(
            "Creating subscription",
            subscription_id=subscription.subscription_id,
            creator_id=subscription.creator_id,
            subscriber_id=subscription.subscriber_id,
        )

        self._subscriptions[subscription.subscription_id] = subscription

        # Index by creator
        if subscription.creator_id not in self._creator_subscriptions:
            self._creator_subscriptions[subscription.creator_id] = []
        self._creator_subscriptions[subscription.creator_id].append(
            subscription.subscription_id
        )

        return subscription

    async def cancel_subscription(
        self, subscription_id: str, reason: str | None = None
    ) -> Subscription:
        """Cancel a subscription.

        Args:
            subscription_id: The subscription to cancel.
            reason: Optional cancellation reason.

        Returns:
            Updated subscription.

        Raises:
            KeyError: If subscription not found.
            ValueError: If subscription is already cancelled.
        """
        if subscription_id not in self._subscriptions:
            raise KeyError(f"Subscription {subscription_id} not found")

        subscription = self._subscriptions[subscription_id]
        if subscription.status == SubscriptionStatus.CANCELLED:
            raise ValueError(f"Subscription {subscription_id} is already cancelled")

        logger.info(
            "Cancelling subscription",
            subscription_id=subscription_id,
            reason=reason,
        )

        subscription.status = SubscriptionStatus.CANCELLED
        subscription.end_date = datetime.now(UTC)
        subscription.auto_renew = False
        subscription.updated_at = datetime.now(UTC)

        if reason:
            subscription.metadata["cancellation_reason"] = reason

        return subscription

    async def renew_subscription(self, subscription_id: str) -> Subscription:
        """Renew a subscription for another period.

        Args:
            subscription_id: The subscription to renew.

        Returns:
            Updated subscription.

        Raises:
            KeyError: If subscription not found.
            ValueError: If subscription is not active.
        """
        if subscription_id not in self._subscriptions:
            raise KeyError(f"Subscription {subscription_id} not found")

        subscription = self._subscriptions[subscription_id]
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise ValueError(
                f"Subscription {subscription_id} is not active (status: {subscription.status})"
            )

        logger.info("Renewing subscription", subscription_id=subscription_id)

        # Extend end date by one month
        if subscription.end_date:
            subscription.end_date = subscription.end_date + timedelta(days=30)
        else:
            subscription.end_date = datetime.now(UTC) + timedelta(days=30)

        subscription.updated_at = datetime.now(UTC)
        return subscription

    async def get_subscription_metrics(self, creator_id: str) -> SubscriptionMetrics:
        """Get subscription metrics for a creator.

        Args:
            creator_id: The creator identifier.

        Returns:
            Subscription metrics.
        """
        sub_ids = self._creator_subscriptions.get(creator_id, [])
        subscriptions = [
            self._subscriptions[sid] for sid in sub_ids if sid in self._subscriptions
        ]

        total = len(subscriptions)
        active = len(
            [s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE]
        )
        trialing = len(
            [s for s in subscriptions if s.status == SubscriptionStatus.TRIALING]
        )
        cancelled = len(
            [s for s in subscriptions if s.status == SubscriptionStatus.CANCELLED]
        )

        mrr = sum(
            (s.amount for s in subscriptions if s.status == SubscriptionStatus.ACTIVE),
            Decimal("0"),
        )
        arr = mrr * Decimal("12")
        arpu = mrr / active if active > 0 else Decimal("0")
        churn_rate = cancelled / total if total > 0 else 0.0

        # Simple LTV calculation: ARPU / churn rate
        ltv = arpu / Decimal(str(churn_rate)) if churn_rate > 0 else arpu * Decimal("12")

        return SubscriptionMetrics(
            creator_id=creator_id,
            total_subscribers=total,
            active_subscribers=active,
            trialing_subscribers=trialing,
            cancelled_subscribers=cancelled,
            monthly_recurring_revenue=mrr.quantize(Decimal("0.01")),
            annual_recurring_revenue=arr.quantize(Decimal("0.01")),
            average_revenue_per_user=arpu.quantize(Decimal("0.01")),
            churn_rate=round(churn_rate, 4),
            lifetime_value=ltv.quantize(Decimal("0.01")),
        )

    async def identify_churn_risk(self, creator_id: str) -> list[dict[str, Any]]:
        """Identify subscribers at risk of churning.

        Args:
            creator_id: The creator identifier.

        Returns:
            List of at-risk subscribers with risk factors.
        """
        sub_ids = self._creator_subscriptions.get(creator_id, [])
        at_risk: list[dict[str, Any]] = []

        for sid in sub_ids:
            if sid not in self._subscriptions:
                continue
            sub = self._subscriptions[sid]
            if sub.status != SubscriptionStatus.ACTIVE:
                continue

            risk_factors = []
            # Check if subscription is near end date
            if sub.end_date:
                days_until_expiry = (sub.end_date - datetime.now(UTC)).days
                if days_until_expiry <= 7:
                    risk_factors.append("expiring_soon")

            # Check if auto-renew is disabled
            if not sub.auto_renew:
                risk_factors.append("auto_renew_disabled")

            if risk_factors:
                at_risk.append(
                    {
                        "subscription_id": sub.subscription_id,
                        "subscriber_id": sub.subscriber_id,
                        "risk_factors": risk_factors,
                        "risk_level": "high" if len(risk_factors) > 1 else "medium",
                    }
                )

        logger.info(
            "Identified churn risk",
            creator_id=creator_id,
            at_risk_count=len(at_risk),
        )
        return at_risk

    def get_subscription_count(self, creator_id: str) -> int:
        """Get the number of subscriptions for a creator.

        Args:
            creator_id: The creator identifier.

        Returns:
            Number of subscriptions.
        """
        return len(self._creator_subscriptions.get(creator_id, []))

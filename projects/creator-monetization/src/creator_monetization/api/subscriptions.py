"""Subscriptions API endpoints."""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from creator_monetization.models.schemas import Subscription, SubscriptionCreate, SubscriptionStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class SubscriptionResponse(BaseModel):
    """Response model for subscription."""

    subscription_id: str
    creator_id: str
    subscriber_id: str
    tier_id: str
    status: str
    start_date: str
    end_date: str | None
    auto_renew: bool
    amount: str
    currency: str
    created_at: str
    updated_at: str


class SubscriptionListResponse(BaseModel):
    """Response model for subscription list."""

    subscriptions: list[SubscriptionResponse]
    total: int
    page: int
    page_size: int


class SubscriptionMetricsResponse(BaseModel):
    """Response model for subscription metrics."""

    creator_id: str
    total_subscribers: int
    active_subscribers: int
    trialing_subscribers: int
    cancelled_subscribers: int
    monthly_recurring_revenue: str
    annual_recurring_revenue: str
    average_revenue_per_user: str
    churn_rate: float
    lifetime_value: str


_subscriptions: dict[str, dict[str, Any]] = {}


def _get_subscription_or_404(subscription_id: str) -> dict[str, Any]:
    """Get a subscription by ID or raise 404."""
    if subscription_id not in _subscriptions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription '{subscription_id}' not found",
        )
    return _subscriptions[subscription_id]


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(request: SubscriptionCreate) -> SubscriptionResponse:
    """Create a new subscription."""
    subscription_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    subscription = {
        "subscription_id": subscription_id,
        "creator_id": request.creator_id,
        "subscriber_id": request.subscriber_id,
        "tier_id": request.tier_id,
        "status": SubscriptionStatus.ACTIVE.value,
        "start_date": now,
        "end_date": None,
        "auto_renew": request.auto_renew,
        "amount": str(request.amount),
        "currency": request.currency,
        "created_at": now,
        "updated_at": now,
    }

    _subscriptions[subscription_id] = subscription
    logger.info("Subscription created", extra={"subscription_id": subscription_id})
    return SubscriptionResponse(**subscription)


@router.get("", response_model=SubscriptionListResponse)
async def list_subscriptions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    creator_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
) -> SubscriptionListResponse:
    """List subscriptions with pagination and filtering."""
    subscriptions = list(_subscriptions.values())

    if creator_id:
        subscriptions = [s for s in subscriptions if s["creator_id"] == creator_id]
    if status_filter:
        subscriptions = [s for s in subscriptions if s["status"] == status_filter]

    total = len(subscriptions)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = subscriptions[start:end]

    return SubscriptionListResponse(
        subscriptions=[SubscriptionResponse(**s) for s in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: str) -> SubscriptionResponse:
    """Get a subscription by ID."""
    subscription = _get_subscription_or_404(subscription_id)
    return SubscriptionResponse(**subscription)


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: str, reason: str | None = None
) -> SubscriptionResponse:
    """Cancel a subscription."""
    subscription = _get_subscription_or_404(subscription_id)

    if subscription["status"] == SubscriptionStatus.CANCELLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is already cancelled",
        )

    subscription["status"] = SubscriptionStatus.CANCELLED.value
    subscription["end_date"] = datetime.now(UTC).isoformat()
    subscription["auto_renew"] = False
    subscription["updated_at"] = datetime.now(UTC).isoformat()

    if reason:
        subscription["cancellation_reason"] = reason

    logger.info("Subscription cancelled", extra={"subscription_id": subscription_id})
    return SubscriptionResponse(**subscription)


@router.post("/{subscription_id}/renew", response_model=SubscriptionResponse)
async def renew_subscription(subscription_id: str) -> SubscriptionResponse:
    """Renew a subscription."""
    subscription = _get_subscription_or_404(subscription_id)

    if subscription["status"] != SubscriptionStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subscription is not active (status: {subscription['status']})",
        )

    # Extend end date by 30 days
    end_date = subscription.get("end_date")
    if end_date:
        from datetime import timedelta
        new_end = datetime.fromisoformat(end_date) + timedelta(days=30)
        subscription["end_date"] = new_end.isoformat()
    else:
        subscription["end_date"] = (datetime.now(UTC) + timedelta(days=30)).isoformat()

    subscription["updated_at"] = datetime.now(UTC).isoformat()
    logger.info("Subscription renewed", extra={"subscription_id": subscription_id})
    return SubscriptionResponse(**subscription)


@router.get("/creator/{creator_id}/metrics", response_model=SubscriptionMetricsResponse)
async def get_subscription_metrics(creator_id: str) -> SubscriptionMetricsResponse:
    """Get subscription metrics for a creator."""
    creator_subs = [
        s for s in _subscriptions.values() if s["creator_id"] == creator_id
    ]

    total = len(creator_subs)
    active = len([s for s in creator_subs if s["status"] == SubscriptionStatus.ACTIVE.value])
    trialing = len([s for s in creator_subs if s["status"] == SubscriptionStatus.TRIALING.value])
    cancelled = len([s for s in creator_subs if s["status"] == SubscriptionStatus.CANCELLED.value])

    mrr = sum(
        Decimal(s["amount"]) for s in creator_subs
        if s["status"] == SubscriptionStatus.ACTIVE.value
    )
    arr = mrr * Decimal("12")
    arpu = mrr / active if active > 0 else Decimal("0")
    churn_rate = cancelled / total if total > 0 else 0.0
    ltv = arpu / Decimal(str(churn_rate)) if churn_rate > 0 else arpu * Decimal("12")

    return SubscriptionMetricsResponse(
        creator_id=creator_id,
        total_subscribers=total,
        active_subscribers=active,
        trialing_subscribers=trialing,
        cancelled_subscribers=cancelled,
        monthly_recurring_revenue=str(mrr.quantize(Decimal("0.01"))),
        annual_recurring_revenue=str(arr.quantize(Decimal("0.01"))),
        average_revenue_per_user=str(arpu.quantize(Decimal("0.01"))),
        churn_rate=round(churn_rate, 4),
        lifetime_value=str(ltv.quantize(Decimal("0.01"))),
    )


@router.get("/creator/{creator_id}/churn-risk")
async def get_churn_risk(creator_id: str) -> dict[str, Any]:
    """Identify subscribers at risk of churning."""
    creator_subs = [
        s for s in _subscriptions.values()
        if s["creator_id"] == creator_id and s["status"] == SubscriptionStatus.ACTIVE.value
    ]

    at_risk: list[dict[str, Any]] = []
    for sub in creator_subs:
        risk_factors = []
        end_date = sub.get("end_date")
        if end_date:
            days_until_expiry = (datetime.fromisoformat(end_date) - datetime.now(UTC)).days
            if days_until_expiry <= 7:
                risk_factors.append("expiring_soon")

        if not sub.get("auto_renew", True):
            risk_factors.append("auto_renew_disabled")

        if risk_factors:
            at_risk.append(
                {
                    "subscription_id": sub["subscription_id"],
                    "subscriber_id": sub["subscriber_id"],
                    "risk_factors": risk_factors,
                    "risk_level": "high" if len(risk_factors) > 1 else "medium",
                }
            )

    return {
        "creator_id": creator_id,
        "at_risk_count": len(at_risk),
        "at_risk_subscribers": at_risk,
    }
"""Webhook subscription endpoints."""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.v1.schemas.common import PaginatedResponse, PaginationParams
from app.api.v1.schemas.webhook import (
    TestWebhookResponse,
    WebhookDelivery,
    WebhookSubscription,
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
)
from app.core.exceptions import NotFoundException
from app.middleware.auth import AuthContext, get_current_auth, require_scope

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

_subscriptions: dict[str, dict] = {}
_deliveries: dict[str, list[dict]] = {}


@router.get("/subscriptions", response_model=PaginatedResponse[WebhookSubscription])
async def list_subscriptions(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("webhooks:manage"))],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[WebhookSubscription]:
    """List webhook subscriptions."""
    results = list(_subscriptions.values())
    total = len(results)

    start = 0
    if pagination.cursor:
        try:
            start = int(pagination.cursor)
        except ValueError:
            start = 0

    end = start + pagination.limit
    page = results[start:end]
    next_cursor = str(end) if end < total else None

    return PaginatedResponse(
        data=[WebhookSubscription(**s) for s in page],
        pagination={
            "next_cursor": next_cursor,
            "has_next": next_cursor is not None,
            "total": total,
        },
    )


@router.post("/subscriptions", response_model=WebhookSubscription, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("webhooks:manage"))],
    body: WebhookSubscriptionCreate,
) -> WebhookSubscription:
    """Create a webhook subscription."""
    subscription_id = f"sub-{len(_subscriptions) + 1:03d}"
    now = datetime.now(timezone.utc)

    subscription = {
        "subscription_id": subscription_id,
        "url": body.url,
        "events": [e.value for e in body.events],
        "secret": body.secret,
        "description": body.description,
        "active": body.active,
        "metadata": body.metadata or {},
        "created_at": now,
        "delivery_stats": {
            "total_deliveries": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "last_delivery_at": None,
        },
    }

    _subscriptions[subscription_id] = subscription
    _deliveries[subscription_id] = []

    return WebhookSubscription(**subscription)


@router.get("/subscriptions/{subscription_id}", response_model=WebhookSubscription)
async def get_subscription(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("webhooks:manage"))],
    subscription_id: str,
) -> WebhookSubscription:
    """Get a webhook subscription by ID."""
    if subscription_id not in _subscriptions:
        raise NotFoundException("Subscription", subscription_id)
    return WebhookSubscription(**_subscriptions[subscription_id])


@router.put("/subscriptions/{subscription_id}", response_model=WebhookSubscription)
async def update_subscription(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("webhooks:manage"))],
    subscription_id: str,
    body: WebhookSubscriptionUpdate,
) -> WebhookSubscription:
    """Update a webhook subscription."""
    if subscription_id not in _subscriptions:
        raise NotFoundException("Subscription", subscription_id)

    subscription = _subscriptions[subscription_id]

    if body.url:
        subscription["url"] = body.url
    if body.events:
        subscription["events"] = [e.value for e in body.events]
    if body.secret:
        subscription["secret"] = body.secret
    if body.description:
        subscription["description"] = body.description
    if body.active is not None:
        subscription["active"] = body.active
    if body.metadata:
        subscription["metadata"] = body.metadata

    return WebhookSubscription(**subscription)


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("webhooks:manage"))],
    subscription_id: str,
) -> None:
    """Delete a webhook subscription."""
    if subscription_id not in _subscriptions:
        raise NotFoundException("Subscription", subscription_id)

    del _subscriptions[subscription_id]
    if subscription_id in _deliveries:
        del _deliveries[subscription_id]


@router.post("/subscriptions/{subscription_id}/test", response_model=TestWebhookResponse)
async def test_subscription(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("webhooks:manage"))],
    subscription_id: str,
) -> TestWebhookResponse:
    """Send a test event to the subscription."""
    if subscription_id not in _subscriptions:
        raise NotFoundException("Subscription", subscription_id)

    subscription = _subscriptions[subscription_id]
    now = datetime.now(timezone.utc)

    # In production, this would actually send the webhook
    test_event_id = f"evt-test-{int(now.timestamp())}"

    # Record delivery
    delivery = {
        "delivery_id": f"del-{len(_deliveries.get(subscription_id, [])) + 1:03d}",
        "subscription_id": subscription_id,
        "event_id": test_event_id,
        "event_type": "test",
        "status": "delivered",
        "http_status": 200,
        "response_time_ms": 45.0,
        "attempts": 1,
        "delivered_at": now,
        "next_retry_at": None,
    }

    if subscription_id not in _deliveries:
        _deliveries[subscription_id] = []
    _deliveries[subscription_id].append(delivery)

    # Update stats
    subscription["delivery_stats"]["total_deliveries"] += 1
    subscription["delivery_stats"]["successful_deliveries"] += 1
    subscription["delivery_stats"]["last_delivery_at"] = now

    return TestWebhookResponse(
        subscription_id=subscription_id,
        test_event_id=test_event_id,
        delivery_status="delivered",
        http_status=200,
        response_time_ms=45.0,
        delivered_at=now,
    )


@router.get("/subscriptions/{subscription_id}/deliveries", response_model=list[WebhookDelivery])
async def get_delivery_history(
    request: Request,
    auth: Annotated[AuthContext, Depends(require_scope("webhooks:manage"))],
    subscription_id: str,
    status_filter: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[WebhookDelivery]:
    """Get webhook delivery history."""
    if subscription_id not in _subscriptions:
        raise NotFoundException("Subscription", subscription_id)

    deliveries = _deliveries.get(subscription_id, [])

    if status_filter:
        deliveries = [d for d in deliveries if d["status"] == status_filter]
    if date_from:
        deliveries = [d for d in deliveries if d["delivered_at"] and d["delivered_at"] >= date_from]
    if date_to:
        deliveries = [d for d in deliveries if d["delivered_at"] and d["delivered_at"] <= date_to]

    return [WebhookDelivery(**d) for d in deliveries]

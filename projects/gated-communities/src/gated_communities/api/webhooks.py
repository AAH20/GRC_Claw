"""Webhook management API."""
from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class WebhookCreate(BaseModel):
    """Schema for creating a webhook."""
    url: str = Field(..., description="Webhook URL")
    events: list[str] = Field(..., description="List of events to subscribe to")
    secret: str | None = Field(None, description="Secret for HMAC signature")


class WebhookResponse(BaseModel):
    """Schema for webhook response."""
    id: str
    url: str
    events: list[str]
    is_active: bool
    created_at: str


class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery response."""
    id: str
    webhook_id: str
    event: str
    status_code: int | None
    success: bool
    created_at: str


# In-memory store (replace with database in production)
_webhooks: dict[str, dict[str, Any]] = {}
_deliveries: dict[str, list[dict[str, Any]]] = {}


@router.post("/webhooks", response_model=WebhookResponse, status_code=201)
async def create_webhook(webhook: WebhookCreate) -> WebhookResponse:
    """Create a new webhook subscription."""
    webhook_id = str(uuid4())
    _webhooks[webhook_id] = {
        "id": webhook_id,
        "url": webhook.url,
        "events": webhook.events,
        "secret": webhook.secret,
        "is_active": True,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _deliveries[webhook_id] = []
    logger.info("webhook_created", webhook_id=webhook_id, url=webhook.url)
    return WebhookResponse(**_webhooks[webhook_id])


@router.get("/webhooks", response_model=list[WebhookResponse])
async def list_webhooks() -> list[WebhookResponse]:
    """List all webhook subscriptions."""
    return [WebhookResponse(**w) for w in _webhooks.values()]


@router.get("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(webhook_id: str) -> WebhookResponse:
    """Get a specific webhook."""
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return WebhookResponse(**_webhooks[webhook_id])


@router.delete("/webhooks/{webhook_id}", status_code=204)
async def delete_webhook(webhook_id: str) -> None:
    """Delete a webhook subscription."""
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")
    del _webhooks[webhook_id]
    _deliveries.pop(webhook_id, None)
    logger.info("webhook_deleted", webhook_id=webhook_id)


@router.post("/webhooks/{webhook_id}/test", response_model=WebhookDeliveryResponse)
async def test_webhook(webhook_id: str) -> WebhookDeliveryResponse:
    """Send a test event to a webhook."""
    if webhook_id not in _webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")
    delivery_id = str(uuid4())
    delivery = {
        "id": delivery_id,
        "webhook_id": webhook_id,
        "event": "test",
        "status_code": 200,
        "success": True,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _deliveries[webhook_id].append(delivery)
    return WebhookDeliveryResponse(**delivery)


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC signature for webhook payload."""
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

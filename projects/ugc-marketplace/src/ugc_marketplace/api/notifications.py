"""
Notifications API endpoints for UGC Marketplace.

Provides:
  GET  /notifications  — paginated list with read-status filtering
  POST /notifications  — create a new notification with validation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ---------------------------------------------------------------------------
# Enums & Models
# ---------------------------------------------------------------------------

class NotificationType(str, Enum):
    """Types of notifications supported by the marketplace."""
    ORDER_PLACED = "order_placed"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    PAYMENT_RECEIVED = "payment_received"
    REVIEW_RECEIVED = "review_received"
    MESSAGE_RECEIVED = "message_received"
    SYSTEM_ALERT = "system_alert"
    PROMOTION = "promotion"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationBase(BaseModel):
    """Shared fields for a notification."""
    user_id: str = Field(..., min_length=1, description="Recipient user ID")
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    message: str = Field(..., min_length=1, max_length=2000, description="Notification body")
    type: NotificationType = Field(..., description="Category of notification")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    link: Optional[str] = Field(default=None, max_length=500, description="Deep link to related resource")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Arbitrary key-value metadata")

    @field_validator("link")
    @classmethod
    def validate_link(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith(("http://", "https://", "/")):
            raise ValueError("link must be a valid URL or relative path")
        return v


class NotificationCreate(NotificationBase):
    """Payload for creating a new notification."""
    pass


class Notification(NotificationBase):
    """Full notification representation (includes server-generated fields)."""
    id: str = Field(..., description="Unique notification ID")
    is_read: bool = Field(default=False, description="Whether the notification has been read")
    created_at: datetime = Field(..., description="ISO-8601 creation timestamp")
    read_at: Optional[datetime] = Field(default=None, description="ISO-8601 read timestamp")

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated list response wrapper."""
    data: List[Notification]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

MOCK_NOTIFICATIONS: List[Dict[str, Any]] = [
    {
        "id": "n-001",
        "user_id": "user-101",
        "title": "Order #UGC-2024-0892 Shipped",
        "message": "Your order for 'Custom Brand Video Package' has been shipped and is on its way.",
        "type": "order_shipped",
        "priority": "normal",
        "link": "/orders/UGC-2024-0892",
        "metadata": {"order_id": "UGC-2024-0892", "carrier": "FedEx", "tracking": "FX-8842-9910"},
        "is_read": False,
        "created_at": "2026-10-01T14:32:00Z",
        "read_at": None,
    },
    {
        "id": "n-002",
        "user_id": "user-101",
        "title": "New 5-Star Review Received",
        "message": "Creator @jane_doe left a glowing review on your product 'Social Media Starter Kit'.",
        "type": "review_received",
        "priority": "normal",
        "link": "/products/social-media-starter-kit/reviews",
        "metadata": {"product_id": "prod-55", "rating": 5, "reviewer": "jane_doe"},
        "is_read": True,
        "created_at": "2026-09-30T09:15:00Z",
        "read_at": "2026-09-30T10:02:00Z",
    },
    {
        "id": "n-003",
        "user_id": "user-102",
        "title": "Payment Received — $249.00",
        "message": "You received a payment of $249.00 for 'Instagram Reel Bundle x3'.",
        "type": "payment_received",
        "priority": "high",
        "link": "/earnings",
        "metadata": {"amount": 249.00, "currency": "USD", "payout_id": "pay-7781"},
        "is_read": False,
        "created_at": "2026-10-02T18:45:00Z",
        "read_at": None,
    },
    {
        "id": "n-004",
        "user_id": "user-101",
        "title": "New Message from @creator_pro",
        "message": "Hey! I'd love to collaborate on a sponsored post. Are you available next week?",
        "type": "message_received",
        "priority": "normal",
        "link": "/messages/thread-42",
        "metadata": {"thread_id": "thread-42", "sender": "creator_pro"},
        "is_read": False,
        "created_at": "2026-10-03T08:20:00Z",
        "read_at": None,
    },
    {
        "id": "n-005",
        "user_id": "user-103",
        "title": "Flash Sale: 30% Off All Templates",
        "message": "This weekend only — get 30% off every template in the marketplace. Don't miss out!",
        "type": "promotion",
        "priority": "low",
        "link": "/marketplace?promo=FLASH30",
        "metadata": {"promo_code": "FLASH30", "discount_pct": 30, "expires": "2026-10-05T23:59:59Z"},
        "is_read": True,
        "created_at": "2026-10-01T00:00:00Z",
        "read_at": "2026-10-01T06:30:00Z",
    },
    {
        "id": "n-006",
        "user_id": "user-102",
        "title": "Order #UGC-2024-0901 Delivered",
        "message": "Your order 'Podcast Intro Jingle' was delivered. Enjoy!",
        "type": "order_delivered",
        "priority": "normal",
        "link": "/orders/UGC-2024-0901",
        "metadata": {"order_id": "UGC-2024-0901", "delivered_at": "2026-10-02T12:00:00Z"},
        "is_read": False,
        "created_at": "2026-10-02T12:00:00Z",
        "read_at": None,
    },
    {
        "id": "n-007",
        "user_id": "user-101",
        "title": "System Maintenance Scheduled",
        "message": "The marketplace will undergo maintenance on Oct 5, 2:00–4:00 AM UTC.",
        "type": "system_alert",
        "priority": "urgent",
        "link": "/status",
        "metadata": {"maintenance_window": "2026-10-05T02:00:00Z/2026-10-05T04:00:00Z"},
        "is_read": False,
        "created_at": "2026-10-01T16:00:00Z",
        "read_at": None,
    },
    {
        "id": "n-008",
        "user_id": "user-103",
        "title": "New Order Placed — UGC-2024-0910",
        "message": "A new order was placed for 'TikTok Dance Challenge Video'.",
        "type": "order_placed",
        "priority": "high",
        "link": "/orders/UGC-2024-0910",
        "metadata": {"order_id": "UGC-2024-0910", "buyer": "brand_x", "total": 150.00},
        "is_read": False,
        "created_at": "2026-10-03T11:10:00Z",
        "read_at": None,
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List notifications",
    description="Retrieve a paginated list of notifications, optionally filtered by read status.",
)
async def list_notifications(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    is_read: Optional[bool] = Query(default=None, description="Filter by read status (true=read, false=unread)"),
    user_id: Optional[str] = Query(default=None, description="Filter by recipient user ID"),
) -> NotificationListResponse:
    """
    List notifications with pagination and optional read-status filtering.
    """
    filtered = MOCK_NOTIFICATIONS.copy()

    if is_read is not None:
        filtered = [n for n in filtered if n["is_read"] == is_read]

    if user_id is not None:
        filtered = [n for n in filtered if n["user_id"] == user_id]

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    return NotificationListResponse(
        data=[Notification(**item) for item in page_items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=end < total,
        has_prev=page > 1,
    )


@router.post(
    "",
    response_model=Notification,
    status_code=status.HTTP_201_CREATED,
    summary="Create a notification",
    description="Create a new notification for a user. Validates all required fields.",
)
async def create_notification(payload: NotificationCreate) -> Notification:
    """
    Create a new notification with full validation.
    Returns the created notification with server-generated ID and timestamps.
    """
    now = datetime.now(timezone.utc)

    new_notification = {
        "id": f"n-{uuid.uuid4().hex[:8]}",
        "user_id": payload.user_id,
        "title": payload.title,
        "message": payload.message,
        "type": payload.type.value,
        "priority": payload.priority.value,
        "link": payload.link,
        "metadata": payload.metadata,
        "is_read": False,
        "created_at": now.isoformat(),
        "read_at": None,
    }

    MOCK_NOTIFICATIONS.append(new_notification)

    return Notification(**new_notification)

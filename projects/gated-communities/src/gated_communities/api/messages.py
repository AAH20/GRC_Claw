"""
Messages API endpoints for gated-communities.

Provides:
  GET  /messages  — list messages with pagination, filtering by channel/user
  POST /messages  — create a new message with validation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/messages", tags=["messages"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class MessageCreate(BaseModel):
    """Payload for creating a new message."""

    channel_id: str = Field(..., min_length=1, max_length=64, description="Target channel ID")
    user_id: str = Field(..., min_length=1, max_length=64, description="Author user ID")
    content: str = Field(..., min_length=1, max_length=4000, description="Message body")
    parent_id: Optional[str] = Field(None, description="Parent message ID for threaded replies")
    attachments: Optional[List[str]] = Field(default_factory=list, max_length=10)

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be blank")
        return v.strip()


class MessageResponse(BaseModel):
    """Response model for a single message."""

    id: str
    channel_id: str
    user_id: str
    content: str
    parent_id: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    edited: bool = False
    reactions: Dict[str, int] = Field(default_factory=dict)


class MessageListResponse(BaseModel):
    """Paginated list of messages."""

    data: List[MessageResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# ---------------------------------------------------------------------------
# Mock data store (in-memory for demonstration)
# ---------------------------------------------------------------------------

MOCK_USERS = {
    "user-001": {"username": "alice", "display_name": "Alice Chen"},
    "user-002": {"username": "bob", "display_name": "Bob Martinez"},
    "user-003": {"username": "carol", "display_name": "Carol Singh"},
    "user-004": {"username": "dave", "display_name": "Dave Kim"},
    "user-005": {"username": "eve", "display_name": "Eve Johnson"},
}

MOCK_CHANNELS = {
    "chan-general": {"name": "general", "community_id": "comm-001"},
    "chan-announcements": {"name": "announcements", "community_id": "comm-001"},
    "chan-help": {"name": "help", "community_id": "comm-001"},
    "chan-random": {"name": "random", "community_id": "comm-001"},
    "chan-dev": {"name": "dev", "community_id": "comm-002"},
}

_MESSAGES: List[Dict[str, Any]] = []


def _seed_mock_data() -> None:
    """Populate the in-memory store with realistic mock messages."""
    if _MESSAGES:
        return

    sample_messages = [
        ("chan-general", "user-001", "Hey everyone! Welcome to the gated community. 🎉"),
        ("chan-general", "user-002", "Thanks Alice! Excited to be here."),
        ("chan-general", "user-003", "Has anyone set up their profile yet? The onboarding flow is pretty smooth."),
        ("chan-general", "user-001", "Yeah, took me about 2 minutes. The verification step is quick."),
        ("chan-announcements", "user-001", "📢 Community guidelines have been updated. Please review them."),
        ("chan-announcements", "user-004", "Reminder: Q3 community call is next Thursday at 3pm UTC."),
        ("chan-help", "user-005", "I'm having trouble with the API rate limits. Anyone else seeing 429s?"),
        ("chan-help", "user-002", "Check your API key tier — the free tier is 100 req/min."),
        ("chan-help", "user-005", "Ah, that explains it. Thanks Bob!"),
        ("chan-random", "user-003", "Just discovered the coolest integration with our CI pipeline 🚀"),
        ("chan-random", "user-004", "Share the repo link!"),
        ("chan-random", "user-003", "Will do — posting it in #dev shortly."),
        ("chan-dev", "user-002", "PR #142 is ready for review. It adds webhook retry logic."),
        ("chan-dev", "user-004", "Looking at it now. Left a few comments on the error handling."),
        ("chan-dev", "user-002", "Good catch — I'll push a fix this afternoon."),
        ("chan-general", "user-004", "The new dashboard looks amazing. Great work team!"),
        ("chan-general", "user-005", "Agreed! The dark mode is *chef's kiss*."),
        ("chan-help", "user-001", "How do I invite members to a private channel?"),
        ("chan-help", "user-002", "Channel settings → Members → Invite. You need the 'manage' permission."),
        ("chan-announcements", "user-001", "🏆 Community milestone: 1,000 members reached!"),
        ("chan-random", "user-005", "Friday meme thread is live. Drop your best ones!"),
    ]

    now = datetime.now(timezone.utc)
    for i, (channel_id, user_id, content) in enumerate(sample_messages):
        ts = now.replace(minute=now.minute - (len(sample_messages) - i))
        msg = {
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"msg-{i}")),
            "channel_id": channel_id,
            "user_id": user_id,
            "content": content,
            "parent_id": None,
            "attachments": [],
            "created_at": ts.isoformat(),
            "updated_at": ts.isoformat(),
            "edited": False,
            "reactions": {"👍": i % 5, "🎉": i % 3} if i % 4 == 0 else {},
        }
        _MESSAGES.append(msg)


# Seed on module load
_seed_mock_data()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=MessageListResponse)
async def list_messages(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    channel_id: Optional[str] = Query(None, description="Filter by channel ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
) -> Dict[str, Any]:
    """
    List messages with pagination and optional filtering by channel or user.
    """
    filtered = _MESSAGES.copy()

    if channel_id:
        filtered = [m for m in filtered if m["channel_id"] == channel_id]
    if user_id:
        filtered = [m for m in filtered if m["user_id"] == user_id]

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    return {
        "data": [MessageResponse(**m) for m in page_items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": end < total,
        "has_prev": page > 1,
    }


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(payload: MessageCreate) -> Dict[str, Any]:
    """
    Create a new message in a channel.
    """
    # Validate channel exists
    if payload.channel_id not in MOCK_CHANNELS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel '{payload.channel_id}' not found",
        )

    # Validate user exists
    if payload.user_id not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{payload.user_id}' not found",
        )

    # Validate parent message exists if provided
    if payload.parent_id:
        parent = next((m for m in _MESSAGES if m["id"] == payload.parent_id), None)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent message '{payload.parent_id}' not found",
            )
        if parent["channel_id"] != payload.channel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent message must be in the same channel",
            )

    now = datetime.now(timezone.utc).isoformat()
    new_message = {
        "id": str(uuid.uuid4()),
        "channel_id": payload.channel_id,
        "user_id": payload.user_id,
        "content": payload.content,
        "parent_id": payload.parent_id,
        "attachments": payload.attachments or [],
        "created_at": now,
        "updated_at": now,
        "edited": False,
        "reactions": {},
    }

    _MESSAGES.append(new_message)
    return MessageResponse(**new_message).model_dump()

"""Pydantic schemas shared across API routes."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Platform(StrEnum):
    """Supported social platforms."""

    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"


class PostStatus(StrEnum):
    """Lifecycle states for a post."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class PostCreate(BaseModel):
    """Request body for creating a post."""

    platform: Platform
    content: str = Field(min_length=1, max_length=63206)
    scheduled_at: datetime | None = None
    hashtags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str) -> str:
        """Reject whitespace-only content."""
        if not value.strip():
            raise ValueError("content must not be blank")
        return value.strip()


class Post(PostCreate):
    """A stored post with server-assigned fields."""

    id: str
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime
    updated_at: datetime


class PostList(BaseModel):
    """Paginated list of posts."""

    items: list[Post]
    total: int
    limit: int
    offset: int


class AgentInvokeRequest(BaseModel):
    """Request body for invoking an agent directly."""

    payload: dict[str, Any] = Field(default_factory=dict)


class AgentInvokeResponse(BaseModel):
    """Envelope returned by the agent invocation endpoint."""

    agent: str
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0


class HealthResponse(BaseModel):
    """Service health payload."""

    status: str
    version: str
    environment: str

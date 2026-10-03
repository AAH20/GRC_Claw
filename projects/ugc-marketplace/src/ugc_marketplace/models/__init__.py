"""Pydantic models for UGC Marketplace."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Supported content types for moderation."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ModerationAction(str, Enum):
    """Possible moderation actions."""

    ALLOW = "allow"
    FLAG = "flag"
    BLOCK = "block"
    ESCALATE = "escalate"


class PolicySeverity(str, Enum):
    """Policy violation severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AppealStatus(str, Enum):
    """Appeal processing status."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ModerationRequest(BaseModel):
    """Request model for content moderation."""

    content: str = Field(..., min_length=1, max_length=100_000, description="Content to moderate")
    content_type: ContentType = Field(..., description="Type of content")
    user_id: str | None = Field(None, description="User identifier")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    callback_url: str | None = Field(None, description="Webhook for async results")


class ModerationResult(BaseModel):
    """Result model for content moderation."""

    id: UUID = Field(default_factory=uuid4)
    request_id: UUID = Field(default_factory=uuid4)
    content_type: ContentType
    action: ModerationAction
    confidence: float = Field(..., ge=0.0, le=1.0)
    categories: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    policy_violations: list[str] = Field(default_factory=list)
    processing_time_ms: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    agent_trace: dict[str, Any] | None = None


class BatchModerationRequest(BaseModel):
    """Request model for batch content moderation."""

    items: list[ModerationRequest] = Field(..., min_length=1, max_length=100)
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")


class BatchModerationResult(BaseModel):
    """Result model for batch content moderation."""

    batch_id: UUID = Field(default_factory=uuid4)
    results: list[ModerationResult]
    total_processed: int
    total_flagged: int
    total_blocked: int


class PolicyRule(BaseModel):
    """Individual rule within a policy."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    pattern: str = Field(..., min_length=1)
    severity: PolicySeverity
    action: ModerationAction
    enabled: bool = True


class Policy(BaseModel):
    """Content moderation policy."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    rules: list[PolicyRule] = Field(default_factory=list)
    content_types: list[ContentType] = Field(default_factory=list)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AppealSubmission(BaseModel):
    """Request model for submitting an appeal."""

    moderation_result_id: UUID
    user_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=10, max_length=5000)
    evidence: dict[str, Any] = Field(default_factory=dict)


class Appeal(BaseModel):
    """Appeal model representing a moderation appeal."""

    id: UUID = Field(default_factory=uuid4)
    moderation_result_id: UUID
    user_id: str
    reason: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    status: AppealStatus = AppealStatus.PENDING
    reviewer_notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

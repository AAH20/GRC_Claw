"""Pydantic models for content moderation pipeline."""

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
    """Request model for content moderation.

    Attributes:
        content: The content to be moderated (text, image URL, or video URL).
        content_type: Type of content being moderated.
        user_id: Optional user identifier for tracking.
        metadata: Optional additional metadata.
        callback_url: Optional webhook URL for async results.
    """

    content: str = Field(..., min_length=1, max_length=100_000, description="Content to moderate")
    content_type: ContentType = Field(..., description="Type of content")
    user_id: str | None = Field(None, description="User identifier")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    callback_url: str | None = Field(None, description="Webhook for async results")


class ModerationResult(BaseModel):
    """Result model for content moderation.

    Attributes:
        id: Unique result identifier.
        request_id: Original request identifier.
        content_type: Type of content that was moderated.
        action: Moderation decision.
        confidence: Confidence score (0.0 to 1.0).
        categories: Detected violation categories.
        reasons: Human-readable reasons for the decision.
        policy_violations: List of violated policy IDs.
        processing_time_ms: Time taken to process in milliseconds.
        created_at: Timestamp of result creation.
        agent_trace: Optional agent execution trace.
    """

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
    """Request model for batch content moderation.

    Attributes:
        items: List of moderation requests to process.
        priority: Processing priority (low, normal, high).
    """

    items: list[ModerationRequest] = Field(..., min_length=1, max_length=100)
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")


class BatchModerationResult(BaseModel):
    """Result model for batch content moderation.

    Attributes:
        batch_id: Unique batch identifier.
        results: List of individual moderation results.
        total_processed: Total number of items processed.
        total_flagged: Total number of items flagged.
        total_blocked: Total number of items blocked.
    """

    batch_id: UUID = Field(default_factory=uuid4)
    results: list[ModerationResult]
    total_processed: int
    total_flagged: int
    total_blocked: int


class PolicyRule(BaseModel):
    """Individual rule within a policy.

    Attributes:
        id: Unique rule identifier.
        name: Human-readable rule name.
        description: Rule description.
        pattern: Regex pattern or keyword list for matching.
        severity: Severity level if rule is triggered.
        action: Action to take when rule is triggered.
        enabled: Whether the rule is active.
    """

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    pattern: str = Field(..., min_length=1)
    severity: PolicySeverity
    action: ModerationAction
    enabled: bool = True


class Policy(BaseModel):
    """Content moderation policy.

    Attributes:
        id: Unique policy identifier.
        name: Policy name.
        description: Policy description.
        rules: List of policy rules.
        content_types: Content types this policy applies to.
        enabled: Whether the policy is active.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="")
    rules: list[PolicyRule] = Field(default_factory=list)
    content_types: list[ContentType] = Field(default_factory=list)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AppealSubmission(BaseModel):
    """Request model for submitting an appeal.

    Attributes:
        moderation_result_id: ID of the moderation result being appealed.
        user_id: User submitting the appeal.
        reason: Reason for the appeal.
        evidence: Optional supporting evidence.
    """

    moderation_result_id: UUID
    user_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=10, max_length=5000)
    evidence: dict[str, Any] = Field(default_factory=dict)


class Appeal(BaseModel):
    """Appeal model representing a moderation appeal.

    Attributes:
        id: Unique appeal identifier.
        moderation_result_id: ID of the original moderation result.
        user_id: User who submitted the appeal.
        reason: Reason for the appeal.
        evidence: Supporting evidence.
        status: Current appeal status.
        reviewer_notes: Notes from the reviewer.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        resolved_at: Resolution timestamp.
    """

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

"""Pydantic data models for the moderation queue application."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ModerationStatus(StrEnum):
    """Status of a moderation item."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    AUTO_MODERATED = "auto_moderated"


class ContentType(StrEnum):
    """Type of content being moderated."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    COMMENT = "comment"
    POST = "post"
    MESSAGE = "message"


class PriorityLevel(StrEnum):
    """Priority level for moderation items."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModerationItem(BaseModel):
    """A content item requiring moderation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique item identifier")
    content: str = Field(..., min_length=1, description="Content to be moderated")
    content_type: ContentType = Field(default=ContentType.TEXT, description="Type of content")
    author_id: str = Field(..., description="ID of the content author")
    status: ModerationStatus = Field(
        default=ModerationStatus.PENDING, description="Current moderation status"
    )
    queue_id: UUID | None = Field(default=None, description="Assigned queue ID")
    priority_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="AI-assigned priority score"
    )
    priority_level: PriorityLevel | None = Field(
        default=None, description="Derived priority level"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional item metadata"
    )
    tags: list[str] = Field(default_factory=list, description="Content tags")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    reviewed_at: datetime | None = Field(default=None, description="Review completion time")
    reviewer_id: str | None = Field(default=None, description="ID of human reviewer")
    review_notes: str | None = Field(default=None, description="Reviewer notes")

    def needs_review(self) -> bool:
        """Check if item needs human review.

        Returns:
            bool: True if item requires human review.
        """
        return self.status in {
            ModerationStatus.PENDING,
            ModerationStatus.IN_REVIEW,
            ModerationStatus.ESCALATED,
        }

    def is_resolved(self) -> bool:
        """Check if item has been resolved.

        Returns:
            bool: True if item is approved, rejected, or auto-moderated.
        """
        return self.status in {
            ModerationStatus.APPROVED,
            ModerationStatus.REJECTED,
            ModerationStatus.AUTO_MODERATED,
        }


class Queue(BaseModel):
    """A moderation queue for organizing items."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique queue identifier")
    name: str = Field(..., min_length=1, description="Queue name")
    description: str = Field(default="", description="Queue description")
    content_types: list[ContentType] = Field(
        default_factory=list, description="Content types this queue handles"
    )
    max_size: int = Field(default=1000, ge=1, description="Maximum items in queue")
    priority_weights: dict[str, float] = Field(
        default_factory=dict, description="Priority weight configuration"
    )
    assigned_reviewers: list[str] = Field(
        default_factory=list, description="IDs of assigned reviewers"
    )
    is_active: bool = Field(default=True, description="Whether queue is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

    def is_full(self, current_size: int) -> bool:
        """Check if queue is at capacity.

        Args:
            current_size: Current number of items in queue.

        Returns:
            bool: True if queue is full.
        """
        return current_size >= self.max_size


class PriorityScore(BaseModel):
    """AI-generated priority score for a moderation item."""

    model_config = ConfigDict(from_attributes=True)

    item_id: UUID = Field(..., description="ID of the scored item")
    score: float = Field(..., ge=0.0, le=1.0, description="Priority score (0-1)")
    level: PriorityLevel = Field(..., description="Derived priority level")
    factors: dict[str, float] = Field(
        default_factory=dict, description="Scoring factors and their weights"
    )
    reasoning: str = Field(default="", description="AI reasoning for the score")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Model confidence")
    scored_at: datetime = Field(default_factory=datetime.utcnow, description="Scoring time")
    model_version: str = Field(default="1.0", description="Model version used")


class ReviewDecision(BaseModel):
    """A human reviewer's decision on a moderation item."""

    model_config = ConfigDict(from_attributes=True)

    item_id: UUID = Field(..., description="ID of the reviewed item")
    reviewer_id: str = Field(..., description="ID of the reviewer")
    decision: Literal["approve", "reject", "escalate", "request_info"] = Field(
        ..., description="Review decision"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Reviewer confidence")
    notes: str = Field(default="", description="Review notes")
    categories: list[str] = Field(
        default_factory=list, description="Violation categories if rejected"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Decision time")


class Escalation(BaseModel):
    """An escalation record for high-priority moderation items."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique escalation identifier")
    item_id: UUID = Field(..., description="ID of the escalated item")
    reason: str = Field(..., description="Reason for escalation")
    from_queue_id: UUID | None = Field(default=None, description="Source queue ID")
    to_queue_id: UUID | None = Field(default=None, description="Destination queue ID")
    assigned_to: str | None = Field(default=None, description="Assigned reviewer ID")
    priority: PriorityLevel = Field(default=PriorityLevel.HIGH, description="Escalation priority")
    status: Literal["open", "in_progress", "resolved", "closed"] = Field(
        default="open", description="Escalation status"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional escalation metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    resolved_at: datetime | None = Field(default=None, description="Resolution time")


class AgentResponse(BaseModel):
    """Standard response from an AI agent."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether the agent operation succeeded")
    agent_name: str = Field(..., description="Name of the agent")
    data: dict[str, Any] = Field(default_factory=dict, description="Response data")
    error: str | None = Field(default=None, description="Error message if failed")
    processing_time_ms: float = Field(
        default=0.0, description="Processing time in milliseconds"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional response metadata"
    )


class AgentResult(BaseModel):
    """Result from an AI agent execution."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether the operation succeeded")
    data: dict[str, Any] = Field(default_factory=dict, description="Result data")
    error: str | None = Field(default=None, description="Error message if failed")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class QueueMetrics(BaseModel):
    """Metrics for a moderation queue."""

    model_config = ConfigDict(from_attributes=True)

    queue_id: UUID = Field(..., description="Queue identifier")
    total_items: int = Field(default=0, description="Total items in queue")
    pending_items: int = Field(default=0, description="Pending items")
    in_review_items: int = Field(default=0, description="Items in review")
    resolved_items: int = Field(default=0, description="Resolved items")
    avg_resolution_time_seconds: float = Field(
        default=0.0, description="Average resolution time"
    )
    oldest_item_age_seconds: float = Field(
        default=0.0, description="Age of oldest item in seconds"
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Metrics time")

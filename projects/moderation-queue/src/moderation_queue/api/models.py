"""Pydantic models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MIXED = "mixed"


class ModerationDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QueueName(str, Enum):
    GENERAL = "general"
    LEGAL = "legal"
    SAFETY = "safety"
    APPEAL = "appeal"
    PRIORITY = "priority"


class ContentSubmission(BaseModel):
    content: str = Field(..., min_length=1, max_length=50_000)
    content_type: ContentType = ContentType.TEXT
    user_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PriorityScoreResponse(BaseModel):
    priority: int = Field(..., ge=0, le=10)
    reasoning: str
    factors: list[str] = Field(default_factory=list)


class ModerationResultResponse(BaseModel):
    decision: ModerationDecision
    confidence: float = Field(..., ge=0.0, le=1.0)
    categories: list[str] = Field(default_factory=list)
    reasoning: str


class RoutingResultResponse(BaseModel):
    queue: QueueName
    urgency: UrgencyLevel
    required_expertise: str
    sla_minutes: int
    reasoning: str


class ModerationPipelineResponse(BaseModel):
    submission_id: str
    priority: PriorityScoreResponse
    moderation: ModerationResultResponse
    routing: RoutingResultResponse | None = None
    final_decision: ModerationDecision
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float


class QueueItemResponse(BaseModel):
    id: str
    content_type: ContentType
    priority: int
    status: str
    assigned_queue: QueueName | None = None
    created_at: datetime
    updated_at: datetime


class QueueStatsResponse(BaseModel):
    total_pending: int
    total_in_review: int
    total_resolved: int
    avg_processing_time_ms: float
    queue_breakdown: dict[str, int] = Field(default_factory=dict)

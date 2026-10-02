"""Pydantic models for lead routing and nurture sequences."""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RoutingStrategy(StrEnum):
    """Routing strategy types."""

    ROUND_ROBIN = "round_robin"
    SKILL_BASED = "skill_based"
    TERRITORY = "territory"
    LOAD_BALANCED = "load_balanced"
    PRIORITY = "priority"


class RouteDestination(StrEnum):
    """Possible routing destinations."""

    SALES = "sales"
    MARKETING = "marketing"
    NURTURE = "nurture"
    DISQUALIFY = "disqualify"
    ACCOUNT_EXECUTIVE = "account_executive"
    SALES_DEVELOPMENT = "sales_development"


class RoutingPriority(StrEnum):
    """Routing priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RoutingRule(BaseModel):
    """A single routing rule with conditions and destination."""

    id: str = Field(..., min_length=1, description="Unique rule identifier")
    name: str = Field(..., min_length=1, description="Human-readable rule name")
    description: str = Field(default="", description="Rule description")
    destination: RouteDestination
    priority: RoutingPriority = RoutingPriority.MEDIUM
    conditions: dict[str, Any] = Field(
        default_factory=dict, description="Condition key-value pairs"
    )
    score_threshold: float | None = Field(
        default=None, ge=0, le=100, description="Minimum score for this rule"
    )
    grade_filter: list[str] = Field(
        default_factory=list, description="Grades this rule applies to"
    )
    industry_filter: list[str] = Field(
        default_factory=list, description="Industries this rule applies to"
    )
    company_size_min: int | None = Field(default=None, ge=0)
    company_size_max: int | None = Field(default=None, ge=0)
    is_active: bool = True
    order: int = Field(default=0, ge=0, description="Rule evaluation order")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    """Result of a routing decision."""

    lead_id: str
    destination: RouteDestination
    priority: RoutingPriority
    assigned_to: str = ""
    assigned_team: str = ""
    rule_id: str = ""
    rule_name: str = ""
    reason: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    routing_strategy: RoutingStrategy = RoutingStrategy.PRIORITY
    routed_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoutingConfig(BaseModel):
    """Configuration for the routing agent."""

    strategy: RoutingStrategy = RoutingStrategy.PRIORITY
    default_destination: RouteDestination = RouteDestination.NURTURE
    rules: list[RoutingRule] = Field(default_factory=list)
    fallback_enabled: bool = True
    max_rules_evaluated: int = Field(default=50, ge=1, le=200)
    enable_logging: bool = True


class NurtureChannel(StrEnum):
    """Nurture communication channels."""

    EMAIL = "email"
    PHONE = "phone"
    LINKEDIN = "linkedin"
    SMS = "sms"
    DIRECT_MAIL = "direct_mail"


class NurtureStepStatus(StrEnum):
    """Status of a nurture step."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    RESPONDED = "responded"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    FAILED = "failed"


class NurtureStep(BaseModel):
    """A single step in a nurture sequence."""

    id: str = Field(..., min_length=1, description="Unique step identifier")
    sequence_id: str = Field(..., min_length=1, description="Parent sequence ID")
    order: int = Field(..., ge=0, description="Step order in sequence")
    channel: NurtureChannel
    subject: str = Field(default="", description="Email subject or message title")
    content_template: str = Field(default="", description="Content template name")
    delay_days: int = Field(default=0, ge=0, description="Days after previous step")
    status: NurtureStepStatus = NurtureStepStatus.PENDING
    sent_at: str | None = None
    opened_at: str | None = None
    clicked_at: str | None = None
    responded_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NurtureSequence(BaseModel):
    """A nurture sequence definition."""

    id: str = Field(..., min_length=1, description="Unique sequence identifier")
    name: str = Field(..., min_length=1, description="Sequence name")
    description: str = Field(default="", description="Sequence description")
    steps: list[NurtureStep] = Field(default_factory=list)
    target_grade: str = Field(default="cold", description="Target lead grade")
    target_destination: RouteDestination = RouteDestination.NURTURE
    is_active: bool = True
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class NurtureEnrollment(BaseModel):
    """A lead's enrollment in a nurture sequence."""

    id: str = Field(..., min_length=1, description="Unique enrollment identifier")
    lead_id: str = Field(..., min_length=1, description="Lead identifier")
    sequence_id: str = Field(..., min_length=1, description="Sequence identifier")
    current_step: int = Field(default=0, ge=0, description="Current step index")
    status: str = Field(default="active", description="Enrollment status")
    enrolled_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    completed_at: str | None = None
    last_activity_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NurtureCampaign(BaseModel):
    """A nurture campaign with multiple sequences."""

    id: str = Field(..., min_length=1, description="Unique campaign identifier")
    name: str = Field(..., min_length=1, description="Campaign name")
    description: str = Field(default="", description="Campaign description")
    sequence_ids: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    target_company_sizes: list[str] = Field(default_factory=list)
    is_active: bool = True
    start_date: str | None = None
    end_date: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NurtureEngagementEvent(BaseModel):
    """An engagement event during nurture."""

    id: str = Field(..., min_length=1, description="Unique event identifier")
    enrollment_id: str = Field(..., min_length=1, description="Enrollment identifier")
    lead_id: str = Field(..., min_length=1, description="Lead identifier")
    step_id: str = Field(..., min_length=1, description="Step identifier")
    event_type: str = Field(..., min_length=1, description="Event type")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoutingRuleCreate(BaseModel):
    """Model for creating a routing rule."""

    name: str = Field(..., min_length=1)
    description: str = ""
    destination: RouteDestination
    priority: RoutingPriority = RoutingPriority.MEDIUM
    conditions: dict[str, Any] = Field(default_factory=dict)
    score_threshold: float | None = Field(default=None, ge=0, le=100)
    grade_filter: list[str] = Field(default_factory=list)
    industry_filter: list[str] = Field(default_factory=list)
    company_size_min: int | None = Field(default=None, ge=0)
    company_size_max: int | None = Field(default=None, ge=0)
    is_active: bool = True
    order: int = Field(default=0, ge=0)


class RoutingRuleUpdate(BaseModel):
    """Model for updating a routing rule."""

    name: str | None = None
    description: str | None = None
    destination: RouteDestination | None = None
    priority: RoutingPriority | None = None
    conditions: dict[str, Any] | None = None
    score_threshold: float | None = Field(default=None, ge=0, le=100)
    grade_filter: list[str] | None = None
    industry_filter: list[str] | None = None
    company_size_min: int | None = Field(default=None, ge=0)
    company_size_max: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    order: int | None = Field(default=None, ge=0)


class BatchRoutingRequest(BaseModel):
    """Request model for batch routing."""

    lead_ids: list[str] = Field(..., min_length=1, max_length=100)
    context: dict[str, Any] = Field(default_factory=dict)


class BatchRoutingResponse(BaseModel):
    """Response model for batch routing results."""

    success: bool
    results: list[RoutingDecision]
    total: int


class NurtureSequenceCreate(BaseModel):
    """Model for creating a nurture sequence."""

    name: str = Field(..., min_length=1)
    description: str = ""
    steps: list[dict[str, Any]] = Field(..., min_length=1)
    target_grade: str = "cold"
    target_destination: RouteDestination = RouteDestination.NURTURE
    is_active: bool = True


class NurtureEnrollmentRequest(BaseModel):
    """Request model for enrolling a lead in nurture."""

    lead_id: str = Field(..., min_length=1)
    sequence_id: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NurtureSequenceResponse(BaseModel):
    """Response model for nurture sequence operations."""

    success: bool
    data: NurtureSequence | None = None
    message: str = ""


class RoutingDecisionResponse(BaseModel):
    """Response model for routing decision."""

    success: bool
    data: RoutingDecision

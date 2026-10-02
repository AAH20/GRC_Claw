"""Pydantic data models for talent pool management."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class CandidateStatus(str, Enum):
    """Status of a candidate in the talent pool."""

    NEW = "new"
    CONTACTED = "contacted"
    ENGAGED = "engaged"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class PoolVisibility(str, Enum):
    """Visibility level of a talent pool."""

    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"
    PUBLIC = "public"


class SegmentType(str, Enum):
    """Type of talent pool segment."""

    SKILL_BASED = "skill_based"
    EXPERIENCE_BASED = "experience_based"
    LOCATION_BASED = "location_based"
    CUSTOM = "custom"


class EngagementType(str, Enum):
    """Type of engagement action."""

    EMAIL = "email"
    MESSAGE = "message"
    CALL = "call"
    MEETING = "meeting"
    SOCIAL = "social"


class EngagementStatus(str, Enum):
    """Status of an engagement action."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    RESPONDED = "responded"
    BOUNCED = "bounced"
    FAILED = "failed"


class OutreachStatus(str, Enum):
    """Status of an outreach campaign."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class OutreachChannel(str, Enum):
    """Channel for outreach communication."""

    EMAIL = "email"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    PHONE = "phone"
    SMS = "sms"


# ---------------------------------------------------------------------------
# Base Models
# ---------------------------------------------------------------------------


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class TimestampedSchema(BaseSchema):
    """Base schema with timestamp fields."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Candidate Models
# ---------------------------------------------------------------------------


class CandidateSkill(BaseSchema):
    """A skill possessed by a candidate."""

    name: str = Field(..., min_length=1, max_length=100)
    proficiency: Literal["beginner", "intermediate", "advanced", "expert"] = "intermediate"
    years_experience: float = Field(default=0, ge=0, le=50)


class CandidateExperience(BaseSchema):
    """Work experience entry for a candidate."""

    company: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=200)
    start_date: datetime
    end_date: datetime | None = None
    description: str | None = None
    is_current: bool = False


class CandidateEducation(BaseSchema):
    """Education entry for a candidate."""

    institution: str = Field(..., min_length=1, max_length=200)
    degree: str = Field(..., min_length=1, max_length=200)
    field_of_study: str | None = None
    graduation_year: int | None = Field(default=None, ge=1950, le=2030)


class CandidateBase(BaseSchema):
    """Base candidate schema with core fields."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    location: str | None = Field(default=None, max_length=200)
    headline: str | None = Field(default=None, max_length=300)
    summary: str | None = Field(default=None, max_length=5000)
    skills: list[CandidateSkill] = Field(default_factory=list)
    experience: list[CandidateExperience] = Field(default_factory=list)
    education: list[CandidateEducation] = Field(default_factory=list)
    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None
    resume_url: HttpUrl | None = None
    source: str = Field(default="manual", max_length=100)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CandidateCreate(CandidateBase):
    """Schema for creating a new candidate."""

    pool_id: UUID


class CandidateUpdate(BaseSchema):
    """Schema for updating an existing candidate."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    location: str | None = Field(default=None, max_length=200)
    headline: str | None = Field(default=None, max_length=300)
    summary: str | None = Field(default=None, max_length=5000)
    skills: list[CandidateSkill] | None = None
    experience: list[CandidateExperience] | None = None
    education: list[CandidateEducation] | None = None
    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None
    resume_url: HttpUrl | None = None
    status: CandidateStatus | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class Candidate(TimestampedSchema, CandidateBase):
    """Full candidate model with system fields."""

    pool_id: UUID
    status: CandidateStatus = CandidateStatus.NEW
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    score_factors: dict[str, float] = Field(default_factory=dict)
    last_contacted_at: datetime | None = None
    notes: str | None = None


class CandidateResponse(Candidate):
    """Candidate response model for API output."""

    pass


class CandidateListResponse(BaseSchema):
    """Paginated list of candidates."""

    items: list[CandidateResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Talent Pool Models
# ---------------------------------------------------------------------------


class TalentPoolBase(BaseSchema):
    """Base talent pool schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    visibility: PoolVisibility = PoolVisibility.PRIVATE
    tags: list[str] = Field(default_factory=list)
    criteria: dict[str, Any] = Field(default_factory=dict)
    auto_refresh: bool = False
    refresh_interval_hours: int = Field(default=24, ge=1, le=168)


class TalentPoolCreate(TalentPoolBase):
    """Schema for creating a new talent pool."""

    organization_id: UUID


class TalentPoolUpdate(BaseSchema):
    """Schema for updating an existing talent pool."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    visibility: PoolVisibility | None = None
    tags: list[str] | None = None
    criteria: dict[str, Any] | None = None
    auto_refresh: bool | None = None
    refresh_interval_hours: int | None = Field(default=None, ge=1, le=168)


class TalentPool(TimestampedSchema, TalentPoolBase):
    """Full talent pool model with system fields."""

    organization_id: UUID
    candidate_count: int = 0
    segment_count: int = 0
    last_refreshed_at: datetime | None = None
    is_active: bool = True


class TalentPoolResponse(TalentPool):
    """Talent pool response model for API output."""

    pass


class TalentPoolListResponse(BaseSchema):
    """Paginated list of talent pools."""

    items: list[TalentPoolResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TalentPoolStats(BaseSchema):
    """Statistics for a talent pool."""

    pool_id: UUID
    total_candidates: int
    active_candidates: int
    average_score: float
    top_skills: list[dict[str, Any]]
    status_breakdown: dict[str, int]
    segment_distribution: dict[str, int]


# ---------------------------------------------------------------------------
# Segment Models
# ---------------------------------------------------------------------------


class SegmentBase(BaseSchema):
    """Base segment schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    segment_type: SegmentType = SegmentType.CUSTOM
    criteria: dict[str, Any] = Field(default_factory=dict)
    is_dynamic: bool = False


class SegmentCreate(SegmentBase):
    """Schema for creating a new segment."""

    pool_id: UUID


class SegmentUpdate(BaseSchema):
    """Schema for updating an existing segment."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    segment_type: SegmentType | None = None
    criteria: dict[str, Any] | None = None
    is_dynamic: bool | None = None


class Segment(TimestampedSchema, SegmentBase):
    """Full segment model with system fields."""

    pool_id: UUID
    candidate_count: int = 0
    average_score: float = 0.0


class SegmentResponse(Segment):
    """Segment response model for API output."""

    pass


class SegmentListResponse(BaseSchema):
    """Paginated list of segments."""

    items: list[SegmentResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Engagement Models
# ---------------------------------------------------------------------------


class EngagementBase(BaseSchema):
    """Base engagement schema."""

    engagement_type: EngagementType
    subject: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=10000)
    channel: OutreachChannel = OutreachChannel.EMAIL
    scheduled_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EngagementCreate(EngagementBase):
    """Schema for creating a new engagement."""

    candidate_id: UUID


class EngagementUpdate(BaseSchema):
    """Schema for updating an existing engagement."""

    subject: str | None = Field(default=None, min_length=1, max_length=500)
    content: str | None = Field(default=None, min_length=1, max_length=10000)
    status: EngagementStatus | None = None
    scheduled_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class Engagement(TimestampedSchema, EngagementBase):
    """Full engagement model with system fields."""

    candidate_id: UUID
    status: EngagementStatus = EngagementStatus.PENDING
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    opened_at: datetime | None = None
    responded_at: datetime | None = None
    response_content: str | None = None


class EngagementResponse(Engagement):
    """Engagement response model for API output."""

    pass


class EngagementListResponse(BaseSchema):
    """Paginated list of engagements."""

    items: list[EngagementResponse]
    total: int
    page: int
    page_size: int
    pages: int


class EngagementMetrics(BaseSchema):
    """Metrics for engagement performance."""

    total_sent: int
    total_delivered: int
    total_opened: int
    total_responded: int
    delivery_rate: float
    open_rate: float
    response_rate: float
    average_response_time_hours: float | None = None


# ---------------------------------------------------------------------------
# Outreach Models
# ---------------------------------------------------------------------------


class OutreachTemplateBase(BaseSchema):
    """Base outreach template schema."""

    name: str = Field(..., min_length=1, max_length=200)
    subject_template: str = Field(..., min_length=1, max_length=500)
    body_template: str = Field(..., min_length=1, max_length=10000)
    channel: OutreachChannel = OutreachChannel.EMAIL
    tone: Literal["professional", "casual", "enthusiastic"] = "professional"
    variables: list[str] = Field(default_factory=list)


class OutreachTemplateCreate(OutreachTemplateBase):
    """Schema for creating a new outreach template."""

    pass


class OutreachTemplateUpdate(BaseSchema):
    """Schema for updating an existing outreach template."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    subject_template: str | None = Field(default=None, min_length=1, max_length=500)
    body_template: str | None = Field(default=None, min_length=1, max_length=10000)
    channel: OutreachChannel | None = None
    tone: Literal["professional", "casual", "enthusiastic"] | None = None
    variables: list[str] | None = None


class OutreachTemplate(TimestampedSchema, OutreachTemplateBase):
    """Full outreach template model with system fields."""

    usage_count: int = 0
    success_rate: float = 0.0


class OutreachTemplateResponse(OutreachTemplate):
    """Outreach template response model for API output."""

    pass


class OutreachCampaignBase(BaseSchema):
    """Base outreach campaign schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    template_id: UUID
    segment_id: UUID | None = None
    pool_id: UUID | None = None
    scheduled_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OutreachCampaignCreate(OutreachCampaignBase):
    """Schema for creating a new outreach campaign."""

    pass


class OutreachCampaignUpdate(BaseSchema):
    """Schema for updating an existing outreach campaign."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: OutreachStatus | None = None
    scheduled_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class OutreachCampaign(TimestampedSchema, OutreachCampaignBase):
    """Full outreach campaign model with system fields."""

    status: OutreachStatus = OutreachStatus.DRAFT
    total_recipients: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0
    responded_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class OutreachCampaignResponse(OutreachCampaign):
    """Outreach campaign response model for API output."""

    pass


class OutreachCampaignListResponse(BaseSchema):
    """Paginated list of outreach campaigns."""

    items: list[OutreachCampaignResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Agent Request/Response Models
# ---------------------------------------------------------------------------


class DiscoveryRequest(BaseSchema):
    """Request model for candidate discovery agent."""

    pool_id: UUID
    query: str = Field(..., min_length=1, max_length=1000)
    sources: list[str] = Field(default_factory=lambda: ["linkedin", "github", "indeed"])
    max_results: int = Field(default=50, ge=1, le=200)
    filters: dict[str, Any] = Field(default_factory=dict)


class DiscoveryResult(BaseSchema):
    """Result model for candidate discovery agent."""

    candidates_found: int
    candidates: list[CandidateResponse]
    source_breakdown: dict[str, int]
    query_used: str
    duration_seconds: float


class SegmentationRequest(BaseSchema):
    """Request model for pool segmentation agent."""

    pool_id: UUID
    segment_count: int = Field(default=5, ge=2, le=20)
    segment_type: SegmentType = SegmentType.SKILL_BASED
    criteria: dict[str, Any] = Field(default_factory=dict)


class SegmentationResult(BaseSchema):
    """Result model for pool segmentation agent."""

    segments: list[SegmentResponse]
    unassigned_count: int
    quality_score: float
    duration_seconds: float


class ScoringRequest(BaseSchema):
    """Request model for talent scoring agent."""

    candidate_ids: list[UUID] = Field(..., min_length=1)
    criteria: dict[str, Any] = Field(default_factory=dict)
    weights: dict[str, float] = Field(default_factory=dict)


class ScoringResult(BaseSchema):
    """Result model for talent scoring agent."""

    scores: dict[UUID, float]
    factors: dict[UUID, dict[str, float]]
    duration_seconds: float


class OutreachRequest(BaseSchema):
    """Request model for outreach agent."""

    campaign_id: UUID
    candidate_ids: list[UUID] = Field(..., min_length=1)
    template_id: UUID
    personalization_level: Literal["low", "medium", "high"] = "medium"
    send_immediately: bool = False


class OutreachResult(BaseSchema):
    """Result model for outreach agent."""

    messages_generated: int
    messages_sent: int
    messages_failed: int
    details: list[dict[str, Any]]
    duration_seconds: float


class EngagementOptimizationRequest(BaseSchema):
    """Request model for engagement optimizer agent."""

    pool_id: UUID
    segment_id: UUID | None = None
    optimization_goal: Literal["response_rate", "open_rate", "conversion", "retention"] = "response_rate"
    constraints: dict[str, Any] = Field(default_factory=dict)


class EngagementOptimizationResult(BaseSchema):
    """Result model for engagement optimizer agent."""

    recommendations: list[dict[str, Any]]
    predicted_improvement: float
    optimal_send_times: list[str]
    optimal_channels: list[OutreachChannel]
    content_suggestions: list[str]
    duration_seconds: float


# ---------------------------------------------------------------------------
# Health & System Models
# ---------------------------------------------------------------------------


class HealthResponse(BaseSchema):
    """Health check response model."""

    status: str
    version: str
    timestamp: datetime
    uptime_seconds: float
    components: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseSchema):
    """Standard error response model."""

    error: str
    detail: str | None = None
    code: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class APIInfo(BaseSchema):
    """API information response model."""

    name: str
    version: str
    description: str
    endpoints: list[str]
    documentation_url: str

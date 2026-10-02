"""Pydantic request/response models for the API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LeadGrade(str, Enum):
    """Lead grade enumeration."""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    F = "F"


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QualificationFramework(str, Enum):
    """Qualification framework enumeration."""
    BANT = "BANT"
    MEDDIC = "MEDDIC"
    CHAMP = "CHAMP"


class LeadCreateRequest(BaseModel):
    """Request to create a new lead."""
    company_name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    industry: str | None = Field(None, max_length=100)
    company_size: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=255)
    contact_name: str | None = Field(None, max_length=255)
    contact_email: str | None = Field(None, max_length=255)
    contact_phone: str | None = Field(None, max_length=50)
    notes: str | None = Field(None, max_length=5000)
    metadata: dict[str, str] = Field(default_factory=dict)


class LeadScoreRequest(BaseModel):
    """Request to score a lead."""
    lead_id: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    domain: str = Field(..., min_length=1)
    industry: str | None = None
    company_size: str | None = None
    location: str | None = None
    firmographic_score: float = Field(default=50.0, ge=0.0, le=100.0)
    technographic_score: float = Field(default=50.0, ge=0.0, le=100.0)
    intent_score: float = Field(default=50.0, ge=0.0, le=100.0)
    engagement_score: float = Field(default=50.0, ge=0.0, le=100.0)
    timing_score: float = Field(default=50.0, ge=0.0, le=100.0)
    evidence_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class BatchScoreRequest(BaseModel):
    """Request to batch score multiple leads."""
    leads: list[LeadScoreRequest] = Field(..., min_length=1, max_length=100)


class QualificationRequest(BaseModel):
    """Request to qualify a lead."""
    lead_id: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    framework: QualificationFramework = QualificationFramework.BANT
    budget: str | None = None
    authority: str | None = None
    need: str | None = None
    timeline: str | None = None
    metrics: str | None = None
    economic_buyer: str | None = None
    decision_criteria: str | None = None
    decision_process: str | None = None
    identify_pain: str | None = None
    champion: str | None = None


class ChurnPredictionRequest(BaseModel):
    """Request to predict churn for a customer."""
    customer_id: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    tenure_months: int = Field(..., ge=0)
    contract_value: float = Field(..., ge=0.0)
    usage_trend: str = Field(default="stable")
    support_tickets_90d: int = Field(default=0, ge=0)
    nps_score: float | None = Field(None, ge=0.0, le=10.0)
    engagement_score: float = Field(default=50.0, ge=0.0, le=100.0)
    last_login_days: int = Field(default=0, ge=0)
    feature_adoption_rate: float = Field(default=0.5, ge=0.0, le=1.0)
    stakeholder_changes: int = Field(default=0, ge=0)
    contract_renewal_date: str | None = None
    competitor_mentions: int = Field(default=0, ge=0)


class NextBestActionRequest(BaseModel):
    """Request to get next best action for a lead."""
    lead_id: str = Field(..., min_length=1)
    company_name: str = Field(..., min_length=1)
    lead_score: float = Field(..., ge=0.0, le=100.0)
    grade: str = Field(default="C")
    qualified: bool = False
    industry: str | None = None
    company_size: str | None = None
    current_stage: str = Field(default="new")
    last_interaction: str | None = None
    preferred_channel: str | None = None
    pain_points: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)


class LeadResponse(BaseModel):
    """Lead response model."""
    id: str
    company_name: str
    domain: str
    industry: str | None = None
    company_size: str | None = None
    location: str | None = None
    score: float | None = None
    grade: str | None = None
    qualified: bool | None = None
    created_at: datetime
    updated_at: datetime


class ScoreBreakdownResponse(BaseModel):
    """Score breakdown response."""
    dimension: str
    score: float
    weight: float
    weighted_score: float
    rationale: str = ""


class LeadScoreResponse(BaseModel):
    """Lead score response."""
    lead_id: str
    total_score: float
    grade: str
    breakdown: list[ScoreBreakdownResponse]
    confidence: float
    scoring_model: str
    timestamp: str
    rationale: str


class BatchScoreResponse(BaseModel):
    """Batch score response."""
    results: list[LeadScoreResponse]
    total_processed: int
    total_failed: int


class QualificationResponse(BaseModel):
    """Qualification response."""
    lead_id: str
    framework: str
    qualified: bool
    qualification_score: float
    criteria: list[dict]
    next_steps: list[str]
    risk_factors: list[str]
    summary: str


class ChurnPredictionResponse(BaseModel):
    """Churn prediction response."""
    customer_id: str
    churn_probability: float
    risk_level: str
    risk_factors: list[dict]
    protective_factors: list[str]
    recommended_actions: list[str]
    confidence: float
    prediction_window_days: int
    summary: str


class NextBestActionResponse(BaseModel):
    """Next best action response."""
    lead_id: str
    actions: list[dict]
    overall_strategy: str
    urgency: str
    next_review_date: str
    summary: str


class InsightResponse(BaseModel):
    """Insight synthesis response."""
    lead_id: str
    overall_assessment: str
    key_insights: list[dict]
    action_items: list[dict]
    opportunities: list[str]
    risks: list[str]
    recommended_approach: str
    confidence: float
    summary: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str
    services: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: str | None = None
    request_id: str | None = None

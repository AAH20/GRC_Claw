"""Pydantic models for Recruitment Platform API requests and responses."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ─── Base Response ───────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")


class APIResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    success: bool = Field(..., description="Whether the request succeeded")
    data: T = Field(..., description="Response data")


# ─── Resume Parser ───────────────────────────────────────────────────────────


class ResumeParseRequest(BaseModel):
    """Request to parse a resume."""

    text: str = Field(..., description="Resume text content")


class ResumeParseResponse(BaseModel):
    """Structured resume data."""

    name: str | None = Field(None, description="Candidate name")
    email: str | None = Field(None, description="Candidate email")
    phone: str | None = Field(None, description="Candidate phone")
    skills: list[str] = Field(default_factory=list, description="Extracted skills")
    experience: list[dict[str, Any]] = Field(default_factory=list, description="Work experience")
    education: list[dict[str, Any]] = Field(default_factory=list, description="Education history")


class ContactExtractionRequest(BaseModel):
    """Request to extract contact information."""

    text: str = Field(..., description="Resume text content")


class ContactExtractionResponse(BaseModel):
    """Extracted contact information."""

    email: str | None = Field(None, description="Email address")
    phone: str | None = Field(None, description="Phone number")
    address: str | None = Field(None, description="Physical address")
    linkedin: str | None = Field(None, description="LinkedIn profile URL")


class SkillsExtractionRequest(BaseModel):
    """Request to extract skills."""

    text: str = Field(..., description="Resume text content")


class SkillsExtractionResponse(BaseModel):
    """Extracted skills list."""

    skills: list[str] = Field(default_factory=list, description="List of extracted skills")


# ─── Candidate Matcher ───────────────────────────────────────────────────────


class CandidateMatchRequest(BaseModel):
    """Request to match candidates to a job."""

    candidates: list[dict[str, Any]] = Field(..., description="List of candidate profiles")
    job_requirements: dict[str, Any] = Field(..., description="Job requirements")


class CandidateMatchResponse(BaseModel):
    """Ranked candidate matches."""

    matches: list[dict[str, Any]] = Field(default_factory=list, description="Ranked matches")


class MatchExplanationRequest(BaseModel):
    """Request to explain a match."""

    candidate: dict[str, Any] = Field(..., description="Candidate profile")
    job: dict[str, Any] = Field(..., description="Job description")
    match_result: dict[str, Any] = Field(..., description="Match result to explain")


class MatchExplanationResponse(BaseModel):
    """Match explanation."""

    explanation: str = Field(..., description="Human-readable explanation")
    factors: list[dict[str, Any]] = Field(default_factory=list, description="Contributing factors")


class GapAnalysisRequest(BaseModel):
    """Request to analyze skills gap."""

    candidate_skills: list[str] = Field(..., description="Candidate's current skills")
    required_skills: list[str] = Field(..., description="Required skills for the role")


class GapAnalysisResponse(BaseModel):
    """Skills gap analysis results."""

    gaps: list[str] = Field(default_factory=list, description="Missing skills")
    matches: list[str] = Field(default_factory=list, description="Matching skills")
    coverage: float = Field(..., description="Skill coverage percentage")


# ─── Interview Scheduler ─────────────────────────────────────────────────────


class InterviewSlotRequest(BaseModel):
    """Request to optimize interview slots."""

    participants: list[dict[str, Any]] = Field(..., description="Participants and their availabilities")


class InterviewSlotResponse(BaseModel):
    """Optimal interview time slots."""

    slots: list[dict[str, Any]] = Field(default_factory=list, description="Optimal time slots")


class ConflictDetectionRequest(BaseModel):
    """Request to detect scheduling conflicts."""

    proposed_slot: dict[str, Any] = Field(..., description="Proposed time slot")
    existing_events: list[dict[str, Any]] = Field(..., description="Existing calendar events")


class ConflictDetectionResponse(BaseModel):
    """Detected conflicts."""

    conflicts: list[dict[str, Any]] = Field(default_factory=list, description="Detected conflicts")


class ReminderRequest(BaseModel):
    """Request to send an interview reminder."""

    interview: dict[str, Any] = Field(..., description="Interview details")
    reminder_type: str = Field(..., description="Type of reminder")


class ReminderResponse(BaseModel):
    """Reminder delivery status."""

    delivered: bool = Field(..., description="Whether the reminder was delivered")
    message: str = Field(..., description="Delivery message")


# ─── Skills Assessor ─────────────────────────────────────────────────────────


class SkillsAssessmentRequest(BaseModel):
    """Request to assess candidate skills."""

    skill_assessments: list[dict[str, Any]] = Field(..., description="Skill assessment data")


class SkillsAssessmentResponse(BaseModel):
    """Assessment results with proficiency scores."""

    assessments: list[dict[str, Any]] = Field(default_factory=list, description="Assessment results")


class LearningPathRequest(BaseModel):
    """Request to recommend a learning path."""

    skill_gaps: list[str] = Field(..., description="Identified skill gaps")
    career_goals: list[str] = Field(..., description="Career goals")


class LearningPathResponse(BaseModel):
    """Learning path recommendations."""

    path: list[dict[str, Any]] = Field(default_factory=list, description="Recommended learning path")


class SkillValidationRequest(BaseModel):
    """Request to validate claimed skills."""

    claimed_skills: list[str] = Field(..., description="Skills claimed by candidate")
    evidence: dict[str, Any] = Field(..., description="Supporting evidence")


class SkillValidationResponse(BaseModel):
    """Skill validation results."""

    validated: list[dict[str, Any]] = Field(default_factory=list, description="Validation results")


# ─── Bias Detector ───────────────────────────────────────────────────────────


class BiasLanguageRequest(BaseModel):
    """Request to detect biased language."""

    text: str = Field(..., description="Text to analyze")


class BiasLanguageResponse(BaseModel):
    """Detected biased phrases with suggestions."""

    biased_phrases: list[dict[str, Any]] = Field(default_factory=list, description="Biased phrases found")
    suggestions: list[str] = Field(default_factory=list, description="Suggested alternatives")


class FairnessScoreRequest(BaseModel):
    """Request to compute fairness metrics."""

    decisions: list[dict[str, Any]] = Field(..., description="Hiring decisions")
    protected_attributes: list[str] = Field(..., description="Protected attributes to check")


class FairnessScoreResponse(BaseModel):
    """Fairness metric scores."""

    scores: dict[str, float] = Field(default_factory=dict, description="Fairness metric scores")


class DemographicAnalysisRequest(BaseModel):
    """Request to analyze demographic patterns."""

    hiring_data: list[dict[str, Any]] = Field(..., description="Hiring data")
    demographics: list[str] = Field(..., description="Demographic categories")


class DemographicAnalysisResponse(BaseModel):
    """Demographic analysis results."""

    analysis: dict[str, Any] = Field(default_factory=dict, description="Demographic analysis")


class BiasRecommendationRequest(BaseModel):
    """Request for bias mitigation recommendations."""

    bias_analysis: dict[str, Any] = Field(..., description="Bias analysis results")


class BiasRecommendationResponse(BaseModel):
    """Actionable bias mitigation recommendations."""

    recommendations: list[dict[str, Any]] = Field(default_factory=list, description="Recommendations")


# ─── Talent Pool Manager ─────────────────────────────────────────────────────


class TalentSourceRequest(BaseModel):
    """Request to source candidates from talent pool."""

    job_requirements: dict[str, Any] = Field(..., description="Job requirements")
    pool_criteria: dict[str, Any] = Field(..., description="Pool search criteria")


class TalentSourceResponse(BaseModel):
    """Sourced candidates with match scores."""

    candidates: list[dict[str, Any]] = Field(default_factory=list, description="Sourced candidates")


class PoolAnalysisRequest(BaseModel):
    """Request to analyze talent pool health."""

    pool_data: dict[str, Any] = Field(..., description="Talent pool data")
    hiring_needs: dict[str, Any] = Field(..., description="Current hiring needs")


class PoolAnalysisResponse(BaseModel):
    """Pool analysis results."""

    health_score: float = Field(..., description="Pool health score")
    insights: list[str] = Field(default_factory=list, description="Pool insights")


class TalentRecommendRequest(BaseModel):
    """Request to recommend talent for a position."""

    job: dict[str, Any] = Field(..., description="Job description")
    pool_members: list[dict[str, Any]] = Field(..., description="Pool members to consider")


class TalentRecommendResponse(BaseModel):
    """Ranked talent recommendations."""

    recommendations: list[dict[str, Any]] = Field(default_factory=list, description="Ranked recommendations")


class EngagementTrackRequest(BaseModel):
    """Request to track candidate engagement."""

    candidate_id: str = Field(..., description="Candidate identifier")
    interactions: list[dict[str, Any]] = Field(..., description="Interaction history")


class EngagementTrackResponse(BaseModel):
    """Engagement metrics."""

    engagement_score: float = Field(..., description="Engagement score")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Engagement metrics")


# ─── Recruitment Analytics ───────────────────────────────────────────────────


class CostAnalysisRequest(BaseModel):
    """Request to analyze recruitment costs."""

    hiring_data: list[dict[str, Any]] = Field(..., description="Hiring data")
    cost_data: dict[str, Any] = Field(..., description="Cost data")


class CostAnalysisResponse(BaseModel):
    """Cost analysis results."""

    total_cost: float = Field(..., description="Total recruitment cost")
    breakdown: dict[str, float] = Field(default_factory=dict, description="Cost breakdown")


class FunnelAnalysisRequest(BaseModel):
    """Request to analyze recruitment funnel."""

    funnel_data: dict[str, Any] = Field(..., description="Funnel stage data")


class FunnelAnalysisResponse(BaseModel):
    """Funnel analysis results."""

    conversion_rates: dict[str, float] = Field(default_factory=dict, description="Stage conversion rates")
    bottlenecks: list[str] = Field(default_factory=list, description="Identified bottlenecks")


class DiversityMetricsRequest(BaseModel):
    """Request to get diversity metrics."""

    pipeline_data: list[dict[str, Any]] = Field(..., description="Pipeline data")
    demographics: list[str] = Field(..., description="Demographic categories")


class DiversityMetricsResponse(BaseModel):
    """Diversity metrics."""

    metrics: dict[str, float] = Field(default_factory=dict, description="Diversity metrics")


class HiringPredictionRequest(BaseModel):
    """Request to generate hiring predictions."""

    historical_data: list[dict[str, Any]] = Field(..., description="Historical hiring data")
    current_pipeline: dict[str, Any] = Field(..., description="Current pipeline data")


class HiringPredictionResponse(BaseModel):
    """Predictive metrics."""

    predictions: dict[str, Any] = Field(default_factory=dict, description="Hiring predictions")


class SourceEffectivenessRequest(BaseModel):
    """Request to analyze source effectiveness."""

    source_data: dict[str, Any] = Field(..., description="Source data")
    outcomes: dict[str, Any] = Field(..., description="Outcome data")


class SourceEffectivenessResponse(BaseModel):
    """Source effectiveness metrics."""

    effectiveness: dict[str, float] = Field(default_factory=dict, description="Source effectiveness scores")


# ─── Onboarding Automator ───────────────────────────────────────────────────


class ComplianceCheckRequest(BaseModel):
    """Request to check onboarding compliance."""

    employee_data: dict[str, Any] = Field(..., description="Employee data")
    jurisdiction: str = Field(..., description="Jurisdiction for compliance")


class ComplianceCheckResponse(BaseModel):
    """Compliance status."""

    compliant: bool = Field(..., description="Whether onboarding is compliant")
    violations: list[str] = Field(default_factory=list, description="Compliance violations")


class DocumentGenerationRequest(BaseModel):
    """Request to generate onboarding documents."""

    employee: dict[str, Any] = Field(..., description="Employee information")
    template_config: dict[str, Any] = Field(..., description="Template configuration")


class DocumentGenerationResponse(BaseModel):
    """Generated documents."""

    documents: list[dict[str, Any]] = Field(default_factory=list, description="Generated documents")


class ProgressTrackRequest(BaseModel):
    """Request to track onboarding progress."""

    employee_id: str = Field(..., description="Employee identifier")
    onboarding_plan: dict[str, Any] = Field(..., description="Onboarding plan")


class ProgressTrackResponse(BaseModel):
    """Progress status."""

    progress_percentage: float = Field(..., description="Progress percentage")
    completed_tasks: list[str] = Field(default_factory=list, description="Completed tasks")
    pending_tasks: list[str] = Field(default_factory=list, description="Pending tasks")


class TaskScheduleRequest(BaseModel):
    """Request to schedule onboarding tasks."""

    employee: dict[str, Any] = Field(..., description="Employee information")
    start_date: str = Field(..., description="Onboarding start date")


class TaskScheduleResponse(BaseModel):
    """Scheduled tasks."""

    tasks: list[dict[str, Any]] = Field(default_factory=list, description="Scheduled tasks")


class WelcomeMessageRequest(BaseModel):
    """Request to generate welcome message."""

    employee: dict[str, Any] = Field(..., description="Employee information")
    team_info: dict[str, Any] = Field(..., description="Team information")


class WelcomeMessageResponse(BaseModel):
    """Welcome message content."""

    message: str = Field(..., description="Welcome message content")


# ─── Job Description Optimizer ───────────────────────────────────────────────


class ATSCompatibilityRequest(BaseModel):
    """Request to check ATS compatibility."""

    job_description: str = Field(..., description="Job description text")


class ATSCompatibilityResponse(BaseModel):
    """ATS compatibility results."""

    compatible: bool = Field(..., description="Whether the JD is ATS compatible")
    issues: list[str] = Field(default_factory=list, description="Compatibility issues")


class BiasRemovalRequest(BaseModel):
    """Request to remove biased language."""

    job_description: str = Field(..., description="Job description text")


class BiasRemovalResponse(BaseModel):
    """Cleaned text with bias report."""

    cleaned_text: str = Field(..., description="Bias-free job description")
    bias_report: dict[str, Any] = Field(default_factory=dict, description="Bias report")


class KeywordOptimizationRequest(BaseModel):
    """Request to optimize keywords."""

    job_description: str = Field(..., description="Job description text")
    target_role: str = Field(..., description="Target role")


class KeywordOptimizationResponse(BaseModel):
    """Optimized text with keyword suggestions."""

    optimized_text: str = Field(..., description="Optimized job description")
    keywords: list[str] = Field(default_factory=list, description="Suggested keywords")


class SEOOptimizationRequest(BaseModel):
    """Request to optimize for SEO."""

    job_description: str = Field(..., description="Job description text")
    platform: str = Field(..., description="Target platform")


class SEOOptimizationResponse(BaseModel):
    """SEO recommendations."""

    recommendations: list[str] = Field(default_factory=list, description="SEO recommendations")


class ToneAnalysisRequest(BaseModel):
    """Request to analyze tone."""

    job_description: str = Field(..., description="Job description text")
    brand_voice: str = Field(..., description="Brand voice guidelines")


class ToneAnalysisResponse(BaseModel):
    """Tone analysis."""

    tone: str = Field(..., description="Detected tone")
    alignment: float = Field(..., description="Brand voice alignment score")


# ─── Employer Branding ───────────────────────────────────────────────────────


class BrandStrategyRequest(BaseModel):
    """Request to develop brand strategy."""

    company_data: dict[str, Any] = Field(..., description="Company data")
    target_audience: dict[str, Any] = Field(..., description="Target audience")


class BrandStrategyResponse(BaseModel):
    """Brand strategy."""

    strategy: dict[str, Any] = Field(default_factory=dict, description="Brand strategy")


class ContentGenerationRequest(BaseModel):
    """Request to generate branding content."""

    content_type: str = Field(..., description="Type of content to generate")
    brand_guidelines: dict[str, Any] = Field(..., description="Brand guidelines")


class ContentGenerationResponse(BaseModel):
    """Generated content."""

    content: str = Field(..., description="Generated content")


class ReputationManagementRequest(BaseModel):
    """Request to manage employer reputation."""

    platform_data: dict[str, Any] = Field(..., description="Platform data")
    reputation_metrics: dict[str, Any] = Field(..., description="Reputation metrics")


class ReputationManagementResponse(BaseModel):
    """Reputation status."""

    status: str = Field(..., description="Reputation status")
    actions: list[str] = Field(default_factory=list, description="Recommended actions")


class ReviewAnalysisRequest(BaseModel):
    """Request to analyze reviews."""

    reviews: list[dict[str, Any]] = Field(..., description="Reviews to analyze")
    platform: str = Field(..., description="Platform name")


class ReviewAnalysisResponse(BaseModel):
    """Review analysis."""

    summary: str = Field(..., description="Review summary")
    themes: list[str] = Field(default_factory=list, description="Identified themes")


class SentimentAnalysisRequest(BaseModel):
    """Request to analyze sentiment."""

    texts: list[str] = Field(..., description="Texts to analyze")


class SentimentAnalysisResponse(BaseModel):
    """Sentiment analysis."""

    sentiment: str = Field(..., description="Overall sentiment")
    scores: dict[str, float] = Field(default_factory=dict, description="Sentiment scores")

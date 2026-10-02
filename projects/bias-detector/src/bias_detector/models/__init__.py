"""Pydantic models for bias detection data structures."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Gender(str, Enum):
    """Gender categories for demographic analysis."""

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    OTHER = "other"


class Ethnicity(str, Enum):
    """Ethnicity categories for demographic analysis."""

    ASIAN = "asian"
    BLACK = "black"
    HISPANIC = "hispanic"
    WHITE = "white"
    NATIVE_AMERICAN = "native_american"
    PACIFIC_ISLANDER = "pacific_islander"
    MULTIRACIAL = "multiracial"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class DecisionOutcome(str, Enum):
    """Possible outcomes of a hiring decision."""

    HIRED = "hired"
    REJECTED = "rejected"
    INTERVIEWED = "interviewed"
    PENDING = "pending"
    WITHDRAWN = "withdrawn"


class BiasSeverity(str, Enum):
    """Severity levels for detected bias."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BiasType(str, Enum):
    """Types of bias that can be detected."""

    GENDER = "gender"
    AGE = "age"
    RACIAL = "racial"
    LANGUAGE = "language"
    EDUCATIONAL = "educational"
    EXPERIENCE = "experience"
    NAME_BASED = "name_based"
    UNCONSCIOUS = "unconscious"
    SYSTEMIC = "systemic"


class RecommendationPriority(str, Enum):
    """Priority levels for recommendations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Demographic Data
# ---------------------------------------------------------------------------


class DemographicData(BaseModel):
    """Demographic information for a candidate or group.

    Attributes:
        total_candidates: Total number of candidates in the dataset.
        gender_distribution: Count of candidates by gender.
        ethnicity_distribution: Count of candidates by ethnicity.
        age_distribution: Count of candidates by age range.
        education_distribution: Count of candidates by education level.
        experience_distribution: Count of candidates by years of experience range.
        metadata: Additional metadata for the demographic data.
    """

    model_config = ConfigDict(extra="forbid")

    total_candidates: int = Field(default=0, ge=0, description="Total number of candidates")
    gender_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count of candidates by gender"
    )
    ethnicity_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count of candidates by ethnicity"
    )
    age_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count of candidates by age range"
    )
    education_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count of candidates by education level"
    )
    experience_distribution: dict[str, int] = Field(
        default_factory=dict, description="Count of candidates by years of experience"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("*", mode="before")
    @classmethod
    def _ensure_non_negative(cls, v: Any) -> Any:
        """Ensure all count values are non-negative."""
        if isinstance(v, dict):
            for key, val in v.items():
                if isinstance(val, (int, float)) and val < 0:
                    raise ValueError(f"Count for '{key}' must be non-negative")
        return v


class DemographicDisparity(BaseModel):
    """Disparity metric between two demographic groups.

    Attributes:
        dimension: The demographic dimension (e.g., "gender", "ethnicity").
        group_a: The first group name.
        group_b: The second group name.
        rate_a: The rate for group A (e.g., hire rate).
        rate_b: The rate for group B.
        disparity_ratio: The ratio of rate_a to rate_b.
        is_significant: Whether the disparity exceeds the threshold.
    """

    model_config = ConfigDict(extra="forbid")

    dimension: str = Field(..., description="Demographic dimension")
    group_a: str = Field(..., description="First group name")
    group_b: str = Field(..., description="Second group name")
    rate_a: float = Field(..., ge=0.0, le=1.0, description="Rate for group A")
    rate_b: float = Field(..., ge=0.0, le=1.0, description="Rate for group B")
    disparity_ratio: float = Field(..., ge=0.0, description="Ratio of rate_a to rate_b")
    is_significant: bool = Field(..., description="Whether disparity exceeds threshold")


class DemographicAnalysisResult(BaseModel):
    """Result of demographic analysis.

    Attributes:
        disparities: List of detected demographic disparities.
        overall_diversity_score: Overall diversity score (0-1).
        underrepresented_groups: List of underrepresented group names.
        analysis_summary: Human-readable summary of the analysis.
    """

    model_config = ConfigDict(extra="forbid")

    disparities: list[DemographicDisparity] = Field(
        default_factory=list, description="Detected disparities"
    )
    overall_diversity_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall diversity score"
    )
    underrepresented_groups: list[str] = Field(
        default_factory=list, description="Underrepresented groups"
    )
    analysis_summary: str = Field(default="", description="Human-readable summary")


# ---------------------------------------------------------------------------
# Language Patterns
# ---------------------------------------------------------------------------


class LanguagePattern(BaseModel):
    """A detected language pattern in text.

    Attributes:
        pattern_type: The type of language pattern (e.g., "gendered_word").
        text: The specific text or phrase detected.
        position: Character position in the original text.
        severity: Severity level of the pattern.
        suggestion: Suggested replacement or improvement.
        category: Broader category of the pattern.
    """

    model_config = ConfigDict(extra="forbid")

    pattern_type: str = Field(..., description="Type of language pattern")
    text: str = Field(..., description="Detected text or phrase")
    position: int = Field(default=0, ge=0, description="Character position in text")
    severity: BiasSeverity = Field(default=BiasSeverity.LOW, description="Severity level")
    suggestion: str = Field(default="", description="Suggested replacement")
    category: str = Field(default="", description="Broader category")


class LanguageBiasResult(BaseModel):
    """Result of language bias detection.

    Attributes:
        patterns: List of detected language patterns.
        overall_bias_score: Overall bias score (0-1, higher = more biased).
        biased_phrases_count: Total number of biased phrases detected.
        text_analyzed: The original text that was analyzed.
        recommendations: List of recommendations for improvement.
    """

    model_config = ConfigDict(extra="forbid")

    patterns: list[LanguagePattern] = Field(
        default_factory=list, description="Detected language patterns"
    )
    overall_bias_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall bias score"
    )
    biased_phrases_count: int = Field(
        default=0, ge=0, description="Total biased phrases detected"
    )
    text_analyzed: str = Field(default="", description="Original text analyzed")
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations for improvement"
    )


# ---------------------------------------------------------------------------
# Fairness Scoring
# ---------------------------------------------------------------------------


class FairnessDimension(BaseModel):
    """A single fairness dimension score.

    Attributes:
        name: Name of the fairness dimension.
        score: Score from 0 to 1 (1 = perfectly fair).
        weight: Weight of this dimension in overall score.
        details: Additional details about the score.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Dimension name")
    score: float = Field(..., ge=0.0, le=1.0, description="Fairness score")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Dimension weight")
    details: dict[str, Any] = Field(default_factory=dict, description="Score details")


class FairnessScore(BaseModel):
    """Comprehensive fairness score across multiple dimensions.

    Attributes:
        overall_score: Weighted overall fairness score (0-1).
        dimensions: Individual dimension scores.
        confidence: Confidence level in the score (0-1).
        methodology: Description of scoring methodology.
        timestamp: When the score was computed.
    """

    model_config = ConfigDict(extra="forbid")

    overall_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall fairness score"
    )
    dimensions: list[FairnessDimension] = Field(
        default_factory=list, description="Individual dimension scores"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence level"
    )
    methodology: str = Field(default="", description="Scoring methodology")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Computation timestamp"
    )


# ---------------------------------------------------------------------------
# Bias Recommendations
# ---------------------------------------------------------------------------


class BiasRecommendation(BaseModel):
    """An actionable recommendation to address detected bias.

    Attributes:
        title: Short title of the recommendation.
        description: Detailed description of the recommendation.
        priority: Priority level for implementation.
        category: Category of the recommendation.
        expected_impact: Expected impact on bias reduction.
        implementation_steps: Steps to implement the recommendation.
        resources: List of helpful resources.
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    priority: RecommendationPriority = Field(
        default=RecommendationPriority.MEDIUM, description="Priority level"
    )
    category: str = Field(default="", description="Recommendation category")
    expected_impact: str = Field(default="", description="Expected impact")
    implementation_steps: list[str] = Field(
        default_factory=list, description="Implementation steps"
    )
    resources: list[str] = Field(default_factory=list, description="Helpful resources")


# ---------------------------------------------------------------------------
# Bias Report
# ---------------------------------------------------------------------------


class HiringDecision(BaseModel):
    """A single hiring decision record.

    Attributes:
        candidate_id: Unique identifier for the candidate.
        decision: The hiring decision outcome.
        demographic_data: Demographic information about the candidate.
        job_id: Identifier for the job position.
        interviewer_id: Identifier for the interviewer.
        notes: Additional notes about the decision.
        timestamp: When the decision was made.
    """

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., description="Candidate identifier")
    decision: DecisionOutcome = Field(..., description="Hiring decision outcome")
    demographic_data: dict[str, str] = Field(
        default_factory=dict, description="Demographic information"
    )
    job_id: str = Field(default="", description="Job position identifier")
    interviewer_id: str = Field(default="", description="Interviewer identifier")
    notes: str = Field(default="", description="Additional notes")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Decision timestamp"
    )


class BiasReport(BaseModel):
    """Comprehensive bias report combining all analysis results.

    Attributes:
        report_id: Unique identifier for the report.
        title: Title of the report.
        description: Description of the report scope.
        demographic_analysis: Results of demographic analysis.
        language_bias: Results of language bias detection.
        fairness_score: Overall fairness score.
        patterns: Detected bias patterns.
        recommendations: Actionable recommendations.
        created_at: When the report was created.
        updated_at: When the report was last updated.
        status: Current status of the report.
        metadata: Additional metadata.
    """

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., description="Unique report identifier")
    title: str = Field(..., description="Report title")
    description: str = Field(default="", description="Report description")
    demographic_analysis: DemographicAnalysisResult = Field(
        default_factory=DemographicAnalysisResult, description="Demographic analysis"
    )
    language_bias: LanguageBiasResult = Field(
        default_factory=LanguageBiasResult, description="Language bias results"
    )
    fairness_score: FairnessScore = Field(
        default_factory=FairnessScore, description="Fairness score"
    )
    patterns: list[dict[str, Any]] = Field(
        default_factory=list, description="Detected bias patterns"
    )
    recommendations: list[BiasRecommendation] = Field(
        default_factory=list, description="Actionable recommendations"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    status: Literal["pending", "in_progress", "completed", "failed"] = Field(
        default="pending", description="Report status"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class CreateReportRequest(BaseModel):
    """Request model for creating a new bias report.

    Attributes:
        title: Title of the report.
        description: Description of the report scope.
        hiring_decisions: List of hiring decisions to analyze.
        job_descriptions: List of job description texts to analyze.
        metadata: Additional metadata.
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200, description="Report title")
    description: str = Field(default="", max_length=2000, description="Report description")
    hiring_decisions: list[HiringDecision] = Field(
        default_factory=list, description="Hiring decisions to analyze"
    )
    job_descriptions: list[str] = Field(
        default_factory=list, description="Job descriptions to analyze"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AnalyzeDemographicsRequest(BaseModel):
    """Request model for demographic analysis.

    Attributes:
        demographic_data: Demographic data to analyze.
        threshold: Disparity threshold for significance.
    """

    model_config = ConfigDict(extra="forbid")

    demographic_data: DemographicData = Field(..., description="Demographic data")
    threshold: float = Field(
        default=0.15, ge=0.0, le=1.0, description="Disparity threshold"
    )


class AnalyzeLanguageRequest(BaseModel):
    """Request model for language bias detection.

    Attributes:
        text: Text to analyze for biased language.
        context: Optional context about the text (e.g., "job_description").
    """

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1, description="Text to analyze")
    context: str = Field(default="", description="Text context")


class AnalyzeFairnessRequest(BaseModel):
    """Request model for fairness scoring.

    Attributes:
        demographic_data: Demographic data for fairness analysis.
        language_patterns: Detected language patterns.
        hiring_decisions: Hiring decisions to evaluate.
    """

    model_config = ConfigDict(extra="forbid")

    demographic_data: DemographicData = Field(..., description="Demographic data")
    language_patterns: list[LanguagePattern] = Field(
        default_factory=list, description="Language patterns"
    )
    hiring_decisions: list[HiringDecision] = Field(
        default_factory=list, description="Hiring decisions"
    )


class AnalyzePatternsRequest(BaseModel):
    """Request model for pattern detection.

    Attributes:
        hiring_decisions: List of hiring decisions to analyze.
        demographic_data: Demographic data for context.
    """

    model_config = ConfigDict(extra="forbid")

    hiring_decisions: list[HiringDecision] = Field(
        ..., description="Hiring decisions to analyze"
    )
    demographic_data: DemographicData = Field(..., description="Demographic data")


class GetRecommendationsRequest(BaseModel):
    """Request model for generating recommendations.

    Attributes:
        demographic_analysis: Demographic analysis results.
        language_bias: Language bias detection results.
        fairness_score: Fairness scoring results.
        patterns: Detected bias patterns.
    """

    model_config = ConfigDict(extra="forbid")

    demographic_analysis: DemographicAnalysisResult = Field(
        ..., description="Demographic analysis results"
    )
    language_bias: LanguageBiasResult = Field(
        ..., description="Language bias results"
    )
    fairness_score: FairnessScore = Field(..., description="Fairness score")
    patterns: list[dict[str, Any]] = Field(
        default_factory=list, description="Detected patterns"
    )


class FullAnalysisRequest(BaseModel):
    """Request model for running the full analysis pipeline.

    Attributes:
        hiring_decisions: List of hiring decisions to analyze.
        job_descriptions: List of job description texts.
        demographic_data: Demographic data for analysis.
    """

    model_config = ConfigDict(extra="forbid")

    hiring_decisions: list[HiringDecision] = Field(
        default_factory=list, description="Hiring decisions"
    )
    job_descriptions: list[str] = Field(
        default_factory=list, description="Job descriptions"
    )
    demographic_data: DemographicData = Field(
        default_factory=DemographicData, description="Demographic data"
    )


class HealthResponse(BaseModel):
    """Health check response model.

    Attributes:
        status: Service status.
        version: Application version.
        timestamp: Response timestamp.
    """

    model_config = ConfigDict(extra="forbid")

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(default="0.1.0", description="Application version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class ErrorResponse(BaseModel):
    """Standard error response model.

    Attributes:
        error: Error type/code.
        message: Human-readable error message.
        details: Additional error details.
    """

    model_config = ConfigDict(extra="forbid")

    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional error details"
    )

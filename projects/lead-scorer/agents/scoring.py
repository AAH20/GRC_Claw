"""Scoring agent — computes multi-dimensional lead scores."""

from __future__ import annotations

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentContext, AgentResult, BaseAgent


class ScoringInput(BaseModel):
    """Input for the Scoring agent."""

    lead_id: str = Field(..., description="Lead identifier")
    company_name: str = Field(..., description="Company name")
    firmographic_score: float = Field(
        ge=0.0, le=100.0,
        description="Company fit score (size, industry, location)",
    )
    technographic_score: float = Field(
        ge=0.0, le=100.0,
        description="Tech stack compatibility score",
    )
    intent_score: float = Field(
        ge=0.0, le=100.0,
        description="Buying intent score",
    )
    engagement_score: float = Field(
        ge=0.0, le=100.0,
        description="Engagement level score",
    )
    timing_score: float = Field(
        ge=0.0, le=100.0,
        description="Timing/readiness score",
    )
    evidence_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Confidence in evidence supporting the scores",
    )


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown by dimension."""

    dimension: str
    score: float = Field(ge=0.0, le=100.0)
    weight: float = Field(ge=0.0, le=1.0)
    weighted_score: float = Field(ge=0.0, le=100.0)
    rationale: str = ""


class ScoringOutput(BaseModel):
    """Output from the Scoring agent."""

    lead_id: str
    total_score: float = Field(ge=0.0, le=100.0)
    grade: str = Field(..., description="Letter grade: A+, A, B+, B, C+, C, D, F")
    breakdown: list[ScoreBreakdown] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    scoring_model: str = "weighted_average"
    timestamp: str = ""
    rationale: str = ""


class ScoringAgent(BaseAgent[ScoringInput, ScoringOutput]):
    """Computes multi-dimensional lead scores.

    Uses weighted scoring across firmographic, technographic, intent,
    engagement, and timing dimensions to produce a 0-100 lead score.
    """

    name = "scoring"
    description = "Computes multi-dimensional lead scores (fit, intent, engagement)"

    # Default scoring weights (must sum to 1.0)
    DEFAULT_WEIGHTS: dict[str, float] = {
        "firmographic": 0.25,
        "technographic": 0.15,
        "intent": 0.20,
        "engagement": 0.30,
        "timing": 0.10,
    }

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        default_config = AgentConfig(
            enabled=True,
            timeout_seconds=30.0,
            max_retries=1,
        )
        if config:
            default_config = config
        super().__init__(llm=llm, config=default_config)
        self.weights = weights or self.DEFAULT_WEIGHTS

    @property
    def input_model(self) -> type[ScoringInput]:
        return ScoringInput

    @property
    def output_model(self) -> type[ScoringOutput]:
        return ScoringOutput

    async def run(
        self, input_data: ScoringInput, context: AgentContext
    ) -> AgentResult[ScoringOutput]:
        """Compute the lead score.

        Args:
            input_data: Dimension scores and metadata.
            context: Execution context.

        Returns:
            Scoring output with total score, grade, and breakdown.
        """
        try:
            breakdown = self._compute_breakdown(input_data)
            total_score = sum(item.weighted_score for item in breakdown)
            total_score = max(0.0, min(100.0, total_score))

            grade = self._score_to_grade(total_score)
            confidence = self._compute_confidence(input_data)

            output = ScoringOutput(
                lead_id=input_data.lead_id,
                total_score=round(total_score, 2),
                grade=grade,
                breakdown=breakdown,
                confidence=round(confidence, 2),
                scoring_model="weighted_average",
                timestamp=context.metadata.get("timestamp", ""),
                rationale=self._build_rationale(breakdown, total_score),
            )
            return AgentResult(success=True, data=output)

        except Exception as exc:
            return AgentResult(
                success=False,
                error=f"Scoring failed: {exc}",
            )

    def _compute_breakdown(self, data: ScoringInput) -> list[ScoreBreakdown]:
        """Compute weighted score breakdown.

        Args:
            data: Input dimension scores.

        Returns:
            List of score breakdowns per dimension.
        """
        dimensions = {
            "firmographic": data.firmographic_score,
            "technographic": data.technographic_score,
            "intent": data.intent_score,
            "engagement": data.engagement_score,
            "timing": data.timing_score,
        }

        breakdown: list[ScoreBreakdown] = []
        for dim_name, score in dimensions.items():
            weight = self.weights.get(dim_name, 0.0)
            breakdown.append(
                ScoreBreakdown(
                    dimension=dim_name,
                    score=score,
                    weight=weight,
                    weighted_score=round(score * weight, 2),
                    rationale=f"{dim_name.title()} score of {score} with weight {weight}",
                )
            )
        return breakdown

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade.

        Args:
            score: Numeric score (0-100).

        Returns:
            Letter grade string.
        """
        if score >= 95:
            return "A+"
        if score >= 85:
            return "A"
        if score >= 75:
            return "B+"
        if score >= 65:
            return "B"
        if score >= 55:
            return "C+"
        if score >= 45:
            return "C"
        if score >= 35:
            return "D"
        return "F"

    def _compute_confidence(self, data: ScoringInput) -> float:
        """Compute overall confidence in the score.

        Args:
            data: Input data with evidence confidence.

        Returns:
            Confidence score between 0 and 1.
        """
        # Base confidence on evidence confidence and score variance
        base = data.evidence_confidence
        scores = [
            data.firmographic_score,
            data.technographic_score,
            data.intent_score,
            data.engagement_score,
            data.timing_score,
        ]
        if scores:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            # Lower variance = higher confidence
            variance_factor = max(0.5, 1.0 - (variance / 2500.0))
            return round(base * variance_factor, 2)
        return base

    def _build_rationale(
        self, breakdown: list[ScoreBreakdown], total: float
    ) -> str:
        """Build human-readable scoring rationale.

        Args:
            breakdown: Score breakdown list.
            total: Total weighted score.

        Returns:
            Rationale string.
        """
        top_dims = sorted(breakdown, key=lambda x: x.weighted_score, reverse=True)[:2]
        top_names = ", ".join(d.dimension for d in top_dims)
        return (
            f"Total score {total:.1f}/100. "
            f"Strongest dimensions: {top_names}. "
            f"Score based on weighted average of {len(breakdown)} dimensions."
        )

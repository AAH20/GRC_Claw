"""Scoring agent for computing weighted lead scores."""

from __future__ import annotations

import time
from datetime import UTC
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from lead_scorer.agents.evidence import EvidenceResult
    from lead_scorer.agents.research import ResearchResult


logger = structlog.get_logger(__name__)


class LeadGrade(StrEnum):
    """Lead grade based on score."""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class ScoreComponent(BaseModel):
    """A single score component with weight and value."""

    name: str
    weight: float = Field(ge=0.0, le=1.0)
    raw_score: float = Field(ge=0.0, le=1.0)
    weighted_score: float = Field(ge=0.0, le=1.0)
    details: dict[str, Any] = Field(default_factory=dict)


class ScoringResult(BaseModel):
    """Result from the scoring agent."""

    lead_id: str
    total_score: float = Field(ge=0.0, le=100.0)
    grade: LeadGrade
    components: list[ScoreComponent] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    scored_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoringAgent:
    """Agent responsible for computing weighted lead scores.

    Combines firmographic, technographic, engagement, intent, and timing
    signals into a single 0-100 lead score.
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        thresholds: dict[str, int] | None = None,
        timeout_seconds: int = 30,
        max_retries: int = 1,
    ) -> None:
        """Initialize the scoring agent.

        Args:
            weights: Score component weights. Must sum to 1.0.
            thresholds: Grade thresholds (hot, warm, cold).
            timeout_seconds: Maximum time allowed for scoring.
            max_retries: Number of retry attempts on failure.
        """
        self.weights = weights or {
            "firmographic": 0.25,
            "technographic": 0.15,
            "engagement": 0.30,
            "intent": 0.20,
            "timing": 0.10,
        }
        self.thresholds = thresholds or {"hot": 80, "warm": 50, "cold": 0}
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._validate_weights()

    def _validate_weights(self) -> None:
        """Validate that weights sum to approximately 1.0."""
        total = sum(self.weights.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Score weights must sum to 1.0, got {total}")

    async def score(
        self,
        lead_id: str,
        research: ResearchResult | None = None,
        evidence: EvidenceResult | None = None,
    ) -> ScoringResult:
        """Compute a lead score.

        Args:
            lead_id: Unique identifier for the lead.
            research: Optional research result for firmographic/technographic data.
            evidence: Optional evidence result for engagement/intent data.

        Returns:
            ScoringResult with total score, grade, and component breakdown.

        Raises:
            ValueError: If lead_id is empty.
            TimeoutError: If scoring exceeds timeout.
        """
        if not lead_id:
            raise ValueError("lead_id is required")

        logger.info("scoring_lead", lead_id=lead_id)
        start_time = time.monotonic()

        try:
            components = self._compute_components(research, evidence)
            total_score = sum(c.weighted_score * 100 for c in components)
            total_score = round(min(max(total_score, 0.0), 100.0), 2)

            grade = self._determine_grade(total_score)
            confidence = self._compute_confidence(research, evidence)

            elapsed = time.monotonic() - start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(f"Scoring timed out after {elapsed:.1f}s")

            from datetime import datetime

            result = ScoringResult(
                lead_id=lead_id,
                total_score=total_score,
                grade=grade,
                components=components,
                confidence=confidence,
                scored_at=datetime.now(UTC).isoformat(),
                metadata={"elapsed_seconds": elapsed},
            )

            logger.info(
                "lead_scored",
                lead_id=lead_id,
                score=total_score,
                grade=grade.value,
                confidence=confidence,
            )
            return result

        except Exception as exc:
            logger.error("scoring_failed", lead_id=lead_id, error=str(exc))
            raise

    def _compute_components(
        self,
        research: ResearchResult | None,
        evidence: EvidenceResult | None,
    ) -> list[ScoreComponent]:
        """Compute individual score components."""
        components: list[ScoreComponent] = []

        # Firmographic component
        firm_score = 0.0
        firm_details: dict[str, Any] = {}
        if research:
            firm = research.firmographic
            if firm.company_size > 0:
                # Score based on company size (larger = higher score, capped)
                firm_score += min(firm.company_size / 500, 1.0) * 0.4
                firm_details["size_score"] = min(firm.company_size / 500, 1.0)
            if firm.industry:
                firm_score += 0.3
                firm_details["has_industry"] = True
            if firm.revenue_range:
                firm_score += 0.3
                firm_details["has_revenue"] = True
        components.append(
            ScoreComponent(
                name="firmographic",
                weight=self.weights["firmographic"],
                raw_score=min(firm_score, 1.0),
                weighted_score=min(firm_score, 1.0) * self.weights["firmographic"],
                details=firm_details,
            )
        )

        # Technographic component
        tech_score = 0.0
        tech_details: dict[str, Any] = {}
        if research:
            tech = research.technographic
            if tech.technologies:
                tech_score += min(len(tech.technologies) / 5, 1.0) * 0.5
                tech_details["tech_count"] = len(tech.technologies)
            if tech.ssl_enabled:
                tech_score += 0.2
                tech_details["ssl"] = True
            if tech.hosting_provider:
                tech_score += 0.3
                tech_details["hosting"] = tech.hosting_provider
        components.append(
            ScoreComponent(
                name="technographic",
                weight=self.weights["technographic"],
                raw_score=min(tech_score, 1.0),
                weighted_score=min(tech_score, 1.0) * self.weights["technographic"],
                details=tech_details,
            )
        )

        # Engagement component
        eng_score = 0.0
        eng_details: dict[str, Any] = {}
        if evidence:
            eng_score = evidence.engagement_score
            eng_details["total_events"] = evidence.total_engagements
            eng_details["recency_score"] = evidence.recency_score
        components.append(
            ScoreComponent(
                name="engagement",
                weight=self.weights["engagement"],
                raw_score=eng_score,
                weighted_score=eng_score * self.weights["engagement"],
                details=eng_details,
            )
        )

        # Intent component
        intent_score = 0.0
        intent_details: dict[str, Any] = {}
        if evidence:
            intent_score = evidence.intent_score
            intent_details["signal_count"] = len(evidence.intent_signals)
        components.append(
            ScoreComponent(
                name="intent",
                weight=self.weights["intent"],
                raw_score=intent_score,
                weighted_score=intent_score * self.weights["intent"],
                details=intent_details,
            )
        )

        # Timing component (placeholder - would use lead age, funnel stage)
        timing_score = 0.5
        components.append(
            ScoreComponent(
                name="timing",
                weight=self.weights["timing"],
                raw_score=timing_score,
                weighted_score=timing_score * self.weights["timing"],
                details={"note": "default timing score"},
            )
        )

        return components

    def _determine_grade(self, score: float) -> LeadGrade:
        """Determine lead grade from total score."""
        if score >= self.thresholds["hot"]:
            return LeadGrade.HOT
        if score >= self.thresholds["warm"]:
            return LeadGrade.WARM
        return LeadGrade.COLD

    def _compute_confidence(
        self, research: ResearchResult | None, evidence: EvidenceResult | None
    ) -> float:
        """Compute overall confidence in the score."""
        confidences: list[float] = []
        if research:
            confidences.append(research.confidence)
        if evidence:
            # Confidence based on data volume
            event_confidence = min(evidence.total_engagements / 10, 1.0)
            confidences.append(event_confidence)
        if not confidences:
            return 0.0
        return round(sum(confidences) / len(confidences), 2)

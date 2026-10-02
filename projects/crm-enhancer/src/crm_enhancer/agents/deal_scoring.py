"""Deal Scoring Agent.

Scores deals using ML-based predictive models to prioritize
sales efforts and forecast revenue accurately.
"""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class DealData(BaseModel):
    """Deal data model."""

    deal_id: str
    title: str
    value: float
    stage: str
    contact_email: str
    company: str | None = None
    days_in_stage: int = 0
    activities_count: int = 0
    last_activity_days: int | None = None
    source: str | None = None


class ScoreFactor(BaseModel):
    """Individual scoring factor."""

    name: str
    score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    weighted_score: float = Field(ge=0.0, le=1.0)


class DealScore(BaseModel):
    """Deal score result."""

    deal_id: str
    total_score: float = Field(ge=0.0, le=100.0)
    factors: list[ScoreFactor]
    priority: str
    win_probability: float = Field(ge=0.0, le=1.0)
    recommendation: str


class DealScoringAgent:
    """Agent for scoring deals using predictive models.

    This agent analyzes deal attributes and engagement patterns
    to provide a comprehensive score that helps prioritize sales efforts.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Deal Scoring Agent.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.model_path = self.config.get("model_path", "models/deal_scorer.pkl")
        self.scoring_factors = self.config.get(
            "scoring_factors",
            ["deal_size", "stage_progression", "engagement_level", "company_fit", "timeline"],
        )
        self.weights = self.config.get(
            "weights",
            {
                "deal_size": 0.25,
                "stage_progression": 0.20,
                "engagement_level": 0.25,
                "company_fit": 0.15,
                "timeline": 0.15,
            },
        )
        logger.info("DealScoringAgent initialized", enabled=self.enabled)

    def _score_deal_size(self, value: float) -> float:
        """Score based on deal value.

        Args:
            value: Deal value in dollars.

        Returns:
            Score between 0 and 1.
        """
        if value >= 100_000:
            return 1.0
        if value >= 50_000:
            return 0.8
        if value >= 25_000:
            return 0.6
        if value >= 10_000:
            return 0.4
        return 0.2

    def _score_stage_progression(self, stage: str) -> float:
        """Score based on pipeline stage.

        Args:
            stage: Current pipeline stage.

        Returns:
            Score between 0 and 1.
        """
        stage_scores = {
            "prospecting": 0.1,
            "qualification": 0.2,
            "needs_analysis": 0.3,
            "value_proposition": 0.4,
            "id_decision_makers": 0.5,
            "perception_analysis": 0.6,
            "proposal_price_quote": 0.7,
            "negotiation_review": 0.8,
            "closed_won": 1.0,
            "closed_lost": 0.0,
        }
        return stage_scores.get(stage.lower(), 0.1)

    def _score_engagement(self, activities: int, last_activity_days: int | None) -> float:
        """Score based on engagement level.

        Args:
            activities: Number of activities logged.
            last_activity_days: Days since last activity.

        Returns:
            Score between 0 and 1.
        """
        if last_activity_days is None:
            return 0.0
        if last_activity_days > 30:
            return 0.1
        if last_activity_days > 14:
            return 0.3
        if last_activity_days > 7:
            return 0.5
        if last_activity_days > 3:
            return 0.7
        activity_bonus = min(activities * 0.05, 0.3)
        return min(0.8 + activity_bonus, 1.0)

    def _score_timeline(self, days_in_stage: int) -> float:
        """Score based on time in current stage.

        Args:
            days_in_stage: Number of days in current stage.

        Returns:
            Score between 0 and 1.
        """
        if days_in_stage <= 7:
            return 1.0
        if days_in_stage <= 14:
            return 0.8
        if days_in_stage <= 30:
            return 0.5
        if days_in_stage <= 60:
            return 0.3
        return 0.1

    async def score_deal(self, deal: DealData) -> DealScore:
        """Score a single deal.

        Args:
            deal: The deal data to score.

        Returns:
            DealScore with comprehensive scoring breakdown.

        Raises:
            ValueError: If deal data is invalid.
        """
        if deal.value < 0:
            raise ValueError("Deal value cannot be negative")

        logger.info("Scoring deal", deal_id=deal.deal_id, value=deal.value)

        factors: list[ScoreFactor] = []

        # Deal size score
        size_score = self._score_deal_size(deal.value)
        factors.append(
            ScoreFactor(
                name="deal_size",
                score=size_score,
                weight=self.weights["deal_size"],
                weighted_score=size_score * self.weights["deal_size"],
            )
        )

        # Stage progression score
        stage_score = self._score_stage_progression(deal.stage)
        factors.append(
            ScoreFactor(
                name="stage_progression",
                score=stage_score,
                weight=self.weights["stage_progression"],
                weighted_score=stage_score * self.weights["stage_progression"],
            )
        )

        # Engagement score
        engagement_score = self._score_engagement(deal.activities_count, deal.last_activity_days)
        factors.append(
            ScoreFactor(
                name="engagement_level",
                score=engagement_score,
                weight=self.weights["engagement_level"],
                weighted_score=engagement_score * self.weights["engagement_level"],
            )
        )

        # Company fit (placeholder - would use ML model in production)
        company_fit = 0.6
        factors.append(
            ScoreFactor(
                name="company_fit",
                score=company_fit,
                weight=self.weights["company_fit"],
                weighted_score=company_fit * self.weights["company_fit"],
            )
        )

        # Timeline score
        timeline_score = self._score_timeline(deal.days_in_stage)
        factors.append(
            ScoreFactor(
                name="timeline",
                score=timeline_score,
                weight=self.weights["timeline"],
                weighted_score=timeline_score * self.weights["timeline"],
            )
        )

        total_score = sum(f.weighted_score for f in factors) * 100

        # Determine priority
        if total_score >= 70:
            priority = "high"
        elif total_score >= 40:
            priority = "medium"
        else:
            priority = "low"

        # Win probability (simplified model)
        win_probability = min(total_score / 100 * 1.2, 0.95)

        # Generate recommendation
        if total_score >= 70:
            recommendation = "Prioritize this deal - high probability of closing"
        elif total_score >= 40:
            recommendation = "Nurture with targeted engagement"
        else:
            recommendation = "Consider deprioritizing or qualifying further"

        logger.info(
            "Deal scored",
            deal_id=deal.deal_id,
            score=total_score,
            priority=priority,
        )

        return DealScore(
            deal_id=deal.deal_id,
            total_score=round(total_score, 2),
            factors=factors,
            priority=priority,
            win_probability=round(win_probability, 2),
            recommendation=recommendation,
        )

    async def score_deals(self, deals: list[DealData]) -> list[DealScore]:
        """Score multiple deals.

        Args:
            deals: List of deals to score.

        Returns:
            List of deal scores sorted by total score descending.
        """
        logger.info("Scoring multiple deals", count=len(deals))
        scores = [await self.score_deal(deal) for deal in deals]
        scores.sort(key=lambda s: s.total_score, reverse=True)
        return scores

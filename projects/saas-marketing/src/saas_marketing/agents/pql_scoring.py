"""Product-Qualified Lead (PQL) scoring agent."""

from __future__ import annotations

from enum import StrEnum

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class PQLTier(StrEnum):
    """PQL qualification tiers."""

    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    SQL = "sql"


class UserBehavior(BaseModel):
    """User behavioral signals for PQL scoring."""

    user_id: str = Field(..., description="Unique user identifier")
    feature_usage_count: int = Field(default=0, description="Number of features used")
    total_sessions: int = Field(default=0, description="Total sessions in lookback period")
    avg_session_duration_seconds: float = Field(default=0.0, description="Average session duration")
    days_since_signup: int = Field(default=0, description="Days since account creation")
    key_actions_completed: list[str] = Field(
        default_factory=list, description="Key product actions"
    )
    team_size: int = Field(default=1, description="Number of team members invited")
    billing_page_visits: int = Field(default=0, description="Number of billing page visits")
    integration_attempts: int = Field(default=0, description="Number of integration attempts")
    nps_score: int | None = Field(default=None, description="NPS score if available")


class PQLScore(BaseModel):
    """PQL scoring result."""

    user_id: str = Field(..., description="User identifier")
    score: float = Field(..., ge=0, le=100, description="PQL score from 0-100")
    tier: PQLTier = Field(..., description="Qualification tier")
    signals: dict[str, float] = Field(default_factory=dict, description="Individual signal scores")
    recommendation: str = Field(..., description="Recommended action")
    confidence: float = Field(default=0.8, ge=0, le=1, description="Confidence in scoring")


class PQLScoringAgent:
    """Agent that scores product-qualified leads based on behavioral signals.

    Uses weighted scoring across feature usage, engagement, profile fit,
    and intent signals to determine lead qualification.
    """

    DEFAULT_WEIGHTS = {
        "feature_usage": 0.35,
        "engagement": 0.25,
        "profile_fit": 0.20,
        "intent_signals": 0.20,
    }

    TIER_THRESHOLDS = {
        PQLTier.COLD: 0,
        PQLTier.WARM: 40,
        PQLTier.HOT: 70,
        PQLTier.SQL: 85,
    }

    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.3,
        scoring_threshold: float = 70.0,
        weights: dict[str, float] | None = None,
    ) -> None:
        """Initialize the PQLScoringAgent.

        Args:
            model: LLM model identifier.
            temperature: Sampling temperature.
            scoring_threshold: Minimum score to consider a lead qualified.
            weights: Custom signal weights (must sum to 1.0).
        """
        self.model = model
        self.temperature = temperature
        self.scoring_threshold = scoring_threshold
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._validate_weights()
        logger.info("pql_scoring_agent_initialized", threshold=scoring_threshold)

    async def score(self, behavior: UserBehavior) -> PQLScore:
        """Calculate PQL score for a user based on behavioral signals.

        Args:
            behavior: User behavioral data.

        Returns:
            PQL score with tier and recommendation.
        """
        logger.info("scoring_user", user_id=behavior.user_id)

        signals = self._calculate_signals(behavior)
        total_score = sum(
            signals[key] * self.weights[key] for key in self.weights
        )
        total_score = min(100.0, max(0.0, total_score))

        tier = self._determine_tier(total_score)
        recommendation = self._generate_recommendation(tier, behavior)

        logger.info(
            "user_scored",
            user_id=behavior.user_id,
            score=total_score,
            tier=tier.value,
        )

        return PQLScore(
            user_id=behavior.user_id,
            score=round(total_score, 2),
            tier=tier,
            signals=signals,
            recommendation=recommendation,
            confidence=self._calculate_confidence(behavior),
        )

    def _validate_weights(self) -> None:
        """Validate that signal weights sum to approximately 1.0.

        Raises:
            ValueError: If weights don't sum to 1.0.
        """
        total = sum(self.weights.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Signal weights must sum to 1.0, got {total}")

    def _calculate_signals(self, behavior: UserBehavior) -> dict[str, float]:
        """Calculate individual signal scores from 0-100.

        Args:
            behavior: User behavioral data.

        Returns:
            Dictionary of signal names to scores.
        """
        feature_usage_score = min(100.0, behavior.feature_usage_count * 10)

        engagement_score = min(
            100.0,
            (behavior.total_sessions * 5)
            + (behavior.avg_session_duration_seconds / 60 * 2),
        )

        profile_fit_score = min(
            100.0,
            (behavior.team_size * 15)
            + (50 if behavior.days_since_signup > 7 else 0),
        )

        intent_score = min(
            100.0,
            (behavior.billing_page_visits * 20)
            + (behavior.integration_attempts * 15)
            + (len(behavior.key_actions_completed) * 10),
        )

        return {
            "feature_usage": feature_usage_score,
            "engagement": engagement_score,
            "profile_fit": profile_fit_score,
            "intent_signals": intent_score,
        }

    def _determine_tier(self, score: float) -> PQLTier:
        """Determine PQL tier from score.

        Args:
            score: Calculated PQL score.

        Returns:
            Appropriate PQL tier.
        """
        if score >= self.TIER_THRESHOLDS[PQLTier.SQL]:
            return PQLTier.SQL
        if score >= self.TIER_THRESHOLDS[PQLTier.HOT]:
            return PQLTier.HOT
        if score >= self.TIER_THRESHOLDS[PQLTier.WARM]:
            return PQLTier.WARM
        return PQLTier.COLD

    def _generate_recommendation(self, tier: PQLTier, behavior: UserBehavior) -> str:
        """Generate a recommendation based on tier and behavior.

        Args:
            tier: Determined PQL tier.
            behavior: User behavioral data.

        Returns:
            Human-readable recommendation.
        """
        recommendations = {
            PQLTier.SQL: (
                f"High-intent lead. Route to sales immediately. "
                f"User has completed {len(behavior.key_actions_completed)} key actions."
            ),
            PQLTier.HOT: (
                "Strong product-qualified lead. Trigger personalized onboarding "
                "and schedule a demo."
            ),
            PQLTier.WARM: (
                "Showing engagement. Send targeted feature education content "
                "and in-app guidance."
            ),
            PQLTier.COLD: (
                "Early-stage user. Focus on activation campaigns and "
                "product education."
            ),
        }
        return recommendations[tier]

    def _calculate_confidence(self, behavior: UserBehavior) -> float:
        """Calculate confidence in the scoring result.

        More data points = higher confidence.

        Args:
            behavior: User behavioral data.

        Returns:
            Confidence score from 0 to 1.
        """
        data_points = sum([
            behavior.feature_usage_count > 0,
            behavior.total_sessions > 0,
            behavior.days_since_signup > 0,
            len(behavior.key_actions_completed) > 0,
            behavior.team_size > 0,
        ])
        return min(1.0, 0.3 + (data_points * 0.14))

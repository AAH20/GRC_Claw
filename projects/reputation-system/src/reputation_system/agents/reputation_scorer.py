"""Reputation Scorer Agent for calculating member reputation scores."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from reputation_system.agents.base import BaseAgent
from reputation_system.models.schemas import ReputationScore, TrustTierLevel


class ScoringInput(BaseModel):
    """Input for reputation scoring."""

    member_id: str = Field(..., description="Member identifier")
    contributions: int = Field(default=0, description="Total contributions")
    positive_feedback: int = Field(default=0, description="Positive feedback count")
    negative_feedback: int = Field(default=0, description="Negative feedback count")
    account_age_days: int = Field(default=0, description="Account age in days")
    badge_count: int = Field(default=0, description="Number of badges earned")
    recent_activity_score: float = Field(default=0.0, description="Recent activity score (0-1)")
    quality_score: float = Field(default=0.0, description="Quality score (0-1)")


class ScoringOutput(BaseModel):
    """Output from reputation scoring."""

    member_id: str
    score: int = Field(..., ge=0, le=1000)
    trust_tier: TrustTierLevel
    factors: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ReputationScorerAgent(BaseAgent[ScoringInput, ScoringOutput]):
    """Agent that calculates reputation scores using AI-powered analysis."""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the reputation scorer."""
        return """You are a reputation scoring agent. Your task is to calculate
        a member's reputation score based on their contributions, feedback, and activity.
        The score ranges from 0 to 1000. Consider all factors and provide a fair assessment.
        Return the score, trust tier, and factors that influenced the decision."""

    async def run(self, input_data: ScoringInput) -> ScoringOutput:
        """Calculate reputation score for a member.

        Args:
            input_data: Scoring input data.

        Returns:
            Calculated reputation score with factors.
        """
        # Weighted scoring algorithm
        contribution_weight = 0.35
        feedback_weight = 0.25
        activity_weight = 0.20
        quality_weight = 0.15
        badge_weight = 0.05

        # Calculate component scores (0-1000 scale)
        contribution_score = min(input_data.contributions * 10, 400)
        feedback_ratio = (
            input_data.positive_feedback
            / max(input_data.positive_feedback + input_data.negative_feedback, 1)
        )
        feedback_score = feedback_ratio * 250
        activity_score = input_data.recent_activity_score * 200
        quality_score = input_data.quality_score * 150
        badge_score = min(input_data.badge_count * 5, 50)

        # Weighted total
        total_score = int(
            contribution_score * contribution_weight
            + feedback_score * feedback_weight
            + activity_score * activity_weight
            + quality_score * quality_weight
            + badge_score * badge_weight
        )

        # Clamp to valid range
        total_score = max(0, min(total_score, 1000))

        # Determine trust tier
        trust_tier = self._determine_trust_tier(total_score)

        # Build factors
        factors = [
            {"name": "contributions", "value": input_data.contributions, "impact": contribution_score * contribution_weight},
            {"name": "feedback_ratio", "value": feedback_ratio, "impact": feedback_score * feedback_weight},
            {"name": "activity", "value": input_data.recent_activity_score, "impact": activity_score * activity_weight},
            {"name": "quality", "value": input_data.quality_score, "impact": quality_score * quality_weight},
            {"name": "badges", "value": input_data.badge_count, "impact": badge_score * badge_weight},
        ]

        # Confidence based on data completeness
        confidence = min(
            0.3
            + (0.1 if input_data.contributions > 0 else 0)
            + (0.1 if input_data.positive_feedback > 0 else 0)
            + (0.1 if input_data.account_age_days > 30 else 0)
            + (0.1 if input_data.badge_count > 0 else 0)
            + (0.1 if input_data.recent_activity_score > 0 else 0)
            + (0.1 if input_data.quality_score > 0 else 0),
            1.0,
        )

        return ScoringOutput(
            member_id=input_data.member_id,
            score=total_score,
            trust_tier=trust_tier,
            factors=factors,
            confidence=confidence,
        )

    def _determine_trust_tier(self, score: int) -> TrustTierLevel:
        """Determine trust tier based on score.

        Args:
            score: Reputation score.

        Returns:
            Trust tier level.
        """
        if score >= 900:
            return TrustTierLevel.DIAMOND
        elif score >= 700:
            return TrustTierLevel.PLATINUM
        elif score >= 500:
            return TrustTierLevel.GOLD
        elif score >= 300:
            return TrustTierLevel.SILVER
        return TrustTierLevel.BRONZE

"""Reputation Explainer Agent for generating human-readable reputation explanations."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from reputation_system.agents.base import BaseAgent
from reputation_system.models.schemas import ReputationExplanation, TrustTierLevel


class ExplanationInput(BaseModel):
    """Input for reputation explanation generation."""

    member_id: str = Field(..., description="Member identifier")
    current_score: int = Field(..., ge=0, le=1000, description="Current reputation score")
    trust_tier: TrustTierLevel = Field(..., description="Current trust tier")
    factors: List[Dict[str, Any]] = Field(..., description="Scoring factors")
    recent_actions: List[Dict[str, Any]] = Field(default_factory=list, description="Recent actions")
    badge_count: int = Field(default=0, description="Number of badges")
    account_age_days: int = Field(default=0, description="Account age in days")


class ExplanationOutput(BaseModel):
    """Output from explanation generation."""

    member_id: str
    explanation: str = Field(..., max_length=5000)
    factors: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ReputationExplainerAgent(BaseAgent[ExplanationInput, ExplanationOutput]):
    """Agent that generates human-readable explanations of reputation scores."""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the reputation explainer."""
        return """You are a reputation explanation agent. Your task is to generate
        clear, human-readable explanations of a member's reputation score. Explain
        the factors that contributed to the score, provide actionable recommendations
        for improvement, and set appropriate expectations."""

    async def run(self, input_data: ExplanationInput) -> ExplanationOutput:
        """Generate a reputation explanation for a member.

        Args:
            input_data: Explanation input data.

        Returns:
            Human-readable reputation explanation.
        """
        explanation = self._build_explanation(input_data)
        recommendations = self._generate_recommendations(input_data)
        confidence = self._calculate_confidence(input_data)

        return ExplanationOutput(
            member_id=input_data.member_id,
            explanation=explanation,
            factors=input_data.factors,
            recommendations=recommendations,
            confidence=confidence,
        )

    def _build_explanation(self, data: ExplanationInput) -> str:
        """Build a human-readable explanation.

        Args:
            data: Explanation input data.

        Returns:
            Explanation text.
        """
        parts: List[str] = []

        # Overview
        parts.append(
            f"Member {data.member_id} has a reputation score of {data.current_score}/1000, "
            f"placing them in the {data.trust_tier.value.upper()} trust tier."
        )

        # Factor breakdown
        if data.factors:
            parts.append("\nKey factors influencing this score:")
            for factor in data.factors:
                name = factor.get("name", "unknown")
                value = factor.get("value", 0)
                impact = factor.get("impact", 0)
                parts.append(f"  - {name}: {value} (impact: {impact:.1f} points)")

        # Badge info
        if data.badge_count > 0:
            parts.append(f"\nThe member has earned {data.badge_count} badge(s).")

        # Account age
        if data.account_age_days > 0:
            parts.append(f"Account age: {data.account_age_days} days")

        # Recent activity summary
        if data.recent_actions:
            positive = sum(1 for a in data.recent_actions if a.get("score_change", 0) > 0)
            negative = sum(1 for a in data.recent_actions if a.get("score_change", 0) < 0)
            parts.append(
                f"\nRecent activity: {positive} positive, {negative} negative actions"
            )

        return "\n".join(parts)

    def _generate_recommendations(self, data: ExplanationInput) -> List[str]:
        """Generate improvement recommendations.

        Args:
            data: Explanation input data.

        Returns:
            List of recommendations.
        """
        recommendations: List[str] = []

        if data.current_score < 300:
            recommendations.append("Focus on increasing contributions to improve your score")
            recommendations.append("Engage positively with the community")
        elif data.current_score < 500:
            recommendations.append("Continue consistent contributions to reach Gold tier")
            recommendations.append("Maintain positive feedback ratio")
        elif data.current_score < 700:
            recommendations.append("Verify your identity to unlock Platinum tier benefits")
            recommendations.append("Mentor other members to increase your impact")
        elif data.current_score < 900:
            recommendations.append("Maintain your excellent standing")
            recommendations.append("Consider applying for Diamond tier verification")

        if data.badge_count < 3:
            recommendations.append("Earn more badges to boost your reputation")

        return recommendations

    def _calculate_confidence(self, data: ExplanationInput) -> float:
        """Calculate confidence in the explanation.

        Args:
            data: Explanation input data.

        Returns:
            Confidence score between 0 and 1.
        """
        confidence = 0.5

        if data.factors:
            confidence += 0.2
        if data.recent_actions:
            confidence += 0.15
        if data.account_age_days > 30:
            confidence += 0.1
        if data.badge_count > 0:
            confidence += 0.05

        return min(confidence, 1.0)

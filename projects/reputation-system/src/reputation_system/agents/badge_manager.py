"""Badge Manager Agent for managing member badges."""

from typing import Any

from pydantic import BaseModel, Field

from reputation_system.agents.base import BaseAgent


class BadgeEvaluationInput(BaseModel):
    """Input for badge evaluation."""

    member_id: str = Field(..., description="Member identifier")
    badge_criteria: dict[str, Any] = Field(..., description="Badge criteria to evaluate")
    member_stats: dict[str, Any] = Field(..., description="Member statistics")
    current_badges: list[str] = Field(default_factory=list, description="Current badge IDs")


class BadgeEvaluationOutput(BaseModel):
    """Output from badge evaluation."""

    member_id: str
    eligible_badges: list[dict[str, Any]] = Field(default_factory=list)
    revoked_badges: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class BadgeManagerAgent(BaseAgent[BadgeEvaluationInput, BadgeEvaluationOutput]):
    """Agent that manages badge assignment, revocation, and recommendations."""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the badge manager."""
        return """You are a badge management agent. Your task is to evaluate
        whether a member qualifies for badges based on their statistics and criteria.
        Assign appropriate badges, revoke ineligible ones, and provide recommendations
        for future badge earning opportunities."""

    async def run(self, input_data: BadgeEvaluationInput) -> BadgeEvaluationOutput:
        """Evaluate and manage badges for a member.

        Args:
            input_data: Badge evaluation input data.

        Returns:
            Badge evaluation results with eligible and revoked badges.
        """
        eligible_badges: list[dict[str, Any]] = []
        revoked_badges: list[str] = []
        recommendations: list[str] = []

        for criterion_name, criterion in input_data.badge_criteria.items():
            is_eligible = self._evaluate_criterion(criterion, input_data.member_stats)

            if is_eligible and criterion_name not in input_data.current_badges:
                eligible_badges.append({
                    "name": criterion_name,
                    "category": criterion.get("category", "contribution"),
                    "points": criterion.get("points", 10),
                    "description": criterion.get("description", ""),
                })
            elif not is_eligible and criterion_name in input_data.current_badges:
                revoked_badges.append(criterion_name)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            input_data.member_stats, input_data.badge_criteria
        )

        return BadgeEvaluationOutput(
            member_id=input_data.member_id,
            eligible_badges=eligible_badges,
            revoked_badges=revoked_badges,
            recommendations=recommendations,
        )

    def _evaluate_criterion(
        self, criterion: dict[str, Any], stats: dict[str, Any]
    ) -> bool:
        """Evaluate if a member meets a badge criterion.

        Args:
            criterion: Badge criteria.
            stats: Member statistics.

        Returns:
            True if the member meets the criterion.
        """
        metric = criterion.get("metric")
        threshold = criterion.get("threshold", 0)

        if not metric:
            return False

        value = stats.get(metric, 0)
        return value >= threshold

    def _generate_recommendations(
        self, stats: dict[str, Any], criteria: dict[str, Any]
    ) -> list[str]:
        """Generate badge earning recommendations.

        Args:
            stats: Member statistics.
            criteria: Badge criteria.

        Returns:
            List of recommendations.
        """
        recommendations: list[str] = []

        for criterion_name, criterion in criteria.items():
            metric = criterion.get("metric")
            threshold = criterion.get("threshold", 0)

            if metric and stats.get(metric, 0) < threshold:
                remaining = threshold - stats.get(metric, 0)
                recommendations.append(
                    f"Earn {remaining} more {metric} to unlock {criterion_name} badge"
                )

        return recommendations

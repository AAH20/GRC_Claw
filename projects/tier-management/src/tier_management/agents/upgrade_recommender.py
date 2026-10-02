"""Upgrade Recommender Agent - Recommends tier upgrades for members.

Uses LangChain DeepAgents to analyze member profiles and recommend
appropriate tier upgrades based on activity, value, and potential.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from tier_management.agents.base import BaseAgent
from tier_management.config.logging_config import get_logger
from tier_management.models.schemas import TierLevel, UpgradeEligibility, UpgradeRequest

logger = get_logger(__name__)


class UpgradeRecommenderAgent(BaseAgent[dict[str, Any], UpgradeRequest]):
    """Agent that recommends tier upgrades for community members.

    This agent uses LangChain DeepAgents to analyze member behavior,
    spending patterns, engagement levels, and growth potential to
    recommend optimal tier upgrades that benefit both the member and
    the community.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Upgrade Recommender Agent.

        Args:
            llm: LangChain language model for recommendation reasoning.
            tools: Tools available to the agent.
            **kwargs: Additional configuration parameters.
        """
        super().__init__(name="UpgradeRecommenderAgent", llm=llm, tools=tools, **kwargs)
        self.tier_hierarchy = [
            TierLevel.BRONZE,
            TierLevel.SILVER,
            TierLevel.GOLD,
            TierLevel.PLATINUM,
            TierLevel.DIAMOND,
        ]
        self.min_score_for_upgrade = kwargs.get("min_score_for_upgrade", 75.0)

    async def execute(self, input_data: dict[str, Any]) -> UpgradeRequest:
        """Generate an upgrade recommendation for a member.

        Args:
            input_data: Dictionary containing:
                - member_id: UUID of the member
                - current_tier_id: UUID of member's current tier
                - target_tier_id: UUID of desired tier (optional)
                - member_metrics: Optional member activity data

        Returns:
            UpgradeRequest with eligibility status and recommendation details.

        Raises:
            ValueError: If required fields are missing.
        """
        member_id = input_data.get("member_id")
        current_tier_id = input_data.get("current_tier_id")

        if not member_id or not current_tier_id:
            raise ValueError("member_id and current_tier_id are required")

        logger.info(
            "generating_upgrade_recommendation",
            member_id=str(member_id),
            current_tier=str(current_tier_id),
        )

        recommendation = await self._generate_recommendation(input_data)

        logger.info(
            "upgrade_recommendation_complete",
            member_id=str(member_id),
            eligibility=recommendation.eligibility.value,
        )

        return recommendation

    async def _generate_recommendation(
        self,
        input_data: dict[str, Any],
    ) -> UpgradeRequest:
        """Generate the upgrade recommendation.

        Args:
            input_data: The recommendation input data.

        Returns:
            An UpgradeRequest instance.
        """
        from datetime import datetime, timezone
        from uuid import uuid4

        member_id = input_data["member_id"]
        current_tier_id = input_data["current_tier_id"]
        target_tier_id = input_data.get("target_tier_id")
        metrics = input_data.get("member_metrics", {})

        # Determine eligibility
        eligibility = self._check_eligibility(metrics)

        # If no target specified, recommend next tier
        if not target_tier_id:
            target_tier_id = self._recommend_next_tier(current_tier_id)

        # Build reason
        reason = self._build_reason(eligibility, metrics)

        return UpgradeRequest(
            id=uuid4(),
            member_id=UUID(str(member_id)),
            current_tier_id=UUID(str(current_tier_id)),
            target_tier_id=UUID(str(target_tier_id)) if target_tier_id else current_tier_id,
            reason=reason,
            eligibility=eligibility,
            status="recommended" if eligibility == UpgradeEligibility.ELIGIBLE else "pending",
            requested_at=datetime.now(timezone.utc),
        )

    def _check_eligibility(self, metrics: dict[str, Any]) -> UpgradeEligibility:
        """Check if member is eligible for upgrade.

        Args:
            metrics: Member activity metrics.

        Returns:
            UpgradeEligibility status.
        """
        if not metrics:
            return UpgradeEligibility.NOT_ELIGIBLE

        score = metrics.get("overall_score", 0.0)
        if score >= self.min_score_for_upgrade:
            return UpgradeEligibility.ELIGIBLE

        return UpgradeEligibility.NOT_ELIGIBLE

    def _recommend_next_tier(self, current_tier_id: Any) -> Any:
        """Recommend the next tier in hierarchy.

        Args:
            current_tier_id: Current tier identifier.

        Returns:
            Recommended next tier identifier.
        """
        # In production, this would look up the tier hierarchy
        return current_tier_id

    def _build_reason(
        self,
        eligibility: UpgradeEligibility,
        metrics: dict[str, Any],
    ) -> str:
        """Build human-readable reason for the recommendation.

        Args:
            eligibility: The eligibility status.
            metrics: Member metrics.

        Returns:
            Reason string.
        """
        if eligibility == UpgradeEligibility.ELIGIBLE:
            score = metrics.get("overall_score", 0.0)
            return f"Member qualifies for upgrade with score {score:.1f}"
        return "Member does not currently meet upgrade criteria"

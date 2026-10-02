"""Audience Agent — Audience segmentation and targeting."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from agents.base import AgentContext, AgentResult, BaseAgent
from core.logging import get_logger

logger = get_logger(__name__)


class AudienceAgent(BaseAgent[dict[str, Any]]):
    """Agent responsible for audience segmentation and targeting.

    The Audience Agent identifies high-value audience segments,
    creates lookalike audiences, recommends targeting parameters,
    and optimizes audience performance throughout the campaign.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
    ) -> None:
        """Initialize the Audience Agent.

        Args:
            llm: Language model for audience analysis.
            tools: Available tools for data analysis and web search.
        """
        super().__init__(
            name="Audience Agent",
            description="Audience segmentation, targeting, and lookalike expansion",
            llm=llm,
            tools=tools,
            timeout=120,
            max_iterations=3,
        )

    async def _execute(self, context: AgentContext) -> AgentResult[dict[str, Any]]:
        """Execute audience analysis and targeting for a campaign.

        Args:
            context: Execution context with audience parameters.

        Returns:
            AgentResult containing audience segments and targeting recommendations.
        """
        self._logger.info(
            "audience_analysis_started",
            campaign_id=context.campaign_id,
            task=context.task,
        )

        audience_data = self._analyze_audience(context)

        return AgentResult(
            success=True,
            data=audience_data,
            metadata={
                "agent": self.name,
                "campaign_id": context.campaign_id,
                "segments_count": len(audience_data.get("segments", [])),
            },
        )

    def _analyze_audience(self, context: AgentContext) -> dict[str, Any]:
        """Analyze and segment the target audience.

        Args:
            context: Execution context with audience parameters.

        Returns:
            Dictionary containing audience analysis and targeting data.
        """
        params = context.parameters
        base_audience = params.get("base_audience", {})
        campaign_goals = params.get("goals", [])
        lookalike_seed = params.get("lookalike_seed", [])

        return {
            "campaign_id": context.campaign_id,
            "segments": self._create_segments(base_audience, campaign_goals),
            "lookalike_audiences": self._create_lookalikes(lookalike_seed),
            "targeting_recommendations": self._recommend_targeting(base_audience),
            "exclusion_lists": self._define_exclusions(base_audience),
            "personalization_strategy": self._personalization_strategy(campaign_goals),
        }

    def _create_segments(
        self, base_audience: dict[str, Any], goals: list[str]
    ) -> list[dict[str, Any]]:
        """Create audience segments based on base audience and goals.

        Args:
            base_audience: Base audience parameters.
            goals: Campaign goals.

        Returns:
            List of audience segment definitions.
        """
        segments = []

        # Demographic segments
        demographics = base_audience.get("demographics", {})
        age_ranges = demographics.get("age_ranges", ["25-34", "35-44", "45-54"])
        locations = demographics.get("locations", ["US", "CA", "UK"])

        for age in age_ranges:
            for location in locations[:2]:  # Limit combinations
                segments.append({
                    "name": f"{age}_{location}",
                    "type": "demographic",
                    "criteria": {
                        "age_range": age,
                        "location": location,
                    },
                    "estimated_reach": "calculating",
                    "priority": "high" if age == "25-34" else "medium",
                })

        # Behavioral segments
        segments.extend([
            {
                "name": "high_intent",
                "type": "behavioral",
                "criteria": {
                    "visits": ">=3 in last 7 days",
                    "actions": ["add_to_cart", "initiate_checkout"],
                },
                "estimated_reach": "calculating",
                "priority": "high",
            },
            {
                "name": "cart_abandoners",
                "type": "behavioral",
                "criteria": {
                    "actions": ["add_to_cart"],
                    "recency": "within 14 days",
                    "exclude": ["purchase"],
                },
                "estimated_reach": "calculating",
                "priority": "high",
            },
            {
                "name": "past_customers",
                "type": "behavioral",
                "criteria": {
                    "actions": ["purchase"],
                    "recency": "within 90 days",
                },
                "estimated_reach": "calculating",
                "priority": "medium",
            },
        ])

        # Goal-based segments
        if "awareness" in goals:
            segments.append({
                "name": "prospecting_broad",
                "type": "expansion",
                "criteria": {
                    "strategy": "broad_targeting",
                    "optimization": "reach",
                },
                "estimated_reach": "calculating",
                "priority": "medium",
            })

        return segments

    def _create_lookalikes(self, seed_audiences: list[str]) -> list[dict[str, Any]]:
        """Create lookalike audience configurations.

        Args:
            seed_audiences: List of seed audience identifiers.

        Returns:
            List of lookalike audience configurations.
        """
        lookalikes = []
        for seed in seed_audiences:
            for similarity in [0.01, 0.05, 0.10]:
                lookalikes.append({
                    "name": f"lookalike_{seed}_{int(similarity * 100)}pct",
                    "seed_audience": seed,
                    "similarity": similarity,
                    "estimated_reach": "calculating",
                    "platforms": ["meta", "google"],
                })

        return lookalikes

    def _recommend_targeting(
        self, base_audience: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate targeting recommendations.

        Args:
            base_audience: Base audience parameters.

        Returns:
            Targeting recommendations.
        """
        return {
            "auto_targeting": {
                "enabled": True,
                "expansion": True,
                "optimization_goal": "conversions",
            },
            "manual_overlays": {
                "interests": base_audience.get("interests", []),
                "behaviors": base_audience.get("behaviors", []),
                "custom_audiences": [],
            },
            "bid_adjustments": {
                "high_value_segment": 1.25,
                "medium_value_segment": 1.0,
                "low_value_segment": 0.75,
            },
        }

    def _define_exclusions(self, base_audience: dict[str, Any]) -> list[dict[str, Any]]:
        """Define audience exclusion lists.

        Args:
            base_audience: Base audience parameters.

        Returns:
            List of exclusion configurations.
        """
        return [
            {
                "name": "existing_customers",
                "type": "custom_audience",
                "reason": "avoid_redundancy",
            },
            {
                "name": "recent_converters",
                "type": "behavioral",
                "criteria": {"actions": ["purchase"], "recency": "within 30 days"},
                "reason": "maximize_efficiency",
            },
            {
                "name": "low_engagement",
                "type": "engagement",
                "criteria": {"clicks": 0, "impressions": ">=10", "recency": "within 30 days"},
                "reason": "reduce_waste",
            },
        ]

    def _personalization_strategy(self, goals: list[str]) -> dict[str, Any]:
        """Define personalization strategy based on campaign goals.

        Args:
            goals: Campaign goals.

        Returns:
            Personalization strategy configuration.
        """
        return {
            "dynamic_creative_optimization": True,
            "message_by_segment": {
                "high_intent": "urgency_driven",
                "cart_abandoners": "reminder_driven",
                "past_customers": "loyalty_driven",
                "prospecting": "awareness_driven",
            },
            "creative_personalization": {
                "location": True,
                "device": True,
                "time_of_day": True,
                "weather": False,
            },
            "goal_specific": {
                "awareness": "focus_on_reach_and_frequency",
                "conversion": "focus_on_social_proof_and_urgency",
                "retention": "focus_on_loyalty_benefits",
            },
        }

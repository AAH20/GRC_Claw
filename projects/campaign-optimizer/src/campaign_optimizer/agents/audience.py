"""Audience Agent — Audience segmentation, targeting, and lookalike expansion."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class AudienceType(StrEnum):
    """Types of audiences."""

    CORE = "core"
    LOOKALIKE = "lookalike"
    RETARGETING = "retargeting"
    CUSTOM = "custom"
    SIMILAR = "similar"


class ExpansionLevel(StrEnum):
    """Lookalike expansion levels."""

    NARROW = "narrow"  # 1% lookalike
    BALANCED = "balanced"  # 3% lookalike
    BROAD = "broad"  # 5% lookalike
    WIDE = "wide"  # 10% lookalike


@dataclass
class AudienceSegment:
    """A defined audience segment."""

    segment_id: str
    name: str
    audience_type: AudienceType
    size_estimate: int
    demographics: dict[str, Any] = field(default_factory=dict)
    interests: list[str] = field(default_factory=list)
    behaviors: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    estimated_cpa: float = 0.0
    priority: int = 0


@dataclass
class AudiencePlan:
    """Complete audience targeting plan."""

    campaign_id: str
    segments: list[AudienceSegment] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)
    expansion_recommendations: list[dict[str, Any]] = field(default_factory=list)


class AudienceAgent:
    """Agent responsible for audience segmentation and targeting.

    The Audience Agent identifies high-value audience segments,
    creates lookalike audiences, manages retargeting pools, and
    optimizes audience targeting for maximum campaign performance.
    """

    def __init__(self, model: str = "gpt-4", temperature: float = 0.4) -> None:
        """Initialize the Audience Agent.

        Args:
            model: The LLM model to use for audience analysis.
            temperature: Sampling temperature for the model.
        """
        self.model = model
        self.temperature = temperature
        self._plans: dict[str, AudiencePlan] = {}

    async def build_audience_plan(
        self,
        campaign_id: str,
        product_category: str,
        target_demographics: dict[str, Any],
        customer_data: dict[str, Any] | None = None,
        platforms: list[str] | None = None,
    ) -> AudiencePlan:
        """Build a comprehensive audience targeting plan.

        Args:
            campaign_id: Campaign identifier.
            product_category: Product category for audience matching.
            target_demographics: Target demographic parameters.
            customer_data: Optional existing customer data for lookalikes.
            platforms: Target advertising platforms.

        Returns:
            An AudiencePlan with segments and recommendations.
        """
        platforms = platforms or ["meta", "google", "linkedin"]

        logger.info(
            "Building audience plan",
            campaign_id=campaign_id,
            category=product_category,
        )

        # Create core audience segments
        segments = await self._create_core_segments(
            product_category, target_demographics, platforms
        )

        # Create lookalike audiences if customer data available
        if customer_data:
            lookalikes = await self._create_lookalike_audiences(
                customer_data, platforms
            )
            segments.extend(lookalikes)

        # Create retargeting segments
        retargeting = await self._create_retargeting_segments(platforms)
        segments.extend(retargeting)

        # Generate expansion recommendations
        expansion_recs = self._generate_expansion_recommendations(segments)

        plan = AudiencePlan(
            campaign_id=campaign_id,
            segments=segments,
            exclusions=["existing_customers", "low_engagement_30d"],
            expansion_recommendations=expansion_recs,
        )

        self._plans[campaign_id] = plan
        logger.info(
            "Audience plan created",
            campaign_id=campaign_id,
            segments=len(segments),
        )
        return plan

    async def _create_core_segments(
        self,
        product_category: str,
        demographics: dict[str, Any],
        platforms: list[str],
    ) -> list[AudienceSegment]:
        """Create core audience segments.

        Args:
            product_category: Product category.
            demographics: Target demographics.
            platforms: Target platforms.

        Returns:
            List of core AudienceSegment objects.
        """
        segments = [
            AudienceSegment(
                segment_id="core_001",
                name=f"{product_category.title()} Enthusiasts",
                audience_type=AudienceType.CORE,
                size_estimate=250000,
                demographics=demographics,
                interests=[product_category, "online shopping", "deals"],
                behaviors=["frequent_buyers", "mobile_shoppers"],
                platforms=platforms,
                estimated_cpa=25.0,
                priority=1,
            ),
            AudienceSegment(
                segment_id="core_002",
                name="High-Value Prospects",
                audience_type=AudienceType.CORE,
                size_estimate=100000,
                demographics={"income": "high", "age_range": "25-54"},
                interests=[product_category, "premium", "quality"],
                behaviors=["high_spenders", "brand_loyal"],
                platforms=["meta", "google"],
                estimated_cpa=45.0,
                priority=2,
            ),
        ]
        return segments

    async def _create_lookalike_audiences(
        self,
        customer_data: dict[str, Any],
        platforms: list[str],
    ) -> list[AudienceSegment]:
        """Create lookalike audience segments from customer data.

        Args:
            customer_data: Existing customer data.
            platforms: Target platforms.

        Returns:
            List of lookalike AudienceSegment objects.
        """
        lookalikes = [
            AudienceSegment(
                segment_id="lookalike_001",
                name="Lookalike — Top Customers (1%)",
                audience_type=AudienceType.LOOKALIKE,
                size_estimate=500000,
                demographics={},
                interests=[],
                behaviors=["similar_to_top_customers"],
                platforms=["meta", "google"],
                estimated_cpa=30.0,
                priority=3,
            ),
            AudienceSegment(
                segment_id="lookalike_002",
                name="Lookalike — All Customers (3%)",
                audience_type=AudienceType.LOOKALIKE,
                size_estimate=1500000,
                demographics={},
                interests=[],
                behaviors=["similar_to_all_customers"],
                platforms=["meta"],
                estimated_cpa=35.0,
                priority=4,
            ),
        ]
        return lookalikes

    async def _create_retargeting_segments(
        self,
        platforms: list[str],
    ) -> list[AudienceSegment]:
        """Create retargeting audience segments.

        Args:
            platforms: Target platforms.

        Returns:
            List of retargeting AudienceSegment objects.
        """
        retargeting = [
            AudienceSegment(
                segment_id="retarget_001",
                name="Website Visitors — 30d",
                audience_type=AudienceType.RETARGETING,
                size_estimate=50000,
                demographics={},
                interests=[],
                behaviors=["website_visitor_30d"],
                platforms=platforms,
                estimated_cpa=15.0,
                priority=5,
            ),
            AudienceSegment(
                segment_id="retarget_002",
                name="Cart Abandoners — 7d",
                audience_type=AudienceType.RETARGETING,
                size_estimate=10000,
                demographics={},
                interests=[],
                behaviors=["cart_abandoner_7d"],
                platforms=["meta"],
                estimated_cpa=10.0,
                priority=6,
            ),
        ]
        return retargeting

    def _generate_expansion_recommendations(
        self,
        segments: list[AudienceSegment],
    ) -> list[dict[str, Any]]:
        """Generate audience expansion recommendations.

        Args:
            segments: Current audience segments.

        Returns:
            List of expansion recommendation dictionaries.
        """
        recommendations = []
        for segment in segments:
            if segment.audience_type == AudienceType.LOOKALIKE:
                recommendations.append(
                    {
                        "segment_id": segment.segment_id,
                        "action": "expand",
                        "target_expansion": ExpansionLevel.BALANCED,
                        "reason": f"Strong performance expected from {segment.name}",
                    }
                )
        return recommendations

    async def optimize_targeting(
        self,
        campaign_id: str,
        performance_by_segment: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Optimize audience targeting based on performance data.

        Args:
            campaign_id: Campaign identifier.
            performance_by_segment: Performance data keyed by segment ID.

        Returns:
            Dictionary of targeting optimizations.
        """
        optimizations: dict[str, Any] = {
            "increase_budget": [],
            "decrease_budget": [],
            "pause": [],
            "expand": [],
        }

        for segment_id, metrics in performance_by_segment.items():
            roas = metrics.get("roas", 0)

            if roas > 3.0:
                optimizations["increase_budget"].append(segment_id)
                optimizations["expand"].append(segment_id)
            elif roas < 1.0:
                optimizations["pause"].append(segment_id)
            elif roas < 1.5:
                optimizations["decrease_budget"].append(segment_id)

        logger.info("Targeting optimization completed", campaign_id=campaign_id)
        return optimizations

    def get_plan(self, campaign_id: str) -> AudiencePlan | None:
        """Retrieve an audience plan by campaign ID.

        Args:
            campaign_id: The campaign identifier.

        Returns:
            The AudiencePlan or None if not found.
        """
        return self._plans.get(campaign_id)

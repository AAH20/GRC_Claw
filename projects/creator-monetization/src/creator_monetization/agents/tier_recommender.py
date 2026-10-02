"""Tier Recommender Agent - Recommends optimal creator tiers using AI."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

import structlog
from pydantic import BaseModel, Field

from creator_monetization.models.schemas import Tier, TierLevel

logger = structlog.get_logger(__name__)


class CreatorProfile(BaseModel):
    """Profile data for tier recommendation."""

    creator_id: str = Field(..., description="Creator identifier")
    subscriber_count: int = Field(..., ge=0)
    monthly_revenue: Decimal = Field(..., ge=0)
    content_category: str = Field(..., description="Content category/niche")
    engagement_rate: float = Field(default=0.0, ge=0, le=1)
    audience_demographics: dict[str, Any] = Field(default_factory=dict)


class TierRecommendation(BaseModel):
    """A tier recommendation with reasoning."""

    recommendation_id: str = Field(..., description="Recommendation identifier")
    recommended_tier: TierLevel = Field(..., description="Recommended tier level")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    reasoning: str = Field(..., description="Explanation for the recommendation")
    suggested_price: Decimal = Field(..., description="Suggested monthly price")
    expected_conversion_rate: float = Field(..., ge=0, le=1)


class TierRecommenderAgent:
    """Agent responsible for recommending optimal creator tiers.

    Uses AI-powered analysis of creator metrics, audience data,
    and market conditions to recommend the best tier structure.
    """

    def __init__(self, min_confidence: float = 0.7) -> None:
        """Initialize the tier recommender agent.

        Args:
            min_confidence: Minimum confidence threshold for recommendations.
        """
        self.min_confidence = min_confidence
        self._tiers: dict[str, Tier] = {}
        self._recommendations: dict[str, list[TierRecommendation]] = {}

    async def recommend_tier(self, profile: CreatorProfile) -> TierRecommendation:
        """Recommend a tier for a creator based on their profile.

        Args:
            profile: The creator's profile data.

        Returns:
            Tier recommendation with confidence and reasoning.

        Raises:
            ValueError: If profile data is invalid.
        """
        if profile.subscriber_count < 0:
            raise ValueError("Subscriber count must be non-negative")
        if profile.monthly_revenue < 0:
            raise ValueError("Monthly revenue must be non-negative")

        logger.info("Recommending tier", creator_id=profile.creator_id)

        # Determine tier level based on subscriber count and revenue
        if profile.subscriber_count >= 100000:
            tier_level = TierLevel.DIAMOND
            suggested_price = Decimal("49.99")
            confidence = 0.95
        elif profile.subscriber_count >= 50000:
            tier_level = TierLevel.PLATINUM
            suggested_price = Decimal("29.99")
            confidence = 0.90
        elif profile.subscriber_count >= 10000:
            tier_level = TierLevel.GOLD
            suggested_price = Decimal("19.99")
            confidence = 0.85
        elif profile.subscriber_count >= 1000:
            tier_level = TierLevel.SILVER
            suggested_price = Decimal("9.99")
            confidence = 0.80
        else:
            tier_level = TierLevel.BRONZE
            suggested_price = Decimal("4.99")
            confidence = 0.75

        # Adjust based on engagement rate
        if profile.engagement_rate > 0.1:
            confidence = min(1.0, confidence + 0.05)
            suggested_price = suggested_price * Decimal("1.1")

        # Adjust based on revenue per subscriber
        if profile.subscriber_count > 0:
            revenue_per_sub = profile.monthly_revenue / profile.subscriber_count
            if revenue_per_sub > Decimal("1.00"):
                suggested_price = suggested_price * Decimal("1.2")
                confidence = min(1.0, confidence + 0.03)

        reasoning = self._generate_reasoning(profile, tier_level, suggested_price)

        recommendation = TierRecommendation(
            recommendation_id=f"rec-{profile.creator_id}",
            recommended_tier=tier_level,
            confidence=round(confidence, 2),
            reasoning=reasoning,
            suggested_price=suggested_price.quantize(Decimal("0.01")),
            expected_conversion_rate=round(0.15 * confidence, 2),
        )

        logger.info(
            "Tier recommendation generated",
            creator_id=profile.creator_id,
            tier=tier_level,
            confidence=confidence,
        )
        return recommendation

    def _generate_reasoning(
        self, profile: CreatorProfile, tier_level: TierLevel, price: Decimal
    ) -> str:
        """Generate human-readable reasoning for a tier recommendation.

        Args:
            profile: The creator's profile.
            tier_level: The recommended tier level.
            price: The suggested price.

        Returns:
            Reasoning explanation string.
        """
        reasons = [
            f"Based on {profile.subscriber_count:,} subscribers",
            f"Monthly revenue of ${profile.monthly_revenue}",
            f"Engagement rate of {profile.engagement_rate:.1%}",
        ]

        if tier_level == TierLevel.DIAMOND:
            reasons.append("Top-tier creator with large audience")
        elif tier_level == TierLevel.PLATINUM:
            reasons.append("Established creator with strong following")
        elif tier_level == TierLevel.GOLD:
            reasons.append("Growing creator with solid engagement")
        elif tier_level == TierLevel.SILVER:
            reasons.append("Emerging creator with potential")
        else:
            reasons.append("New creator building audience")

        return "; ".join(reasons)

    async def compare_tiers(
        self, creator_id: str, tiers: list[Tier]
    ) -> dict[str, Any]:
        """Compare multiple tier options for a creator.

        Args:
            creator_id: The creator identifier.
            tiers: List of tiers to compare.

        Returns:
            Comparison results with rankings.

        Raises:
            ValueError: If tiers list is empty.
        """
        if not tiers:
            raise ValueError("At least one tier is required for comparison")

        logger.info("Comparing tiers", creator_id=creator_id, tier_count=len(tiers))

        comparisons = []
        for tier in tiers:
            # Calculate value score based on benefits and price
            benefit_score = len(tier.benefits) * 10
            price_score = 100 - float(tier.monthly_price) * 2
            value_score = benefit_score + max(0, price_score)

            comparisons.append(
                {
                    "tier_id": tier.tier_id,
                    "name": tier.name,
                    "level": tier.level,
                    "monthly_price": tier.monthly_price,
                    "benefit_count": len(tier.benefits),
                    "value_score": round(value_score, 2),
                }
            )

        # Sort by value score descending
        comparisons.sort(key=lambda x: x["value_score"], reverse=True)

        return {
            "creator_id": creator_id,
            "tier_count": len(tiers),
            "rankings": comparisons,
            "best_value": comparisons[0]["tier_id"] if comparisons else None,
        }

    async def optimize_tier_structure(
        self, creator_id: str, current_tiers: list[Tier]
    ) -> dict[str, Any]:
        """Optimize the tier structure for a creator.

        Args:
            creator_id: The creator identifier.
            current_tiers: Current tier structure.

        Returns:
            Optimization recommendations.

        Raises:
            ValueError: If current_tiers is empty.
        """
        if not current_tiers:
            raise ValueError("At least one tier is required")

        logger.info("Optimizing tier structure", creator_id=creator_id)

        recommendations = []
        tier_count = len(current_tiers)

        if tier_count < 3:
            recommendations.append(
                "Consider adding more tier levels to capture different audience segments"
            )

        # Check price gaps
        prices = sorted([t.monthly_price for t in current_tiers])
        for i in range(1, len(prices)):
            gap = prices[i] - prices[i - 1]
            if gap > Decimal("20.00"):
                recommendations.append(
                    f"Large price gap detected between ${prices[i-1]} and ${prices[i]} - consider adding intermediate tier"
                )

        # Check benefit differentiation
        all_benefits = set()
        for tier in current_tiers:
            all_benefits.update(tier.benefits)

        if len(all_benefits) < 5:
            recommendations.append(
                "Increase benefit differentiation across tiers to improve perceived value"
            )

        return {
            "creator_id": creator_id,
            "current_tier_count": tier_count,
            "recommendations": recommendations,
            "suggested_tier_count": max(3, tier_count),
        }

    def get_recommendation_count(self, creator_id: str) -> int:
        """Get the number of recommendations for a creator.

        Args:
            creator_id: The creator identifier.

        Returns:
            Number of recommendations.
        """
        return len(self._recommendations.get(creator_id, []))
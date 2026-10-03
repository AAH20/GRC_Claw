"""Tier Recommender Agent for creator monetization."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CreatorProfile(BaseModel):
    """Creator profile for tier recommendations."""

    creator_id: str = Field(..., description="Creator identifier")
    subscriber_count: int = Field(default=0, ge=0)
    content_category: str = Field(default="general")
    monthly_revenue: Decimal = Field(default=Decimal("0"), ge=0)
    audience_demographics: dict[str, Any] = Field(default_factory=dict)


class TierRecommendation(BaseModel):
    """A tier recommendation."""

    tier_name: str = Field(..., description="Recommended tier name")
    level: str = Field(..., description="Tier level (bronze, silver, gold, etc.)")
    monthly_price: Decimal = Field(..., ge=0)
    yearly_price: Decimal = Field(..., ge=0)
    benefits: list[str] = Field(default_factory=list)
    rationale: str = Field(default="", description="Recommendation rationale")


class TierRecommenderAgent:
    """Agent that recommends optimal pricing tiers for creators.

    Analyzes creator profile, audience, and market data
    to suggest tier structures and pricing.
    """

    def __init__(self) -> None:
        """Initialize the tier recommender agent."""
        self._tiers: dict[str, list[dict[str, Any]]] = {}

    async def recommend_tiers(
        self, profile: CreatorProfile
    ) -> list[TierRecommendation]:
        """Generate tier recommendations for a creator.

        Args:
            profile: Creator profile data.

        Returns:
            List of tier recommendations.
        """
        recommendations: list[TierRecommendation] = []

        # Bronze tier - entry level
        bronze_price = self._calculate_base_price(profile, 0.5)
        recommendations.append(
            TierRecommendation(
                tier_name="Bronze Supporter",
                level="bronze",
                monthly_price=bronze_price,
                yearly_price=bronze_price * Decimal("10"),
                benefits=[
                    "Access to exclusive content",
                    "Community badge",
                    "Monthly Q&A access",
                ],
                rationale="Entry-level tier to capture broad audience support",
            )
        )

        # Silver tier - mid level
        silver_price = self._calculate_base_price(profile, 1.0)
        recommendations.append(
            TierRecommendation(
                tier_name="Silver Member",
                level="silver",
                monthly_price=silver_price,
                yearly_price=silver_price * Decimal("10"),
                benefits=[
                    "All Bronze benefits",
                    "Early access to content",
                    "Monthly behind-the-scenes",
                    "Discord community access",
                ],
                rationale="Core tier for engaged fans seeking deeper connection",
            )
        )

        # Gold tier - premium
        gold_price = self._calculate_base_price(profile, 2.5)
        recommendations.append(
            TierRecommendation(
                tier_name="Gold Patron",
                level="gold",
                monthly_price=gold_price,
                yearly_price=gold_price * Decimal("10"),
                benefits=[
                    "All Silver benefits",
                    "One-on-one monthly call",
                    "Exclusive merchandise discounts",
                    "Name in credits",
                    "Priority support",
                ],
                rationale="Premium tier for dedicated supporters willing to pay more",
            )
        )

        logger.info(
            "Tier recommendations generated",
            creator_id=profile.creator_id,
            count=len(recommendations),
        )
        return recommendations

    def _calculate_base_price(
        self, profile: CreatorProfile, multiplier: float
    ) -> Decimal:
        """Calculate base price for a tier.

        Args:
            profile: Creator profile.
            multiplier: Price multiplier.

        Returns:
            Calculated price.
        """
        base = Decimal("5.00")
        if profile.subscriber_count > 10000:
            base = Decimal("10.00")
        elif profile.subscriber_count > 1000:
            base = Decimal("7.50")

        return (base * Decimal(str(multiplier))).quantize(Decimal("0.01"))

    async def create_tier(
        self,
        creator_id: str,
        name: str,
        level: str,
        monthly_price: Decimal,
        yearly_price: Decimal,
        benefits: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a tier for a creator.

        Args:
            creator_id: Creator identifier.
            name: Tier name.
            level: Tier level.
            monthly_price: Monthly price.
            yearly_price: Yearly price.
            benefits: List of benefits.

        Returns:
            Created tier data.

        Raises:
            ValueError: If prices are non-positive.
        """
        if monthly_price < 0 or yearly_price < 0:
            raise ValueError("Prices must be non-negative")

        tier = {
            "tier_id": f"tier_{creator_id}_{level}",
            "creator_id": creator_id,
            "name": name,
            "level": level,
            "monthly_price": str(monthly_price),
            "yearly_price": str(yearly_price),
            "benefits": benefits or [],
            "is_active": True,
        }

        if creator_id not in self._tiers:
            self._tiers[creator_id] = []
        self._tiers[creator_id].append(tier)

        logger.info("Tier created", creator_id=creator_id, tier_name=name, level=level)
        return tier

    def get_tiers(self, creator_id: str) -> list[dict[str, Any]]:
        """Get tiers for a creator.

        Args:
            creator_id: Creator identifier.

        Returns:
            List of tier data.
        """
        return self._tiers.get(creator_id, [])

    def compare_tiers(self, tier_ids: list[str]) -> dict[str, Any]:
        """Compare multiple tiers.

        Args:
            tier_ids: List of tier identifiers.

        Returns:
            Comparison data.
        """
        all_tiers = []
        for tiers in self._tiers.values():
            all_tiers.extend(tiers)

        selected = [t for t in all_tiers if t["tier_id"] in tier_ids]
        return {
            "tiers": selected,
            "count": len(selected),
            "price_range": {
                "min": min(
                    (Decimal(t["monthly_price"]) for t in selected),
                    default=Decimal("0"),
                ),
                "max": max(
                    (Decimal(t["monthly_price"]) for t in selected),
                    default=Decimal("0"),
                ),
            },
        }

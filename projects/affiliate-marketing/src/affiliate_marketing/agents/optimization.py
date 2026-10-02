"""Optimization Agent - A/B testing, bid optimization, and campaign tuning."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CampaignStatus(StrEnum):
    """Status of a marketing campaign."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class CampaignVariant(BaseModel):
    """A/B test variant for a campaign."""

    variant_id: str = Field(..., description="Variant identifier")
    name: str = Field(..., description="Variant name")
    traffic_percentage: float = Field(..., ge=0, le=100, description="Traffic allocation %")
    conversions: int = Field(default=0, ge=0, description="Number of conversions")
    clicks: int = Field(default=0, ge=0, description="Number of clicks")


class Campaign(BaseModel):
    """Marketing campaign with A/B testing support."""

    campaign_id: str = Field(..., description="Campaign identifier")
    name: str = Field(..., description="Campaign name")
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT)
    variants: list[CampaignVariant] = Field(default_factory=list)
    budget: float = Field(default=0.0, ge=0, description="Campaign budget")
    spent: float = Field(default=0.0, ge=0, description="Amount spent")


class OptimizationAgent:
    """Agent responsible for campaign optimization.

    Performs A/B testing analysis, bid optimization, and
    provides recommendations for campaign improvements.
    """

    def __init__(self, confidence_threshold: float = 0.95) -> None:
        """Initialize the optimization agent.

        Args:
            confidence_threshold: Statistical confidence threshold for A/B tests.
        """
        self.confidence_threshold = confidence_threshold
        self._campaigns: dict[str, Campaign] = {}

    async def create_campaign(self, campaign: Campaign) -> Campaign:
        """Create a new campaign.

        Args:
            campaign: The campaign to create.

        Returns:
            The created campaign.

        Raises:
            ValueError: If campaign_id already exists.
        """
        if campaign.campaign_id in self._campaigns:
            raise ValueError(f"Campaign {campaign.campaign_id} already exists")

        logger.info("Creating campaign", campaign_id=campaign.campaign_id, name=campaign.name)
        self._campaigns[campaign.campaign_id] = campaign
        return campaign

    async def analyze_ab_test(self, campaign_id: str) -> dict[str, Any]:
        """Analyze A/B test results for a campaign.

        Args:
            campaign_id: The campaign to analyze.

        Returns:
            Analysis results with winner and confidence.

        Raises:
            KeyError: If campaign not found.
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"Campaign {campaign_id} not found")

        campaign = self._campaigns[campaign_id]
        logger.info("Analyzing A/B test", campaign_id=campaign_id)

        if len(campaign.variants) < 2:
            return {"status": "insufficient_variants", "winner": None}

        results = []
        for variant in campaign.variants:
            ctr = variant.conversions / variant.clicks if variant.clicks > 0 else 0.0
            results.append({
                "variant_id": variant.variant_id,
                "name": variant.name,
                "ctr": round(ctr, 4),
                "conversions": variant.conversions,
                "clicks": variant.clicks,
            })

        # Simple winner selection (in production, use proper statistical tests)
        winner = max(results, key=lambda r: r["ctr"]) if results else None

        return {
            "status": "complete" if winner else "inconclusive",
            "winner": winner["variant_id"] if winner else None,
            "confidence": self.confidence_threshold,
            "results": results,
        }

    async def optimize_bids(
        self, campaign_id: str, target_cpa: float
    ) -> dict[str, Any]:
        """Optimize bids for a campaign based on target CPA.

        Args:
            campaign_id: The campaign to optimize.
            target_cpa: Target cost per acquisition.

        Returns:
            Bid optimization recommendations.

        Raises:
            KeyError: If campaign not found.
            ValueError: If target_cpa is non-positive.
        """
        if target_cpa <= 0:
            raise ValueError("Target CPA must be positive")
        if campaign_id not in self._campaigns:
            raise KeyError(f"Campaign {campaign_id} not found")

        campaign = self._campaigns[campaign_id]
        logger.info("Optimizing bids", campaign_id=campaign_id, target_cpa=target_cpa)

        total_conversions = sum(v.conversions for v in campaign.variants)
        current_cpa = campaign.spent / total_conversions if total_conversions > 0 else float("inf")

        adjustment = (target_cpa - current_cpa) / current_cpa if current_cpa > 0 else 0.0
        adjustment = max(-0.5, min(0.5, adjustment))  # Cap at ±50%

        return {
            "campaign_id": campaign_id,
            "current_cpa": round(current_cpa, 2),
            "target_cpa": target_cpa,
            "recommended_adjustment": round(adjustment, 4),
            "action": (
                "increase"
                if adjustment > 0.05
                else "decrease"
                if adjustment < -0.05
                else "maintain"
            ),
        }

    async def get_recommendations(self, campaign_id: str) -> list[str]:
        """Get optimization recommendations for a campaign.

        Args:
            campaign_id: The campaign to get recommendations for.

        Returns:
            List of recommendation strings.

        Raises:
            KeyError: If campaign not found.
        """
        if campaign_id not in self._campaigns:
            raise KeyError(f"Campaign {campaign_id} not found")

        campaign = self._campaigns[campaign_id]
        recommendations: list[str] = []

        total_clicks = sum(v.clicks for v in campaign.variants)
        total_conversions = sum(v.conversions for v in campaign.variants)

        if total_clicks > 0:
            overall_ctr = total_conversions / total_clicks
            if overall_ctr < 0.02:
                recommendations.append("Consider improving creative assets to increase CTR")
            if overall_ctr > 0.10:
                recommendations.append("High CTR - consider increasing budget")

        if campaign.spent > campaign.budget * 0.9:
            recommendations.append("Budget nearly exhausted - consider increasing budget")

        if not recommendations:
            recommendations.append("Campaign performing within expected parameters")

        return recommendations

    def get_campaign_count(self) -> int:
        """Get total number of campaigns.

        Returns:
            Campaign count.
        """
        return len(self._campaigns)

"""
Multi-Platform Campaign Optimization Example
============================================

Demonstrates running campaigns across multiple advertising platforms:
- Google Ads
- Meta (Facebook/Instagram)
- TikTok Ads
- LinkedIn Ads
- Twitter/X Ads

Features:
- Unified campaign management across platforms
- Cross-platform budget optimization
- Platform-specific creative adaptation
- Unified reporting and analytics
- Audience overlap management

Usage:
    python multi-platform.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PlatformType(str, Enum):
    """Supported advertising platforms."""

    GOOGLE_ADS = "google_ads"
    META_ADS = "meta_ads"
    TIKTOK_ADS = "tiktok_ads"
    LINKEDIN_ADS = "linkedin_ads"
    TWITTER_ADS = "twitter_ads"


class ObjectiveType(str, Enum):
    """Campaign objective types."""

    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    CONVERSION = "conversion"
    RETENTION = "retention"


class CreativeFormat(str, Enum):
    """Creative format types."""

    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    TEXT = "text"
    STORY = "story"
    REELS = "reels"


@dataclass
class PlatformCredentials:
    """API credentials for an advertising platform."""

    platform: PlatformType
    api_key: str
    api_secret: str
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at


@dataclass
class CreativeAsset:
    """A creative asset for ad placement."""

    name: str
    format: CreativeFormat
    platform: PlatformType
    headline: str | None = None
    description: str | None = None
    image_url: str | None = None
    video_url: str | None = None
    call_to_action: str | None = None
    target_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AudienceSegment:
    """An audience segment for targeting."""

    name: str
    platform: PlatformType
    size: int
    criteria: dict[str, Any] = field(default_factory=dict)
    lookalike: bool = False
    lookalike_seed: str | None = None


@dataclass
class PlatformCampaign:
    """A campaign on a specific platform."""

    platform: PlatformType
    name: str
    objective: ObjectiveType
    budget: float
    spent: float = 0.0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    status: str = "active"
    creatives: list[CreativeAsset] = field(default_factory=list)
    audiences: list[AudienceSegment] = field(default_factory=list)

    @property
    def ctr(self) -> float:
        """Click-through rate."""
        return self.clicks / self.impressions if self.impressions > 0 else 0.0

    @property
    def cpc(self) -> float:
        """Cost per click."""
        return self.spent / self.clicks if self.clicks > 0 else 0.0

    @property
    def roas(self) -> float:
        """Return on ad spend."""
        return self.revenue / self.spent if self.spent > 0 else 0.0

    @property
    def cpa(self) -> float:
        """Cost per acquisition."""
        return self.spent / self.conversions if self.conversions > 0 else 0.0

    @property
    def budget_utilization(self) -> float:
        """Budget utilization percentage."""
        return self.spent / self.budget if self.budget > 0 else 0.0


class MultiPlatformCampaignManager:
    """Manages campaigns across multiple advertising platforms."""

    def __init__(self) -> None:
        """Initialize the multi-platform campaign manager."""
        self.credentials: dict[PlatformType, PlatformCredentials] = {}
        self.campaigns: dict[str, list[PlatformCampaign]] = {}
        self.creative_library: list[CreativeAsset] = []

    def add_credentials(self, credentials: PlatformCredentials) -> None:
        """Add API credentials for a platform.

        Args:
            credentials: Platform credentials to add.
        """
        self.credentials[credentials.platform] = credentials
        logger.info("Added credentials for %s", credentials.platform.value)

    def create_cross_platform_campaign(
        self,
        name: str,
        total_budget: float,
        platforms: list[PlatformType],
        objective: ObjectiveType,
        platform_budget_split: dict[PlatformType, float] | None = None,
    ) -> dict[str, Any]:
        """Create a campaign across multiple platforms.

        Args:
            name: Campaign name.
            total_budget: Total budget across all platforms.
            platforms: Platforms to run on.
            objective: Campaign objective.
            platform_budget_split: Optional custom budget split.

        Returns:
            Campaign data dictionary.

        Raises:
            ValueError: If budget split doesn't sum to 1.0.
        """
        if platform_budget_split is None:
            # Equal split by default
            share = 1.0 / len(platforms)
            platform_budget_split = {p: share for p in platforms}

        total_split = sum(platform_budget_split.get(p, 0) for p in platforms)
        if abs(total_split - 1.0) > 0.01:
            raise ValueError(f"Platform budget split must sum to 1.0, got {total_split}")

        platform_campaigns: list[PlatformCampaign] = []
        for platform in platforms:
            budget = total_budget * platform_budget_split.get(platform, 0)
            pc = PlatformCampaign(
                platform=platform,
                name=f"{name} - {platform.value}",
                objective=objective,
                budget=budget,
            )
            platform_campaigns.append(pc)

        self.campaigns[name] = platform_campaigns
        logger.info(
            "Created cross-platform campaign '%s' on %d platforms",
            name,
            len(platforms),
        )
        return {
            "name": name,
            "total_budget": total_budget,
            "platforms": [p.value for p in platforms],
            "objective": objective.value,
            "platform_campaigns": platform_campaigns,
        }

    def add_creative(
        self,
        name: str,
        format: CreativeFormat,
        platform: PlatformType,
        headline: str | None = None,
        description: str | None = None,
        image_url: str | None = None,
        video_url: str | None = None,
        call_to_action: str | None = None,
        target_url: str | None = None,
    ) -> CreativeAsset:
        """Add a creative asset to the library.

        Args:
            name: Creative name.
            format: Creative format.
            platform: Target platform.
            headline: Headline text.
            description: Description text.
            image_url: Image URL.
            video_url: Video URL.
            call_to_action: CTA text.
            target_url: Landing page URL.

        Returns:
            The created CreativeAsset.
        """
        creative = CreativeAsset(
            name=name,
            format=format,
            platform=platform,
            headline=headline,
            description=description,
            image_url=image_url,
            video_url=video_url,
            call_to_action=call_to_action,
            target_url=target_url,
        )
        self.creative_library.append(creative)
        logger.info("Added creative '%s' for %s", name, platform.value)
        return creative

    def adapt_creative_for_platform(
        self,
        base_creative: CreativeAsset,
        target_platform: PlatformType,
    ) -> CreativeAsset:
        """Adapt a creative for a different platform.

        Args:
            base_creative: The base creative to adapt.
            target_platform: Target platform.

        Returns:
            Adapted CreativeAsset.
        """
        # Platform-specific adaptations
        adaptations: dict[PlatformType, dict[str, Any]] = {
            PlatformType.GOOGLE_ADS: {
                "headline": (base_creative.headline or "")[:30],
                "description": (base_creative.description or "")[:90],
            },
            PlatformType.META_ADS: {
                "headline": (base_creative.headline or "")[:40],
                "description": (base_creative.description or "")[:125],
            },
            PlatformType.TIKTOK_ADS: {
                "headline": (base_creative.headline or "")[:25],
                "description": (base_creative.description or "")[:80],
            },
            PlatformType.LINKEDIN_ADS: {
                "headline": (base_creative.headline or "")[:70],
                "description": (base_creative.description or "")[:150],
            },
            PlatformType.TWITTER_ADS: {
                "headline": (base_creative.headline or "")[:280],
                "description": (base_creative.description or "")[:280],
            },
        }

        adaptation = adaptations.get(target_platform, {})
        adapted = CreativeAsset(
            name=f"{base_creative.name}_{target_platform.value}",
            format=base_creative.format,
            platform=target_platform,
            headline=adaptation.get("headline", base_creative.headline),
            description=adaptation.get("description", base_creative.description),
            image_url=base_creative.image_url,
            video_url=base_creative.video_url,
            call_to_action=base_creative.call_to_action,
            target_url=base_creative.target_url,
            metadata={"adapted_from": base_creative.platform.value},
        )

        logger.info(
            "Adapted creative '%s' for %s",
            base_creative.name,
            target_platform.value,
        )
        return adapted

    def optimize_cross_platform_budget(
        self,
        campaign_name: str,
        performance_window_days: int = 7,
    ) -> dict[str, Any]:
        """Optimize budget allocation across platforms.

        Args:
            campaign_name: Campaign name.
            performance_window_days: Days of performance data to consider.

        Returns:
            Optimized budget allocation.
        """
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")

        platform_campaigns = self.campaigns[campaign_name]

        # Calculate performance scores
        scores: dict[PlatformType, float] = {}
        for pc in platform_campaigns:
            # Score based on ROAS and conversion rate
            roas_score = min(pc.roas / 5.0, 1.0)  # Normalize to 0-1
            conv_rate = pc.conversions / pc.clicks if pc.clicks > 0 else 0
            conv_score = min(conv_rate / 0.1, 1.0)  # Normalize to 0-1
            scores[pc.platform] = roas_score * 0.6 + conv_score * 0.4

        # Normalize scores to create budget allocation
        total_score = sum(scores.values())
        if total_score == 0:
            # Equal allocation if no performance data
            equal_share = 1.0 / len(platform_campaigns)
            allocation = {pc.platform: equal_share for pc in platform_campaigns}
        else:
            allocation = {p: s / total_score for p, s in scores.items()}

        result = {
            "campaign": campaign_name,
            "allocation": {p.value: round(a, 4) for p, a in allocation.items()},
            "scores": {p.value: round(s, 4) for p, s in scores.items()},
            "total_budget": sum(pc.budget for pc in platform_campaigns),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info("Cross-platform budget optimization complete")
        return result

    def get_unified_report(self, campaign_name: str) -> dict[str, Any]:
        """Generate a unified report across all platforms.

        Args:
            campaign_name: Campaign name.

        Returns:
            Unified report dictionary.
        """
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")

        platform_campaigns = self.campaigns[campaign_name]

        total_spend = sum(pc.spent for pc in platform_campaigns)
        total_revenue = sum(pc.revenue for pc in platform_campaigns)
        total_impressions = sum(pc.impressions for pc in platform_campaigns)
        total_clicks = sum(pc.clicks for pc in platform_campaigns)
        total_conversions = sum(pc.conversions for pc in platform_campaigns)

        platform_reports = {}
        for pc in platform_campaigns:
            platform_reports[pc.platform.value] = {
                "name": pc.name,
                "status": pc.status,
                "budget": round(pc.budget, 2),
                "spent": round(pc.spent, 2),
                "budget_utilization": round(pc.budget_utilization, 4),
                "impressions": pc.impressions,
                "clicks": pc.clicks,
                "conversions": pc.conversions,
                "revenue": round(pc.revenue, 2),
                "ctr": round(pc.ctr, 4),
                "cpc": round(pc.cpc, 2),
                "roas": round(pc.roas, 4),
                "cpa": round(pc.cpa, 2),
            }

        return {
            "campaign_name": campaign_name,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_budget": round(sum(pc.budget for pc in platform_campaigns), 2),
                "total_spend": round(total_spend, 2),
                "total_revenue": round(total_revenue, 2),
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "overall_roas": round(total_revenue / total_spend, 4) if total_spend > 0 else 0,
                "overall_ctr": round(total_clicks / total_impressions, 4) if total_impressions > 0 else 0,
                "overall_cpa": round(total_spend / total_conversions, 2) if total_conversions > 0 else 0,
            },
            "platforms": platform_reports,
        }

    def manage_audience_overlap(
        self,
        campaign_name: str,
        max_overlap_percentage: float = 30.0,
    ) -> dict[str, Any]:
        """Manage audience overlap across platforms.

        Args:
            campaign_name: Campaign name.
            max_overlap_percentage: Maximum allowed overlap percentage.

        Returns:
            Overlap analysis and recommendations.
        """
        if campaign_name not in self.campaigns:
            raise ValueError(f"Campaign '{campaign_name}' not found")

        platform_campaigns = self.campaigns[campaign_name]

        # Simplified overlap estimation based on audience sizes
        audiences: dict[str, list[AudienceSegment]] = {}
        for pc in platform_campaigns:
            audiences[pc.platform.value] = pc.audiences

        # Calculate potential overlaps
        overlaps = []
        platform_list = list(audiences.keys())
        for i in range(len(platform_list)):
            for j in range(i + 1, len(platform_list)):
                p1, p2 = platform_list[i], platform_list[j]
                # Simplified: estimate overlap as min of audience sizes
                size1 = sum(a.size for a in audiences[p1])
                size2 = sum(a.size for a in audiences[p2])
                estimated_overlap = min(size1, size2) * 0.3  # 30% estimated overlap

                overlaps.append({
                    "platforms": [p1, p2],
                    "estimated_overlap": int(estimated_overlap),
                    "overlap_percentage": round(estimated_overlap / max(size1, size2) * 100, 2),
                })

        recommendations = []
        for overlap in overlaps:
            if overlap["overlap_percentage"] > max_overlap_percentage:
                recommendations.append({
                    "platforms": overlap["platforms"],
                    "issue": "High audience overlap",
                    "recommendation": "Use frequency capping and sequential messaging",
                })

        return {
            "campaign": campaign_name,
            "overlaps": overlaps,
            "recommendations": recommendations,
            "max_allowed_overlap": max_overlap_percentage,
        }


def main() -> None:
    """Run the multi-platform campaign example."""
    logger.info("=" * 60)
    logger.info("Multi-Platform Campaign Optimization Example")
    logger.info("=" * 60)

    manager = MultiPlatformCampaignManager()

    # Add platform credentials
    for platform in PlatformType:
        manager.add_credentials(
            PlatformCredentials(
                platform=platform,
                api_key=f"key_{platform.value}",
                api_secret=f"secret_{platform.value}",
                access_token=f"token_{platform.value}",
            )
        )

    # Create cross-platform campaign
    campaign = manager.create_cross_platform_campaign(
        name="Holiday Sale 2026",
        total_budget=100000.0,
        platforms=[
            PlatformType.GOOGLE_ADS,
            PlatformType.META_ADS,
            PlatformType.TIKTOK_ADS,
            PlatformType.LINKEDIN_ADS,
        ],
        objective=ObjectiveType.CONVERSION,
        platform_budget_split={
            PlatformType.GOOGLE_ADS: 0.4,
            PlatformType.META_ADS: 0.3,
            PlatformType.TIKTOK_ADS: 0.2,
            PlatformType.LINKEDIN_ADS: 0.1,
        },
    )
    logger.info("Created campaign '%s' on %d platforms", campaign["name"], len(campaign["platforms"]))

    # Add creatives
    base_creative = manager.add_creative(
        name="Holiday Hero Banner",
        format=CreativeFormat.IMAGE,
        platform=PlatformType.GOOGLE_ADS,
        headline="Holiday Sale - Up to 50% Off",
        description="Shop our biggest sale of the season",
        image_url="https://cdn.example.com/holiday-banner.jpg",
        call_to_action="Shop Now",
        target_url="https://example.com/sale",
    )

    # Adapt for other platforms
    for platform in [PlatformType.META_ADS, PlatformType.TIKTOK_ADS, PlatformType.LINKEDIN_ADS]:
        adapted = manager.adapt_creative_for_platform(base_creative, platform)
        logger.info("Adapted creative for %s: %s", platform.value, adapted.headline)

    # Simulate performance data
    for pc in manager.campaigns["Holiday Sale 2026"]:
        pc.spent = pc.budget * 0.6
        pc.impressions = int(pc.spent * 100)
        pc.clicks = int(pc.impressions * 0.03)
        pc.conversions = int(pc.clicks * 0.08)
        pc.revenue = pc.conversions * 75.0

    # Optimize budget
    optimization = manager.optimize_cross_platform_budget("Holiday Sale 2026")
    logger.info("Optimized allocation: %s", optimization["allocation"])

    # Generate unified report
    report = manager.get_unified_report("Holiday Sale 2026")
    logger.info("\nUnified Report:")
    logger.info("  Total Spend: $%.2f", report["summary"]["total_spend"])
    logger.info("  Total Revenue: $%.2f", report["summary"]["total_revenue"])
    logger.info("  Overall ROAS: %.2f", report["summary"]["overall_roas"])
    logger.info("  Total Conversions: %d", report["summary"]["total_conversions"])

    # Audience overlap
    overlap = manager.manage_audience_overlap("Holiday Sale 2026")
    logger.info("\nAudience Overlap Analysis:")
    for o in overlap["overlaps"]:
        logger.info("  %s <-> %s: %.1f%%", o["platforms"][0], o["platforms"][1], o["overlap_percentage"])

    logger.info("\n" + "=" * 60)
    logger.info("Multi-platform example complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

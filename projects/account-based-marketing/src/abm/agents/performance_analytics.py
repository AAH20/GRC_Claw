"""Performance Analytics Agent for tracking campaign metrics and ROI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class AttributionModel(str, Enum):
    """Attribution models for credit assignment."""

    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    MULTI_TOUCH = "multi_touch"
    W_SHAPED = "w_shaped"


@dataclass
class CampaignMetrics:
    """Represents aggregated campaign performance metrics."""

    campaign_id: str
    impressions: int = 0
    clicks: int = 0
    engagements: int = 0
    leads_generated: int = 0
    opportunities_created: int = 0
    pipeline_generated: float = 0.0
    revenue_influenced: float = 0.0
    spend: float = 0.0
    start_date: datetime | None = None
    end_date: datetime | None = None

    @property
    def ctr(self) -> float:
        """Click-through rate."""
        return round(self.clicks / self.impressions, 4) if self.impressions > 0 else 0.0

    @property
    def engagement_rate(self) -> float:
        """Engagement rate."""
        return round(self.engagements / self.impressions, 4) if self.impressions > 0 else 0.0

    @property
    def cpc(self) -> float:
        """Cost per click."""
        return round(self.spend / self.clicks, 2) if self.clicks > 0 else 0.0

    @property
    def cpl(self) -> float:
        """Cost per lead."""
        return round(self.spend / self.leads_generated, 2) if self.leads_generated > 0 else 0.0

    @property
    def roi(self) -> float:
        """Return on investment."""
        return (
            round((self.revenue_influenced - self.spend) / self.spend, 4)
            if self.spend > 0
            else 0.0
        )


@dataclass
class AccountEngagement:
    """Represents engagement metrics for a single account."""

    account_id: str
    touchpoints_received: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    ads_clicked: int = 0
    website_visits: int = 0
    content_downloads: int = 0
    meetings_booked: int = 0
    last_engagement: datetime | None = None


class PerformanceAnalyticsAgent:
    """Tracks and analyzes ABM campaign performance and ROI.

    This agent aggregates performance data from all channels, computes
    attribution, and provides insights on campaign effectiveness.
    """

    def __init__(self, attribution_model: AttributionModel = AttributionModel.MULTI_TOUCH) -> None:
        """Initialize the Performance Analytics Agent.

        Args:
            attribution_model: The attribution model to use for credit assignment.
        """
        self.attribution_model = attribution_model
        logger.info(
            "PerformanceAnalyticsAgent initialized",
            attribution_model=attribution_model.value,
        )

    async def get_campaign_metrics(self, campaign_id: str) -> CampaignMetrics:
        """Get aggregated metrics for a campaign.

        Args:
            campaign_id: The campaign identifier.

        Returns:
            CampaignMetrics with aggregated performance data.

        Raises:
            ValueError: If campaign_id is empty.
        """
        if not campaign_id:
            raise ValueError("campaign_id cannot be empty")

        logger.info("Fetching campaign metrics", campaign_id=campaign_id)

        # In production, this would query analytics databases
        return CampaignMetrics(
            campaign_id=campaign_id,
            impressions=150000,
            clicks=3200,
            engagements=8500,
            leads_generated=320,
            opportunities_created=45,
            pipeline_generated=2500000.0,
            revenue_influenced=8000000.0,
            spend=150000.0,
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 3, 31, tzinfo=timezone.utc),
        )

    async def get_account_engagement(self, campaign_id: str) -> list[AccountEngagement]:
        """Get engagement metrics per account for a campaign.

        Args:
            campaign_id: The campaign identifier.

        Returns:
            List of AccountEngagement objects.
        """
        if not campaign_id:
            raise ValueError("campaign_id cannot be empty")

        logger.info("Fetching account engagement", campaign_id=campaign_id)

        return [
            AccountEngagement(
                account_id="acc_001",
                touchpoints_received=12,
                emails_opened=8,
                emails_clicked=5,
                ads_clicked=3,
                website_visits=15,
                content_downloads=4,
                meetings_booked=1,
                last_engagement=datetime(2024, 3, 15, tzinfo=timezone.utc),
            ),
            AccountEngagement(
                account_id="acc_002",
                touchpoints_received=8,
                emails_opened=3,
                emails_clicked=1,
                ads_clicked=2,
                website_visits=6,
                content_downloads=1,
                meetings_booked=0,
                last_engagement=datetime(2024, 2, 28, tzinfo=timezone.utc),
            ),
        ]

    async def compute_attribution(
        self,
        campaign_id: str,
        model: AttributionModel | None = None,
    ) -> dict[str, Any]:
        """Compute attribution for a campaign.

        Args:
            campaign_id: The campaign identifier.
            model: Optional override for attribution model.

        Returns:
            Dictionary with attribution breakdown by channel.

        Raises:
            ValueError: If campaign_id is empty.
        """
        if not campaign_id:
            raise ValueError("campaign_id cannot be empty")

        attribution_model = model or self.attribution_model
        logger.info(
            "Computing attribution",
            campaign_id=campaign_id,
            model=attribution_model.value,
        )

        # Mock attribution data
        return {
            "campaign_id": campaign_id,
            "model": attribution_model.value,
            "total_revenue": 8000000.0,
            "channel_attribution": {
                "email": {"revenue": 3200000.0, "percentage": 0.40},
                "linkedin_ads": {"revenue": 2400000.0, "percentage": 0.30},
                "google_ads": {"revenue": 1600000.0, "percentage": 0.20},
                "direct_mail": {"revenue": 800000.0, "percentage": 0.10},
            },
        }

    async def generate_report(self, campaign_id: str) -> dict[str, Any]:
        """Generate a comprehensive campaign performance report.

        Args:
            campaign_id: The campaign identifier.

        Returns:
            Dictionary containing the full performance report.
        """
        if not campaign_id:
            raise ValueError("campaign_id cannot be empty")

        logger.info("Generating performance report", campaign_id=campaign_id)

        metrics = await self.get_campaign_metrics(campaign_id)
        engagement = await self.get_account_engagement(campaign_id)
        attribution = await self.compute_attribution(campaign_id)

        return {
            "campaign_id": campaign_id,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "summary": {
                "impressions": metrics.impressions,
                "clicks": metrics.clicks,
                "ctr": metrics.ctr,
                "engagement_rate": metrics.engagement_rate,
                "leads_generated": metrics.leads_generated,
                "opportunities_created": metrics.opportunities_created,
                "pipeline_generated": metrics.pipeline_generated,
                "revenue_influenced": metrics.revenue_influenced,
                "spend": metrics.spend,
                "roi": metrics.roi,
                "cpl": metrics.cpl,
            },
            "account_engagement": [
                {
                    "account_id": e.account_id,
                    "touchpoints": e.touchpoints_received,
                    "meetings_booked": e.meetings_booked,
                    "last_engagement": e.last_engagement.isoformat() if e.last_engagement else None,
                }
                for e in engagement
            ],
            "attribution": attribution,
        }

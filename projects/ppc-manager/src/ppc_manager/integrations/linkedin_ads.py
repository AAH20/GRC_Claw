"""LinkedIn Ads API integration client."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class LinkedInAdsConfig(BaseModel):
    """Configuration for LinkedIn Ads API.

    Attributes:
        access_token: LinkedIn Marketing API access token.
        ad_account_id: The LinkedIn ad account ID.
    """

    access_token: str
    ad_account_id: str


class LinkedInCampaign(BaseModel):
    """A LinkedIn Ads campaign.

    Attributes:
        id: Campaign ID.
        name: Campaign name.
        status: Campaign status.
        daily_budget: Daily budget in USD.
    """

    id: str
    name: str
    status: str
    daily_budget: float = 0.0


class LinkedInAdsClient:
    """Client for the LinkedIn Marketing API.

    Provides methods to interact with LinkedIn Ads campaigns and
    retrieve performance data.
    """

    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, config: LinkedInAdsConfig) -> None:
        """Initialize the LinkedIn Ads client.

        Args:
            config: The LinkedIn Ads API configuration.
        """
        self.config = config

    async def list_campaigns(self) -> list[LinkedInCampaign]:
        """List all campaigns for the ad account.

        Returns:
            A list of LinkedInCampaign objects.

        Raises:
            ValueError: If ad_account_id is not set.
        """
        if not self.config.ad_account_id:
            raise ValueError("Ad account ID is required")

        logger.info("Listing LinkedIn Ads campaigns", account_id=self.config.ad_account_id)

        import httpx

        url = f"{self.BASE_URL}/adCampaignsV2"
        headers = {"Authorization": f"Bearer {self.config.access_token}"}
        params = {
            "q": "search",
            "search.account.values": f"urn:li:sponsoredAccount:{self.config.ad_account_id}",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        campaigns: list[LinkedInCampaign] = []
        for item in data.get("elements", []):
            campaigns.append(
                LinkedInCampaign(
                    id=str(item.get("id", "")),
                    name=item.get("name", ""),
                    status=item.get("status", "UNKNOWN"),
                    daily_budget=float(item.get("dailyBudget", {}).get("amount", 0)),
                )
            )

        logger.info("LinkedIn Ads campaigns listed", count=len(campaigns))
        return campaigns

    async def get_campaign_analytics(
        self,
        campaign_id: str,
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get analytics for a campaign.

        Args:
            campaign_id: The campaign ID.
            metrics: Optional list of metrics to retrieve.

        Returns:
            A dictionary of analytics data.

        Raises:
            ValueError: If campaign_id is empty.
        """
        if not campaign_id:
            raise ValueError("Campaign ID is required")

        default_metrics = ["impressions", "clicks", "costInLocalCurrency", "conversions"]
        metrics = metrics or default_metrics

        import httpx

        url = f"{self.BASE_URL}/adAnalyticsV2"
        headers = {"Authorization": f"Bearer {self.config.access_token}"}
        params = {
            "q": "analytics",
            "pivot": "CAMPAIGN",
            "campaigns[0]": f"urn:sponsoredCampaign:{campaign_id}",
            "fields": ",".join(metrics),
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

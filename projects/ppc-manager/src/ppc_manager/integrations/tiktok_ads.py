"""TikTok Ads API integration client."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class TikTokAdsConfig(BaseModel):
    """Configuration for TikTok Marketing API.

    Attributes:
        access_token: TikTok Marketing API access token.
        advertiser_id: The TikTok advertiser ID.
    """

    access_token: str
    advertiser_id: str


class TikTokCampaign(BaseModel):
    """A TikTok Ads campaign.

    Attributes:
        id: Campaign ID.
        name: Campaign name.
        status: Campaign status.
        budget: Daily budget in USD.
    """

    id: str
    name: str
    status: str
    budget: float = 0.0


class TikTokAdsClient:
    """Client for the TikTok Marketing API.

    Provides methods to interact with TikTok Ads campaigns and
    retrieve performance data.
    """

    BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"

    def __init__(self, config: TikTokAdsConfig) -> None:
        """Initialize the TikTok Ads client.

        Args:
            config: The TikTok Ads API configuration.
        """
        self.config = config

    async def list_campaigns(self) -> list[TikTokCampaign]:
        """List all campaigns for the advertiser.

        Returns:
            A list of TikTokCampaign objects.

        Raises:
            ValueError: If advertiser_id is not set.
        """
        if not self.config.advertiser_id:
            raise ValueError("Advertiser ID is required")

        logger.info("Listing TikTok Ads campaigns", advertiser_id=self.config.advertiser_id)

        import httpx

        url = f"{self.BASE_URL}/campaign/get/"
        headers = {"Access-Token": self.config.access_token}
        params = {
            "advertiser_id": self.config.advertiser_id,
            "page": 1,
            "page_size": 100,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        campaigns: list[TikTokCampaign] = []
        for item in data.get("data", {}).get("list", []):
            campaigns.append(
                TikTokCampaign(
                    id=str(item.get("campaign_id", "")),
                    name=item.get("campaign_name", ""),
                    status=item.get("status", "UNKNOWN"),
                    budget=float(item.get("budget", 0)),
                )
            )

        logger.info("TikTok Ads campaigns listed", count=len(campaigns))
        return campaigns

    async def get_campaign_report(
        self,
        campaign_id: str,
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get performance report for a campaign.

        Args:
            campaign_id: The campaign ID.
            metrics: Optional list of metrics to retrieve.

        Returns:
            A dictionary of report data.

        Raises:
            ValueError: If campaign_id is empty.
        """
        if not campaign_id:
            raise ValueError("Campaign ID is required")

        default_metrics = ["impressions", "clicks", "spend", "ctr", "cpc", "conversions"]
        metrics = metrics or default_metrics

        import httpx

        url = f"{self.BASE_URL}/report/integrated/get/"
        headers = {
            "Access-Token": self.config.access_token,
            "Content-Type": "application/json",
        }
        payload = {
            "advertiser_id": self.config.advertiser_id,
            "report_type": "BASIC",
            "data_level": "AUCTION_CAMPAIGN",
            "dimensions": ["campaign_id"],
            "metrics": metrics,
            "filters": [
                {
                    "field_name": "campaign_id",
                    "filter_type": "IN",
                    "filter_value": [campaign_id],
                }
            ],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

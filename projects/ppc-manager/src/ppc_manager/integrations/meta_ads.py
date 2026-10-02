"""Meta Ads API integration client."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class MetaAdsConfig(BaseModel):
    """Configuration for Meta Ads API.

    Attributes:
        access_token: Meta Marketing API access token.
        app_id: Meta app ID.
        app_secret: Meta app secret.
        ad_account_id: The ad account ID.
    """

    access_token: str
    app_id: str
    app_secret: str
    ad_account_id: str


class MetaCampaign(BaseModel):
    """A Meta Ads campaign.

    Attributes:
        id: Campaign ID.
        name: Campaign name.
        status: Campaign status.
        daily_budget: Daily budget in cents.
    """

    id: str
    name: str
    status: str
    daily_budget: int = 0


class MetaAdsClient:
    """Client for the Meta Marketing API.

    Provides methods to interact with Meta Ads campaigns, ad sets,
    and ads via the Meta Marketing API.
    """

    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, config: MetaAdsConfig) -> None:
        """Initialize the Meta Ads client.

        Args:
            config: The Meta Ads API configuration.
        """
        self.config = config

    async def list_campaigns(self) -> list[MetaCampaign]:
        """List all campaigns for the ad account.

        Returns:
            A list of MetaCampaign objects.

        Raises:
            ValueError: If ad_account_id is not set.
        """
        if not self.config.ad_account_id:
            raise ValueError("Ad account ID is required")

        logger.info("Listing Meta Ads campaigns", account_id=self.config.ad_account_id)

        import httpx

        url = f"{self.BASE_URL}/{self.config.ad_account_id}/campaigns"
        params = {
            "fields": "id,name,status,daily_budget",
            "access_token": self.config.access_token,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        campaigns: list[MetaCampaign] = []
        for item in data.get("data", []):
            campaigns.append(
                MetaCampaign(
                    id=item["id"],
                    name=item["name"],
                    status=item.get("status", "UNKNOWN"),
                    daily_budget=int(item.get("daily_budget", 0)),
                )
            )

        logger.info("Meta Ads campaigns listed", count=len(campaigns))
        return campaigns

    async def update_campaign_budget(
        self,
        campaign_id: str,
        daily_budget_cents: int,
    ) -> MetaCampaign:
        """Update a campaign's daily budget.

        Args:
            campaign_id: The campaign ID.
            daily_budget_cents: The new daily budget in cents.

        Returns:
            The updated MetaCampaign.

        Raises:
            ValueError: If campaign_id is empty.
        """
        if not campaign_id:
            raise ValueError("Campaign ID is required")

        logger.info(
            "Updating Meta Ads campaign budget",
            campaign_id=campaign_id,
            daily_budget_cents=daily_budget_cents,
        )

        import httpx

        url = f"{self.BASE_URL}/{campaign_id}"
        params = {
            "daily_budget": daily_budget_cents,
            "access_token": self.config.access_token,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params)
            response.raise_for_status()
            data = response.json()

        return MetaCampaign(
            id=campaign_id,
            name=data.get("name", ""),
            status=data.get("status", "UNKNOWN"),
            daily_budget=daily_budget_cents,
        )

    async def get_campaign_insights(
        self,
        campaign_id: str,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get performance insights for a campaign.

        Args:
            campaign_id: The campaign ID.
            fields: Optional list of insight fields to retrieve.

        Returns:
            A dictionary of insight data.

        Raises:
            ValueError: If campaign_id is empty.
        """
        if not campaign_id:
            raise ValueError("Campaign ID is required")

        default_fields = ["impressions", "clicks", "spend", "ctr", "cpc"]
        fields = fields or default_fields

        import httpx

        url = f"{self.BASE_URL}/{campaign_id}/insights"
        params = {
            "fields": ",".join(fields),
            "access_token": self.config.access_token,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

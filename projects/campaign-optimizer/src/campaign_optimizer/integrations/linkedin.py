"""LinkedIn Marketing API integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class LinkedInAdsClient:
    """Client for the LinkedIn Marketing API.

    Provides methods to interact with LinkedIn's advertising platform
    for campaign management, audience targeting, and performance reporting.
    """

    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(
        self,
        access_token: str,
        ad_account_id: str,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the LinkedIn Ads client.

        Args:
            access_token: LinkedIn Marketing API access token.
            ad_account_id: LinkedIn ad account ID (format: urn:li:sponsoredAccount:XXXXXX).
            timeout: Request timeout in seconds.

        Raises:
            ValueError: If access_token or ad_account_id is empty.
        """
        if not access_token:
            raise ValueError("Access token is required")
        if not ad_account_id:
            raise ValueError("Ad account ID is required")

        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            Configured AsyncClient instance.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_campaigns(self) -> list[dict[str, Any]]:
        """Get all campaigns in the ad account.

        Returns:
            List of campaign dictionaries.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        account_urn = f"urn:li:sponsoredAccount:{self.ad_account_id}"

        response = await client.get(
            "/adCampaigns",
            params={
                "q": "search",
                "search.account.values": [account_urn],
                "count": 50,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("elements", [])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_campaign_analytics(
        self,
        campaign_id: str,
        date_range: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get analytics for a campaign.

        Args:
            campaign_id: The campaign ID.
            date_range: Optional date range with start/end dates.

        Returns:
            List of analytics dictionaries.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        campaign_urn = f"urn:li:sponsoredCampaign:{campaign_id}"

        params: dict[str, Any] = {
            "q": "analytics",
            "pivot": "CAMPAIGN",
            "campaigns": [campaign_urn],
        }
        if date_range:
            params["dateRange"] = date_range

        response = await client.get("/adAnalytics", params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("elements", [])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_campaign(
        self,
        name: str,
        campaign_group_id: str,
        daily_budget: float,
        objective: str = "WEBSITE_VISITS",
    ) -> dict[str, Any]:
        """Create a new LinkedIn campaign.

        Args:
            name: Campaign name.
            campaign_group_id: The campaign group URN.
            daily_budget: Daily budget in USD.
            objective: Campaign objective.

        Returns:
            Created campaign data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        account_urn = f"urn:li:sponsoredAccount:{self.ad_account_id}"

        payload = {
            "account": account_urn,
            "name": name,
            "campaignGroup": campaign_group_id,
            "status": "DRAFT",
            "type": "SPONSORED_UPDATES",
            "dailyBudget": {
                "amount": str(daily_budget),
                "currencyCode": "USD",
            },
            "objective": objective,
        }

        response = await client.post("/adCampaigns", json=payload)
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def update_campaign_status(
        self,
        campaign_id: str,
        status: str,
    ) -> dict[str, Any]:
        """Update a campaign's status.

        Args:
            campaign_id: The campaign ID.
            status: New status (ACTIVE/PAUSED/DRAFT/ARCHIVED).

        Returns:
            Updated campaign data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        campaign_urn = f"urn:li:sponsoredCampaign:{campaign_id}"

        response = await client.post(
            f"/adCampaigns/{campaign_urn}",
            json={"status": status},
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_audience_segments(self) -> list[dict[str, Any]]:
        """Get available audience segments.

        Returns:
            List of audience segment dictionaries.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()

        response = await client.get(
            "/adTargetingEntities",
            params={"q": "targetingFacetType", "type": "AUDIENCE"},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("elements", [])

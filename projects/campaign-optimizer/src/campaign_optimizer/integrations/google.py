"""Google Ads API integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class GoogleAdsClient:
    """Client for the Google Ads API.

    Provides methods to interact with Google's advertising platform
    for campaign management, keyword targeting, and performance reporting.
    """

    BASE_URL = "https://googleads.googleapis.com/v17"

    def __init__(
        self,
        developer_token: str,
        customer_id: str,
        login_customer_id: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Google Ads client.

        Args:
            developer_token: Google Ads API developer token.
            customer_id: Google Ads customer ID.
            login_customer_id: Optional manager account ID for MCC access.
            timeout: Request timeout in seconds.

        Raises:
            ValueError: If developer_token or customer_id is empty.
        """
        if not developer_token:
            raise ValueError("Developer token is required")
        if not customer_id:
            raise ValueError("Customer ID is required")

        self.developer_token = developer_token
        self.customer_id = customer_id
        self.login_customer_id = login_customer_id
        self.timeout = timeout
        self._access_token: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client.

        Returns:
            Configured AsyncClient instance.
        """
        if self._client is None or self._client.is_closed:
            headers = {
                "developer-token": self.developer_token,
                "Content-Type": "application/json",
            }
            if self._access_token:
                headers["Authorization"] = f"Bearer {self._access_token}"
            if self.login_customer_id:
                headers["login-customer-id"] = self.login_customer_id

            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                timeout=self.timeout,
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def set_access_token(self, access_token: str) -> None:
        """Set the OAuth2 access token for API requests.

        Args:
            access_token: Valid OAuth2 access token.
        """
        self._access_token = access_token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_campaigns(self) -> list[dict[str, Any]]:
        """Get all campaigns for the customer account.

        Returns:
            List of campaign dictionaries.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                campaign_budget.amount_micros
            FROM campaign
            ORDER BY campaign.id
        """

        response = await client.post(
            f"/customers/{self.customer_id}/googleAds:search",
            json={"query": query},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_campaign_metrics(
        self,
        campaign_id: str | None = None,
        date_range: str = "LAST_30_DAYS",
    ) -> list[dict[str, Any]]:
        """Get performance metrics for campaigns.

        Args:
            campaign_id: Optional campaign ID to filter by.
            date_range: Date range for metrics.

        Returns:
            List of metric dictionaries.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        campaign_filter = ""
        if campaign_id:
            campaign_filter = f"WHERE campaign.id = {campaign_id}"

        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_per_conversion
            FROM campaign
            {campaign_filter}
            DURING {date_range}
        """

        response = await client.post(
            f"/customers/{self.customer_id}/googleAds:search",
            json={"query": query},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_campaign(
        self,
        name: str,
        advertising_channel_type: str = "SEARCH",
        budget_micros: int = 10_000_000,  # $10 in micros
    ) -> dict[str, Any]:
        """Create a new Google Ads campaign.

        Args:
            name: Campaign name.
            advertising_channel_type: Channel type (SEARCH, DISPLAY, etc.).
            budget_micros: Daily budget in micros (1/1,000,000 of currency).

        Returns:
            Created campaign data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()

        # Create budget first
        budget_operation = {
            "create": {
                "name": f"Budget for {name}",
                "amount_micros": budget_micros,
                "delivery_method": "STANDARD",
            }
        }

        budget_response = await client.post(
            f"/customers/{self.customer_id}/campaignBudgets:mutate",
            json={"operations": [budget_operation]},
        )
        budget_response.raise_for_status()
        budget_result = budget_response.json()
        budget_resource = budget_result["results"][0]["resourceName"]

        # Create campaign
        campaign_operation = {
            "create": {
                "name": name,
                "advertising_channel_type": advertising_channel_type,
                "status": "PAUSED",
                "campaign_budget": budget_resource,
            }
        }

        response = await client.post(
            f"/customers/{self.customer_id}/campaigns:mutate",
            json={"operations": [campaign_operation]},
        )
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
            status: New status (ENABLED/PAUSED).

        Returns:
            Updated campaign data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        operation = {
            "update": {
                "resource_name": f"customers/{self.customer_id}/campaigns/{campaign_id}",
                "status": status,
            },
            "update_mask": {"paths": ["status"]},
        }

        response = await client.post(
            f"/customers/{self.customer_id}/campaigns:mutate",
            json={"operations": [operation]},
        )
        response.raise_for_status()
        return response.json()

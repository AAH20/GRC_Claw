"""Meta (Facebook) Ads API integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class MetaAdsClient:
    """Client for the Meta (Facebook) Marketing API.

    Provides methods to interact with Meta's advertising platform
    for campaign management, audience targeting, and performance reporting.
    """

    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(
        self,
        access_token: str,
        ad_account_id: str,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Meta Ads client.

        Args:
            access_token: Meta Marketing API access token.
            ad_account_id: Meta ad account ID (format: act_XXXXXX).
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
                headers={"Authorization": f"Bearer {self.access_token}"},
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
    async def get_campaigns(self, fields: list[str] | None = None) -> list[dict[str, Any]]:
        """Get all campaigns in the ad account.

        Args:
            fields: List of fields to retrieve.

        Returns:
            List of campaign dictionaries.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        fields = fields or ["id", "name", "status", "objective", "spend_cap"]
        client = await self._get_client()

        response = await client.get(
            f"/{self.ad_account_id}/campaigns",
            params={"fields": ",".join(fields)},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_campaign_insights(
        self,
        campaign_id: str,
        date_preset: str = "last_30d",
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get performance insights for a campaign.

        Args:
            campaign_id: The campaign ID.
            date_preset: Date range preset.
            metrics: List of metrics to retrieve.

        Returns:
            Dictionary of insight metrics.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        metrics = metrics or [
            "impressions",
            "clicks",
            "spend",
            "conversions",
            "cost_per_conversion",
            "ctr",
            "cpc",
        ]
        client = await self._get_client()

        response = await client.get(
            f"/{campaign_id}/insights",
            params={
                "date_preset": date_preset,
                "fields": ",".join(metrics),
            },
        )
        response.raise_for_status()
        data = response.json()
        insights = data.get("data", [])
        return insights[0] if insights else {}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_campaign(
        self,
        name: str,
        objective: str,
        status: str = "PAUSED",
        daily_budget: float | None = None,
        bid_strategy: str = "LOWEST_COST_WITHOUT_CAP",
    ) -> dict[str, Any]:
        """Create a new campaign.

        Args:
            name: Campaign name.
            objective: Campaign objective.
            status: Initial status (ACTIVE/PAUSED).
            daily_budget: Daily budget in cents.
            bid_strategy: Bid strategy.

        Returns:
            Created campaign data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {
            "name": name,
            "objective": objective,
            "status": status,
            "bid_strategy": bid_strategy,
        }
        if daily_budget:
            payload["daily_budget"] = int(daily_budget * 100)  # Convert to cents

        response = await client.post(
            f"/{self.ad_account_id}/campaigns",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def update_campaign_budget(
        self,
        campaign_id: str,
        daily_budget: float,
    ) -> dict[str, Any]:
        """Update a campaign's daily budget.

        Args:
            campaign_id: The campaign ID.
            daily_budget: New daily budget in USD.

        Returns:
            Updated campaign data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        client = await self._get_client()
        response = await client.post(
            f"/{campaign_id}",
            json={"daily_budget": int(daily_budget * 100)},
        )
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_ad_sets(
        self,
        campaign_id: str,
        fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get ad sets for a campaign.

        Args:
            campaign_id: The campaign ID.
            fields: List of fields to retrieve.

        Returns:
            List of ad set dictionaries.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        fields = fields or ["id", "name", "status", "daily_budget", "bid_amount"]
        client = await self._get_client()

        response = await client.get(
            f"/{campaign_id}/adsets",
            params={"fields": ",".join(fields)},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

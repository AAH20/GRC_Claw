"""LinkedIn Ads integration for the ABM platform."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class LinkedInAdsError(Exception):
    """Custom exception for LinkedIn Ads API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize LinkedInAdsError.

        Args:
            message: Error message.
            status_code: HTTP status code if available.
        """
        super().__init__(message)
        self.status_code = status_code


class LinkedInAdsClient:
    """Client for interacting with the LinkedIn Marketing API.

    Provides methods for managing ad accounts, campaigns, audiences,
    and fetching analytics data.
    """

    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(
        self,
        access_token: str,
        ad_account_id: str | None = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the LinkedIn Ads client.

        Args:
            access_token: LinkedIn OAuth2 access token.
            ad_account_id: LinkedIn ad account ID (format: urn:li:sponsoredAccount:XXXXX).
            timeout: Request timeout in seconds.
        """
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.timeout = timeout
        logger.info("LinkedInAdsClient initialized", ad_account_id=ad_account_id)

    def _get_headers(self) -> dict[str, str]:
        """Get default headers for API requests.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_ad_accounts(self) -> list[dict[str, Any]]:
        """Fetch available ad accounts.

        Returns:
            List of ad account records.

        Raises:
            LinkedInAdsError: If the request fails.
        """
        url = f"{self.BASE_URL}/adAccounts"
        params = {"q": "search"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    url, headers=self._get_headers(), params=params
                )
                response.raise_for_status()
                data = response.json()
                return data.get("elements", [])
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "LinkedIn get_ad_accounts failed",
                    status_code=exc.response.status_code,
                )
                raise LinkedInAdsError(
                    f"Failed to fetch ad accounts: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_campaigns(
        self,
        account_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch campaigns for an ad account.

        Args:
            account_id: Ad account ID (defaults to initialized account).
            limit: Maximum number of campaigns to return.

        Returns:
            List of campaign records.

        Raises:
            LinkedInAdsError: If the request fails.
            ValueError: If no account ID is available.
        """
        account = account_id or self.ad_account_id
        if not account:
            raise ValueError("ad_account_id is required")

        url = f"{self.BASE_URL}/adCampaigns"
        params = {
            "q": "search",
            "search.account.values": [account],
            "count": limit,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    url, headers=self._get_headers(), params=params
                )
                response.raise_for_status()
                data = response.json()
                return data.get("elements", [])
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "LinkedIn get_campaigns failed",
                    status_code=exc.response.status_code,
                )
                raise LinkedInAdsError(
                    f"Failed to fetch campaigns: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_account_list(
        self,
        name: str,
        account_ids: list[str],
    ) -> dict[str, Any]:
        """Create an account list (matched audience) for ABM targeting.

        Args:
            name: Name for the account list.
            account_ids: List of organization URNs to include.

        Returns:
            Created account list record.

        Raises:
            LinkedInAdsError: If creation fails.
        """
        url = f"{self.BASE_URL}/accountLists"
        payload = {
            "name": name,
            "type": "COMPANY",
            "accountIds": account_ids,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url, headers=self._get_headers(), json=payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "LinkedIn create_account_list failed",
                    status_code=exc.response.status_code,
                )
                raise LinkedInAdsError(
                    f"Failed to create account list: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_campaign_analytics(
        self,
        campaign_id: str,
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch analytics for a specific campaign.

        Args:
            campaign_id: The campaign URN.
            metrics: List of metrics to fetch (impressions, clicks, etc.).

        Returns:
            Analytics data for the campaign.

        Raises:
            LinkedInAdsError: If the request fails.
        """
        default_metrics = ["impressions", "clicks", "costInLocalCurrency", "externalWebsiteConversions"]
        selected_metrics = metrics or default_metrics

        url = f"{self.BASE_URL}/adAnalytics"
        params = {
            "q": "analytics",
            "pivot": "CAMPAIGN",
            "campaigns[0]": campaign_id,
            "fields": ",".join(selected_metrics),
            "dateRange.start.day": 1,
            "dateRange.start.month": 1,
            "dateRange.start.year": 2024,
            "timeGranularity": "DAILY",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    url, headers=self._get_headers(), params=params
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "LinkedIn get_campaign_analytics failed",
                    status_code=exc.response.status_code,
                )
                raise LinkedInAdsError(
                    f"Failed to fetch analytics: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_sponsored_content(
        self,
        account_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Create sponsored content (ad) for an account.

        Args:
            account_id: The ad account URN.
            payload: Sponsored content configuration.

        Returns:
            Created sponsored content record.

        Raises:
            LinkedInAdsError: If creation fails.
        """
        url = f"{self.BASE_URL}/sponsoredContent"
        content_payload = {
            "account": account_id,
            **payload,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url, headers=self._get_headers(), json=content_payload
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "LinkedIn create_sponsored_content failed",
                    status_code=exc.response.status_code,
                )
                raise LinkedInAdsError(
                    f"Failed to create sponsored content: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

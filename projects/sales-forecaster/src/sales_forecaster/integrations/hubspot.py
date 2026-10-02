"""HubSpot CRM integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
import structlog

from sales_forecaster.core import get_settings
from sales_forecaster.core.exceptions import AuthenticationError, IntegrationError
from sales_forecaster.core.retry import async_retry

logger = structlog.get_logger(__name__)


class HubSpotIntegration:
    """Integration with HubSpot CRM via REST API.

    Handles authentication, deal querying, and data normalization.
    """

    def __init__(
        self,
        api_key: str | None = None,
        portal_id: str | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        """Initialize HubSpot integration.

        Args:
            api_key: HubSpot API key.
            portal_id: HubSpot portal ID.
            timeout_seconds: HTTP request timeout.
        """
        settings = get_settings()
        self.api_key = api_key or settings.hubspot_api_key
        self.portal_id = portal_id or settings.hubspot_portal_id
        self.timeout_seconds = timeout_seconds
        self._base_url = "https://api.hubapi.com"

    @property
    def is_configured(self) -> bool:
        """Check if the integration is properly configured."""
        return bool(self.api_key)

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests.

        Returns:
            Dictionary of HTTP headers.
        """
        if not self.api_key:
            raise AuthenticationError(
                "HubSpot API key not configured",
                source="hubspot",
            )
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @async_retry(
        max_attempts=3,
        base_delay=1.0,
        retryable_exceptions=(ConnectionError, TimeoutError),
    )
    async def get_deals(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Fetch deals from HubSpot.

        Args:
            start_date: Start date for deal creation.
            end_date: End date for deal creation.
            limit: Maximum number of records to fetch.

        Returns:
            List of raw deal records.

        Raises:
            IntegrationError: If the API request fails.
        """
        if not self.is_configured:
            raise AuthenticationError(
                "HubSpot integration not configured",
                source="hubspot",
            )

        url = f"{self._base_url}/crm/v3/objects/deals"
        params: dict[str, Any] = {
            "limit": min(limit, 100),
            "properties": (
                "dealname,amount,closedate,createdate,dealstage,"
                "hubspot_owner_id,hs_currency_code"
            ),
        }

        all_deals: list[dict[str, Any]] = []
        after: str | None = None

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            while True:
                if after:
                    params["after"] = after

                response = await client.get(url, headers=self._get_headers(), params=params)

                if response.status_code != 200:
                    raise IntegrationError(
                        f"HubSpot API request failed: {response.text}",
                        source="hubspot",
                        status_code=response.status_code,
                    )

                data = response.json()
                deals = data.get("results", [])
                all_deals.extend(deals)

                paging = data.get("paging", {})
                next_page = paging.get("next", {})
                after = next_page.get("after")

                if not after or len(all_deals) >= limit:
                    break

        filtered: list[dict[str, Any]] = []
        for deal in all_deals:
            props = deal.get("properties", {})
            created = props.get("createdate", "")
            if created:
                deal_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if start_date <= deal_date <= end_date:
                    filtered.append(deal)

        logger.info("Fetched deals from HubSpot", total=len(all_deals), filtered=len(filtered))
        return filtered[:limit]

    async def get_companies(self, limit: int = 500) -> list[dict[str, Any]]:
        """Fetch companies from HubSpot.

        Args:
            limit: Maximum number of records to fetch.

        Returns:
            List of raw company records.

        Raises:
            IntegrationError: If the API request fails.
        """
        if not self.is_configured:
            raise AuthenticationError(
                "HubSpot integration not configured",
                source="hubspot",
            )

        url = f"{self._base_url}/crm/v3/objects/companies"
        params: dict[str, Any] = {
            "limit": min(limit, 100),
            "properties": "name,industry,region,annual_revenue",
        }

        all_companies: list[dict[str, Any]] = []
        after: str | None = None

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            while True:
                if after:
                    params["after"] = after

                response = await client.get(url, headers=self._get_headers(), params=params)

                if response.status_code != 200:
                    raise IntegrationError(
                        f"HubSpot API request failed: {response.text}",
                        source="hubspot",
                        status_code=response.status_code,
                    )

                data = response.json()
                companies = data.get("results", [])
                all_companies.extend(companies)

                paging = data.get("paging", {})
                next_page = paging.get("next", {})
                after = next_page.get("after")

                if not after or len(all_companies) >= limit:
                    break

        return all_companies[:limit]

    async def health_check(self) -> bool:
        """Check if the HubSpot connection is healthy.

        Returns:
            True if the connection is healthy, False otherwise.
        """
        if not self.is_configured:
            return False

        try:
            url = f"{self._base_url}/crm/v3/objects/deals"
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    url, headers=self._get_headers(), params={"limit": 1}
                )
                return response.status_code == 200
        except Exception as exc:
            logger.warning("HubSpot health check failed", error=str(exc))
            return False

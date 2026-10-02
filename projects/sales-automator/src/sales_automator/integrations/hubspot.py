"""HubSpot integration client."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from sales_automator.config import get_settings

logger = structlog.get_logger(__name__)


class HubSpotError(Exception):
    """HubSpot API error."""


class HubSpotClient:
    """Client for HubSpot API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.hubspot_api_key
        self.portal_id = settings.hubspot_portal_id
        self.base_url = "https://api.hubapi.com"
        self.logger = logger.bind(integration="hubspot")

    def _headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request to HubSpot API.

        Args:
            method: HTTP method.
            path: API path.
            **kwargs: Additional request arguments.

        Returns:
            Response data.

        Raises:
            HubSpotError: If the request fails.
        """
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(),
                timeout=30.0,
                **kwargs,
            )
            if response.status_code >= 400:
                raise HubSpotError(f"API error {response.status_code}: {response.text}")
            return response.json() if response.content else {}

    async def get_contacts(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get contacts from HubSpot.

        Args:
            limit: Maximum number of contacts.

        Returns:
            List of contacts.
        """
        self.logger.info("Fetching contacts", limit=limit)
        result = await self._request("GET", f"/crm/v3/objects/contacts?limit={limit}")
        return result.get("results", [])

    async def get_deals(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get deals from HubSpot.

        Args:
            limit: Maximum number of deals.

        Returns:
            List of deals.
        """
        self.logger.info("Fetching deals", limit=limit)
        result = await self._request("GET", f"/crm/v3/objects/deals?limit={limit}")
        return result.get("results", [])

    async def create_contact(self, contact_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new contact in HubSpot.

        Args:
            contact_data: Contact data.

        Returns:
            Created contact.
        """
        self.logger.info("Creating contact", email=contact_data.get("properties", {}).get("email"))
        return await self._request(
            "POST",
            "/crm/v3/objects/contacts",
            json={"properties": contact_data},
        )

    async def update_contact(self, contact_id: str, contact_data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing contact.

        Args:
            contact_id: Contact ID.
            contact_data: Updated contact data.

        Returns:
            Updated contact.
        """
        self.logger.info("Updating contact", contact_id=contact_id)
        return await self._request(
            "PATCH",
            f"/crm/v3/objects/contacts/{contact_id}",
            json={"properties": contact_data},
        )

    async def get_companies(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get companies from HubSpot.

        Args:
            limit: Maximum number of companies.

        Returns:
            List of companies.
        """
        self.logger.info("Fetching companies", limit=limit)
        result = await self._request("GET", f"/crm/v3/objects/companies?limit={limit}")
        return result.get("results", [])

    async def create_engagement(self, engagement_data: dict[str, Any]) -> dict[str, Any]:
        """Create an engagement (note, email, call, etc.).

        Args:
            engagement_data: Engagement data.

        Returns:
            Created engagement.
        """
        self.logger.info(
            "Creating engagement",
            type=engagement_data.get("engagement", {}).get("type"),
        )
        return await self._request(
            "POST",
            "/engagements/v1/engagements",
            json=engagement_data,
        )

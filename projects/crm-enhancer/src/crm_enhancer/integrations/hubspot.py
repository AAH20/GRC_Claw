"""HubSpot integration module."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class HubSpotError(Exception):
    """HubSpot API error."""


class HubSpotClient:
    """Client for HubSpot API integration.

    Provides methods to interact with HubSpot CRM including
    contact management, deal tracking, and engagement data.
    """

    def __init__(self, api_key: str, app_id: str = "") -> None:
        """Initialize HubSpot client.

        Args:
            api_key: HubSpot API key.
            app_id: HubSpot app ID.
        """
        self.api_key = api_key
        self.app_id = app_id
        self._base_url = "https://api.hubapi.com"
        self._rate_limit = 10  # requests per second

        logger.info("HubSpotClient initialized")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_contacts(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get contacts from HubSpot.

        Args:
            limit: Maximum number of contacts to retrieve.

        Returns:
            List of contact records.
        """
        logger.info("Fetching contacts from HubSpot", limit=limit)

        url = f"{self._base_url}/crm/v3/objects/cont"
        params = {"limit": limit, "properties": "email,firstname,lastname,phone,company"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        contacts = data.get("results", [])
        logger.info("Contacts fetched", count=len(contacts))
        return contacts

    async def get_deals(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get deals from HubSpot.

        Args:
            limit: Maximum number of deals to retrieve.

        Returns:
            List of deal records.
        """
        logger.info("Fetching deals from HubSpot", limit=limit)

        url = f"{self._base_url}/crm/v3/objects/deals"
        params = {"limit": limit, "properties": "dealname,amount,dealstage,closedate"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        deals = data.get("results", [])
        logger.info("Deals fetched", count=len(deals))
        return deals

    async def create_contact(self, properties: dict[str, Any]) -> dict[str, Any]:
        """Create a contact in HubSpot.

        Args:
            properties: Contact properties.

        Returns:
            Created contact record.
        """
        logger.info("Creating contact in HubSpot")

        url = f"{self._base_url}/crm/v3/objects/cont"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json={"properties": properties},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def update_contact(self, contact_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        """Update a contact in HubSpot.

        Args:
            contact_id: Contact ID to update.
            properties: Properties to update.

        Returns:
            Updated contact record.
        """
        logger.info("Updating contact", contact_id=contact_id)

        url = f"{self._base_url}/crm/v3/objects/cont/{contact_id}"

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=self._get_headers(),
                json={"properties": properties},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_engagements(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get engagements from HubSpot.

        Args:
            limit: Maximum number of engagements to retrieve.

        Returns:
            List of engagement records.
        """
        logger.info("Fetching engagements from HubSpot", limit=limit)

        url = f"{self._base_url}/engagements/v1/engagements/paged"
        params = {"limit": limit}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        engagements = data.get("results", [])
        logger.info("Engagements fetched", count=len(engagements))
        return engagements

    async def health_check(self) -> bool:
        """Check HubSpot API connectivity.

        Returns:
            True if connection is healthy.
        """
        try:
            url = f"{self._base_url}/integrations/v1/me"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception as exc:
            logger.error("HubSpot health check failed", error=str(exc))
            return False

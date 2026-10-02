"""HubSpot integration client for the Broker Enablement platform."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class HubSpotClient:
    """Client for HubSpot API integration.

    Handles contact management, deal tracking, and marketing automation
    for partner data synchronization with HubSpot.
    """

    def __init__(
        self,
        api_key: str,
        portal_id: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the HubSpot client.

        Args:
            api_key: HubSpot API key.
            portal_id: HubSpot portal ID.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key
        self.portal_id = portal_id
        self.timeout = timeout
        self._base_url = "https://api.hubapi.com"

        logger.info("HubSpotClient initialized")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authorization.

        Returns:
            Headers dictionary.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_contact(self, contact_data: dict[str, Any]) -> dict[str, Any]:
        """Create a contact in HubSpot.

        Args:
            contact_data: Contact properties to create.

        Returns:
            Created contact data from HubSpot.

        Raises:
            RuntimeError: If creation fails.
        """
        logger.info("Creating HubSpot contact", email=contact_data.get("email"))

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self._base_url}/crm/v3/objects/contacts",
                    json={"properties": contact_data},
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to create HubSpot contact",
                status_code=e.response.status_code,
                response=e.response.text,
            )
            raise RuntimeError(f"Failed to create HubSpot contact: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def update_contact(
        self, contact_id: str, contact_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a contact in HubSpot.

        Args:
            contact_id: The HubSpot contact ID.
            contact_data: Contact properties to update.

        Returns:
            Updated contact data from HubSpot.

        Raises:
            RuntimeError: If update fails.
        """
        logger.info("Updating HubSpot contact", contact_id=contact_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    f"{self._base_url}/crm/v3/objects/contacts/{contact_id}",
                    json={"properties": contact_data},
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to update HubSpot contact",
                contact_id=contact_id,
                status_code=e.response.status_code,
            )
            raise RuntimeError(f"Failed to update HubSpot contact: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_deal(self, deal_data: dict[str, Any]) -> dict[str, Any]:
        """Create a deal in HubSpot.

        Args:
            deal_data: Deal properties to create.

        Returns:
            Created deal data from HubSpot.

        Raises:
            RuntimeError: If creation fails.
        """
        logger.info("Creating HubSpot deal", deal_name=deal_data.get("dealname"))

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self._base_url}/crm/v3/objects/deals",
                    json={"properties": deal_data},
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to create HubSpot deal",
                status_code=e.response.status_code,
                response=e.response.text,
            )
            raise RuntimeError(f"Failed to create HubSpot deal: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_contact_by_email(self, email: str) -> dict[str, Any] | None:
        """Get a contact by email address.

        Args:
            email: The contact email address.

        Returns:
            Contact data if found, None otherwise.

        Raises:
            RuntimeError: If the request fails.
        """
        logger.info("Fetching HubSpot contact by email", email=email)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self._base_url}/crm/v3/objects/contacts/search",
                    json={
                        "filterGroups": [
                            {
                                "filters": [
                                    {
                                        "propertyName": "email",
                                        "operator": "EQ",
                                        "value": email,
                                    }
                                ]
                            }
                        ]
                    },
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                return results[0] if results else None

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to fetch HubSpot contact",
                status_code=e.response.status_code,
            )
            raise RuntimeError(f"Failed to fetch HubSpot contact: {e}") from e

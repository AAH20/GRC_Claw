"""HubSpot CRM integration for the ABM platform."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class HubSpotError(Exception):
    """Custom exception for HubSpot API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize HubSpotError.

        Args:
            message: Error message.
            status_code: HTTP status code if available.
        """
        super().__init__(message)
        self.status_code = status_code


class HubSpotClient:
    """Client for interacting with the HubSpot API.

    Provides methods for managing contacts, companies, deals, and
    engagement data using HubSpot's v3 API.
    """

    BASE_URL = "https://api.hubapi.com"

    def __init__(
        self,
        api_key: str,
        portal_id: str | None = None,
        timeout: int = 30,
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
        logger.info("HubSpotClient initialized", portal_id=portal_id)

    def _get_headers(self) -> dict[str, str]:
        """Get default headers for API requests.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_companies(
        self,
        limit: int = 100,
        properties: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch companies from HubSpot.

        Args:
            limit: Maximum number of companies to return.
            properties: List of company properties to include.

        Returns:
            List of company records.

        Raises:
            HubSpotError: If the request fails.
        """
        url = f"{self.BASE_URL}/companies/v2/companies/paged"
        params: dict[str, Any] = {"limit": limit}
        if properties:
            params["properties"] = properties

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    url, headers=self._get_headers(), params=params
                )
                response.raise_for_status()
                data = response.json()
                return data.get("companies", [])
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "HubSpot get_companies failed",
                    status_code=exc.response.status_code,
                )
                raise HubSpotError(
                    f"Failed to fetch companies: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_contacts(
        self,
        limit: int = 100,
        properties: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch contacts from HubSpot.

        Args:
            limit: Maximum number of contacts to return.
            properties: List of contact properties to include.

        Returns:
            List of contact records.

        Raises:
            HubSpotError: If the request fails.
        """
        url = f"{self.BASE_URL}/contacts/v1/lists/all/contacts/all"
        params: dict[str, Any] = {"count": limit}
        if properties:
            params["property"] = properties

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    url, headers=self._get_headers(), params=params
                )
                response.raise_for_status()
                data = response.json()
                return data.get("contacts", [])
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "HubSpot get_contacts failed",
                    status_code=exc.response.status_code,
                )
                raise HubSpotError(
                    f"Failed to fetch contacts: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_deals(
        self,
        limit: int = 100,
        pipeline: str | None = None,
        dealstage: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch deals from HubSpot.

        Args:
            limit: Maximum number of deals to return.
            pipeline: Optional pipeline filter.
            dealstage: Optional deal stage filter.

        Returns:
            List of deal records.

        Raises:
            HubSpotError: If the request fails.
        """
        url = f"{self.BASE_URL}/deals/v1/deal/paged"
        params: dict[str, Any] = {"limit": limit}
        if pipeline:
            params["pipeline"] = pipeline
        if dealstage:
            params["dealstage"] = dealstage

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    url, headers=self._get_headers(), params=params
                )
                response.raise_for_status()
                data = response.json()
                return data.get("deals", [])
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "HubSpot get_deals failed",
                    status_code=exc.response.status_code,
                )
                raise HubSpotError(
                    f"Failed to fetch deals: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_engagement(self, engagement_data: dict[str, Any]) -> dict[str, Any]:
        """Create an engagement (note, email, call, meeting) in HubSpot.

        Args:
            engagement_data: Engagement data including type, metadata, and associations.

        Returns:
            Created engagement record.

        Raises:
            HubSpotError: If creation fails.
        """
        url = f"{self.BASE_URL}/engagements/v1/engagements"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url, headers=self._get_headers(), json=engagement_data
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "HubSpot create_engagement failed",
                    status_code=exc.response.status_code,
                )
                raise HubSpotError(
                    f"Failed to create engagement: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_engagements(
        self,
        contact_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch engagements for a specific contact.

        Args:
            contact_id: The HubSpot contact/vid ID.
            limit: Maximum number of engagements to return.

        Returns:
            List of engagement records.

        Raises:
            HubSpotError: If the request fails.
        """
        url = f"{self.BASE_URL}/engagements/v1/engagements/associated/contact/{contact_id}/paged"
        params = {"limit": limit}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    url, headers=self._get_headers(), params=params
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "HubSpot get_engagements failed",
                    status_code=exc.response.status_code,
                )
                raise HubSpotError(
                    f"Failed to fetch engagements: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

"""LinkedIn integration client."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from sales_automator.config import get_settings

logger = structlog.get_logger(__name__)


class LinkedInError(Exception):
    """LinkedIn API error."""


class LinkedInClient:
    """Client for LinkedIn API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client_id = settings.linkedin_client_id
        self.client_secret = settings.linkedin_client_secret
        self.access_token = settings.linkedin_access_token
        self.base_url = "https://api.linkedin.com/v2"
        self.logger = logger.bind(integration="linkedin")

    def _headers(self) -> dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request to LinkedIn API.

        Args:
            method: HTTP method.
            path: API path.
            **kwargs: Additional request arguments.

        Returns:
            Response data.

        Raises:
            LinkedInError: If the request fails.
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
                raise LinkedInError(f"API error {response.status_code}: {response.text}")
            return response.json() if response.content else {}

    async def search_people(
        self,
        keywords: str,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """Search for people on LinkedIn.

        Args:
            keywords: Search keywords.
            limit: Maximum number of results.

        Returns:
            List of people profiles.
        """
        self.logger.info("Searching people", keywords=keywords, limit=limit)
        result = await self._request(
            "GET",
            f"/search?q=keywords&keywords={keywords}&count={limit}",
        )
        return result.get("elements", [])

    async def get_profile(self, profile_id: str) -> dict[str, Any]:
        """Get a LinkedIn profile.

        Args:
            profile_id: LinkedIn profile ID or vanity name.

        Returns:
            Profile data.
        """
        self.logger.info("Getting profile", profile_id=profile_id)
        return await self._request("GET", f"/people/{profile_id}")

    async def send_message(
        self,
        recipient_id: str,
        message: str,
    ) -> dict[str, Any]:
        """Send a LinkedIn message.

        Args:
            recipient_id: Recipient's LinkedIn ID.
            message: Message body.

        Returns:
            Message send result.
        """
        self.logger.info("Sending message", recipient_id=recipient_id)
        payload = {
            "message": {
                "body": {
                    "text": message,
                },
            },
            "recipients": [
                {"person": f"urn:li:person:{recipient_id}"},
            ],
        }
        return await self._request("POST", "/messages", json=payload)

    async def get_connections(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get connections.

        Args:
            limit: Maximum number of connections.

        Returns:
            List of connections.
        """
        self.logger.info("Getting connections", limit=limit)
        result = await self._request("GET", f"/connections?count={limit}")
        return result.get("elements", [])

    async def search_companies(
        self,
        keywords: str,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """Search for companies on LinkedIn.

        Args:
            keywords: Search keywords.
            limit: Maximum number of results.

        Returns:
            List of companies.
        """
        self.logger.info("Searching companies", keywords=keywords, limit=limit)
        result = await self._request(
            "GET",
            f"/search?q=companySearchKeywords&keywords={keywords}&count={limit}",
        )
        return result.get("elements", [])

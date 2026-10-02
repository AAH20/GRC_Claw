"""HubSpot integration adapter."""

from __future__ import annotations

from typing import Any

from compliance.integrations.base import BaseIntegrationClient


class HubSpotClient(BaseIntegrationClient):
    """Client for retrieving marketing content from HubSpot."""

    name = "hubspot"

    def __init__(
        self,
        *,
        access_token: str,
        api_version: str = "v3",
        timeout: float = 30.0,
    ) -> None:
        """Initialise the HubSpot client.

        Args:
            access_token: Private app access token.
            api_version: HubSpot API version.
            timeout: Per-request timeout in seconds.
        """
        super().__init__(
            "https://api.hubapi.com",
            timeout=timeout,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.api_version = api_version

    async def fetch_campaigns(self, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch marketing emails.

        Args:
            limit: Maximum number of emails to return.

        Returns:
            A list of normalised campaign records.
        """
        data = await self.request(
            "GET",
            f"/marketing/{self.api_version}/emails",
            params={"limit": limit},
        )
        results = data.get("results", [])
        return [
            {
                "id": str(item.get("id")),
                "source": self.name,
                "content": item.get("subject", ""),
                "channel": "email",
                "metadata": {"name": item.get("name"), "state": item.get("state")},
            }
            for item in results
        ]

    async def fetch_contacts(self, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch contacts (used for consent auditing).

        Args:
            limit: Maximum number of contacts to return.

        Returns:
            A list of contact records.
        """
        data = await self.request(
            "GET",
            f"/crm/{self.api_version}/objects/contacts",
            params={"limit": limit},
        )
        return list(data.get("results", []))

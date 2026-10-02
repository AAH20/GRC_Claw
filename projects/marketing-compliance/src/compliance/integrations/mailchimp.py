"""Mailchimp integration adapter."""

from __future__ import annotations

from typing import Any

from compliance.integrations.base import BaseIntegrationClient, IntegrationError


class MailchimpClient(BaseIntegrationClient):
    """Client for retrieving campaign content from Mailchimp."""

    name = "mailchimp"

    def __init__(
        self,
        *,
        api_key: str,
        server_prefix: str,
        api_version: str = "3.0",
        timeout: float = 30.0,
    ) -> None:
        """Initialise the Mailchimp client.

        Args:
            api_key: Mailchimp API key.
            server_prefix: Datacenter prefix (e.g. ``us1``).
            api_version: Mailchimp API version.
            timeout: Per-request timeout in seconds.

        Raises:
            IntegrationError: If required configuration is missing.
        """
        if not api_key or not server_prefix:
            raise IntegrationError("mailchimp requires both api_key and server_prefix")
        super().__init__(f"https://{server_prefix}.api.mailchimp.com", timeout=timeout)
        self.api_key = api_key
        self.api_version = api_version
        self.headers["Authorization"] = f"apikey {api_key}"

    async def fetch_campaigns(self, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch campaigns.

        Args:
            limit: Maximum number of campaigns to return.

        Returns:
            A list of normalised campaign records.
        """
        data = await self.request(
            "GET",
            f"/{self.api_version}/campaigns",
            params={"count": limit},
        )
        campaigns = data.get("campaigns", [])
        return [
            {
                "id": str(campaign.get("id")),
                "source": self.name,
                "content": campaign.get("settings", {}).get("subject_line", ""),
                "channel": "email",
                "metadata": {
                    "title": campaign.get("settings", {}).get("title"),
                    "status": campaign.get("status"),
                },
            }
            for campaign in campaigns
        ]

    async def fetch_audiences(self, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch audience (list) definitions.

        Args:
            limit: Maximum number of audiences to return.

        Returns:
            A list of audience records.
        """
        data = await self.request(
            "GET",
            f"/{self.api_version}/lists",
            params={"count": limit},
        )
        return list(data.get("lists", []))

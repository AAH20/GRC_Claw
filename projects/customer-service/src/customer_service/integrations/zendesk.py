"""Zendesk integration module."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class ZendeskClient:
    """Client for interacting with the Zendesk API.

    Provides methods for creating, updating, and retrieving tickets
    from Zendesk with automatic retry and error handling.
    """

    def __init__(
        self,
        subdomain: str,
        email: str,
        api_token: str,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Zendesk client.

        Args:
            subdomain: Zendesk subdomain.
            email: Zendesk account email.
            api_token: Zendesk API token.
            base_url: Optional custom base URL.
            timeout: Request timeout in seconds.
        """
        self._subdomain = subdomain
        self._email = email
        self._api_token = api_token
        self._base_url = base_url or f"https://{subdomain}.zendesk.com/api/v2"
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            auth=(f"{email}/token", api_token),
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def create_ticket(
        self,
        subject: str,
        description: str,
        requester_email: str,
        priority: str = "normal",
        tags: list[str] | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new ticket in Zendesk.

        Args:
            subject: Ticket subject.
            description: Ticket description.
            requester_email: Email of the requester.
            priority: Ticket priority (low, normal, high, urgent).
            tags: Optional list of tags.
            custom_fields: Optional custom field values.

        Returns:
            Created ticket data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        payload: dict[str, Any] = {
            "ticket": {
                "subject": subject,
                "description": description,
                "requester": {"email": requester_email},
                "priority": priority,
            }
        }
        if tags:
            payload["ticket"]["tags"] = tags
        if custom_fields:
            payload["ticket"]["custom_fields"] = [
                {"id": k, "value": v} for k, v in custom_fields.items()
            ]

        response = await self._client.post("/tickets.json", json=payload)
        response.raise_for_status()
        logger.info("Zendesk ticket created", ticket_id=response.json().get("ticket", {}).get("id"))
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_ticket(self, ticket_id: int) -> dict[str, Any]:
        """Retrieve a ticket from Zendesk.

        Args:
            ticket_id: The Zendesk ticket ID.

        Returns:
            Ticket data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        response = await self._client.get(f"/tickets/{ticket_id}.json")
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def update_ticket(
        self,
        ticket_id: int,
        comment: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update an existing Zendesk ticket.

        Args:
            ticket_id: The Zendesk ticket ID.
            comment: Optional comment to add.
            status: Optional new status.
            priority: Optional new priority.
            tags: Optional updated tags.

        Returns:
            Updated ticket data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        payload: dict[str, Any] = {"ticket": {}}
        if comment:
            payload["ticket"]["comment"] = {"body": comment}
        if status:
            payload["ticket"]["status"] = status
        if priority:
            payload["ticket"]["priority"] = priority
        if tags:
            payload["ticket"]["tags"] = tags

        response = await self._client.put(f"/tickets/{ticket_id}.json", json=payload)
        response.raise_for_status()
        logger.info("Zendesk ticket updated", ticket_id=ticket_id)
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def search_tickets(self, query: str, per_page: int = 30) -> dict[str, Any]:
        """Search for tickets in Zendesk.

        Args:
            query: Search query string.
            per_page: Number of results per page.

        Returns:
            Search results.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        response = await self._client.get(
            "/search.json",
            params={"query": query, "per_page": per_page},
        )
        response.raise_for_status()
        return response.json()

"""Intercom integration module."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class IntercomClient:
    """Client for interacting with the Intercom API.

    Provides methods for managing contacts, conversations, and messages
    in Intercom with automatic retry and error handling.
    """

    def __init__(
        self,
        access_token: str,
        base_url: str = "https://api.intercom.io",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Intercom client.

        Args:
            access_token: Intercom access token.
            base_url: Intercom API base URL.
            timeout: Request timeout in seconds.
        """
        self._access_token = access_token
        self._base_url = base_url
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def create_contact(
        self,
        email: str,
        name: str | None = None,
        phone: str | None = None,
        custom_attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new contact in Intercom.

        Args:
            email: Contact email address.
            name: Optional contact name.
            phone: Optional contact phone number.
            custom_attributes: Optional custom attributes.

        Returns:
            Created contact data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        payload: dict[str, Any] = {"email": email}
        if name:
            payload["name"] = name
        if phone:
            payload["phone"] = phone
        if custom_attributes:
            payload["custom_attributes"] = custom_attributes

        response = await self._client.post("/contacts", json=payload)
        response.raise_for_status()
        logger.info("Intercom contact created", email=email)
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Retrieve a contact from Intercom.

        Args:
            contact_id: The Intercom contact ID.

        Returns:
            Contact data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        response = await self._client.get(f"/contacts/{contact_id}")
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def create_conversation(
        self,
        contact_id: str,
        message: str,
        admin_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new conversation in Intercom.

        Args:
            contact_id: The contact ID.
            message: The message body.
            admin_id: Optional admin assignee ID.

        Returns:
            Created conversation data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        payload: dict[str, Any] = {
            "from": {"type": "contact", "id": contact_id},
            "body": message,
        }
        if admin_id:
            payload["assignee_id"] = admin_id

        response = await self._client.post("/conversations", json=payload)
        response.raise_for_status()
        logger.info("Intercom conversation created", contact_id=contact_id)
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def reply_to_conversation(
        self,
        conversation_id: str,
        message: str,
        admin_id: str | None = None,
    ) -> dict[str, Any]:
        """Reply to an existing Intercom conversation.

        Args:
            conversation_id: The conversation ID.
            message: The reply message body.
            admin_id: Optional admin ID.

        Returns:
            Reply data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        payload: dict[str, Any] = {
            "type": "admin",
            "body": message,
            "message_type": "comment",
        }
        if admin_id:
            payload["admin_id"] = admin_id

        response = await self._client.post(
            f"/conversations/{conversation_id}/reply",
            json=payload,
        )
        response.raise_for_status()
        logger.info("Intercom conversation replied", conversation_id=conversation_id)
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def search_contacts(self, query: str) -> dict[str, Any]:
        """Search for contacts in Intercom.

        Args:
            query: Search query string.

        Returns:
            Search results.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        response = await self._client.post(
            "/contacts/search",
            json={"query": {"field": "email", "operator": "=", "value": query}},
        )
        response.raise_for_status()
        return response.json()

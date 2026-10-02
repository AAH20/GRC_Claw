"""Salesforce CRM integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class SalesforceClient:
    """Client for Salesforce CRM API integration.

    Handles authentication, contact/lead management, and journey
    data synchronization with Salesforce.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        security_token: str,
        domain: str = "https://login.salesforce.com",
    ) -> None:
        """Initialize the Salesforce client.

        Args:
            client_id: Salesforce OAuth client ID.
            client_secret: Salesforce OAuth client secret.
            username: Salesforce username.
            password: Salesforce password.
            security_token: Salesforce security token.
            domain: Salesforce login domain.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.security_token = security_token
        self.domain = domain
        self.access_token: str | None = None
        self.instance_url: str | None = None
        self.logger = logger.bind(integration="salesforce")

    async def authenticate(self) -> None:
        """Authenticate with Salesforce using OAuth2 username-password flow.

        Raises:
            httpx.HTTPStatusError: If authentication fails.
        """
        auth_url = f"{self.domain}/services/oauth2/token"
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": f"{self.password}{self.security_token}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(auth_url, data=payload)
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            self.instance_url = data["instance_url"]

        self.logger.info("Authenticated with Salesforce")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Get a contact by ID from Salesforce.

        Args:
            contact_id: The Salesforce contact ID.

        Returns:
            The contact data.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.instance_url}/services/data/v58.0/sobjects/Contact/{contact_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def upsert_journey_data(
        self, contact_id: str, journey_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Upsert journey data to a Salesforce contact.

        Args:
            contact_id: The Salesforce contact ID.
            journey_data: The journey data to store.

        Returns:
            The API response.

        Raises:
            httpx.HTTPStatusError: If the request fails.
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.instance_url}/services/data/v58.0/sobjects/Contact/{contact_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {"Journey_Data__c": str(journey_data)}

        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=headers, json=payload)
            response.raise_for_status()
            return {"success": True, "contact_id": contact_id}

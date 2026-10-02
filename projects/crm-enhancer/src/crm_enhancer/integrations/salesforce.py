"""Salesforce integration module."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class SalesforceError(Exception):
    """Salesforce API error."""


class SalesforceClient:
    """Client for Salesforce API integration.

    Provides methods to interact with Salesforce CRM including
    contact management, deal tracking, and data synchronization.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        security_token: str = "",
        sandbox: bool = False,
    ) -> None:
        """Initialize Salesforce client.

        Args:
            client_id: OAuth client ID.
            client_secret: OAuth client secret.
            username: Salesforce username.
            password: Salesforce password.
            security_token: Security token for API access.
            sandbox: Whether to use sandbox environment.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password + security_token
        self.sandbox = sandbox
        self._access_token: str | None = None
        self._instance_url: str | None = None

        domain = "test" if sandbox else "login"
        self._auth_url = f"https://{domain}.salesforce.com/services/oauth2/token"
        self._api_version = "v58.0"

        logger.info("SalesforceClient initialized", sandbox=sandbox)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def authenticate(self) -> None:
        """Authenticate with Salesforce using OAuth2."""
        logger.info("Authenticating with Salesforce")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._auth_url,
                data={
                    "grant_type": "password",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "username": self.username,
                    "password": self.password,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        self._access_token = data["access_token"]
        self._instance_url = data["instance_url"]
        logger.info("Salesforce authentication successful")

    async def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated."""
        if not self._access_token:
            await self.authenticate()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def get_contacts(self, limit: int = 200) -> list[dict[str, Any]]:
        """Get contacts from Salesforce.

        Args:
            limit: Maximum number of contacts to retrieve.

        Returns:
            List of contact records.
        """
        await self._ensure_authenticated()
        logger.info("Fetching contacts from Salesforce", limit=limit)

        query = (
            f"SELECT Id, FirstName, LastName, Email, Phone, "
            f"Account.Name FROM Contact LIMIT {limit}"
        )
        url = f"{self._instance_url}/services/data/{self._api_version}/query"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params={"q": query},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        contacts = data.get("records", [])
        logger.info("Contacts fetched", count=len(contacts))
        return contacts

    async def get_opportunities(self, limit: int = 200) -> list[dict[str, Any]]:
        """Get opportunities from Salesforce.

        Args:
            limit: Maximum number of opportunities to retrieve.

        Returns:
            List of opportunity records.
        """
        await self._ensure_authenticated()
        logger.info("Fetching opportunities from Salesforce", limit=limit)

        query = (
            f"SELECT Id, Name, Amount, StageName, CloseDate, Account.Name "
            f"FROM Opportunity LIMIT {limit}"
        )
        url = f"{self._instance_url}/services/data/{self._api_version}/query"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params={"q": query},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        opportunities = data.get("records", [])
        logger.info("Opportunities fetched", count=len(opportunities))
        return opportunities

    async def create_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """Create a task in Salesforce.

        Args:
            task_data: Task data to create.

        Returns:
            Created task record.
        """
        await self._ensure_authenticated()
        logger.info("Creating task in Salesforce")

        url = f"{self._instance_url}/services/data/{self._api_version}/sobjects/Task"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=task_data,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def update_contact(self, contact_id: str, data: dict[str, Any]) -> None:
        """Update a contact in Salesforce.

        Args:
            contact_id: Contact ID to update.
            data: Data to update.
        """
        await self._ensure_authenticated()
        logger.info("Updating contact", contact_id=contact_id)

        url = (
            f"{self._instance_url}/services/data/{self._api_version}"
            f"/sobjects/Contact/{contact_id}"
        )

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=self._get_headers(),
                json=data,
                timeout=30.0,
            )
            response.raise_for_status()

    async def health_check(self) -> bool:
        """Check Salesforce API connectivity.

        Returns:
            True if connection is healthy.
        """
        try:
            await self._ensure_authenticated()
            return True
        except Exception as exc:
            logger.error("Salesforce health check failed", error=str(exc))
            return False

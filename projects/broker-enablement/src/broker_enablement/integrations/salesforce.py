"""Salesforce integration client for the Broker Enablement platform."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class SalesforceClient:
    """Client for Salesforce API integration.

    Handles authentication, CRUD operations, and webhook processing
    for partner data synchronization with Salesforce.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        security_token: str,
        sandbox: bool = False,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Salesforce client.

        Args:
            client_id: Salesforce OAuth client ID.
            client_secret: Salesforce OAuth client secret.
            username: Salesforce username.
            password: Salesforce password.
            security_token: Salesforce security token.
            sandbox: Whether to use Salesforce sandbox.
            timeout: Request timeout in seconds.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.security_token = security_token
        self.sandbox = sandbox
        self.timeout = timeout
        self._access_token: str | None = None
        self._instance_url: str | None = None

        domain = "test" if sandbox else "login"
        self._auth_url = f"https://{domain}.salesforce.com/services/oauth2/token"
        self._base_url: str | None = None

        logger.info("SalesforceClient initialized", sandbox=sandbox)

    async def authenticate(self) -> None:
        """Authenticate with Salesforce using OAuth2 username-password flow.

        Raises:
            RuntimeError: If authentication fails.
        """
        logger.info("Authenticating with Salesforce")

        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": f"{self.password}{self.security_token}",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self._auth_url, data=payload)
                response.raise_for_status()
                data = response.json()

            self._access_token = data["access_token"]
            self._instance_url = data["instance_url"]
            self._base_url = f"{self._instance_url}/services/data/v58.0"

            logger.info("Salesforce authentication successful")

        except httpx.HTTPStatusError as e:
            logger.error(
                "Salesforce authentication failed",
                status_code=e.response.status_code,
                response=e.response.text,
            )
            raise RuntimeError(f"Salesforce authentication failed: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def create_account(self, account_data: dict[str, Any]) -> dict[str, Any]:
        """Create an account in Salesforce.

        Args:
            account_data: Account data to create.

        Returns:
            Created account data from Salesforce.

        Raises:
            RuntimeError: If creation fails.
        """
        if not self._access_token or not self._base_url:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        logger.info("Creating Salesforce account", name=account_data.get("Name"))

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self._base_url}/sobjects/Account",
                    json=account_data,
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to create Salesforce account",
                status_code=e.response.status_code,
                response=e.response.text,
            )
            raise RuntimeError(f"Failed to create Salesforce account: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def update_account(
        self, account_id: str, account_data: dict[str, Any]
    ) -> None:
        """Update an account in Salesforce.

        Args:
            account_id: The Salesforce account ID.
            account_data: Account data to update.

        Raises:
            RuntimeError: If update fails.
        """
        if not self._access_token or not self._base_url:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        logger.info("Updating Salesforce account", account_id=account_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    f"{self._base_url}/sobjects/Account/{account_id}",
                    json=account_data,
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                response.raise_for_status()

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to update Salesforce account",
                account_id=account_id,
                status_code=e.response.status_code,
            )
            raise RuntimeError(f"Failed to update Salesforce account: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def query(self, soql: str) -> list[dict[str, Any]]:
        """Execute a SOQL query against Salesforce.

        Args:
            soql: SOQL query string.

        Returns:
            List of records from the query result.

        Raises:
            RuntimeError: If query fails.
        """
        if not self._access_token or not self._base_url:
            raise RuntimeError("Client not authenticated. Call authenticate() first.")

        logger.info("Executing Salesforce query", query=soql[:100])

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self._base_url}/query",
                    params={"q": soql},
                    headers={"Authorization": f"Bearer {self._access_token}"},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("records", [])

        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to execute Salesforce query",
                status_code=e.response.status_code,
            )
            raise RuntimeError(f"Failed to execute Salesforce query: {e}") from e

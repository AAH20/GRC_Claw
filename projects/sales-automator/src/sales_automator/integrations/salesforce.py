"""Salesforce integration client."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from sales_automator.config import get_settings

logger = structlog.get_logger(__name__)


class SalesforceError(Exception):
    """Salesforce API error."""


class SalesforceClient:
    """Client for Salesforce REST API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client_id = settings.salesforce_client_id
        self.client_secret = settings.salesforce_client_secret
        self.username = settings.salesforce_username
        self.password = settings.salesforce_password
        self.security_token = settings.salesforce_security_token
        self.sandbox = settings.salesforce_sandbox
        self.base_url: str | None = None
        self.access_token: str | None = None
        self.logger = logger.bind(integration="salesforce")

    def _get_auth_url(self) -> str:
        """Get the authentication URL based on environment."""
        if self.sandbox:
            return "https://test.salesforce.com/services/oauth2/token"
        return "https://login.salesforce.com/services/oauth2/token"

    def _get_api_url(self) -> str:
        """Get the API base URL based on environment."""
        if self.sandbox:
            return "https://test.salesforce.com"
        return "https://login.salesforce.com"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def authenticate(self) -> str:
        """Authenticate with Salesforce and get access token.

        Returns:
            Access token.

        Raises:
            SalesforceError: If authentication fails.
        """
        self.logger.info("Authenticating with Salesforce")
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": f"{self.password}{self.security_token}",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._get_auth_url(),
                data=payload,
                timeout=30.0,
            )
            if response.status_code != 200:
                raise SalesforceError(f"Authentication failed: {response.text}")
            data = response.json()
            self.access_token = data["access_token"]
            self.base_url = data["instance_url"]
            self.logger.info("Successfully authenticated with Salesforce")
            return self.access_token

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an authenticated request to Salesforce API.

        Args:
            method: HTTP method.
            path: API path.
            **kwargs: Additional request arguments.

        Returns:
            Response data.

        Raises:
            SalesforceError: If the request fails.
        """
        if not self.access_token:
            await self.authenticate()

        url = f"{self.base_url}/services/data/v59.0{path}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                timeout=30.0,
                **kwargs,
            )
            if response.status_code == 401:
                # Token expired, re-authenticate and retry
                await self.authenticate()
                return await self._request(method, path, **kwargs)
            if response.status_code >= 400:
                raise SalesforceError(f"API error {response.status_code}: {response.text}")
            return response.json() if response.content else {}

    async def get_leads(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get leads from Salesforce.

        Args:
            limit: Maximum number of leads.

        Returns:
            List of leads.
        """
        self.logger.info("Fetching leads", limit=limit)
        result = await self._request(
            "GET",
            f"/query?q=SELECT+Id,Name,Company,Email,Title+FROM+Lead+LIMIT+{limit}",
        )
        return result.get("records", [])

    async def get_opportunities(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get opportunities from Salesforce.

        Args:
            limit: Maximum number of opportunities.

        Returns:
            List of opportunities.
        """
        self.logger.info("Fetching opportunities", limit=limit)
        result = await self._request(
            "GET",
            f"/query?q=SELECT+Id,Name,StageName,Amount,CloseDate+FROM+Opportunity+LIMIT+{limit}",
        )
        return result.get("records", [])

    async def create_lead(self, lead_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new lead in Salesforce.

        Args:
            lead_data: Lead data.

        Returns:
            Created lead.
        """
        self.logger.info("Creating lead", email=lead_data.get("email"))
        return await self._request("POST", "/sobjects/Lead/", json=lead_data)

    async def update_lead(self, lead_id: str, lead_data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing lead.

        Args:
            lead_id: Lead ID.
            lead_data: Updated lead data.

        Returns:
            Updated lead.
        """
        self.logger.info("Updating lead", lead_id=lead_id)
        return await self._request("PATCH", f"/sobjects/Lead/{lead_id}", json=lead_data)

    async def get_accounts(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get accounts from Salesforce.

        Args:
            limit: Maximum number of accounts.

        Returns:
            List of accounts.
        """
        self.logger.info("Fetching accounts", limit=limit)
        result = await self._request(
            "GET",
            f"/query?q=SELECT+Id,Name,Industry+FROM+Account+LIMIT+{limit}",
        )
        return result.get("records", [])

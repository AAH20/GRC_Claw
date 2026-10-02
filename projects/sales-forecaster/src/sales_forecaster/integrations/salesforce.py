"""Salesforce CRM integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
import structlog

from sales_forecaster.core import get_settings
from sales_forecaster.core.exceptions import AuthenticationError, IntegrationError
from sales_forecaster.core.retry import async_retry

logger = structlog.get_logger(__name__)


class SalesforceIntegration:
    """Integration with Salesforce CRM via REST API.

    Handles authentication, opportunity querying, and data normalization.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        username: str | None = None,
        password: str | None = None,
        security_token: str | None = None,
        sandbox: bool = False,
        timeout_seconds: int = 30,
    ) -> None:
        """Initialize Salesforce integration.

        Args:
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret.
            username: Salesforce username.
            password: Salesforce password.
            security_token: Salesforce security token.
            sandbox: Whether to use the sandbox environment.
            timeout_seconds: HTTP request timeout.
        """
        settings = get_settings()
        self.client_id = client_id or settings.salesforce_client_id
        self.client_secret = client_secret or settings.salesforce_client_secret
        self.username = username or settings.salesforce_username
        self.password = password or settings.salesforce_password
        self.security_token = security_token or settings.salesforce_security_token
        self.sandbox = sandbox or settings.salesforce_sandbox
        self.timeout_seconds = timeout_seconds

        self._access_token: str | None = None
        self._instance_url: str | None = None
        self._token_expires_at: datetime | None = None

        self._base_url = (
            "https://test.salesforce.com"
            if self.sandbox
            else "https://login.salesforce.com"
        )

    @property
    def is_configured(self) -> bool:
        """Check if the integration is properly configured."""
        return all([self.client_id, self.client_secret, self.username, self.password])

    @async_retry(
        max_attempts=3,
        base_delay=1.0,
        retryable_exceptions=(ConnectionError, TimeoutError),
    )
    async def authenticate(self) -> str:
        """Authenticate with Salesforce using OAuth2 username-password flow.

        Returns:
            Access token.

        Raises:
            AuthenticationError: If authentication fails.
        """
        if not self.is_configured:
            raise AuthenticationError(
                "Salesforce integration not fully configured",
                source="salesforce",
            )

        auth_url = f"{self._base_url}/services/oauth2/token"

        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": f"{self.password}{self.security_token}",
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(auth_url, data=payload)

            if response.status_code != 200:
                raise AuthenticationError(
                    f"Salesforce authentication failed: {response.text}",
                    source="salesforce",
                    status_code=response.status_code,
                )

            data = response.json()
            self._access_token = data["access_token"]
            self._instance_url = data["instance_url"]
            self._token_expires_at = datetime.now()

            logger.info("Salesforce authentication successful")
            return self._access_token

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid access token."""
        if not self._access_token:
            await self.authenticate()

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests.

        Returns:
            Dictionary of HTTP headers.
        """
        if not self._access_token:
            raise AuthenticationError(
                "Not authenticated. Call authenticate() first.",
                source="salesforce",
            )
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    @async_retry(
        max_attempts=3,
        base_delay=1.0,
        retryable_exceptions=(ConnectionError, TimeoutError),
    )
    async def get_opportunities(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Fetch opportunities from Salesforce.

        Args:
            start_date: Start date for opportunity close date.
            end_date: End date for opportunity close date.
            limit: Maximum number of records to fetch.

        Returns:
            List of raw opportunity records.

        Raises:
            IntegrationError: If the API request fails.
        """
        await self._ensure_authenticated()

        assert self._instance_url is not None

        query = (
            "SELECT Id, Name, Amount, CloseDate, StageName, Probability, "
            "AccountId, OwnerId, CurrencyIsoCode "
            f"FROM Opportunity WHERE CloseDate >= {start_date.strftime('%Y-%m-%d')} "
            f"AND CloseDate <= {end_date.strftime('%Y-%m-%d')} "
            f"LIMIT {limit}"
        )

        url = f"{self._instance_url}/services/data/v59.0/query"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                url, headers=self._get_headers(), params={"q": query}
            )

            if response.status_code != 200:
                raise IntegrationError(
                    f"Salesforce query failed: {response.text}",
                    source="salesforce",
                    status_code=response.status_code,
                )

            data = response.json()
            records = data.get("records", [])
            logger.info("Fetched opportunities from Salesforce", count=len(records))
            return records

    async def get_accounts(self, limit: int = 500) -> list[dict[str, Any]]:
        """Fetch accounts from Salesforce.

        Args:
            limit: Maximum number of records to fetch.

        Returns:
            List of raw account records.

        Raises:
            IntegrationError: If the API request fails.
        """
        await self._ensure_authenticated()

        assert self._instance_url is not None

        query = "SELECT Id, Name, Industry, Region__c, AnnualRevenue FROM Account LIMIT {limit}"
        url = f"{self._instance_url}/services/data/v59.0/query"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                url, headers=self._get_headers(), params={"q": query}
            )

            if response.status_code != 200:
                raise IntegrationError(
                    f"Salesforce query failed: {response.text}",
                    source="salesforce",
                    status_code=response.status_code,
                )

            data = response.json()
            return data.get("records", [])

    async def health_check(self) -> bool:
        """Check if the Salesforce connection is healthy.

        Returns:
            True if the connection is healthy, False otherwise.
        """
        try:
            await self.authenticate()
            return True
        except Exception as exc:
            logger.warning("Salesforce health check failed", error=str(exc))
            return False

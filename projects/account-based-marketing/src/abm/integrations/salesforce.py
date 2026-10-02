"""Salesforce CRM integration for the ABM platform."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class SalesforceError(Exception):
    """Custom exception for Salesforce API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize SalesforceError.

        Args:
            message: Error message.
            status_code: HTTP status code if available.
        """
        super().__init__(message)
        self.status_code = status_code


class SalesforceClient:
    """Client for interacting with the Salesforce REST API.

    Handles authentication, rate limiting, and provides methods for
    querying accounts, contacts, and opportunities.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        security_token: str,
        domain: str = "login",
        timeout: int = 30,
    ) -> None:
        """Initialize the Salesforce client.

        Args:
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret.
            username: Salesforce username.
            password: Salesforce password.
            security_token: Salesforce security token.
            domain: Salesforce domain (login/test).
            timeout: Request timeout in seconds.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password + security_token
        self.domain = domain
        self.timeout = timeout
        self._access_token: str | None = None
        self._instance_url: str | None = None
        logger.info("SalesforceClient initialized", username=username)

    async def authenticate(self) -> None:
        """Authenticate with Salesforce using OAuth2 username-password flow.

        Raises:
            SalesforceError: If authentication fails.
        """
        url = f"https://{self.domain}.salesforce.com/services/oauth2/token"
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, data=payload)
                response.raise_for_status()
                data = response.json()
                self._access_token = data["access_token"]
                self._instance_url = data["instance_url"]
                logger.info("Salesforce authentication successful")
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Salesforce authentication failed",
                    status_code=exc.response.status_code,
                )
                raise SalesforceError(
                    f"Authentication failed: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def query(self, soql: str) -> list[dict[str, Any]]:
        """Execute a SOQL query against Salesforce.

        Args:
            soql: SOQL query string.

        Returns:
            List of records from the query.

        Raises:
            SalesforceError: If the query fails.
        """
        if not self._access_token or not self._instance_url:
            await self.authenticate()

        url = f"{self._instance_url}/services/data/v58.0/query"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        params = {"q": soql}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("records", [])
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 401:
                    # Token expired, re-authenticate and retry
                    await self.authenticate()
                    raise  # Let tenacity retry
                logger.error(
                    "Salesforce query failed",
                    status_code=exc.response.status_code,
                    soql=soql,
                )
                raise SalesforceError(
                    f"Query failed: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

    async def get_accounts(
        self,
        industry: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Fetch accounts from Salesforce.

        Args:
            industry: Optional industry filter.
            limit: Maximum number of records.

        Returns:
            List of account records.
        """
        soql = "SELECT Id, Name, Industry, NumberOfEmployees, Website, BillingState FROM Account"
        if industry:
            soql += f" WHERE Industry = '{industry}'"
        soql += f" LIMIT {limit}"

        return await self.query(soql)

    async def get_contacts(self, account_id: str) -> list[dict[str, Any]]:
        """Fetch contacts for a specific account.

        Args:
            account_id: The Salesforce account ID.

        Returns:
            List of contact records.
        """
        soql = (
            f"SELECT Id, FirstName, LastName, Title, Email, Phone "
            f"FROM Contact WHERE AccountId = '{account_id}'"
        )
        return await self.query(soql)

    async def get_opportunities(
        self,
        account_id: str | None = None,
        stage: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch opportunities from Salesforce.

        Args:
            account_id: Optional account filter.
            stage: Optional stage filter.

        Returns:
            List of opportunity records.
        """
        soql = (
            "SELECT Id, Name, Amount, StageName, CloseDate, AccountId "
            "FROM Opportunity"
        )
        conditions: list[str] = []
        if account_id:
            conditions.append(f"AccountId = '{account_id}'")
        if stage:
            conditions.append(f"StageName = '{stage}'")
        if conditions:
            soql += " WHERE " + " AND ".join(conditions)
        soql += " ORDER BY CloseDate DESC LIMIT 200"

        return await self.query(soql)

    async def create_task(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """Create a task in Salesforce.

        Args:
            task_data: Task fields including Subject, WhoId, WhatId, etc.

        Returns:
            Created task record.

        Raises:
            SalesforceError: If creation fails.
        """
        if not self._access_token or not self._instance_url:
            await self.authenticate()

        url = f"{self._instance_url}/services/data/v58.0/sobjects/Task"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=task_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Failed to create Salesforce task",
                    status_code=exc.response.status_code,
                )
                raise SalesforceError(
                    f"Task creation failed: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

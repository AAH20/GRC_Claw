"""Salesforce Service Cloud integration module."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class SalesforceClient:
    """Client for interacting with the Salesforce Service Cloud API.

    Provides methods for managing cases, contacts, and accounts
    in Salesforce with OAuth authentication and automatic retry.
    """

    def __init__(
        self,
        username: str,
        password: str,
        security_token: str,
        client_id: str,
        client_secret: str,
        domain: str = "login",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Salesforce client.

        Args:
            username: Salesforce username.
            password: Salesforce password.
            security_token: Salesforce security token.
            client_id: OAuth connected app client ID.
            client_secret: OAuth connected app client secret.
            domain: Salesforce domain (login/test).
            timeout: Request timeout in seconds.
        """
        self._username = username
        self._password = password
        self._security_token = security_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._domain = domain
        self._timeout = timeout
        self._access_token: str | None = None
        self._instance_url: str | None = None
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _authenticate(self) -> None:
        """Authenticate with Salesforce using OAuth2 password flow.

        Raises:
            httpx.HTTPStatusError: If authentication fails.
        """
        if self._access_token:
            return

        auth_url = f"https://{self._domain}.salesforce.com/services/oauth2/token"
        payload = {
            "grant_type": "password",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "username": self._username,
            "password": f"{self._password}{self._security_token}",
        }

        response = await self._client.post(auth_url, data=payload)
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        self._instance_url = data["instance_url"]
        logger.info("Salesforce authentication successful")

    def _get_headers(self) -> dict[str, str]:
        """Get authenticated request headers.

        Returns:
            Headers with authorization.

        Raises:
            RuntimeError: If not authenticated.
        """
        if not self._access_token:
            raise RuntimeError("Not authenticated. Call _authenticate() first.")
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def create_case(
        self,
        contact_id: str,
        subject: str,
        description: str,
        status: str = "New",
        priority: str = "Medium",
        origin: str = "Web",
    ) -> dict[str, Any]:
        """Create a new case in Salesforce Service Cloud.

        Args:
            contact_id: Salesforce contact ID.
            subject: Case subject.
            description: Case description.
            status: Case status.
            priority: Case priority.
            origin: Case origin.

        Returns:
            Created case data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        await self._authenticate()
        url = f"{self._instance_url}/services/data/v58.0/sobjects/Case"
        payload = {
            "ContactId": contact_id,
            "Subject": subject,
            "Description": description,
            "Status": status,
            "Priority": priority,
            "Origin": origin,
        }

        response = await self._client.post(url, json=payload, headers=self._get_headers())
        response.raise_for_status()
        logger.info("Salesforce case created", case_id=response.json().get("id"))
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_case(self, case_id: str) -> dict[str, Any]:
        """Retrieve a case from Salesforce.

        Args:
            case_id: The Salesforce case ID.

        Returns:
            Case data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        await self._authenticate()
        url = f"{self._instance_url}/services/data/v58.0/sobjects/Case/{case_id}"

        response = await self._client.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def update_case(
        self,
        case_id: str,
        **fields: Any,
    ) -> dict[str, Any]:
        """Update an existing Salesforce case.

        Args:
            case_id: The Salesforce case ID.
            **fields: Fields to update.

        Returns:
            Updated case data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        await self._authenticate()
        url = f"{self._instance_url}/services/data/v58.0/sobjects/Case/{case_id}"

        response = await self._client.patch(url, json=fields, headers=self._get_headers())
        response.raise_for_status()
        logger.info("Salesforce case updated", case_id=case_id)
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def create_case_comment(
        self,
        case_id: str,
        comment_body: str,
        is_public: bool = False,
    ) -> dict[str, Any]:
        """Add a comment to a Salesforce case.

        Args:
            case_id: The Salesforce case ID.
            comment_body: Comment text.
            is_public: Whether the comment is public.

        Returns:
            Created comment data.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        await self._authenticate()
        url = f"{self._instance_url}/services/data/v58.0/sobjects/CaseComment"
        payload = {
            "ParentId": case_id,
            "CommentBody": comment_body,
            "IsPublished": is_public,
        }

        response = await self._client.post(url, json=payload, headers=self._get_headers())
        response.raise_for_status()
        logger.info("Salesforce case comment created", case_id=case_id)
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def query(self, soql: str) -> dict[str, Any]:
        """Execute a SOQL query against Salesforce.

        Args:
            soql: SOQL query string.

        Returns:
            Query results.

        Raises:
            httpx.HTTPStatusError: If the API request fails.
        """
        await self._authenticate()
        url = f"{self._instance_url}/services/data/v58.0/query"

        response = await self._client.get(
            url,
            params={"q": soql},
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()

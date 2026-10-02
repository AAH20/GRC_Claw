"""Salesforce Marketing Cloud integration adapter."""

from __future__ import annotations

from typing import Any

from compliance.integrations.base import BaseIntegrationClient, IntegrationError


class SalesforceClient(BaseIntegrationClient):
    """Client for retrieving marketing content from Salesforce.

    Supports both production and sandbox orgs and lazily acquires an OAuth
    bearer token using the configured connected-app credentials.
    """

    name = "salesforce"

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        security_token: str = "",
        sandbox: bool = False,
        api_version: str = "v58.0",
        timeout: float = 30.0,
    ) -> None:
        """Initialise the Salesforce client.

        Args:
            client_id: Connected app consumer key.
            client_secret: Connected app consumer secret.
            username: Salesforce username.
            password: Salesforce password.
            security_token: Optional security token appended to the password.
            sandbox: Whether to target the sandbox login host.
            api_version: REST API version.
            timeout: Per-request timeout in seconds.
        """
        host = "test.salesforce.com" if sandbox else "login.salesforce.com"
        super().__init__(f"https://{host}", timeout=timeout)
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.security_token = security_token
        self.api_version = api_version
        self._instance_url: str | None = None
        self._access_token: str | None = None

    async def authenticate(self) -> str:
        """Acquire an OAuth access token.

        Returns:
            The bearer access token.

        Raises:
            IntegrationError: If the token response omits required fields.
        """
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": f"{self.password}{self.security_token}",
        }
        data = await self.request("POST", "/services/oauth2/token", json=payload)
        token = data.get("access_token")
        instance_url = data.get("instance_url")
        if not token or not instance_url:
            raise IntegrationError("salesforce authentication returned an invalid response")
        self._access_token = token
        self._instance_url = instance_url
        self.headers["Authorization"] = f"Bearer {token}"
        return token

    async def fetch_campaigns(self, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch marketing campaigns.

        Args:
            limit: Maximum number of campaigns to return.

        Returns:
            A list of normalised campaign records.
        """
        if self._access_token is None:
            await self.authenticate()
        data = await self.request(
            "GET",
            f"/services/data/{self.api_version}/query",
            params={"q": f"SELECT Id, Name, Description FROM Campaign LIMIT {limit}"},
        )
        records = data.get("records", [])
        return [
            {
                "id": record.get("Id"),
                "source": self.name,
                "content": record.get("Description", ""),
                "channel": "email",
                "metadata": {"name": record.get("Name")},
            }
            for record in records
        ]

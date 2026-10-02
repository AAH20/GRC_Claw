"""Salesforce integration module."""

from __future__ import annotations

import httpx
import structlog
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class SalesforceConfig(BaseModel):
    """Salesforce API configuration."""

    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    username: str = Field(..., description="Salesforce username")
    password: str = Field(..., description="Salesforce password")
    security_token: str = Field(default="", description="Security token")
    domain: str = Field(default="login", description="Salesforce domain")
    api_version: str = Field(default="v58.0", description="API version")


class SalesforceContact(BaseModel):
    """Salesforce contact record."""

    id: str | None = Field(default=None, description="Salesforce record ID")
    email: str = Field(..., description="Contact email")
    first_name: str = Field(default="", description="First name")
    last_name: str = Field(..., description="Last name")
    company: str = Field(default="", description="Company name")
    title: str = Field(default="", description="Job title")
    lead_source: str | None = Field(default=None, description="Lead source")
    custom_fields: dict[str, str] = Field(default_factory=dict, description="Custom fields")


class SalesforceOpportunity(BaseModel):
    """Salesforce opportunity record."""

    id: str | None = Field(default=None, description="Opportunity ID")
    name: str = Field(..., description="Opportunity name")
    stage: str = Field(..., description="Sales stage")
    amount: float = Field(default=0.0, description="Opportunity amount")
    close_date: str = Field(..., description="Expected close date (YYYY-MM-DD)")
    account_id: str = Field(default="", description="Related account ID")
    contact_id: str = Field(default="", description="Related contact ID")


class SalesforceIntegration:
    """Integration with Salesforce CRM.

    Provides methods to sync contacts, leads, and opportunities
    between the marketing platform and Salesforce.
    """

    def __init__(self, config: SalesforceConfig) -> None:
        """Initialize Salesforce integration.

        Args:
            config: Salesforce API configuration.
        """
        self.config = config
        self._access_token: str | None = None
        self._instance_url: str | None = None
        logger.info("salesforce_integration_initialized")

    async def authenticate(self) -> str:
        """Authenticate with Salesforce using OAuth2 username-password flow.

        Returns:
            Access token.

        Raises:
            httpx.HTTPStatusError: If authentication fails.
        """
        url = f"https://{self.config.domain}.salesforce.com/services/oauth2/token"

        payload = {
            "grant_type": "password",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "username": self.config.username,
            "password": f"{self.config.password}{self.config.security_token}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()

        self._access_token = data["access_token"]
        self._instance_url = data["instance_url"]

        logger.info("salesforce_authenticated")
        return self._access_token

    @retry(
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def upsert_contact(self, contact: SalesforceContact) -> dict:
        """Create or update a contact in Salesforce.

        Args:
            contact: Contact data to upsert.

        Returns:
            Salesforce API response.

        Raises:
            RuntimeError: If not authenticated.
            httpx.HTTPStatusError: If API call fails.
        """
        self._ensure_authenticated()

        url = (
            f"{self._instance_url}/services/data/{self.config.api_version}"
            f"/sobjects/Contact/"
        )

        payload = {
            "Email": contact.email,
            "FirstName": contact.first_name,
            "LastName": contact.last_name,
            "Company": contact.company,
            "Title": contact.title,
        }
        if contact.lead_source:
            payload["LeadSource"] = contact.lead_source

        headers = {"Authorization": f"Bearer {self._access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=headers, timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        logger.info("salesforce_contact_upserted", email=contact.email)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def create_opportunity(self, opportunity: SalesforceOpportunity) -> dict:
        """Create an opportunity in Salesforce.

        Args:
            opportunity: Opportunity data.

        Returns:
            Salesforce API response.

        Raises:
            RuntimeError: If not authenticated.
            httpx.HTTPStatusError: If API call fails.
        """
        self._ensure_authenticated()

        url = (
            f"{self._instance_url}/services/data/{self.config.api_version}"
            f"/sobjects/Opportunity/"
        )

        payload = {
            "Name": opportunity.name,
            "StageName": opportunity.stage,
            "Amount": opportunity.amount,
            "CloseDate": opportunity.close_date,
        }
        if opportunity.account_id:
            payload["AccountId"] = opportunity.account_id

        headers = {"Authorization": f"Bearer {self._access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=headers, timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        logger.info("salesforce_opportunity_created", name=opportunity.name)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def query(self, soql: str) -> list[dict]:
        """Execute a SOQL query against Salesforce.

        Args:
            soql: SOQL query string.

        Returns:
            List of records matching the query.

        Raises:
            RuntimeError: If not authenticated.
            httpx.HTTPStatusError: If query fails.
        """
        self._ensure_authenticated()

        url = (
            f"{self._instance_url}/services/data/{self.config.api_version}"
            f"/query/"
        )

        headers = {"Authorization": f"Bearer {self._access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, params={"q": soql}, headers=headers, timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        return result.get("records", [])

    def _ensure_authenticated(self) -> None:
        """Ensure the integration is authenticated.

        Raises:
            RuntimeError: If not authenticated.
        """
        if not self._access_token or not self._instance_url:
            raise RuntimeError(
                "Salesforce integration not authenticated. Call authenticate() first."
            )

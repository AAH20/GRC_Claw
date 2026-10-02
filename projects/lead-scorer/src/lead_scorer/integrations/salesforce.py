"""Salesforce CRM integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class SalesforceConfig(BaseModel):
    """Salesforce connection configuration."""

    client_id: str = ""
    client_secret: str = ""
    username: str = ""
    password: str = ""
    security_token: str = ""
    domain: str = "login"
    api_version: str = "v58.0"
    timeout_seconds: int = 30
    retry_attempts: int = 3


class SalesforceAuth(BaseModel):
    """Salesforce authentication token."""

    access_token: str
    instance_url: str
    issued_at: str
    token_type: str = "Bearer"


class SalesforceLead(BaseModel):
    """Salesforce lead record."""

    id: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    company: str = ""
    title: str = ""
    phone: str = ""
    website: str = ""
    source: str = ""
    status: str = ""
    rating: str = ""
    industry: str = ""
    annual_revenue: float | None = None
    number_of_employees: int | None = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class SalesforceIntegration:
    """Integration with Salesforce CRM.

    Provides methods to authenticate, query, and sync lead data
    with Salesforce using the REST API.
    """

    def __init__(self, config: SalesforceConfig) -> None:
        """Initialize Salesforce integration.

        Args:
            config: Salesforce connection configuration.
        """
        self.config = config
        self._auth: SalesforceAuth | None = None
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout_seconds,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def authenticate(self) -> SalesforceAuth:
        """Authenticate with Salesforce using OAuth2 username-password flow.

        Returns:
            SalesforceAuth with access token and instance URL.

        Raises:
            httpx.HTTPStatusError: If authentication fails.
        """
        client = await self._get_client()

        auth_url = f"https://{self.config.domain}.salesforce.com/services/oauth2/token"

        payload = {
            "grant_type": "password",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "username": self.config.username,
            "password": f"{self.config.password}{self.config.security_token}",
        }

        logger.info("authenticating_with_salesforce", username=self.config.username)

        response = await client.post(auth_url, data=payload)
        response.raise_for_status()

        data = response.json()
        self._auth = SalesforceAuth(
            access_token=data["access_token"],
            instance_url=data["instance_url"],
            issued_at=data["issued_at"],
        )

        logger.info("salesforce_auth_success", instance=self._auth.instance_url)
        return self._auth

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token."""
        if self._auth is None:
            await self.authenticate()

    async def get_lead(self, lead_id: str) -> SalesforceLead:
        """Get a lead by ID from Salesforce.

        Args:
            lead_id: Salesforce lead ID.

        Returns:
            SalesforceLead with lead data.

        Raises:
            httpx.HTTPStatusError: If request fails.
        """
        await self._ensure_authenticated()
        client = await self._get_client()

        url = (
            f"{self._auth.instance_url}/services/data/{self.config.api_version}"
            f"/sobjects/Lead/{lead_id}"
        )

        response = await client.get(
            url, headers={"Authorization": f"Bearer {self._auth.access_token}"}
        )
        response.raise_for_status()

        data = response.json()
        return SalesforceLead(
            id=data.get("Id", ""),
            first_name=data.get("FirstName", ""),
            last_name=data.get("LastName", ""),
            email=data.get("Email", ""),
            company=data.get("Company", ""),
            title=data.get("Title", ""),
            phone=data.get("Phone", ""),
            website=data.get("Website", ""),
            source=data.get("LeadSource", ""),
            status=data.get("Status", ""),
            rating=data.get("Rating", ""),
            industry=data.get("Industry", ""),
            annual_revenue=data.get("AnnualRevenue"),
            number_of_employees=data.get("NumberOfEmployees"),
        )

    async def upsert_lead(self, lead: SalesforceLead) -> str:
        """Create or update a lead in Salesforce.

        Args:
            lead: Lead data to upsert.

        Returns:
            Salesforce lead ID.

        Raises:
            httpx.HTTPStatusError: If request fails.
        """
        await self._ensure_authenticated()
        client = await self._get_client()

        url = (
            f"{self._auth.instance_url}/services/data/{self.config.api_version}"
            f"/sobjects/Lead/Email/{lead.email}"
        )

        payload = {
            "FirstName": lead.first_name,
            "LastName": lead.last_name,
            "Company": lead.company,
            "Title": lead.title,
            "Phone": lead.phone,
            "Website": lead.website,
            "LeadSource": lead.source,
            "Status": lead.status,
            "Rating": lead.rating,
            "Industry": lead.industry,
        }

        if lead.annual_revenue is not None:
            payload["AnnualRevenue"] = lead.annual_revenue
        if lead.number_of_employees is not None:
            payload["NumberOfEmployees"] = lead.number_of_employees

        response = await client.patch(
            url,
            headers={"Authorization": f"Bearer {self._auth.access_token}"},
            json=payload,
        )
        response.raise_for_status()

        if response.status_code == 201:
            result = response.json()
            sf_id = result.get("id", "")
            logger.info("salesforce_lead_created", lead_id=sf_id, email=lead.email)
            return sf_id

        logger.info("salesforce_lead_updated", email=lead.email)
        return lead.id

    async def query_leads(self, soql: str) -> list[SalesforceLead]:
        """Query leads using SOQL.

        Args:
            soql: SOQL query string.

        Returns:
            List of SalesforceLead records.

        Raises:
            httpx.HTTPStatusError: If request fails.
        """
        await self._ensure_authenticated()
        client = await self._get_client()

        url = (
            f"{self._auth.instance_url}/services/data/{self.config.api_version}"
            f"/query"
        )

        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {self._auth.access_token}"},
            params={"q": soql},
        )
        response.raise_for_status()

        data = response.json()
        records = data.get("records", [])

        leads: list[SalesforceLead] = []
        for record in records:
            leads.append(
                SalesforceLead(
                    id=record.get("Id", ""),
                    first_name=record.get("FirstName", ""),
                    last_name=record.get("LastName", ""),
                    email=record.get("Email", ""),
                    company=record.get("Company", ""),
                    title=record.get("Title", ""),
                    phone=record.get("Phone", ""),
                    website=record.get("Website", ""),
                    source=record.get("LeadSource", ""),
                    status=record.get("Status", ""),
                    rating=record.get("Rating", ""),
                    industry=record.get("Industry", ""),
                    annual_revenue=record.get("AnnualRevenue"),
                    number_of_employees=record.get("NumberOfEmployees"),
                )
            )

        logger.info("salesforce_query_complete", count=len(leads))
        return leads

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

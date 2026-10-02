"""HubSpot integration module."""

from __future__ import annotations

import httpx
import structlog
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class HubSpotConfig(BaseModel):
    """HubSpot API configuration."""

    api_key: str = Field(..., description="HubSpot API key")
    portal_id: str = Field(default="", description="HubSpot portal ID")
    api_version: str = Field(default="v3", description="API version")


class HubSpotContact(BaseModel):
    """HubSpot contact record."""

    email: str = Field(..., description="Contact email")
    firstname: str = Field(default="", description="First name")
    lastname: str = Field(default="", description="Last name")
    company: str = Field(default="", description="Company name")
    jobtitle: str = Field(default="", description="Job title")
    lifecycle_stage: str | None = Field(default=None, description="Lifecycle stage")
    custom_properties: dict[str, str] = Field(default_factory=dict, description="Custom properties")


class HubSpotDeal(BaseModel):
    """HubSpot deal record."""

    dealname: str = Field(..., description="Deal name")
    dealstage: str = Field(..., description="Deal stage")
    amount: float = Field(default=0.0, description="Deal amount")
    closedate: str | None = Field(default=None, description="Close date")
    pipeline: str = Field(default="default", description="Pipeline name")
    hubspot_owner_id: str | None = Field(default=None, description="Owner ID")


class HubSpotIntegration:
    """Integration with HubSpot CRM.

    Provides methods to sync contacts, deals, and marketing events
    between the marketing platform and HubSpot.
    """

    BASE_URL = "https://api.hubapi.com"

    def __init__(self, config: HubSpotConfig) -> None:
        """Initialize HubSpot integration.

        Args:
            config: HubSpot API configuration.
        """
        self.config = config
        logger.info("hubspot_integration_initialized")

    def _headers(self) -> dict[str, str]:
        """Build request headers with API key.

        Returns:
            Headers dictionary.
        """
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def upsert_contact(self, contact: HubSpotContact) -> dict:
        """Create or update a contact in HubSpot.

        Args:
            contact: Contact data.

        Returns:
            HubSpot API response.

        Raises:
            httpx.HTTPStatusError: If API call fails.
        """
        url = f"{self.BASE_URL}/crm/v3/objects/cont"

        properties = {
            "email": contact.email,
            "firstname": contact.firstname,
            "lastname": contact.lastname,
            "company": contact.company,
            "jobtitle": contact.jobtitle,
        }
        if contact.lifecycle_stage:
            properties["lifecyclestage"] = contact.lifecycle_stage
        properties.update(contact.custom_properties)

        payload = {"properties": properties}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=self._headers(), timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        logger.info("hubspot_contact_upserted", email=contact.email)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def create_deal(self, deal: HubSpotDeal) -> dict:
        """Create a deal in HubSpot.

        Args:
            deal: Deal data.

        Returns:
            HubSpot API response.

        Raises:
            httpx.HTTPStatusError: If API call fails.
        """
        url = f"{self.BASE_URL}/crm/v3/objects/deals"

        properties = {
            "dealname": deal.dealname,
            "dealstage": deal.dealstage,
            "amount": str(deal.amount),
            "pipeline": deal.pipeline,
        }
        if deal.closedate:
            properties["closedate"] = deal.closedate
        if deal.hubspot_owner_id:
            properties["hubspot_owner_id"] = deal.hubspot_owner_id

        payload = {"properties": properties}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=self._headers(), timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        logger.info("hubspot_deal_created", dealname=deal.dealname)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def track_event(
        self, email: str, event_name: str, properties: dict | None = None
    ) -> dict:
        """Track a marketing event for a contact.

        Args:
            email: Contact email.
            event_name: Event name to track.
            properties: Additional event properties.

        Returns:
            HubSpot API response.

        Raises:
            httpx.HTTPStatusError: If API call fails.
        """
        url = f"{self.BASE_URL}/events/v3/send"

        payload = {
            "email": email,
            "eventName": event_name,
        }
        if properties:
            payload["properties"] = properties

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=self._headers(), timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        logger.info("hubspot_event_tracked", event_name=event_name, email=email)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_contact_by_email(self, email: str) -> dict | None:
        """Retrieve a contact by email address.

        Args:
            email: Contact email to look up.

        Returns:
            Contact data if found, None otherwise.

        Raises:
            httpx.HTTPStatusError: If API call fails.
        """
        url = f"{self.BASE_URL}/crm/v3/objects/cont/search"

        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email,
                        }
                    ]
                }
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=self._headers(), timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        results = result.get("results", [])
        return results[0] if results else None

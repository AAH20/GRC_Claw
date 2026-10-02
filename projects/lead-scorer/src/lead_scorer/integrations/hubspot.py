"""HubSpot CRM integration."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class HubSpotConfig(BaseModel):
    """HubSpot connection configuration."""

    api_key: str = ""
    portal_id: str = ""
    api_version: str = "v3"
    timeout_seconds: int = 30
    retry_attempts: int = 3


class HubSpotContact(BaseModel):
    """HubSpot contact record."""

    id: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    company: str = ""
    website: str = ""
    job_title: str = ""
    lifecycle_stage: str = ""
    lead_status: str = ""
    custom_properties: dict[str, Any] = Field(default_factory=dict)


class HubSpotEngagement(BaseModel):
    """HubSpot engagement record."""

    id: str = ""
    type: str = ""
    active: bool = True
    created_at: str = ""
    last_updated: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class HubSpotIntegration:
    """Integration with HubSpot CRM.

    Provides methods to query and sync lead data with HubSpot
    using the REST API.
    """

    def __init__(self, config: HubSpotConfig) -> None:
        """Initialize HubSpot integration.

        Args:
            config: HubSpot connection configuration.
        """
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout_seconds,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config.api_key}",
                },
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_contact(self, contact_id: str) -> HubSpotContact:
        """Get a contact by ID from HubSpot.

        Args:
            contact_id: HubSpot contact ID.

        Returns:
            HubSpotContact with contact data.

        Raises:
            httpx.HTTPStatusError: If request fails.
        """
        client = await self._get_client()
        url = f"https://api.hubapi.com/crm/v3/objects/cont/{contact_id}"

        logger.info("fetching_hubspot_contact", contact_id=contact_id)

        response = await client.get(url)
        response.raise_for_status()

        data = response.json()
        properties = data.get("properties", {})

        return HubSpotContact(
            id=data.get("id", ""),
            email=properties.get("email", ""),
            first_name=properties.get("firstname", ""),
            last_name=properties.get("lastname", ""),
            phone=properties.get("phone", ""),
            company=properties.get("company", ""),
            website=properties.get("website", ""),
            job_title=properties.get("jobtitle", ""),
            lifecycle_stage=properties.get("lifecyclestage", ""),
            lead_status=properties.get("hs_lead_status", ""),
            custom_properties={
                k: v for k, v in properties.items()
                if k not in {
                    "email", "firstname", "lastname", "phone",
                    "company", "website", "jobtitle", "lifecyclestage",
                    "hs_lead_status",
                }
            },
        )

    async def get_contact_by_email(self, email: str) -> HubSpotContact | None:
        """Get a contact by email address.

        Args:
            email: Contact email address.

        Returns:
            HubSpotContact if found, None otherwise.

        Raises:
            httpx.HTTPStatusError: If request fails.
        """
        client = await self._get_client()
        url = "https://api.hubapi.com/crm/v3/objects/cont/search"

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
            ],
            "limit": 1,
        }

        response = await client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            return None

        properties = results[0].get("properties", {})
        return HubSpotContact(
            id=results[0].get("id", ""),
            email=properties.get("email", ""),
            first_name=properties.get("firstname", ""),
            last_name=properties.get("lastname", ""),
            phone=properties.get("phone", ""),
            company=properties.get("company", ""),
            website=properties.get("website", ""),
            job_title=properties.get("jobtitle", ""),
            lifecycle_stage=properties.get("lifecyclestage", ""),
            lead_status=properties.get("hs_lead_status", ""),
        )

    async def upsert_contact(self, contact: HubSpotContact) -> str:
        """Create or update a contact in HubSpot.

        Args:
            contact: Contact data to upsert.

        Returns:
            HubSpot contact ID.

        Raises:
            httpx.HTTPStatusError: If request fails.
        """
        client = await self._get_client()
        url = "https://api.hubapi.com/crm/v3/objects/cont"

        properties: dict[str, Any] = {
            "email": contact.email,
            "firstname": contact.first_name,
            "lastname": contact.last_name,
            "phone": contact.phone,
            "company": contact.company,
            "website": contact.website,
            "jobtitle": contact.job_title,
        }

        if contact.lifecycle_stage:
            properties["lifecyclestage"] = contact.lifecycle_stage
        if contact.lead_status:
            properties["hs_lead_status"] = contact.lead_status

        properties.update(contact.custom_properties)

        # Try to find existing contact
        existing = await self.get_contact_by_email(contact.email)

        if existing:
            # Update existing
            update_url = f"{url}/{existing.id}"
            response = await client.patch(update_url, json={"properties": properties})
            response.raise_for_status()
            logger.info("hubspot_contact_updated", contact_id=existing.id)
            return existing.id
        else:
            # Create new
            response = await client.post(url, json={"properties": properties})
            response.raise_for_status()
            data = response.json()
            contact_id = data.get("id", "")
            logger.info("hubspot_contact_created", contact_id=contact_id)
            return contact_id

    async def get_engagements(self, contact_id: str) -> list[HubSpotEngagement]:
        """Get engagements for a contact.

        Args:
            contact_id: HubSpot contact ID.

        Returns:
            List of HubSpotEngagement records.

        Raises:
            httpx.HTTPStatusError: If request fails.
        """
        client = await self._get_client()
        url = (
            f"https://api.hubapi.com/crm/v3/objects/cont"
            f"/{contact_id}/associations/engagements"
        )

        response = await client.get(url)
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        engagements: list[HubSpotEngagement] = []
        for record in results:
            engagements.append(
                HubSpotEngagement(
                    id=record.get("id", ""),
                    type=record.get("type", ""),
                    active=record.get("active", True),
                    created_at=record.get("createdAt", ""),
                    last_updated=record.get("lastUpdated", ""),
                )
            )

        logger.info(
            "hubspot_engagements_fetched",
            contact_id=contact_id,
            count=len(engagements),
        )
        return engagements

    async def create_engagement(
        self,
        contact_id: str,
        engagement_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create an engagement for a contact.

        Args:
            contact_id: HubSpot contact ID.
            engagement_type: Type of engagement (EMAIL, CALL, MEETING, etc.).
            metadata: Optional engagement metadata.

        Returns:
            HubSpot engagement ID.

        Raises:
            httpx.HTTPStatusError: If request fails.
        """
        client = await self._get_client()
        url = "https://api.hubapi.com/crm/v3/objects/engagements"

        payload: dict[str, Any] = {
            "properties": {
                "type": engagement_type,
                "active": True,
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 1,
                        }
                    ],
                }
            ],
        }

        if metadata:
            payload["properties"].update(metadata)

        response = await client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        engagement_id = data.get("id", "")
        logger.info(
            "hubspot_engagement_created",
            engagement_id=engagement_id,
            contact_id=contact_id,
        )
        return engagement_id

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

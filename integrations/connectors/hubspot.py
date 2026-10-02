"""HubSpot API connector."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import APIResponse, BaseConnector, ConnectorConfig, ConnectorError
from .oauth import OAuth2Handler

logger = logging.getLogger(__name__)


class HubSpotConnector(BaseConnector):
    """HubSpot CRM API connector.

    Supports contacts, companies, deals, tickets, and engagements.
    Uses OAuth 2.0 or API key for authentication.
    """

    DEFAULT_BASE_URL = "https://api.hubapi.com"
    API_VERSION = "v3"

    def __init__(
        self,
        access_token: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[ConnectorConfig] = None,
    ) -> None:
        if config is None:
            config = ConnectorConfig(
                base_url=self.DEFAULT_BASE_URL,
                access_token=access_token,
                api_key=api_key,
            )
        super().__init__(config)
        self._access_token = access_token
        self._api_key = api_key
        self._oauth_handler: Optional[OAuth2Handler] = None

    async def authenticate(self) -> None:
        """Authenticate with HubSpot."""
        self._state = self._state.AUTHENTICATING
        try:
            if self._access_token:
                self._auth_token = self._access_token
            elif self._api_key:
                self._auth_token = self._api_key
            else:
                raise ConnectorError("Either access_token or api_key is required")

            # Validate credentials
            response = await self.get("/integrations/v1/me", auth=False)
            if not response.is_success:
                raise ConnectorError("Invalid HubSpot credentials")
            self._state = self._state.AUTHENTICATED
        except Exception as e:
            self._state = self._state.ERROR
            raise ConnectorError(f"HubSpot authentication failed: {e}") from e

    async def refresh_auth(self) -> None:
        """Refresh the HubSpot OAuth token."""
        if self._oauth_handler:
            token = await self._oauth_handler.refresh(session=self._session)
            self._auth_token = token.access_token

    async def health_check(self) -> bool:
        """Check if HubSpot API is reachable."""
        try:
            response = await self.get("/integrations/v1/me", auth=False)
            return response.is_success
        except Exception:
            return False

    def _auth_headers(self) -> Dict[str, str]:
        """Get auth headers based on authentication method."""
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}

    def _query_params(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add API key to query params if using API key auth."""
        result = dict(params or {})
        if self._api_key and not self._access_token:
            result["hapikey"] = self._api_key
        return result

    # ─── Contacts ───────────────────────────────────────────────────────

    async def get_contacts(
        self,
        *,
        properties: Optional[List[str]] = None,
        limit: int = 100,
        after: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get contacts.

        Args:
            properties: Contact properties to retrieve.
            limit: Maximum number of contacts.
            after: Pagination cursor.

        Returns:
            Paginated response with 'results' and 'paging'.
        """
        params: Dict[str, Any] = {"count": min(limit, 100)}
        if properties:
            params["property"] = properties
        if after:
            params["after"] = after

        response = await self.get(
            f"/crm/{self.API_VERSION}/objects/contacts",
            params=self._query_params(params),
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_contact(self, contact_id: str, *, properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get a single contact by ID or email.

        Args:
            contact_id: Contact ID or email address.
            properties: Contact properties to retrieve.

        Returns:
            Contact record.
        """
        params = self._query_params({"properties": properties} if properties else None)
        response = await self.get(
            f"/crm/{self.API_VERSION}/objects/contacts/{contact_id}",
            params=params,
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_contact(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact.

        Args:
            properties: Contact properties (email, firstname, lastname, etc.).

        Returns:
            Created contact record.
        """
        response = await self.post(
            f"/crm/{self.API_VERSION}/objects/contacts",
            data={"properties": properties},
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def update_contact(self, contact_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing contact.

        Args:
            contact_id: Contact ID or email.
            properties: Properties to update.

        Returns:
            Updated contact record.
        """
        response = await self.patch(
            f"/crm/{self.API_VERSION}/objects/contacts/{contact_id}",
            data={"properties": properties},
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact.

        Args:
            contact_id: Contact ID.

        Returns:
            True if deletion was successful.
        """
        response = await self.delete(f"/crm/{self.API_VERSION}/objects/contacts/{contact_id}")
        return response.is_success

    async def search_contacts(
        self,
        query: str,
        *,
        properties: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Search contacts by query string.

        Args:
            query: Search query.
            properties: Properties to retrieve.
            limit: Maximum number of results.

        Returns:
            List of matching contacts.
        """
        data: Dict[str, Any] = {
            "query": query,
            "limit": limit,
        }
        if properties:
            data["properties"] = properties

        response = await self.post(
            f"/crm/{self.API_VERSION}/objects/contacts/search",
            data=data,
        )
        if isinstance(response.data, dict):
            return response.data.get("results", [])
        return []

    # ─── Companies ──────────────────────────────────────────────────────

    async def get_companies(
        self,
        *,
        properties: Optional[List[str]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get companies.

        Args:
            properties: Company properties to retrieve.
            limit: Maximum number of companies.

        Returns:
            Paginated response with 'results' and 'paging'.
        """
        params: Dict[str, Any] = {"count": min(limit, 100)}
        if properties:
            params["property"] = properties

        response = await self.get(
            f"/crm/{self.API_VERSION}/objects/companies",
            params=self._query_params(params),
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_company(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new company.

        Args:
            properties: Company properties (name, domain, industry, etc.).

        Returns:
            Created company record.
        """
        response = await self.post(
            f"/crm/{self.API_VERSION}/objects/companies",
            data={"properties": properties},
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Deals ──────────────────────────────────────────────────────────

    async def get_deals(
        self,
        *,
        properties: Optional[List[str]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get deals.

        Args:
            properties: Deal properties to retrieve.
            limit: Maximum number of deals.

        Returns:
            Paginated response with 'results' and 'paging'.
        """
        params: Dict[str, Any] = {"count": min(limit, 100)}
        if properties:
            params["property"] = properties

        response = await self.get(
            f"/crm/{self.API_VERSION}/objects/deals",
            params=self._query_params(params),
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_deal(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new deal.

        Args:
            properties: Deal properties (dealname, amount, pipeline, dealstage, etc.).

        Returns:
            Created deal record.
        """
        response = await self.post(
            f"/crm/{self.API_VERSION}/objects/deals",
            data={"properties": properties},
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Tickets ────────────────────────────────────────────────────────

    async def get_tickets(
        self,
        *,
        properties: Optional[List[str]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get tickets.

        Args:
            properties: Ticket properties to retrieve.
            limit: Maximum number of tickets.

        Returns:
            Paginated response with 'results' and 'paging'.
        """
        params: Dict[str, Any] = {"count": min(limit, 100)}
        if properties:
            params["property"] = properties

        response = await self.get(
            f"/crm/{self.API_VERSION}/objects/tickets",
            params=self._query_params(params),
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Engagements ────────────────────────────────────────────────────

    async def create_engagement(
        self,
        engagement_type: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        associations: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create an engagement (note, email, call, meeting, task).

        Args:
            engagement_type: Type of engagement (NOTE, EMAIL, CALL, MEETING, TASK).
            metadata: Engagement metadata.
            associations: Associations to contacts, companies, or deals.

        Returns:
            Created engagement record.
        """
        data: Dict[str, Any] = {
            "engagement": {"type": engagement_type},
        }
        if metadata:
            data["metadata"] = metadata
        if associations:
            data["associations"] = associations

        response = await self.post(
            f"/crm/{self.API_VERSION}/objects/engagements",
            data=data,
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Owners ─────────────────────────────────────────────────────────

    async def get_owners(self) -> List[Dict[str, Any]]:
        """Get all owners.

        Returns:
            List of owner records.
        """
        response = await self.get(f"/crm/{self.API_VERSION}/owners")
        if isinstance(response.data, dict):
            return response.data.get("results", [])
        return []

"""GoHighLevel API connector."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import APIResponse, BaseConnector, ConnectorConfig, ConnectorError
from .oauth import OAuth2Handler

logger = logging.getLogger(__name__)


class GoHighLevelConnector(BaseConnector):
    """GoHighLevel (HighLevel) API connector.

    Supports contacts, opportunities, calendars, campaigns, and workflows.
    Uses OAuth 2.0 for authentication.
    """

    DEFAULT_BASE_URL = "https://rest.gohighlevel.com/v1"
    OAUTH_BASE_URL = "https://marketplace.gohighlevel.com/oauth"

    def __init__(
        self,
        access_token: str,
        location_id: Optional[str] = None,
        company_id: Optional[str] = None,
        config: Optional[ConnectorConfig] = None,
    ) -> None:
        if config is None:
            config = ConnectorConfig(
                base_url=self.DEFAULT_BASE_URL,
                access_token=access_token,
            )
        super().__init__(config)
        self._access_token = access_token
        self.location_id = location_id
        self.company_id = company_id

    async def authenticate(self) -> None:
        """Authenticate with GoHighLevel using the provided access token."""
        self._state = self._state.AUTHENTICATING
        try:
            response = await self.get("/locations/", auth=False)
            if not response.is_success:
                raise ConnectorError("Invalid GoHighLevel access token")
            self._auth_token = self._access_token
            self._state = self._state.AUTHENTICATED
        except Exception as e:
            self._state = self._state.ERROR
            raise ConnectorError(f"GoHighLevel authentication failed: {e}") from e

    async def refresh_auth(self) -> None:
        """Refresh the GoHighLevel OAuth token."""
        logger.info("GoHighLevel token refresh requires re-authorization")

    async def health_check(self) -> bool:
        """Check if GoHighLevel API is reachable."""
        try:
            response = await self.get("/locations/", auth=False)
            return response.is_success
        except Exception:
            return False

    def _auth_headers(self) -> Dict[str, str]:
        """Get auth headers."""
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}

    def _location_params(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add location ID to params."""
        result = dict(params or {})
        if self.location_id:
            result["locationId"] = self.location_id
        return result

    # ─── Locations ──────────────────────────────────────────────────────

    async def get_locations(self) -> List[Dict[str, Any]]:
        """Get all locations.

        Returns:
            List of location dictionaries.
        """
        response = await self.get("/locations/", auth=False)
        if isinstance(response.data, dict):
            return response.data.get("locations", [])
        return []

    async def get_location(self, location_id: str) -> Dict[str, Any]:
        """Get a specific location.

        Args:
            location_id: The location ID.

        Returns:
            Location details.
        """
        response = await self.get(f"/locations/{location_id}", auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Contacts ───────────────────────────────────────────────────────

    async def get_contacts(
        self,
        *,
        location_id: Optional[str] = None,
        limit: int = 100,
        page: int = 1,
    ) -> Dict[str, Any]:
        """Get contacts.

        Args:
            location_id: Location ID (uses default if not specified).
            limit: Maximum number of contacts.
            page: Page number.

        Returns:
            Paginated response with 'contacts' and 'count'.
        """
        loc_id = location_id or self.location_id
        params = self._location_params({
            "limit": limit,
            "page": page,
        })
        response = await self.get("/contacts/", params=params, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get a single contact.

        Args:
            contact_id: The contact ID.

        Returns:
            Contact details.
        """
        response = await self.get(f"/contacts/{contact_id}", auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_contact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contact.

        Args:
            data: Contact data (firstName, lastName, email, phone, etc.).

        Returns:
            Created contact record.
        """
        response = await self.post("/contacts/", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def update_contact(self, contact_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing contact.

        Args:
            contact_id: The contact ID.
            data: Fields to update.

        Returns:
            Updated contact record.
        """
        response = await self.put(f"/contacts/{contact_id}", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact.

        Args:
            contact_id: The contact ID.

        Returns:
            True if deletion was successful.
        """
        response = await self.delete(f"/contacts/{contact_id}", auth=False)
        return response.is_success

    # ─── Opportunities ──────────────────────────────────────────────────

    async def get_opportunities(
        self,
        *,
        pipeline_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get opportunities.

        Args:
            pipeline_id: Filter by pipeline.
            stage_id: Filter by stage.
            limit: Maximum number of opportunities.

        Returns:
            Paginated response with 'opportunities'.
        """
        params: Dict[str, Any] = {"limit": limit}
        if pipeline_id:
            params["pipelineId"] = pipeline_id
        if stage_id:
            params["stageId"] = stage_id

        response = await self.get(
            "/opportunities/",
            params=self._location_params(params),
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data
        return {}

    async def create_opportunity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new opportunity.

        Args:
            data: Opportunity data (name, status, pipelineId, stageId, etc.).

        Returns:
            Created opportunity record.
        """
        response = await self.post("/opportunities/", data=data, auth=False)
        if isinstance(response.data, dict):
            return response.data
        return {}

    # ─── Pipelines ──────────────────────────────────────────────────────

    async def get_pipelines(self) -> List[Dict[str, Any]]:
        """Get all pipelines.

        Returns:
            List of pipeline dictionaries.
        """
        response = await self.get(
            "/pipelines/",
            params=self._location_params(),
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("pipelines", [])
        return []

    # ─── Calendars ──────────────────────────────────────────────────────

    async def get_calendars(self) -> List[Dict[str, Any]]:
        """Get all calendars.

        Returns:
            List of calendar dictionaries.
        """
        response = await self.get(
            "/calendars/",
            params=self._location_params(),
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("calendars", [])
        return []

    async def get_calendar_events(
        self,
        calendar_id: str,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get calendar events.

        Args:
            calendar_id: The calendar ID.
            start_date: Start date (ISO format).
            end_date: End date (ISO format).

        Returns:
            List of event dictionaries.
        """
        params: Dict[str, Any] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        response = await self.get(
            f"/calendars/{calendar_id}/events",
            params=params,
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("events", [])
        return []

    # ─── Campaigns ──────────────────────────────────────────────────────

    async def get_campaigns(self) -> List[Dict[str, Any]]:
        """Get all campaigns.

        Returns:
            List of campaign dictionaries.
        """
        response = await self.get(
            "/campaigns/",
            params=self._location_params(),
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("campaigns", [])
        return []

    # ─── Workflows ──────────────────────────────────────────────────────

    async def get_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows.

        Returns:
            List of workflow dictionaries.
        """
        response = await self.get(
            "/workflows/",
            params=self._location_params(),
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("workflows", [])
        return []

    async def add_contact_to_workflow(self, contact_id: str, workflow_id: str) -> bool:
        """Add a contact to a workflow.

        Args:
            contact_id: The contact ID.
            workflow_id: The workflow ID.

        Returns:
            True if successful.
        """
        response = await self.post(
            f"/workflows/{workflow_id}/contacts/{contact_id}",
            auth=False,
        )
        return response.is_success

    # ─── Custom Fields ──────────────────────────────────────────────────

    async def get_custom_fields(self) -> List[Dict[str, Any]]:
        """Get custom fields.

        Returns:
            List of custom field dictionaries.
        """
        response = await self.get(
            "/custom-fields/",
            params=self._location_params(),
            auth=False,
        )
        if isinstance(response.data, dict):
            return response.data.get("customFields", [])
        return []

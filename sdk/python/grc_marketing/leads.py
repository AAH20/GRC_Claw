"""Lead client for the GRC Marketing SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import APIClient
from .types import Lead, LeadCreatePayload, LeadUpdatePayload


class LeadClient:
    """Client for managing marketing leads."""

    def __init__(self, api_client: APIClient) -> None:
        """Initialize the lead client.

        Args:
            api_client: The low-level API client.
        """
        self._client = api_client

    def list(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        source: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """List leads with optional filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page.
            status: Filter by status.
            source: Filter by source.
            sort_by: Field to sort by.
            sort_order: Sort order ('asc' or 'desc').

        Returns:
            Paginated list response with leads.
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        if status:
            params["status"] = status
        if source:
            params["source"] = source

        response = self._client.get("/leads", params=params)
        leads = [Lead.from_dict(lead) for lead in response.get("data", [])]
        return {
            "data": leads,
            "total": response.get("total", 0),
            "page": response.get("page", page),
            "per_page": response.get("per_page", per_page),
            "total_pages": response.get("total_pages", 0),
        }

    def get(self, lead_id: str) -> Lead:
        """Get a lead by ID.

        Args:
            lead_id: The lead ID.

        Returns:
            The lead.
        """
        response = self._client.get(f"/leads/{lead_id}")
        return Lead.from_dict(response["data"])

    def create(self, payload: LeadCreatePayload) -> Lead:
        """Create a new lead.

        Args:
            payload: Lead creation payload.

        Returns:
            The created lead.
        """
        response = self._client.post("/leads", json=dict(payload))
        return Lead.from_dict(response["data"])

    def update(self, lead_id: str, payload: LeadUpdatePayload) -> Lead:
        """Update an existing lead.

        Args:
            lead_id: The lead ID.
            payload: Lead update payload.

        Returns:
            The updated lead.
        """
        response = self._client.patch(f"/leads/{lead_id}", json=dict(payload))
        return Lead.from_dict(response["data"])

    def delete(self, lead_id: str) -> None:
        """Delete a lead.

        Args:
            lead_id: The lead ID.
        """
        self._client.delete(f"/leads/{lead_id}")

    def qualify(self, lead_id: str) -> Lead:
        """Mark a lead as qualified.

        Args:
            lead_id: The lead ID.

        Returns:
            The updated lead.
        """
        return self.update(lead_id, {"status": "qualified"})

    def convert(self, lead_id: str) -> Lead:
        """Mark a lead as converted.

        Args:
            lead_id: The lead ID.

        Returns:
            The updated lead.
        """
        return self.update(lead_id, {"status": "converted"})

    def mark_lost(self, lead_id: str) -> Lead:
        """Mark a lead as lost.

        Args:
            lead_id: The lead ID.

        Returns:
            The updated lead.
        """
        return self.update(lead_id, {"status": "lost"})

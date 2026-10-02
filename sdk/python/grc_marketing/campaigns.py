"""Campaign client for the GRC Marketing SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import APIClient
from .types import Campaign, CampaignCreatePayload, CampaignUpdatePayload


class CampaignClient:
    """Client for managing marketing campaigns."""

    def __init__(self, api_client: APIClient) -> None:
        """Initialize the campaign client.

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
        channel: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """List campaigns with optional filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page.
            status: Filter by status.
            channel: Filter by channel.
            sort_by: Field to sort by.
            sort_order: Sort order ('asc' or 'desc').

        Returns:
            Paginated list response with campaigns.
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        if status:
            params["status"] = status
        if channel:
            params["channel"] = channel

        response = self._client.get("/campaigns", params=params)
        campaigns = [Campaign.from_dict(c) for c in response.get("data", [])]
        return {
            "data": campaigns,
            "total": response.get("total", 0),
            "page": response.get("page", page),
            "per_page": response.get("per_page", per_page),
            "total_pages": response.get("total_pages", 0),
        }

    def get(self, campaign_id: str) -> Campaign:
        """Get a campaign by ID.

        Args:
            campaign_id: The campaign ID.

        Returns:
            The campaign.
        """
        response = self._client.get(f"/campaigns/{campaign_id}")
        return Campaign.from_dict(response["data"])

    def create(self, payload: CampaignCreatePayload) -> Campaign:
        """Create a new campaign.

        Args:
            payload: Campaign creation payload.

        Returns:
            The created campaign.
        """
        response = self._client.post("/campaigns", json=dict(payload))
        return Campaign.from_dict(response["data"])

    def update(self, campaign_id: str, payload: CampaignUpdatePayload) -> Campaign:
        """Update an existing campaign.

        Args:
            campaign_id: The campaign ID.
            payload: Campaign update payload.

        Returns:
            The updated campaign.
        """
        response = self._client.patch(
            f"/campaigns/{campaign_id}", json=dict(payload)
        )
        return Campaign.from_dict(response["data"])

    def delete(self, campaign_id: str) -> None:
        """Delete a campaign.

        Args:
            campaign_id: The campaign ID.
        """
        self._client.delete(f"/campaigns/{campaign_id}")

    def activate(self, campaign_id: str) -> Campaign:
        """Activate a campaign.

        Args:
            campaign_id: The campaign ID.

        Returns:
            The updated campaign.
        """
        return self.update(campaign_id, {"status": "active"})

    def pause(self, campaign_id: str) -> Campaign:
        """Pause a campaign.

        Args:
            campaign_id: The campaign ID.

        Returns:
            The updated campaign.
        """
        return self.update(campaign_id, {"status": "paused"})

    def complete(self, campaign_id: str) -> Campaign:
        """Mark a campaign as completed.

        Args:
            campaign_id: The campaign ID.

        Returns:
            The updated campaign.
        """
        return self.update(campaign_id, {"status": "completed"})

    def archive(self, campaign_id: str) -> Campaign:
        """Archive a campaign.

        Args:
            campaign_id: The campaign ID.

        Returns:
            The updated campaign.
        """
        return self.update(campaign_id, {"status": "archived"})

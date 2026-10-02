"""Journey client for the GRC Marketing SDK."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .client import APIClient
from .types import Journey, JourneyCreatePayload, JourneyUpdatePayload


class JourneyClient:
    """Client for managing customer journeys."""

    def __init__(self, api_client: APIClient) -> None:
        """Initialize the journey client.

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
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """List journeys with optional filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page.
            status: Filter by status.
            sort_by: Field to sort by.
            sort_order: Sort order ('asc' or 'desc').

        Returns:
            Paginated list response with journeys.
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        if status:
            params["status"] = status

        response = self._client.get("/journeys", params=params)
        journeys = [Journey.from_dict(j) for j in response.get("data", [])]
        return {
            "data": journeys,
            "total": response.get("total", 0),
            "page": response.get("page", page),
            "per_page": response.get("per_page", per_page),
            "total_pages": response.get("total_pages", 0),
        }

    def get(self, journey_id: str) -> Journey:
        """Get a journey by ID.

        Args:
            journey_id: The journey ID.

        Returns:
            The journey.
        """
        response = self._client.get(f"/journeys/{journey_id}")
        return Journey.from_dict(response["data"])

    def create(self, payload: JourneyCreatePayload) -> Journey:
        """Create a new journey.

        Args:
            payload: Journey creation payload.

        Returns:
            The created journey.
        """
        response = self._client.post("/journeys", json=dict(payload))
        return Journey.from_dict(response["data"])

    def update(self, journey_id: str, payload: JourneyUpdatePayload) -> Journey:
        """Update an existing journey.

        Args:
            journey_id: The journey ID.
            payload: Journey update payload.

        Returns:
            The updated journey.
        """
        response = self._client.patch(
            f"/journeys/{journey_id}", json=dict(payload)
        )
        return Journey.from_dict(response["data"])

    def delete(self, journey_id: str) -> None:
        """Delete a journey.

        Args:
            journey_id: The journey ID.
        """
        self._client.delete(f"/journeys/{journey_id}")

    def activate(self, journey_id: str) -> Journey:
        """Activate a journey.

        Args:
            journey_id: The journey ID.

        Returns:
            The updated journey.
        """
        return self.update(journey_id, {"status": "active"})

    def pause(self, journey_id: str) -> Journey:
        """Pause a journey.

        Args:
            journey_id: The journey ID.

        Returns:
            The updated journey.
        """
        return self.update(journey_id, {"status": "paused"})

    def complete(self, journey_id: str) -> Journey:
        """Mark a journey as completed.

        Args:
            journey_id: The journey ID.

        Returns:
            The updated journey.
        """
        return self.update(journey_id, {"status": "completed"})

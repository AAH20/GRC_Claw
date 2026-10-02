"""Listing Manager Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from content_marketplace.models.listing import Listing, ListingCreate, ListingStatus, ListingUpdate

logger = logging.getLogger(__name__)


class ListingManagerAgent:
    """Agent responsible for managing content listings.

    Uses LangChain DeepAgents to handle listing creation, updates,
    categorization, and lifecycle management.
    """

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the ListingManagerAgent.

        Args:
            llm: Optional LangChain chat model for AI-powered operations.
        """
        self.llm = llm
        self._listings: dict[UUID, Listing] = {}

    async def create_listing(self, data: ListingCreate) -> Listing:
        """Create a new content listing.

        Args:
            data: Listing creation data.

        Returns:
            The newly created listing.

        Raises:
            ValueError: If listing data is invalid.
        """
        if not data.title or not data.description:
            raise ValueError("Title and description are required")

        listing = Listing(
            title=data.title,
            description=data.description,
            seller_id=data.seller_id,
            category=data.category,
            tags=data.tags,
            base_price=data.base_price,
            currency=data.currency,
            content_url=data.content_url,
            metadata=data.metadata,
            status=ListingStatus.DRAFT,
        )
        self._listings[listing.id] = listing
        logger.info("Created listing %s for seller %s", listing.id, data.seller_id)
        return listing

    async def update_listing(self, listing_id: UUID, data: ListingUpdate) -> Listing:
        """Update an existing listing.

        Args:
            listing_id: The listing UUID to update.
            data: Update data.

        Returns:
            The updated listing.

        Raises:
            KeyError: If listing not found.
        """
        if listing_id not in self._listings:
            raise KeyError(f"Listing {listing_id} not found")

        listing = self._listings[listing_id]
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                setattr(listing, field, value)

        from datetime import UTC, datetime
        listing.updated_at = datetime.now(tz=UTC)
        logger.info("Updated listing %s", listing_id)
        return listing

    async def get_listing(self, listing_id: UUID) -> Listing:
        """Retrieve a listing by ID.

        Args:
            listing_id: The listing UUID.

        Returns:
            The listing.

        Raises:
            KeyError: If listing not found.
        """
        if listing_id not in self._listings:
            raise KeyError(f"Listing {listing_id} not found")
        return self._listings[listing_id]

    async def list_listings(
        self,
        seller_id: str | None = None,
        status: ListingStatus | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Listing]:
        """List listings with optional filters.

        Args:
            seller_id: Filter by seller.
            status: Filter by status.
            category: Filter by category.
            limit: Maximum results.
            offset: Pagination offset.

        Returns:
            Filtered list of listings.
        """
        results = list(self._listings.values())

        if seller_id:
            results = [l for l in results if l.seller_id == seller_id]
        if status:
            results = [l for l in results if l.status == status]
        if category:
            results = [l for l in results if l.category == category]

        return results[offset : offset + limit]

    async def delete_listing(self, listing_id: UUID) -> None:
        """Delete a listing.

        Args:
            listing_id: The listing UUID to delete.

        Raises:
            KeyError: If listing not found.
        """
        if listing_id not in self._listings:
            raise KeyError(f"Listing {listing_id} not found")
        del self._listings[listing_id]
        logger.info("Deleted listing %s", listing_id)

    async def categorize_listing(self, title: str, description: str) -> dict[str, Any]:
        """Use AI to auto-categorize a listing.

        Args:
            title: Listing title.
            description: Listing description.

        Returns:
            Dictionary with suggested category and tags.
        """
        if self.llm is None:
            return {"category": "general", "tags": []}

        prompt = (
            f"Categorize this content listing and suggest tags.\n"
            f"Title: {title}\n"
            f"Description: {description}\n"
            f"Respond with JSON: {{\"category\": \"...\", \"tags\": [\"...\"]}}"
        )

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        import json
        try:
            result = json.loads(response.content)
            return result
        except (json.JSONDecodeError, TypeError):
            return {"category": "general", "tags": []}

    async def moderate_listing(self, listing_id: UUID) -> dict[str, Any]:
        """Use AI to moderate listing content.

        Args:
            listing_id: The listing UUID to moderate.

        Returns:
            Moderation result with approved flag and reasons.
        """
        listing = await self.get_listing(listing_id)

        if self.llm is None:
            return {"approved": True, "reasons": []}

        prompt = (
            f"Moderate this content listing for marketplace policy violations.\n"
            f"Title: {listing.title}\n"
            f"Description: {listing.description}\n"
            f"Respond with JSON: {{\"approved\": true/false, \"reasons\": [\"...\"]}}"
        )

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        import json
        try:
            result = json.loads(response.content)
            return result
        except (json.JSONDecodeError, TypeError):
            return {"approved": True, "reasons": []}

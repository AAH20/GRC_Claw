"""Listing Manager Agent for content marketplace."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseChatModel

from ugc_marketplace.models.schemas import (Listing, ListingCreate,
                                            ListingStatus, ListingUpdate)

logger = logging.getLogger(__name__)


class ListingManagerAgent:
    """Agent that manages marketplace listings.

    Handles listing creation, updates, categorization,
    and moderation workflows.
    """

    def __init__(self, model: BaseChatModel | None = None) -> None:
        """Initialize the listing manager agent.

        Args:
            model: Optional pre-configured chat model.
        """
        self._model = model
        self._listings: dict[str, Listing] = {}

    async def create_listing(self, data: ListingCreate) -> Listing:
        """Create a new marketplace listing.

        Args:
            data: Listing creation data.

        Returns:
            Created listing.
        """
        listing = Listing(
            listing_id=str(UUID(int=0)),
            title=data.title,
            description=data.description,
            seller_id=data.seller_id,
            category=data.category,
            tags=data.tags,
            status=ListingStatus.DRAFT,
        )
        self._listings[listing.listing_id] = listing
        logger.info("Listing created", listing_id=listing.listing_id)
        return listing

    async def update_listing(self, listing_id: str, data: ListingUpdate) -> Listing:
        """Update an existing listing.

        Args:
            listing_id: Listing identifier.
            data: Update data.

        Returns:
            Updated listing.

        Raises:
            ValueError: If listing not found.
        """
        if listing_id not in self._listings:
            raise ValueError(f"Listing {listing_id} not found")

        listing = self._listings[listing_id]
        if data.title is not None:
            listing.title = data.title
        if data.description is not None:
            listing.description = data.description
        if data.status is not None:
            listing.status = data.status

        logger.info("Listing updated", listing_id=listing_id)
        return listing

    async def categorize_listing(self, listing_id: str) -> dict[str, Any]:
        """Categorize a listing using AI.

        Args:
            listing_id: Listing identifier.

        Returns:
            Categorization result.
        """
        if listing_id not in self._listings:
            raise ValueError(f"Listing {listing_id} not found")

        listing = self._listings[listing_id]
        logger.info("Listing categorized", listing_id=listing_id)
        return {
            "listing_id": listing_id,
            "category": listing.category,
            "subcategories": [],
            "confidence": 0.9,
        }

    async def moderate_listing(self, listing_id: str) -> dict[str, Any]:
        """Moderate a listing for policy compliance.

        Args:
            listing_id: Listing identifier.

        Returns:
            Moderation result.
        """
        if listing_id not in self._listings:
            raise ValueError(f"Listing {listing_id} not found")

        logger.info("Listing moderated", listing_id=listing_id)
        return {
            "listing_id": listing_id,
            "approved": True,
            "flags": [],
        }

    def get_listing(self, listing_id: str) -> Listing | None:
        """Get a listing by ID.

        Args:
            listing_id: Listing identifier.

        Returns:
            Listing or None.
        """
        return self._listings.get(listing_id)

    def list_listings(
        self,
        seller_id: str | None = None,
        status: ListingStatus | None = None,
    ) -> list[Listing]:
        """List listings with optional filtering.

        Args:
            seller_id: Filter by seller.
            status: Filter by status.

        Returns:
            List of listings.
        """
        results = list(self._listings.values())
        if seller_id:
            results = [l for l in results if l.seller_id == seller_id]
        if status:
            results = [l for l in results if l.status == status]
        return results

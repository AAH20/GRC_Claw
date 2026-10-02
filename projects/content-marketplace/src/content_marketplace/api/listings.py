"""Listing API routes."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from content_marketplace.agents.listing_manager import ListingManagerAgent
from content_marketplace.models.listing import Listing, ListingCreate, ListingStatus, ListingUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


_listing_agent_instance: ListingManagerAgent | None = None


def get_listing_agent() -> ListingManagerAgent:
    """Dependency to get the listing manager agent (singleton)."""
    global _listing_agent_instance
    if _listing_agent_instance is None:
        _listing_agent_instance = ListingManagerAgent()
    return _listing_agent_instance


@router.post("", response_model=Listing, status_code=status.HTTP_201_CREATED)
async def create_listing(
    data: ListingCreate,
    agent: ListingManagerAgent = Depends(get_listing_agent),  # noqa: B008
) -> Listing:
    """Create a new content listing."""
    try:
        return await agent.create_listing(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{listing_id}", response_model=Listing)
async def get_listing(
    listing_id: UUID,
    agent: ListingManagerAgent = Depends(get_listing_agent),  # noqa: B008
) -> Listing:
    """Get a listing by ID."""
    try:
        return await agent.get_listing(listing_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")


@router.put("/{listing_id}", response_model=Listing)
async def update_listing(
    listing_id: UUID,
    data: ListingUpdate,
    agent: ListingManagerAgent = Depends(get_listing_agent),  # noqa: B008
) -> Listing:
    """Update an existing listing."""
    try:
        return await agent.update_listing(listing_id, data)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: UUID,
    agent: ListingManagerAgent = Depends(get_listing_agent),  # noqa: B008
) -> None:
    """Delete a listing."""
    try:
        await agent.delete_listing(listing_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")


@router.get("", response_model=list[Listing])
async def list_listings(
    seller_id: str | None = Query(None),
    status: ListingStatus | None = Query(None),
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    agent: ListingManagerAgent = Depends(get_listing_agent),  # noqa: B008
) -> list[Listing]:
    """List listings with optional filters."""
    return await agent.list_listings(
        seller_id=seller_id, status=status, category=category, limit=limit, offset=offset
    )


@router.post("/{listing_id}/categorize")
async def categorize_listing(
    listing_id: UUID,
    agent: ListingManagerAgent = Depends(get_listing_agent),  # noqa: B008
) -> dict:
    """Auto-categorize a listing using AI."""
    try:
        listing = await agent.get_listing(listing_id)
        return await agent.categorize_listing(listing.title, listing.description)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")


@router.post("/{listing_id}/moderate")
async def moderate_listing(
    listing_id: UUID,
    agent: ListingManagerAgent = Depends(get_listing_agent),  # noqa: B008
) -> dict:
    """Moderate a listing using AI."""
    try:
        return await agent.moderate_listing(listing_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

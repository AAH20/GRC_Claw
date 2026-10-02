"""Content generation and management endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from employer_branding.agents.content_generator import ContentGeneratorAgent
from employer_branding.models import BrandAsset, ContentGenerationRequest

router = APIRouter(prefix="/api/v1/content", tags=["content"])

# In-memory store for demo purposes
_content_store: dict[UUID, BrandAsset] = {}


def get_content_agent() -> ContentGeneratorAgent:
    """Dependency to get content generator agent."""
    return ContentGeneratorAgent()


@router.post("/generate", response_model=BrandAsset, status_code=status.HTTP_201_CREATED)
async def generate_content(
    request: ContentGenerationRequest,
    agent: ContentGeneratorAgent = Depends(get_content_agent),
) -> BrandAsset:
    """Generate new brand content.

    Args:
        request: Content generation request.
        agent: Content generator agent.

    Returns:
        Generated BrandAsset.

    Raises:
        HTTPException: If generation fails.
    """
    try:
        asset = await agent.run(request)
        _content_store[asset.id] = asset
        return asset
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {exc}",
        ) from exc


@router.get("/{asset_id}", response_model=BrandAsset)
async def get_content(asset_id: UUID) -> BrandAsset:
    """Get a content asset by ID.

    Args:
        asset_id: Asset UUID.

    Returns:
        BrandAsset if found.

    Raises:
        HTTPException: If asset not found.
    """
    if asset_id not in _content_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content asset {asset_id} not found",
        )
    return _content_store[asset_id]


@router.get("/", response_model=list[BrandAsset])
async def list_content(
    skip: int = 0,
    limit: int = 100,
) -> list[BrandAsset]:
    """List all content assets.

    Args:
        skip: Number of items to skip.
        limit: Maximum items to return.

    Returns:
        List of BrandAsset objects.
    """
    assets = list(_content_store.values())
    return assets[skip : skip + limit]


@router.patch("/{asset_id}", response_model=BrandAsset)
async def update_content(
    asset_id: UUID,
    updates: dict,
) -> BrandAsset:
    """Update a content asset.

    Args:
        asset_id: Asset UUID.
        updates: Dictionary of fields to update.

    Returns:
        Updated BrandAsset.

    Raises:
        HTTPException: If asset not found.
    """
    if asset_id not in _content_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content asset {asset_id} not found",
        )

    asset = _content_store[asset_id]
    for key, value in updates.items():
        if hasattr(asset, key):
            setattr(asset, key, value)

    _content_store[asset_id] = asset
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(asset_id: UUID) -> None:
    """Delete a content asset.

    Args:
        asset_id: Asset UUID.

    Raises:
        HTTPException: If asset not found.
    """
    if asset_id not in _content_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content asset {asset_id} not found",
        )
    del _content_store[asset_id]


@router.post("/{asset_id}/publish", response_model=BrandAsset)
async def publish_content(asset_id: UUID) -> BrandAsset:
    """Publish a content asset.

    Args:
        asset_id: Asset UUID.

    Returns:
        Published BrandAsset.

    Raises:
        HTTPException: If asset not found.
    """
    if asset_id not in _content_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content asset {asset_id} not found",
        )

    asset = _content_store[asset_id]
    asset.is_published = True
    asset.published_at = datetime.utcnow()
    _content_store[asset_id] = asset
    return asset

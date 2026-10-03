"""Moderation item API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, status
from moderation_queue.api.dependencies import get_logger
from moderation_queue.models import ContentType, ModerationItem, ModerationStatus
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from uuid import UUID

router = APIRouter(prefix="/items", tags=["items"])

# In-memory store for demo purposes
_items_db: dict[UUID, ModerationItem] = {}


class CreateItemRequest(BaseModel):
    """Request model for creating a moderation item."""

    content: str = Field(..., min_length=1, description="Content to moderate")
    content_type: ContentType = Field(
        default=ContentType.TEXT, description="Content type"
    )
    author_id: str = Field(..., description="Author ID")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    tags: list[str] = Field(default_factory=list, description="Content tags")


class UpdateItemRequest(BaseModel):
    """Request model for updating a moderation item."""

    status: ModerationStatus | None = Field(default=None, description="New status")
    priority_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Priority score"
    )
    queue_id: UUID | None = Field(default=None, description="Queue assignment")
    review_notes: str | None = Field(default=None, description="Review notes")
    reviewer_id: str | None = Field(default=None, description="Reviewer ID")


class ItemListResponse(BaseModel):
    """Response model for item list."""

    items: list[ModerationItem] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")


@router.post(
    "",
    response_model=ModerationItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new moderation item",
    description="Submit a new content item for moderation",
)
async def create_item(
    request: CreateItemRequest,
    logger=Depends(get_logger),  # noqa: B008
) -> ModerationItem:
    """Create a new moderation item.

    Args:
        request: Item creation request.
        logger: Request logger.

    Returns:
        ModerationItem: Created item.
    """
    item = ModerationItem(
        content=request.content,
        content_type=request.content_type,
        author_id=request.author_id,
        metadata=request.metadata,
        tags=request.tags,
    )
    _items_db[item.id] = item
    logger.info("Created moderation item", item_id=str(item.id))
    return item


@router.get(
    "",
    response_model=ItemListResponse,
    summary="List moderation items",
    description="Get a paginated list of moderation items",
)
async def list_items(
    status_filter: ModerationStatus | None = Query(
        default=None, alias="status"
    ),  # noqa: B008
    content_type: ContentType | None = Query(default=None),  # noqa: B008
    author_id: str | None = Query(default=None),  # noqa: B008
    page: int = Query(default=1, ge=1),  # noqa: B008
    page_size: int = Query(default=20, ge=1, le=100),  # noqa: B008
    logger=Depends(get_logger),  # noqa: B008
) -> ItemListResponse:
    """List moderation items with optional filters.

    Args:
        status_filter: Filter by status.
        content_type: Filter by content type.
        author_id: Filter by author.
        page: Page number.
        page_size: Items per page.
        logger: Request logger.

    Returns:
        ItemListResponse: Paginated item list.
    """
    items = list(_items_db.values())

    if status_filter:
        items = [i for i in items if i.status == status_filter]
    if content_type:
        items = [i for i in items if i.content_type == content_type]
    if author_id:
        items = [i for i in items if i.author_id == author_id]

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = items[start:end]

    return ItemListResponse(
        items=paginated, total=total, page=page, page_size=page_size
    )


@router.get(
    "/{item_id}",
    response_model=ModerationItem,
    summary="Get a moderation item",
    description="Get a specific moderation item by ID",
)
async def get_item(
    item_id: UUID,
    logger=Depends(get_logger),  # noqa: B008
) -> ModerationItem:
    """Get a moderation item by ID.

    Args:
        item_id: Item identifier.
        logger: Request logger.

    Returns:
        ModerationItem: The requested item.

    Raises:
        HTTPException: If item not found.
    """
    item = _items_db.get(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return item


@router.patch(
    "/{item_id}",
    response_model=ModerationItem,
    summary="Update a moderation item",
    description="Update a moderation item's status or metadata",
)
async def update_item(
    item_id: UUID,
    request: UpdateItemRequest,
    logger=Depends(get_logger),  # noqa: B008
) -> ModerationItem:
    """Update a moderation item.

    Args:
        item_id: Item identifier.
        request: Update request.
        logger: Request logger.

    Returns:
        ModerationItem: Updated item.

    Raises:
        HTTPException: If item not found.
    """
    item = _items_db.get(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )

    if request.status is not None:
        item.status = request.status
    if request.priority_score is not None:
        item.priority_score = request.priority_score
    if request.queue_id is not None:
        item.queue_id = request.queue_id
    if request.review_notes is not None:
        item.review_notes = request.review_notes
    if request.reviewer_id is not None:
        item.reviewer_id = request.reviewer_id

    from datetime import datetime

    item.updated_at = datetime.utcnow()
    _items_db[item_id] = item
    logger.info("Updated moderation item", item_id=str(item_id))
    return item


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a moderation item",
    description="Delete a moderation item by ID",
)
async def delete_item(
    item_id: UUID,
    logger=Depends(get_logger),  # noqa: B008
) -> None:
    """Delete a moderation item.

    Args:
        item_id: Item identifier.
        logger: Request logger.

    Raises:
        HTTPException: If item not found.
    """
    if item_id not in _items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    del _items_db[item_id]
    logger.info("Deleted moderation item", item_id=str(item_id))

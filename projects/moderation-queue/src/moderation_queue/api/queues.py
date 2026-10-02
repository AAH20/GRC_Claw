"""Queue API routes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import Field

from moderation_queue.api.dependencies import get_logger
from moderation_queue.models import ContentType, Queue, QueueMetrics

router = APIRouter(prefix="/queues", tags=["queues"])

# In-memory store for demo purposes
_queues_db: dict[UUID, Queue] = {}


class CreateQueueRequest(BaseModel):
    """Request model for creating a queue."""

    name: str = Field(..., min_length=1, description="Queue name")
    description: str = Field(default="", description="Queue description")
    content_types: list[ContentType] = Field(default_factory=list, description="Content types")
    max_size: int = Field(default=1000, ge=1, description="Maximum items")
    priority_weights: dict[str, float] = Field(default_factory=dict, description="Priority weights")
    assigned_reviewers: list[str] = Field(default_factory=list, description="Reviewer IDs")


class QueueListResponse(BaseModel):
    """Response model for queue list."""

    queues: list[Queue] = Field(..., description="List of queues")
    total: int = Field(..., description="Total number of queues")


@router.post(
    "",
    response_model=Queue,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new queue",
    description="Create a new moderation queue",
)
async def create_queue(
    request: CreateQueueRequest,
    logger=Depends(get_logger),
) -> Queue:
    """Create a new moderation queue.

    Args:
        request: Queue creation request.
        logger: Request logger.

    Returns:
        Queue: Created queue.
    """
    queue = Queue(
        name=request.name,
        description=request.description,
        content_types=request.content_types,
        max_size=request.max_size,
        priority_weights=request.priority_weights,
        assigned_reviewers=request.assigned_reviewers,
    )
    _queues_db[queue.id] = queue
    logger.info("Created queue", queue_id=str(queue.id))
    return queue


@router.get(
    "",
    response_model=QueueListResponse,
    summary="List queues",
    description="Get a list of all moderation queues",
)
async def list_queues(
    active_only: bool = Query(default=False, description="Filter active queues only"),
    logger=Depends(get_logger),
) -> QueueListResponse:
    """List moderation queues.

    Args:
        active_only: Filter to active queues only.
        logger: Request logger.

    Returns:
        QueueListResponse: List of queues.
    """
    queues = list(_queues_db.values())
    if active_only:
        queues = [q for q in queues if q.is_active]
    return QueueListResponse(queues=queues, total=len(queues))


@router.get(
    "/{queue_id}",
    response_model=Queue,
    summary="Get a queue",
    description="Get a specific queue by ID",
)
async def get_queue(
    queue_id: UUID,
    logger=Depends(get_logger),
) -> Queue:
    """Get a queue by ID.

    Args:
        queue_id: Queue identifier.
        logger: Request logger.

    Returns:
        Queue: The requested queue.

    Raises:
        HTTPException: If queue not found.
    """
    queue = _queues_db.get(queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found",
        )
    return queue


@router.get(
    "/{queue_id}/metrics",
    response_model=QueueMetrics,
    summary="Get queue metrics",
    description="Get performance metrics for a queue",
)
async def get_queue_metrics(
    queue_id: UUID,
    logger=Depends(get_logger),
) -> QueueMetrics:
    """Get metrics for a queue.

    Args:
        queue_id: Queue identifier.
        logger: Request logger.

    Returns:
        QueueMetrics: Queue metrics.

    Raises:
        HTTPException: If queue not found.
    """
    queue = _queues_db.get(queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found",
        )

    # Generate placeholder metrics
    return QueueMetrics(
        queue_id=queue_id,
        total_items=0,
        pending_items=0,
        in_review_items=0,
        resolved_items=0,
    )


@router.patch(
    "/{queue_id}",
    response_model=Queue,
    summary="Update a queue",
    description="Update queue configuration",
)
async def update_queue(
    queue_id: UUID,
    name: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    max_size: int | None = Query(default=None, ge=1),
    logger=Depends(get_logger),
) -> Queue:
    """Update a queue.

    Args:
        queue_id: Queue identifier.
        name: New name.
        is_active: New active status.
        max_size: New maximum size.
        logger: Request logger.

    Returns:
        Queue: Updated queue.

    Raises:
        HTTPException: If queue not found.
    """
    queue = _queues_db.get(queue_id)
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found",
        )

    if name is not None:
        queue.name = name
    if is_active is not None:
        queue.is_active = is_active
    if max_size is not None:
        queue.max_size = max_size

    queue.updated_at = datetime.utcnow()
    _queues_db[queue_id] = queue
    logger.info("Updated queue", queue_id=str(queue_id))
    return queue


@router.delete(
    "/{queue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a queue",
    description="Delete a queue by ID",
)
async def delete_queue(
    queue_id: UUID,
    logger=Depends(get_logger),
) -> None:
    """Delete a queue.

    Args:
        queue_id: Queue identifier.
        logger: Request logger.

    Raises:
        HTTPException: If queue not found.
    """
    if queue_id not in _queues_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found",
        )
    del _queues_db[queue_id]
    logger.info("Deleted queue", queue_id=str(queue_id))

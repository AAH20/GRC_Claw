"""Journey management API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status

from api.models import (
    JourneyCreateRequest,
    JourneyExecuteRequest,
    JourneyExecuteResponse,
    JourneyListResponse,
    JourneyResponse,
    JourneyStatus,
    JourneyStatusResponse,
    JourneyUpdateRequest,
)
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# In-memory store for demo purposes — replace with database in production
_journeys: dict[str, dict[str, Any]] = {}


@router.post("", response_model=JourneyResponse, status_code=status.HTTP_201_CREATED)
async def create_journey(request: JourneyCreateRequest) -> JourneyResponse:
    """Create a new customer journey.

    Args:
        request: The journey creation request.

    Returns:
        The created journey.
    """
    journey_id = str(uuid.uuid4())
    now = datetime.utcnow()

    journey = {
        "id": journey_id,
        "name": request.name,
        "description": request.description,
        "target_audience": request.target_audience,
        "business_goal": request.business_goal,
        "channels": [c.value for c in request.channels],
        "status": JourneyStatus.DRAFT.value,
        "stages": [],
        "created_at": now,
        "updated_at": now,
        "metadata": request.metadata,
    }

    _journeys[journey_id] = journey
    logger.info("journey_created", journey_id=journey_id, name=request.name)

    return JourneyResponse(**journey)


@router.get("", response_model=JourneyListResponse)
async def list_journeys(
    page: int = 1,
    page_size: int = 20,
    status: JourneyStatus | None = None,
) -> JourneyListResponse:
    """List all journeys with optional filtering.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status: Optional status filter.

    Returns:
        Paginated list of journeys.
    """
    journeys = list(_journeys.values())

    if status:
        journeys = [j for j in journeys if j["status"] == status.value]

    total = len(journeys)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = journeys[start:end]

    return JourneyListResponse(
        journeys=[JourneyResponse(**j) for j in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{journey_id}", response_model=JourneyResponse)
async def get_journey(journey_id: str) -> JourneyResponse:
    """Get a journey by ID.

    Args:
        journey_id: The journey identifier.

    Returns:
        The journey.

    Raises:
        HTTPException: If the journey is not found.
    """
    journey = _journeys.get(journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey {journey_id} not found",
        )
    return JourneyResponse(**journey)


@router.put("/{journey_id}", response_model=JourneyResponse)
async def update_journey(journey_id: str, request: JourneyUpdateRequest) -> JourneyResponse:
    """Update a journey.

    Args:
        journey_id: The journey identifier.
        request: The update request.

    Returns:
        The updated journey.

    Raises:
        HTTPException: If the journey is not found.
    """
    journey = _journeys.get(journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey {journey_id} not found",
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "channels" and value is not None:
            journey[key] = [c.value for c in value]
        else:
            journey[key] = value

    journey["updated_at"] = datetime.utcnow()
    logger.info("journey_updated", journey_id=journey_id)

    return JourneyResponse(**journey)


@router.delete("/{journey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journey(journey_id: str) -> None:
    """Delete a journey.

    Args:
        journey_id: The journey identifier.

    Raises:
        HTTPException: If the journey is not found.
    """
    if journey_id not in _journeys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey {journey_id} not found",
        )
    del _journeys[journey_id]
    logger.info("journey_deleted", journey_id=journey_id)


@router.post("/{journey_id}/execute", response_model=JourneyExecuteResponse)
async def execute_journey(
    journey_id: str, request: JourneyExecuteRequest | None = None
) -> JourneyExecuteResponse:
    """Execute a journey.

    Args:
        journey_id: The journey identifier.
        request: Optional execution request.

    Returns:
        The execution response.

    Raises:
        HTTPException: If the journey is not found.
    """
    journey = _journeys.get(journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey {journey_id} not found",
        )

    execution_id = str(uuid.uuid4())
    journey["status"] = JourneyStatus.ACTIVE.value
    journey["updated_at"] = datetime.utcnow()

    logger.info(
        "journey_execution_started",
        journey_id=journey_id,
        execution_id=execution_id,
    )

    return JourneyExecuteResponse(
        execution_id=execution_id,
        journey_id=journey_id,
        status=JourneyStatus.ACTIVE,
        message="Journey execution started",
    )


@router.get("/{journey_id}/status", response_model=JourneyStatusResponse)
async def get_journey_status(journey_id: str) -> JourneyStatusResponse:
    """Get the execution status of a journey.

    Args:
        journey_id: The journey identifier.

    Returns:
        The journey status.

    Raises:
        HTTPException: If the journey is not found.
    """
    journey = _journeys.get(journey_id)
    if not journey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journey {journey_id} not found",
        )

    return JourneyStatusResponse(
        journey_id=journey_id,
        status=JourneyStatus(journey["status"]),
        progress=0.0,
        customers_processed=0,
        customers_total=0,
    )

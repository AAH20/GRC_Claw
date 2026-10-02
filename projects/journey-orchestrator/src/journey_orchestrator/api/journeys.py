"""Journey API routes."""

from __future__ import annotations

from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException

from journey_orchestrator.agents.journey_designer import JourneyDesigner, JourneyDesignRequest
from journey_orchestrator.models.journey import Journey, JourneyCreate, JourneyStatus

logger = structlog.get_logger(__name__)
router = APIRouter()

# In-memory store (replace with database in production)
_journeys: dict[str, Journey] = {}


@router.post("", response_model=Journey, status_code=201)
async def create_journey(request: JourneyCreate) -> Journey:
    """Create a new customer journey.

    Args:
        request: The journey creation request.

    Returns:
        The created journey.

    Raises:
        HTTPException: If journey creation fails.
    """
    designer = JourneyDesigner()
    design_request = JourneyDesignRequest(
        business_goal=request.business_goal,
        target_audience=request.target_audience,
        channels=request.channels,
        constraints=request.constraints,
    )

    try:
        blueprint = await designer.design(design_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    journey = Journey(
        id=str(uuid4()),
        name=blueprint.name,
        description=blueprint.description,
        business_goal=request.business_goal,
        target_audience=request.target_audience,
        channels=request.channels,
        status=JourneyStatus.DRAFT,
        steps=[step.model_dump() for step in blueprint.steps],
        success_metrics=blueprint.success_metrics,
    )

    _journeys[journey.id] = journey
    logger.info("Journey created", journey_id=journey.id)
    return journey


@router.get("/{journey_id}", response_model=Journey)
async def get_journey(journey_id: str) -> Journey:
    """Get a journey by ID.

    Args:
        journey_id: The journey ID.

    Returns:
        The journey.

    Raises:
        HTTPException: If journey not found.
    """
    journey = _journeys.get(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")
    return journey


@router.get("", response_model=list[Journey])
async def list_journeys() -> list[Journey]:
    """List all journeys.

    Returns:
        List of all journeys.
    """
    return list(_journeys.values())


@router.post("/{journey_id}/activate", response_model=Journey)
async def activate_journey(journey_id: str) -> Journey:
    """Activate a journey.

    Args:
        journey_id: The journey ID.

    Returns:
        The activated journey.

    Raises:
        HTTPException: If journey not found or activation fails.
    """
    journey = _journeys.get(journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    journey.status = JourneyStatus.ACTIVE
    logger.info("Journey activated", journey_id=journey_id)
    return journey

"""Segments API routes."""

from __future__ import annotations

from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)
router = APIRouter()

# In-memory store (replace with database in production)
_segments: dict[str, dict] = {}


class SegmentCreate(BaseModel):
    """Request to create a segment."""

    name: str = Field(..., description="Segment name")
    description: str = Field(default="", description="Segment description")
    criteria: dict = Field(default_factory=dict, description="Segment criteria")


class SegmentResponse(BaseModel):
    """Segment response model."""

    id: str
    name: str
    description: str
    criteria: dict
    customer_count: int = 0


@router.post("", response_model=SegmentResponse, status_code=201)
async def create_segment(request: SegmentCreate) -> SegmentResponse:
    """Create a new customer segment.

    Args:
        request: The segment creation request.

    Returns:
        The created segment.

    Raises:
        HTTPException: If segment creation fails.
    """
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="name must not be empty")

    segment_id = str(uuid4())
    segment = {
        "id": segment_id,
        "name": request.name,
        "description": request.description,
        "criteria": request.criteria,
        "customer_count": 0,
    }

    _segments[segment_id] = segment
    logger.info("Segment created", segment_id=segment_id)
    return SegmentResponse(**segment)


@router.get("", response_model=list[SegmentResponse])
async def list_segments() -> list[SegmentResponse]:
    """List all segments.

    Returns:
        List of all segments.
    """
    return [SegmentResponse(**s) for s in _segments.values()]


@router.get("/{segment_id}", response_model=SegmentResponse)
async def get_segment(segment_id: str) -> SegmentResponse:
    """Get a segment by ID.

    Args:
        segment_id: The segment ID.

    Returns:
        The segment.

    Raises:
        HTTPException: If segment not found.
    """
    segment = _segments.get(segment_id)
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return SegmentResponse(**segment)

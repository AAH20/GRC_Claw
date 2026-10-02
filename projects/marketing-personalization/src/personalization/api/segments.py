"""Segment API routes."""

from __future__ import annotations

from datetime import UTC
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter()


class SegmentCreate(BaseModel):
    """Segment creation request model."""

    name: str
    description: str | None = None
    criteria: dict[str, Any] = Field(default_factory=dict)
    segment_type: str = "dynamic"


class SegmentResponse(BaseModel):
    """Segment response model."""

    segment_id: str
    name: str
    description: str | None = None
    segment_type: str
    customer_count: int = 0
    criteria: dict[str, Any] = Field(default_factory=dict)
    created_at: str


_segments: dict[str, dict[str, Any]] = {}


@router.post("", response_model=SegmentResponse, status_code=status.HTTP_201_CREATED)
async def create_segment(segment: SegmentCreate) -> SegmentResponse:
    """Create a new customer segment."""
    import uuid
    from datetime import datetime

    segment_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    segment_data = {
        "segment_id": segment_id,
        "name": segment.name,
        "description": segment.description,
        "segment_type": segment.segment_type,
        "customer_count": 0,
        "criteria": segment.criteria,
        "created_at": now,
    }
    _segments[segment_id] = segment_data
    logger.info("Segment created", segment_id=segment_id, name=segment.name)
    return SegmentResponse(**segment_data)


@router.get("", response_model=list[SegmentResponse])
async def list_segments() -> list[SegmentResponse]:
    """List all segments."""
    logger.info("Listing segments", count=len(_segments))
    return [SegmentResponse(**s) for s in _segments.values()]


@router.get("/{segment_id}", response_model=SegmentResponse)
async def get_segment(segment_id: str) -> SegmentResponse:
    """Get a segment by ID."""
    if segment_id not in _segments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Segment {segment_id} not found",
        )
    return SegmentResponse(**_segments[segment_id])

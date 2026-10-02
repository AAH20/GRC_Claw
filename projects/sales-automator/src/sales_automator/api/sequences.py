"""API routes for outreach sequence management."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from sales_automator.agents.outreach import OutreachAgent, OutreachSequence

logger = structlog.get_logger(__name__)
router = APIRouter()

# In-memory store for demo purposes — replace with database in production
_sequences: dict[str, OutreachSequence] = {}
_agent = OutreachAgent()


class CreateSequenceRequest(BaseModel):
    """Request model for creating an outreach sequence."""

    name: str = Field(..., min_length=1, description="Sequence name")
    prospect_id: str = Field(..., description="Target prospect ID")
    steps: int = Field(5, ge=1, le=10, description="Number of steps")
    context: dict[str, Any] = Field(default_factory=dict, description="Prospect context")


class EnrollRequest(BaseModel):
    """Request model for enrolling a prospect in a sequence."""

    prospect_id: str = Field(..., description="Prospect to enroll")
    start_step: int = Field(1, ge=1, description="Step to start from")


class SequenceResponse(BaseModel):
    """Response model for an outreach sequence."""

    id: str
    name: str
    steps: list[dict[str, Any]]
    target_prospect_id: str
    status: str = "draft"
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/sequences", response_model=SequenceResponse, status_code=status.HTTP_201_CREATED)
async def create_sequence(request: CreateSequenceRequest) -> SequenceResponse:
    """Create a new outreach sequence.

    Args:
        request: Sequence creation data.

    Returns:
        The created sequence.
    """
    sequence = await _agent.generate_sequence(
        prospect_id=request.prospect_id,
        context=request.context,
        steps=request.steps,
    )
    sequence.name = request.name
    _sequences[sequence.id] = sequence
    logger.info("Created sequence", sequence_id=sequence.id, prospect_id=request.prospect_id)
    return SequenceResponse(**sequence.model_dump())


@router.get("/sequences", response_model=list[SequenceResponse])
async def list_sequences(
    skip: int = 0,
    limit: int = 100,
) -> list[SequenceResponse]:
    """List all outreach sequences.

    Args:
        skip: Number of sequences to skip.
        limit: Maximum number to return.

    Returns:
        List of sequences.
    """
    sequences = list(_sequences.values())[skip : skip + limit]
    return [SequenceResponse(**s.model_dump()) for s in sequences]


@router.get("/sequences/{sequence_id}", response_model=SequenceResponse)
async def get_sequence(sequence_id: str) -> SequenceResponse:
    """Get a sequence by ID.

    Args:
        sequence_id: The sequence ID.

    Returns:
        The sequence.

    Raises:
        HTTPException: If sequence not found.
    """
    sequence = _sequences.get(sequence_id)
    if not sequence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sequence {sequence_id} not found",
        )
    return SequenceResponse(**sequence.model_dump())


@router.post("/sequences/{sequence_id}/enroll", response_model=dict[str, Any])
async def enroll_prospect(sequence_id: str, request: EnrollRequest) -> dict[str, Any]:
    """Enroll a prospect in a sequence.

    Args:
        sequence_id: The sequence ID.
        request: Enrollment data.

    Returns:
        Enrollment confirmation.

    Raises:
        HTTPException: If sequence not found.
    """
    sequence = _sequences.get(sequence_id)
    if not sequence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sequence {sequence_id} not found",
        )
    logger.info(
        "Enrolled prospect in sequence",
        sequence_id=sequence_id,
        prospect_id=request.prospect_id,
    )
    return {
        "sequence_id": sequence_id,
        "prospect_id": request.prospect_id,
        "status": "enrolled",
        "started_at": "2026-10-01T00:00:00Z",
    }

"""API routes for lead nurture endpoints."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from lead_scorer.agents.lead_nurture import LeadNurtureAgent, NurtureStatus
from lead_scorer.agents.scoring import LeadGrade
from lead_scorer.models.routing import (
    NurtureEnrollment,
    NurtureEnrollmentRequest,
    NurtureSequence,
    NurtureSequenceCreate,
    NurtureSequenceResponse,
)

router = APIRouter(prefix="/api/v1/nurture", tags=["nurture"])


class EnrollRequest(BaseModel):
    """Request model for enrolling a lead in nurture."""

    lead_id: str = Field(..., min_length=1, description="Lead identifier")
    sequence_id: str = Field(..., min_length=1, description="Sequence identifier")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnrollResponse(BaseModel):
    """Response model for enrollment."""

    success: bool
    data: NurtureEnrollment
    message: str = ""


class SequenceListResponse(BaseModel):
    """Response model for sequence list."""

    success: bool
    sequences: list[NurtureSequence]
    total: int


class EngagementEventRequest(BaseModel):
    """Request model for recording engagement."""

    enrollment_id: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EngagementEventResponse(BaseModel):
    """Response model for engagement event."""

    success: bool
    message: str = ""


class AdvanceStepResponse(BaseModel):
    """Response model for step advancement."""

    success: bool
    data: NurtureEnrollment | None = None
    message: str = ""


class ExitEvaluationRequest(BaseModel):
    """Request model for exit evaluation."""

    enrollment_id: str = Field(..., min_length=1)
    current_score: float | None = Field(default=None, ge=0, le=100)
    current_grade: str | None = None
    qualification_status: str | None = None


class ExitEvaluationResponse(BaseModel):
    """Response model for exit evaluation."""

    success: bool
    should_exit: bool
    reason: str
    destination: str | None = None
    engagement_score: float | None = None


class NurtureStatsResponse(BaseModel):
    """Response model for nurture statistics."""

    success: bool
    stats: dict[str, int]


def get_nurture_agent() -> LeadNurtureAgent:
    """Dependency to get nurture agent instance."""
    return LeadNurtureAgent()


@router.post(
    "/sequences",
    response_model=NurtureSequenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sequence(
    request: NurtureSequenceCreate,
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
) -> NurtureSequenceResponse:
    """Create a new nurture sequence.

    Args:
        request: Sequence creation request.
        nurture_agent: Nurture agent instance.

    Returns:
        NurtureSequenceResponse with created sequence.

    Raises:
        HTTPException: If sequence creation fails.
    """
    try:
        sequence = nurture_agent.create_sequence(request)
        return NurtureSequenceResponse(
            success=True, data=sequence, message="Sequence created successfully"
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sequence creation failed: {str(exc)}",
        ) from exc


@router.get("/sequences", response_model=SequenceListResponse)
async def list_sequences(
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
    active_only: bool = True,
) -> SequenceListResponse:
    """List all nurture sequences.

    Args:
        active_only: If True, return only active sequences.
        nurture_agent: Nurture agent instance.

    Returns:
        SequenceListResponse with all sequences.
    """
    sequences = nurture_agent.list_sequences(active_only=active_only)
    return SequenceListResponse(success=True, sequences=sequences, total=len(sequences))


@router.get("/sequences/{sequence_id}", response_model=NurtureSequenceResponse)
async def get_sequence(
    sequence_id: str,
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
) -> NurtureSequenceResponse:
    """Get a nurture sequence by ID.

    Args:
        sequence_id: The sequence identifier.
        nurture_agent: Nurture agent instance.

    Returns:
        NurtureSequenceResponse with the sequence.

    Raises:
        HTTPException: If sequence not found.
    """
    sequence = nurture_agent.get_sequence(sequence_id)
    if not sequence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sequence {sequence_id} not found",
        )
    return NurtureSequenceResponse(success=True, data=sequence)


@router.delete("/sequences/{sequence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sequence(
    sequence_id: str,
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
) -> None:
    """Delete a nurture sequence.

    Args:
        sequence_id: The sequence identifier.
        nurture_agent: Nurture agent instance.

    Raises:
        HTTPException: If sequence not found.
    """
    deleted = nurture_agent.delete_sequence(sequence_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sequence {sequence_id} not found",
        )


@router.post("/enroll", response_model=EnrollResponse, status_code=status.HTTP_201_CREATED)
async def enroll_lead(
    request: EnrollRequest,
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
) -> EnrollResponse:
    """Enroll a lead in a nurture sequence.

    Args:
        request: Enrollment request.
        nurture_agent: Nurture agent instance.

    Returns:
        EnrollResponse with enrollment details.

    Raises:
        HTTPException: If enrollment fails.
    """
    try:
        enrollment_request = NurtureEnrollmentRequest(
            lead_id=request.lead_id,
            sequence_id=request.sequence_id,
            metadata=request.metadata,
        )
        enrollment = await nurture_agent.enroll(enrollment_request)
        return EnrollResponse(
            success=True, data=enrollment, message="Lead enrolled successfully"
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrollment failed: {str(exc)}",
        ) from exc


@router.get("/enrollments/{enrollment_id}", response_model=EnrollResponse)
async def get_enrollment(
    enrollment_id: str,
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
) -> EnrollResponse:
    """Get an enrollment by ID.

    Args:
        enrollment_id: The enrollment identifier.
        nurture_agent: Nurture agent instance.

    Returns:
        EnrollResponse with enrollment details.

    Raises:
        HTTPException: If enrollment not found.
    """
    enrollment = nurture_agent.get_enrollment(enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrollment {enrollment_id} not found",
        )
    return EnrollResponse(success=True, data=enrollment)


@router.get("/enrollments/lead/{lead_id}", response_model=list[NurtureEnrollment])
async def get_lead_enrollments(
    lead_id: str,
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
) -> list[NurtureEnrollment]:
    """Get all enrollments for a lead.

    Args:
        lead_id: The lead identifier.
        nurture_agent: Nurture agent instance.

    Returns:
        List of NurtureEnrollment objects.
    """
    return nurture_agent.get_lead_enrollments(lead_id)


@router.post("/engagement", response_model=EngagementEventResponse)
async def record_engagement(
    request: EngagementEventRequest,
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
) -> EngagementEventResponse:
    """Record an engagement event for an enrolled lead.

    Args:
        request: Engagement event request.
        nurture_agent: Nurture agent instance.

    Returns:
        EngagementEventResponse confirming the event was recorded.

    Raises:
        HTTPException: If enrollment not found.
    """
    try:
        await nurture_agent.process_engagement(
            enrollment_id=request.enrollment_id,
            event_type=request.event_type,
            metadata=request.metadata,
        )
        return EngagementEventResponse(
            success=True, message="Engagement event recorded"
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record engagement: {str(exc)}",
        ) from exc


@router.post("/advance/{enrollment_id}", response_model=AdvanceStepResponse)
async def advance_step(
    enrollment_id: str,
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
) -> AdvanceStepResponse:
    """Advance an enrollment to the next step.

    Args:
        enrollment_id: The enrollment identifier.
        nurture_agent: Nurture agent instance.

    Returns:
        AdvanceStepResponse with updated enrollment.

    Raises:
        HTTPException: If enrollment not found.
    """
    enrollment = await nurture_agent.advance_step(enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrollment {enrollment_id} not found",
        )
    message = "Step advanced" if enrollment.status == NurtureStatus.ACTIVE else "Sequence completed"
    return AdvanceStepResponse(success=True, data=enrollment, message=message)


@router.post("/evaluate-exit", response_model=ExitEvaluationResponse)
async def evaluate_exit(
    request: ExitEvaluationRequest,
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
) -> ExitEvaluationResponse:
    """Evaluate whether a lead should exit nurture.

    Args:
        request: Exit evaluation request.
        nurture_agent: Nurture agent instance.

    Returns:
        ExitEvaluationResponse with exit decision.

    Raises:
        HTTPException: If enrollment not found.
    """
    try:
        grade = LeadGrade(request.current_grade) if request.current_grade else None
        result = await nurture_agent.evaluate_exit(
            enrollment_id=request.enrollment_id,
            current_score=request.current_score,
            current_grade=grade,
            qualification_status=request.qualification_status,
        )
        return ExitEvaluationResponse(
            success=True,
            should_exit=result.get("should_exit", False),
            reason=result.get("reason", ""),
            destination=result.get("destination"),
            engagement_score=result.get("engagement_score"),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exit evaluation failed: {str(exc)}",
        ) from exc


@router.get("/stats", response_model=NurtureStatsResponse)
async def get_nurture_stats(
    nurture_agent: Annotated[LeadNurtureAgent, Depends(get_nurture_agent)],
) -> NurtureStatsResponse:
    """Get nurture statistics.

    Args:
        nurture_agent: Nurture agent instance.

    Returns:
        NurtureStatsResponse with nurture metrics.
    """
    stats = nurture_agent.get_nurture_stats()
    return NurtureStatsResponse(success=True, stats=stats)

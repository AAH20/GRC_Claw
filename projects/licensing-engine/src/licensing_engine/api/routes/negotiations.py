"""Terms negotiation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from licensing_engine.agents import AgentContext, TermsNegotiatorAgent
from licensing_engine.config.settings import Settings, get_settings
from licensing_engine.models import (
    NegotiationStatus,
    TermsNegotiation,
    TermsNegotiationCreate,
    TermsNegotiationResponse,
    TermsNegotiationUpdate,
)

router = APIRouter()

# In-memory store for demo purposes
_negotiations: dict[UUID, TermsNegotiation] = {}


@router.post(
    "",
    response_model=TermsNegotiationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new negotiation",
)
async def create_negotiation(
    data: TermsNegotiationCreate,
    settings: Settings = Depends(get_settings),
) -> TermsNegotiationResponse:
    """Start a new terms negotiation using the TermsNegotiatorAgent.

    Args:
        data: The negotiation creation data.
        settings: Application settings.

    Returns:
        The created negotiation.
    """
    context = AgentContext(settings=settings)
    agent = TermsNegotiatorAgent(context)
    result = await agent.execute(
        {
            "license_id": str(data.license_id),
            "proposals": [data.initial_proposal.model_dump(mode="json")],
        }
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Failed to start negotiation",
        )

    negotiation = TermsNegotiation(
        license_id=data.license_id,
        proposals=[data.initial_proposal],
        status=NegotiationStatus.INITIATED,
    )
    _negotiations[negotiation.id] = negotiation
    return TermsNegotiationResponse(
        negotiation=negotiation, message="Negotiation started successfully"
    )


@router.get(
    "/{negotiation_id}",
    response_model=TermsNegotiationResponse,
    summary="Get a negotiation by ID",
)
async def get_negotiation(negotiation_id: UUID) -> TermsNegotiationResponse:
    """Get a specific negotiation by its ID.

    Args:
        negotiation_id: The negotiation ID.

    Returns:
        The requested negotiation.

    Raises:
        HTTPException: If the negotiation is not found.
    """
    negotiation = _negotiations.get(negotiation_id)
    if not negotiation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Negotiation {negotiation_id} not found",
        )
    return TermsNegotiationResponse(negotiation=negotiation)


@router.post(
    "/{negotiation_id}/counter",
    response_model=TermsNegotiationResponse,
    summary="Submit a counter proposal",
)
async def submit_counter_proposal(
    negotiation_id: UUID,
    data: TermsNegotiationUpdate,
    settings: Settings = Depends(get_settings),
) -> TermsNegotiationResponse:
    """Submit a counter proposal in a negotiation.

    Args:
        negotiation_id: The negotiation ID.
        data: The counter proposal data.
        settings: Application settings.

    Returns:
        The updated negotiation.

    Raises:
        HTTPException: If the negotiation is not found.
    """
    negotiation = _negotiations.get(negotiation_id)
    if not negotiation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Negotiation {negotiation_id} not found",
        )

    if data.counter_proposal:
        context = AgentContext(settings=settings)
        agent = TermsNegotiatorAgent(context)
        result = await agent.execute(
            {
                "license_id": str(negotiation.license_id),
                "proposals": [p.model_dump(mode="json") for p in negotiation.proposals],
                "counter_proposal": data.counter_proposal.model_dump(mode="json"),
            }
        )
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to process counter proposal",
            )
        negotiation.proposals.append(data.counter_proposal)
        negotiation.status = NegotiationStatus.COUNTERED
        negotiation.current_proposal_index = len(negotiation.proposals) - 1

    return TermsNegotiationResponse(
        negotiation=negotiation, message="Counter proposal submitted"
    )


@router.post(
    "/{negotiation_id}/accept",
    response_model=TermsNegotiationResponse,
    summary="Accept current proposal",
)
async def accept_proposal(negotiation_id: UUID) -> TermsNegotiationResponse:
    """Accept the current proposal in a negotiation.

    Args:
        negotiation_id: The negotiation ID.

    Returns:
        The updated negotiation.

    Raises:
        HTTPException: If the negotiation is not found.
    """
    negotiation = _negotiations.get(negotiation_id)
    if not negotiation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Negotiation {negotiation_id} not found",
        )
    negotiation.status = NegotiationStatus.ACCEPTED
    return TermsNegotiationResponse(
        negotiation=negotiation, message="Proposal accepted"
    )


@router.post(
    "/{negotiation_id}/reject",
    response_model=TermsNegotiationResponse,
    summary="Reject current proposal",
)
async def reject_proposal(negotiation_id: UUID) -> TermsNegotiationResponse:
    """Reject the current proposal in a negotiation.

    Args:
        negotiation_id: The negotiation ID.

    Returns:
        The updated negotiation.

    Raises:
        HTTPException: If the negotiation is not found.
    """
    negotiation = _negotiations.get(negotiation_id)
    if not negotiation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Negotiation {negotiation_id} not found",
        )
    negotiation.status = NegotiationStatus.REJECTED
    return TermsNegotiationResponse(
        negotiation=negotiation, message="Proposal rejected"
    )

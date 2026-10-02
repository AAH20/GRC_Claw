"""API routes for ticket management."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from customer_service.agents import EscalationAgent, ResolutionAgent, TriageAgent

logger = structlog.get_logger(__name__)

router = APIRouter()


class TicketCreateRequest(BaseModel):
    """Request model for creating a ticket."""

    customer_id: str = Field(..., description="Customer identifier")
    subject: str = Field(..., description="Ticket subject")
    content: str = Field(..., description="Ticket content")
    channel: str = Field(default="email", description="Communication channel")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TicketResponse(BaseModel):
    """Response model for ticket operations."""

    ticket_id: str = Field(..., description="Ticket identifier")
    status: str = Field(..., description="Ticket status")
    message: str = Field(..., description="Response message")


class TriageResponse(BaseModel):
    """Response model for triage results."""

    category: str = Field(..., description="Ticket category")
    priority: str = Field(..., description="Priority level")
    confidence: float = Field(..., description="Classification confidence")
    intent: str = Field(..., description="Detected intent")
    summary: str = Field(..., description="Ticket summary")
    suggested_team: str = Field(..., description="Suggested team")


class ResolutionResponse(BaseModel):
    """Response model for resolution results."""

    suggestion: str = Field(..., description="Resolution suggestion")
    confidence: float = Field(..., description="Confidence score")
    auto_reply: str | None = Field(None, description="Suggested auto-reply")
    escalation_recommended: bool = Field(..., description="Whether escalation is recommended")


class EscalationResponse(BaseModel):
    """Response model for escalation results."""

    should_escalate: bool = Field(..., description="Whether to escalate")
    reason: str = Field(..., description="Escalation reason")
    urgency: str = Field(..., description="Urgency level")
    assigned_team: str = Field(..., description="Assigned team")
    context_summary: str = Field(..., description="Context summary")


# In-memory ticket store (replace with database in production)
_tickets: dict[str, dict[str, Any]] = {}


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(request: TicketCreateRequest) -> TicketResponse:
    """Create a new customer ticket.

    Args:
        request: Ticket creation request.

    Returns:
        Created ticket response.
    """
    import uuid

    ticket_id = str(uuid.uuid4())
    _tickets[ticket_id] = {
        "ticket_id": ticket_id,
        "customer_id": request.customer_id,
        "subject": request.subject,
        "content": request.content,
        "channel": request.channel,
        "status": "open",
        "metadata": request.metadata,
    }

    logger.info("Ticket created", ticket_id=ticket_id, customer_id=request.customer_id)
    return TicketResponse(
        ticket_id=ticket_id,
        status="open",
        message="Ticket created successfully",
    )


@router.get("/{ticket_id}", response_model=dict[str, Any])
async def get_ticket(ticket_id: str) -> dict[str, Any]:
    """Get ticket details by ID.

    Args:
        ticket_id: The ticket identifier.

    Returns:
        Ticket details.

    Raises:
        HTTPException: If ticket is not found.
    """
    ticket = _tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    return ticket


@router.post("/{ticket_id}/triage", response_model=TriageResponse)
async def run_triage(ticket_id: str) -> TriageResponse:
    """Run triage classification on a ticket.

    Args:
        ticket_id: The ticket identifier.

    Returns:
        Triage classification result.

    Raises:
        HTTPException: If ticket is not found or triage fails.
    """
    ticket = _tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )

    try:
        agent = TriageAgent()
        result = await agent.run(
            ticket_content=ticket["content"],
            customer_context={"customer_id": ticket["customer_id"]},
        )
        return TriageResponse(
            category=result.category,
            priority=result.priority,
            confidence=result.confidence,
            intent=result.intent,
            summary=result.summary,
            suggested_team=result.suggested_team,
        )
    except Exception as e:
        logger.error("Triage failed", ticket_id=ticket_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Triage failed: {e}",
        ) from e


@router.post("/{ticket_id}/resolve", response_model=ResolutionResponse)
async def run_resolution(ticket_id: str) -> ResolutionResponse:
    """Generate resolution suggestion for a ticket.

    Args:
        ticket_id: The ticket identifier.

    Returns:
        Resolution suggestion result.

    Raises:
        HTTPException: If ticket is not found or resolution fails.
    """
    ticket = _tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )

    try:
        agent = ResolutionAgent()
        result = await agent.run(
            ticket_content=ticket["content"],
            customer_context={"customer_id": ticket["customer_id"]},
        )
        return ResolutionResponse(
            suggestion=result.suggestion,
            confidence=result.confidence,
            auto_reply=result.auto_reply,
            escalation_recommended=result.escalation_recommended,
        )
    except Exception as e:
        logger.error("Resolution failed", ticket_id=ticket_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resolution failed: {e}",
        ) from e


@router.post("/{ticket_id}/escalate", response_model=EscalationResponse)
async def run_escalation(ticket_id: str) -> EscalationResponse:
    """Evaluate and process ticket escalation.

    Args:
        ticket_id: The ticket identifier.

    Returns:
        Escalation evaluation result.

    Raises:
        HTTPException: If ticket is not found or escalation fails.
    """
    ticket = _tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )

    try:
        agent = EscalationAgent()
        result = await agent.run(
            ticket_content=ticket["content"],
            customer_context={"customer_id": ticket["customer_id"]},
        )
        return EscalationResponse(
            should_escalate=result.should_escalate,
            reason=result.reason,
            urgency=result.urgency,
            assigned_team=result.assigned_team,
            context_summary=result.context_summary,
        )
    except Exception as e:
        logger.error("Escalation failed", ticket_id=ticket_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Escalation failed: {e}",
        ) from e

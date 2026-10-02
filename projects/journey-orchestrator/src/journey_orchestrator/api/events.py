"""Events API routes."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)
router = APIRouter()

# In-memory event store (replace with database in production)
_events: list[dict] = []


class EventIngestRequest(BaseModel):
    """Request to ingest a customer event."""

    customer_id: str = Field(..., description="The customer ID")
    event_type: str = Field(..., description="Type of event")
    properties: dict = Field(default_factory=dict, description="Event properties")
    timestamp: datetime | None = Field(default=None, description="Event timestamp")


class EventIngestResponse(BaseModel):
    """Response after ingesting an event."""

    event_id: str
    status: str
    message: str


@router.post("", response_model=EventIngestResponse, status_code=201)
async def ingest_event(request: EventIngestRequest) -> EventIngestResponse:
    """Ingest a customer event.

    Args:
        request: The event ingestion request.

    Returns:
        The ingestion response.

    Raises:
        HTTPException: If event ingestion fails.
    """
    if not request.customer_id.strip():
        raise HTTPException(status_code=400, detail="customer_id must not be empty")
    if not request.event_type.strip():
        raise HTTPException(status_code=400, detail="event_type must not be empty")

    event = {
        "id": str(uuid4()),
        "customer_id": request.customer_id,
        "event_type": request.event_type,
        "properties": request.properties,
        "timestamp": request.timestamp or datetime.now(UTC),
    }

    _events.append(event)
    logger.info("Event ingested", event_id=event["id"], customer_id=request.customer_id)

    return EventIngestResponse(
        event_id=event["id"],
        status="accepted",
        message="Event ingested successfully",
    )


@router.get("/{customer_id}")
async def get_customer_events(customer_id: str) -> list[dict]:
    """Get events for a customer.

    Args:
        customer_id: The customer ID.

    Returns:
        List of events for the customer.
    """
    return [e for e in _events if e["customer_id"] == customer_id]

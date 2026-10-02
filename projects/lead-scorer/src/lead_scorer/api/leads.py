"""API routes for lead management endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])


class LeadCreateRequest(BaseModel):
    """Request model for creating a lead."""

    email: str = Field(..., min_length=3, description="Lead email address")
    first_name: str = Field(default="", description="First name")
    last_name: str = Field(default="", description="Last name")
    company: str = Field(default="", description="Company name")
    domain: str = Field(default="", description="Company domain")
    phone: str = Field(default="", description="Phone number")
    source: str = Field(default="api", description="Lead source")
    metadata: dict[str, Any] = Field(default_factory=dict)


class LeadResponse(BaseModel):
    """Response model for a lead."""

    id: str
    email: str
    first_name: str
    last_name: str
    company: str
    domain: str
    phone: str
    source: str
    created_at: str
    metadata: dict[str, Any]


class LeadDetailResponse(BaseModel):
    """Response model for lead detail."""

    success: bool
    data: LeadResponse


# In-memory store for demo purposes
_leads: dict[str, dict[str, Any]] = {}


@router.post("", response_model=LeadDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(request: LeadCreateRequest) -> LeadDetailResponse:
    """Create a new lead.

    Args:
        request: Lead creation request.

    Returns:
        LeadDetailResponse with created lead data.

    Raises:
        HTTPException: If lead creation fails.
    """
    lead_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    lead_data = {
        "id": lead_id,
        "email": request.email,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "company": request.company,
        "domain": request.domain,
        "phone": request.phone,
        "source": request.source,
        "created_at": now,
        "metadata": request.metadata,
    }

    _leads[lead_id] = lead_data

    return LeadDetailResponse(success=True, data=LeadResponse(**lead_data))


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead(lead_id: str) -> LeadDetailResponse:
    """Get a lead by ID.

    Args:
        lead_id: Unique lead identifier.

    Returns:
        LeadDetailResponse with lead data.

    Raises:
        HTTPException: If lead not found.
    """
    if lead_id not in _leads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} not found",
        )

    return LeadDetailResponse(success=True, data=LeadResponse(**_leads[lead_id]))


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(lead_id: str) -> None:
    """Delete a lead by ID.

    Args:
        lead_id: Unique lead identifier.

    Raises:
        HTTPException: If lead not found.
    """
    if lead_id not in _leads:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} not found",
        )

    del _leads[lead_id]

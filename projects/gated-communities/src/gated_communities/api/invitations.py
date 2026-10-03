"""
Invitations API endpoints for gated communities.

Provides endpoints to list and create community invitations.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/invitations", tags=["invitations"])


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class InvitationCreate(BaseModel):
    """Schema for creating a new invitation."""

    community_id: str = Field(..., description="ID of the community to invite to")
    email: EmailStr = Field(..., description="Email address of the invitee")
    role: str = Field(default="member", description="Role to assign upon acceptance")
    message: Optional[str] = Field(
        default=None, max_length=500, description="Optional personal message"
    )
    expires_in_days: int = Field(
        default=7, ge=1, le=90, description="Days until invitation expires"
    )


class InvitationResponse(BaseModel):
    """Schema for invitation response."""

    id: str
    community_id: str
    community_name: str
    email: str
    role: str
    status: str
    message: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    invited_by: str


class InvitationListResponse(BaseModel):
    """Schema for paginated invitation list."""

    items: list[InvitationResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Mock Data Store (replace with real DB in production)
# ---------------------------------------------------------------------------

MOCK_COMMUNITIES = {
    "comm-001": {"name": "Engineering Guild", "owner": "user-101"},
    "comm-002": {"name": "Design Circle", "owner": "user-102"},
    "comm-003": {"name": "Product Leaders", "owner": "user-103"},
    "comm-004": {"name": "Data Science Hub", "owner": "user-104"},
    "comm-005": {"name": "Marketing Collective", "owner": "user-105"},
}

MOCK_INVITATIONS = [
    {
        "id": f"inv-{i:04d}",
        "community_id": comm_id,
        "community_name": MOCK_COMMUNITIES[comm_id]["name"],
        "email": f"user{i}@example.com",
        "role": role,
        "status": status_val,
        "message": msg,
        "created_at": datetime(2026, 9, 20 + (i % 10), 10, 30, 0),
        "expires_at": datetime(2026, 9, 20 + (i % 10), 10, 30, 0) + timedelta(days=7),
        "invited_by": MOCK_COMMUNITIES[comm_id]["owner"],
    }
    for i, (comm_id, role, status_val, msg) in enumerate([
        ("comm-001", "member", "pending", "Join our engineering community!"),
        ("comm-001", "moderator", "accepted", None),
        ("comm-002", "member", "pending", "We'd love your design expertise."),
        ("comm-002", "member", "expired", None),
        ("comm-003", "admin", "pending", "Leadership team invitation."),
        ("comm-003", "member", "revoked", None),
        ("comm-004", "member", "accepted", "Data team onboarding."),
        ("comm-004", "moderator", "pending", None),
        ("comm-005", "member", "pending", "Marketing sync invite."),
        ("comm-005", "member", "declined", None),
        ("comm-001", "member", "pending", "Second invite to engineering."),
        ("comm-002", "member", "accepted", "Welcome to the circle!"),
    ], start=1)
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=InvitationListResponse)
async def list_invitations(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="Filter by invitation status",
        pattern="^(pending|accepted|declined|expired|revoked)$",
    ),
    community_id: Optional[str] = Query(
        default=None, description="Filter by community ID"
    ),
) -> dict:
    """
    List invitations with pagination and optional filtering.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status_filter: Optional status to filter by.
        community_id: Optional community ID to filter by.

    Returns:
        Paginated list of invitations.
    """
    filtered = MOCK_INVITATIONS.copy()

    if status_filter:
        filtered = [inv for inv in filtered if inv["status"] == status_filter]

    if community_id:
        filtered = [inv for inv in filtered if inv["community_id"] == community_id]

    total = len(filtered)
    pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(payload: InvitationCreate) -> dict:
    """
    Create a new invitation.

    Args:
        payload: Invitation creation data.

    Returns:
        The newly created invitation.

    Raises:
        HTTPException: If the community does not exist.
    """
    if payload.community_id not in MOCK_COMMUNITIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Community '{payload.community_id}' not found",
        )

    community = MOCK_COMMUNITIES[payload.community_id]
    now = datetime.utcnow()

    invitation = {
        "id": f"inv-{uuid4().hex[:8]}",
        "community_id": payload.community_id,
        "community_name": community["name"],
        "email": payload.email,
        "role": payload.role,
        "status": "pending",
        "message": payload.message,
        "created_at": now,
        "expires_at": now + timedelta(days=payload.expires_in_days),
        "invited_by": community["owner"],
    }

    MOCK_INVITATIONS.append(invitation)

    return invitation

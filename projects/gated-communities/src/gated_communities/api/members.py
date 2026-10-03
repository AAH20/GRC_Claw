"""Member management routes for gated communities."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class MemberCreate(BaseModel):
    email: EmailStr
    name: str
    role: str = "member"
    community_id: str


class MemberResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str
    community_id: str
    joined_at: datetime
    is_active: bool


class MemberListResponse(BaseModel):
    members: List[MemberResponse]
    total: int
    page: int
    per_page: int


# Mock data store
MOCK_MEMBERS = [
    MemberResponse(
        id="mem_001",
        email="alice@example.com",
        name="Alice Johnson",
        role="admin",
        community_id="comm_001",
        joined_at=datetime(2024, 1, 15, 10, 30),
        is_active=True,
    ),
    MemberResponse(
        id="mem_002",
        email="bob@example.com",
        name="Bob Smith",
        role="member",
        community_id="comm_001",
        joined_at=datetime(2024, 2, 20, 14, 0),
        is_active=True,
    ),
    MemberResponse(
        id="mem_003",
        email="carol@example.com",
        name="Carol Davis",
        role="moderator",
        community_id="comm_002",
        joined_at=datetime(2024, 3, 10, 9, 15),
        is_active=False,
    ),
]


@router.get("/members", response_model=MemberListResponse)
async def list_members(
    community_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List members, optionally filtered by community."""
    filtered = MOCK_MEMBERS
    if community_id:
        filtered = [m for m in filtered if m.community_id == community_id]

    start = (page - 1) * per_page
    end = start + per_page
    paginated = filtered[start:end]

    return MemberListResponse(
        members=paginated,
        total=len(filtered),
        page=page,
        per_page=per_page,
    )


@router.post("/members", response_model=MemberResponse, status_code=201)
async def create_member(payload: MemberCreate):
    """Add a new member to a community."""
    new_member = MemberResponse(
        id=f"mem_{len(MOCK_MEMBERS) + 1:03d}",
        email=payload.email,
        name=payload.name,
        role=payload.role,
        community_id=payload.community_id,
        joined_at=datetime.utcnow(),
        is_active=True,
    )
    return new_member


@router.get("/members/{member_id}", response_model=MemberResponse)
async def get_member(member_id: str):
    """Retrieve a specific member by ID."""
    for member in MOCK_MEMBERS:
        if member.id == member_id:
            return member
    raise HTTPException(status_code=404, detail=f"Member {member_id} not found")

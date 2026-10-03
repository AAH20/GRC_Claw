"""Community management routes."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class CommunityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    is_private: bool = True
    tier_id: Optional[str] = None
    max_members: int = Field(default=100, ge=1, le=10000)


class CommunityResponse(BaseModel):
    id: str
    name: str
    description: str
    is_private: bool
    tier_id: Optional[str]
    max_members: int
    member_count: int
    created_at: datetime
    updated_at: datetime


class CommunityListResponse(BaseModel):
    communities: List[CommunityResponse]
    total: int


MOCK_COMMUNITIES = [
    CommunityResponse(
        id="comm_001",
        name="Alpha Testers",
        description="Exclusive community for alpha testers",
        is_private=True,
        tier_id="tier_alpha",
        max_members=50,
        member_count=23,
        created_at=datetime(2024, 1, 1, 8, 0),
        updated_at=datetime(2024, 6, 15, 12, 30),
    ),
    CommunityResponse(
        id="comm_002",
        name="Beta Access",
        description="Beta program participants",
        is_private=True,
        tier_id="tier_beta",
        max_members=200,
        member_count=145,
        created_at=datetime(2024, 2, 1, 10, 0),
        updated_at=datetime(2024, 7, 20, 16, 45),
    ),
    CommunityResponse(
        id="comm_003",
        name="Public Forum",
        description="Open discussion for all users",
        is_private=False,
        tier_id=None,
        max_members=1000,
        member_count=567,
        created_at=datetime(2024, 3, 1, 9, 0),
        updated_at=datetime(2024, 8, 1, 11, 0),
    ),
]


@router.get("/communities", response_model=CommunityListResponse)
async def list_communities(
    include_private: bool = Query(False),
    tier_id: Optional[str] = Query(None),
):
    """List all communities with optional filtering."""
    results = MOCK_COMMUNITIES

    if not include_private:
        results = [c for c in results if not c.is_private]

    if tier_id:
        results = [c for c in results if c.tier_id == tier_id]

    return CommunityListResponse(
        communities=results,
        total=len(results),
    )


@router.post("/communities", response_model=CommunityResponse, status_code=201)
async def create_community(payload: CommunityCreate):
    """Create a new gated community."""
    now = datetime.utcnow()
    new_community = CommunityResponse(
        id=f"comm_{len(MOCK_COMMUNITIES) + 1:03d}",
        name=payload.name,
        description=payload.description,
        is_private=payload.is_private,
        tier_id=payload.tier_id,
        max_members=payload.max_members,
        member_count=0,
        created_at=now,
        updated_at=now,
    )
    return new_community

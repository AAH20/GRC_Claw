"""Member management routes for gated communities."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import datetime, timezone

router = APIRouter()


class MemberCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=120)
    role: Literal["member", "moderator", "admin"] = "member"
    community_id: str = Field(..., min_length=1)
    tier: Literal["free", "basic", "premium", "enterprise"] = "free"
    status: Literal["active", "inactive", "suspended", "pending"] = "pending"
    metadata: Optional[dict] = None


class MemberResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str
    community_id: str
    tier: str
    status: str
    joined_at: datetime
    updated_at: datetime
    is_active: bool
    metadata: Optional[dict] = None


class MemberListResponse(BaseModel):
    members: List[MemberResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# Mock data store
MOCK_MEMBERS = [
    MemberResponse(
        id="mem_001",
        email="alice@example.com",
        name="Alice Johnson",
        role="admin",
        community_id="comm_001",
        tier="premium",
        status="active",
        joined_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
        updated_at=datetime(2025, 6, 20, 14, 22, tzinfo=timezone.utc),
        is_active=True,
        metadata={"department": "Engineering", "team": "Platform"},
    ),
    MemberResponse(
        id="mem_002",
        email="bob@example.com",
        name="Bob Smith",
        role="member",
        community_id="comm_001",
        tier="basic",
        status="active",
        joined_at=datetime(2024, 2, 20, 14, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 5, 18, 9, 45, tzinfo=timezone.utc),
        is_active=True,
        metadata={"department": "Design", "team": "UX"},
    ),
    MemberResponse(
        id="mem_003",
        email="carol@example.com",
        name="Carol Davis",
        role="moderator",
        community_id="comm_002",
        tier="free",
        status="pending",
        joined_at=datetime(2024, 3, 10, 9, 15, tzinfo=timezone.utc),
        updated_at=datetime(2024, 3, 10, 9, 15, tzinfo=timezone.utc),
        is_active=False,
        metadata=None,
    ),
    MemberResponse(
        id="mem_004",
        email="dave@example.com",
        name="Dave Brown",
        role="admin",
        community_id="comm_002",
        tier="enterprise",
        status="active",
        joined_at=datetime(2024, 11, 20, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 7, 1, 11, 30, tzinfo=timezone.utc),
        is_active=True,
        metadata={"department": "Sales", "team": "Enterprise", "seats": 50},
    ),
    MemberResponse(
        id="mem_005",
        email="eve@example.com",
        name="Eve Wilson",
        role="member",
        community_id="comm_001",
        tier="premium",
        status="suspended",
        joined_at=datetime(2025, 4, 12, 9, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 6, 15, 17, 0, tzinfo=timezone.utc),
        is_active=False,
        metadata={"department": "Marketing", "team": "Growth"},
    ),
    MemberResponse(
        id="mem_006",
        email="frank@example.com",
        name="Frank Miller",
        role="member",
        community_id="comm_003",
        tier="basic",
        status="inactive",
        joined_at=datetime(2025, 1, 28, 14, 30, tzinfo=timezone.utc),
        updated_at=datetime(2025, 4, 10, 10, 0, tzinfo=timezone.utc),
        is_active=False,
        metadata=None,
    ),
    MemberResponse(
        id="mem_007",
        email="grace@example.com",
        name="Grace Lee",
        role="member",
        community_id="comm_001",
        tier="premium",
        status="active",
        joined_at=datetime(2025, 5, 1, 11, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 7, 10, 15, 30, tzinfo=timezone.utc),
        is_active=True,
        metadata={"department": "Engineering", "team": "Frontend"},
    ),
    MemberResponse(
        id="mem_008",
        email="henry@example.com",
        name="Henry Taylor",
        role="member",
        community_id="comm_003",
        tier="free",
        status="active",
        joined_at=datetime(2025, 6, 15, 8, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 6, 15, 8, 0, tzinfo=timezone.utc),
        is_active=True,
        metadata=None,
    ),
    MemberResponse(
        id="mem_009",
        email="iris@example.com",
        name="Iris Chen",
        role="moderator",
        community_id="comm_002",
        tier="enterprise",
        status="active",
        joined_at=datetime(2024, 12, 1, 10, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 8, 1, 9, 0, tzinfo=timezone.utc),
        is_active=True,
        metadata={"department": "Support", "team": "Customer Success"},
    ),
    MemberResponse(
        id="mem_010",
        email="jack@example.com",
        name="Jack Anderson",
        role="member",
        community_id="comm_003",
        tier="basic",
        status="pending",
        joined_at=datetime(2025, 7, 20, 13, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 7, 20, 13, 0, tzinfo=timezone.utc),
        is_active=False,
        metadata=None,
    ),
    MemberResponse(
        id="mem_011",
        email="karen@example.com",
        name="Karen Martinez",
        role="member",
        community_id="comm_001",
        tier="premium",
        status="active",
        joined_at=datetime(2025, 3, 18, 10, 0, tzinfo=timezone.utc),
        updated_at=datetime(2025, 6, 25, 12, 0, tzinfo=timezone.utc),
        is_active=True,
        metadata={"department": "Product", "team": "Core"},
    ),
    MemberResponse(
        id="mem_012",
        email="leo@example.com",
        name="Leo Thomas",
        role="member",
        community_id="comm_003",
        tier="free",
        status="inactive",
        joined_at=datetime(2025, 2, 22, 9, 30, tzinfo=timezone.utc),
        updated_at=datetime(2025, 5, 1, 8, 0, tzinfo=timezone.utc),
        is_active=False,
        metadata=None,
    ),
]


@router.get("/members", response_model=MemberListResponse)
async def list_members(
    community_id: Optional[str] = Query(None),
    tier: Optional[Literal["free", "basic", "premium", "enterprise"]] = Query(None),
    status: Optional[Literal["active", "inactive", "suspended", "pending"]] = Query(None),
    role: Optional[Literal["member", "moderator", "admin"]] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """List members with pagination and filtering by community, tier, status, or role."""
    filtered = MOCK_MEMBERS
    if community_id:
        filtered = [m for m in filtered if m.community_id == community_id]
    if tier:
        filtered = [m for m in filtered if m.tier == tier]
    if status:
        filtered = [m for m in filtered if m.status == status]
    if role:
        filtered = [m for m in filtered if m.role == role]

    total = len(filtered)
    total_pages = max(1, (total + per_page - 1) // per_page)

    if page > total_pages and total > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Page {page} exceeds total pages ({total_pages})",
        )

    start = (page - 1) * per_page
    end = start + per_page
    paginated = filtered[start:end]

    return MemberListResponse(
        members=paginated,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.post("/members", response_model=MemberResponse, status_code=201)
async def create_member(payload: MemberCreate):
    """Add a new member to a community with validation."""
    # Check for duplicate email
    existing = [m for m in MOCK_MEMBERS if m.email == payload.email]
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Member with email '{payload.email}' already exists",
        )

    now = datetime.now(timezone.utc)
    new_member = MemberResponse(
        id=f"mem_{len(MOCK_MEMBERS) + 1:03d}",
        email=payload.email,
        name=payload.name,
        role=payload.role,
        community_id=payload.community_id,
        tier=payload.tier,
        status=payload.status,
        joined_at=now,
        updated_at=now,
        is_active=payload.status == "active",
        metadata=payload.metadata,
    )
    return new_member


@router.get("/members/{member_id}", response_model=MemberResponse)
async def get_member(member_id: str):
    """Retrieve a specific member by ID."""
    for member in MOCK_MEMBERS:
        if member.id == member_id:
            return member
    raise HTTPException(status_code=404, detail=f"Member {member_id} not found")

"""
Creators API endpoints for UGC Marketplace.

Provides listing with pagination/filtering and creation with validation.
"""

from datetime import datetime, timezone
from typing import Literal, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field, field_validator

router = APIRouter(prefix="/creators", tags=["creators"])

# ---------------------------------------------------------------------------
# Mock data store
# ---------------------------------------------------------------------------

MOCK_CREATORS = [
    {
        "id": "cr_001",
        "name": "Aisha Rahman",
        "email": "aisha.rahman@example.com",
        "handle": "@aishacreates",
        "tier": "gold",
        "status": "active",
        "bio": "Lifestyle & travel content creator based in Dubai.",
        "followers": 125000,
        "engagement_rate": 4.2,
        "categories": ["lifestyle", "travel", "food"],
        "joined_at": "2024-03-15T09:30:00Z",
        "verified": True,
    },
    {
        "id": "cr_002",
        "name": "Marcus Chen",
        "email": "marcus.chen@example.com",
        "handle": "@marcustech",
        "tier": "platinum",
        "status": "active",
        "bio": "Tech reviewer and gadget enthusiast. 500K+ community.",
        "followers": 512000,
        "engagement_rate": 6.8,
        "categories": ["tech", "gadgets", "reviews"],
        "joined_at": "2023-11-02T14:00:00Z",
        "verified": True,
    },
    {
        "id": "cr_003",
        "name": "Sofia Almeida",
        "email": "sofia.almeida@example.com",
        "handle": "@sofiafit",
        "tier": "silver",
        "status": "active",
        "bio": "Fitness coach sharing workouts and nutrition tips.",
        "followers": 45000,
        "engagement_rate": 3.5,
        "categories": ["fitness", "health", "wellness"],
        "joined_at": "2024-06-20T11:15:00Z",
        "verified": False,
    },
    {
        "id": "cr_004",
        "name": "James Okafor",
        "email": "james.okafor@example.com",
        "handle": "@jamescooks",
        "tier": "gold",
        "status": "active",
        "bio": "Chef and food content creator. Recipes from around the world.",
        "followers": 89000,
        "engagement_rate": 5.1,
        "categories": ["food", "cooking", "travel"],
        "joined_at": "2024-01-10T08:45:00Z",
        "verified": True,
    },
    {
        "id": "cr_005",
        "name": "Elena Petrova",
        "email": "elena.petrova@example.com",
        "handle": "@elenastyle",
        "tier": "bronze",
        "status": "pending",
        "bio": "Fashion blogger exploring sustainable style.",
        "followers": 12000,
        "engagement_rate": 2.8,
        "categories": ["fashion", "sustainability"],
        "joined_at": "2025-01-05T16:20:00Z",
        "verified": False,
    },
    {
        "id": "cr_006",
        "name": "David Kim",
        "email": "david.kim@example.com",
        "handle": "@davidgames",
        "tier": "platinum",
        "status": "active",
        "bio": "Gaming streamer and esports commentator.",
        "followers": 780000,
        "engagement_rate": 7.3,
        "categories": ["gaming", "esports", "entertainment"],
        "joined_at": "2023-08-18T20:00:00Z",
        "verified": True,
    },
    {
        "id": "cr_007",
        "name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "handle": "@priyadiys",
        "tier": "silver",
        "status": "active",
        "bio": "DIY crafts and home decor content creator.",
        "followers": 34000,
        "engagement_rate": 3.9,
        "categories": ["diy", "crafts", "home"],
        "joined_at": "2024-09-12T10:30:00Z",
        "verified": False,
    },
    {
        "id": "cr_008",
        "name": "Tom Mueller",
        "email": "tom.mueller@example.com",
        "handle": "@tomauto",
        "tier": "gold",
        "status": "suspended",
        "bio": "Automotive content creator and car reviewer.",
        "followers": 210000,
        "engagement_rate": 4.7,
        "categories": ["automotive", "reviews", "tech"],
        "joined_at": "2023-05-22T13:00:00Z",
        "verified": True,
    },
    {
        "id": "cr_009",
        "name": "Layla Hassan",
        "email": "layla.hassan@example.com",
        "handle": "@laylamua",
        "tier": "silver",
        "status": "active",
        "bio": "Makeup artist and beauty content creator.",
        "followers": 67000,
        "engagement_rate": 4.0,
        "categories": ["beauty", "makeup", "lifestyle"],
        "joined_at": "2024-04-08T12:00:00Z",
        "verified": True,
    },
    {
        "id": "cr_010",
        "name": "Ryan O'Brien",
        "email": "ryan.obrien@example.com",
        "handle": "@ryanoutdoors",
        "tier": "bronze",
        "status": "pending",
        "bio": "Outdoor adventure and hiking content creator.",
        "followers": 8500,
        "engagement_rate": 2.1,
        "categories": ["outdoors", "adventure", "travel"],
        "joined_at": "2025-02-14T09:00:00Z",
        "verified": False,
    },
    {
        "id": "cr_011",
        "name": "Nina Kowalski",
        "email": "nina.kowalski@example.com",
        "handle": "@ninaphoto",
        "tier": "gold",
        "status": "active",
        "bio": "Photographer sharing street and portrait photography.",
        "followers": 156000,
        "engagement_rate": 5.5,
        "categories": ["photography", "art", "travel"],
        "joined_at": "2023-12-01T15:30:00Z",
        "verified": True,
    },
    {
        "id": "cr_012",
        "name": "Carlos Rivera",
        "email": "carlos.rivera@example.com",
        "handle": "@carlosdance",
        "tier": "silver",
        "status": "active",
        "bio": "Dance choreographer and movement artist.",
        "followers": 52000,
        "engagement_rate": 4.4,
        "categories": ["dance", "entertainment", "fitness"],
        "joined_at": "2024-07-19T18:45:00Z",
        "verified": False,
    },
]

# In-memory store (replace with database in production)
_creators_db = {c["id"]: c for c in MOCK_CREATORS}
_next_id = 100


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

CreatorTier = Literal["bronze", "silver", "gold", "platinum"]
CreatorStatus = Literal["active", "pending", "suspended", "inactive"]


class CreatorCreate(BaseModel):
    """Payload for creating a new creator."""

    name: str = Field(..., min_length=2, max_length=100, description="Creator's full name")
    email: EmailStr = Field(..., description="Creator's email address")
    handle: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern=r"^@[a-zA-Z0-9_]+$",
        description="Unique handle starting with @",
    )
    tier: CreatorTier = Field(default="bronze", description="Creator tier level")
    bio: Optional[str] = Field(default=None, max_length=500, description="Short bio")
    categories: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Content categories (max 5)",
    )

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[str]) -> list[str]:
        if len(v) != len(set(v)):
            raise ValueError("Categories must be unique")
        return v


class CreatorResponse(BaseModel):
    """Creator representation returned by the API."""

    id: str
    name: str
    email: str
    handle: str
    tier: CreatorTier
    status: CreatorStatus
    bio: Optional[str] = None
    followers: int = 0
    engagement_rate: float = 0.0
    categories: list[str] = Field(default_factory=list)
    joined_at: str
    verified: bool = False


class CreatorListResponse(BaseModel):
    """Paginated list of creators."""

    data: list[CreatorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=CreatorListResponse,
    summary="List creators with pagination and filtering",
)
async def list_creators(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    tier: Optional[CreatorTier] = Query(default=None, description="Filter by tier"),
    status: Optional[CreatorStatus] = Query(default=None, description="Filter by status"),
    search: Optional[str] = Query(default=None, min_length=1, description="Search by name or handle"),
) -> dict:
    """
    Return a paginated list of creators.

    Supports filtering by tier, status, and a free-text search on name/handle.
    """
    filtered = list(_creators_db.values())

    if tier is not None:
        filtered = [c for c in filtered if c["tier"] == tier]

    if status is not None:
        filtered = [c for c in filtered if c["status"] == status]

    if search:
        q = search.lower()
        filtered = [
            c
            for c in filtered
            if q in c["name"].lower() or q in c["handle"].lower()
        ]

    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    return {
        "data": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post(
    "",
    response_model=CreatorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new creator",
)
async def create_creator(payload: CreatorCreate) -> dict:
    """
    Create a new creator with validation.

    Returns the newly created creator with a generated ID and default status 'pending'.
    """
    global _next_id

    # Check for duplicate email
    for existing in _creators_db.values():
        if existing["email"] == payload.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A creator with email '{payload.email}' already exists.",
            )

    # Check for duplicate handle
    for existing in _creators_db.values():
        if existing["handle"].lower() == payload.handle.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A creator with handle '{payload.handle}' already exists.",
            )

    _next_id += 1
    new_id = f"cr_{_next_id:03d}"

    new_creator = {
        "id": new_id,
        "name": payload.name,
        "email": payload.email,
        "handle": payload.handle,
        "tier": payload.tier,
        "status": "pending",
        "bio": payload.bio,
        "followers": 0,
        "engagement_rate": 0.0,
        "categories": payload.categories,
        "joined_at": datetime.now(timezone.utc).isoformat(),
        "verified": False,
    }

    _creators_db[new_id] = new_creator

    return new_creator

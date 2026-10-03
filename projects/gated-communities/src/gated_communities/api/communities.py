"""
Communities API endpoints for gated-communities.

Provides:
  GET  /communities  — list communities with pagination and filtering
  POST /communities  — create a new community with validation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/communities", tags=["communities"])


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    SECRET = "secret"


class CommunityCategory(str, Enum):
    TECHNOLOGY = "technology"
    GAMING = "gaming"
    ART = "art"
    MUSIC = "music"
    SPORTS = "sports"
    EDUCATION = "education"
    LIFESTYLE = "lifestyle"
    BUSINESS = "business"
    SCIENCE = "science"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class CommunityBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    description: str = Field(..., min_length=10, max_length=500)
    category: CommunityCategory
    privacy: PrivacyLevel = PrivacyLevel.PUBLIC
    tags: List[str] = Field(default_factory=list, max_length=10)
    rules: List[str] = Field(default_factory=list, max_length=20)
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None


class CommunityCreate(CommunityBase):
    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Community name cannot be empty or whitespace")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def tags_must_be_lowercase(cls, v: List[str]) -> List[str]:
        return [tag.lower().strip() for tag in v if tag.strip()]


class CommunityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=80)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    category: Optional[CommunityCategory] = None
    privacy: Optional[PrivacyLevel] = None
    tags: Optional[List[str]] = None
    rules: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None


class CommunityResponse(CommunityBase):
    id: str
    slug: str
    member_count: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    owner_id: str

    class Config:
        from_attributes = True


class CommunityListResponse(BaseModel):
    data: List[CommunityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Mock data store (in-memory for demonstration)
# ---------------------------------------------------------------------------

def _generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a community name."""
    return (
        name.lower()
        .replace(" ", "-")
        .replace("_", "-")
        .replace(".", "")
        .replace(",", "")
        .replace("'", "")
        .replace('"', "")
        .replace("!", "")
        .replace("?", "")
        .replace("&", "and")
    )


MOCK_COMMUNITIES: List[Dict[str, Any]] = [
    {
        "id": "c0000000-0000-4000-8000-000000000001",
        "name": "Python Developers",
        "slug": "python-developers",
        "description": "A community for Python enthusiasts to share knowledge, ask questions, and collaborate on projects.",
        "category": "technology",
        "privacy": "public",
        "tags": ["python", "programming", "backend", "data-science"],
        "rules": ["Be respectful", "No spam", "Stay on topic", "Share code with context"],
        "avatar_url": "https://cdn.example.com/avatars/python-devs.png",
        "banner_url": "https://cdn.example.com/banners/python-devs.png",
        "member_count": 15420,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2025-09-20T14:22:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000001",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000002",
        "name": "Indie Game Devs",
        "slug": "indie-game-devs",
        "description": "Independent game developers sharing their journey, assets, and feedback on game design.",
        "category": "gaming",
        "privacy": "public",
        "tags": ["gamedev", "indie", "unity", "godot"],
        "rules": ["Constructive feedback only", "No asset flipping", "Credit original creators"],
        "avatar_url": "https://cdn.example.com/avatars/indie-gamedev.png",
        "banner_url": None,
        "member_count": 8730,
        "created_at": "2024-03-22T08:15:00Z",
        "updated_at": "2025-10-01T09:45:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000002",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000003",
        "name": "Digital Art Collective",
        "slug": "digital-art-collective",
        "description": "A private community for digital artists to critique work, share techniques, and collaborate.",
        "category": "art",
        "privacy": "private",
        "tags": ["digital-art", "illustration", "concept-art", "3d"],
        "rules": ["Critique with kindness", "No AI-generated art without disclosure", "NSFW must be tagged"],
        "avatar_url": "https://cdn.example.com/avatars/digital-art.png",
        "banner_url": "https://cdn.example.com/banners/digital-art.png",
        "member_count": 3210,
        "created_at": "2024-05-10T16:00:00Z",
        "updated_at": "2025-08-15T11:30:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000003",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000004",
        "name": "Startup Founders",
        "slug": "startup-founders",
        "description": "A secret community for startup founders to discuss fundraising, growth, and challenges.",
        "category": "business",
        "privacy": "secret",
        "tags": ["startups", "entrepreneurship", "fundraising", "saas"],
        "rules": ["Confidentiality required", "No solicitation", "Be genuine"],
        "avatar_url": None,
        "banner_url": None,
        "member_count": 890,
        "created_at": "2024-07-01T12:00:00Z",
        "updated_at": "2025-09-28T18:00:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000004",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000005",
        "name": "Machine Learning Research",
        "slug": "machine-learning-research",
        "description": "Discuss the latest papers, share implementations, and collaborate on ML research.",
        "category": "science",
        "privacy": "public",
        "tags": ["machine-learning", "deep-learning", "nlp", "computer-vision"],
        "rules": ["Cite papers", "No low-effort posts", "Be open to questions"],
        "avatar_url": "https://cdn.example.com/avatars/ml-research.png",
        "banner_url": "https://cdn.example.com/banners/ml-research.png",
        "member_count": 12100,
        "created_at": "2024-02-14T09:00:00Z",
        "updated_at": "2025-10-02T07:15:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000005",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000006",
        "name": "Fitness & Nutrition",
        "slug": "fitness-nutrition",
        "description": "Share workout routines, nutrition tips, and progress updates in a supportive environment.",
        "category": "lifestyle",
        "privacy": "public",
        "tags": ["fitness", "nutrition", "health", "wellness"],
        "rules": ["No medical advice", "Be supportive", "No body shaming"],
        "avatar_url": "https://cdn.example.com/avatars/fitness.png",
        "banner_url": None,
        "member_count": 22300,
        "created_at": "2024-04-05T07:30:00Z",
        "updated_at": "2025-09-10T12:00:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000006",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000007",
        "name": "Music Producers Hub",
        "slug": "music-producers-hub",
        "description": "A community for music producers to share tracks, get feedback, and discuss production techniques.",
        "category": "music",
        "privacy": "public",
        "tags": ["music-production", "ableton", "fl-studio", "sound-design"],
        "rules": ["Feedback must be constructive", "No self-promotion in main feed", "Tag your genre"],
        "avatar_url": "https://cdn.example.com/avatars/music-producers.png",
        "banner_url": "https://cdn.example.com/banners/music-producers.png",
        "member_count": 6540,
        "created_at": "2024-06-18T14:45:00Z",
        "updated_at": "2025-08-22T16:30:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000007",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000008",
        "name": "Photography Enthusiasts",
        "slug": "photography-enthusiasts",
        "description": "Share your best shots, discuss camera gear, and learn composition techniques.",
        "category": "art",
        "privacy": "public",
        "tags": ["photography", "landscape", "portrait", "street"],
        "rules": ["Include EXIF data when asking for feedback", "No stolen photos", "Be respectful"],
        "avatar_url": "https://cdn.example.com/avatars/photography.png",
        "banner_url": None,
        "member_count": 18900,
        "created_at": "2024-03-01T11:00:00Z",
        "updated_at": "2025-09-05T10:00:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000008",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000009",
        "name": "Book Club",
        "slug": "book-club",
        "description": "Monthly book reads with discussions, reviews, and author Q&A sessions.",
        "category": "education",
        "privacy": "private",
        "tags": ["books", "reading", "literature", "discussion"],
        "rules": ["No spoilers outside marked threads", "Respect all opinions", "One book at a time"],
        "avatar_url": "https://cdn.example.com/avatars/book-club.png",
        "banner_url": "https://cdn.example.com/banners/book-club.png",
        "member_count": 4200,
        "created_at": "2024-08-12T09:30:00Z",
        "updated_at": "2025-09-15T13:45:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000009",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000010",
        "name": "Esports Arena",
        "slug": "esports-arena",
        "description": "Competitive gaming community with tournaments, team finder, and strategy discussions.",
        "category": "gaming",
        "privacy": "public",
        "tags": ["esports", "competitive", "tournaments", "team-finder"],
        "rules": ["No cheating", "Be a good sport", "No toxicity"],
        "avatar_url": "https://cdn.example.com/avatars/esports.png",
        "banner_url": "https://cdn.example.com/banners/esports.png",
        "member_count": 31200,
        "created_at": "2024-01-20T15:00:00Z",
        "updated_at": "2025-10-01T20:00:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000010",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000011",
        "name": "Crypto Traders",
        "slug": "crypto-traders",
        "description": "Discuss market trends, trading strategies, and blockchain technology.",
        "category": "business",
        "privacy": "private",
        "tags": ["crypto", "trading", "blockchain", "defi"],
        "rules": ["No financial advice", "No pump and dump", "DYOR"],
        "avatar_url": None,
        "banner_url": None,
        "member_count": 9800,
        "created_at": "2024-05-25T10:00:00Z",
        "updated_at": "2025-09-20T08:30:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000011",
    },
    {
        "id": "c0000000-0000-4000-8000-000000000012",
        "name": "Language Learners",
        "slug": "language-learners",
        "description": "Practice languages with native speakers, share resources, and track progress.",
        "category": "education",
        "privacy": "public",
        "tags": ["languages", "learning", "practice", "culture"],
        "rules": ["Be patient with beginners", "Correct gently", "No translation services"],
        "avatar_url": "https://cdn.example.com/avatars/language.png",
        "banner_url": "https://cdn.example.com/banners/language.png",
        "member_count": 27600,
        "created_at": "2024-02-28T08:00:00Z",
        "updated_at": "2025-09-30T17:00:00Z",
        "is_active": True,
        "owner_id": "u0000000-0000-4000-8000-000000000012",
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=CommunityListResponse,
    summary="List communities",
    description="Retrieve a paginated list of communities with optional filtering by category and privacy level.",
)
async def list_communities(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    category: Optional[CommunityCategory] = Query(None, description="Filter by category"),
    privacy: Optional[PrivacyLevel] = Query(None, description="Filter by privacy level"),
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Search by name or description"),
    sort_by: str = Query("created_at", regex="^(created_at|member_count|name)$", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
) -> CommunityListResponse:
    """
    List communities with pagination and filtering.

    Returns a paginated list of communities matching the specified filters.
    """
    filtered = MOCK_COMMUNITIES.copy()

    # Apply filters
    if category is not None:
        filtered = [c for c in filtered if c["category"] == category.value]

    if privacy is not None:
        filtered = [c for c in filtered if c["privacy"] == privacy.value]

    if search:
        search_lower = search.lower()
        filtered = [
            c for c in filtered
            if search_lower in c["name"].lower() or search_lower in c["description"].lower()
        ]

    # Apply sorting
    reverse = sort_order == "desc"
    if sort_by == "name":
        filtered.sort(key=lambda c: c["name"].lower(), reverse=reverse)
    elif sort_by == "member_count":
        filtered.sort(key=lambda c: c["member_count"], reverse=reverse)
    else:  # created_at
        filtered.sort(key=lambda c: c["created_at"], reverse=reverse)

    # Apply pagination
    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    if page > total_pages and total > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Page {page} exceeds total pages ({total_pages})",
        )

    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    return CommunityListResponse(
        data=[CommunityResponse(**c) for c in paginated],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=CommunityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a community",
    description="Create a new community with the provided details.",
)
async def create_community(payload: CommunityCreate) -> CommunityResponse:
    """
    Create a new community.

    Validates the input and returns the created community with generated metadata.
    """
    # Check for duplicate slug
    slug = _generate_slug(payload.name)
    existing_slugs = {c["slug"] for c in MOCK_COMMUNITIES}
    if slug in existing_slugs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A community with a similar name already exists (slug: '{slug}')",
        )

    now = datetime.now(timezone.utc).isoformat()

    new_community = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "slug": slug,
        "description": payload.description,
        "category": payload.category.value,
        "privacy": payload.privacy.value,
        "tags": payload.tags,
        "rules": payload.rules,
        "avatar_url": payload.avatar_url,
        "banner_url": payload.banner_url,
        "member_count": 1,  # Creator is the first member
        "created_at": now,
        "updated_at": now,
        "is_active": True,
        "owner_id": str(uuid.uuid4()),  # In real app, from auth context
    }

    # In a real app, this would persist to the database
    MOCK_COMMUNITIES.append(new_community)

    return CommunityResponse(**new_community)

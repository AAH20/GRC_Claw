"""Tags API endpoints for UGC Marketplace."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/tags", tags=["tags"])


# ─── Mock Data ───────────────────────────────────────────────────────────────

MOCK_TAGS = [
    {"id": 1, "name": "lifestyle", "slug": "lifestyle", "description": "Everyday life and wellness content", "color": "#6366f1", "usage_count": 1247, "created_at": "2025-01-15T08:30:00Z", "updated_at": "2025-06-20T14:22:00Z"},
    {"id": 2, "name": "fitness", "slug": "fitness", "description": "Workout routines and health tips", "color": "#22c55e", "usage_count": 892, "created_at": "2025-01-18T10:15:00Z", "updated_at": "2025-07-11T09:45:00Z"},
    {"id": 3, "name": "food", "slug": "food", "description": "Recipes, reviews, and culinary content", "color": "#f59e0b", "usage_count": 2103, "created_at": "2025-01-22T12:00:00Z", "updated_at": "2025-08-03T16:30:00Z"},
    {"id": 4, "name": "travel", "slug": "travel", "description": "Destination guides and travel vlogs", "color": "#3b82f6", "usage_count": 1568, "created_at": "2025-02-01T09:00:00Z", "updated_at": "2025-07-28T11:10:00Z"},
    {"id": 5, "name": "tech", "slug": "tech", "description": "Gadget reviews and tech tutorials", "color": "#8b5cf6", "usage_count": 734, "created_at": "2025-02-10T14:30:00Z", "updated_at": "2025-06-15T08:00:00Z"},
    {"id": 6, "name": "fashion", "slug": "fashion", "description": "Style tips, hauls, and outfit ideas", "color": "#ec4899", "usage_count": 1890, "created_at": "2025-02-14T11:45:00Z", "updated_at": "2025-08-10T13:20:00Z"},
    {"id": 7, "name": "beauty", "slug": "beauty", "description": "Makeup tutorials and skincare routines", "color": "#f43f5e", "usage_count": 1456, "created_at": "2025-02-20T16:00:00Z", "updated_at": "2025-07-05T10:30:00Z"},
    {"id": 8, "name": "gaming", "slug": "gaming", "description": "Game reviews, streams, and esports", "color": "#14b8a6", "usage_count": 623, "created_at": "2025-03-01T08:00:00Z", "updated_at": "2025-06-25T15:45:00Z"},
    {"id": 9, "name": "diy", "slug": "diy", "description": "Crafts, home improvement, and projects", "color": "#a855f7", "usage_count": 412, "created_at": "2025-03-05T13:15:00Z", "updated_at": "2025-05-30T09:00:00Z"},
    {"id": 10, "name": "finance", "slug": "finance", "description": "Personal finance and investment advice", "color": "#059669", "usage_count": 389, "created_at": "2025-03-10T10:30:00Z", "updated_at": "2025-07-18T14:00:00Z"},
    {"id": 11, "name": "education", "slug": "education", "description": "Tutorials, courses, and learning resources", "color": "#0ea5e9", "usage_count": 567, "created_at": "2025-03-15T09:45:00Z", "updated_at": "2025-08-01T11:30:00Z"},
    {"id": 12, "name": "music", "slug": "music", "description": "Covers, originals, and music reviews", "color": "#e11d48", "usage_count": 834, "created_at": "2025-03-20T15:00:00Z", "updated_at": "2025-07-22T16:15:00Z"},
    {"id": 13, "name": "photography", "slug": "photography", "description": "Photo tips, edits, and showcases", "color": "#7c3aed", "usage_count": 478, "created_at": "2025-04-01T08:30:00Z", "updated_at": "2025-06-10T12:45:00Z"},
    {"id": 14, "name": "pets", "slug": "pets", "description": "Pet care, training, and cute moments", "color": "#d97706", "usage_count": 1102, "created_at": "2025-04-05T11:00:00Z", "updated_at": "2025-08-05T10:00:00Z"},
    {"id": 15, "name": "sustainability", "slug": "sustainability", "description": "Eco-friendly living and green tips", "color": "#16a34a", "usage_count": 298, "created_at": "2025-04-10T14:15:00Z", "updated_at": "2025-07-14T09:30:00Z"},
    {"id": 16, "name": "comedy", "slug": "comedy", "description": "Sketches, parodies, and humor content", "color": "#f97316", "usage_count": 1678, "created_at": "2025-04-15T10:00:00Z", "updated_at": "2025-08-12T13:00:00Z"},
    {"id": 17, "name": "motorsports", "slug": "motorsports", "description": "Car reviews, racing, and automotive content", "color": "#dc2626", "usage_count": 345, "created_at": "2025-04-20T16:30:00Z", "updated_at": "2025-06-28T08:45:00Z"},
    {"id": 18, "name": "parenting", "slug": "parenting", "description": "Family content and parenting advice", "color": "#0d9488", "usage_count": 789, "created_at": "2025-05-01T09:15:00Z", "updated_at": "2025-07-30T15:30:00Z"},
    {"id": 19, "name": "art", "slug": "art", "description": "Digital art, traditional art, and creative process", "color": "#9333ea", "usage_count": 521, "created_at": "2025-05-05T12:00:00Z", "updated_at": "2025-08-08T11:00:00Z"},
    {"id": 20, "name": "science", "slug": "science", "description": "Science explainers, experiments, and news", "color": "#2563eb", "usage_count": 412, "created_at": "2025-05-10T08:45:00Z", "updated_at": "2025-07-25T14:15:00Z"},
]


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    """Schema for creating a new tag."""
    name: str = Field(..., min_length=1, max_length=50, description="Display name of the tag")
    slug: Optional[str] = Field(None, max_length=50, description="URL-friendly slug (auto-generated from name if omitted)")
    description: Optional[str] = Field(None, max_length=255, description="Short description of the tag")
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$", description="Hex color code for the tag")


class TagResponse(BaseModel):
    """Schema for tag response."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = None
    usage_count: int
    created_at: str
    updated_at: str


class TagListResponse(BaseModel):
    """Schema for paginated tag list response."""
    data: list[TagResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a tag name."""
    return name.lower().strip().replace(" ", "-")


def _tag_exists(name: str) -> bool:
    """Check if a tag with the given name already exists (case-insensitive)."""
    return any(t["name"].lower() == name.lower() for t in MOCK_TAGS)


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/", response_model=TagListResponse, summary="List all tags with pagination")
async def list_tags(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: Optional[str] = Query(None, description="Filter tags by name (case-insensitive)"),
):
    """
    Retrieve a paginated list of tags.

    Supports optional search filtering by tag name.
    """
    filtered = MOCK_TAGS
    if search:
        filtered = [t for t in MOCK_TAGS if search.lower() in t["name"].lower()]

    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size

    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    return TagListResponse(
        data=[TagResponse(**t) for t in paginated],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/", response_model=TagResponse, status_code=201, summary="Create a new tag")
async def create_tag(payload: TagCreate):
    """
    Create a new tag with validation.

    - **name**: Required, must be unique (case-insensitive)
    - **slug**: Optional, auto-generated from name if not provided
    - **description**: Optional, max 255 characters
    - **color**: Optional, must be a valid hex color (e.g., #ff5733)
    """
    # Validate uniqueness
    if _tag_exists(payload.name):
        raise HTTPException(
            status_code=409,
            detail=f"Tag with name '{payload.name}' already exists",
        )

    # Auto-generate slug if not provided
    slug = payload.slug or _generate_slug(payload.name)

    # Check slug uniqueness
    if any(t["slug"] == slug for t in MOCK_TAGS):
        raise HTTPException(
            status_code=409,
            detail=f"Tag with slug '{slug}' already exists",
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_id = max(t["id"] for t in MOCK_TAGS) + 1

    new_tag = {
        "id": new_id,
        "name": payload.name,
        "slug": slug,
        "description": payload.description,
        "color": payload.color or "#6b7280",
        "usage_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    MOCK_TAGS.append(new_tag)

    return TagResponse(**new_tag)

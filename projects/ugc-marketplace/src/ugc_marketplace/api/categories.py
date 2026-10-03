"""
Categories API endpoints for UGC Marketplace.

Provides CRUD operations for product/service categories with pagination
and input validation.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/categories", tags=["categories"])


# ─── Pydantic Schemas ────────────────────────────────────────────────────────


class CategoryBase(BaseModel):
    """Shared category fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Category display name")
    slug: str = Field(
        ...,
        min_length=1,
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-friendly identifier",
    )
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[int] = Field(None, description="Parent category ID for nesting")
    icon: Optional[str] = Field(None, max_length=200, description="Icon URL or emoji")
    is_active: bool = Field(True)
    sort_order: int = Field(0, ge=0, le=9999)


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[int] = None
    icon: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0, le=9999)


class CategoryResponse(CategoryBase):
    """Full category representation returned by the API."""

    id: int
    created_at: datetime
    updated_at: datetime
    product_count: int = 0

    class Config:
        from_attributes = True


class PaginatedCategoryResponse(BaseModel):
    """Paginated list wrapper."""

    items: List[CategoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Mock Data Store ─────────────────────────────────────────────────────────

MOCK_CATEGORIES: List[dict] = [
    {
        "id": 1,
        "name": "Digital Products",
        "slug": "digital-products",
        "description": "Software, templates, and digital downloads",
        "parent_id": None,
        "icon": "💻",
        "is_active": True,
        "sort_order": 1,
        "created_at": datetime(2025, 1, 15, 10, 30, 0),
        "updated_at": datetime(2025, 6, 20, 14, 0, 0),
        "product_count": 142,
    },
    {
        "id": 2,
        "name": "Graphic Design",
        "slug": "graphic-design",
        "description": "Logos, branding, illustrations, and visual assets",
        "parent_id": None,
        "icon": "🎨",
        "is_active": True,
        "sort_order": 2,
        "created_at": datetime(2025, 1, 15, 10, 35, 0),
        "updated_at": datetime(2025, 7, 1, 9, 15, 0),
        "product_count": 89,
    },
    {
        "id": 3,
        "name": "Video & Animation",
        "slug": "video-animation",
        "description": "Stock footage, motion graphics, and animated content",
        "parent_id": None,
        "icon": "🎬",
        "is_active": True,
        "sort_order": 3,
        "created_at": datetime(2025, 1, 20, 8, 0, 0),
        "updated_at": datetime(2025, 5, 10, 11, 45, 0),
        "product_count": 67,
    },
    {
        "id": 4,
        "name": "Writing & Content",
        "slug": "writing-content",
        "description": "Articles, copywriting, and editorial services",
        "parent_id": None,
        "icon": "✍️",
        "is_active": True,
        "sort_order": 4,
        "created_at": datetime(2025, 2, 1, 12, 0, 0),
        "updated_at": datetime(2025, 8, 12, 16, 30, 0),
        "product_count": 54,
    },
    {
        "id": 5,
        "name": "Music & Audio",
        "slug": "music-audio",
        "description": "Royal tracks, sound effects, and audio production",
        "parent_id": None,
        "icon": "🎵",
        "is_active": True,
        "sort_order": 5,
        "created_at": datetime(2025, 2, 10, 9, 0, 0),
        "updated_at": datetime(2025, 4, 22, 13, 0, 0),
        "product_count": 38,
    },
    {
        "id": 6,
        "name": "UI/UX Design",
        "slug": "ui-ux-design",
        "description": "Interface design, wireframes, and user experience assets",
        "parent_id": 2,
        "icon": "📱",
        "is_active": True,
        "sort_order": 6,
        "created_at": datetime(2025, 3, 5, 14, 20, 0),
        "updated_at": datetime(2025, 9, 1, 10, 0, 0),
        "product_count": 73,
    },
    {
        "id": 7,
        "name": "3D Models",
        "slug": "3d-models",
        "description": "3D assets, characters, environments, and printable models",
        "parent_id": None,
        "icon": "🧊",
        "is_active": True,
        "sort_order": 7,
        "created_at": datetime(2025, 3, 15, 11, 0, 0),
        "updated_at": datetime(2025, 6, 30, 8, 45, 0),
        "product_count": 45,
    },
    {
        "id": 8,
        "name": "Photography",
        "slug": "photography",
        "description": "Stock photos, presets, and editing services",
        "parent_id": None,
        "icon": "📷",
        "is_active": True,
        "sort_order": 8,
        "created_at": datetime(2025, 4, 1, 10, 0, 0),
        "updated_at": datetime(2025, 7, 18, 15, 30, 0),
        "product_count": 112,
    },
    {
        "id": 9,
        "name": "Web Development",
        "slug": "web-development",
        "description": "Themes, plugins, scripts, and development services",
        "parent_id": None,
        "icon": "🌐",
        "is_active": True,
        "sort_order": 9,
        "created_at": datetime(2025, 4, 20, 9, 30, 0),
        "updated_at": datetime(2025, 8, 5, 12, 0, 0),
        "product_count": 96,
    },
    {
        "id": 10,
        "name": "Marketing & Ads",
        "slug": "marketing-ads",
        "description": "Ad creatives, campaign assets, and marketing templates",
        "parent_id": None,
        "icon": "📣",
        "is_active": False,
        "sort_order": 10,
        "created_at": datetime(2025, 5, 1, 8, 0, 0),
        "updated_at": datetime(2025, 5, 1, 8, 0, 0),
        "product_count": 21,
    },
    {
        "id": 11,
        "name": "Icon Sets",
        "slug": "icon-sets",
        "description": "Custom icon packs and vector icon libraries",
        "parent_id": 2,
        "icon": "🔣",
        "is_active": True,
        "sort_order": 11,
        "created_at": datetime(2025, 5, 15, 13, 0, 0),
        "updated_at": datetime(2025, 9, 10, 17, 0, 0),
        "product_count": 33,
    },
    {
        "id": 12,
        "name": "Fonts & Typography",
        "slug": "fonts-typography",
        "description": "Custom fonts, typefaces, and lettering assets",
        "parent_id": None,
        "icon": "🔤",
        "is_active": True,
        "sort_order": 12,
        "created_at": datetime(2025, 6, 1, 10, 0, 0),
        "updated_at": datetime(2025, 10, 1, 9, 0, 0),
        "product_count": 58,
    },
]

_next_id = max(c["id"] for c in MOCK_CATEGORIES) + 1


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=PaginatedCategoryResponse,
    summary="List categories",
    description="Retrieve a paginated list of categories with optional filtering.",
)
async def list_categories(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Filter by name or slug (case-insensitive)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    parent_id: Optional[int] = Query(None, description="Filter by parent category ID"),
) -> PaginatedCategoryResponse:
    """
    Return a paginated list of categories.

    Supports filtering by search term, active status, and parent category.
    Results are ordered by sort_order ascending, then by name.
    """
    filtered = MOCK_CATEGORIES.copy()

    if search:
        term = search.lower()
        filtered = [
            c
            for c in filtered
            if term in c["name"].lower() or term in c["slug"].lower()
        ]

    if is_active is not None:
        filtered = [c for c in filtered if c["is_active"] == is_active]

    if parent_id is not None:
        filtered = [c for c in filtered if c["parent_id"] == parent_id]

    # Sort by sort_order, then name
    filtered.sort(key=lambda c: (c["sort_order"], c["name"]))

    total = len(filtered)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return PaginatedCategoryResponse(
        items=[CategoryResponse(**c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
    description="Create a new category with validated input.",
)
async def create_category(payload: CategoryCreate) -> CategoryResponse:
    """
    Create a new category.

    Validates that the slug is unique among existing categories.
    Returns the newly created category with 201 status.
    """
    global _next_id

    # Check for duplicate slug
    existing_slugs = {c["slug"] for c in MOCK_CATEGORIES}
    if payload.slug in existing_slugs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category with slug '{payload.slug}' already exists.",
        )

    # Validate parent_id if provided
    if payload.parent_id is not None:
        parent_ids = {c["id"] for c in MOCK_CATEGORIES}
        if payload.parent_id not in parent_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent category with id {payload.parent_id} does not exist.",
            )

    now = datetime.utcnow()
    new_category = {
        "id": _next_id,
        "name": payload.name,
        "slug": payload.slug,
        "description": payload.description,
        "parent_id": payload.parent_id,
        "icon": payload.icon,
        "is_active": payload.is_active,
        "sort_order": payload.sort_order,
        "created_at": now,
        "updated_at": now,
        "product_count": 0,
    }

    MOCK_CATEGORIES.append(new_category)
    _next_id += 1

    return CategoryResponse(**new_category)

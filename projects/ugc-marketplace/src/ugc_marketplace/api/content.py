"""
Content API endpoints for UGC Marketplace.

Provides:
  GET  /content  — list content with pagination, filtering by type/status
  POST /content  — create content with validation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/content", tags=["content"])


# ─── Mock data store ────────────────────────────────────────────────────────

MOCK_CONTENT: List[Dict[str, Any]] = [
    {
        "id": "c-001",
        "title": "Summer Collection Showcase",
        "type": "image",
        "status": "published",
        "author_id": "u-101",
        "tags": ["summer", "fashion", "lifestyle"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-001.jpg",
        "description": "Bright and breezy summer looks featuring the new collection.",
        "created_at": "2026-08-15T10:30:00Z",
        "updated_at": "2026-08-15T10:30:00Z",
        "views": 12450,
        "likes": 892,
    },
    {
        "id": "c-002",
        "title": "Unboxing: Tech Gadget Pro",
        "type": "video",
        "status": "published",
        "author_id": "u-102",
        "tags": ["tech", "unboxing", "review"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-002.mp4",
        "description": "Full unboxing and first impressions of the Tech Gadget Pro.",
        "created_at": "2026-08-20T14:00:00Z",
        "updated_at": "2026-08-20T14:00:00Z",
        "views": 34200,
        "likes": 2100,
    },
    {
        "id": "c-003",
        "title": "Behind the Scenes: Studio Shoot",
        "type": "image",
        "status": "draft",
        "author_id": "u-103",
        "tags": ["bts", "photography"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-003.jpg",
        "description": "Exclusive behind-the-scenes look at our latest studio shoot.",
        "created_at": "2026-09-01T09:15:00Z",
        "updated_at": "2026-09-01T09:15:00Z",
        "views": 0,
        "likes": 0,
    },
    {
        "id": "c-004",
        "title": "Customer Review: Blender Max",
        "type": "review",
        "status": "published",
        "author_id": "u-104",
        "tags": ["review", "kitchen", "appliances"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-004.jpg",
        "description": "Honest review of the Blender Max after 30 days of use.",
        "created_at": "2026-09-05T16:45:00Z",
        "updated_at": "2026-09-05T16:45:00Z",
        "views": 8900,
        "likes": 654,
    },
    {
        "id": "c-005",
        "title": "Tutorial: Skincare Routine",
        "type": "video",
        "status": "pending",
        "author_id": "u-105",
        "tags": ["skincare", "tutorial", "beauty"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-005.mp4",
        "description": "Step-by-step skincare routine for glowing skin.",
        "created_at": "2026-09-10T11:00:00Z",
        "updated_at": "2026-09-10T11:00:00Z",
        "views": 0,
        "likes": 0,
    },
    {
        "id": "c-006",
        "title": "Autumn Lookbook",
        "type": "image",
        "status": "published",
        "author_id": "u-106",
        "tags": ["autumn", "fashion", "lookbook"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-006.jpg",
        "description": "Cozy autumn outfits for every occasion.",
        "created_at": "2026-09-12T08:20:00Z",
        "updated_at": "2026-09-12T08:20:00Z",
        "views": 15600,
        "likes": 1100,
    },
    {
        "id": "c-007",
        "title": "Product Comparison: Headphones",
        "type": "review",
        "status": "archived",
        "author_id": "u-107",
        "tags": ["tech", "comparison", "audio"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-007.jpg",
        "description": "Comparing the top 5 headphones of 2026.",
        "created_at": "2026-07-20T13:30:00Z",
        "updated_at": "2026-08-01T10:00:00Z",
        "views": 45000,
        "likes": 3200,
    },
    {
        "id": "c-008",
        "title": "Fitness Challenge Week 1",
        "type": "video",
        "status": "published",
        "author_id": "u-108",
        "tags": ["fitness", "challenge", "health"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-008.mp4",
        "description": "Join me for a 30-day fitness challenge — week 1 recap.",
        "created_at": "2026-09-15T07:00:00Z",
        "updated_at": "2026-09-15T07:00:00Z",
        "views": 22100,
        "likes": 1800,
    },
    {
        "id": "c-009",
        "title": "DIY Home Decor Ideas",
        "type": "image",
        "status": "draft",
        "author_id": "u-109",
        "tags": ["diy", "home", "decor"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-009.jpg",
        "description": "Budget-friendly DIY home decor ideas for small spaces.",
        "created_at": "2026-09-18T15:45:00Z",
        "updated_at": "2026-09-18T15:45:00Z",
        "views": 0,
        "likes": 0,
    },
    {
        "id": "c-010",
        "title": "Restaurant Review: Downtown Bistro",
        "type": "review",
        "status": "published",
        "author_id": "u-110",
        "tags": ["food", "restaurant", "review"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-010.jpg",
        "description": "A detailed review of the Downtown Bistro experience.",
        "created_at": "2026-09-20T19:00:00Z",
        "updated_at": "2026-09-20T19:00:00Z",
        "views": 6700,
        "likes": 430,
    },
    {
        "id": "c-011",
        "title": "Travel Vlog: Mountain Escape",
        "type": "video",
        "status": "pending",
        "author_id": "u-111",
        "tags": ["travel", "vlog", "mountains"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-011.mp4",
        "description": "A weekend escape to the mountains — full vlog.",
        "created_at": "2026-09-22T12:00:00Z",
        "updated_at": "2026-09-22T12:00:00Z",
        "views": 0,
        "likes": 0,
    },
    {
        "id": "c-012",
        "title": "Gaming Setup Tour 2026",
        "type": "image",
        "status": "published",
        "author_id": "u-112",
        "tags": ["gaming", "setup", "tech"],
        "media_url": "https://cdn.ugc-marketplace.example/media/c-012.jpg",
        "description": "Complete tour of my 2026 gaming setup with all peripherals.",
        "created_at": "2026-09-25T17:30:00Z",
        "updated_at": "2026-09-25T17:30:00Z",
        "views": 19800,
        "likes": 1450,
    },
]


# ─── Pydantic models ────────────────────────────────────────────────────────

VALID_TYPES = {"image", "video", "review"}
VALID_STATUSES = {"draft", "pending", "published", "archived"}


class ContentCreate(BaseModel):
    """Schema for creating new content."""

    title: str = Field(..., min_length=1, max_length=200)
    type: str = Field(..., description="Content type: image, video, or review")
    author_id: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    tags: List[str] = Field(default_factory=list)
    media_url: Optional[str] = Field(None, max_length=500)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(VALID_TYPES))}")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        if len(v) > 20:
            raise ValueError("maximum 20 tags allowed")
        for tag in v:
            if len(tag) > 50:
                raise ValueError("each tag must be 50 characters or fewer")
        return v


class ContentResponse(BaseModel):
    """Schema for content response."""

    id: str
    title: str
    type: str
    status: str
    author_id: str
    tags: List[str]
    media_url: Optional[str]
    description: Optional[str]
    created_at: str
    updated_at: str
    views: int
    likes: int


class ContentListResponse(BaseModel):
    """Schema for paginated content list response."""

    items: List[ContentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Endpoints ──────────────────────────────────────────────────────────────


@router.get("", response_model=ContentListResponse)
async def list_content(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    type: Optional[str] = Query(None, description="Filter by content type"),
    status: Optional[str] = Query(None, description="Filter by content status"),
) -> Dict[str, Any]:
    """
    List content with pagination and optional filtering by type and/or status.
    """
    # Validate filter values
    if type is not None and type not in VALID_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid type filter. Must be one of: {', '.join(sorted(VALID_TYPES))}",
        )
    if status is not None and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status filter. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    # Apply filters
    filtered = MOCK_CONTENT.copy()
    if type is not None:
        filtered = [c for c in filtered if c["type"] == type]
    if status is not None:
        filtered = [c for c in filtered if c["status"] == status]

    # Pagination
    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(payload: ContentCreate) -> Dict[str, Any]:
    """
    Create new content with validation. Returns the created content object.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_id = f"c-{str(uuid.uuid4())[:8]}"

    new_content: Dict[str, Any] = {
        "id": new_id,
        "title": payload.title,
        "type": payload.type,
        "status": "draft",
        "author_id": payload.author_id,
        "tags": payload.tags,
        "media_url": payload.media_url,
        "description": payload.description,
        "created_at": now,
        "updated_at": now,
        "views": 0,
        "likes": 0,
    }

    # In a real app, this would persist to a database
    MOCK_CONTENT.append(new_content)

    return new_content

"""
Posts API endpoints for gated communities.

Provides:
  GET  /posts  — list posts with pagination, filtering by community/author
  POST /posts  — create a post with validation
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/posts", tags=["posts"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class PostCreate(BaseModel):
    """Payload for creating a new post."""
    community_id: int = Field(..., gt=0, description="ID of the community this post belongs to")
    author_id: int = Field(..., gt=0, description="ID of the post author")
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=10_000)
    is_pinned: bool = False


class PostResponse(BaseModel):
    """Response model for a single post."""
    id: int
    community_id: int
    author_id: int
    title: str
    body: str
    is_pinned: bool
    created_at: str
    updated_at: str


class PostListResponse(BaseModel):
    """Paginated list of posts."""
    items: list[PostResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# ---------------------------------------------------------------------------
# Mock data store
# ---------------------------------------------------------------------------

MOCK_POSTS: list[dict] = [
    {
        "id": 1,
        "community_id": 1,
        "author_id": 101,
        "title": "Welcome to the community!",
        "body": "This is the first post. Feel free to introduce yourself.",
        "is_pinned": True,
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": "2026-09-01T10:00:00Z",
    },
    {
        "id": 2,
        "community_id": 1,
        "author_id": 102,
        "title": "Weekly discussion thread",
        "body": "Share your thoughts on this week's topic.",
        "is_pinned": False,
        "created_at": "2026-09-08T14:30:00Z",
        "updated_at": "2026-09-08T14:30:00Z",
    },
    {
        "id": 3,
        "community_id": 2,
        "author_id": 103,
        "title": "Project showcase",
        "body": "Show off what you've been building.",
        "is_pinned": False,
        "created_at": "2026-09-15T09:15:00Z",
        "updated_at": "2026-09-15T09:15:00Z",
    },
    {
        "id": 4,
        "community_id": 1,
        "author_id": 101,
        "title": "Guidelines update",
        "body": "Please review the updated community guidelines.",
        "is_pinned": True,
        "created_at": "2026-09-20T16:45:00Z",
        "updated_at": "2026-09-20T16:45:00Z",
    },
    {
        "id": 5,
        "community_id": 2,
        "author_id": 104,
        "title": "Bug reports thread",
        "body": "Post any bugs you encounter here.",
        "is_pinned": False,
        "created_at": "2026-09-25T11:00:00Z",
        "updated_at": "2026-09-25T11:00:00Z",
    },
    {
        "id": 6,
        "community_id": 3,
        "author_id": 105,
        "title": "Announcement: New features",
        "body": "We've shipped several new features this month.",
        "is_pinned": True,
        "created_at": "2026-10-01T08:00:00Z",
        "updated_at": "2026-10-01T08:00:00Z",
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=PostListResponse)
async def list_posts(
    community_id: Optional[int] = Query(None, gt=0, description="Filter by community ID"),
    author_id: Optional[int] = Query(None, gt=0, description="Filter by author ID"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
) -> dict:
    """
    List posts with optional filtering by community and/or author.

    Returns a paginated list of posts matching the given filters.
    """
    filtered = MOCK_POSTS

    if community_id is not None:
        filtered = [p for p in filtered if p["community_id"] == community_id]

    if author_id is not None:
        filtered = [p for p in filtered if p["author_id"] == author_id]

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": end < total,
        "has_prev": page > 1,
    }


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate) -> dict:
    """
    Create a new post in a gated community.

    Validates the payload and returns the created post.
    """
    new_id = max(p["id"] for p in MOCK_POSTS) + 1 if MOCK_POSTS else 1
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    post = {
        "id": new_id,
        "community_id": payload.community_id,
        "author_id": payload.author_id,
        "title": payload.title,
        "body": payload.body,
        "is_pinned": payload.is_pinned,
        "created_at": now,
        "updated_at": now,
    }

    MOCK_POSTS.append(post)
    return post

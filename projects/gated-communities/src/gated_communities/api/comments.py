"""
Comments API endpoints for gated-communities.

Provides:
  GET  /comments  — list comments with pagination and post filtering
  POST /comments  — create a new comment with validation
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator

router = APIRouter()

# ---------------------------------------------------------------------------
# Mock data store (in-memory for demonstration)
# ---------------------------------------------------------------------------

MOCK_COMMENTS: List[Dict[str, Any]] = [
    {
        "id": "cmt_001",
        "post_id": "post_alpha",
        "author_id": "user_alice",
        "author_name": "Alice Chen",
        "content": "Great write-up on community governance. The quadratic funding section was especially insightful.",
        "parent_id": None,
        "created_at": "2026-09-28T14:22:00Z",
        "updated_at": "2026-09-28T14:22:00Z",
        "upvotes": 12,
        "downvotes": 1,
        "is_edited": False,
        "is_pinned": False,
    },
    {
        "id": "cmt_002",
        "post_id": "post_alpha",
        "author_id": "user_bob",
        "author_name": "Bob Martinez",
        "content": "I disagree with the conclusion about token-weighted voting. It tends to concentrate power in early adopters.",
        "parent_id": None,
        "created_at": "2026-09-28T15:05:00Z",
        "updated_at": "2026-09-28T15:05:00Z",
        "upvotes": 8,
        "downvotes": 3,
        "is_edited": False,
        "is_pinned": False,
    },
    {
        "id": "cmt_003",
        "post_id": "post_alpha",
        "author_id": "user_carol",
        "author_name": "Carol Singh",
        "content": "Bob, that's a fair point. Maybe a hybrid model could work — one-person-one-vote for certain decisions and token-weighted for others.",
        "parent_id": "cmt_002",
        "created_at": "2026-09-28T15:42:00Z",
        "updated_at": "2026-09-28T15:42:00Z",
        "upvotes": 15,
        "downvotes": 0,
        "is_edited": False,
        "is_pinned": True,
    },
    {
        "id": "cmt_004",
        "post_id": "post_beta",
        "author_id": "user_dave",
        "author_name": "Dave Park",
        "content": "Has anyone tested the new reputation system on the testnet? Curious about the sybil resistance mechanisms.",
        "parent_id": None,
        "created_at": "2026-09-29T09:10:00Z",
        "updated_at": "2026-09-29T09:10:00Z",
        "upvotes": 5,
        "downvotes": 0,
        "is_edited": False,
        "is_pinned": False,
    },
    {
        "id": "cmt_005",
        "post_id": "post_beta",
        "author_id": "user_eve",
        "author_name": "Eve Johnson",
        "content": "Yes! I've been running a node on the testnet for two weeks. The BrightID integration works well but the UX could be smoother.",
        "parent_id": "cmt_004",
        "created_at": "2026-09-29T10:30:00Z",
        "updated_at": "2026-09-29T10:30:00Z",
        "upvotes": 7,
        "downvotes": 1,
        "is_edited": False,
        "is_pinned": False,
    },
    {
        "id": "cmt_006",
        "post_id": "post_gamma",
        "author_id": "user_frank",
        "author_name": "Frank Liu",
        "content": "Proposal #42 looks promising. The budget allocation for Q4 seems reasonable given current treasury status.",
        "parent_id": None,
        "created_at": "2026-09-30T11:00:00Z",
        "updated_at": "2026-09-30T11:00:00Z",
        "upvotes": 20,
        "downvotes": 2,
        "is_edited": False,
        "is_pinned": True,
    },
    {
        "id": "cmt_007",
        "post_id": "post_gamma",
        "author_id": "user_grace",
        "author_name": "Grace Williams",
        "content": "I'd like to see more detail on the marketing budget breakdown. 40% for a single quarter feels aggressive.",
        "parent_id": "cmt_006",
        "created_at": "2026-09-30T12:15:00Z",
        "updated_at": "2026-09-30T12:15:00Z",
        "upvotes": 11,
        "downvotes": 0,
        "is_edited": False,
        "is_pinned": False,
    },
    {
        "id": "cmt_008",
        "post_id": "post_alpha",
        "author_id": "user_henry",
        "author_name": "Henry Zhao",
        "content": "Following this thread — would love to see a follow-up post with concrete implementation timelines.",
        "parent_id": None,
        "created_at": "2026-10-01T08:45:00Z",
        "updated_at": "2026-10-01T08:45:00Z",
        "upvotes": 3,
        "downvotes": 0,
        "is_edited": False,
        "is_pinned": False,
    },
    {
        "id": "cmt_009",
        "post_id": "post_delta",
        "author_id": "user_iris",
        "author_name": "Iris Patel",
        "content": "The community call recording from last Thursday is now available. Key topics: governance v2, delegation mechanics, and the upcoming airdrop.",
        "parent_id": None,
        "created_at": "2026-10-02T16:20:00Z",
        "updated_at": "2026-10-02T16:20:00Z",
        "upvotes": 18,
        "downvotes": 0,
        "is_edited": False,
        "is_pinned": True,
    },
    {
        "id": "cmt_010",
        "post_id": "post_delta",
        "author_id": "user_jack",
        "author_name": "Jack Thompson",
        "content": "Thanks for sharing! The delegation mechanics explanation finally cleared up my confusion about vote locking periods.",
        "parent_id": "cmt_009",
        "created_at": "2026-10-02T17:00:00Z",
        "updated_at": "2026-10-02T17:00:00Z",
        "upvotes": 6,
        "downvotes": 0,
        "is_edited": False,
        "is_pinned": False,
    },
]


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class CommentCreate(BaseModel):
    """Schema for creating a new comment."""

    post_id: str = Field(..., min_length=1, max_length=64, description="ID of the post this comment belongs to")
    content: str = Field(..., min_length=1, max_length=5000, description="Comment body text")
    parent_id: Optional[str] = Field(None, max_length=64, description="Parent comment ID for threaded replies")

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Comment content cannot be blank or whitespace only")
        return v.strip()

    @field_validator("post_id")
    @classmethod
    def post_id_valid(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("post_id cannot be blank")
        return v.strip()


class CommentResponse(BaseModel):
    """Schema for a comment in API responses."""

    id: str
    post_id: str
    author_id: str
    author_name: str
    content: str
    parent_id: Optional[str] = None
    created_at: str
    updated_at: str
    upvotes: int = 0
    downvotes: int = 0
    is_edited: bool = False
    is_pinned: bool = False


class CommentListResponse(BaseModel):
    """Paginated list of comments."""

    data: List[CommentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/comments", response_model=CommentListResponse, tags=["comments"])
async def list_comments(
    request: Request,
    post_id: Optional[str] = Query(None, description="Filter comments by post ID"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of comments per page"),
) -> Dict[str, Any]:
    """
    List comments with optional post filtering and pagination.

    Returns a paginated list of comments. When `post_id` is provided,
    only comments belonging to that post are returned.
    """
    # Filter by post_id if provided
    filtered = MOCK_COMMENTS
    if post_id:
        filtered = [c for c in MOCK_COMMENTS if c["post_id"] == post_id]

    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)

    # Clamp page to valid range
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    return {
        "data": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post(
    "/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["comments"],
)
async def create_comment(payload: CommentCreate, request: Request) -> Dict[str, Any]:
    """
    Create a new comment.

    Validates the payload, checks that the referenced post exists,
    and returns the newly created comment.
    """
    # Verify the post exists (mock check)
    valid_post_ids = {c["post_id"] for c in MOCK_COMMENTS}
    if payload.post_id not in valid_post_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id '{payload.post_id}' not found",
        )

    # If parent_id is provided, verify it exists
    if payload.parent_id:
        valid_parent_ids = {c["id"] for c in MOCK_COMMENTS}
        if payload.parent_id not in valid_parent_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent comment with id '{payload.parent_id}' not found",
            )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_comment: Dict[str, Any] = {
        "id": f"cmt_{uuid.uuid4().hex[:8]}",
        "post_id": payload.post_id,
        "author_id": "user_current",  # Would come from auth context in production
        "author_name": "Current User",
        "content": payload.content,
        "parent_id": payload.parent_id,
        "created_at": now,
        "updated_at": now,
        "upvotes": 0,
        "downvotes": 0,
        "is_edited": False,
        "is_pinned": False,
    }

    # In production this would persist to a database
    MOCK_COMMENTS.append(new_comment)

    return new_comment

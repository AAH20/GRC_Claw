"""Post management API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status

from social_media_manager.api.schemas import (
    Post,
    PostCreate,
    PostList,
    PostStatus,
)
from social_media_manager.api.store import post_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/posts", tags=["posts"])


@router.post("", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate) -> Post:
    """Create a new social media post.

    Args:
        payload: Validated post creation body.

    Returns:
        The persisted post with server-assigned id and timestamps.
    """
    post = post_store.create(payload)
    logger.info("post_created id=%s platform=%s", post.id, post.platform.value)
    return post


@router.get("", response_model=PostList)
async def list_posts(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PostList:
    """List posts with pagination, newest first.

    Args:
        limit: Maximum number of posts to return.
        offset: Number of posts to skip.

    Returns:
        A paginated list envelope.
    """
    items, total = post_store.list(limit=limit, offset=offset)
    return PostList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{post_id}", response_model=Post)
async def get_post(post_id: str) -> Post:
    """Fetch a single post by id.

    Raises:
        HTTPException: 404 if the post does not exist.
    """
    post = post_store.get(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"Post '{post_id}' not found")
    return post


@router.patch("/{post_id}/status", response_model=Post)
async def update_post_status(post_id: str, new_status: PostStatus) -> Post:
    """Transition a post to a new lifecycle status.

    Raises:
        HTTPException: 404 if the post does not exist.
    """
    post = post_store.update_status(post_id, new_status)
    if post is None:
        raise HTTPException(status_code=404, detail=f"Post '{post_id}' not found")
    logger.info("post_status_updated id=%s status=%s", post_id, new_status.value)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: str) -> None:
    """Delete a post.

    Raises:
        HTTPException: 404 if the post does not exist.
    """
    if not post_store.delete(post_id):
        raise HTTPException(status_code=404, detail=f"Post '{post_id}' not found")
    logger.info("post_deleted id=%s", post_id)

"""In-memory post repository (swap for a DB-backed store in production)."""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from typing import Any

from social_media_manager.api.schemas import Post, PostCreate, PostStatus


class PostStore:
    """Thread-safe, in-memory store for posts.

    This provides a functional reference implementation; a production
    deployment should replace it with a persistent backend behind the
    same interface.
    """

    def __init__(self) -> None:
        self._items: dict[str, Post] = {}
        self._lock = threading.RLock()

    def create(self, data: PostCreate) -> Post:
        """Persist a new post and return it."""
        now = datetime.now(UTC)
        post = Post(
            id=str(uuid.uuid4()),
            status=PostStatus.SCHEDULED if data.scheduled_at else PostStatus.DRAFT,
            created_at=now,
            updated_at=now,
            **data.model_dump(),
        )
        with self._lock:
            self._items[post.id] = post
        return post

    def get(self, post_id: str) -> Post | None:
        """Return a post by id, or ``None`` if not found."""
        with self._lock:
            return self._items.get(post_id)

    def list(self, limit: int = 50, offset: int = 0) -> tuple[list[Post], int]:
        """Return a page of posts ordered newest-first and the total count."""
        with self._lock:
            items = sorted(
                self._items.values(), key=lambda p: p.created_at, reverse=True
            )
        return items[offset : offset + limit], len(items)

    def delete(self, post_id: str) -> bool:
        """Delete a post; return whether it existed."""
        with self._lock:
            return self._items.pop(post_id, None) is not None

    def update_status(self, post_id: str, status: PostStatus) -> Post | None:
        """Update a post's status and return the updated post."""
        with self._lock:
            post = self._items.get(post_id)
            if post is None:
                return None
            updated = post.model_copy(
                update={"status": status, "updated_at": datetime.now(UTC)}
            )
            self._items[post_id] = updated
            return updated

    def all_posts(self) -> list[dict[str, Any]]:
        """Return every post as a plain dictionary (for analytics)."""
        with self._lock:
            return [p.model_dump() for p in self._items.values()]


post_store = PostStore()

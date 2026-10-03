"""Comment service for gated communities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class CommentServiceError(Exception):
    """Base exception for comment service errors."""


class CommentNotFoundError(CommentServiceError):
    """Raised when a comment cannot be found."""


class CommentValidationError(CommentServiceError):
    """Raised when comment data fails validation."""


@dataclass
class Comment:
    """Represents a comment in a gated community post."""

    id: str
    post_id: str
    author_id: str
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    parent_id: Optional[str] = None
    is_edited: bool = False
    is_deleted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize comment to dictionary."""
        return {
            "id": self.id,
            "post_id": self.post_id,
            "author_id": self.author_id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "parent_id": self.parent_id,
            "is_edited": self.is_edited,
            "is_deleted": self.is_deleted,
        }


class CommentService:
    """Service for managing comments on gated community posts."""

    def __init__(self) -> None:
        self._comments: Dict[str, Comment] = {}
        self._post_comments: Dict[str, List[str]] = {}

    def create_comment(self, data: Dict[str, Any]) -> Comment:
        """Create a new comment with validation.

        Args:
            data: Dictionary containing comment data. Required keys:
                - id: Unique comment identifier
                - post_id: ID of the post being commented on
                - author_id: ID of the comment author
                - content: Comment text content

        Returns:
            The created Comment instance.

        Raises:
            CommentValidationError: If required fields are missing or invalid.
        """
        required_fields = ["id", "post_id", "author_id", "content"]
        missing = [f for f in required_fields if f not in data or data[f] is None]
        if missing:
            raise CommentValidationError(
                f"Missing required fields: {', '.join(missing)}"
            )

        comment_id = str(data["id"])
        if comment_id in self._comments:
            raise CommentValidationError(f"Comment with id '{comment_id}' already exists")

        content = str(data["content"]).strip()
        if not content:
            raise CommentValidationError("Comment content cannot be empty")

        if len(content) > 10000:
            raise CommentValidationError("Comment content exceeds maximum length of 10000 characters")

        comment = Comment(
            id=comment_id,
            post_id=str(data["post_id"]),
            author_id=str(data["author_id"]),
            content=content,
            parent_id=str(data["parent_id"]) if data.get("parent_id") else None,
        )

        self._comments[comment_id] = comment
        self._post_comments.setdefault(comment.post_id, []).append(comment_id)

        return comment

    def get_comment(self, comment_id: str) -> Comment:
        """Get a comment by its ID.

        Args:
            comment_id: The unique identifier of the comment.

        Returns:
            The Comment instance.

        Raises:
            CommentNotFoundError: If no comment exists with the given ID.
            CommentValidationError: If comment_id is empty or invalid.
        """
        if not comment_id or not isinstance(comment_id, str):
            raise CommentValidationError("comment_id must be a non-empty string")

        comment = self._comments.get(comment_id)
        if comment is None:
            raise CommentNotFoundError(f"Comment with id '{comment_id}' not found")

        return comment

    def list_comments(self, post_id: str) -> List[Comment]:
        """List all comments for a given post.

        Args:
            post_id: The ID of the post to list comments for.

        Returns:
            List of Comment instances for the post, ordered by creation time.

        Raises:
            CommentValidationError: If post_id is empty or invalid.
        """
        if not post_id or not isinstance(post_id, str):
            raise CommentValidationError("post_id must be a non-empty string")

        comment_ids = self._post_comments.get(post_id, [])
        comments = [self._comments[cid] for cid in comment_ids if cid in self._comments]
        comments.sort(key=lambda c: c.created_at)

        return comments

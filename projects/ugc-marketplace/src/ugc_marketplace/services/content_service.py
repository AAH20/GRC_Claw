"""Content service for UGC marketplace operations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ContentType(str, Enum):
    """Supported content types."""

    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    AUDIO = "audio"


class ContentStatus(str, Enum):
    """Content lifecycle statuses."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class ContentValidationError(Exception):
    """Raised when content data fails validation."""

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        self.field = field
        super().__init__(message)


class ContentNotFoundError(Exception):
    """Raised when a content item cannot be found."""

    def __init__(self, content_id: str) -> None:
        self.content_id = content_id
        super().__init__(f"Content with id '{content_id}' not found")


@dataclass
class Content:
    """Represents a content item in the marketplace."""

    id: str
    title: str
    description: str
    content_type: ContentType
    status: ContentStatus
    creator_id: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PaginationParams:
    """Pagination parameters for list queries."""

    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be >= 1")
        if self.page_size < 1:
            raise ValueError("page_size must be >= 1")
        if self.page_size > 100:
            raise ValueError("page_size must be <= 100")


@dataclass
class ContentFilters:
    """Filters for listing content."""

    content_type: Optional[ContentType] = None
    status: Optional[ContentStatus] = None
    creator_id: Optional[str] = None
    tags: Optional[List[str]] = None
    search_query: Optional[str] = None


@dataclass
class PaginatedResult:
    """Paginated result wrapper."""

    items: List[Content]
    total: int
    page: int
    page_size: int
    total_pages: int


# In-memory store for demonstration — replace with real database in production
_content_store: Dict[str, Content] = {}


def _validate_content_data(data: Dict[str, Any]) -> None:
    """Validate raw content data before creation.

    Args:
        data: Dictionary containing content fields.

    Raises:
        ContentValidationError: If validation fails.
    """
    required_fields = ["title", "description", "content_type", "creator_id"]
    for req_field in required_fields:
        if req_field not in data or data[req_field] is None:
            raise ContentValidationError(
                f"Missing required field: {req_field}", field=req_field
            )

    title = data.get("title", "")
    if not isinstance(title, str) or len(title.strip()) == 0:
        raise ContentValidationError("title must be a non-empty string", field="title")
    if len(title) > 200:
        raise ContentValidationError(
            "title must be at most 200 characters", field="title"
        )

    description = data.get("description", "")
    if not isinstance(description, str) or len(description.strip()) == 0:
        raise ContentValidationError(
            "description must be a non-empty string", field="description"
        )
    if len(description) > 5000:
        raise ContentValidationError(
            "description must be at most 5000 characters", field="description"
        )

    content_type = data.get("content_type")
    if content_type not in [ct.value for ct in ContentType]:
        raise ContentValidationError(
            f"content_type must be one of: {[ct.value for ct in ContentType]}",
            field="content_type",
        )

    creator_id = data.get("creator_id", "")
    if not isinstance(creator_id, str) or len(creator_id.strip()) == 0:
        raise ContentValidationError(
            "creator_id must be a non-empty string", field="creator_id"
        )

    tags = data.get("tags", [])
    if tags is not None and not isinstance(tags, list):
        raise ContentValidationError("tags must be a list", field="tags")
    if tags is not None:
        for tag in tags:
            if not isinstance(tag, str):
                raise ContentValidationError(
                    "each tag must be a string", field="tags"
                )


def create_content(data: Dict[str, Any]) -> Content:
    """Create a new content item with validation.

    Args:
        data: Dictionary containing content fields:
            - title (str): Content title (required, max 200 chars)
            - description (str): Content description (required, max 5000 chars)
            - content_type (str): One of 'image', 'video', 'text', 'audio' (required)
            - creator_id (str): ID of the content creator (required)
            - tags (list[str]): Optional list of tags
            - metadata (dict): Optional metadata key-value pairs

    Returns:
        Content: The newly created content item.

    Raises:
        ContentValidationError: If the provided data fails validation.
    """
    _validate_content_data(data)

    content_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    content = Content(
        id=content_id,
        title=data["title"].strip(),
        description=data["description"].strip(),
        content_type=ContentType(data["content_type"]),
        status=ContentStatus.DRAFT,
        creator_id=data["creator_id"].strip(),
        tags=data.get("tags", []),
        metadata=data.get("metadata", {}),
        created_at=now,
        updated_at=now,
    )

    _content_store[content_id] = content
    return content


def get_content(content_id: str) -> Content:
    """Retrieve a content item by its ID.

    Args:
        content_id: The unique identifier of the content item.

    Returns:
        Content: The requested content item.

    Raises:
        ContentNotFoundError: If no content exists with the given ID.
        ValueError: If content_id is empty or not a string.
    """
    if not isinstance(content_id, str) or not content_id.strip():
        raise ValueError("content_id must be a non-empty string")

    content = _content_store.get(content_id)
    if content is None:
        raise ContentNotFoundError(content_id)

    return content


def list_content(
    filters: Optional[ContentFilters] = None,
    pagination: Optional[PaginationParams] = None,
) -> PaginatedResult:
    """List content items with optional filtering and pagination.

    Args:
        filters: Optional filters to apply (content_type, status, creator_id,
                 tags, search_query).
        pagination: Optional pagination parameters (page, page_size).

    Returns:
        PaginatedResult: Paginated list of matching content items.

    Raises:
        ValueError: If pagination parameters are invalid.
    """
    if filters is None:
        filters = ContentFilters()
    if pagination is None:
        pagination = PaginationParams()

    items = list(_content_store.values())

    # Apply filters
    if filters.content_type is not None:
        items = [c for c in items if c.content_type == filters.content_type]

    if filters.status is not None:
        items = [c for c in items if c.status == filters.status]

    if filters.creator_id is not None:
        items = [c for c in items if c.creator_id == filters.creator_id]

    if filters.tags:
        items = [
            c for c in items if any(tag in c.tags for tag in filters.tags)
        ]

    if filters.search_query:
        query = filters.search_query.lower()
        items = [
            c
            for c in items
            if query in c.title.lower() or query in c.description.lower()
        ]

    # Sort by creation date descending (newest first)
    items.sort(key=lambda c: c.created_at, reverse=True)

    total = len(items)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    # Apply pagination
    start = (pagination.page - 1) * pagination.page_size
    end = start + pagination.page_size
    paginated_items = items[start:end]

    return PaginatedResult(
        items=paginated_items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )

"""Community service for gated-communities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class CommunityError(Exception):
    """Base exception for community service errors."""


class ValidationError(CommunityError):
    """Raised when community data fails validation."""


class CommunityNotFoundError(CommunityError):
    """Raised when a community is not found."""


class CommunityStatus(str, Enum):
    """Community status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


@dataclass
class Community:
    """Represents a gated community."""

    id: str
    name: str
    description: str
    status: CommunityStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PaginationParams:
    """Pagination parameters."""

    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValidationError("page must be >= 1")
        if self.page_size < 1 or self.page_size > 100:
            raise ValidationError("page_size must be between 1 and 100")


@dataclass
class PaginatedResult:
    """Paginated result wrapper."""

    items: List[Community]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size


class CommunityService:
    """Service for managing gated communities."""

    def __init__(self) -> None:
        self._communities: Dict[str, Community] = {}

    def create_community(self, data: Dict[str, Any]) -> Community:
        """Create a new community with validation.

        Args:
            data: Dictionary containing community data.
                Required keys: name, description
                Optional keys: status, metadata

        Returns:
            The created Community instance.

        Raises:
            ValidationError: If required fields are missing or invalid.
        """
        if not isinstance(data, dict):
            raise ValidationError("data must be a dictionary")

        name = data.get("name")
        if not name or not isinstance(name, str):
            raise ValidationError("name is required and must be a non-empty string")
        if len(name.strip()) == 0:
            raise ValidationError("name cannot be whitespace only")
        if len(name) > 255:
            raise ValidationError("name must be 255 characters or fewer")

        description = data.get("description")
        if not description or not isinstance(description, str):
            raise ValidationError("description is required and must be a non-empty string")
        if len(description.strip()) == 0:
            raise ValidationError("description cannot be whitespace only")
        if len(description) > 5000:
            raise ValidationError("description must be 5000 characters or fewer")

        status_str = data.get("status", CommunityStatus.ACTIVE.value)
        try:
            status = CommunityStatus(status_str)
        except ValueError:
            valid = ", ".join(s.value for s in CommunityStatus)
            raise ValidationError(f"status must be one of: {valid}")

        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValidationError("metadata must be a dictionary")

        now = datetime.now(timezone.utc)
        community = Community(
            id=str(uuid.uuid4()),
            name=name.strip(),
            description=description.strip(),
            status=status,
            created_at=now,
            updated_at=now,
            metadata=dict(metadata),
        )

        self._communities[community.id] = community
        return community

    def get_community(self, community_id: str) -> Community:
        """Get a community by its ID.

        Args:
            community_id: The unique identifier of the community.

        Returns:
            The Community instance.

        Raises:
            ValidationError: If community_id is empty or invalid.
            CommunityNotFoundError: If no community exists with the given ID.
        """
        if not community_id or not isinstance(community_id, str):
            raise ValidationError("community_id is required and must be a non-empty string")

        community = self._communities.get(community_id)
        if community is None:
            raise CommunityNotFoundError(f"Community not found: {community_id}")

        return community

    def list_communities(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> PaginatedResult:
        """List communities with optional filtering and pagination.

        Args:
            filters: Optional filter criteria.
                Supported keys: status, name_contains
            pagination: Optional pagination parameters.

        Returns:
            PaginatedResult containing the filtered, paginated communities.
        """
        filters = filters or {}
        pagination = pagination or PaginationParams()

        communities = list(self._communities.values())

        status_filter = filters.get("status")
        if status_filter is not None:
            try:
                status_enum = CommunityStatus(status_filter)
            except ValueError:
                valid = ", ".join(s.value for s in CommunityStatus)
                raise ValidationError(f"status filter must be one of: {valid}")
            communities = [c for c in communities if c.status == status_enum]

        name_contains = filters.get("name_contains")
        if name_contains is not None:
            if not isinstance(name_contains, str):
                raise ValidationError("name_contains filter must be a string")
            search = name_contains.lower()
            communities = [c for c in communities if search in c.name.lower()]

        total = len(communities)

        start = (pagination.page - 1) * pagination.page_size
        end = start + pagination.page_size
        paginated = communities[start:end]

        return PaginatedResult(
            items=paginated,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

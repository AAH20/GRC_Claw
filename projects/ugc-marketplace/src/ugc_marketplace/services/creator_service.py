"""Creator service for ugc-marketplace."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class CreatorValidationError(Exception):
    """Raised when creator data fails validation."""


class CreatorNotFoundError(Exception):
    """Raised when a creator is not found."""


class CreatorService:
    """Service for managing creators."""

    def __init__(self, db: Any = None) -> None:
        """Initialize the creator service.

        Args:
            db: Database session or repository instance.
        """
        self._db = db
        self._creators: Dict[str, Dict[str, Any]] = {}

    def create_creator(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new creator with validation.

        Args:
            data: Creator data containing at minimum 'name' and 'email'.

        Returns:
            The created creator record.

        Raises:
            CreatorValidationError: If required fields are missing or invalid.
        """
        if not isinstance(data, dict):
            raise CreatorValidationError("Creator data must be a dictionary")

        name = data.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            raise CreatorValidationError("Creator name is required and must be a non-empty string")

        email = data.get("email")
        if not email or not isinstance(email, str) or "@" not in email:
            raise CreatorValidationError("A valid email address is required")

        creator_id = str(uuid4())
        creator = {
            "id": creator_id,
            "name": name.strip(),
            "email": email.strip().lower(),
            "bio": data.get("bio", ""),
            "avatar_url": data.get("avatar_url", ""),
            "is_active": data.get("is_active", True),
            "metadata": data.get("metadata", {}),
        }

        self._creators[creator_id] = creator
        return creator

    def get_creator(self, creator_id: str) -> Dict[str, Any]:
        """Get a creator by ID.

        Args:
            creator_id: The unique identifier of the creator.

        Returns:
            The creator record.

        Raises:
            CreatorNotFoundError: If no creator exists with the given ID.
            CreatorValidationError: If creator_id is empty or invalid.
        """
        if not creator_id or not isinstance(creator_id, str):
            raise CreatorValidationError("A valid creator ID is required")

        creator = self._creators.get(creator_id)
        if creator is None:
            raise CreatorNotFoundError(f"Creator with ID '{creator_id}' not found")

        return creator

    def list_creators(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """List creators with optional filtering and pagination.

        Args:
            filters: Optional filters (e.g., {'is_active': True, 'name': 'John'}).
            pagination: Optional pagination params ('page', 'per_page').

        Returns:
            A dict with 'items', 'total', 'page', and 'per_page'.
        """
        filters = filters or {}
        pagination = pagination or {}

        page = max(1, int(pagination.get("page", 1)))
        per_page = min(100, max(1, int(pagination.get("per_page", 20))))

        results: List[Dict[str, Any]] = list(self._creators.values())

        if "is_active" in filters:
            results = [c for c in results if c["is_active"] == filters["is_active"]]
        if "name" in filters:
            name_filter = filters["name"].lower()
            results = [c for c in results if name_filter in c["name"].lower()]
        if "email" in filters:
            email_filter = filters["email"].lower()
            results = [c for c in results if email_filter in c["email"].lower()]

        total = len(results)
        start = (page - 1) * per_page
        end = start + per_page
        items = results[start:end]

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

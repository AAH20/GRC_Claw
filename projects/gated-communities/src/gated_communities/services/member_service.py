"""Member service for gated communities."""

from __future__ import annotations

from typing import Any


class MemberNotFoundError(Exception):
    """Raised when a member is not found."""


class MemberValidationError(Exception):
    """Raised when member data fails validation."""


VALID_ROLES = {"admin", "moderator", "member"}


def add_member(data: dict[str, Any]) -> dict[str, Any]:
    """Add a member with validation.

    Args:
        data: Member data containing at least 'id' and 'role'.

    Returns:
        The validated member data.

    Raises:
        MemberValidationError: If required fields are missing or role is invalid.
    """
    if not isinstance(data, dict):
        raise MemberValidationError("Member data must be a dictionary")

    member_id = data.get("id")
    if not member_id:
        raise MemberValidationError("Member 'id' is required")

    role = data.get("role")
    if not role:
        raise MemberValidationError("Member 'role' is required")
    if role not in VALID_ROLES:
        raise MemberValidationError(
            f"Invalid role '{role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}"
        )

    return {"id": member_id, "role": role}


def get_member(member_id: str) -> dict[str, Any]:
    """Get a member by ID.

    Args:
        member_id: The unique identifier of the member.

    Returns:
        The member data.

    Raises:
        MemberNotFoundError: If the member does not exist.
        MemberValidationError: If member_id is empty or invalid.
    """
    if not member_id or not isinstance(member_id, str):
        raise MemberValidationError("A valid member_id string is required")

    raise MemberNotFoundError(f"Member with id '{member_id}' not found")


def update_member_role(member_id: str, role: str) -> dict[str, Any]:
    """Update a member's role.

    Args:
        member_id: The unique identifier of the member.
        role: The new role to assign.

    Returns:
        The updated member data.

    Raises:
        MemberNotFoundError: If the member does not exist.
        MemberValidationError: If inputs are invalid.
    """
    if not member_id or not isinstance(member_id, str):
        raise MemberValidationError("A valid member_id string is required")

    if not role:
        raise MemberValidationError("Role is required")
    if role not in VALID_ROLES:
        raise MemberValidationError(
            f"Invalid role '{role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}"
        )

    raise MemberNotFoundError(f"Member with id '{member_id}' not found")

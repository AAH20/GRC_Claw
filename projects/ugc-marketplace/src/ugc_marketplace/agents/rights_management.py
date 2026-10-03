"""Rights Management Agent for UGC Marketplace.

Handles access control decisions and rights grants for content assets.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------


class RightType(str, Enum):
    """Types of rights that can be granted on content."""

    VIEW = "view"
    DOWNLOAD = "download"
    EDIT = "edit"
    DELETE = "delete"
    SHARE = "share"
    COMMERCIAL_USE = "commercial_use"
    ATTRIBUTION = "attribution"


class AccessDecision(str, Enum):
    """Possible outcomes of a rights check."""

    ALLOWED = "allowed"
    DENIED = "denied"
    PENDING = "pending"
    EXPIRED = "expired"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class RightsRecord:
    """Represents a single rights grant."""

    content_id: str
    user_id: str
    rights: set[RightType]
    granted_by: str
    granted_at: datetime
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_active(self) -> bool:
        """Check if the rights grant is still valid (not expired)."""
        if self.expires_at is None:
            return True
        return datetime.now(timezone.utc) < self.expires_at


@dataclass
class AccessCheckResult:
    """Result of a rights check operation."""

    content_id: str
    user_id: str
    decision: AccessDecision
    granted_rights: set[RightType]
    reason: str
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class GrantResult:
    """Result of a rights grant operation."""

    success: bool
    grant_id: str
    content_id: str
    user_id: str
    rights: set[RightType]
    message: str
    granted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

# Simulated content ownership registry
_MOCK_CONTENT_OWNERS: dict[str, str] = {
    "content-001": "user-admin-01",
    "content-002": "user-creator-42",
    "content-003": "user-creator-42",
    "content-004": "user-admin-01",
    "content-005": "user-creator-99",
}

# Simulated rights grants: (content_id, user_id) -> RightsRecord
_MOCK_RIGHTS_DB: dict[tuple[str, str], RightsRecord] = {
    ("content-001", "user-viewer-10"): RightsRecord(
        content_id="content-001",
        user_id="user-viewer-10",
        rights={RightType.VIEW, RightType.DOWNLOAD},
        granted_by="user-admin-01",
        granted_at=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        expires_at=datetime(2027, 9, 1, 10, 0, tzinfo=timezone.utc),
    ),
    ("content-002", "user-viewer-10"): RightsRecord(
        content_id="content-002",
        user_id="user-viewer-10",
        rights={RightType.VIEW},
        granted_by="user-creator-42",
        granted_at=datetime(2026, 9, 15, 14, 30, tzinfo=timezone.utc),
        expires_at=datetime(2026, 10, 15, 14, 30, tzinfo=timezone.utc),
    ),
    ("content-003", "user-editor-77"): RightsRecord(
        content_id="content-003",
        user_id="user-editor-77",
        rights={RightType.VIEW, RightType.EDIT, RightType.SHARE},
        granted_by="user-creator-42",
        granted_at=datetime(2026, 8, 20, 9, 0, tzinfo=timezone.utc),
        expires_at=None,
    ),
    ("content-004", "user-commercial-55"): RightsRecord(
        content_id="content-004",
        user_id="user-commercial-55",
        rights={
            RightType.VIEW,
            RightType.DOWNLOAD,
            RightType.COMMERCIAL_USE,
            RightType.ATTRIBUTION,
        },
        granted_by="user-admin-01",
        granted_at=datetime(2026, 7, 1, 0, 0, tzinfo=timezone.utc),
        expires_at=datetime(2027, 7, 1, 0, 0, tzinfo=timezone.utc),
        metadata={"license_type": "commercial", "territory": "worldwide"},
    ),
}

# Simulated pending approval requests
_MOCK_PENDING_REQUESTS: set[tuple[str, str]] = {
    ("content-005", "user-viewer-10"),
}


# ---------------------------------------------------------------------------
# Rights Management Agent
# ---------------------------------------------------------------------------


class RightsManagementAgent:
    """Agent responsible for checking and granting content rights."""

    def __init__(self) -> None:
        """Initialize the rights management agent."""
        self._content_owners = _MOCK_CONTENT_OWNERS.copy()
        self._rights_db = _MOCK_RIGHTS_DB.copy()
        self._pending_requests = _MOCK_PENDING_REQUESTS.copy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_rights(
        self,
        content_id: str,
        user_id: str,
        required_right: RightType = RightType.VIEW,
    ) -> AccessCheckResult:
        """Check whether a user has the required right on a content asset.

        Args:
            content_id: Unique identifier of the content asset.
            user_id: Unique identifier of the user requesting access.
            required_right: The specific right being requested (default: VIEW).

        Returns:
            AccessCheckResult with the decision and supporting details.
        """
        now = datetime.now(timezone.utc)

        # Check if there is a pending approval request
        if (content_id, user_id) in self._pending_requests:
            return AccessCheckResult(
                content_id=content_id,
                user_id=user_id,
                decision=AccessDecision.PENDING,
                granted_rights=set(),
                reason="Access request is pending approval from content owner.",
                checked_at=now,
            )

        # Check if user is the content owner (owners have all rights)
        owner_id = self._content_owners.get(content_id)
        if owner_id == user_id:
            return AccessCheckResult(
                content_id=content_id,
                user_id=user_id,
                decision=AccessDecision.ALLOWED,
                granted_rights=set(RightType),
                reason="User is the content owner.",
                checked_at=now,
            )

        # Look up existing rights grant
        record = self._rights_db.get((content_id, user_id))
        if record is None:
            return AccessCheckResult(
                content_id=content_id,
                user_id=user_id,
                decision=AccessDecision.DENIED,
                granted_rights=set(),
                reason="No rights grant found for this user on this content.",
                checked_at=now,
            )

        # Check expiration
        if not record.is_active():
            return AccessCheckResult(
                content_id=content_id,
                user_id=user_id,
                decision=AccessDecision.EXPIRED,
                granted_rights=record.rights,
                reason=f"Rights grant expired on {record.expires_at.isoformat()}.",
                checked_at=now,
            )

        # Check if the required right is in the granted set
        if required_right not in record.rights:
            return AccessCheckResult(
                content_id=content_id,
                user_id=user_id,
                decision=AccessDecision.DENIED,
                granted_rights=record.rights,
                reason=(
                    f"User does not have '{required_right.value}' right. "
                    f"Granted rights: {[r.value for r in record.rights]}."
                ),
                checked_at=now,
            )

        # All checks passed
        return AccessCheckResult(
            content_id=content_id,
            user_id=user_id,
            decision=AccessDecision.ALLOWED,
            granted_rights=record.rights,
            reason=f"User has '{required_right.value}' right on this content.",
            checked_at=now,
        )

    def grant_rights(
        self,
        content_id: str,
        user_id: str,
        rights: set[RightType],
        *,
        granted_by: str | None = None,
        duration_days: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GrantResult:
        """Grant specific rights on a content asset to a user.

        Args:
            content_id: Unique identifier of the content asset.
            user_id: Unique identifier of the user receiving the rights.
            rights: Set of RightType values to grant.
            granted_by: User ID of the grantor (defaults to content owner).
            duration_days: Optional expiration period in days.
            metadata: Optional additional metadata for the grant.

        Returns:
            GrantResult indicating success or failure with details.
        """
        now = datetime.now(timezone.utc)

        # Validate inputs
        if not rights:
            return GrantResult(
                success=False,
                grant_id="",
                content_id=content_id,
                user_id=user_id,
                rights=set(),
                message="At least one right must be specified.",
                granted_at=now,
            )

        # Determine the grantor
        if granted_by is None:
            granted_by = self._content_owners.get(content_id, "system")

        # Calculate expiration
        expires_at: datetime | None = None
        if duration_days is not None:
            if duration_days <= 0:
                return GrantResult(
                    success=False,
                    grant_id="",
                    content_id=content_id,
                    user_id=user_id,
                    rights=rights,
                    message="duration_days must be a positive integer.",
                    granted_at=now,
                )
            expires_at = now + timedelta(days=duration_days)

        # Create the rights record
        grant_id = str(uuid.uuid4())
        record = RightsRecord(
            content_id=content_id,
            user_id=user_id,
            rights=rights.copy(),
            granted_by=granted_by,
            granted_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        # Store the grant
        self._rights_db[(content_id, user_id)] = record

        # Remove from pending if it was there
        self._pending_requests.discard((content_id, user_id))

        rights_str = ", ".join(sorted(r.value for r in rights))
        expiry_str = (
            f" (expires {expires_at.isoformat()})" if expires_at else " (no expiration)"
        )
        message = (
            f"Granted rights [{rights_str}] to {user_id} on {content_id}"
            f"{expiry_str}."
        )

        return GrantResult(
            success=True,
            grant_id=grant_id,
            content_id=content_id,
            user_id=user_id,
            rights=rights.copy(),
            message=message,
            granted_at=now,
        )

    # ------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------

    def revoke_rights(
        self,
        content_id: str,
        user_id: str,
        rights: set[RightType] | None = None,
    ) -> bool:
        """Revoke rights from a user on a content asset.

        Args:
            content_id: Unique identifier of the content asset.
            user_id: Unique identifier of the user.
            rights: Specific rights to revoke. If None, revokes all rights.

        Returns:
            True if revocation was successful, False otherwise.
        """
        key = (content_id, user_id)
        record = self._rights_db.get(key)
        if record is None:
            return False

        if rights is None:
            # Revoke all rights
            del self._rights_db[key]
        else:
            # Revoke specific rights
            record.rights -= rights
            if not record.rights:
                del self._rights_db[key]

        return True

    def list_user_rights(self, user_id: str) -> list[AccessCheckResult]:
        """List all active rights for a given user.

        Args:
            user_id: Unique identifier of the user.

        Returns:
            List of AccessCheckResult for each content the user has rights on.
        """
        results: list[AccessCheckResult] = []
        for (cid, uid), record in self._rights_db.items():
            if uid == user_id and record.is_active():
                results.append(
                    AccessCheckResult(
                        content_id=cid,
                        user_id=uid,
                        decision=AccessDecision.ALLOWED,
                        granted_rights=record.rights,
                        reason="Active rights grant.",
                    )
                )
        return results


# ---------------------------------------------------------------------------
# Module-level convenience functions (stateless facade)
# ---------------------------------------------------------------------------

_default_agent = RightsManagementAgent()


def check_rights(
    content_id: str,
    user_id: str,
    required_right: RightType = RightType.VIEW,
) -> AccessCheckResult:
    """Check whether a user has the required right on a content asset.

    Args:
        content_id: Unique identifier of the content asset.
        user_id: Unique identifier of the user requesting access.
        required_right: The specific right being requested (default: VIEW).

    Returns:
        AccessCheckResult with the decision and supporting details.
    """
    return _default_agent.check_rights(content_id, user_id, required_right)


def grant_rights(
    content_id: str,
    user_id: str,
    rights: set[RightType],
    *,
    granted_by: str | None = None,
    duration_days: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> GrantResult:
    """Grant specific rights on a content asset to a user.

    Args:
        content_id: Unique identifier of the content asset.
        user_id: Unique identifier of the user receiving the rights.
        rights: Set of RightType values to grant.
        granted_by: User ID of the grantor (defaults to content owner).
        duration_days: Optional expiration period in days.
        metadata: Optional additional metadata for the grant.

    Returns:
        GrantResult indicating success or failure with details.
    """
    return _default_agent.grant_rights(
        content_id,
        user_id,
        rights,
        granted_by=granted_by,
        duration_days=duration_days,
        metadata=metadata,
    )

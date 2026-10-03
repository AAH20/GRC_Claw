"""Access Control Agent for Gated Communities.

Provides member access decisions and permission grants for community resources.
Uses realistic mock data for demonstration and testing purposes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Set


class Permission(str, Enum):
    """Available permission levels for community resources."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    MODERATE = "moderate"


class AccessDecision(str, Enum):
    """Possible outcomes of an access check."""

    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    EXPIRED = "expired"


@dataclass
class Member:
    """Represents a community member."""

    member_id: str
    name: str
    email: str
    role: str
    is_active: bool = True
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Resource:
    """Represents a gated community resource."""

    resource_id: str
    name: str
    resource_type: str
    owner_id: str
    required_permission: Permission = Permission.READ
    is_public: bool = False


@dataclass
class AccessGrant:
    """Represents an access grant for a member to a resource."""

    grant_id: str
    member_id: str
    resource_id: str
    permissions: Set[Permission]
    granted_at: datetime
    expires_at: Optional[datetime]
    granted_by: str


@dataclass
class AccessResult:
    """Result of an access check."""

    decision: AccessDecision
    member_id: str
    resource: str
    permissions: Set[Permission]
    reason: str
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Mock Data ───────────────────────────────────────────────────────────────

MOCK_MEMBERS: Dict[str, Member] = {
    "mbr_001": Member(
        member_id="mbr_001",
        name="Alice Chen",
        email="alice.chen@example.com",
        role="admin",
        joined_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
    ),
    "mbr_002": Member(
        member_id="mbr_002",
        name="Bob Martinez",
        email="bob.martinez@example.com",
        role="moderator",
        joined_at=datetime(2024, 3, 22, 14, 0, tzinfo=timezone.utc),
    ),
    "mbr_003": Member(
        member_id="mbr_003",
        name="Carol Williams",
        email="carol.williams@example.com",
        role="member",
        joined_at=datetime(2024, 6, 10, 9, 15, tzinfo=timezone.utc),
    ),
    "mbr_004": Member(
        member_id="mbr_004",
        name="David Kim",
        email="david.kim@example.com",
        role="member",
        is_active=False,
        joined_at=datetime(2024, 8, 5, 16, 45, tzinfo=timezone.utc),
    ),
    "mbr_005": Member(
        member_id="mbr_005",
        name="Elena Rodriguez",
        email="elena.rodriguez@example.com",
        role="member",
        joined_at=datetime(2025, 1, 20, 11, 0, tzinfo=timezone.utc),
    ),
}

MOCK_RESOURCES: Dict[str, Resource] = {
    "res_001": Resource(
        resource_id="res_001",
        name="General Discussion Forum",
        resource_type="forum",
        owner_id="mbr_001",
        required_permission=Permission.READ,
        is_public=True,
    ),
    "res_002": Resource(
        resource_id="res_002",
        name="Premium Content Library",
        resource_type="library",
        owner_id="mbr_001",
        required_permission=Permission.READ,
        is_public=False,
    ),
    "res_003": Resource(
        resource_id="res_003",
        name="Admin Dashboard",
        resource_type="dashboard",
        owner_id="mbr_001",
        required_permission=Permission.ADMIN,
        is_public=False,
    ),
    "res_004": Resource(
        resource_id="res_004",
        name="Moderation Queue",
        resource_type="queue",
        owner_id="mbr_002",
        required_permission=Permission.MODERATE,
        is_public=False,
    ),
    "res_005": Resource(
        resource_id="res_005",
        name="Community Wiki",
        resource_type="wiki",
        owner_id="mbr_001",
        required_permission=Permission.WRITE,
        is_public=False,
    ),
}

MOCK_GRANTS: Dict[str, List[AccessGrant]] = {
    "mbr_001": [
        AccessGrant(
            grant_id="grnt_001",
            member_id="mbr_001",
            resource_id="res_001",
            permissions={Permission.READ, Permission.WRITE, Permission.ADMIN},
            granted_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            expires_at=None,
            granted_by="system",
        ),
        AccessGrant(
            grant_id="grnt_002",
            member_id="mbr_001",
            resource_id="res_002",
            permissions={Permission.READ, Permission.WRITE, Permission.ADMIN},
            granted_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            expires_at=None,
            granted_by="system",
        ),
        AccessGrant(
            grant_id="grnt_003",
            member_id="mbr_001",
            resource_id="res_003",
            permissions={Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN},
            granted_at=datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc),
            expires_at=None,
            granted_by="system",
        ),
    ],
    "mbr_002": [
        AccessGrant(
            grant_id="grnt_004",
            member_id="mbr_002",
            resource_id="res_001",
            permissions={Permission.READ, Permission.WRITE, Permission.MODERATE},
            granted_at=datetime(2024, 3, 22, 14, 0, tzinfo=timezone.utc),
            expires_at=None,
            granted_by="mbr_001",
        ),
        AccessGrant(
            grant_id="grnt_005",
            member_id="mbr_002",
            resource_id="res_004",
            permissions={Permission.READ, Permission.WRITE, Permission.MODERATE},
            granted_at=datetime(2024, 3, 22, 14, 0, tzinfo=timezone.utc),
            expires_at=None,
            granted_by="mbr_001",
        ),
    ],
    "mbr_003": [
        AccessGrant(
            grant_id="grnt_006",
            member_id="mbr_003",
            resource_id="res_001",
            permissions={Permission.READ},
            granted_at=datetime(2024, 6, 10, 9, 15, tzinfo=timezone.utc),
            expires_at=datetime(2025, 6, 10, 9, 15, tzinfo=timezone.utc),
            granted_by="mbr_001",
        ),
        AccessGrant(
            grant_id="grnt_007",
            member_id="mbr_003",
            resource_id="res_002",
            permissions={Permission.READ},
            granted_at=datetime(2024, 6, 10, 9, 15, tzinfo=timezone.utc),
            expires_at=datetime(2025, 6, 10, 9, 15, tzinfo=timezone.utc),
            granted_by="mbr_001",
        ),
    ],
    "mbr_005": [
        AccessGrant(
            grant_id="grnt_008",
            member_id="mbr_005",
            resource_id="res_001",
            permissions={Permission.READ},
            granted_at=datetime(2025, 1, 20, 11, 0, tzinfo=timezone.utc),
            expires_at=None,
            granted_by="mbr_001",
        ),
    ],
}


class AccessControlAgent:
    """Agent that manages access control for gated communities."""

    def __init__(
        self,
        members: Optional[Dict[str, Member]] = None,
        resources: Optional[Dict[str, Resource]] = None,
        grants: Optional[Dict[str, List[AccessGrant]]] = None,
    ) -> None:
        """Initialize the access control agent with mock or custom data."""
        self._members: Dict[str, Member] = members if members is not None else MOCK_MEMBERS
        self._resources: Dict[str, Resource] = resources if resources is not None else MOCK_RESOURCES
        self._grants: Dict[str, List[AccessGrant]] = grants if grants is not None else MOCK_GRANTS

    def check_access(self, member_id: str, resource: str) -> AccessResult:
        """Check whether a member has access to a resource.

        Args:
            member_id: The unique identifier of the member.
            resource: The resource identifier or name to check access against.

        Returns:
            AccessResult with the decision, permissions, and reason.
        """
        now = datetime.now(timezone.utc)

        # Validate member exists
        member = self._members.get(member_id)
        if member is None:
            return AccessResult(
                decision=AccessDecision.DENIED,
                member_id=member_id,
                resource=resource,
                permissions=set(),
                reason=f"Member '{member_id}' not found in the community.",
                checked_at=now,
            )

        # Validate member is active
        if not member.is_active:
            return AccessResult(
                decision=AccessDecision.DENIED,
                member_id=member_id,
                resource=resource,
                permissions=set(),
                reason=f"Member '{member.name}' is currently suspended/inactive.",
                checked_at=now,
            )

        # Resolve resource by ID or name
        target_resource = self._resolve_resource(resource)
        if target_resource is None:
            return AccessResult(
                decision=AccessDecision.DENIED,
                member_id=member_id,
                resource=resource,
                permissions=set(),
                reason=f"Resource '{resource}' not found.",
                checked_at=now,
            )

        # Public resources grant READ to all active members
        if target_resource.is_public and target_resource.required_permission == Permission.READ:
            return AccessResult(
                decision=AccessDecision.GRANTED,
                member_id=member_id,
                resource=target_resource.name,
                permissions={Permission.READ},
                reason="Resource is public; read access granted to all active members.",
                checked_at=now,
            )

        # Check existing grants
        member_grants = self._grants.get(member_id, [])
        for grant in member_grants:
            if grant.resource_id != target_resource.resource_id:
                continue

            # Check expiration
            if grant.expires_at is not None and grant.expires_at < now:
                return AccessResult(
                    decision=AccessDecision.EXPIRED,
                    member_id=member_id,
                    resource=target_resource.name,
                    permissions=grant.permissions,
                    reason=f"Access grant '{grant.grant_id}' expired on {grant.expires_at.isoformat()}.",
                    checked_at=now,
                )

            # Check if grant covers the required permission
            if target_resource.required_permission in grant.permissions:
                return AccessResult(
                    decision=AccessDecision.GRANTED,
                    member_id=member_id,
                    resource=target_resource.name,
                    permissions=grant.permissions,
                    reason=f"Access granted via grant '{grant.grant_id}'.",
                    checked_at=now,
                )

            # Grant exists but lacks the required permission level
            return AccessResult(
                decision=AccessDecision.DENIED,
                member_id=member_id,
                resource=target_resource.name,
                permissions=grant.permissions,
                reason=(
                    f"Existing grant '{grant.grant_id}' does not include "
                    f"required permission '{target_resource.required_permission.value}'."
                ),
                checked_at=now,
            )

        # No grant found
        return AccessResult(
            decision=AccessDecision.DENIED,
            member_id=member_id,
            resource=target_resource.name,
            permissions=set(),
            reason=f"No access grant found for member '{member.name}' on resource '{target_resource.name}'.",
            checked_at=now,
        )

    def grant_access(
        self,
        member_id: str,
        resource: str,
        permissions: List[Permission],
        granted_by: str = "system",
        duration_days: Optional[int] = 365,
    ) -> AccessGrant:
        """Grant access to a resource for a member.

        Args:
            member_id: The unique identifier of the member receiving access.
            resource: The resource identifier or name to grant access to.
            permissions: List of permissions to grant.
            granted_by: Identifier of the entity granting access.
            duration_days: Number of days until the grant expires. None means no expiration.

        Returns:
            The created AccessGrant.

        Raises:
            ValueError: If the member or resource does not exist, or if permissions is empty.
        """
        # Validate member
        member = self._members.get(member_id)
        if member is None:
            raise ValueError(f"Cannot grant access: member '{member_id}' not found.")

        # Resolve resource
        target_resource = self._resolve_resource(resource)
        if target_resource is None:
            raise ValueError(f"Cannot grant access: resource '{resource}' not found.")

        # Validate permissions
        if not permissions:
            raise ValueError("At least one permission must be specified.")

        # Deduplicate permissions
        unique_permissions: Set[Permission] = set(permissions)

        # Calculate expiration
        now = datetime.now(timezone.utc)
        expires_at: Optional[datetime] = None
        if duration_days is not None:
            expires_at = now + timedelta(days=duration_days)

        # Create the grant
        grant = AccessGrant(
            grant_id=f"grnt_{uuid.uuid4().hex[:8]}",
            member_id=member_id,
            resource_id=target_resource.resource_id,
            permissions=unique_permissions,
            granted_at=now,
            expires_at=expires_at,
            granted_by=granted_by,
        )

        # Store the grant
        if member_id not in self._grants:
            self._grants[member_id] = []
        self._grants[member_id].append(grant)

        return grant

    def revoke_access(self, member_id: str, resource: str) -> bool:
        """Revoke all access grants for a member on a resource.

        Args:
            member_id: The unique identifier of the member.
            resource: The resource identifier or name.

        Returns:
            True if any grants were removed, False otherwise.
        """
        target_resource = self._resolve_resource(resource)
        if target_resource is None:
            return False

        member_grants = self._grants.get(member_id, [])
        original_count = len(member_grants)
        self._grants[member_id] = [
            g for g in member_grants if g.resource_id != target_resource.resource_id
        ]
        return len(self._grants[member_id]) < original_count

    def list_member_grants(self, member_id: str) -> List[AccessGrant]:
        """List all access grants for a member.

        Args:
            member_id: The unique identifier of the member.

        Returns:
            List of AccessGrant objects for the member.
        """
        return list(self._grants.get(member_id, []))

    def _resolve_resource(self, resource: str) -> Optional[Resource]:
        """Resolve a resource by ID or by name.

        Args:
            resource: Resource identifier or name.

        Returns:
            The matching Resource, or None if not found.
        """
        # Try direct ID lookup first
        if resource in self._resources:
            return self._resources[resource]

        # Try name lookup (case-insensitive)
        resource_lower = resource.lower()
        for res in self._resources.values():
            if res.name.lower() == resource_lower:
                return res

        return None

"""Role-Based Access Control (RBAC) and Policy-Based Access Control (PBAC).

Provides role management, permission evaluation, policy enforcement,
and attribute-based access control for agentic AI marketing security.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set, Tuple, Union


class AccessDecision(Enum):
    """Access decision outcomes."""

    ALLOW = auto()
    DENY = auto()
    ABSTAIN = auto()


class Effect(Enum):
    """Policy effect."""

    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class Resource:
    """Resource identifier."""

    type: str
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.type}:{self.name}"


@dataclass(frozen=True)
class Action:
    """Action identifier."""

    verb: str
    resource: Resource

    def __str__(self) -> str:
        return f"{self.verb}:{self.resource}"


@dataclass(frozen=True)
class Role:
    """Role definition."""

    name: str
    description: str
    permissions: FrozenSet[str]
    parent_roles: FrozenSet[str] = frozenset()
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_all_permissions(self, role_registry: "RoleRegistry") -> Set[str]:
        """Get all permissions including inherited from parent roles."""
        all_perms = set(self.permissions)
        for parent_name in self.parent_roles:
            parent = role_registry.get_role(parent_name)
            if parent:
                all_perms.update(parent.get_all_permissions(role_registry))
        return all_perms


@dataclass(frozen=True)
class User:
    """User identity."""

    id: str
    name: str
    roles: FrozenSet[str] = frozenset()
    attributes: Dict[str, Any] = field(default_factory=dict)
    groups: FrozenSet[str] = frozenset()


@dataclass(frozen=True)
class Group:
    """Group definition."""

    name: str
    roles: FrozenSet[str] = frozenset()
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Policy:
    """Access control policy."""

    name: str
    description: str
    effect: Effect
    subjects: FrozenSet[str]
    actions: FrozenSet[str]
    resources: FrozenSet[str]
    conditions: Tuple[Callable[..., bool], ...] = ()
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches_subject(self, subject: str) -> bool:
        """Check if the policy applies to the given subject."""
        return subject in self.subjects or "*" in self.subjects

    def matches_action(self, action: str) -> bool:
        """Check if the policy applies to the given action."""
        return action in self.actions or "*" in self.actions

    def matches_resource(self, resource: str) -> bool:
        """Check if the policy applies to the given resource."""
        return resource in self.resources or "*" in self.resources

    def evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """Evaluate all policy conditions."""
        return all(condition(context) for condition in self.conditions)


class RoleRegistry:
    """Registry for role definitions."""

    def __init__(self) -> None:
        self._roles: Dict[str, Role] = {}

    def register_role(self, role: Role) -> None:
        """Register a role."""
        self._roles[role.name] = role

    def get_role(self, name: str) -> Optional[Role]:
        """Get a role by name."""
        return self._roles.get(name)

    def remove_role(self, name: str) -> None:
        """Remove a role."""
        self._roles.pop(name, None)

    def list_roles(self) -> List[Role]:
        """List all registered roles."""
        return list(self._roles.values())

    def validate_role_hierarchy(self) -> None:
        """Validate that role hierarchy has no cycles."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def _visit(role_name: str) -> None:
            visited.add(role_name)
            rec_stack.add(role_name)
            role = self._roles.get(role_name)
            if role:
                for parent in role.parent_roles:
                    if parent not in visited:
                        _visit(parent)
                    elif parent in rec_stack:
                        raise ValueError(
                            f"Cycle detected in role hierarchy: {role_name} -> {parent}"
                        )
            rec_stack.discard(role_name)

        for role_name in self._roles:
            if role_name not in visited:
                _visit(role_name)


class RBACEngine:
    """Role-Based Access Control engine."""

    def __init__(self, role_registry: RoleRegistry) -> None:
        self.role_registry = role_registry
        self._user_roles: Dict[str, Set[str]] = {}
        self._group: Dict[str, Group] = {}

    def assign_role(self, user_id: str, role_name: str) -> None:
        """Assign a role to a user."""
        if not self.role_registry.get_role(role_name):
            raise ValueError(f"Role '{role_name}' does not exist")
        self._user_roles.setdefault(user_id, set()).add(role_name)

    def revoke_role(self, user_id: str, role_name: str) -> None:
        """Revoke a role from a user."""
        if user_id in self._user_roles:
            self._user_roles[user_id].discard(role_name)

    def get_user_roles(self, user_id: str) -> Set[str]:
        """Get all roles assigned to a user."""
        return self._user_roles.get(user_id, set()).copy()

    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user."""
        permissions: Set[str] = set()
        for role_name in self.get_user_roles(user_id):
            role = self.role_registry.get_role(role_name)
            if role:
                permissions.update(role.get_all_permissions(self.role_registry))
        return permissions

    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if a user has a specific permission."""
        return permission in self.get_user_permissions(user_id)

    def check_any_permission(self, user_id: str, permissions: Set[str]) -> bool:
        """Check if a user has any of the specified permissions."""
        user_perms = self.get_user_permissions(user_id)
        return bool(user_perms & permissions)

    def check_all_permissions(self, user_id: str, permissions: Set[str]) -> bool:
        """Check if a user has all of the specified permissions."""
        user_perms = self.get_user_permissions(user_id)
        return permissions.issubset(user_perms)

    def create_group(self, group: Group) -> None:
        """Create a group."""
        self._groups[group.name] = group

    def add_user_to_group(self, user_id: str, group_name: str) -> None:
        """Add a user to a group."""
        if group_name not in self._groups:
            raise ValueError(f"Group '{group_name}' does not exist")
        # In production, this would update the user's group membership
        pass

    def get_group_permissions(self, group_name: str) -> Set[str]:
        """Get all permissions for a group."""
        group = self._groups.get(group_name)
        if not group:
            return set()
        permissions: Set[str] = set()
        for role_name in group.roles:
            role = self.role_registry.get_role(role_name)
            if role:
                permissions.update(role.get_all_permissions(self.role_registry))
        return permissions


class PBACEngine:
    """Policy-Based Access Control engine."""

    def __init__(self) -> None:
        self._policies: List[Policy] = []

    def add_policy(self, policy: Policy) -> None:
        """Add a policy."""
        self._policies.append(policy)
        # Sort by priority (higher first)
        self._policies.sort(key=lambda p: p.priority, reverse=True)

    def remove_policy(self, name: str) -> None:
        """Remove a policy by name."""
        self._policies = [p for p in self._policies if p.name != name]

    def evaluate(
        self,
        subject: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AccessDecision:
        """Evaluate access request against all policies."""
        context = context or {}

        for policy in self._policies:
            if not policy.matches_subject(subject):
                continue
            if not policy.matches_action(action):
                continue
            if not policy.matches_resource(resource):
                continue
            if not policy.evaluate_conditions(context):
                continue

            if policy.effect == Effect.ALLOW:
                return AccessDecision.ALLOW
            elif policy.effect == Effect.DENY:
                return AccessDecision.DENY

        return AccessDecision.ABSTAIN

    def authorize(
        self,
        subject: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Authorize an action. Returns True if allowed, False otherwise."""
        decision = self.evaluate(subject, action, resource, context)
        return decision == AccessDecision.ALLOW


class HybridAccessEngine:
    """Hybrid RBAC + PBAC access control engine."""

    def __init__(
        self,
        rbac_engine: RBACEngine,
        pbac_engine: PBACEngine,
    ) -> None:
        self.rbac = rbac_engine
        self.pbac = pbac_engine

    def authorize(
        self,
        user_id: str,
        action: str,
        resource: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Authorize using both RBAC and PBAC."""
        context = context or {}

        # First check RBAC
        user_perms = self.rbac.get_user_permissions(user_id)
        rbac_allowed = action in user_perms or "*" in user_perms

        # Then check PBAC
        pbac_decision = self.pbac.evaluate(user_id, action, resource, context)

        # PBAC deny overrides RBAC allow
        if pbac_decision == AccessDecision.DENY:
            return False

        # PBAC allow overrides RBAC deny
        if pbac_decision == AccessDecision.ALLOW:
            return True

        # If PBAC abstains, fall back to RBAC
        return rbac_allowed


# Common condition factories


def time_restriction_condition(
    allowed_hours: Tuple[int, int],
    timezone: str = "UTC",
) -> Callable[[Dict[str, Any]], bool]:
    """Create a time-based restriction condition."""
    def condition(context: Dict[str, Any]) -> bool:
        import datetime
        tz = datetime.timezone.utc if timezone == "UTC" else datetime.timezone.utc
        now = datetime.datetime.now(tz)
        return allowed_hours[0] <= now.hour < allowed_hours[1]
    return condition


def ip_allowlist_condition(
    allowed_ips: Set[str],
) -> Callable[[Dict[str, Any]], bool]:
    """Create an IP allowlist condition."""
    def condition(context: Dict[str, Any]) -> bool:
        client_ip = context.get("client_ip", "")
        return client_ip in allowed_ips
    return condition


def attribute_condition(
    attribute: str,
    expected_value: Any,
) -> Callable[[Dict[str, Any]], bool]:
    """Create an attribute-based condition."""
    def condition(context: Dict[str, Any]) -> bool:
        return context.get(attribute) == expected_value
    return condition


def rate_limit_condition(
    max_requests: int,
    window_seconds: int,
) -> Callable[[Dict[str, Any]], bool]:
    """Create a rate limit condition."""
    _request_counts: Dict[str, List[float]] = {}

    def condition(context: Dict[str, Any]) -> bool:
        now = time.time()
        subject = context.get("subject", "anonymous")
        window_start = now - window_seconds

        if subject not in _request_counts:
            _request_counts[subject] = []

        # Clean old entries
        _request_counts[subject] = [
            t for t in _request_counts[subject] if t > window_start
        ]

        if len(_request_counts[subject]) >= max_requests:
            return False

        _request_counts[subject].append(now)
        return True

    return condition

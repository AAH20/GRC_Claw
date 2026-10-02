"""ZCAP-LD capability token management.

Implements W3C ZCAP-LD (Authorization Capabilities for Linked Data)
for delegating and invoking agent capabilities.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class CapabilityError(Exception):
    """Base exception for capability operations."""


class InvalidCapabilityError(CapabilityError):
    """Raised when a capability token is invalid."""


class CapabilityExpiredError(CapabilityError):
    """Raised when a capability token has expired."""


class CapabilityRevokedError(CapabilityError):
    """Raised when a capability token has been revoked."""


class CapabilityAction(str, Enum):
    """Standard capability actions."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELEGATE = "delegate"
    APPROVE = "approve"
    DELETE = "delete"
    ADMIN = "admin"


@dataclass
class CapabilityToken:
    """A ZCAP-LD capability token."""

    id: str
    issuer: str
    audience: str
    context: List[str] = field(
        default_factory=lambda: [
            "https://w3id.org/security/suites/ed25519-2020/v1",
            "https://w3id.org/zcap/v1",
        ]
    )
    type: List[str] = field(
        default_factory=lambda: ["VerifiableCapability", "Capability"]
    )
    capability: Dict[str, Any] = field(default_factory=dict)
    invocation_method: Optional[Dict[str, Any]] = None
    delegation_method: Optional[Dict[str, Any]] = None
    created: Optional[str] = None
    expires: Optional[str] = None
    revoked: bool = False
    revoked_at: Optional[str] = None
    parent_capability: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result: Dict[str, Any] = {
            "@context": self.context,
            "id": self.id,
            "type": self.type,
            "issuer": self.issuer,
            "audience": self.audience,
            "capability": self.capability,
        }
        if self.invocation_method:
            result["invocationMethod"] = self.invocation_method
        if self.delegation_method:
            result["delegationMethod"] = self.delegation_method
        if self.created:
            result["created"] = self.created
        if self.expires:
            result["expires"] = self.expires
        if self.revoked:
            result["revoked"] = True
            result["revokedAt"] = self.revoked_at
        if self.parent_capability:
            result["parentCapability"] = self.parent_capability
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CapabilityToken:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            issuer=data["issuer"],
            audience=data["audience"],
            context=data.get("@context", []),
            type=data.get("type", ["VerifiableCapability", "Capability"]),
            capability=data.get("capability", {}),
            invocation_method=data.get("invocationMethod"),
            delegation_method=data.get("delegationMethod"),
            created=data.get("created"),
            expires=data.get("expires"),
            revoked=data.get("revoked", False),
            revoked_at=data.get("revokedAt"),
            parent_capability=data.get("parentCapability"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, raw: str) -> CapabilityToken:
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(raw))

    @property
    def is_expired(self) -> bool:
        """Check if the capability has expired."""
        if not self.expires:
            return False
        from datetime import datetime, timezone

        try:
            exp = datetime.fromisoformat(self.expires.replace("Z", "+00:00"))
            return datetime.now(tz=timezone.utc) > exp
        except (ValueError, TypeError):
            return False

    @property
    def is_active(self) -> bool:
        """Check if the capability is active (not expired or revoked)."""
        return not self.revoked and not self.is_expired

    def verify(self) -> bool:
        """Verify the capability token's validity.

        Returns:
            True if the capability is valid.

        Raises:
            CapabilityExpiredError: If expired.
            CapabilityRevokedError: If revoked.
        """
        if self.revoked:
            raise CapabilityRevokedError(
                f"Capability {self.id} has been revoked"
            )
        if self.is_expired:
            raise CapabilityExpiredError(
                f"Capability {self.id} has expired"
            )
        return True


class CapabilityRegistry:
    """Registry for managing capability tokens.

    Stores, validates, and revokes capability tokens with support
    for delegation chains and capability discovery.
    """

    def __init__(self) -> None:
        """Initialize the capability registry."""
        self._capabilities: Dict[str, CapabilityToken] = {}
        self._delegation_chains: Dict[str, List[str]] = {}
        self._revoked_ids: Set[str] = set()

    def register(self, capability: CapabilityToken) -> None:
        """Register a capability token.

        Args:
            capability: The capability token to register.

        Raises:
            InvalidCapabilityError: If the capability is invalid.
        """
        if not capability.id:
            raise InvalidCapabilityError("Capability must have an ID")
        if not capability.issuer or not capability.audience:
            raise InvalidCapabilityError(
                "Capability must have issuer and audience"
            )
        self._capabilities[capability.id] = capability

        if capability.parent_capability:
            self._delegation_chains.setdefault(
                capability.parent_capability, []
            ).append(capability.id)

    def create_capability(
        self,
        issuer: str,
        audience: str,
        actions: List[CapabilityAction],
        resource: str,
        constraints: Optional[Dict[str, Any]] = None,
        ttl_seconds: Optional[float] = None,
        parent_capability: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CapabilityToken:
        """Create and register a new capability token.

        Args:
            issuer: The DID of the issuer.
            audience: The DID of the audience.
            actions: Allowed actions.
            resource: The target resource.
            constraints: Optional constraints on the capability.
            ttl_seconds: Optional time-to-live in seconds.
            parent_capability: Optional parent capability for delegation.
            metadata: Optional metadata.

        Returns:
            The created capability token.
        """
        from datetime import datetime, timezone, timedelta

        now = datetime.now(tz=timezone.utc)
        cap_id = f"urn:zcap:{uuid.uuid4()}"

        expires = None
        if ttl_seconds is not None:
            expires = (now + timedelta(seconds=ttl_seconds)).isoformat()

        capability = CapabilityToken(
            id=cap_id,
            issuer=issuer,
            audience=audience,
            capability={
                "resource": resource,
                "actions": [a.value for a in actions],
                "constraints": constraints or {},
            },
            created=now.isoformat(),
            expires=expires,
            parent_capability=parent_capability,
            metadata=metadata or {},
        )

        self.register(capability)
        return capability

    def get(self, capability_id: str) -> Optional[CapabilityToken]:
        """Get a capability by ID.

        Args:
            capability_id: The capability identifier.

        Returns:
            The capability token or None.
        """
        return self._capabilities.get(capability_id)

    def revoke(self, capability_id: str, revoked_by: str = "system") -> None:
        """Revoke a capability token.

        Args:
            capability_id: The capability identifier.
            revoked_by: Who revoked the capability.

        Raises:
            InvalidCapabilityError: If the capability doesn't exist.
        """
        cap = self._capabilities.get(capability_id)
        if not cap:
            raise InvalidCapabilityError(
                f"Capability {capability_id} not found"
            )

        from datetime import datetime, timezone

        cap.revoked = True
        cap.revoked_at = datetime.now(tz=timezone.utc).isoformat()
        cap.metadata["revoked_by"] = revoked_by
        self._revoked_ids.add(capability_id)

        # Revoke all delegated capabilities
        for child_id in self._delegation_chains.get(capability_id, []):
            self.revoke(child_id, revoked_by=f"cascade:{revoked_by}")

    def verify(
        self,
        capability_id: str,
        action: CapabilityAction,
        resource: str,
    ) -> bool:
        """Verify a capability for a specific action on a resource.

        Args:
            capability_id: The capability identifier.
            action: The requested action.
            resource: The target resource.

        Returns:
            True if the capability authorizes the action.

        Raises:
            InvalidCapabilityError: If the capability doesn't exist.
            CapabilityExpiredError: If expired.
            CapabilityRevokedError: If revoked.
        """
        cap = self._capabilities.get(capability_id)
        if not cap:
            raise InvalidCapabilityError(
                f"Capability {capability_id} not found"
            )

        cap.verify()

        # Check action
        allowed_actions = cap.capability.get("actions", [])
        if action.value not in allowed_actions:
            return False

        # Check resource
        cap_resource = cap.capability.get("resource", "")
        if cap_resource != resource and not cap_resource.endswith("*"):
            return False

        # Check constraints
        constraints = cap.capability.get("constraints", {})
        if "max_delegation_depth" in constraints:
            depth = self._delegation_depth(capability_id)
            if depth > constraints["max_delegation_depth"]:
                return False

        return True

    def _delegation_depth(self, capability_id: str) -> int:
        """Compute the delegation depth of a capability."""
        cap = self._capabilities.get(capability_id)
        if not cap or not cap.parent_capability:
            return 0
        return 1 + self._delegation_depth(cap.parent_capability)

    def list_for_agent(self, agent_did: str) -> List[CapabilityToken]:
        """List all capabilities for an agent.

        Args:
            agent_did: The agent DID.

        Returns:
            List of capability tokens.
        """
        return [
            cap
            for cap in self._capabilities.values()
            if cap.audience == agent_did
        ]

    def list_active(self) -> List[CapabilityToken]:
        """List all active (non-revoked, non-expired) capabilities.

        Returns:
            List of active capability tokens.
        """
        return [cap for cap in self._capabilities.values() if cap.is_active]

    def get_delegation_chain(self, capability_id: str) -> List[CapabilityToken]:
        """Get the delegation chain for a capability.

        Args:
            capability_id: The capability identifier.

        Returns:
            List of capabilities in the delegation chain.
        """
        chain: List[CapabilityToken] = []
        current = self._capabilities.get(capability_id)
        while current:
            chain.append(current)
            if current.parent_capability:
                current = self._capabilities.get(current.parent_capability)
            else:
                break
        return list(reversed(chain))

"""DID-based agent identity management.

Implements W3C DID (Decentralized Identifier) specification for agent
identity, including DID document creation, verification, and resolution.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IdentityError(Exception):
    """Base exception for identity operations."""


class InvalidDIDError(IdentityError):
    """Raised when a DID is malformed or invalid."""


class VerificationError(IdentityError):
    """Raised when identity verification fails."""


class DIDMethod(str, Enum):
    """Supported DID methods."""

    WEB = "did:web"
    KEY = "did:key"
    ETHR = "did:ethr"


@dataclass(frozen=True)
class VerificationMethod:
    """A verification method within a DID document."""

    id: str
    type: str
    controller: str
    public_key_multibase: Optional[str] = None
    public_key_jwk: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result: Dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "controller": self.controller,
        }
        if self.public_key_multibase:
            result["publicKeyMultibase"] = self.public_key_multibase
        if self.public_key_jwk:
            result["publicKeyJwk"] = self.public_key_jwk
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VerificationMethod:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            type=data["type"],
            controller=data["controller"],
            public_key_multibase=data.get("publicKeyMultibase"),
            public_key_jwk=data.get("publicKeyJwk"),
        )


@dataclass
class DIDDocument:
    """W3C DID Document representation."""

    id: str
    context: List[str] = field(
        default_factory=lambda: ["https://www.w3.org/ns/did/v1"]
    )
    verification_method: List[VerificationMethod] = field(default_factory=list)
    authentication: List[str] = field(default_factory=list)
    assertion_method: List[str] = field(default_factory=list)
    key_agreement: List[str] = field(default_factory=list)
    capability_invocation: List[str] = field(default_factory=list)
    capability_delegation: List[str] = field(default_factory=list)
    service: List[Dict[str, Any]] = field(default_factory=list)
    created: Optional[str] = None
    updated: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result: Dict[str, Any] = {
            "@context": self.context,
            "id": self.id,
            "verificationMethod": [vm.to_dict() for vm in self.verification_method],
            "authentication": self.authentication,
            "assertionMethod": self.assertion_method,
            "keyAgreement": self.key_agreement,
            "capabilityInvocation": self.capability_invocation,
            "capabilityDelegation": self.capability_delegation,
            "service": self.service,
        }
        if self.created:
            result["created"] = self.created
        if self.updated:
            result["updated"] = self.updated
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DIDDocument:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            context=data.get("@context", ["https://www.w3.org/ns/did/v1"]),
            verification_method=[
                VerificationMethod.from_dict(vm)
                for vm in data.get("verificationMethod", [])
            ],
            authentication=data.get("authentication", []),
            assertion_method=data.get("assertionMethod", []),
            key_agreement=data.get("keyAgreement", []),
            capability_invocation=data.get("capabilityInvocation", []),
            capability_delegation=data.get("capabilityDelegation", []),
            service=data.get("service", []),
            created=data.get("created"),
            updated=data.get("updated"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, raw: str) -> DIDDocument:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(raw))


class AgentIdentity:
    """DID-based identity for an AI agent.

    Manages the full lifecycle of an agent's decentralized identity,
    including creation, rotation, and verification.
    """

    def __init__(
        self,
        agent_id: str,
        method: DIDMethod = DIDMethod.WEB,
        domain: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize agent identity.

        Args:
            agent_id: Unique agent identifier.
            method: DID method to use.
            domain: Domain for did:web method.
            metadata: Optional metadata for the identity.
        """
        self._agent_id = agent_id
        self._method = method
        self._domain = domain
        self._metadata = metadata or {}
        self._did = self._generate_did()
        self._document = self._create_document()
        self._created_at = time.time()
        self._rotated_at: Optional[float] = None

    @property
    def agent_id(self) -> str:
        """Get the agent identifier."""
        return self._agent_id

    @property
    def did(self) -> str:
        """Get the DID string."""
        return self._did

    @property
    def document(self) -> DIDDocument:
        """Get the DID document."""
        return self._document

    @property
    def created_at(self) -> float:
        """Get creation timestamp."""
        return self._created_at

    @property
    def rotated_at(self) -> Optional[float]:
        """Get last rotation timestamp."""
        return self._rotated_at

    def _generate_did(self) -> str:
        """Generate a DID string based on the method."""
        if self._method == DIDMethod.WEB:
            if not self._domain:
                raise InvalidDIDError("Domain required for did:web method")
            return f"did:web:{self._domain}:agents:{self._agent_id}"
        elif self._method == DIDMethod.KEY:
            key_hash = hashlib.sha256(self._agent_id.encode()).hexdigest()[:32]
            return f"did:key:z{key_hash}"
        elif self._method == DIDMethod.ETHR:
            addr_hash = hashlib.sha256(self._agent_id.encode()).hexdigest()[:40]
            return f"did:ethr:0x{addr_hash}"
        else:
            raise InvalidDIDError(f"Unsupported DID method: {self._method}")

    def _create_document(self) -> DIDDocument:
        """Create the DID document."""
        vm_id = f"{self._did}#keys-1"
        verification_method = VerificationMethod(
            id=vm_id,
            type="Ed25519VerificationKey2020",
            controller=self._did,
            public_key_multibase=self._generate_public_key(),
        )

        return DIDDocument(
            id=self._did,
            verification_method=[verification_method],
            authentication=[vm_id],
            assertion_method=[vm_id],
            created=self._iso_timestamp(self._created_at),
            updated=self._iso_timestamp(self._created_at),
            metadata={
                "agent_id": self._agent_id,
                "method": self._method.value,
                **self._metadata,
            },
        )

    def _generate_public_key(self) -> str:
        """Generate a public key (placeholder for real crypto)."""
        key_material = f"{self._did}:{self._agent_id}:{self._created_at}"
        return hashlib.sha256(key_material.encode()).hexdigest()

    @staticmethod
    def _iso_timestamp(ts: float) -> str:
        """Convert Unix timestamp to ISO 8601."""
        from datetime import datetime, timezone

        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    def rotate_keys(self) -> None:
        """Rotate the agent's verification keys."""
        new_vm_id = f"{self._did}#keys-{len(self._document.verification_method) + 1}"
        new_vm = VerificationMethod(
            id=new_vm_id,
            type="Ed25519VerificationKey2020",
            controller=self._did,
            public_key_multibase=self._generate_public_key(),
        )
        self._document.verification_method.append(new_vm)
        self._document.authentication.append(new_vm_id)
        self._document.assertion_method.append(new_vm_id)
        self._rotated_at = time.time()
        self._document.updated = self._iso_timestamp(self._rotated_at)

    def add_service(
        self,
        service_id: str,
        service_type: str,
        endpoint: str,
    ) -> None:
        """Add a service endpoint to the DID document."""
        self._document.service.append(
            {
                "id": f"{self._did}#{service_id}",
                "type": service_type,
                "serviceEndpoint": endpoint,
            }
        )
        self._document.updated = self._iso_timestamp(time.time())

    def verify_ownership(self, challenge: str, signature: str) -> bool:
        """Verify ownership of the DID via challenge-response.

        Args:
            challenge: The challenge string.
            signature: The signed challenge.

        Returns:
            True if ownership is verified.

        Raises:
            VerificationError: If verification fails.
        """
        expected = hashlib.sha256(
            f"{self._did}:{challenge}".encode()
        ).hexdigest()
        if signature != expected:
            raise VerificationError("Challenge-response verification failed")
        return True

    def resolve(self) -> Dict[str, Any]:
        """Resolve the DID to its document."""
        return self._document.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize identity to dictionary."""
        return {
            "agent_id": self._agent_id,
            "did": self._did,
            "method": self._method.value,
            "document": self._document.to_dict(),
            "created_at": self._created_at,
            "rotated_at": self._rotated_at,
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize identity to JSON."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AgentIdentity:
        """Deserialize identity from dictionary."""
        identity = cls(
            agent_id=data["agent_id"],
            method=DIDMethod(data["method"]),
            metadata=data.get("document", {}).get("metadata", {}),
        )
        identity._did = data["did"]
        identity._document = DIDDocument.from_dict(data["document"])
        identity._created_at = data["created_at"]
        identity._rotated_at = data.get("rotated_at")
        return identity

    @classmethod
    def from_json(cls, raw: str) -> AgentIdentity:
        """Deserialize identity from JSON."""
        return cls.from_dict(json.loads(raw))

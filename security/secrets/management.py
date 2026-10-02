"""Secret rotation for agentic AI marketing security layer.

Provides automated secret rotation, versioned secrets, rotation policies,
and integration with HashiCorp Vault and cloud secret managers.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class SecretError(Exception):
    """Base exception for secret management errors."""


class RotationError(SecretError):
    """Raised when secret rotation fails."""


class SecretNotFoundError(SecretError):
    """Raised when a secret is not found."""


class RotationPolicyError(SecretError):
    """Raised when rotation policy is invalid."""


class SecretType(str, Enum):
    """Types of secrets."""

    API_KEY = "api_key"
    DATABASE = "database"
    CERTIFICATE = "certificate"
    TOKEN = "token"
    PASSWORD = "password"
    ENCRYPTION_KEY = "encryption_key"
    SSH_KEY = "ssh_key"
    OAUTH_CREDENTIAL = "oauth_credential"
    CUSTOM = "custom"


class RotationStrategy(str, Enum):
    """Rotation strategies."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    ON_DEMAND = "on_demand"
    EVENT_DRIVEN = "event_driven"


class SecretStatus(str, Enum):
    """Secret status."""

    ACTIVE = "active"
    ROTATING = "rotating"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(frozen=True)
class SecretMetadata:
    """Secret metadata."""

    id: str
    name: str
    type: SecretType
    created_at: float
    updated_at: float
    expires_at: Optional[float] = None
    rotation_policy: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    status: SecretStatus = SecretStatus.ACTIVE


@dataclass(frozen=True)
class Secret:
    """A secret with metadata."""

    metadata: SecretMetadata
    value: str

    def is_expired(self) -> bool:
        """Check if the secret is expired."""
        if self.metadata.expires_at is None:
            return False
        return time.time() >= self.metadata.expires_at

    def should_rotate(self, rotation_interval: int) -> bool:
        """Check if the secret should be rotated."""
        return time.time() >= self.metadata.updated_at + rotation_interval


@dataclass(frozen=True)
class RotationPolicy:
    """Secret rotation policy."""

    name: str
    secret_type: SecretType
    interval_seconds: int
    strategy: RotationStrategy
    auto_rotate: bool = True
    notify_before_expiry: int = 86400 * 7  # 7 days
    grace_period: int = 86400 * 1  # 1 day
    max_versions: int = 5
    require_approval: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RotationRecord:
    """Record of a secret rotation."""

    id: str
    secret_id: str
    old_version: int
    new_version: int
    rotated_at: float
    rotated_by: str
    reason: str
    status: str
    error: Optional[str] = None


class SecretGenerator:
    """Generates secure secrets."""

    @staticmethod
    def generate_api_key(length: int = 64) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_password(
        length: int = 32,
        use_uppercase: bool = True,
        use_lowercase: bool = True,
        use_digits: bool = True,
        use_special: bool = True,
    ) -> str:
        """Generate a secure password."""
        chars = ""
        if use_uppercase:
            chars += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if use_lowercase:
            chars += "abcdefghijklmnopqrstuvwxyz"
        if use_digits:
            chars += "0123456789"
        if use_special:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        if not chars:
            raise SecretError("At least one character set must be enabled")

        return "".join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    def generate_token(length: int = 64) -> str:
        """Generate a secure token."""
        return secrets.token_hex(length)

    @staticmethod
    def generate_encryption_key(length: int = 32) -> str:
        """Generate an encryption key."""
        return secrets.token_bytes(length).hex()

    @staticmethod
    def generate_secret(secret_type: SecretType, **kwargs: Any) -> str:
        """Generate a secret based on type."""
        generators = {
            SecretType.API_KEY: SecretGenerator.generate_api_key,
            SecretType.PASSWORD: SecretGenerator.generate_password,
            SecretType.TOKEN: SecretGenerator.generate_token,
            SecretType.ENCRYPTION_KEY: SecretGenerator.generate_encryption_key,
        }
        generator = generators.get(secret_type)
        if not generator:
            raise SecretError(f"No generator for secret type: {secret_type}")
        return generator(**kwargs)


class SecretStore:
    """Abstract secret store interface."""

    async def store(self, secret: Secret) -> None:
        """Store a secret."""
        raise NotImplementedError

    async def retrieve(self, secret_id: str) -> Optional[Secret]:
        """Retrieve a secret."""
        raise NotImplementedError

    async def delete(self, secret_id: str) -> None:
        """Delete a secret."""
        raise NotImplementedError

    async def list_secrets(self) -> List[SecretMetadata]:
        """List all secrets."""
        raise NotImplementedError


class InMemorySecretStore(SecretStore):
    """In-memory secret store for testing."""

    def __init__(self) -> None:
        self._secrets: Dict[str, Secret] = {}
        self._versions: Dict[str, List[Secret]] = {}

    async def store(self, secret: Secret) -> None:
        """Store a secret."""
        self._secrets[secret.metadata.id] = secret
        if secret.metadata.id not in self._versions:
            self._versions[secret.metadata.id] = []
        self._versions[secret.metadata.id].append(secret)

    async def retrieve(self, secret_id: str) -> Optional[Secret]:
        """Retrieve a secret."""
        return self._secrets.get(secret_id)

    async def delete(self, secret_id: str) -> None:
        """Delete a secret."""
        self._secrets.pop(secret_id, None)
        self._versions.pop(secret_id, None)

    async def list_secrets(self) -> List[SecretMetadata]:
        """List all secrets."""
        return [s.metadata for s in self._secrets.values()]

    def get_versions(self, secret_id: str) -> List[Secret]:
        """Get all versions of a secret."""
        return self._versions.get(secret_id, [])


class SecretRotationManager:
    """Manages secret rotation."""

    def __init__(self, store: SecretStore) -> None:
        self.store = store
        self._policies: Dict[str, RotationPolicy] = {}
        self._rotation_history: List[RotationRecord] = []
        self._running = False

    def register_policy(self, policy: RotationPolicy) -> None:
        """Register a rotation policy."""
        if policy.interval_seconds < 3600:
            raise RotationPolicyError("Rotation interval must be at least 1 hour")
        self._policies[policy.name] = policy

    def get_policy(self, name: str) -> Optional[RotationPolicy]:
        """Get a rotation policy."""
        return self._policies.get(name)

    async def rotate_secret(
        self,
        secret_id: str,
        policy_name: str,
        rotated_by: str = "system",
        reason: str = "scheduled",
    ) -> RotationRecord:
        """Rotate a secret."""
        policy = self._policies.get(policy_name)
        if not policy:
            raise RotationError(f"Policy '{policy_name}' not found")

        old_secret = await self.store.retrieve(secret_id)
        if not old_secret:
            raise SecretNotFoundError(f"Secret '{secret_id}' not found")

        # Generate new secret value
        new_value = SecretGenerator.generate_secret(policy.secret_type)

        # Create new secret version
        new_metadata = SecretMetadata(
            id=old_secret.metadata.id,
            name=old_secret.metadata.name,
            type=old_secret.metadata.type,
            created_at=old_secret.metadata.created_at,
            updated_at=time.time(),
            expires_at=time.time() + policy.interval_seconds,
            rotation_policy=policy_name,
            tags=old_secret.metadata.tags,
            metadata=old_secret.metadata.metadata,
            version=old_secret.metadata.version + 1,
            status=SecretStatus.ACTIVE,
        )

        new_secret = Secret(metadata=new_metadata, value=new_value)

        # Store new version
        await self.store.store(new_secret)

        # Deprecate old version
        old_metadata = SecretMetadata(
            **{**old_secret.metadata.__dict__, "status": SecretStatus.DEPRECATED}
        )
        old_secret_deprecated = Secret(metadata=old_metadata, value=old_secret.value)
        await self.store.store(old_secret_deprecated)

        # Record rotation
        record = RotationRecord(
            id=hashlib.sha256(f"{secret_id}-{time.time()}".encode()).hexdigest()[:16],
            secret_id=secret_id,
            old_version=old_secret.metadata.version,
            new_version=new_metadata.version,
            rotated_at=time.time(),
            rotated_by=rotated_by,
            reason=reason,
            status="success",
        )
        self._rotation_history.append(record)
        return record

    async def check_expired_secrets(self) -> List[SecretMetadata]:
        """Check for expired secrets."""
        secrets = await self.store.list_secrets()
        return [s for s in secrets if s.expires_at and time.time() >= s.expires_at]

    async def check_secrets_due_for_rotation(self) -> List[Tuple[str, str]]:
        """Check for secrets due for rotation."""
        secrets = await self.store.list_secrets()
        due = []
        for secret in secrets:
            if secret.rotation_policy:
                policy = self._policies.get(secret.rotation_policy)
                if policy and policy.auto_rotate:
                    if time.time() >= secret.updated_at + policy.interval_seconds:
                        due.append((secret.id, secret.rotation_policy))
        return due

    async def start_rotation_scheduler(self) -> None:
        """Start the rotation scheduler."""
        self._running = True
        while self._running:
            try:
                due = await self.check_secrets_due_for_rotation()
                for secret_id, policy_name in due:
                    await self.rotate_secret(secret_id, policy_name)
            except Exception as exc:
                print(f"Rotation error: {exc}")
            await asyncio.sleep(3600)  # Check every hour

    def stop_rotation_scheduler(self) -> None:
        """Stop the rotation scheduler."""
        self._running = False

    def get_rotation_history(
        self,
        secret_id: Optional[str] = None,
    ) -> List[RotationRecord]:
        """Get rotation history."""
        if secret_id:
            return [r for r in self._rotation_history if r.secret_id == secret_id]
        return self._rotation_history.copy()

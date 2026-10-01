"""Security utilities for authentication and authorization."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    scopes: list[str],
    tenant_id: str,
    roles: list[str],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "iss": settings.OIDC_ISSUER,
        "sub": subject,
        "aud": settings.OIDC_AUDIENCE,
        "iat": now,
        "exp": now + expires_delta,
        "scope": " ".join(scopes),
        "tenant_id": tenant_id,
        "roles": roles,
        "mfa_verified": True,
        "auth_time": now,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, tenant_id: str) -> str:
    """Create a JWT refresh token."""
    now = datetime.now(timezone.utc)
    expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {
        "iss": settings.OIDC_ISSUER,
        "sub": subject,
        "aud": settings.OIDC_AUDIENCE,
        "iat": now,
        "exp": now + expires_delta,
        "token_type": "refresh",
        "tenant_id": tenant_id,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.OIDC_AUDIENCE,
            issuer=settings.OIDC_ISSUER,
        )
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"grc_live_{secrets.token_urlsafe(32)}"


def verify_api_key_prefix(api_key: str) -> bool:
    """Verify API key prefix."""
    return api_key.startswith("grc_live_") or api_key.startswith("grc_test_")


def compute_webhook_signature(secret: str, timestamp: str, payload: str) -> str:
    """Compute HMAC-SHA256 webhook signature."""
    signed_payload = f"{timestamp}.{payload}"
    return hmac.new(
        secret.encode(),
        signed_payload.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_webhook_signature(secret: str, timestamp: str, payload: str, signature: str) -> bool:
    """Verify HMAC-SHA256 webhook signature."""
    expected = compute_webhook_signature(secret, timestamp, payload)
    return hmac.compare_digest(signature, expected)


def generate_idempotency_key() -> str:
    """Generate an idempotency key."""
    return secrets.token_hex(16)


# RBAC permission matrix
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "policies:read", "policies:write",
        "evidence:read", "evidence:write",
        "enforcement:decide",
        "assessments:read", "assessments:write",
        "compliance:read", "compliance:write",
        "agents:read", "agents:write",
        "audit:read",
        "webhooks:manage",
    },
    "assessor": {
        "assessments:read", "assessments:write",
        "evidence:read",
    },
    "auditor": {
        "audit:read", "evidence:read", "compliance:read",
    },
    "operator": {
        "policies:read", "evidence:read", "evidence:write",
        "enforcement:decide",
    },
    "viewer": {
        "policies:read", "evidence:read", "compliance:read",
    },
}


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_any_permission(role: str, permissions: list[str]) -> bool:
    """Check if a role has any of the specified permissions."""
    role_perms = ROLE_PERMISSIONS.get(role, set())
    return any(p in role_perms for p in permissions)

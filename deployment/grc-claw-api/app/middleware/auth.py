"""Authentication middleware supporting OAuth 2.1/OIDC, API keys, and mTLS."""

import time
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token, verify_api_key_prefix

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


class AuthContext(BaseModel):
    """Authenticated request context."""

    subject: str
    subject_type: str  # "user", "agent", "service"
    tenant_id: str
    roles: list[str]
    scopes: list[str]
    auth_method: str  # "oidc", "api_key", "mtls"
    token: str | None = None
    api_key_id: str | None = None
    spiffe_id: str | None = None
    request_id: str | None = None
    trace_id: str | None = None


class AuthenticationMiddleware:
    """Multi-method authentication middleware."""

    def __init__(self):
        self._jwks_cache: dict | None = None
        self._jwks_last_fetch: float = 0
        self._jwks_ttl: int = 300  # 5 minutes

    async def authenticate(self, request: Request) -> AuthContext:
        """Authenticate an incoming request."""
        # Extract request IDs
        request_id = request.headers.get("X-Request-ID", "")
        trace_id = request.headers.get("X-Trace-ID", "")

        # Try mTLS first (agent identity)
        mtls_auth = self._try_mtls_auth(request)
        if mtls_auth:
            return mtls_auth

        # Try Bearer token (OAuth/JWT or API key)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

            # Try API key first (grc_live_ / grc_test_)
            if verify_api_key_prefix(token):
                return await self._authenticate_api_key(token, request_id, trace_id)

            # Try JWT token
            return await self._authenticate_jwt(token, request_id, trace_id)

        raise UnauthorizedException("Missing or invalid Authorization header.")

    def _try_mtls_auth(self, request: Request) -> AuthContext | None:
        """Try mTLS authentication (SPIFFE SVID)."""
        # In production, this would be handled by the service mesh / TLS termination
        # and passed as headers. For direct mTLS:
        client_cert = request.headers.get("X-Client-Certificate")
        spiffe_id = request.headers.get("X-SPIFFE-ID")

        if spiffe_id:
            # Validate SPIFFE ID format
            if spiffe_id.startswith("spiffe://grc-claw.io/"):
                agent_id = spiffe_id.split("/sa/")[-1] if "/sa/" in spiffe_id else spiffe_id
                namespace = spiffe_id.split("/ns/")[-1].split("/sa/")[0] if "/ns/" in spiffe_id else "default"
                return AuthContext(
                    subject=agent_id,
                    subject_type="agent",
                    tenant_id=namespace,
                    roles=["operator"],
                    scopes=["enforcement:decide"],
                    auth_method="mtls",
                    spiffe_id=spiffe_id,
                )
        return None

    async def _authenticate_jwt(self, token: str, request_id: str, trace_id: str) -> AuthContext:
        """Authenticate using JWT token."""
        payload = decode_token(token)
        if not payload:
            raise UnauthorizedException("Invalid or expired token.")

        # Validate required claims
        if "sub" not in payload or "tenant_id" not in payload:
            raise UnauthorizedException("Token missing required claims.")

        scopes = payload.get("scope", "").split()
        roles = payload.get("roles", ["viewer"])

        return AuthContext(
            subject=payload["sub"],
            subject_type="user",
            tenant_id=payload["tenant_id"],
            roles=roles,
            scopes=scopes,
            auth_method="oidc",
            token=token,
            request_id=request_id,
            trace_id=trace_id,
        )

    async def _authenticate_api_key(self, api_key: str, request_id: str, trace_id: str) -> AuthContext:
        """Authenticate using API key.

        In production, this would validate against a database/secret store.
        For now, we validate the prefix and extract tenant info.
        """
        if not verify_api_key_prefix(api_key):
            raise UnauthorizedException("Invalid API key format.")

        # In production: lookup API key in database, validate hash, check expiry
        # For demo, we use a simple lookup
        # TODO: Replace with actual API key validation
        tenant_id = "default"
        scopes = self._get_scopes_for_key(api_key)

        return AuthContext(
            subject=api_key[:16],
            subject_type="service",
            tenant_id=tenant_id,
            roles=["service"],
            scopes=scopes,
            auth_method="api_key",
            api_key_id=api_key[:16],
            request_id=request_id,
            trace_id=trace_id,
        )

    def _get_scopes_for_key(self, api_key: str) -> list[str]:
        """Get scopes associated with an API key."""
        # In production, this would come from the database
        # For demo purposes, return all scopes
        return [
            "policies:read", "policies:write",
            "evidence:read", "evidence:write",
            "enforcement:decide",
            "assessments:read", "assessments:write",
            "compliance:read", "compliance:write",
            "agents:read", "agents:write",
            "audit:read",
            "webhooks:manage",
        ]


# Singleton instance
auth_middleware = AuthenticationMiddleware()


async def get_current_auth(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
) -> AuthContext:
    """Dependency to get the current authenticated context."""
    return await auth_middleware.authenticate(request)


def require_scope(*required_scopes: str):
    """Dependency factory to require specific scopes."""

    def check_scopes(auth: Annotated[AuthContext, Depends(get_current_auth)]) -> AuthContext:
        if not any(scope in auth.scopes for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient scope. Required: {', '.join(required_scopes)}",
            )
        return auth

    return check_scopes


def require_role(*required_roles: str):
    """Dependency factory to require specific roles."""

    def check_roles(auth: Annotated[AuthContext, Depends(get_current_auth)]) -> AuthContext:
        if not any(role in auth.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required: {', '.join(required_roles)}",
            )
        return auth

    return check_roles


async def get_optional_auth(
    request: Request,
) -> AuthContext | None:
    """Get authentication context if available, None otherwise."""
    try:
        return await auth_middleware.authenticate(request)
    except UnauthorizedException:
        return None

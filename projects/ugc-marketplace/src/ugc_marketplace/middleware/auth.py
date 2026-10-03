"""
Authentication and Authorization Middleware for UGC Marketplace.

Provides:
1. JWT token validation middleware
2. API key authentication middleware
3. Role-based access control (RBAC) middleware
"""

import logging
from enum import Enum
from typing import Callable, List, Optional, Set

import jwt
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# In production, load these from environment variables or a secrets manager
JWT_SECRET_KEY = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
API_KEY_HEADER = "X-API-Key"
AUTHORIZATION_HEADER = "Authorization"
BEARER_PREFIX = "Bearer "


class UserRole(str, Enum):
    """Enumeration of user roles for RBAC."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    CREATOR = "creator"
    CONSUMER = "consumer"
    GUEST = "guest"


# Role hierarchy: higher roles inherit permissions of lower roles
ROLE_HIERARCHY: dict[UserRole, Set[UserRole]] = {
    UserRole.ADMIN: {UserRole.ADMIN, UserRole.MODERATOR, UserRole.CREATOR, UserRole.CONSUMER, UserRole.GUEST},
    UserRole.MODERATOR: {UserRole.MODERATOR, UserRole.CREATOR, UserRole.CONSUMER, UserRole.GUEST},
    UserRole.CREATOR: {UserRole.CREATOR, UserRole.CONSUMER, UserRole.GUEST},
    UserRole.CONSUMER: {UserRole.CONSUMER, UserRole.GUEST},
    UserRole.GUEST: {UserRole.GUEST},
}


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthorizationError(Exception):
    """Raised when authorization fails (insufficient permissions)."""

    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message
        self.status_code = status.HTTP_403_FORBIDDEN
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# 1. JWT Token Validation Middleware
# ---------------------------------------------------------------------------


class JWTValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates JWT tokens from the Authorization header.

    Extracts the Bearer token, decodes and validates it, then attaches
    the decoded payload to request.state for downstream use.

    Paths listed in `exclude_paths` are skipped (e.g., health checks, docs).
    """

    def __init__(
        self,
        app: ASGIApp,
        secret_key: str = JWT_SECRET_KEY,
        algorithm: str = JWT_ALGORITHM,
        exclude_paths: Optional[List[str]] = None,
    ) -> None:
        super().__init__(app)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.exclude_paths = set(exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get(AUTHORIZATION_HEADER)
        if not auth_header:
            logger.warning("Missing Authorization header for %s", request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing Authorization header"},
            )

        if not auth_header.startswith(BEARER_PREFIX):
            logger.warning("Invalid Authorization header format for %s", request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Authorization header format. Expected 'Bearer <token>'"},
            )

        token = auth_header[len(BEARER_PREFIX):]

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token for %s", request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token has expired"},
            )
        except jwt.InvalidTokenError as exc:
            logger.warning("Invalid JWT token for %s: %s", request.url.path, exc)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Invalid token: {str(exc)}"},
            )

        # Attach decoded payload to request state
        request.state.jwt_payload = payload
        request.state.user_id = payload.get("sub")
        request.state.user_roles = payload.get("roles", [])

        return await call_next(request)


# ---------------------------------------------------------------------------
# 2. API Key Authentication Middleware
# ---------------------------------------------------------------------------


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates API keys from the X-API-Key header.

    API keys are looked up in a configurable store. In production, this
    should query a database or cache (e.g., Redis). For now, a simple
    in-memory store is used as a placeholder.

    Valid keys have associated metadata (owner, roles, rate limits) that
    is attached to request.state.
    """

    # Placeholder API key store — replace with DB/cache lookup in production
    _api_key_store: dict[str, dict] = {
        "ugc_test_key_001": {
            "owner": "test-client",
            "roles": [UserRole.CONSUMER],
            "rate_limit": 100,
            "active": True,
        },
        "ugc_admin_key_001": {
            "owner": "admin-client",
            "roles": [UserRole.ADMIN],
            "rate_limit": 1000,
            "active": True,
        },
    }

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[List[str]] = None,
        key_header: str = API_KEY_HEADER,
    ) -> None:
        super().__init__(app)
        self.exclude_paths = set(exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"])
        self.key_header = key_header

    def _lookup_api_key(self, api_key: str) -> Optional[dict]:
        """Look up an API key in the store. Returns None if not found."""
        return self._api_key_store.get(api_key)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        api_key = request.headers.get(self.key_header)
        if not api_key:
            logger.warning("Missing API key for %s", request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Missing {self.key_header} header"},
            )

        key_data = self._lookup_api_key(api_key)
        if key_data is None:
            logger.warning("Invalid API key for %s", request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key"},
            )

        if not key_data.get("active", False):
            logger.warning("Inactive API key used for %s", request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "API key is deactivated"},
            )

        # Attach API key metadata to request state
        request.state.api_key = api_key
        request.state.api_key_owner = key_data.get("owner")
        request.state.api_key_roles = key_data.get("roles", [])
        request.state.api_key_rate_limit = key_data.get("rate_limit", 0)

        return await call_next(request)


# ---------------------------------------------------------------------------
# 3. Role-Based Access Control (RBAC) Middleware
# ---------------------------------------------------------------------------


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces role-based access control.

    Requires that either JWTValidationMiddleware or APIKeyAuthMiddleware
    has already populated request.state with user roles. If no roles are
    found, the request is rejected.

    The `required_roles` parameter specifies which roles are allowed to
    access the protected routes. Role hierarchy is respected: if a user
    has a higher role in the hierarchy, they can access routes requiring
    a lower role.
    """

    def __init__(
        self,
        app: ASGIApp,
        required_roles: Optional[List[UserRole]] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> None:
        super().__init__(app)
        self.required_roles = set(required_roles or [])
        self.exclude_paths = set(exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"])

    def _get_user_roles(self, request: Request) -> List[UserRole]:
        """Extract user roles from request state (set by prior middleware)."""
        # Try JWT payload roles first
        jwt_roles = getattr(request.state, "user_roles", None)
        if jwt_roles:
            return [UserRole(r) if not isinstance(r, UserRole) else r for r in jwt_roles]

        # Fall back to API key roles
        api_roles = getattr(request.state, "api_key_roles", None)
        if api_roles:
            return [UserRole(r) if not isinstance(r, UserRole) else r for r in api_roles]

        return []

    def _has_required_role(self, user_roles: List[UserRole]) -> bool:
        """Check if any of the user's roles satisfy the required roles."""
        if not self.required_roles:
            return True  # No specific role required

        for user_role in user_roles:
            # Check direct match
            if user_role in self.required_roles:
                return True
            # Check role hierarchy (higher roles inherit lower permissions)
            inherited = ROLE_HIERARCHY.get(user_role, set())
            if inherited & self.required_roles:
                return True

        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        user_roles = self._get_user_roles(request)
        if not user_roles:
            logger.warning("No roles found in request state for %s", request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required. No roles found."},
            )

        if not self._has_required_role(user_roles):
            logger.warning(
                "Access denied for %s: user roles %s do not satisfy required roles %s",
                request.url.path,
                [r.value for r in user_roles],
                [r.value for r in self.required_roles],
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Access denied. Insufficient permissions.",
                    "required_roles": [r.value for r in self.required_roles],
                    "your_roles": [r.value for r in user_roles],
                },
            )

        # Attach resolved roles for downstream handlers
        request.state.resolved_roles = user_roles

        return await call_next(request)


# ---------------------------------------------------------------------------
# Convenience: Combined Auth Middleware (JWT + API Key + RBAC)
# ---------------------------------------------------------------------------


class CombinedAuthMiddleware(BaseHTTPMiddleware):
    """
    Combined middleware that supports both JWT and API key authentication,
    with optional RBAC enforcement.

    Authentication is attempted in this order:
    1. JWT Bearer token (Authorization header)
    2. API key (X-API-Key header)

    If neither is present, the request is rejected. If `required_roles`
    is specified, RBAC is enforced after successful authentication.
    """

    def __init__(
        self,
        app: ASGIApp,
        secret_key: str = JWT_SECRET_KEY,
        algorithm: str = JWT_ALGORITHM,
        required_roles: Optional[List[UserRole]] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> None:
        super().__init__(app)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.required_roles = set(required_roles or [])
        self.exclude_paths = set(exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"])

    def _authenticate_jwt(self, request: Request) -> bool:
        """Attempt JWT authentication. Returns True on success."""
        auth_header = request.headers.get(AUTHORIZATION_HEADER)
        if not auth_header or not auth_header.startswith(BEARER_PREFIX):
            return False

        token = auth_header[len(BEARER_PREFIX):]
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return False

        request.state.jwt_payload = payload
        request.state.user_id = payload.get("sub")
        request.state.user_roles = payload.get("roles", [])
        request.state.auth_method = "jwt"
        return True

    def _authenticate_api_key(self, request: Request) -> bool:
        """Attempt API key authentication. Returns True on success."""
        api_key = request.headers.get(API_KEY_HEADER)
        if not api_key:
            return False

        key_data = APIKeyAuthMiddleware._api_key_store.get(api_key)
        if not key_data or not key_data.get("active", False):
            return False

        request.state.api_key = api_key
        request.state.api_key_owner = key_data.get("owner")
        request.state.api_key_roles = key_data.get("roles", [])
        request.state.auth_method = "api_key"
        return True

    def _get_user_roles(self, request: Request) -> List[UserRole]:
        """Extract user roles from request state."""
        jwt_roles = getattr(request.state, "user_roles", None)
        if jwt_roles:
            return [UserRole(r) if not isinstance(r, UserRole) else r for r in jwt_roles]

        api_roles = getattr(request.state, "api_key_roles", None)
        if api_roles:
            return [UserRole(r) if not isinstance(r, UserRole) else r for r in api_roles]

        return []

    def _has_required_role(self, user_roles: List[UserRole]) -> bool:
        """Check if user has any of the required roles (with hierarchy)."""
        if not self.required_roles:
            return True

        for user_role in user_roles:
            if user_role in self.required_roles:
                return True
            inherited = ROLE_HIERARCHY.get(user_role, set())
            if inherited & self.required_roles:
                return True

        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Attempt authentication
        authenticated = self._authenticate_jwt(request) or self._authenticate_api_key(request)

        if not authenticated:
            logger.warning("Authentication failed for %s", request.url.path)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Authentication required",
                    "methods": ["Bearer token (Authorization header)", f"API key ({API_KEY_HEADER} header)"],
                },
            )

        # Enforce RBAC if roles are specified
        if self.required_roles:
            user_roles = self._get_user_roles(request)
            if not self._has_required_role(user_roles):
                logger.warning(
                    "RBAC denied for %s: roles %s, required %s",
                    request.url.path,
                    [r.value for r in user_roles],
                    [r.value for r in self.required_roles],
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "detail": "Access denied. Insufficient permissions.",
                        "required_roles": [r.value for r in self.required_roles],
                        "your_roles": [r.value for r in user_roles],
                    },
                )

            request.state.resolved_roles = user_roles

        return await call_next(request)


# ---------------------------------------------------------------------------
# Helper: Register all middleware on a FastAPI app
# ---------------------------------------------------------------------------


def setup_auth_middleware(
    app: FastAPI,
    secret_key: str = JWT_SECRET_KEY,
    algorithm: str = JWT_ALGORITHM,
    exclude_paths: Optional[List[str]] = None,
    enable_jwt: bool = True,
    enable_api_key: bool = True,
    enable_rbac: bool = True,
    required_roles: Optional[List[UserRole]] = None,
) -> None:
    """
    Register all authentication middleware on a FastAPI application.

    Middleware is added in reverse order of execution (last added = first executed).
    We add RBAC first, then API key, then JWT, so the execution order is:
    JWT -> API Key -> RBAC -> Route handler.
    """
    if enable_rbac:
        app.add_middleware(
            RBACMiddleware,
            required_roles=required_roles,
            exclude_paths=exclude_paths,
        )
    if enable_api_key:
        app.add_middleware(
            APIKeyAuthMiddleware,
            exclude_paths=exclude_paths,
        )
    if enable_jwt:
        app.add_middleware(
            JWTValidationMiddleware,
            secret_key=secret_key,
            algorithm=algorithm,
            exclude_paths=exclude_paths,
        )

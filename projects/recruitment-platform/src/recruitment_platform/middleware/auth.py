"""
Authentication and Authorization Middleware for Recruitment Platform.

Provides:
- JWT token validation middleware
- API key authentication middleware
- Role-based access control (RBAC) middleware
"""

import logging
from enum import Enum
from typing import Callable, Optional, Set

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """Enumeration of user roles in the recruitment platform."""

    ADMIN = "admin"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"
    CANDIDATE = "candidate"
    VIEWER = "viewer"


class AuthError(Exception):
    """Custom exception for authentication/authorization errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class JWTValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating JWT tokens in incoming requests.

    Extracts the JWT token from the Authorization header, validates it,
    and attaches the decoded payload to request.state.user.
    """

    def __init__(
        self,
        app: ASGIApp,
        secret_key: str,
        algorithm: str = "HS256",
        exclude_paths: Optional[Set[str]] = None,
    ) -> None:
        super().__init__(app)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.exclude_paths = exclude_paths or {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through JWT validation."""
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        try:
            token = self._extract_token(request)
            payload = self._validate_token(token)
            request.state.user = payload
            request.state.auth_method = "jwt"
        except AuthError as exc:
            logger.warning(
                "JWT validation failed for %s %s: %s",
                request.method,
                request.url.path,
                exc.message,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.message, "error": "jwt_validation_failed"},
            )

        return await call_next(request)

    def _extract_token(self, request: Request) -> str:
        """Extract JWT token from the Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise AuthError("Missing Authorization header")

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthError(
                "Invalid Authorization header format. Expected 'Bearer <token>'"
            )

        return parts[1]

    def _validate_token(self, token: str) -> dict:
        """Validate the JWT token and return its payload."""
        try:
            import jwt

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError("Token has expired", status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError as exc:
            raise AuthError(f"Invalid token: {str(exc)}", status.HTTP_401_UNAUTHORIZED)
        except ImportError:
            raise AuthError(
                "JWT library not available", status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    Validates API keys provided via X-API-Key header or api_key query parameter.
    Suitable for service-to-service communication and external integrations.
    """

    def __init__(
        self,
        app: ASGIApp,
        valid_api_keys: Optional[Set[str]] = None,
        exclude_paths: Optional[Set[str]] = None,
    ) -> None:
        super().__init__(app)
        self.valid_api_keys = valid_api_keys or set()
        self.exclude_paths = exclude_paths or {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through API key validation."""
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        try:
            api_key = self._extract_api_key(request)
            self._validate_api_key(api_key)
            request.state.api_key = api_key
            request.state.auth_method = "api_key"
        except AuthError as exc:
            logger.warning(
                "API key validation failed for %s %s: %s",
                request.method,
                request.url.path,
                exc.message,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.message, "error": "api_key_validation_failed"},
            )

        return await call_next(request)

    def _extract_api_key(self, request: Request) -> str:
        """Extract API key from header or query parameter."""
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key

        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key

        raise AuthError(
            "Missing API key. Provide it via X-API-Key header or api_key query parameter"
        )

    def _validate_api_key(self, api_key: str) -> None:
        """Validate the API key against the set of valid keys."""
        if api_key not in self.valid_api_keys:
            raise AuthError("Invalid API key", status.HTTP_403_FORBIDDEN)


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Role-Based Access Control (RBAC).

    Enforces role-based permissions on protected routes. Roles and their
    allowed paths are configurable. Must run after authentication middleware.
    """

    def __init__(
        self,
        app: ASGIApp,
        role_permissions: Optional[dict] = None,
        exclude_paths: Optional[Set[str]] = None,
        default_deny: bool = True,
    ) -> None:
        super().__init__(app)
        self.role_permissions = role_permissions or self._default_permissions()
        self.exclude_paths = exclude_paths or {
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
        }
        self.default_deny = default_deny

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through role-based access control."""
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        try:
            user_roles = self._get_user_roles(request)
            if not user_roles:
                raise AuthError(
                    "No roles found for user", status.HTTP_403_FORBIDDEN
                )

            if not self._has_permission(user_roles, request.url.path, request.method):
                logger.warning(
                    "RBAC denied %s %s for roles %s",
                    request.method,
                    request.url.path,
                    user_roles,
                )
                raise AuthError(
                    "Insufficient permissions for this resource",
                    status.HTTP_403_FORBIDDEN,
                )
        except AuthError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.message, "error": "access_denied"},
            )

        return await call_next(request)

    def _get_user_roles(self, request: Request) -> Set[str]:
        """Extract user roles from request state (set by auth middleware)."""
        user = getattr(request.state, "user", None)
        if not user:
            return set()

        roles = user.get("roles", [])
        if isinstance(roles, str):
            return {roles}
        return set(roles)

    def _has_permission(
        self, user_roles: Set[str], path: str, method: str
    ) -> bool:
        """Check if any of the user's roles has permission for the path/method."""
        for role in user_roles:
            allowed = self.role_permissions.get(role, {})
            for pattern, methods in allowed.items():
                if self._path_matches(path, pattern) and method.upper() in methods:
                    return True
        return False

    def _path_matches(self, path: str, pattern: str) -> bool:
        """Check if a path matches a pattern (supports wildcards)."""
        if pattern == path:
            return True
        if pattern.endswith("/*"):
            prefix = pattern[:-2]
            return path.startswith(prefix)
        return False

    @staticmethod
    def _default_permissions() -> dict:
        """Define default role-to-permission mappings."""
        return {
            UserRole.ADMIN.value: {
                "/admin/*": {"GET", "POST", "PUT", "DELETE", "PATCH"},
                "/users/*": {"GET", "POST", "PUT", "DELETE", "PATCH"},
                "/jobs/*": {"GET", "POST", "PUT", "DELETE", "PATCH"},
                "/candidates/*": {"GET", "POST", "PUT", "DELETE", "PATCH"},
                "/applications/*": {"GET", "POST", "PUT", "DELETE", "PATCH"},
                "/reports/*": {"GET", "POST", "PUT", "DELETE", "PATCH"},
                "/settings/*": {"GET", "POST", "PUT", "DELETE", "PATCH"},
            },
            UserRole.RECRUITER.value: {
                "/jobs/*": {"GET", "POST", "PUT", "PATCH"},
                "/candidates/*": {"GET", "POST", "PUT", "PATCH"},
                "/applications/*": {"GET", "POST", "PUT", "PATCH"},
                "/interviews/*": {"GET", "POST", "PUT", "PATCH"},
            },
            UserRole.HIRING_MANAGER.value: {
                "/jobs/*": {"GET", "POST", "PUT", "PATCH"},
                "/candidates/*": {"GET"},
                "/applications/*": {"GET", "PUT", "PATCH"},
                "/interviews/*": {"GET", "POST", "PUT", "PATCH"},
                "/reports/*": {"GET"},
            },
            UserRole.CANDIDATE.value: {
                "/jobs/*": {"GET"},
                "/applications/*": {"GET", "POST"},
                "/profile/*": {"GET", "PUT", "PATCH"},
            },
            UserRole.VIEWER.value: {
                "/jobs/*": {"GET"},
                "/reports/*": {"GET"},
            },
        }


def setup_auth_middleware(
    app: FastAPI,
    jwt_secret_key: str,
    jwt_algorithm: str = "HS256",
    api_keys: Optional[Set[str]] = None,
    role_permissions: Optional[dict] = None,
) -> None:
    """
    Configure and attach all authentication middleware to the FastAPI app.

    Middleware is added in reverse order of execution (last added = first executed).
    RBAC runs first, then API key, then JWT validation.

    Args:
        app: The FastAPI application instance.
        jwt_secret_key: Secret key for JWT validation.
        jwt_algorithm: JWT signing algorithm (default: HS256).
        api_keys: Set of valid API keys for service authentication.
        role_permissions: Custom role-permission mappings.
    """
    # Add in reverse order: last added executes first
    app.add_middleware(
        RBACMiddleware,
        role_permissions=role_permissions,
    )
    app.add_middleware(
        APIKeyMiddleware,
        valid_api_keys=api_keys,
    )
    app.add_middleware(
        JWTValidationMiddleware,
        secret_key=jwt_secret_key,
        algorithm=jwt_algorithm,
    )

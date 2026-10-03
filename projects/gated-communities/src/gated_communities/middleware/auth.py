"""
Authentication and Authorization Middleware for Gated Communities.

Provides:
1. JWT token validation middleware
2. API key authentication middleware
3. Role-based access control (RBAC) middleware
"""

import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

import jwt
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class AuthConfig:
    """Central configuration for authentication middleware."""

    # JWT settings
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: Optional[str] = None
    JWT_ISSUER: Optional[str] = None
    JWT_LEEWAY_SECONDS: int = 30
    JWT_TOKEN_HEADER: str = "Authorization"
    JWT_TOKEN_PREFIX: str = "Bearer"

    # API key settings
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY_QUERY_PARAM: str = "api_key"

    # RBAC settings
    RBAC_DEFAULT_ROLES: List[str] = ["viewer"]

    # Exempt paths (no auth required)
    EXEMPT_PATHS: Set[str] = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/auth/login",
        "/auth/register",
        "/auth/refresh",
    }

    # Role hierarchy (higher inherits lower permissions)
    ROLE_HIERARCHY: Dict[str, int] = {
        "viewer": 0,
        "member": 1,
        "moderator": 2,
        "admin": 3,
        "superadmin": 4,
    }


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthorizationError(Exception):
    """Raised when authorization fails (insufficient permissions)."""

    def __init__(self, message: str, status_code: int = 403):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class JWTValidationError(AuthenticationError):
    """Raised when JWT token validation fails."""


class APIKeyError(AuthenticationError):
    """Raised when API key validation fails."""


# ---------------------------------------------------------------------------
# Role Definitions
# ---------------------------------------------------------------------------

class Role(str, Enum):
    """Standard roles for gated communities."""

    VIEWER = "viewer"
    MEMBER = "member"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


# ---------------------------------------------------------------------------
# 1. JWT Token Validation Middleware
# ---------------------------------------------------------------------------

class JWTValidationMiddleware(BaseHTTPMiddleware):
    """
    Validates JWT tokens from the Authorization header.

    Extracts the Bearer token, validates signature, expiration, and claims.
    Attaches decoded payload to request.state.jwt_payload on success.
    """

    def __init__(
        self,
        app: ASGIApp,
        secret_key: Optional[str] = None,
        algorithm: Optional[str] = None,
        audience: Optional[str] = None,
        issuer: Optional[str] = None,
        leeway: Optional[int] = None,
        exempt_paths: Optional[Set[str]] = None,
    ):
        super().__init__(app)
        self.secret_key = secret_key or AuthConfig.JWT_SECRET_KEY
        self.algorithm = algorithm or AuthConfig.JWT_ALGORITHM
        self.audience = audience or AuthConfig.JWT_AUDIENCE
        self.issuer = issuer or AuthConfig.JWT_ISSUER
        self.leeway = leeway or AuthConfig.JWT_LEEWAY_SECONDS
        self.exempt_paths = exempt_paths or AuthConfig.EXEMPT_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip exempt paths
        if self._is_exempt(request.url.path):
            return await call_next(request)

        try:
            token = self._extract_token(request)
            payload = self._validate_token(token)
            request.state.jwt_payload = payload
            request.state.user_id = payload.get("sub")
            request.state.user_roles = payload.get("roles", AuthConfig.RBAC_DEFAULT_ROLES)
            request.state.auth_method = "jwt"
        except JWTValidationError as exc:
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
        except Exception as exc:
            logger.error("Unexpected error in JWT middleware: %s", exc, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal authentication error", "error": "internal_error"},
            )

        return await call_next(request)

    def _is_exempt(self, path: str) -> bool:
        """Check if the request path is exempt from authentication."""
        return path in self.exempt_paths

    def _extract_token(self, request: Request) -> str:
        """Extract JWT token from the Authorization header."""
        auth_header = request.headers.get(AuthConfig.JWT_TOKEN_HEADER)

        if not auth_header:
            raise JWTValidationError(
                f"Missing {AuthConfig.JWT_TOKEN_HEADER} header"
            )

        parts = auth_header.split()

        if len(parts) == 1:
            # Token without prefix
            return parts[0]

        if len(parts) == 2 and parts[0] == AuthConfig.JWT_TOKEN_PREFIX:
            return parts[1]

        raise JWTValidationError("Invalid authorization header format")

    def _validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return decoded payload."""
        try:
            options: Dict[str, Any] = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "require": ["exp", "iat", "sub"],
            }

            if self.audience:
                options["verify_aud"] = True
            else:
                options["verify_aud"] = False

            if self.issuer:
                options["verify_iss"] = True
            else:
                options["verify_iss"] = False

            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                leeway=self.leeway,
                options=options,
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise JWTValidationError("Token has expired")
        except jwt.InvalidAudienceError:
            raise JWTValidationError("Invalid token audience")
        except jwt.InvalidIssuerError:
            raise JWTValidationError("Invalid token issuer")
        except jwt.InvalidIssuedAtError:
            raise JWTValidationError("Invalid token issued-at time")
        except jwt.InvalidTokenError as exc:
            raise JWTValidationError(f"Invalid token: {str(exc)}")
        except Exception as exc:
            raise JWTValidationError(f"Token validation error: {str(exc)}")


# ---------------------------------------------------------------------------
# 2. API Key Authentication Middleware
# ---------------------------------------------------------------------------

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Authenticates requests using API keys.

    Checks X-API-Key header or api_key query parameter.
    Validates against a store of active API keys.
    Attaches key metadata to request.state.api_key_data on success.
    """

    def __init__(
        self,
        app: ASGIApp,
        api_key_store: Optional[Any] = None,
        exempt_paths: Optional[Set[str]] = None,
        header_name: Optional[str] = None,
        query_param: Optional[str] = None,
    ):
        super().__init__(app)
        self.api_key_store = api_key_store or self._default_key_store()
        self.exempt_paths = exempt_paths or AuthConfig.EXEMPT_PATHS
        self.header_name = header_name or AuthConfig.API_KEY_HEADER
        self.query_param = query_param or AuthConfig.API_KEY_QUERY_PARAM

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip exempt paths
        if self._is_exempt(request.url.path):
            return await call_next(request)

        try:
            api_key = self._extract_api_key(request)
            key_data = await self._validate_api_key(api_key)

            request.state.api_key_data = key_data
            request.state.user_id = key_data.get("user_id")
            request.state.user_roles = key_data.get("roles", AuthConfig.RBAC_DEFAULT_ROLES)
            request.state.auth_method = "api_key"
            request.state.api_key = api_key

        except APIKeyError as exc:
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
        except Exception as exc:
            logger.error("Unexpected error in API key middleware: %s", exc, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal authentication error", "error": "internal_error"},
            )

        return await call_next(request)

    def _is_exempt(self, path: str) -> bool:
        """Check if the request path is exempt from authentication."""
        return path in self.exempt_paths

    def _extract_api_key(self, request: Request) -> str:
        """Extract API key from header or query parameter."""
        # Check header first
        api_key = request.headers.get(self.header_name)
        if api_key:
            return api_key

        # Fall back to query parameter
        api_key = request.query_params.get(self.query_param)
        if api_key:
            return api_key

        raise APIKeyError(
            f"Missing API key (header: {self.header_name} or query param: {self.query_param})"
        )

    async def _validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Validate API key against the key store."""
        if not api_key or not api_key.strip():
            raise APIKeyError("Empty API key")

        # Check key format (basic validation)
        if len(api_key) < 16:
            raise APIKeyError("Invalid API key format")

        # Look up key in store
        key_data = await self._lookup_key(api_key)

        if key_data is None:
            raise APIKeyError("Invalid API key")

        # Check if key is active
        if not key_data.get("is_active", False):
            raise APIKeyError("API key is deactivated")

        # Check expiration
        expires_at = key_data.get("expires_at")
        if expires_at and time.time() > expires_at:
            raise APIKeyError("API key has expired")

        # Check rate limiting (optional)
        rate_limit = key_data.get("rate_limit")
        if rate_limit:
            await self._check_rate_limit(api_key, rate_limit)

        return key_data

    async def _lookup_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Look up API key in the store. Override for custom backends."""
        if hasattr(self.api_key_store, "get"):
            return self.api_key_store.get(api_key)
        if hasattr(self.api_key_store, "get_key"):
            return await self.api_key_store.get_key(api_key)
        if callable(self.api_key_store):
            return self.api_key_store(api_key)
        return None

    async def _check_rate_limit(self, api_key: str, rate_limit: Dict[str, Any]) -> None:
        """Check if the API key has exceeded its rate limit."""
        # Placeholder for rate limiting logic
        # In production, use Redis or similar for distributed rate limiting
        pass

    @staticmethod
    def _default_key_store() -> Dict[str, Dict[str, Any]]:
        """Default in-memory key store. Replace with database in production."""
        return {}


# ---------------------------------------------------------------------------
# 3. Role-Based Access Control (RBAC) Middleware
# ---------------------------------------------------------------------------

class RBACMiddleware(BaseHTTPMiddleware):
    """
    Role-based access control middleware.

    Enforces role requirements on protected routes.
    Supports path-based role requirements and role hierarchy.
    """

    def __init__(
        self,
        app: ASGIApp,
        role_hierarchy: Optional[Dict[str, int]] = None,
        path_roles: Optional[Dict[str, List[str]]] = None,
        default_required_roles: Optional[List[str]] = None,
        exempt_paths: Optional[Set[str]] = None,
    ):
        super().__init__(app)
        self.role_hierarchy = role_hierarchy or AuthConfig.ROLE_HIERARCHY
        self.path_roles = path_roles or {}
        self.default_required_roles = default_required_roles or []
        self.exempt_paths = exempt_paths or AuthConfig.EXEMPT_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip exempt paths
        if self._is_exempt(request.url.path):
            return await call_next(request)

        try:
            # Get user roles from request state (set by auth middleware)
            user_roles = self._get_user_roles(request)

            if not user_roles:
                raise AuthorizationError(
                    "No roles found for user. Ensure authentication middleware runs first."
                )

            # Determine required roles for this path
            required_roles = self._get_required_roles(request.url.path)

            if not required_roles:
                # No specific roles required, allow access
                return await call_next(request)

            # Check if user has sufficient role
            if not self._has_required_role(user_roles, required_roles):
                logger.warning(
                    "RBAC denied for %s %s: user roles=%s, required=%s",
                    request.method,
                    request.url.path,
                    user_roles,
                    required_roles,
                )
                raise AuthorizationError(
                    f"Insufficient permissions. Required roles: {required_roles}"
                )

            # Attach matched role info
            request.state.matched_roles = self._get_matching_roles(user_roles, required_roles)

        except AuthorizationError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.message, "error": "insufficient_permissions"},
            )
        except Exception as exc:
            logger.error("Unexpected error in RBAC middleware: %s", exc, exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal authorization error", "error": "internal_error"},
            )

        return await call_next(request)

    def _is_exempt(self, path: str) -> bool:
        """Check if the request path is exempt from RBAC."""
        return path in self.exempt_paths

    def _get_user_roles(self, request: Request) -> List[str]:
        """Extract user roles from request state."""
        roles = getattr(request.state, "user_roles", None)
        if roles is None:
            return []
        if isinstance(roles, str):
            return [roles]
        return list(roles)

    def _get_required_roles(self, path: str) -> List[str]:
        """Get required roles for a given path."""
        # Direct path match
        if path in self.path_roles:
            return self.path_roles[path]

        # Pattern matching for parameterized paths
        for pattern, roles in self.path_roles.items():
            if self._path_matches(pattern, path):
                return roles

        return self.default_required_roles

    def _path_matches(self, pattern: str, path: str) -> bool:
        """Check if a path matches a pattern (supports wildcards)."""
        if pattern == path:
            return True

        # Simple wildcard matching
        if pattern.endswith("/*"):
            prefix = pattern[:-1]
            return path.startswith(prefix)

        # Path parameter matching (e.g., /communities/{id}/)
        pattern_parts = pattern.split("/")
        path_parts = path.split("/")

        if len(pattern_parts) != len(path_parts):
            return False

        for p_part, path_part in zip(pattern_parts, path_parts):
            if p_part.startswith("{") and p_part.endswith("}"):
                continue  # Path parameter matches anything
            if p_part != path_part:
                return False

        return True

    def _has_required_role(self, user_roles: List[str], required_roles: List[str]) -> bool:
        """Check if user has at least one of the required roles (with hierarchy)."""
        for required in required_roles:
            for user_role in user_roles:
                if self._role_satisfies(user_role, required):
                    return True
        return False

    def _role_satisfies(self, user_role: str, required_role: str) -> bool:
        """Check if user_role satisfies required_role using hierarchy."""
        if user_role == required_role:
            return True

        user_level = self.role_hierarchy.get(user_role, -1)
        required_level = self.role_hierarchy.get(required_role, -1)

        # Higher or equal level satisfies the requirement
        return user_level >= required_level >= 0

    def _get_matching_roles(self, user_roles: List[str], required_roles: List[str]) -> List[str]:
        """Get the list of user roles that match the required roles."""
        matches = []
        for required in required_roles:
            for user_role in user_roles:
                if self._role_satisfies(user_role, required) and user_role not in matches:
                    matches.append(user_role)
        return matches


# ---------------------------------------------------------------------------
# Combined Auth Middleware (convenience)
# ---------------------------------------------------------------------------

class CombinedAuthMiddleware(BaseHTTPMiddleware):
    """
    Combined authentication middleware supporting both JWT and API key auth.

    Tries JWT first, falls back to API key. Attaches user info to request.state.
    """

    def __init__(
        self,
        app: ASGIApp,
        jwt_secret_key: Optional[str] = None,
        jwt_algorithm: Optional[str] = None,
        api_key_store: Optional[Any] = None,
        exempt_paths: Optional[Set[str]] = None,
    ):
        super().__init__(app)
        self.jwt_middleware = JWTValidationMiddleware(
            app,
            secret_key=jwt_secret_key,
            algorithm=jwt_algorithm,
            exempt_paths=exempt_paths,
        )
        self.api_key_middleware = APIKeyAuthMiddleware(
            app,
            api_key_store=api_key_store,
            exempt_paths=exempt_paths,
        )
        self.exempt_paths = exempt_paths or AuthConfig.EXEMPT_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self._is_exempt(request.url.path):
            return await call_next(request)

        # Try JWT first
        auth_header = request.headers.get(AuthConfig.JWT_TOKEN_HEADER, "")
        if auth_header and AuthConfig.JWT_TOKEN_PREFIX in auth_header:
            return await self.jwt_middleware.dispatch(request, call_next)

        # Fall back to API key
        return await self.api_key_middleware.dispatch(request, call_next)

    def _is_exempt(self, path: str) -> bool:
        return path in self.exempt_paths


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def create_jwt_token(
    user_id: str,
    roles: List[str],
    secret_key: Optional[str] = None,
    algorithm: Optional[str] = None,
    expires_in_seconds: int = 3600,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a JWT token for a user."""
    secret = secret_key or AuthConfig.JWT_SECRET_KEY
    algo = algorithm or AuthConfig.JWT_ALGORITHM

    now = time.time()
    payload: Dict[str, Any] = {
        "sub": user_id,
        "roles": roles,
        "iat": now,
        "exp": now + expires_in_seconds,
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, secret, algorithm=algo)


def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get the current authenticated user from request state."""
    user_id = getattr(request.state, "user_id", None)
    roles = getattr(request.state, "user_roles", [])
    auth_method = getattr(request.state, "auth_method", None)

    if not user_id:
        return None

    return {
        "user_id": user_id,
        "roles": roles,
        "auth_method": auth_method,
    }


def require_roles(*roles: str):
    """
    Decorator/dependency factory for requiring specific roles on endpoints.

    Usage as FastAPI dependency:
        @app.get("/admin")
        async def admin_endpoint(user=Depends(require_roles("admin", "superadmin"))):
            ...
    """
    required = list(roles)

    async def role_checker(request: Request) -> Dict[str, Any]:
        user = get_current_user(request)
        if not user:
            raise AuthenticationError("Not authenticated")

        user_roles = user.get("roles", [])
        for req_role in required:
            for user_role in user_roles:
                if user_role == req_role:
                    return user

        raise AuthorizationError(
            f"Insufficient permissions. Required: {required}"
        )

    return role_checker


# ---------------------------------------------------------------------------
# FastAPI Application Setup Helper
# ---------------------------------------------------------------------------

def setup_auth_middleware(
    app: FastAPI,
    jwt_secret_key: Optional[str] = None,
    jwt_algorithm: Optional[str] = None,
    api_key_store: Optional[Any] = None,
    path_roles: Optional[Dict[str, List[str]]] = None,
    exempt_paths: Optional[Set[str]] = None,
) -> FastAPI:
    """
    Set up all authentication middleware on a FastAPI application.

    Order matters: RBAC must run after authentication.
    """
    # Add RBAC middleware first (runs last in the stack)
    app.add_middleware(
        RBACMiddleware,
        path_roles=path_roles,
        exempt_paths=exempt_paths,
    )

    # Add combined auth middleware (runs first in the stack)
    app.add_middleware(
        CombinedAuthMiddleware,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=jwt_algorithm,
        api_key_store=api_key_store,
        exempt_paths=exempt_paths,
    )

    return app

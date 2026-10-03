"""API key authentication middleware for UGC Marketplace."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API key authentication middleware.

    Validates X-API-Key header against configured API keys.
    Supports key rotation and scoped permissions.
    """

    # Paths that don't require API key
    EXCLUDED_PATHS = {
        "/health",
        "/ready",
        "/live",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/api/v1/health/ready",
        "/api/v1/health/live",
    }

    def __init__(
        self,
        app: Any,
        api_keys: dict[str, dict[str, Any]] | None = None,
        header_name: str = "X-API-Key",
    ) -> None:
        """Initialize API key middleware.

        Args:
            app: The ASGI application.
            api_keys: Dictionary of API keys with metadata.
                Format: {"key": {"name": "...", "scopes": [...], "expires_at": ...}}
            header_name: Header name for API key.
        """
        super().__init__(app)
        self.api_keys = api_keys or {}
        self.header_name = header_name

    def _hash_key(self, key: str) -> str:
        """Hash API key for secure comparison.

        Args:
            key: API key to hash.

        Returns:
            Hashed key.
        """
        return hashlib.sha256(key.encode()).hexdigest()

    def _verify_key(self, key: str) -> dict[str, Any] | None:
        """Verify API key.

        Args:
            key: API key to verify.

        Returns:
            Key metadata if valid, None otherwise.
        """
        # In production, this should query a database or cache
        # For now, we use a simple in-memory store
        for key_id, metadata in self.api_keys.items():
            if hmac.compare_digest(key, key_id):
                # Check expiration
                expires_at = metadata.get("expires_at")
                if expires_at and time.time() > expires_at:
                    logger.warning("API key expired", key_id=key_id[:8])
                    return None
                return metadata
        return None

    def _get_scopes(self, key_metadata: dict[str, Any]) -> list[str]:
        """Get scopes for API key.

        Args:
            key_metadata: Key metadata.

        Returns:
            List of scopes.
        """
        return key_metadata.get("scopes", ["read"])

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Process request with API key authentication.

        Args:
            request: The incoming request.
            call_next: The next handler in the chain.

        Returns:
            Response from next handler or authentication error.
        """
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get(self.header_name)

        if not api_key:
            # Also check query parameter for WebSocket support
            api_key = request.query_params.get("api_key")

        if not api_key:
            logger.warning(
                "API key missing",
                path=request.url.path,
                client=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "API key required. Provide it in X-API-Key header."},
            )

        # Verify API key
        key_metadata = self._verify_key(api_key)

        if not key_metadata:
            logger.warning(
                "Invalid API key",
                path=request.url.path,
                client=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid or expired API key."},
            )

        # Store key metadata in request state
        request.state.api_key = key_metadata
        request.state.api_key_scopes = self._get_scopes(key_metadata)
        request.state.user_id = key_metadata.get("user_id")

        return await call_next(request)

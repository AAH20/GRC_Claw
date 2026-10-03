"""Audit logging middleware for UGC Marketplace."""

from __future__ import annotations

import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests for audit purposes.

    Logs include timestamp, method, path, status code, client info,
    and processing time. Sensitive data is redacted.
    """

    # Paths to exclude from audit logging
    EXCLUDED_PATHS = {
        "/health",
        "/ready",
        "/live",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    # Headers to redact
    SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "proxy-authorization"}

    def _redact_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Redact sensitive headers.

        Args:
            headers: Request headers.

        Returns:
            Redacted headers.
        """
        return {
            k: "[REDACTED]" if k.lower() in self.SENSITIVE_HEADERS else v
            for k, v in headers.items()
        }

    def _get_client_info(self, request: Request) -> dict[str, Any]:
        """Get client information from request.

        Args:
            request: The incoming request.

        Returns:
            Client information dictionary.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")

        return {
            "ip": (
                forwarded.split(",")[0].strip()
                if forwarded
                else (real_ip or (request.client.host if request.client else "unknown"))
            ),
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "referer": request.headers.get("Referer"),
        }

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Process request with audit logging.

        Args:
            request: The incoming request.
            call_next: The next handler in the chain.

        Returns:
            Response from next handler.
        """
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.monotonic()
        client_info = self._get_client_info(request)

        try:
            response = await call_next(request)
            duration_ms = (time.monotonic() - start_time) * 1000

            # Get user ID from request state if available
            user_id = getattr(request.state, "user_id", None)

            logger.info(
                "API request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                client_ip=client_info["ip"],
                user_agent=client_info["user_agent"],
                referer=client_info["referer"],
                user_id=user_id,
                query_params=str(request.query_params),
            )

            return response

        except Exception as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                "API request failed",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                duration_ms=round(duration_ms, 2),
                client_ip=client_info["ip"],
                user_agent=client_info["user_agent"],
            )
            raise

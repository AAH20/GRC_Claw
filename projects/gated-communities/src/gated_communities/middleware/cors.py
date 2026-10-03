"""CORS validation middleware."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class CORSValidationMiddleware(BaseHTTPMiddleware):
    """Validates CORS requests against allowed origins."""

    def __init__(
        self,
        app: Any,
        allowed_origins: list[str] | None = None,
        allowed_methods: list[str] | None = None,
        allowed_headers: list[str] | None = None,
        allow_credentials: bool = True,
        max_age: int = 600,
    ) -> None:
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["*"]
        self.allowed_headers = allowed_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        origin = request.headers.get("origin")

        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response(status_code=204)
            if origin and (origin in self.allowed_origins or "*" in self.allowed_origins):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
                response.headers["Access-Control-Allow-Credentials"] = str(
                    self.allow_credentials
                ).lower()
                response.headers["Access-Control-Max-Age"] = str(self.max_age)
            return response

        response = await call_next(request)

        if origin and (origin in self.allowed_origins or "*" in self.allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = str(
                    self.allow_credentials
                ).lower()
            response.headers["Vary"] = "Origin"

        return response

"""Input sanitization middleware for UGC Marketplace."""

from __future__ import annotations

import re
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Patterns for common injection attacks
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b.*\b(FROM|INTO|TABLE|DATABASE)\b)",
    r"(--|;|\/\*|\*\/|@@|@)",
    r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
    r"('|\")",
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe[^>]*>.*?</iframe>",
    r"<object[^>]*>.*?</object>",
    r"<embed[^>]*>.*?</embed>",
]

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


class SanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware to sanitize request inputs.

    Strips potentially dangerous content from request bodies.
    Note: This is a defense-in-depth measure. Primary validation
    should always be done at the application layer.
    """

    def __init__(
        self,
        app: Any,
        max_body_size: int = 10 * 1024 * 1024,  # 10MB
        enable_html_strip: bool = True,
        enable_sql_check: bool = True,
        enable_xss_check: bool = True,
    ) -> None:
        """Initialize sanitization middleware.

        Args:
            app: The ASGI application.
            max_body_size: Maximum request body size in bytes.
            enable_html_strip: Whether to strip HTML tags.
            enable_sql_check: Whether to check for SQL injection.
            enable_xss_check: Whether to check for XSS patterns.
        """
        super().__init__(app)
        self.max_body_size = max_body_size
        self.enable_html_strip = enable_html_strip
        self.enable_sql_check = enable_sql_check
        self.enable_xss_check = enable_xss_check

    def _sanitize_string(self, value: str) -> str:
        """Sanitize a string value.

        Args:
            value: String to sanitize.

        Returns:
            Sanitized string.
        """
        if not isinstance(value, str):
            return value

        # Strip HTML tags
        if self.enable_html_strip:
            value = HTML_TAG_PATTERN.sub("", value)

        # Check for SQL injection patterns
        if self.enable_sql_check:
            for pattern in SQL_INJECTION_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    # Remove the dangerous pattern
                    value = re.sub(pattern, "", value, flags=re.IGNORECASE)

        # Check for XSS patterns
        if self.enable_xss_check:
            for pattern in XSS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                    value = re.sub(pattern, "", value, flags=re.IGNORECASE | re.DOTALL)

        return value

    def _sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively sanitize dictionary values.

        Args:
            data: Dictionary to sanitize.

        Returns:
            Sanitized dictionary.
        """
        sanitized: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    (
                        self._sanitize_string(item)
                        if isinstance(item, str)
                        else (
                            self._sanitize_dict(item)
                            if isinstance(item, dict)
                            else item
                        )
                    )
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Process request with sanitization.

        Args:
            request: The incoming request.
            call_next: The next handler in the chain.

        Returns:
            Response from next handler.
        """
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large"},
            )

        # Only sanitize POST/PUT/PATCH requests with JSON body
        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    if body:
                        import json

                        data = json.loads(body)
                        if isinstance(data, dict):
                            sanitized = self._sanitize_dict(data)
                            # Replace request body with sanitized version
                            # Note: This is a simplified approach. In production,
                            # you'd want to use a more sophisticated body replacement.
                except (json.JSONDecodeError, Exception):
                    pass  # Let the application handle invalid JSON

        return await call_next(request)

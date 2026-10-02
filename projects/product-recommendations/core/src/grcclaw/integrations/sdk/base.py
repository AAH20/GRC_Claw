"""
Base connector class — the foundation for all GRC_Claw connectors.
"""

from __future__ import annotations

import json
import logging
import time
import urllib.request
import urllib.error
import urllib.parse
from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncIterator
from datetime import datetime, timezone

from .config import ConnectorConfig
from .auth import AuthStrategy
from .types import ConnectorMetadata, ConnectorCapability, ConnectorStatus, RequestContext, ResponseContext
from .exceptions import (
    ConnectorError,
    ConnectionError,
    TimeoutError,
    RateLimitError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Abstract base class for all GRC_Claw connectors.

    Provides:
    - HTTP request execution with retry logic
    - Authentication strategy injection
    - Rate limiting
    - Response parsing and error handling
    - Health checking
    - Pagination support
    - Request/response logging
    """

    def __init__(self, config: ConnectorConfig, auth: Optional[AuthStrategy] = None):
        self.config = config
        self.auth = auth
        self._status = ConnectorStatus.UNKNOWN
        self._last_request_time: float = 0.0
        self._request_count: int = 0
        self._error_count: int = 0
        self._rate_limit_tokens: float = float(config.rate_limit.burst_size)
        self._rate_limit_last_update: float = time.monotonic()
        self._metadata = self._define_metadata()

    @abstractmethod
    def _define_metadata(self) -> ConnectorMetadata:
        """Define connector metadata. Must be implemented by subclasses."""
        ...

    @property
    def metadata(self) -> ConnectorMetadata:
        return self._metadata

    @property
    def status(self) -> ConnectorStatus:
        return self._status

    @property
    def request_count(self) -> int:
        return self._request_count

    @property
    def error_count(self) -> int:
        return self._error_count

    def health_check(self) -> dict[str, Any]:
        """Check connector health. Override for custom health checks."""
        return {
            "name": self.config.name,
            "status": self._status.value,
            "healthy": self._status == ConnectorStatus.CONNECTED,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
        }

    def execute(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> ResponseContext:
        """
        Execute an HTTP request through the connector.

        Handles authentication, rate limiting, retries, and error mapping.
        """
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        timeout = timeout or self.config.timeout_seconds

        request_ctx = RequestContext(
            method=method.upper(),
            url=url,
            headers={**self.config.headers, **(headers or {})},
            params=params or {},
            body=body,
            timeout_seconds=timeout,
        )

        # Apply authentication
        if self.auth:
            auth_request = {
                "method": method.upper(),
                "path": path,
                "headers": request_ctx.headers,
                "params": request_ctx.params,
                "body": body,
            }
            auth_result = self.auth.apply(auth_request)
            request_ctx.headers = auth_result.get("headers", request_ctx.headers)
            request_ctx.params = auth_result.get("params", request_ctx.params)

        # Rate limiting
        self._wait_for_rate_limit()

        # Execute with retry
        last_error: Exception | None = None
        for attempt in range(self.config.retry.max_retries + 1):
            try:
                response = self._execute_request(request_ctx)
                self._status = ConnectorStatus.CONNECTED
                return response
            except (ConnectionError, TimeoutError) as e:
                last_error = e
                self._error_count += 1
                if attempt < self.config.retry.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "Request failed (attempt %d/%d): %s. Retrying in %.1fs",
                        attempt + 1,
                        self.config.retry.max_retries + 1,
                        e,
                        delay,
                    )
                    time.sleep(delay)
                else:
                    self._status = ConnectorStatus.ERROR
                    raise
            except RateLimitError:
                self._status = ConnectorStatus.RATE_LIMITED
                raise
            except ConnectorError:
                self._error_count += 1
                self._status = ConnectorStatus.ERROR
                raise

        raise last_error or ConnectorError("Request failed after all retries")

    def get(self, path: str, **kwargs) -> ResponseContext:
        """Convenience method for GET requests."""
        return self.execute("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> ResponseContext:
        """Convenience method for POST requests."""
        return self.execute("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> ResponseContext:
        """Convenience method for PUT requests."""
        return self.execute("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> ResponseContext:
        """Convenience method for PATCH requests."""
        return self.execute("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> ResponseContext:
        """Convenience method for DELETE requests."""
        return self.execute("DELETE", path, **kwargs)

    def paginate(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        page_size: int = 100,
        max_pages: int = 100,
    ) -> list[ResponseContext]:
        """
        Execute a paginated request, following cursor-based pagination.
        """
        results: list[ResponseContext] = []
        cursor: str | None = None
        page = 0

        while page < max_pages:
            page_params = {**(params or {}), "limit": page_size}
            if cursor:
                page_params["cursor"] = cursor

            response = self.get(path, params=page_params)
            results.append(response)

            if not response.pagination_has_more or not response.pagination_cursor:
                break

            cursor = response.pagination_cursor
            page += 1

        return results

    def _execute_request(self, request: RequestContext) -> ResponseContext:
        """Execute a single HTTP request."""
        start_time = time.monotonic()
        self._request_count += 1

        # Build URL with query params
        url = request.url
        if request.params:
            query = urllib.parse.urlencode(request.params)
            url = f"{url}?{query}" if "?" not in url else f"{url}&{query}"

        # Prepare body
        data = None
        if request.body is not None:
            if isinstance(request.body, (dict, list)):
                data = json.dumps(request.body).encode("utf-8")
                request.headers.setdefault("Content-Type", "application/json")
            elif isinstance(request.body, str):
                data = request.body.encode("utf-8")
            elif isinstance(request.body, bytes):
                data = request.body

        # Create request
        req = urllib.request.Request(
            url,
            data=data,
            headers=request.headers,
            method=request.method,
        )

        try:
            with urllib.request.urlopen(req, timeout=request.timeout_seconds) as resp:
                latency_ms = (time.monotonic() - start_time) * 1000
                raw_content = resp.read()
                status_code = resp.getcode()
                resp_headers = dict(resp.getheaders())

                # Parse body
                body = self._parse_response_body(raw_content, resp_headers)

                return ResponseContext(
                    status_code=status_code,
                    headers=resp_headers,
                    body=body,
                    raw_content=raw_content,
                    latency_ms=latency_ms,
                    request=request,
                    is_success=200 <= status_code < 300,
                    rate_limit_remaining=self._extract_rate_limit_remaining(resp_headers),
                    rate_limit_reset=self._extract_rate_limit_reset(resp_headers),
                    pagination_cursor=self._extract_pagination_cursor(body),
                    pagination_has_more=self._extract_pagination_has_more(body),
                )

        except urllib.error.HTTPError as e:
            latency_ms = (time.monotonic() - start_time) * 1000
            raw_content = e.read() if hasattr(e, "read") else b""
            body = self._parse_response_body(raw_content, dict(e.headers) if e.headers else {})

            if e.code == 429:
                retry_after = float(e.headers.get("Retry-After", 60)) if e.headers else 60.0
                raise RateLimitError(
                    f"Rate limit exceeded (HTTP {e.code})",
                    connector=self.config.name,
                    retry_after_seconds=retry_after,
                )
            elif e.code in (401, 403):
                from .exceptions import AuthenticationError
                raise AuthenticationError(
                    f"Authentication failed (HTTP {e.code})",
                    connector=self.config.name,
                )
            elif e.code >= 500:
                raise ConnectionError(
                    f"Server error (HTTP {e.code})",
                    connector=self.config.name,
                    details={"status_code": e.code, "body": body},
                )
            else:
                raise ConnectorError(
                    f"HTTP error {e.code}",
                    connector=self.config.name,
                    details={"status_code": e.code, "body": body},
                )

        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Connection failed: {e.reason}",
                connector=self.config.name,
            ) from e

        except TimeoutError:
            raise TimeoutError(
                f"Request timed out after {request.timeout_seconds}s",
                connector=self.config.name,
            )

    def _parse_response_body(self, raw: bytes, headers: dict[str, str]) -> Any:
        """Parse response body based on content type."""
        content_type = headers.get("Content-Type", headers.get("content-type", "")).lower()

        if not raw:
            return None

        if "application/json" in content_type:
            try:
                return json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return raw.decode("utf-8", errors="replace")
        elif "text/" in content_type or "xml" in content_type:
            return raw.decode("utf-8", errors="replace")
        else:
            try:
                return json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return raw.decode("utf-8", errors="replace")

    def _wait_for_rate_limit(self) -> None:
        """Token bucket rate limiter."""
        now = time.monotonic()
        elapsed = now - self._rate_limit_last_update
        self._rate_limit_last_update = now

        # Replenish tokens
        rate_per_second = self.config.rate_limit.requests_per_minute / 60.0
        self._rate_limit_tokens = min(
            float(self.config.rate_limit.burst_size),
            self._rate_limit_tokens + elapsed * rate_per_second,
        )

        if self._rate_limit_tokens < 1.0:
            sleep_time = (1.0 - self._rate_limit_tokens) / rate_per_second
            time.sleep(sleep_time)
            self._rate_limit_tokens = 0.0
        else:
            self._rate_limit_tokens -= 1.0

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        base = self.config.retry.base_delay_seconds
        if self.config.retry.exponential_backoff:
            delay = base * (2 ** attempt)
        else:
            delay = base
        return min(delay, self.config.retry.max_delay_seconds)

    def _extract_rate_limit_remaining(self, headers: dict[str, str]) -> Optional[int]:
        for key in ("X-RateLimit-Remaining", "X-Rate-Limit-Remaining", "RateLimit-Remaining"):
            if key in headers:
                try:
                    return int(headers[key])
                except (ValueError, TypeError):
                    pass
        return None

    def _extract_rate_limit_reset(self, headers: dict[str, str]) -> Optional[datetime]:
        for key in ("X-RateLimit-Reset", "X-Rate-Limit-Reset", "RateLimit-Reset"):
            if key in headers:
                try:
                    ts = int(headers[key])
                    return datetime.fromtimestamp(ts, tz=timezone.utc)
                except (ValueError, TypeError):
                    pass
        return None

    def _extract_pagination_cursor(self, body: Any) -> Optional[str]:
        if isinstance(body, dict):
            for key in ("next_cursor", "cursor", "nextCursor", "page_token", "pageToken"):
                if key in body:
                    return str(body[key])
            pagination = body.get("pagination", {})
            if isinstance(pagination, dict):
                return pagination.get("next_cursor") or pagination.get("cursor")
        return None

    def _extract_pagination_has_more(self, body: Any) -> bool:
        if isinstance(body, dict):
            for key in ("has_more", "hasMore", "has_next", "hasNext"):
                if key in body:
                    return bool(body[key])
            pagination = body.get("pagination", {})
            if isinstance(pagination, dict):
                return bool(pagination.get("has_more", pagination.get("hasMore", False)))
        return False

    def close(self) -> None:
        """Clean up resources. Override for custom cleanup."""
        self._status = ConnectorStatus.DISCONNECTED

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

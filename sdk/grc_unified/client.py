"""Unified client for all 75 GRC projects.

This module provides :class:`GRCClient`, the primary entry point for
interacting with the GRC API across all projects.  It handles:

- Authentication (API key, bearer token)
- Request retries with exponential backoff
- Automatic pagination
- Connection pooling
- Error mapping to typed exceptions
- Request/response logging

Usage::

    from grc_unified import GRCClient

    client = GRCClient(api_key="your-key")
    projects = client.list_projects()
    for project in projects:
        findings = client.list_findings(project.id)
"""

from __future__ import annotations

import logging
import time
from typing import Any, TypeVar

import httpx

from .config import GRCConfig, get_config
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ConnectionError,
    GRCError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .models import (
    Assessment,
    AuditEntry,
    Control,
    Evidence,
    Finding,
    HealthStatus,
    PageMetadata,
    PaginatedResponse,
    Project,
    ProjectStats,
    ProjectSummary,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type variables for generic paginated responses
# ---------------------------------------------------------------------------

T = TypeVar("T")


class GRCClient:
    """Unified client for the GRC API.

    The client manages HTTP connections, authentication, retries, and
    error handling.  It is safe to reuse across multiple requests and
    can be used as a context manager to ensure proper cleanup.

    Args:
        config: A :class:`GRCConfig` instance.  If ``None``, the default
            configuration is loaded via :func:`grc_unified.config.get_config`.
        api_key: API key for authentication.  Overrides the config value.
        api_base_url: Base URL for the GRC API.  Overrides the config value.
        timeout: Request timeout in seconds.  Overrides the config value.
        max_retries: Maximum retry attempts.  Overrides the config value.
        http_client: An optional pre-configured ``httpx.Client`` for
            dependency injection or testing.

    Example::

        # Simple usage with defaults
        client = GRCClient()

        # With explicit config
        config = GRCConfig(api_key="secret", timeout=60)
        client = GRCClient(config=config)

        # As context manager
        with GRCClient() as client:
            projects = client.list_projects()
    """

    def __init__(
        self,
        config: GRCConfig | None = None,
        *,
        api_key: str | None = None,
        api_base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config or get_config()

        # Apply overrides
        if api_key is not None:
            self._config = self._config.with_overrides(api_key=api_key)
        if api_base_url is not None:
            self._config = self._config.with_overrides(api_base_url=api_base_url)
        if timeout is not None:
            self._config = self._config.with_overrides(timeout=timeout)
        if max_retries is not None:
            self._config = self._config.with_overrides(max_retries=max_retries)

        self._closed = False

        # Build headers
        headers: dict[str, str] = {
            "User-Agent": self._config.user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        headers.update(self._config.extra_headers)

        # Create or use provided HTTP client
        if http_client is not None:
            self._client = http_client
        else:
            self._client = httpx.Client(
                base_url=self._config.api_base_url,
                headers=headers,
                timeout=self._config.timeout,
                verify=self._config.verify_ssl,
            )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> GRCClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        if not self._closed:
            self._client.close()
            self._closed = True

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def config(self) -> GRCConfig:
        """The resolved configuration for this client."""
        return self._config

    @property
    def base_url(self) -> str:
        """The base URL for API requests."""
        return self._config.api_base_url

    # ------------------------------------------------------------------
    # Internal HTTP helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Execute an HTTP request with retries and error mapping.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API path (relative to base_url).
            params: Query parameters.
            json_body: JSON request body.
            headers: Additional headers for this request only.

        Returns:
            The raw ``httpx.Response`` object.

        Raises:
            AuthenticationError: On 401 responses.
            AuthorizationError: On 403 responses.
            NotFoundError: On 404 responses.
            ValidationError: On 422 responses.
            ConflictError: On 409 responses.
            RateLimitError: On 429 responses.
            ServerError: On 5xx responses.
            ConnectionError: On network failures.
            TimeoutError: On request timeouts.
        """
        if self._closed:
            raise GRCError("Client has been closed")

        url = f"{self._config.api_base_url}{path}"
        request_headers = dict(headers or {})

        last_exception: Exception | None = None

        for attempt in range(self._config.max_retries + 1):
            try:
                logger.debug(
                    "HTTP %s %s (attempt %d/%d)",
                    method,
                    url,
                    attempt + 1,
                    self._config.max_retries + 1,
                )

                response = self._client.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    headers=request_headers,
                )

                # Map error responses to typed exceptions
                if response.status_code >= 400:
                    self._raise_for_status(response)

                return response

            except httpx.TimeoutException as exc:
                last_exception = TimeoutError(
                    f"Request to {url} timed out after {self._config.timeout}s",
                    timeout=self._config.timeout,
                )
                logger.warning("Timeout on attempt %d: %s", attempt + 1, exc)

            except httpx.ConnectError as exc:
                last_exception = ConnectionError(
                    f"Failed to connect to {url}: {exc}"
                )
                logger.warning("Connection error on attempt %d: %s", attempt + 1, exc)

            except httpx.HTTPStatusError:
                raise  # Already mapped, don't retry

            except httpx.HTTPError as exc:
                last_exception = GRCError(f"HTTP error: {exc}")
                logger.warning("HTTP error on attempt %d: %s", attempt + 1, exc)

            # Retry with exponential backoff
            if attempt < self._config.max_retries:
                sleep_time = self._config.retry_backoff * (2**attempt)
                logger.debug("Retrying in %.1fs", sleep_time)
                time.sleep(sleep_time)

        # All retries exhausted
        if last_exception is not None:
            raise last_exception
        raise GRCError("Request failed after all retries")

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Map an error response to the appropriate typed exception.

        Args:
            response: The HTTP response with an error status code.

        Raises:
            A subclass of :class:`GRCError` appropriate for the status code.
        """
        status = response.status_code
        body = self._parse_error_body(response)

        message = body.get("message", body.get("error", response.reason_phrase))
        code = body.get("code")
        details = body.get("details", {})

        if status == 401:
            raise AuthenticationError(message, code=code, details=details)
        elif status == 403:
            raise AuthorizationError(message, code=code, details=details)
        elif status == 404:
            raise NotFoundError(message, code=code, details=details)
        elif status == 409:
            raise ConflictError(message, code=code, details=details)
        elif status == 422:
            raise ValidationError(message, code=code, details=details)
        elif status == 429:
            retry_after = None
            if "retry_after" in body:
                try:
                    retry_after = float(body["retry_after"])
                except (ValueError, TypeError):
                    pass
            raise RateLimitError(
                message, retry_after=retry_after, code=code, details=details
            )
        elif status >= 500:
            raise ServerError(
                message, status_code=status, code=code, details=details
            )
        else:
            raise GRCError(
                message, code=code or f"HTTP_{status}", details=details
            )

    @staticmethod
    def _parse_error_body(response: httpx.Response) -> dict[str, Any]:
        """Parse the error response body as JSON, returning an empty dict on failure."""
        try:
            data = response.json()
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    @staticmethod
    def _parse_paginated_response(
        response: httpx.Response, item_type: type[T]
    ) -> PaginatedResponse[T]:
        """Parse a paginated API response into a typed ``PaginatedResponse``.

        Args:
            response: The HTTP response to parse.
            item_type: The Pydantic model class for list items.

        Returns:
            A ``PaginatedResponse`` with typed data and pagination metadata.
        """
        body = response.json()

        # Support both wrapped and unwrapped response formats
        if "data" in body:
            raw_items = body["data"]
            raw_pagination = body.get("pagination", {})
        else:
            raw_items = body if isinstance(body, list) else []
            raw_pagination = {}

        items = [item_type.model_validate(item) for item in raw_items]
        pagination = PageMetadata.model_validate(raw_pagination)

        return PaginatedResponse[T](data=items, pagination=pagination)

    # ------------------------------------------------------------------
    # Project operations
    # ------------------------------------------------------------------

    def list_projects(
        self,
        *,
        page: int = 1,
        page_size: int | None = None,
        status: str | None = None,
        framework: str | None = None,
    ) -> PaginatedResponse[ProjectSummary]:
        """List all projects.

        Args:
            page: Page number (1-indexed).
            page_size: Items per page.  Defaults to config value.
            status: Filter by project status.
            framework: Filter by compliance framework.

        Returns:
            Paginated list of project summaries.
        """
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size or self._config.page_size,
        }
        if status:
            params["status"] = status
        if framework:
            params["framework"] = framework

        response = self._request("GET", "/v1/projects", params=params)
        return self._parse_paginated_response(response, ProjectSummary)

    def get_project(self, project_id: str) -> Project:
        """Get a single project by ID.

        Args:
            project_id: The project identifier.

        Returns:
            The full project representation.

        Raises:
            NotFoundError: If the project does not exist.
        """
        response = self._request("GET", f"/v1/projects/{project_id}")
        return Project.model_validate(response.json())

    def get_project_stats(self, project_id: str) -> ProjectStats:
        """Get aggregate statistics for a project.

        Args:
            project_id: The project identifier.

        Returns:
            Project statistics including control and finding counts.
        """
        response = self._request("GET", f"/v1/projects/{project_id}/stats")
        return ProjectStats.model_validate(response.json())

    # ------------------------------------------------------------------
    # Control operations
    # ------------------------------------------------------------------

    def list_controls(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int | None = None,
        status: str | None = None,
    ) -> PaginatedResponse[Control]:
        """List controls for a project.

        Args:
            project_id: The project identifier.
            page: Page number (1-indexed).
            page_size: Items per page.
            status: Filter by control status.

        Returns:
            Paginated list of controls.
        """
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size or self._config.page_size,
        }
        if status:
            params["status"] = status

        response = self._request(
            "GET", f"/v1/projects/{project_id}/controls", params=params
        )
        return self._parse_paginated_response(response, Control)

    def get_control(self, project_id: str, control_id: str) -> Control:
        """Get a single control by ID.

        Args:
            project_id: The project identifier.
            control_id: The control identifier.

        Returns:
            The control representation.
        """
        response = self._request(
            "GET", f"/v1/projects/{project_id}/controls/{control_id}"
        )
        return Control.model_validate(response.json())

    # ------------------------------------------------------------------
    # Evidence operations
    # ------------------------------------------------------------------

    def list_evidence(
        self,
        project_id: str,
        control_id: str | None = None,
        *,
        page: int = 1,
        page_size: int | None = None,
    ) -> PaginatedResponse[Evidence]:
        """List evidence artifacts for a project or control.

        Args:
            project_id: The project identifier.
            control_id: Optional control ID to filter by.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Paginated list of evidence artifacts.
        """
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size or self._config.page_size,
        }
        if control_id:
            params["control_id"] = control_id

        response = self._request(
            "GET", f"/v1/projects/{project_id}/evidence", params=params
        )
        return self._parse_paginated_response(response, Evidence)

    def get_evidence(self, project_id: str, evidence_id: str) -> Evidence:
        """Get a single evidence artifact by ID.

        Args:
            project_id: The project identifier.
            evidence_id: The evidence identifier.

        Returns:
            The evidence representation.
        """
        response = self._request(
            "GET", f"/v1/projects/{project_id}/evidence/{evidence_id}"
        )
        return Evidence.model_validate(response.json())

    # ------------------------------------------------------------------
    # Finding operations
    # ------------------------------------------------------------------

    def list_findings(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> PaginatedResponse[Finding]:
        """List findings for a project.

        Args:
            project_id: The project identifier.
            page: Page number (1-indexed).
            page_size: Items per page.
            severity: Filter by severity level.
            status: Filter by lifecycle status.

        Returns:
            Paginated list of findings.
        """
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size or self._config.page_size,
        }
        if severity:
            params["severity"] = severity
        if status:
            params["status"] = status

        response = self._request(
            "GET", f"/v1/projects/{project_id}/findings", params=params
        )
        return self._parse_paginated_response(response, Finding)

    def get_finding(self, project_id: str, finding_id: str) -> Finding:
        """Get a single finding by ID.

        Args:
            project_id: The project identifier.
            finding_id: The finding identifier.

        Returns:
            The finding representation.
        """
        response = self._request(
            "GET", f"/v1/projects/{project_id}/findings/{finding_id}"
        )
        return Finding.model_validate(response.json())

    # ------------------------------------------------------------------
    # Assessment operations
    # ------------------------------------------------------------------

    def list_assessments(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int | None = None,
        status: str | None = None,
    ) -> PaginatedResponse[Assessment]:
        """List assessments for a project.

        Args:
            project_id: The project identifier.
            page: Page number (1-indexed).
            page_size: Items per page.
            status: Filter by assessment status.

        Returns:
            Paginated list of assessments.
        """
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size or self._config.page_size,
        }
        if status:
            params["status"] = status

        response = self._request(
            "GET", f"/v1/projects/{project_id}/assessments", params=params
        )
        return self._parse_paginated_response(response, Assessment)

    def get_assessment(self, project_id: str, assessment_id: str) -> Assessment:
        """Get a single assessment by ID.

        Args:
            project_id: The project identifier.
            assessment_id: The assessment identifier.

        Returns:
            The assessment representation.
        """
        response = self._request(
            "GET", f"/v1/projects/{project_id}/assessments/{assessment_id}"
        )
        return Assessment.model_validate(response.json())

    # ------------------------------------------------------------------
    # Audit operations
    # ------------------------------------------------------------------

    def list_audit_entries(
        self,
        project_id: str,
        *,
        page: int = 1,
        page_size: int | None = None,
        action: str | None = None,
    ) -> PaginatedResponse[AuditEntry]:
        """List audit log entries for a project.

        Args:
            project_id: The project identifier.
            page: Page number (1-indexed).
            page_size: Items per page.
            action: Filter by action type.

        Returns:
            Paginated list of audit entries.
        """
        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size or self._config.page_size,
        }
        if action:
            params["action"] = action

        response = self._request(
            "GET", f"/v1/projects/{project_id}/audit", params=params
        )
        return self._parse_paginated_response(response, AuditEntry)

    # ------------------------------------------------------------------
    # Health operations
    # ------------------------------------------------------------------

    def health_check(self, project_id: str | None = None) -> HealthStatus:
        """Check the health of the GRC system or a specific project.

        Args:
            project_id: Optional project ID for project-level health check.

        Returns:
            Health status information.
        """
        if project_id:
            response = self._request(
                "GET", f"/v1/projects/{project_id}/health"
            )
        else:
            response = self._request("GET", "/v1/health")
        return HealthStatus.model_validate(response.json())

    # ------------------------------------------------------------------
    # Pagination helper
    # ------------------------------------------------------------------

    def paginate(
        self,
        fetch_page: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Auto-paginate through all results of a list operation.

        This is a generator that yields individual items, automatically
        fetching subsequent pages as needed.

        Args:
            fetch_page: A callable that returns a ``PaginatedResponse``.
                Typically a bound method like ``client.list_projects``.
            *args: Positional arguments passed to *fetch_page*.
            **kwargs: Keyword arguments passed to *fetch_page*.

        Yields:
            Individual items from all pages.

        Example::

            for project in client.paginate(client.list_projects):
                print(project.name)
        """
        page = 1
        while True:
            kwargs["page"] = page
            response = fetch_page(*args, **kwargs)
            yield from response.data
            if not response.pagination.has_next:
                break
            page += 1

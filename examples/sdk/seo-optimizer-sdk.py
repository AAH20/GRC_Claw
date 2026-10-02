"""
SEO optimization with keyword tracking, rank monitoring, and content suggestions - SDK Example
==============================================================================================

Production-grade Python SDK example demonstrating:
- Authentication (API key and OAuth2)
- CRUD operations with full error handling
- Best practices for production use
- Type hints and comprehensive docstrings
- Logging and monitoring
- Retry logic with exponential backoff
- Context manager support

Usage:
    python seo-optimizer-sdk.py

Environment Variables:
    GRC_API_KEY: API key for authentication
    GRC_CLIENT_ID: OAuth2 client ID (optional)
    GRC_CLIENT_SECRET: OAuth2 client secret (optional)
    GRC_BASE_URL: API base URL (default: https://api.grc.example.com)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# --- Enums ---


class SEOProjectStatus(str, Enum):
    """SEOProject lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Channel(str, Enum):
    """Supported channels."""

    ORGANIC_SEARCH = "organic_search"


class Metric(str, Enum):
    """Available metrics."""

    RANKINGS = "rankings"
    TRAFFIC = "traffic"
    BACKLINKS = "backlinks"
    DOMAIN_AUTHORITY = "domain_authority"
    PAGE_SPEED = "page_speed"


# --- Exceptions ---


class SDKError(Exception):
    """Base exception for SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body or {}

    def __str__(self) -> str:
        if self.status_code:
            return "[" + str(self.status_code) + "] " + self.message
        return self.message


class AuthenticationError(SDKError):
    """Raised when authentication fails (401)."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, status_code=401)


class AuthorizationError(SDKError):
    """Raised when access is denied (403)."""

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message, status_code=403)


class NotFoundError(SDKError):
    """Raised when a resource is not found (404)."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class ValidationError(SDKError):
    """Raised when request validation fails (422)."""

    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message, status_code=422)


class RateLimitError(SDKError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None) -> None:
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ServerError(SDKError):
    """Raised when the server returns a 5xx error."""

    def __init__(self, message: str = "Internal server error", status_code: int = 500) -> None:
        super().__init__(message, status_code=status_code)


class NetworkError(SDKError):
    """Raised when a network-level error occurs."""

    def __init__(self, message: str = "Network error", original_error: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class TimeoutError(SDKError):
    """Raised when a request times out."""

    def __init__(self, message: str = "Request timed out", timeout_seconds: Optional[float] = None) -> None:
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class ConfigurationError(SDKError):
    """Raised when the SDK is misconfigured."""

    def __init__(self, message: str = "SDK configuration error") -> None:
        super().__init__(message)


# --- Data Models ---


@dataclass
class SEOProject:
    """Represents a seo project."""

    id: str
    name: str
    description: str = ""
    status: SEOProjectStatus = SEOProjectStatus.DRAFT
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SEOProject:
        """Create a SEOProject from an API response dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            status=SEOProjectStatus(data.get("status", "draft")),
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at")),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse an ISO datetime string."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API payload dict."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "metadata": self.metadata,
            "tags": self.tags,
        }


# --- API Client ---


class APIClient:
    """Low-level HTTP client with retry logic and error handling."""

    def __init__(
        self,
        base_url: str,
        authenticator: Authenticator,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url: The base URL of the API.
            authenticator: The authenticator instance.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts for transient errors.
        """
        self.base_url = base_url.rstrip("/")
        self.authenticator = authenticator
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = requests.Session()

    def _build_url(self, path: str) -> str:
        """Build a full URL from a path."""
        return self.base_url + path

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers including authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            auth_headers = self.authenticator.get_auth_headers()
            headers.update(auth_headers)
        except AuthenticationError:
            pass
        return headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method.
            path: API path.
            params: Query parameters.
            json: JSON body.
            data: Form data.
            headers: Additional headers.

        Returns:
            The parsed JSON response.

        Raises:
            SDKError: On API errors.
            NetworkError: On network failures.
            TimeoutError: On request timeout.
        """
        url = self._build_url(path)
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        last_error: Optional[Exception] = None
        response: Optional[requests.Response] = None

        for attempt in range(self.max_retries):
            try:
                response = self._session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json,
                    data=data,
                    headers=request_headers,
                    timeout=self.timeout,
                )
                break
            except requests.Timeout as exc:
                last_error = TimeoutError(timeout_seconds=self.timeout)
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning("Timeout, retrying in %ss...", wait_time)
                    time.sleep(wait_time)
                    continue
                raise last_error from exc
            except requests.RequestException as exc:
                last_error = NetworkError(original_error=exc)
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning("Network error, retrying in %ss...", wait_time)
                    time.sleep(wait_time)
                    continue
                raise last_error from exc

        if response is None:
            raise last_error if last_error else NetworkError("Request failed")

        try:
            response_body = response.json()
        except (ValueError, AttributeError):
            response_body = {}

        if not response.ok:
            self._raise_for_status(response.status_code, response_body)

        return response_body

    def _raise_for_status(self, status_code: int, response_body: Optional[Dict[str, Any]] = None) -> None:
        """Raise the appropriate exception for an HTTP status code."""
        message = "Unknown error"
        if response_body and isinstance(response_body, dict):
            message = response_body.get("message", response_body.get("error", message))

        error_map = {
            401: AuthenticationError,
            403: AuthorizationError,
            404: NotFoundError,
            422: ValidationError,
            429: RateLimitError,
        }

        error_cls = error_map.get(status_code)
        if error_cls:
            raise error_cls(message=message, response_body=response_body)

        if status_code >= 500:
            raise ServerError(message=message, status_code=status_code, response_body=response_body)

        if status_code >= 400:
            raise SDKError(message=message, status_code=status_code, response_body=response_body)

    def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", path, params=params)

    def post(self, path: str, *, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", path, json=json, data=data)

    def put(self, path: str, *, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", path, json=json)

    def patch(self, path: str, *, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PATCH request."""
        return self.request("PATCH", path, json=json)

    def delete(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", path, params=params)

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self) -> APIClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()


# --- Authenticator ---


class Authenticator:
    """Handles authentication with the API.

    Supports API key and OAuth2 client credentials authentication.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_url: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the authenticator.

        Args:
            base_url: The base URL of the API.
            api_key: API key for key-based authentication.
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret.
            token_url: OAuth2 token endpoint URL.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url or self.base_url + "/oauth/token"
        self.timeout = timeout
        self._token: Optional[Dict[str, Any]] = None

    @property
    def token(self) -> Optional[Dict[str, Any]]:
        """Get the current auth token, if any."""
        return self._token

    def is_authenticated(self) -> bool:
        """Check if currently authenticated with a valid token."""
        if not self._token:
            return False
        expires_at = self._token.get("expires_at")
        if expires_at:
            return datetime.now().timestamp() < expires_at
        return True

    def authenticate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Authenticate using an API key.

        Args:
            api_key: The API key to authenticate with.

        Returns:
            The authentication token.

        Raises:
            AuthenticationError: If authentication fails.
            NetworkError: If a network error occurs.
            TimeoutError: If the request times out.
        """
        self.api_key = api_key
        try:
            response = requests.post(
                self.base_url + "/auth/api-key",
                json={"api_key": api_key},
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise TimeoutError(timeout_seconds=self.timeout) from exc
        except requests.RequestException as exc:
            raise NetworkError(original_error=exc) from exc

        if response.status_code != 200:
            raise AuthenticationError(
                message="API key authentication failed: " + response.text,
            )

        token_data = response.json()
        token_data["expires_at"] = datetime.now().timestamp() + token_data.get("expires_in", 3600)
        self._token = token_data
        return self._token

    def authenticate_oauth2(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Authenticate using OAuth2 client credentials flow.

        Args:
            client_id: OAuth2 client ID (overrides constructor value).
            client_secret: OAuth2 client secret (overrides constructor value).

        Returns:
            The authentication token.

        Raises:
            AuthenticationError: If authentication fails.
            NetworkError: If a network error occurs.
            TimeoutError: If the request times out.
        """
        cid = client_id or self.client_id
        csecret = client_secret or self.client_secret

        if not cid or not csecret:
            raise AuthenticationError(
                message="client_id and client_secret are required for OAuth2 authentication",
            )

        try:
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": cid,
                    "client_secret": csecret,
                },
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise TimeoutError(timeout_seconds=self.timeout) from exc
        except requests.RequestException as exc:
            raise NetworkError(original_error=exc) from exc

        if response.status_code != 200:
            raise AuthenticationError(
                message="OAuth2 authentication failed: " + response.text,
            )

        token_data = response.json()
        token_data["expires_at"] = datetime.now().timestamp() + token_data.get("expires_in", 3600)
        self._token = token_data
        return self._token

    def refresh_token(self) -> Dict[str, Any]:
        """Refresh the current OAuth2 token.

        Returns:
            The new authentication token.

        Raises:
            AuthenticationError: If no refresh token is available or refresh fails.
        """
        if not self._token or not self._token.get("refresh_token"):
            raise AuthenticationError(message="No refresh token available")

        try:
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._token["refresh_token"],
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise TimeoutError(timeout_seconds=self.timeout) from exc
        except requests.RequestException as exc:
            raise NetworkError(original_error=exc) from exc

        if response.status_code != 200:
            raise AuthenticationError(
                message="Token refresh failed: " + response.text,
            )

        token_data = response.json()
        token_data["expires_at"] = datetime.now().timestamp() + token_data.get("expires_in", 3600)
        self._token = token_data
        return self._token

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests.

        Returns:
            Dictionary of HTTP headers.

        Raises:
            AuthenticationError: If not authenticated.
        """
        if not self.is_authenticated():
            raise AuthenticationError(
                message="Not authenticated. Call authenticate_api_key() or authenticate_oauth2() first.",
            )

        assert self._token is not None
        return {
            "Authorization": self._token.get("token_type", "Bearer") + " " + self._token["access_token"],
        }

    def logout(self) -> None:
        """Clear the current authentication token."""
        self._token = None


# --- Main SDK Client ---


class SESOptimizer:
    """SEO optimization with keyword tracking, rank monitoring, and content suggestions.

    Provides authenticated access to seo project management with
    full CRUD operations, error handling, and best practices.

    Example:
        >>> from seo_optimizer_sdk import SESOptimizer
        >>> sdk = SESOptimizer(
        ...     api_key="your-api-key",
        ...     base_url="https://api.grc.example.com",
        ... )
        >>> sdk.authenticate()
        >>> items = sdk.list()
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the SESOptimizer SDK.

        Args:
            api_key: API key for key-based authentication.
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret.
            base_url: The base URL of the API.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts for transient errors.

        Raises:
            ConfigurationError: If no credentials are provided.
        """
        self.base_url = base_url or os.environ.get("GRC_BASE_URL", "https://api.grc.example.com")
        self.api_key = api_key or os.environ.get("GRC_API_KEY")
        self.client_id = client_id or os.environ.get("GRC_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("GRC_CLIENT_SECRET")

        if not self.api_key and not (self.client_id and self.client_secret):
            raise ConfigurationError(
                message="No credentials configured. Provide api_key or client_id/client_secret.",
            )

        self.authenticator = Authenticator(
            base_url=self.base_url,
            api_key=self.api_key,
            client_id=self.client_id,
            client_secret=self.client_secret,
            timeout=timeout,
        )
        self._api_client = APIClient(
            base_url=self.base_url,
            authenticator=self.authenticator,
            timeout=timeout,
            max_retries=max_retries,
        )

    def authenticate(self) -> Dict[str, Any]:
        """Authenticate with the configured credentials.

        Uses API key if provided, otherwise OAuth2 client credentials.

        Returns:
            The authentication token.

        Raises:
            ConfigurationError: If no credentials are configured.
            AuthenticationError: If authentication fails.
        """
        if self.authenticator.api_key:
            return self.authenticator.authenticate_api_key(self.authenticator.api_key)
        if self.authenticator.client_id and self.authenticator.client_secret:
            return self.authenticator.authenticate_oauth2()
        raise ConfigurationError(
            message="No credentials configured. Provide api_key or client_id/client_secret.",
        )

    def is_authenticated(self) -> bool:
        """Check if the SDK has a valid authentication token."""
        return self.authenticator.is_authenticated()

    def logout(self) -> None:
        """Clear the current authentication token."""
        self.authenticator.logout()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._api_client.close()

    def __enter__(self) -> SESOptimizer:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def create(self, name: str, **kwargs: Any) -> SEOProject:
        """Create a new seo project.

        Args:
            name: The name of the seo project.
            **kwargs: Additional seo project attributes.

        Returns:
            The created SEOProject instance.

        Raises:
            ValidationError: If the seo project data is invalid.
            AuthenticationError: If authentication fails.
            RateLimitError: If rate limit is exceeded.
        """
        payload = {"name": name, **kwargs}
        try:
            response = self._client.post("/seo_projects", json=payload)
            result = SEOProject.from_dict(response["data"])
            logger.info("Created seo project: %s", result.id)
            return result
        except ValidationError:
            logger.error("Validation failed for seo project creation")
            raise
        except AuthenticationError:
            logger.error("Authentication failed during creation")
            raise
        except RateLimitError as e:
            logger.warning("Rate limit hit, retry after %ss", e.retry_after)
            raise

    def list(self, *, page: int = 1, per_page: int = 20, **filters: Any) -> Dict[str, Any]:
        """List seo projects with pagination and filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page.
            **filters: Additional filter parameters.

        Returns:
            Paginated list response with seo projects.

        Raises:
            AuthenticationError: If authentication fails.
            RateLimitError: If rate limit is exceeded.
        """
        params = {"page": page, "per_page": per_page, **filters}
        try:
            response = self._client.get("/seo_projects", params=params)
            items = [SEOProject.from_dict(item) for item in response.get("data", [])]
            return {
                "data": items,
                "total": response.get("total", 0),
                "page": response.get("page", page),
                "per_page": response.get("per_page", per_page),
                "total_pages": response.get("total_pages", 0),
            }
        except AuthenticationError:
            logger.error("Authentication failed during list operation")
            raise
        except RateLimitError as e:
            logger.warning("Rate limit hit, retry after %ss", e.retry_after)
            raise

    def get(self, seo_project_id: str) -> SEOProject:
        """Get a seo project by ID.

        Args:
            seo_project_id: The seo project ID.

        Returns:
            The SEOProject instance.

        Raises:
            NotFoundError: If the seo project is not found.
            AuthenticationError: If authentication fails.
        """
        try:
            response = self._client.get("/seo_projects/{seo_project_id}")
            return SEOProject.from_dict(response["data"])
        except NotFoundError:
            logger.error("SEOProject not found: %s", seo_project_id)
            raise
        except AuthenticationError:
            logger.error("Authentication failed during get operation")
            raise

    def update(self, seo_project_id: str, **kwargs: Any) -> SEOProject:
        """Update an existing seo project.

        Args:
            seo_project_id: The seo project ID.
            **kwargs: Attributes to update.

        Returns:
            The updated SEOProject instance.

        Raises:
            NotFoundError: If the seo project is not found.
            ValidationError: If the update data is invalid.
        """
        try:
            response = self._client.patch("/seo_projects/{seo_project_id}", json=kwargs)
            result = SEOProject.from_dict(response["data"])
            logger.info("Updated seo project: %s", seo_project_id)
            return result
        except NotFoundError:
            logger.error("SEOProject not found: %s", seo_project_id)
            raise
        except ValidationError:
            logger.error("Validation failed for seo project update")
            raise

    def delete(self, seo_project_id: str) -> None:
        """Delete a seo project.

        Args:
            seo_project_id: The seo project ID.

        Raises:
            NotFoundError: If the seo project is not found.
            AuthenticationError: If authentication fails.
        """
        try:
            self._client.delete("/seo_projects/{seo_project_id}")
            logger.info("Deleted seo project: %s", seo_project_id)
        except NotFoundError:
            logger.error("SEOProject not found: %s", seo_project_id)
            raise
        except AuthenticationError:
            logger.error("Authentication failed during delete operation")
            raise

    def analyze(self, seo_project_id: str) -> Dict[str, Any]:
        """Analyze a seo project.

        Args:
            seo_project_id: The seo project ID.

        Returns:
            Analysis results with insights and recommendations.
        """
        try:
            response = self._client.get("/seo_projects/{seo_project_id}/analyze")
            return response.get("data", {})
        except NotFoundError:
            logger.error("SEOProject not found: %s", seo_project_id)
            raise

    def track(self, seo_project_id: str, event: str, **properties: Any) -> None:
        """Track an event for a seo project.

        Args:
            seo_project_id: The seo project ID.
            event: The event name.
            **properties: Event properties.
        """
        payload = {"event": event, "properties": properties}
        try:
            self._client.post("/seo_projects/{seo_project_id}/track", json=payload)
            logger.debug("Tracked event '%s' for seo project %s", event, seo_project_id)
        except NotFoundError:
            logger.error("SEOProject not found: %s", seo_project_id)
            raise



# --- Main ---


def main() -> None:
    """Run the seo-optimizer SDK example."""
    logger.info("=" * 60)
    logger.info("SEO optimization with keyword tracking, rank monitoring, and content suggestions - SDK Example")
    logger.info("=" * 60)

    # Initialize SDK
    sdk = SESOptimizer(
        api_key=os.environ.get("GRC_API_KEY", "grc_live_example_key"),
        base_url=os.environ.get("GRC_BASE_URL", "https://api.grc.example.com"),
    )

    try:
        # Authenticate
        logger.info("Authenticating...")
        token = sdk.authenticate()
        logger.info("Authenticated successfully")

        # Create
        logger.info("\nCreating seo project...")
        item = sdk.create(
            name="Example SEOProject",
            description="Created via SDK example",
            tags=["example", "sdk"],
        )
        logger.info("Created: %s", item.id)

        # List
        logger.info("\nListing seo projects...")
        results = sdk.list(page=1, per_page=10)
        logger.info("Found %d seo projects", results["total"])

        # Get
        logger.info("\nGetting seo project...")
        fetched = sdk.get(item.id)
        logger.info("Fetched: %s", fetched.name)

        # Update
        logger.info("\nUpdating seo project...")
        updated = sdk.update(item.id, description="Updated via SDK example")
        logger.info("Updated: %s", updated.description)

        # Delete
        logger.info("\nDeleting seo project...")
        sdk.delete(item.id)
        logger.info("Deleted successfully")

    except AuthenticationError as e:
        logger.error("Authentication failed: %s", e)
    except AuthorizationError as e:
        logger.error("Authorization failed: %s", e)
    except NotFoundError as e:
        logger.error("Not found: %s", e)
    except ValidationError as e:
        logger.error("Validation failed: %s", e)
    except RateLimitError as e:
        logger.error("Rate limit exceeded: %s", e)
    except ServerError as e:
        logger.error("Server error: %s", e)
    except NetworkError as e:
        logger.error("Network error: %s", e)
    except TimeoutError as e:
        logger.error("Timeout: %s", e)
    except SDKError as e:
        logger.error("SDK error: %s", e)
    finally:
        sdk.close()

    logger.info("\n" + "=" * 60)
    logger.info("Example complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

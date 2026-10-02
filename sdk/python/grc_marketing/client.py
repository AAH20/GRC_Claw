"""Core API client for the GRC Marketing SDK."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from .auth import Authenticator
from .errors import (
    GRCMarketingError,
    NetworkError,
    TimeoutError,
    raise_for_status,
)


class APIClient:
    """Low-level HTTP client for the GRC Marketing API.

    Handles request construction, authentication headers, and error mapping.
    """

    def __init__(
        self,
        base_url: str,
        authenticator: Authenticator,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url: The base URL of the GRC Marketing API.
            authenticator: The authenticator instance.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts for transient errors.
        """
        self.base_url = base_url.rstrip("/")
        self.authenticator = authenticator
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = requests.Session()

    def _build_url(self, path: str) -> str:
        """Build a full URL from a path.

        Args:
            path: The API path.

        Returns:
            The full URL.
        """
        return f"{self.base_url}{path}"

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers including authentication.

        Returns:
            Dictionary of HTTP headers.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            auth_headers = self.authenticator.get_auth_headers()
            headers.update(auth_headers)
        except GRCMarketingError:
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
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API path.
            params: Query parameters.
            json: JSON body.
            data: Form data.
            headers: Additional headers.

        Returns:
            The parsed JSON response.

        Raises:
            GRCMarketingError: On API errors.
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
                    import time

                    time.sleep(2**attempt)
                    continue
                raise last_error from exc
            except requests.RequestException as exc:
                last_error = NetworkError(original_error=exc)
                if attempt < self.max_retries - 1:
                    import time

                    time.sleep(2**attempt)
                    continue
                raise last_error from exc

        if response is None:
            raise last_error if last_error else NetworkError("Request failed")

        try:
            response_body = response.json()
        except (ValueError, AttributeError):
            response_body = {}

        if not response.ok:
            raise_for_status(response.status_code, response_body)

        return response_body

    def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a GET request.

        Args:
            path: API path.
            params: Query parameters.

        Returns:
            The parsed JSON response.
        """
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a POST request.

        Args:
            path: API path.
            json: JSON body.
            data: Form data.

        Returns:
            The parsed JSON response.
        """
        return self.request("POST", path, json=json, data=data)

    def put(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a PUT request.

        Args:
            path: API path.
            json: JSON body.

        Returns:
            The parsed JSON response.
        """
        return self.request("PUT", path, json=json)

    def patch(
        self,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a PATCH request.

        Args:
            path: API path.
            json: JSON body.

        Returns:
            The parsed JSON response.
        """
        return self.request("PATCH", path, json=json)

    def delete(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a DELETE request.

        Args:
            path: API path.
            params: Query parameters.

        Returns:
            The parsed JSON response.
        """
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

"""Authentication module for the GRC Marketing SDK."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests

from .errors import AuthenticationError, NetworkError, TimeoutError
from .types import AuthToken


class Authenticator:
    """Handles authentication with the GRC Marketing API.

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
            base_url: The base URL of the GRC Marketing API.
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
        self.token_url = token_url or f"{self.base_url}/oauth/token"
        self.timeout = timeout
        self._token: Optional[AuthToken] = None

    @property
    def token(self) -> Optional[AuthToken]:
        """Get the current auth token, if any."""
        return self._token

    def is_authenticated(self) -> bool:
        """Check if currently authenticated with a valid token."""
        return self._token is not None and not self._token.is_expired

    def authenticate_api_key(self, api_key: str) -> AuthToken:
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
                f"{self.base_url}/auth/api-key",
                json={"api_key": api_key},
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            raise TimeoutError(timeout_seconds=self.timeout) from exc
        except requests.RequestException as exc:
            raise NetworkError(original_error=exc) from exc

        if response.status_code != 200:
            raise AuthenticationError(
                message=f"API key authentication failed: {response.text}",
            )

        self._token = AuthToken.from_dict(response.json())
        return self._token

    def authenticate_oauth2(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> AuthToken:
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
                message="client_id and client_secret are required for OAuth2 authentication"
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
                message=f"OAuth2 authentication failed: {response.text}",
            )

        self._token = AuthToken.from_dict(response.json())
        return self._token

    def refresh_token(self) -> AuthToken:
        """Refresh the current OAuth2 token.

        Returns:
            The new authentication token.

        Raises:
            AuthenticationError: If no refresh token is available or refresh fails.
        """
        if not self._token or not self._token.refresh_token:
            raise AuthenticationError(message="No refresh token available")

        try:
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._token.refresh_token,
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
                message=f"Token refresh failed: {response.text}",
            )

        self._token = AuthToken.from_dict(response.json())
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
                message="Not authenticated. Call authenticate_api_key() or authenticate_oauth2() first."
            )

        assert self._token is not None
        return {
            "Authorization": f"{self._token.token_type} {self._token.access_token}",
        }

    def logout(self) -> None:
        """Clear the current authentication token."""
        self._token = None

"""
Authentication strategies for connectors.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime, timezone


class AuthStrategy(ABC):
    """Abstract base class for authentication strategies."""

    @abstractmethod
    def apply(self, request: dict[str, Any]) -> dict[str, Any]:
        """Apply authentication to a request dict. Returns modified request."""
        ...

    @abstractmethod
    def refresh(self) -> bool:
        """Refresh authentication tokens if needed. Returns True if refreshed."""
        ...

    @abstractmethod
    def is_expired(self) -> bool:
        """Check if the current auth credentials are expired."""
        ...


@dataclass
class APIKeyAuth(AuthStrategy):
    """API key authentication (header or query param)."""

    api_key: str
    header_name: str = "X-API-Key"
    location: str = "header"  # header, query

    def apply(self, request: dict[str, Any]) -> dict[str, Any]:
        if self.location == "header":
            request.setdefault("headers", {})[self.header_name] = self.api_key
        elif self.location == "query":
            request.setdefault("params", {})[self.header_name] = self.api_key
        return request

    def refresh(self) -> bool:
        return False

    def is_expired(self) -> bool:
        return False


@dataclass
class BearerAuth(AuthStrategy):
    """Bearer token authentication."""

    token: str
    header_name: str = "Authorization"
    prefix: str = "Bearer"

    def apply(self, request: dict[str, Any]) -> dict[str, Any]:
        request.setdefault("headers", {})[self.header_name] = f"{self.prefix} {self.token}"
        return request

    def refresh(self) -> bool:
        return False

    def is_expired(self) -> bool:
        return False


@dataclass
class BasicAuth(AuthStrategy):
    """HTTP Basic authentication."""

    username: str
    password: str

    def apply(self, request: dict[str, Any]) -> dict[str, Any]:
        credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        request.setdefault("headers", {})["Authorization"] = f"Basic {credentials}"
        return request

    def refresh(self) -> bool:
        return False

    def is_expired(self) -> bool:
        return False


@dataclass
class OAuth2Auth(AuthStrategy):
    """OAuth2 client credentials flow authentication."""

    client_id: str
    client_secret: str
    token_url: str
    scope: str = ""
    access_token: str = ""
    refresh_token: str = ""
    expires_at: float = 0.0
    token_type: str = "Bearer"
    _token_fetched_at: float = 0.0

    def __post_init__(self):
        if not self.access_token:
            self._fetch_token()

    def _fetch_token(self) -> None:
        """Fetch a new access token from the token endpoint."""
        import urllib.request
        import urllib.parse
        import json

        data = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
        }).encode()

        req = urllib.request.Request(
            self.token_url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                self.access_token = result.get("access_token", "")
                self.refresh_token = result.get("refresh_token", "")
                self.token_type = result.get("token_type", "Bearer")
                expires_in = result.get("expires_in", 3600)
                self._token_fetched_at = time.time()
                self.expires_at = self._token_fetched_at + expires_in - 60  # 60s buffer
        except Exception as e:
            raise AuthenticationError(f"OAuth2 token fetch failed: {e}") from e

    def apply(self, request: dict[str, Any]) -> dict[str, Any]:
        if self.is_expired():
            self._fetch_token()
        request.setdefault("headers", {})["Authorization"] = f"{self.token_type} {self.access_token}"
        return request

    def refresh(self) -> bool:
        try:
            self._fetch_token()
            return True
        except Exception:
            return False

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at


@dataclass
class HMACAuth(AuthStrategy):
    """HMAC signature authentication."""

    api_key: str
    api_secret: str
    algorithm: str = "sha256"
    include_timestamp: bool = True
    timestamp_header: str = "X-Timestamp"
    signature_header: str = "X-Signature"

    def apply(self, request: dict[str, Any]) -> dict[str, Any]:
        timestamp = str(int(time.time()))
        method = request.get("method", "GET").upper()
        path = request.get("path", "/")
        body = request.get("body", "")

        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")
        elif isinstance(body, dict):
            import json
            body = json.dumps(body, separators=(",", ":"))

        message = f"{method}\n{path}\n{timestamp}\n{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            getattr(hashlib, self.algorithm),
        ).hexdigest()

        headers = request.setdefault("headers", {})
        headers[self.signature_header] = signature
        headers["X-API-Key"] = self.api_key
        if self.include_timestamp:
            headers[self.timestamp_header] = timestamp

        return request

    def refresh(self) -> bool:
        return False

    def is_expired(self) -> bool:
        return False


@dataclass
class JWTAuth(AuthStrategy):
    """JWT token authentication."""

    token: str
    algorithm: str = "HS256"
    claims: dict[str, Any] = field(default_factory=dict)

    def apply(self, request: dict[str, Any]) -> dict[str, Any]:
        request.setdefault("headers", {})["Authorization"] = f"Bearer {self.token}"
        return request

    def refresh(self) -> bool:
        return False

    def is_expired(self) -> bool:
        try:
            import base64
            import json

            parts = self.token.split(".")
            if len(parts) != 3:
                return True

            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            decoded = json.loads(base64.urlsafe_b64decode(payload))
            exp = decoded.get("exp", 0)
            return time.time() >= exp - 60
        except Exception:
            return True


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

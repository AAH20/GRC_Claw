"""OAuth2/OIDC integration for agentic AI marketing security layer.

Provides OAuth2 authorization code flow, OIDC discovery, token exchange,
and PKCE support for secure agent authentication.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse

import httpx


class OAuth2Error(Exception):
    """Base exception for OAuth2 errors."""


class TokenExchangeError(OAuth2Error):
    """Raised when token exchange fails."""


class DiscoveryError(OAuth2Error):
    """Raised when OIDC discovery fails."""


class GrantType(str, Enum):
    """OAuth2 grant types."""

    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"
    DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"


@dataclass(frozen=True)
class OIDCConfiguration:
    """OIDC provider configuration."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    end_session_endpoint: Optional[str] = None
    introspection_endpoint: Optional[str] = None
    registration_endpoint: Optional[str] = None
    scopes_supported: List[str] = field(default_factory=list)
    response_types_supported: List[str] = field(default_factory=list)
    grant_types_supported: List[str] = field(default_factory=list)
    token_endpoint_auth_methods_supported: List[str] = field(default_factory=list)
    claims_supported: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TokenSet:
    """OAuth2 token set."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None
    obtained_at: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Check if access token is expired."""
        return time.time() >= self.obtained_at + self.expires_in - 30  # 30s buffer

    @property
    def scopes(self) -> List[str]:
        """Return list of scopes."""
        return self.scope.split() if self.scope else []


@dataclass(frozen=True)
class PKCEPair:
    """PKCE code verifier and challenge pair."""

    code_verifier: str
    code_challenge: str
    code_challenge_method: str = "S256"


def generate_pkce_pair() -> PKCEPair:
    """Generate a PKCE code verifier and challenge pair."""
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).rstrip(b"=").decode("ascii")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    return PKCEPair(
        code_verifier=code_verifier,
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )


class OAuth2Client:
    """OAuth2/OIDC client for agent authentication."""

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.timeout = timeout
        self._config: Optional[OIDCConfiguration] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "OAuth2Client":
        self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._http_client:
            await self._http_client.aclose()

    async def discover(self, issuer: str) -> OIDCConfiguration:
        """Perform OIDC discovery on the given issuer."""
        if not self._http_client:
            raise OAuth2Error("Client not initialized. Use async context manager.")

        well_known_url = issuer.rstrip("/") + "/.well-known/openid-configuration"
        try:
            response = await self._http_client.get(well_known_url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise DiscoveryError(f"OIDC discovery failed: {exc}") from exc

        data = response.json()
        self._config = OIDCConfiguration(
            issuer=data["issuer"],
            authorization_endpoint=data["authorization_endpoint"],
            token_endpoint=data["token_endpoint"],
            userinfo_endpoint=data.get("userinfo_endpoint", ""),
            jwks_uri=data["jwks_uri"],
            end_session_endpoint=data.get("end_session_endpoint"),
            introspection_endpoint=data.get("introspection_endpoint"),
            registration_endpoint=data.get("registration_endpoint"),
            scopes_supported=data.get("scopes_supported", []),
            response_types_supported=data.get("response_types_supported", []),
            grant_types_supported=data.get("grant_types_supported", []),
            token_endpoint_auth_methods_supported=data.get(
                "token_endpoint_auth_methods_supported", []
            ),
            claims_supported=data.get("claims_supported", []),
        )
        return self._config

    def build_authorization_url(
        self,
        state: str,
        scope: Optional[List[str]] = None,
        pkce_pair: Optional[PKCEPair] = None,
        additional_params: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build the authorization URL for the authorization code flow."""
        if not self._config:
            raise OAuth2Error("OIDC configuration not loaded. Call discover() first.")

        params: Dict[str, str] = {
            "response_type": "code",
            "client_id": self.client_id,
            "state": state,
        }
        if self.redirect_uri:
            params["redirect_uri"] = self.redirect_uri
        if scope:
            params["scope"] = " ".join(scope)
        if pkce_pair:
            params["code_challenge"] = pkce_pair.code_challenge
            params["code_challenge_method"] = pkce_pair.code_challenge_method
        if additional_params:
            params.update(additional_params)

        return f"{self._config.authorization_endpoint}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        pkce_pair: Optional[PKCEPair] = None,
    ) -> TokenSet:
        """Exchange authorization code for tokens."""
        if not self._config:
            raise OAuth2Error("OIDC configuration not loaded. Call discover() first.")
        if not self._http_client:
            raise OAuth2Error("Client not initialized. Use async context manager.")

        data: Dict[str, str] = {
            "grant_type": GrantType.AUTHORIZATION_CODE.value,
            "code": code,
            "client_id": self.client_id,
        }
        if self.redirect_uri:
            data["redirect_uri"] = self.redirect_uri
        if self.client_secret:
            data["client_secret"] = self.client_secret
        if pkce_pair:
            data["code_verifier"] = pkce_pair.code_verifier

        try:
            response = await self._http_client.post(
                self._config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TokenExchangeError(f"Token exchange failed: {exc}") from exc

        token_data = response.json()
        return TokenSet(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in", 3600),
            refresh_token=token_data.get("refresh_token"),
            id_token=token_data.get("id_token"),
            scope=token_data.get("scope"),
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenSet:
        """Refresh an access token using a refresh token."""
        if not self._config:
            raise OAuth2Error("OIDC configuration not loaded. Call discover() first.")
        if not self._http_client:
            raise OAuth2Error("Client not initialized. Use async context manager.")

        data: Dict[str, str] = {
            "grant_type": GrantType.REFRESH_TOKEN.value,
            "refresh_token": refresh_token,
            "client_id": self.client_id,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret

        try:
            response = await self._http_client.post(
                self._config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TokenExchangeError(f"Token refresh failed: {exc}") from exc

        token_data = response.json()
        return TokenSet(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in", 3600),
            refresh_token=token_data.get("refresh_token", refresh_token),
            id_token=token_data.get("id_token"),
            scope=token_data.get("scope"),
        )

    async def client_credentials_grant(
        self,
        scope: Optional[List[str]] = None,
    ) -> TokenSet:
        """Perform client credentials grant."""
        if not self._config:
            raise OAuth2Error("OIDC configuration not loaded. Call discover() first.")
        if not self._http_client:
            raise OAuth2Error("Client not initialized. Use async context manager.")

        data: Dict[str, str] = {
            "grant_type": GrantType.CLIENT_CREDENTIALS.value,
            "client_id": self.client_id,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret
        if scope:
            data["scope"] = " ".join(scope)

        try:
            response = await self._http_client.post(
                self._config.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TokenExchangeError(f"Client credentials grant failed: {exc}") from exc

        token_data = response.json()
        return TokenSet(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in", 3600),
            refresh_token=token_data.get("refresh_token"),
            id_token=token_data.get("id_token"),
            scope=token_data.get("scope"),
        )

    async def introspect_token(self, token: str) -> Dict[str, Any]:
        """Introspect a token to get its metadata."""
        if not self._config or not self._config.introspection_endpoint:
            raise OAuth2Error("Introspection endpoint not available.")
        if not self._http_client:
            raise OAuth2Error("Client not initialized. Use async context manager.")

        data = {
            "token": token,
            "client_id": self.client_id,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret

        try:
            response = await self._http_client.post(
                self._config.introspection_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OAuth2Error(f"Token introspection failed: {exc}") from exc

        return response.json()

    async def get_userinfo(self, access_token: str) -> Dict[str, Any]:
        """Fetch userinfo using an access token."""
        if not self._config:
            raise OAuth2Error("OIDC configuration not loaded. Call discover() first.")
        if not self._http_client:
            raise OAuth2Error("Client not initialized. Use async context manager.")

        try:
            response = await self._http_client.get(
                self._config.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OAuth2Error(f"Userinfo request failed: {exc}") from exc

        return response.json()

    async def end_session(
        self,
        id_token_hint: str,
        post_logout_redirect_uri: Optional[str] = None,
    ) -> str:
        """Build end session URL."""
        if not self._config or not self._config.end_session_endpoint:
            raise OAuth2Error("End session endpoint not available.")

        params: Dict[str, str] = {"id_token_hint": id_token_hint}
        if post_logout_redirect_uri:
            params["post_logout_redirect_uri"] = post_logout_redirect_uri

        return f"{self._config.end_session_endpoint}?{urlencode(params)}"

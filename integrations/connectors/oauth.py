"""Authentication handlers for OAuth1, OAuth2, API-key, JWT, and mTLS."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import secrets
import ssl
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse

import aiohttp
import jwt

from .base import AuthenticationError, ConnectorConfig, ConnectorError

logger = logging.getLogger(__name__)


@dataclass
class TokenInfo:
    """OAuth token information."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None
    obtained_at: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        if self.expires_in is None:
            return False
        # Consider token expired 60 seconds before actual expiry
        return time.time() >= (self.obtained_at + self.expires_in - 60)

    @property
    def expires_at(self) -> Optional[float]:
        """Absolute expiration timestamp."""
        if self.expires_in is None:
            return None
        return self.obtained_at + self.expires_in

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "refresh_token": self.refresh_token,
            "scope": self.scope,
            "id_token": self.id_token,
            "obtained_at": self.obtained_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenInfo:
        """Deserialize from dictionary."""
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
            id_token=data.get("id_token"),
            obtained_at=data.get("obtained_at", time.time()),
        )


class OAuth2Handler:
    """OAuth 2.0 authentication handler.

    Supports authorization code, client credentials, and refresh token flows.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        *,
        authorization_url: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        scope: Optional[List[str]] = None,
        state: Optional[str] = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.authorization_url = authorization_url
        self.redirect_uri = redirect_uri
        self.scope = scope or []
        self.state = state or secrets.token_urlsafe(32)
        self._token: Optional[TokenInfo] = None
        self._lock = asyncio.Lock()

    @property
    def token(self) -> Optional[TokenInfo]:
        """Current token info."""
        return self._token

    def get_authorization_url(self, *, extra_params: Optional[Dict[str, str]] = None) -> str:
        """Build the authorization URL for the authorization code flow.

        Args:
            extra_params: Additional query parameters for the authorization URL.

        Returns:
            Full authorization URL to redirect the user to.
        """
        if not self.authorization_url:
            raise ConnectorError("authorization_url is required for authorization code flow")

        params: Dict[str, str] = {
            "response_type": "code",
            "client_id": self.client_id,
            "state": self.state,
        }
        if self.redirect_uri:
            params["redirect_uri"] = self.redirect_uri
        if self.scope:
            params["scope"] = " ".join(self.scope)
        if extra_params:
            params.update(extra_params)

        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_code(self, code: str, *, session: Optional[aiohttp.ClientSession] = None) -> TokenInfo:
        """Exchange an authorization code for tokens.

        Args:
            code: The authorization code from the callback.
            session: Optional aiohttp session to use.

        Returns:
            TokenInfo with the obtained tokens.

        Raises:
            AuthenticationError: If the token exchange fails.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.redirect_uri:
            data["redirect_uri"] = self.redirect_uri

        token = await self._request_token(data, session=session)
        self._token = token
        return token

    async def client_credentials(self, *, session: Optional[aiohttp.ClientSession] = None) -> TokenInfo:
        """Obtain a token using the client credentials flow.

        Args:
            session: Optional aiohttp session to use.

        Returns:
            TokenInfo with the obtained tokens.
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scope:
            data["scope"] = " ".join(self.scope)

        token = await self._request_token(data, session=session)
        self._token = token
        return token

    async def refresh(self, *, session: Optional[aiohttp.ClientSession] = None) -> TokenInfo:
        """Refresh the access token using the refresh token.

        Args:
            session: Optional aiohttp session to use.

        Returns:
            TokenInfo with the new tokens.

        Raises:
            AuthenticationError: If no refresh token is available or refresh fails.
        """
        if not self._token or not self._token.refresh_token:
            raise AuthenticationError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._token.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        token = await self._request_token(data, session=session)
        # Preserve refresh token if not returned in response
        if not token.refresh_token and self._token:
            token.refresh_token = self._token.refresh_token
        self._token = token
        return token

    async def get_valid_token(self, *, session: Optional[aiohttp.ClientSession] = None) -> str:
        """Get a valid access token, refreshing if necessary.

        Args:
            session: Optional aiohttp session to use.

        Returns:
            Valid access token string.
        """
        async with self._lock:
            if self._token and not self._token.is_expired:
                return self._token.access_token
            if self._token and self._token.refresh_token:
                await self.refresh(session=session)
                return self._token.access_token
            await self.client_credentials(session=session)
            return self._token.access_token  # type: ignore[union-attr]

    async def _request_token(
        self, data: Dict[str, str], *, session: Optional[aiohttp.ClientSession] = None
    ) -> TokenInfo:
        """Make a token request to the token endpoint."""
        close_session = session is None
        session = session or aiohttp.ClientSession()

        try:
            async with session.post(self.token_url, data=data) as resp:
                body = await resp.json()
                if resp.status != 200:
                    error = body.get("error", "unknown")
                    description = body.get("error_description", "")
                    raise AuthenticationError(
                        f"Token request failed: {error} - {description}",
                        status_code=resp.status,
                    )
                return TokenInfo(
                    access_token=body["access_token"],
                    token_type=body.get("token_type", "Bearer"),
                    expires_in=body.get("expires_in"),
                    refresh_token=body.get("refresh_token"),
                    scope=body.get("scope"),
                    id_token=body.get("id_token"),
                )
        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Token request failed: {e}") from e
        finally:
            if close_session:
                await session.close()


class OAuth1Handler:
    """OAuth 1.0a authentication handler.

    Implements the full OAuth 1.0a flow with request signing.
    """

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        *,
        request_token_url: Optional[str] = None,
        authorization_url: Optional[str] = None,
        access_token_url: Optional[str] = None,
        callback_uri: Optional[str] = "oob",
    ) -> None:
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.request_token_url = request_token_url
        self.authorization_url = authorization_url
        self.access_token_url = access_token_url
        self.callback_uri = callback_uri
        self._request_token: Optional[str] = None
        self._request_token_secret: Optional[str] = None
        self._access_token: Optional[str] = None
        self._access_token_secret: Optional[str] = None

    def set_access_token(self, token: str, token_secret: str) -> None:
        """Set the access token directly (e.g., from stored credentials)."""
        self._access_token = token
        self._access_token_secret = token_secret

    async def get_request_token(self, *, session: Optional[aiohttp.ClientSession] = None) -> Tuple[str, str]:
        """Obtain a request token (first step of OAuth 1.0a).

        Returns:
            Tuple of (request_token, request_token_secret).
        """
        if not self.request_token_url:
            raise ConnectorError("request_token_url is required")

        oauth_params = self._base_oauth_params()
        oauth_params["oauth_callback"] = self.callback_uri
        signature = self._sign("POST", self.request_token_url, oauth_params)
        oauth_params["oauth_signature"] = signature

        close_session = session is None
        session = session or aiohttp.ClientSession()
        try:
            async with session.post(
                self.request_token_url,
                headers=self._auth_header(oauth_params),
            ) as resp:
                body = await resp.text()
                if resp.status != 200:
                    raise AuthenticationError(f"Request token failed: {body}", status_code=resp.status)
                parsed = parse_qs(body)
                self._request_token = parsed["oauth_token"][0]
                self._request_token_secret = parsed["oauth_token_secret"][0]
                return self._request_token, self._request_token_secret
        finally:
            if close_session:
                await session.close()

    def get_authorization_url(self) -> str:
        """Get the authorization URL for the user to authorize the app."""
        if not self.authorization_url or not self._request_token:
            raise ConnectorError("authorization_url and request_token are required")
        return f"{self.authorization_url}?oauth_token={self._request_token}"

    async def exchange_for_access_token(
        self,
        verifier: str,
        *,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> Tuple[str, str]:
        """Exchange the request token + verifier for an access token.

        Args:
            verifier: The OAuth verifier from the callback.
            session: Optional aiohttp session.

        Returns:
            Tuple of (access_token, access_token_secret).
        """
        if not self.access_token_url or not self._request_token or not self._request_token_secret:
            raise ConnectorError("access_token_url and request token are required")

        oauth_params = self._base_oauth_params()
        oauth_params["oauth_token"] = self._request_token
        oauth_params["oauth_verifier"] = verifier
        signature = self._sign("POST", self.access_token_url, oauth_params, self._request_token_secret)
        oauth_params["oauth_signature"] = signature

        close_session = session is None
        session = session or aiohttp.ClientSession()
        try:
            async with session.post(
                self.access_token_url,
                headers=self._auth_header(oauth_params),
            ) as resp:
                body = await resp.text()
                if resp.status != 200:
                    raise AuthenticationError(f"Access token exchange failed: {body}", status_code=resp.status)
                parsed = parse_qs(body)
                self._access_token = parsed["oauth_token"][0]
                self._access_token_secret = parsed["oauth_token_secret"][0]
                return self._access_token, self._access_token_secret
        finally:
            if close_session:
                await session.close()

    def sign_request(
        self, method: str, url: str, params: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Sign a request with OAuth 1.0a headers.

        Args:
            method: HTTP method.
            url: Full request URL.
            params: Additional query parameters.

        Returns:
            Dictionary of OAuth authorization header parameters.
        """
        if not self._access_token or not self._access_token_secret:
            raise AuthenticationError("Access token not set")

        oauth_params = self._base_oauth_params()
        oauth_params["oauth_token"] = self._access_token

        # Include query params in signature
        all_params = {**oauth_params}
        if params:
            all_params.update(params)

        parsed = urlparse(url)
        if parsed.query:
            for key, value in parse_qs(parsed.query).items():
                all_params[key] = value[0]

        signature = self._sign(method, url, all_params, self._access_token_secret)
        oauth_params["oauth_signature"] = signature
        return oauth_params

    def _base_oauth_params(self) -> Dict[str, str]:
        """Build base OAuth parameters."""
        return {
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": secrets.token_hex(16),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_version": "1.0",
        }

    def _sign(
        self,
        method: str,
        url: str,
        params: Dict[str, str],
        token_secret: str = "",
    ) -> str:
        """Generate HMAC-SHA1 signature."""
        # Remove query string from URL for signature base
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Sort and encode parameters
        sorted_params = sorted(params.items())
        param_string = urlencode(sorted_params, safe="")

        signature_base = f"{method.upper()}&{self._percent_encode(base_url)}&{self._percent_encode(param_string)}"
        signing_key = f"{self._percent_encode(self.consumer_secret)}&{self._percent_encode(token_secret)}"

        signature = hmac.new(
            signing_key.encode("utf-8"),
            signature_base.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        return base64.b64encode(signature).decode("utf-8")

    def _auth_header(self, oauth_params: Dict[str, str]) -> Dict[str, str]:
        """Build the Authorization header string."""
        header_params = ", ".join(
            f'{self._percent_encode(k)}="{self._percent_encode(v)}"'
            for k, v in sorted(oauth_params.items())
            if k.startswith("oauth_")
        )
        return {"Authorization": f"OAuth {header_params}"}

    @staticmethod
    def _percent_encode(value: str) -> str:
        """Percent-encode a string per RFC 3986."""
        from urllib.parse import quote
        return quote(value, safe="")


class APIKeyAuth:
    """API key authentication handler.

    Supports header-based and query-parameter-based API key authentication.
    """

    def __init__(
        self,
        api_key: str,
        *,
        key_name: str = "X-API-Key",
        location: str = "header",
    ) -> None:
        """
        Args:
            api_key: The API key value.
            key_name: The header name or query parameter name.
            location: Where to place the key - 'header' or 'query'.
        """
        self.api_key = api_key
        self.key_name = key_name
        self.location = location

    def apply(self, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, str]] = None) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Apply the API key to headers or params.

        Returns:
            Tuple of (headers, params) with the API key applied.
        """
        headers = headers or {}
        params = params or {}

        if self.location == "header":
            headers[self.key_name] = self.api_key
        elif self.location == "query":
            params[self.key_name] = self.api_key
        else:
            raise ValueError(f"Invalid location: {self.location}. Must be 'header' or 'query'")

        return headers, params


class JWTAuth:
    """JWT-based authentication handler.

    Supports both client-side JWT generation and validation.
    """

    def __init__(
        self,
        *,
        secret: Optional[str] = None,
        private_key: Optional[str] = None,
        algorithm: str = "HS256",
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        subject: Optional[str] = None,
        expiry_seconds: int = 3600,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Args:
            secret: Secret key for HMAC algorithms.
            private_key: Private key for RSA/ECDSA algorithms.
            algorithm: JWT signing algorithm.
            issuer: Token issuer claim.
            audience: Token audience claim.
            subject: Token subject claim.
            expiry_seconds: Token expiry in seconds.
            extra_claims: Additional claims to include.
        """
        self.secret = secret
        self.private_key = private_key
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.subject = subject
        self.expiry_seconds = expiry_seconds
        self.extra_claims = extra_claims or {}

    def generate_token(self, *, extra_claims: Optional[Dict[str, Any]] = None) -> str:
        """Generate a new JWT token.

        Args:
            extra_claims: Additional claims for this specific token.

        Returns:
            Encoded JWT string.
        """
        now = time.time()
        claims: Dict[str, Any] = {
            "iat": now,
            "exp": now + self.expiry_seconds,
            **self.extra_claims,
        }
        if self.issuer:
            claims["iss"] = self.issuer
        if self.audience:
            claims["aud"] = self.audience
        if self.subject:
            claims["sub"] = self.subject
        if extra_claims:
            claims.update(extra_claims)

        key = self.private_key or self.secret
        if not key:
            raise AuthenticationError("Either secret or private_key must be provided")

        return jwt.encode(claims, key, algorithm=self.algorithm)

    def validate_token(self, token: str, *, verify_exp: bool = True) -> Dict[str, Any]:
        """Validate and decode a JWT token.

        Args:
            token: The JWT string to validate.
            verify_exp: Whether to verify expiration.

        Returns:
            Decoded claims dictionary.

        Raises:
            AuthenticationError: If the token is invalid or expired.
        """
        key = self.private_key or self.secret
        if not key:
            raise AuthenticationError("Either secret or private_key must be provided")

        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
                options={"verify_exp": verify_exp},
            )
            return claims
        except jwt.ExpiredSignatureError as e:
            raise AuthenticationError("Token has expired") from e
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {e}") from e

    def get_auth_header(self, *, extra_claims: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Get an Authorization header with a fresh JWT.

        Returns:
            Dictionary with Authorization header.
        """
        token = self.generate_token(extra_claims=extra_claims)
        return {"Authorization": f"Bearer {token}"}


class mTLSAuth:
    """Mutual TLS authentication handler.

    Creates an SSL context with client certificate for mTLS connections.
    """

    def __init__(
        self,
        cert_file: str,
        key_file: str,
        *,
        ca_file: Optional[str] = None,
        key_password: Optional[str] = None,
    ) -> None:
        """
        Args:
            cert_file: Path to the client certificate file (PEM).
            key_file: Path to the client private key file (PEM).
            ca_file: Optional path to CA certificate for server verification.
            key_password: Optional password for the private key.
        """
        self.cert_file = cert_file
        self.key_file = key_file
        self.ca_file = ca_file
        self.key_password = key_password
        self._ssl_context: Optional[ssl.SSLContext] = None

    def get_ssl_context(self) -> ssl.SSLContext:
        """Get or create the SSL context for mTLS.

        Returns:
            Configured SSLContext with client certificate loaded.
        """
        if self._ssl_context is not None:
            return self._ssl_context

        context = ssl.create_default_context(cafile=self.ca_file)
        context.load_cert_chain(
            certfile=self.cert_file,
            keyfile=self.key_file,
            password=self.key_password,
        )
        context.verify_mode = ssl.CERT_REQUIRED
        self._ssl_context = context
        return context

    def get_connector(self) -> aiohttp.TCPConnector:
        """Get an aiohttp TCPConnector configured for mTLS.

        Returns:
            TCPConnector with the mTLS SSL context.
        """
        return aiohttp.TCPConnector(ssl=self.get_ssl_context())


class AuthManager:
    """Centralized authentication manager.

    Manages multiple authentication methods and provides a unified
    interface for obtaining auth headers.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Any] = {}
        self._default_handler: Optional[str] = None

    def register(self, name: str, handler: Any, *, default: bool = False) -> None:
        """Register an authentication handler.

        Args:
            name: Unique name for this handler.
            handler: The auth handler instance.
            default: Whether this is the default handler.
        """
        self._handlers[name] = handler
        if default or self._default_handler is None:
            self._default_handler = name

    def get_handler(self, name: Optional[str] = None) -> Any:
        """Get a registered handler by name."""
        handler_name = name or self._default_handler
        if not handler_name or handler_name not in self._handlers:
            raise ConnectorError(f"Auth handler not found: {handler_name}")
        return self._handlers[handler_name]

    async def get_auth_headers(
        self, name: Optional[str] = None, *, extra_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Get authentication headers from the specified handler.

        Args:
            name: Handler name (uses default if not specified).
            extra_claims: Additional claims for JWT handlers.

        Returns:
            Dictionary of authentication headers.
        """
        handler = self.get_handler(name)

        if isinstance(handler, OAuth2Handler):
            token = await handler.get_valid_token()
            return {"Authorization": f"Bearer {token}"}

        if isinstance(handler, JWTAuth):
            return handler.get_auth_header(extra_claims=extra_claims)

        if isinstance(handler, APIKeyAuth):
            headers, _ = handler.apply()
            return headers

        if isinstance(handler, OAuth1Handler):
            # OAuth1 requires request-specific signing, return empty here
            return {}

        raise ConnectorError(f"Unsupported auth handler type: {type(handler).__name__}")

    def create_oauth2(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        token_url: str,
        **kwargs: Any,
    ) -> OAuth2Handler:
        """Create and register an OAuth2 handler."""
        handler = OAuth2Handler(client_id, client_secret, token_url, **kwargs)
        self.register(name, handler)
        return handler

    def create_oauth1(
        self,
        name: str,
        consumer_key: str,
        consumer_secret: str,
        **kwargs: Any,
    ) -> OAuth1Handler:
        """Create and register an OAuth1 handler."""
        handler = OAuth1Handler(consumer_key, consumer_secret, **kwargs)
        self.register(name, handler)
        return handler

    def create_api_key(
        self,
        name: str,
        api_key: str,
        **kwargs: Any,
    ) -> APIKeyAuth:
        """Create and register an API key handler."""
        handler = APIKeyAuth(api_key, **kwargs)
        self.register(name, handler)
        return handler

    def create_jwt(
        self,
        name: str,
        **kwargs: Any,
    ) -> JWTAuth:
        """Create and register a JWT handler."""
        handler = JWTAuth(**kwargs)
        self.register(name, handler)
        return handler

    def create_mtls(
        self,
        name: str,
        cert_file: str,
        key_file: str,
        **kwargs: Any,
    ) -> mTLSAuth:
        """Create and register an mTLS handler."""
        handler = mTLSAuth(cert_file, key_file, **kwargs)
        self.register(name, handler)
        return handler

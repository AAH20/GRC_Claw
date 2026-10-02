"""HashiCorp Vault integration for agentic AI marketing security layer.

Provides Vault client, secret engine operations, dynamic credentials,
PKI integration, and transit encryption-as-a-service.
"""

from __future__ import annotations

import json
import ssl
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx


class VaultError(Exception):
    """Base exception for Vault errors."""


class VaultAuthenticationError(VaultError):
    """Raised when Vault authentication fails."""


class VaultSecretError(VaultError):
    """Raised when secret operations fail."""


class VaultConnectionError(VaultError):
    """Raised when Vault connection fails."""


class AuthMethod(str, Enum):
    """Vault authentication methods."""

    TOKEN = "token"
    APP_ROLE = "approle"
    KUBERNETES = "kubernetes"
    LDAP = "ldap"
    USERPASS = "userpass"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class SecretEngine(str, Enum):
    """Vault secret engines."""

    KV_V1 = "kv"
    KV_V2 = "kv-v2"
    DATABASE = "database"
    PKI = "pki"
    TRANSIT = "transit"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    TOTP = "totp"
    SSH = "ssh"


@dataclass(frozen=True)
class VaultConfig:
    """Vault client configuration."""

    url: str = "http://127.0.0.1:8200"
    namespace: Optional[str] = None
    verify_ssl: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass(frozen=True)
class VaultToken:
    """Vault token information."""

    accessor: str
    token: str
    lease_duration: int
    renewable: bool
    policies: List[str] = field(default_factory=list)
    entity_id: Optional[str] = None
    token_type: str = "service"
    orphan: bool = False
    mfa_requirement: Optional[Dict[str, Any]] = None
    num_uses: int = 0


@dataclass(frozen=True)
class VaultSecret:
    """Vault secret data."""

    path: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    lease_id: Optional[str] = None
    lease_duration: int = 0
    renewable: bool = False


@dataclass(frozen=True)
class DatabaseCredentials:
    """Dynamic database credentials."""

    username: str
    password: str
    lease_id: str
    lease_duration: int
    renewable: bool
    last_vault_rotation: Optional[str] = None


class VaultClient:
    """HashiCorp Vault client."""

    def __init__(self, config: Optional[VaultConfig] = None) -> None:
        self.config = config or VaultConfig()
        self._token: Optional[VaultToken] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "VaultClient":
        self._http_client = httpx.AsyncClient(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._http_client:
            await self._http_client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["X-Vault-Token"] = self._token.token
        if self.config.namespace:
            headers["X-Vault-Namespace"] = self.config.namespace
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make a request to Vault."""
        if not self._http_client:
            raise VaultConnectionError("Client not initialized. Use async context manager.")

        url = f"{self.config.url}/v1/{path}"
        headers = self._get_headers()

        for attempt in range(self.config.max_retries):
            try:
                response = await self._http_client.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs,
                )
                response.raise_for_status()
                return response.json() if response.content else {}
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 403:
                    raise VaultAuthenticationError(
                        f"Authentication failed: {exc.response.text}"
                    ) from exc
                if exc.response.status_code >= 500 and attempt < self.config.max_retries - 1:
                    import asyncio
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                raise VaultError(f"Vault request failed: {exc}") from exc
            except httpx.RequestError as exc:
                if attempt < self.config.max_retries - 1:
                    import asyncio
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
                raise VaultConnectionError(f"Vault connection failed: {exc}") from exc

        raise VaultError("Max retries exceeded")

    async def authenticate_token(self, token: str) -> VaultToken:
        """Authenticate using a token."""
        self._http_client = self._http_client or httpx.AsyncClient(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        )
        # Verify token by looking it up
        result = await self._request("POST", "auth/token/lookup-self")
        data = result.get("data", {})
        self._token = VaultToken(
            accessor=data.get("accessor", ""),
            token=token,
            lease_duration=data.get("ttl", 0),
            renewable=data.get("renewable", False),
            policies=data.get("policies", []),
            entity_id=data.get("entity_id"),
            token_type=data.get("type", "service"),
            orphan=data.get("orphan", False),
            num_uses=data.get("num_uses", 0),
        )
        return self._token

    async def authenticate_approle(
        self,
        role_id: str,
        secret_id: str,
    ) -> VaultToken:
        """Authenticate using AppRole."""
        result = await self._request(
            "POST",
            "auth/approle/login",
            json={"role_id": role_id, "secret_id": secret_id},
        )
        auth = result.get("auth", {})
        self._token = VaultToken(
            accessor=auth.get("accessor", ""),
            token=auth.get("client_token", ""),
            lease_duration=auth.get("lease_duration", 0),
            renewable=auth.get("renewable", False),
            policies=auth.get("policies", []),
            entity_id=auth.get("entity_id"),
            token_type=auth.get("token_type", "service"),
            orphan=auth.get("orphan", False),
            num_uses=auth.get("num_uses", 0),
        )
        return self._token

    async def authenticate_kubernetes(
        self,
        role: str,
        jwt: str,
    ) -> VaultToken:
        """Authenticate using Kubernetes service account token."""
        result = await self._request(
            "POST",
            f"auth/kubernetes/login",
            json={"role": role, "jwt": jwt},
        )
        auth = result.get("auth", {})
        self._token = VaultToken(
            accessor=auth.get("accessor", ""),
            token=auth.get("client_token", ""),
            lease_duration=auth.get("lease_duration", 0),
            renewable=auth.get("renewable", False),
            policies=auth.get("policies", []),
            entity_id=auth.get("entity_id"),
            token_type=auth.get("token_type", "service"),
            orphan=auth.get("orphan", False),
            num_uses=auth.get("num_uses", 0),
        )
        return self._token

    async def read_secret(self, path: str, version: Optional[int] = None) -> VaultSecret:
        """Read a secret from KV v2."""
        if version is not None:
            path = f"{path}?version={version}"
        result = await self._request("GET", f"secret/data/{path}")
        data = result.get("data", {})
        metadata = data.get("metadata", {})
        return VaultSecret(
            path=path,
            data=data.get("data", {}),
            metadata=metadata,
        )

    async def write_secret(
        self,
        path: str,
        data: Dict[str, Any],
        cas: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Write a secret to KV v2."""
        payload: Dict[str, Any] = {"data": data}
        if cas is not None:
            payload["options"] = {"cas": cas}
        return await self._request("POST", f"secret/data/{path}", json=payload)

    async def delete_secret(self, path: str, versions: Optional[List[int]] = None) -> None:
        """Delete a secret (KV v2)."""
        if versions:
            await self._request(
                "POST",
                f"secret/delete/{path}",
                json={"versions": versions},
            )
        else:
            await self._request("DELETE", f"secret/data/{path}")

    async def list_secrets(self, path: str = "") -> List[str]:
        """List secrets at a path."""
        result = await self._request("GET", f"secret/metadata/{path}?list=true")
        return result.get("data", {}).get("keys", [])

    async def renew_token(self, increment: int = 0) -> VaultToken:
        """Renew the current token."""
        payload = {}
        if increment > 0:
            payload["increment"] = increment
        result = await self._request("POST", "auth/token/renew-self", json=payload)
        auth = result.get("auth", {})
        self._token = VaultToken(
            accessor=auth.get("accessor", ""),
            token=auth.get("client_token", ""),
            lease_duration=auth.get("lease_duration", 0),
            renewable=auth.get("renewable", False),
            policies=auth.get("policies", []),
            entity_id=auth.get("entity_id"),
            token_type=auth.get("token_type", "service"),
            orphan=auth.get("orphan", False),
            num_uses=auth.get("num_uses", 0),
        )
        return self._token

    async def revoke_token(self, token: Optional[str] = None) -> None:
        """Revoke a token."""
        target = token or (self._token.token if self._token else None)
        if not target:
            raise VaultError("No token to revoke")
        await self._request("POST", "auth/token/revoke-self")

    async def generate_database_credentials(
        self,
        role: str,
        mount_point: str = "database",
    ) -> DatabaseCredentials:
        """Generate dynamic database credentials."""
        result = await self._request("GET", f"{mount_point}/creds/{role}")
        data = result.get("data", {})
        return DatabaseCredentials(
            username=data.get("username", ""),
            password=data.get("password", ""),
            lease_id=result.get("lease_id", ""),
            lease_duration=result.get("lease_duration", 0),
            renewable=result.get("renewable", False),
            last_vault_rotation=data.get("last_vault_rotation"),
        )

    async def transit_encrypt(
        self,
        key_name: str,
        plaintext: bytes,
        mount_point: str = "transit",
    ) -> str:
        """Encrypt data using Vault transit engine."""
        import base64
        plaintext_b64 = base64.b64encode(plaintext).decode("ascii")
        result = await self._request(
            "POST",
            f"{mount_point}/encrypt/{key_name}",
            json={"plaintext": plaintext_b64},
        )
        return result.get("data", {}).get("ciphertext", "")

    async def transit_decrypt(
        self,
        key_name: str,
        ciphertext: str,
        mount_point: str = "transit",
    ) -> bytes:
        """Decrypt data using Vault transit engine."""
        import base64
        result = await self._request(
            "POST",
            f"{mount_point}/decrypt/{key_name}",
            json={"ciphertext": ciphertext},
        )
        plaintext_b64 = result.get("data", {}).get("plaintext", "")
        return base64.b64decode(plaintext_b64)

    async def transit_rotate_key(
        self,
        key_name: str,
        mount_point: str = "transit",
    ) -> None:
        """Rotate a transit key."""
        await self._request(
            "POST",
            f"{mount_point}/keys/{key_name}/rotate",
        )

    async def pki_issue_certificate(
        self,
        role: str,
        common_name: str,
        ttl: str = "24h",
        mount_point: str = "pki",
    ) -> Dict[str, Any]:
        """Issue a certificate from Vault PKI."""
        result = await self._request(
            "POST",
            f"{mount_point}/issue/{role}",
            json={"common_name": common_name, "ttl": ttl},
        )
        return result.get("data", {})

    async def enable_secret_engine(
        self,
        engine: SecretEngine,
        path: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Enable a secret engine."""
        payload: Dict[str, Any] = {"type": engine.value}
        if config:
            payload.update(config)
        await self._request("POST", f"sys/mounts/{path}", json=payload)

    async def enable_auth_method(
        self,
        method: AuthMethod,
        path: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Enable an auth method."""
        payload: Dict[str, Any] = {"type": method.value}
        if config:
            payload.update(config)
        await self._request("POST", f"sys/auth/{path}", json=payload)

    async def create_policy(self, name: str, policy: str) -> None:
        """Create a Vault policy."""
        await self._request(
            "POST",
            f"sys/policy/{name}",
            json={"policy": policy},
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check Vault health."""
        if not self._http_client:
            self._http_client = httpx.AsyncClient(
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
        url = f"{self.config.url}/v1/sys/health"
        response = await self._http_client.get(url)
        return response.json()

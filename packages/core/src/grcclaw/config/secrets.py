"""Secret management integration for GRC_Claw.

Provides a unified interface for resolving secrets from multiple
backends: environment variables, AWS Secrets Manager, HashiCorp Vault,
Azure Key Vault, and Docker secrets.

Secret references in configuration use the format:
    ${secret:backend://path/to/secret}

Examples:
    ${secret:env://DATABASE_PASSWORD}
    ${secret:aws://prod/grc-claw/database#password}
    ${secret:vault://secret/data/grc-claw#api_key}
    ${secret:azure://my-vault/api-key}
    ${secret:file:///run/secrets/db_password}
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .exceptions import SecretError


# ─── Secret Reference Parsing ───────────────────────────────────────────────

SECRET_PATTERN = re.compile(r"\$\{secret:([^}]+)\}")


@dataclass
class SecretReference:
    """A parsed secret reference."""

    raw: str
    backend: str
    path: str
    key: Optional[str] = None

    @classmethod
    def parse(cls, raw: str) -> SecretReference:
        """Parse a secret reference string.

        Args:
            raw: Secret reference like ``${secret:env://DATABASE_PASSWORD}``

        Returns:
            Parsed SecretReference.

        Raises:
            SecretError: If the reference format is invalid.
        """
        match = SECRET_PATTERN.match(raw)
        if not match:
            raise SecretError(
                f"Invalid secret reference format: {raw}",
                secret_ref=raw,
            )

        uri = match.group(1)
        if "://" not in uri:
            raise SecretError(
                f"Secret reference must include backend scheme: {raw}",
                secret_ref=raw,
            )

        backend, _, path = uri.partition("://")

        # Extract key from fragment or hash
        key: Optional[str] = None
        if "#" in path:
            path, _, key = path.partition("#")

        return cls(raw=raw, backend=backend, path=path, key=key)

    def __str__(self) -> str:
        return self.raw


def find_secret_refs(value: Any) -> list[SecretReference]:
    """Recursively find all secret references in a value.

    Args:
        value: Any value (dict, list, str, etc.) to scan.

    Returns:
        List of found SecretReference objects.
    """
    refs: list[SecretReference] = []

    if isinstance(value, str):
        for match in SECRET_PATTERN.finditer(value):
            try:
                refs.append(SecretReference.parse(match.group(0)))
            except SecretError:
                pass
    elif isinstance(value, dict):
        for v in value.values():
            refs.extend(find_secret_refs(v))
    elif isinstance(value, (list, tuple)):
        for item in value:
            refs.extend(find_secret_refs(item))

    return refs


# ─── Secret Manager Base ────────────────────────────────────────────────────


class SecretManager(ABC):
    """Abstract base class for secret management backends."""

    @abstractmethod
    def resolve(self, ref: SecretReference) -> str:
        """Resolve a secret reference to its value.

        Args:
            ref: The secret reference to resolve.

        Returns:
            The secret value as a string.

        Raises:
            SecretError: If the secret cannot be resolved.
        """
        ...

    def resolve_in_value(self, value: Any) -> Any:
        """Resolve all secret references within a value.

        Args:
            value: Value that may contain secret references.

        Returns:
            Value with all secret references resolved.
        """
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self.resolve_in_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve_in_value(item) for item in value]
        return value

    def _resolve_string(self, value: str) -> str:
        """Resolve secret references in a string."""
        def replacer(match: re.Match) -> str:
            try:
                ref = SecretReference.parse(match.group(0))
                return self.resolve(ref)
            except SecretError:
                return match.group(0)

        return SECRET_PATTERN.sub(replacer, value)


# ─── Environment Variable Secrets ──────────────────────────────────────────


class EnvVarSecretManager(SecretManager):
    """Resolve secrets from environment variables.

    Format: ``${secret:env://VARIABLE_NAME}``
    """

    def resolve(self, ref: SecretReference) -> str:
        if ref.backend != "env":
            raise SecretError(
                f"EnvVarSecretManager cannot resolve backend '{ref.backend}'",
                secret_ref=ref.raw,
                backend=ref.backend,
            )

        var_name = ref.path
        value = os.environ.get(var_name)
        if value is None:
            raise SecretError(
                f"Environment variable not set: {var_name}",
                secret_ref=ref.raw,
                backend=ref.backend,
            )
        return value


# ─── File-based Secrets ────────────────────────────────────────────────────


class FileSecretManager(SecretManager):
    """Resolve secrets from files (e.g., Docker secrets).

    Format: ``${secret:file:///path/to/secret_file}``
    """

    def __init__(self, base_path: Optional[str | Path] = None):
        self.base_path = Path(base_path) if base_path else None

    def resolve(self, ref: SecretReference) -> str:
        if ref.backend != "file":
            raise SecretError(
                f"FileSecretManager cannot resolve backend '{ref.backend}'",
                secret_ref=ref.raw,
                backend=ref.backend,
            )

        file_path = Path(ref.path)
        if self.base_path and not file_path.is_absolute():
            file_path = self.base_path / file_path

        try:
            return file_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            raise SecretError(
                f"Secret file not found: {file_path}",
                secret_ref=ref.raw,
                backend=ref.backend,
            )
        except OSError as e:
            raise SecretError(
                f"Failed to read secret file {file_path}: {e}",
                secret_ref=ref.raw,
                backend=ref.backend,
            )


# ─── AWS Secrets Manager ───────────────────────────────────────────────────


class AWSSecretsManager(SecretManager):
    """Resolve secrets from AWS Secrets Manager.

    Format: ``${secret:aws://secret-name#json-key}``
    """

    def __init__(
        self,
        region: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
    ):
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-initialize the boto3 client."""
        if self._client is not None:
            return self._client

        try:
            import boto3
        except ImportError:
            raise SecretError(
                "boto3 is required for AWS Secrets Manager. Install with: pip install boto3",
                backend="aws",
            )

        kwargs: dict[str, Any] = {"region_name": self.region}
        if self.access_key_id and self.secret_access_key:
            kwargs["aws_access_key_id"] = self.access_key_id
            kwargs["aws_secret_access_key"] = self.secret_access_key

        self._client = boto3.client("secretsmanager", **kwargs)
        return self._client

    def resolve(self, ref: SecretReference) -> str:
        if ref.backend != "aws":
            raise SecretError(
                f"AWSSecretsManager cannot resolve backend '{ref.backend}'",
                secret_ref=ref.raw,
                backend=ref.backend,
            )

        try:
            client = self._get_client()
            response = client.get_secret_value(SecretId=ref.path)
        except Exception as e:
            raise SecretError(
                f"Failed to retrieve secret from AWS: {e}",
                secret_ref=ref.raw,
                backend=ref.backend,
            )

        secret_string = response.get("SecretString")
        if secret_string is None:
            raise SecretError(
                f"AWS secret has no string value: {ref.path}",
                secret_ref=ref.raw,
                backend=ref.backend,
            )

        # If a key is specified, parse as JSON and extract
        if ref.key:
            try:
                data = json.loads(secret_string)
                if ref.key not in data:
                    raise SecretError(
                        f"Key '{ref.key}' not found in AWS secret: {ref.path}",
                        secret_ref=ref.raw,
                        backend=ref.backend,
                    )
                return str(data[ref.key])
            except json.JSONDecodeError:
                raise SecretError(
                    f"AWS secret is not valid JSON: {ref.path}",
                    secret_ref=ref.raw,
                    backend=ref.backend,
                )

        return secret_string


# ─── HashiCorp Vault ───────────────────────────────────────────────────────


class HashiCorpVaultManager(SecretManager):
    """Resolve secrets from HashiCorp Vault.

    Format: ``${secret:vault://secret/data/path#key}``
    """

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        role: Optional[str] = None,
        mount_point: str = "secret",
    ):
        self.url = url or os.environ.get("VAULT_ADDR", "http://localhost:8200")
        self.token = token or os.environ.get("VAULT_TOKEN")
        self.role = role or os.environ.get("VAULT_ROLE")
        self.mount_point = mount_point
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-initialize the hvac client."""
        if self._client is not None:
            return self._client

        try:
            import hvac
        except ImportError:
            raise SecretError(
                "hvac is required for HashiCorp Vault. Install with: pip install hvac",
                backend="vault",
            )

        self._client = hvac.Client(url=self.url, token=self.token)
        return self._client

    def resolve(self, ref: SecretReference) -> str:
        if ref.backend != "vault":
            raise SecretError(
                f"HashiCorpVaultManager cannot resolve backend '{ref.backend}'",
                secret_ref=ref.raw,
                backend=ref.backend,
            )

        try:
            client = self._get_client()
            # Path format: secret/data/path -> mount_point + /data/ + path
            if ref.path.startswith("data/"):
                # KV v2 format
                full_path = ref.path
            else:
                full_path = f"data/{ref.path}"

            response = client.secrets.kv.v2.read_secret_version(
                path=full_path,
                mount_point=self.mount_point,
            )
        except Exception as e:
            raise SecretError(
                f"Failed to retrieve secret from Vault: {e}",
                secret_ref=ref.raw,
                backend=ref.backend,
            )

        data = response.get("data", {}).get("data", {})
        if not data:
            raise SecretError(
                f"No data found in Vault secret: {ref.path}",
                secret_ref=ref.raw,
                backend=ref.backend,
            )

        if ref.key:
            if ref.key not in data:
                raise SecretError(
                    f"Key '{ref.key}' not found in Vault secret: {ref.path}",
                    secret_ref=ref.raw,
                    backend=ref.backend,
                )
            return str(data[ref.key])

        # Return first value if no key specified
        if data:
            return str(next(iter(data.values())))

        raise SecretError(
            f"Vault secret is empty: {ref.path}",
            secret_ref=ref.raw,
            backend=ref.backend,
        )


# ─── Azure Key Vault ───────────────────────────────────────────────────────


class AzureKeyVaultManager(SecretManager):
    """Resolve secrets from Azure Key Vault.

    Format: ``${secret:azure://vault-name/secret-name}``
    """

    def __init__(
        self,
        vault_url: Optional[str] = None,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.vault_url = vault_url or os.environ.get("AZURE_KEY_VAULT_URL")
        self.tenant_id = tenant_id or os.environ.get("AZURE_TENANT_ID")
        self.client_id = client_id or os.environ.get("AZURE_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("AZURE_CLIENT_SECRET")
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-initialize the Azure client."""
        if self._client is not None:
            return self._client

        try:
            from azure.identity import ClientSecretCredential
            from azure.keyvault.secrets import SecretClient
        except ImportError:
            raise SecretError(
                "azure-identity and azure-keyvault-secrets are required. "
                "Install with: pip install azure-identity azure-keyvault-secrets",
                backend="azure",
            )

        if not self.vault_url:
            raise SecretError(
                "Azure Key Vault URL is required",
                backend="azure",
            )

        credential = ClientSecretCredential(
            tenant_id=self.tenant_id or "",
            client_id=self.client_id or "",
            client_secret=self.client_secret or "",
        )
        self._client = SecretClient(vault_url=self.vault_url, credential=credential)
        return self._client

    def resolve(self, ref: SecretReference) -> str:
        if ref.backend != "azure":
            raise SecretError(
                f"AzureKeyVaultManager cannot resolve backend '{ref.backend}'",
                secret_ref=ref.raw,
                backend=ref.backend,
            )

        try:
            client = self._get_client()
            # Path format: vault-name/secret-name
            parts = ref.path.split("/", 1)
            if len(parts) != 2:
                raise SecretError(
                    f"Invalid Azure Key Vault path: {ref.path}. Expected: vault-name/secret-name",
                    secret_ref=ref.raw,
                    backend="azure",
                )

            secret = client.get_secret(parts[1])
            return secret.value or ""
        except SecretError:
            raise
        except Exception as e:
            raise SecretError(
                f"Failed to retrieve secret from Azure Key Vault: {e}",
                secret_ref=ref.raw,
                backend="azure",
            )


# ─── Composite Secret Manager ──────────────────────────────────────────────


class CompositeSecretManager(SecretManager):
    """Try multiple secret managers in order.

    Each manager is tried in sequence until one succeeds. This allows
    falling back from a cloud provider to environment variables.
    """

    def __init__(self, managers: Optional[list[SecretManager]] = None):
        self.managers: list[SecretManager] = managers or []

    def add_manager(self, manager: SecretManager) -> None:
        """Add a manager to the chain."""
        self.managers.append(manager)

    def resolve(self, ref: SecretReference) -> str:
        """Resolve using the first manager that can handle the backend."""
        errors: list[str] = []

        for manager in self.managers:
            try:
                return manager.resolve(ref)
            except SecretError as e:
                errors.append(str(e))
                continue

        raise SecretError(
            f"All secret managers failed to resolve {ref.raw}: {'; '.join(errors)}",
            secret_ref=ref.raw,
        )


# ─── Factory ───────────────────────────────────────────────────────────────


def create_default_secret_manager() -> CompositeSecretManager:
    """Create a composite secret manager with all available backends.

    Order: env vars -> file -> AWS -> Vault -> Azure
    """
    composite = CompositeSecretManager()
    composite.add_manager(EnvVarSecretManager())
    composite.add_manager(FileSecretManager())

    # Only add cloud providers if their SDKs are available
    try:
        import boto3  # noqa: F401
        composite.add_manager(AWSSecretsManager())
    except ImportError:
        pass

    try:
        import hvac  # noqa: F401
        composite.add_manager(HashiCorpVaultManager())
    except ImportError:
        pass

    try:
        import azure.keyvault.secrets  # noqa: F401
        composite.add_manager(AzureKeyVaultManager())
    except ImportError:
        pass

    return composite

"""Kubernetes secret injection for agentic AI marketing security layer.

Provides secure secret injection into Kubernetes pods, sidecar integration,
secret volume management, and automatic secret rotation.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class InjectionError(Exception):
    """Base exception for secret injection errors."""


class SecretNotFoundError(InjectionError):
    """Raised when a secret is not found."""


class InjectionValidationError(InjectionError):
    """Raised when injection validation fails."""


class InjectionMethod(str, Enum):
    """Secret injection methods."""

    ENV_VAR = "env_var"
    VOLUME = "volume"
    SIDECAR = "sidecar"
    CSI_DRIVER = "csi_driver"
    EXTERNAL_SECRETS = "external_secrets"


class SecretFormat(str, Enum):
    """Secret formats."""

    PLAIN = "plain"
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV_FILE = "env_file"


@dataclass(frozen=True)
class SecretReference:
    """Reference to a secret."""

    name: str
    key: Optional[str] = None
    version: Optional[str] = None
    source: str = "vault"


@dataclass(frozen=True)
class InjectionConfig:
    """Secret injection config."""

    method: InjectionMethod
    secret_ref: SecretReference
    target_path: Optional[str] = None
    target_env: Optional[str] = None
    format: SecretFormat = SecretFormat.PLAIN
    template: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class InjectedSecret:
    """An injected secret."""

    name: str
    value: str
    method: InjectionMethod
    injected_at: float
    expires_at: Optional[float] = None
    version: Optional[str] = None
    checksum: Optional[str] = None


class KubernetesSecretInjector:
    """Injects secrets into Kubernetes pods."""

    def __init__(self, namespace: str = "default") -> None:
        self.namespace = namespace
        self._injected_secrets: Dict[str, InjectedSecret] = {}

    def create_env_var_injection(
        self,
        secret_ref: SecretReference,
        env_var_name: str,
    ) -> Dict[str, Any]:
        """Create environment variable injection config."""
        return {
            "name": env_var_name,
            "valueFrom": {
                "secretKeyRef": {
                    "name": secret_ref.name,
                    "key": secret_ref.key or secret_ref.name,
                }
            }
        }

    def create_volume_injection(
        self,
        secret_ref: SecretReference,
        volume_name: str,
        mount_path: str,
        optional: bool = False,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Create volume injection config."""
        volume = {
            "name": volume_name,
            "secret": {
                "secretName": secret_ref.name,
                "optional": optional,
            }
        }

        volume_mount = {
            "name": volume_name,
            "mountPath": mount_path,
            "readOnly": True,
        }

        return volume, volume_mount

    def create_csi_volume(
        self,
        secret_ref: SecretReference,
        volume_name: str,
        mount_path: str,
        driver: str = "secrets-store.csi.k8s.io",
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Create CSI driver volume injection."""
        volume = {
            "name": volume_name,
            "csi": {
                "driver": driver,
                "readOnly": True,
                "volumeAttributes": {
                    "secretProviderClass": secret_ref.name,
                }
            }
        }

        volume_mount = {
            "name": volume_name,
            "mountPath": mount_path,
            "readOnly": True,
        }

        return volume, volume_mount

    def create_external_secrets_config(
        self,
        secret_ref: SecretReference,
        refresh_interval: str = "1h",
    ) -> Dict[str, Any]:
        """Create ExternalSecrets operator config."""
        return {
            "apiVersion": "external-secrets.io/v1beta1",
            "kind": "ExternalSecret",
            "metadata": {
                "name": secret_ref.name,
                "namespace": self.namespace,
            },
            "spec": {
                "refreshInterval": refresh_interval,
                "secretStoreRef": {
                    "name": "vault-backend",
                    "kind": "ClusterSecretStore",
                },
                "target": {
                    "name": secret_ref.name,
                    "creationPolicy": "Owner",
                },
                "data": [
                    {
                        "secretKey": secret_ref.key or secret_ref.name,
                        "remoteRef": {
                            "key": secret_ref.name,
                            "version": secret_ref.version or "latest",
                        }
                    }
                ]
            }
        }

    def inject_secret(
        self,
        config: InjectionConfig,
        secret_value: str,
    ) -> InjectedSecret:
        """Inject a secret into a pod."""
        checksum = hashlib.sha256(secret_value.encode()).hexdigest()

        injected = InjectedSecret(
            name=config.secret_ref.name,
            value=secret_value,
            method=config.method,
            injected_at=time.time(),
            version=config.secret_ref.version,
            checksum=checksum,
        )

        self._injected_secrets[config.secret_ref.name] = injected
        return injected

    def create_pod_spec_with_secrets(
        self,
        base_spec: Dict[str, Any],
        configs: List[InjectionConfig],
        secret_values: Dict[str, str],
    ) -> Dict[str, Any]:
        """Create a pod spec with injected secrets."""
        spec = json.loads(json.dumps(base_spec))  # Deep copy

        containers = spec.get("spec", {}).get("containers", [])
        if not containers:
            raise InjectionValidationError("Pod spec must have at least one container")

        container = containers[0]

        for config in configs:
            secret_value = secret_values.get(config.secret_ref.name)
            if secret_value is None:
                raise SecretNotFoundError(
                    f"Secret value not found for {config.secret_ref.name}"
                )

            self.inject_secret(config, secret_value)

            if config.method == InjectionMethod.ENV_VAR:
                env_var = self.create_env_var_injection(
                    config.secret_ref, config.target_env or config.secret_ref.name
                )
                container.setdefault("env", []).append(env_var)

            elif config.method == InjectionMethod.VOLUME:
                volume, volume_mount = self.create_volume_injection(
                    config.secret_ref,
                    f"secret-{config.secret_ref.name}",
                    config.target_path or f"/etc/secrets/{config.secret_ref.name}",
                )
                spec["spec"].setdefault("volumes", []).append(volume)
                container.setdefault("volumeMounts", []).append(volume_mount)

            elif config.method == InjectionMethod.CSI_DRIVER:
                volume, volume_mount = self.create_csi_volume(
                    config.secret_ref,
                    f"secret-{config.secret_ref.name}",
                    config.target_path or f"/etc/secrets/{config.secret_ref.name}",
                )
                spec["spec"].setdefault("volumes", []).append(volume)
                container.setdefault("volumeMounts", []).append(volume_mount)

        return spec

    def create_secret_resource(
        self,
        name: str,
        secret_type: str = "Opaque",
        data: Optional[Dict[str, str]] = None,
        string_data: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Kubernetes Secret resource."""
        secret = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "namespace": self.namespace,
            },
            "type": secret_type,
        }

        if labels:
            secret["metadata"]["labels"] = labels

        if data:
            secret["data"] = {
                k: base64.b64encode(v.encode()).decode()
                for k, v in data.items()
            }

        if string_data:
            secret["stringData"] = string_data

        return secret

    def rotate_injected_secret(
        self,
        name: str,
        new_value: str,
    ) -> InjectedSecret:
        """Rotate an injected secret."""
        old = self._injected_secrets.get(name)
        if not old:
            raise SecretNotFoundError(f"Secret '{name}' not found in injected secrets")

        checksum = hashlib.sha256(new_value.encode()).hexdigest()

        rotated = InjectedSecret(
            name=name,
            value=new_value,
            method=old.method,
            injected_at=time.time(),
            version=old.version,
            checksum=checksum,
        )

        self._injected_secrets[name] = rotated
        return rotated

    def get_injected_secret(self, name: str) -> Optional[InjectedSecret]:
        """Get an injected secret by name."""
        return self._injected_secrets.get(name)

    def list_injected_secrets(self) -> List[InjectedSecret]:
        """List all injected secrets."""
        return list(self._injected_secrets.values())

    def verify_secret_integrity(self, name: str) -> bool:
        """Verify the integrity of an injected secret."""
        secret = self._injected_secrets.get(name)
        if not secret:
            return False
        current_checksum = hashlib.sha256(secret.value.encode()).hexdigest()
        return current_checksum == secret.checksum


class SecretInjectionSidecar:
    """Sidecar container for secret injection."""

    def __init__(
        self,
        image: str = "grc-security/secret-injector:latest",
        resources: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.image = image
        self.resources = resources or {
            "limits": {"cpu": "100m", "memory": "128Mi"},
            "requests": {"cpu": "50m", "memory": "64Mi"},
        }

    def create_sidecar_container(
        self,
        secret_refs: List[SecretReference],
        mount_path: str = "/shared/secrets",
    ) -> Dict[str, Any]:
        """Create a sidecar container spec."""
        env_vars = []
        for ref in secret_refs:
            env_vars.append({
                "name": f"SECRET_{ref.name.upper()}",
                "value": ref.name,
            })

        return {
            "name": "secret-injector",
            "image": self.image,
            "env": env_vars,
            "volumeMounts": [
                {
                    "name": "shared-secrets",
                    "mountPath": mount_path,
                    "readOnly": True,
                }
            ],
            "resources": self.resources,
            "securityContext": {
                "readOnlyRootFilesystem": True,
                "runAsNonRoot": True,
                "runAsUser": 1000,
                "allowPrivilegeEscalation": False,
            },
        }

    def create_shared_volume(self) -> Dict[str, Any]:
        """Create a shared emptyDir volume."""
        return {
            "name": "shared-secrets",
            "emptyDir": {
                "medium": "Memory",
                "sizeLimit": "10Mi",
            }
        }

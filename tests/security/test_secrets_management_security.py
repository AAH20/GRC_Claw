"""Secrets management security tests for GRC_Claw.

Tests secret generation, storage, rotation, and injection to ensure
secrets are managed securely throughout their lifecycle.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
import time
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Set, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from secrets.management import (
    InMemorySecretStore,
    RotationError,
    RotationPolicy,
    RotationPolicyError,
    RotationRecord,
    RotationStrategy,
    Secret,
    SecretError,
    SecretGenerator,
    SecretMetadata,
    SecretNotFoundError,
    SecretRotationManager,
    SecretStatus,
    SecretStore,
    SecretType,
)
from secrets.injection import (
    InjectionConfig,
    InjectionError,
    InjectionMethod,
    InjectionValidationError,
    InjectedSecret,
    KubernetesSecretInjector,
    SecretFormat,
    SecretInjectionSidecar,
    SecretNotFoundError as InjectionSecretNotFoundError,
    SecretReference,
)


# ===========================================================================
# Secret Generator Tests
# ===========================================================================


class TestSecretGenerator:
    """Tests for secure secret generation."""

    def test_generate_api_key_length(self) -> None:
        """Verify API key generation produces correct length."""
        key = SecretGenerator.generate_api_key(length=64)
        assert len(key) >= 64

    def test_generate_api_key_uniqueness(self) -> None:
        """Verify generated API keys are unique."""
        keys = [SecretGenerator.generate_api_key() for _ in range(100)]
        assert len(set(keys)) == 100

    def test_generate_api_key_url_safe(self) -> None:
        """Verify API keys are URL-safe."""
        key = SecretGenerator.generate_api_key()
        import string
        url_safe_chars = string.ascii_letters + string.digits + "-_"
        assert all(c in url_safe_chars for c in key)

    def test_generate_password_default(self) -> None:
        """Verify default password generation."""
        password = SecretGenerator.generate_password()
        assert len(password) == 32

    def test_generate_password_custom_length(self) -> None:
        """Verify password generation with custom length."""
        password = SecretGenerator.generate_password(length=64)
        assert len(password) == 64

    def test_generate_password_character_sets(self) -> None:
        """Verify password contains characters from all enabled sets."""
        password = SecretGenerator.generate_password(
            length=100,
            use_uppercase=True,
            use_lowercase=True,
            use_digits=True,
            use_special=True,
        )
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    def test_generate_password_no_uppercase(self) -> None:
        """Verify password generation without uppercase."""
        password = SecretGenerator.generate_password(
            length=100,
            use_uppercase=False,
        )
        assert not any(c.isupper() for c in password)

    def test_generate_password_no_lowercase(self) -> None:
        """Verify password generation without lowercase."""
        password = SecretGenerator.generate_password(
            length=100,
            use_lowercase=False,
        )
        assert not any(c.islower() for c in password)

    def test_generate_password_no_digits(self) -> None:
        """Verify password generation without digits."""
        password = SecretGenerator.generate_password(
            length=100,
            use_digits=False,
        )
        assert not any(c.isdigit() for c in password)

    def test_generate_password_no_special(self) -> None:
        """Verify password generation without special characters."""
        password = SecretGenerator.generate_password(
            length=100,
            use_special=False,
        )
        assert not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    def test_generate_password_no_charsets_raises(self) -> None:
        """Verify that disabling all character sets raises an error."""
        with pytest.raises(SecretError, match="At least one character set"):
            SecretGenerator.generate_password(
                use_uppercase=False,
                use_lowercase=False,
                use_digits=False,
                use_special=False,
            )

    def test_generate_token(self) -> None:
        """Verify token generation."""
        token = SecretGenerator.generate_token(length=32)
        assert len(token) == 64  # hex encoding doubles length

    def test_generate_encryption_key(self) -> None:
        """Verify encryption key generation."""
        key = SecretGenerator.generate_encryption_key(length=32)
        assert len(key) == 64  # hex encoding

    def test_generate_secret_by_type(self) -> None:
        """Verify secret generation by type."""
        api_key = SecretGenerator.generate_secret(SecretType.API_KEY)
        assert len(api_key) > 0
        password = SecretGenerator.generate_secret(SecretType.PASSWORD)
        assert len(password) > 0

    def test_generate_secret_unsupported_type_raises(self) -> None:
        """Verify unsupported secret type raises an error."""
        with pytest.raises(SecretError, match="No generator"):
            SecretGenerator.generate_secret(SecretType.CERTIFICATE)


# ===========================================================================
# Secret Store Tests
# ===========================================================================


class TestSecretStore:
    """Tests for secret storage operations."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_secret(self) -> None:
        """Verify storing and retrieving a secret."""
        store = InMemorySecretStore()
        now = time.time()
        secret = Secret(
            metadata=SecretMetadata(
                id="secret-1",
                name="test-secret",
                type=SecretType.API_KEY,
                created_at=now,
                updated_at=now,
            ),
            value="secret-value-123",
        )
        await store.store(secret)
        retrieved = await store.retrieve("secret-1")
        assert retrieved is not None
        assert retrieved.value == "secret-value-123"

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_secret(self) -> None:
        """Verify retrieving non-existent secret returns None."""
        store = InMemorySecretStore()
        result = await store.retrieve("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_secret(self) -> None:
        """Verify deleting a secret."""
        store = InMemorySecretStore()
        now = time.time()
        secret = Secret(
            metadata=SecretMetadata(
                id="secret-1",
                name="test-secret",
                type=SecretType.API_KEY,
                created_at=now,
                updated_at=now,
            ),
            value="secret-value",
        )
        await store.store(secret)
        assert await store.retrieve("secret-1") is not None
        await store.delete("secret-1")
        assert await store.retrieve("secret-1") is None

    @pytest.mark.asyncio
    async def test_list_secrets(self) -> None:
        """Verify listing all secrets."""
        store = InMemorySecretStore()
        now = time.time()
        for i in range(3):
            secret = Secret(
                metadata=SecretMetadata(
                    id=f"secret-{i}",
                    name=f"test-secret-{i}",
                    type=SecretType.API_KEY,
                    created_at=now,
                    updated_at=now,
                ),
                value=f"value-{i}",
            )
            await store.store(secret)
        secrets = await store.list_secrets()
        assert len(secrets) == 3

    @pytest.mark.asyncio
    async def test_get_versions(self) -> None:
        """Verify getting all versions of a secret."""
        store = InMemorySecretStore()
        now = time.time()
        for i in range(3):
            secret = Secret(
                metadata=SecretMetadata(
                    id="secret-1",
                    name="test-secret",
                    type=SecretType.API_KEY,
                    created_at=now,
                    updated_at=now,
                    version=i + 1,
                ),
                value=f"value-{i}",
            )
            await store.store(secret)
        versions = store.get_versions("secret-1")
        assert len(versions) == 3

    @pytest.mark.asyncio
    async def test_store_overwrites_same_id(self) -> None:
        """Verify storing with same ID overwrites previous value."""
        store = InMemorySecretStore()
        now = time.time()
        secret1 = Secret(
            metadata=SecretMetadata(
                id="secret-1",
                name="test-secret",
                type=SecretType.API_KEY,
                created_at=now,
                updated_at=now,
            ),
            value="old-value",
        )
        secret2 = Secret(
            metadata=SecretMetadata(
                id="secret-1",
                name="test-secret",
                type=SecretType.API_KEY,
                created_at=now,
                updated_at=now,
            ),
            value="new-value",
        )
        await store.store(secret1)
        await store.store(secret2)
        retrieved = await store.retrieve("secret-1")
        assert retrieved.value == "new-value"


# ===========================================================================
# Secret Rotation Tests
# ===========================================================================


class TestSecretRotation:
    """Tests for secret rotation management."""

    @pytest.mark.asyncio
    async def test_rotate_secret(self) -> None:
        """Verify secret rotation creates new version."""
        store = InMemorySecretStore()
        now = time.time()
        secret = Secret(
            metadata=SecretMetadata(
                id="secret-1",
                name="test-secret",
                type=SecretType.API_KEY,
                created_at=now,
                updated_at=now,
                version=1,
            ),
            value="old-value",
        )
        await store.store(secret)
        policy = RotationPolicy(
            name="test-policy",
            secret_type=SecretType.API_KEY,
            interval_seconds=3600,
            strategy=RotationStrategy.AUTOMATIC,
        )
        manager = SecretRotationManager(store)
        manager.register_policy(policy)
        record = await manager.rotate_secret("secret-1", "test-policy")
        assert record.old_version == 1
        assert record.new_version == 2
        assert record.status == "success"

    @pytest.mark.asyncio
    async def test_rotate_nonexistent_secret_raises(self) -> None:
        """Verify rotating non-existent secret raises an error."""
        store = InMemorySecretStore()
        policy = RotationPolicy(
            name="test-policy",
            secret_type=SecretType.API_KEY,
            interval_seconds=3600,
            strategy=RotationStrategy.AUTOMATIC,
        )
        manager = SecretRotationManager(store)
        manager.register_policy(policy)
        with pytest.raises(SecretNotFoundError):
            await manager.rotate_secret("nonexistent", "test-policy")

    @pytest.mark.asyncio
    async def test_rotate_with_nonexistent_policy_raises(self) -> None:
        """Verify rotating with non-existent policy raises an error."""
        store = InMemorySecretStore()
        now = time.time()
        secret = Secret(
            metadata=SecretMetadata(
                id="secret-1",
                name="test-secret",
                type=SecretType.API_KEY,
                created_at=now,
                updated_at=now,
            ),
            value="value",
        )
        await store.store(secret)
        manager = SecretRotationManager(store)
        with pytest.raises(RotationError, match="not found"):
            await manager.rotate_secret("secret-1", "nonexistent-policy")

    def test_register_policy_minimum_interval(self) -> None:
        """Verify rotation policy enforces minimum interval."""
        manager = SecretRotationManager(InMemorySecretStore())
        with pytest.raises(RotationPolicyError, match="at least 1 hour"):
            manager.register_policy(
                RotationPolicy(
                    name="bad-policy",
                    secret_type=SecretType.API_KEY,
                    interval_seconds=1800,  # 30 minutes
                    strategy=RotationStrategy.AUTOMATIC,
                )
            )

    @pytest.mark.asyncio
    async def test_check_expired_secrets(self) -> None:
        """Verify detection of expired secrets."""
        store = InMemorySecretStore()
        now = time.time()
        expired_secret = Secret(
            metadata=SecretMetadata(
                id="expired-1",
                name="expired-secret",
                type=SecretType.API_KEY,
                created_at=now - 86400 * 2,
                updated_at=now - 86400 * 2,
                expires_at=now - 86400,  # Expired yesterday
            ),
            value="expired-value",
        )
        valid_secret = Secret(
            metadata=SecretMetadata(
                id="valid-1",
                name="valid-secret",
                type=SecretType.API_KEY,
                created_at=now,
                updated_at=now,
                expires_at=now + 86400,
            ),
            value="valid-value",
        )
        await store.store(expired_secret)
        await store.store(valid_secret)
        manager = SecretRotationManager(store)
        expired = await manager.check_expired_secrets()
        assert len(expired) == 1
        assert expired[0].id == "expired-1"

    @pytest.mark.asyncio
    async def test_check_secrets_due_for_rotation(self) -> None:
        """Verify detection of secrets due for rotation."""
        store = InMemorySecretStore()
        now = time.time()
        policy = RotationPolicy(
            name="test-policy",
            secret_type=SecretType.API_KEY,
            interval_seconds=3600,
            strategy=RotationStrategy.AUTOMATIC,
            auto_rotate=True,
        )
        old_secret = Secret(
            metadata=SecretMetadata(
                id="old-1",
                name="old-secret",
                type=SecretType.API_KEY,
                created_at=now - 7200,
                updated_at=now - 7200,
                rotation_policy="test-policy",
            ),
            value="old-value",
        )
        await store.store(old_secret)
        manager = SecretRotationManager(store)
        manager.register_policy(policy)
        due = await manager.check_secrets_due_for_rotation()
        assert len(due) == 1
        assert due[0][0] == "old-1"

    def test_get_rotation_history(self) -> None:
        """Verify rotation history retrieval."""
        manager = SecretRotationManager(InMemorySecretStore())
        # Initially empty
        assert manager.get_rotation_history() == []


# ===========================================================================
# Secret Injection Tests
# ===========================================================================


class TestSecretInjection:
    """Tests for Kubernetes secret injection."""

    def test_create_env_var_injection(self) -> None:
        """Verify environment variable injection config creation."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        ref = SecretReference(name="my-secret", key="password")
        config = injector.create_env_var_injection(ref, "DB_PASSWORD")
        assert config["name"] == "DB_PASSWORD"
        assert config["valueFrom"]["secretKeyRef"]["name"] == "my-secret"
        assert config["valueFrom"]["secretKeyRef"]["key"] == "password"

    def test_create_volume_injection(self) -> None:
        """Verify volume injection config creation."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        ref = SecretReference(name="my-secret")
        volume, mount = injector.create_volume_injection(
            ref, "secret-vol", "/etc/secrets"
        )
        assert volume["name"] == "secret-vol"
        assert volume["secret"]["secretName"] == "my-secret"
        assert mount["mountPath"] == "/etc/secrets"
        assert mount["readOnly"] is True

    def test_create_csi_volume(self) -> None:
        """Verify CSI volume injection config creation."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        ref = SecretReference(name="my-provider")
        volume, mount = injector.create_csi_volume(
            ref, "csi-vol", "/etc/secrets"
        )
        assert volume["csi"]["driver"] == "secrets-store.csi.k8s.io"
        assert volume["csi"]["readOnly"] is True

    def test_create_external_secrets_config(self) -> None:
        """Verify ExternalSecrets operator config creation."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        ref = SecretReference(name="my-secret", key="api-key")
        config = injector.create_external_secrets_config(ref)
        assert config["apiVersion"] == "external-secrets.io/v1beta1"
        assert config["kind"] == "ExternalSecret"
        assert config["spec"]["refreshInterval"] == "1h"

    def test_inject_secret(self) -> None:
        """Verify secret injection."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        config = InjectionConfig(
            method=InjectionMethod.ENV_VAR,
            secret_ref=SecretReference(name="my-secret"),
            target_env="MY_SECRET",
        )
        injected = injector.inject_secret(config, "secret-value-123")
        assert injected.name == "my-secret"
        assert injected.value == "secret-value-123"
        assert injected.method == InjectionMethod.ENV_VAR
        assert injected.checksum is not None

    def test_inject_secret_computes_checksum(self) -> None:
        """Verify injected secret checksum is computed correctly."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        config = InjectionConfig(
            method=InjectionMethod.ENV_VAR,
            secret_ref=SecretReference(name="my-secret"),
        )
        value = "test-secret-value"
        injected = injector.inject_secret(config, value)
        expected_checksum = hashlib.sha256(value.encode()).hexdigest()
        assert injected.checksum == expected_checksum

    def test_create_pod_spec_with_env_secrets(self) -> None:
        """Verify pod spec creation with env var secrets."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        base_spec = {
            "apiVersion": "v1",
            "kind": "Pod",
            "spec": {
                "containers": [{"name": "app", "image": "app:latest"}]
            },
        }
        configs = [
            InjectionConfig(
                method=InjectionMethod.ENV_VAR,
                secret_ref=SecretReference(name="db-secret", key="password"),
                target_env="DB_PASSWORD",
            )
        ]
        secret_values = {"db-secret": "db-password-123"}
        spec = injector.create_pod_spec_with_secrets(base_spec, configs, secret_values)
        container = spec["spec"]["containers"][0]
        assert "env" in container
        env_var = container["env"][0]
        assert env_var["name"] == "DB_PASSWORD"
        assert env_var["valueFrom"]["secretKeyRef"]["name"] == "db-secret"

    def test_create_pod_spec_with_volume_secrets(self) -> None:
        """Verify pod spec creation with volume secrets."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        base_spec = {
            "apiVersion": "v1",
            "kind": "Pod",
            "spec": {
                "containers": [{"name": "app", "image": "app:latest"}]
            },
        }
        configs = [
            InjectionConfig(
                method=InjectionMethod.VOLUME,
                secret_ref=SecretReference(name="tls-secret"),
                target_path="/etc/tls",
            )
        ]
        secret_values = {"tls-secret": "tls-cert-data"}
        spec = injector.create_pod_spec_with_secrets(base_spec, configs, secret_values)
        assert "volumes" in spec["spec"]
        volume = spec["spec"]["volumes"][0]
        assert volume["secret"]["secretName"] == "tls-secret"

    def test_create_pod_spec_without_containers_raises(self) -> None:
        """Verify pod spec without containers raises an error."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        base_spec = {
            "apiVersion": "v1",
            "kind": "Pod",
            "spec": {},
        }
        configs = [
            InjectionConfig(
                method=InjectionMethod.ENV_VAR,
                secret_ref=SecretReference(name="secret"),
            )
        ]
        with pytest.raises(InjectionValidationError, match="at least one container"):
            injector.create_pod_spec_with_secrets(base_spec, configs, {"secret": "value"})

    def test_create_pod_spec_missing_secret_value_raises(self) -> None:
        """Verify missing secret value raises an error."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        base_spec = {
            "apiVersion": "v1",
            "kind": "Pod",
            "spec": {
                "containers": [{"name": "app", "image": "app:latest"}]
            },
        }
        configs = [
            InjectionConfig(
                method=InjectionMethod.ENV_VAR,
                secret_ref=SecretReference(name="missing-secret"),
            )
        ]
        with pytest.raises(InjectionSecretNotFoundError):
            injector.create_pod_spec_with_secrets(base_spec, configs, {})

    def test_create_secret_resource(self) -> None:
        """Verify Kubernetes Secret resource creation."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        secret = injector.create_secret_resource(
            name="my-secret",
            data={"username": "admin", "password": "secret123"},
        )
        assert secret["apiVersion"] == "v1"
        assert secret["kind"] == "Secret"
        assert secret["metadata"]["name"] == "my-secret"
        assert secret["metadata"]["namespace"] == "test-ns"
        # Data should be base64 encoded
        import base64
        assert base64.b64decode(secret["data"]["username"]) == b"admin"

    def test_rotate_injected_secret(self) -> None:
        """Verify rotating an injected secret."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        config = InjectionConfig(
            method=InjectionMethod.ENV_VAR,
            secret_ref=SecretReference(name="my-secret"),
        )
        injector.inject_secret(config, "old-value")
        rotated = injector.rotate_injected_secret("my-secret", "new-value")
        assert rotated.value == "new-value"
        assert rotated.checksum != injector.get_injected_secret("my-secret").checksum

    def test_rotate_nonexistent_injected_secret_raises(self) -> None:
        """Verify rotating non-existent injected secret raises an error."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        with pytest.raises(InjectionSecretNotFoundError):
            injector.rotate_injected_secret("nonexistent", "new-value")

    def test_verify_secret_integrity(self) -> None:
        """Verify injected secret integrity check."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        config = InjectionConfig(
            method=InjectionMethod.ENV_VAR,
            secret_ref=SecretReference(name="my-secret"),
        )
        injector.inject_secret(config, "secret-value")
        assert injector.verify_secret_integrity("my-secret") is True

    def test_verify_secret_integrity_tampered(self) -> None:
        """Verify integrity check fails for tampered secret."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        config = InjectionConfig(
            method=InjectionMethod.ENV_VAR,
            secret_ref=SecretReference(name="my-secret"),
        )
        injected = injector.inject_secret(config, "secret-value")
        # Tamper with the value
        object.__setattr__(injected, "value", "tampered-value")
        assert injector.verify_secret_integrity("my-secret") is False

    def test_list_injected_secrets(self) -> None:
        """Verify listing all injected secrets."""
        injector = KubernetesSecretInjector(namespace="test-ns")
        config = InjectionConfig(
            method=InjectionMethod.ENV_VAR,
            secret_ref=SecretReference(name="secret-1"),
        )
        injector.inject_secret(config, "value-1")
        config2 = InjectionConfig(
            method=InjectionMethod.ENV_VAR,
            secret_ref=SecretReference(name="secret-2"),
        )
        injector.inject_secret(config2, "value-2")
        secrets = injector.list_injected_secrets()
        assert len(secrets) == 2


# ===========================================================================
# Secret Injection Sidecar Tests
# ===========================================================================


class TestSecretInjectionSidecar:
    """Tests for secret injection sidecar container."""

    def test_create_sidecar_container(self) -> None:
        """Verify sidecar container creation."""
        sidecar = SecretInjectionSidecar()
        refs = [
            SecretReference(name="secret-1"),
            SecretReference(name="secret-2"),
        ]
        container = sidecar.create_sidecar_container(refs)
        assert container["name"] == "secret-injector"
        assert container["image"] == "grc-security/secret-injector:latest"
        assert len(container["env"]) == 2
        assert container["securityContext"]["readOnlyRootFilesystem"] is True
        assert container["securityContext"]["runAsNonRoot"] is True

    def test_create_shared_volume(self) -> None:
        """Verify shared volume creation."""
        sidecar = SecretInjectionSidecar()
        volume = sidecar.create_shared_volume()
        assert volume["name"] == "shared-secrets"
        assert volume["emptyDir"]["medium"] == "Memory"
        assert volume["emptyDir"]["sizeLimit"] == "10Mi"


# ===========================================================================
# Secrets Management Edge Cases
# ===========================================================================


class TestSecretsManagementEdgeCases:
    """Tests for secrets management edge cases."""

    def test_secret_expiration_check(self) -> None:
        """Verify secret expiration detection."""
        now = time.time()
        expired = Secret(
            metadata=SecretMetadata(
                id="expired",
                name="expired",
                type=SecretType.API_KEY,
                created_at=now - 86400,
                updated_at=now - 86400,
                expires_at=now - 1,
            ),
            value="value",
        )
        assert expired.is_expired() is True
        valid = Secret(
            metadata=SecretMetadata(
                id="valid",
                name="valid",
                type=SecretType.API_KEY,
                created_at=now,
                updated_at=now,
                expires_at=now + 86400,
            ),
            value="value",
        )
        assert valid.is_expired() is False

    def test_secret_should_rotate(self) -> None:
        """Verify secret rotation due detection."""
        now = time.time()
        old_secret = Secret(
            metadata=SecretMetadata(
                id="old",
                name="old",
                type=SecretType.API_KEY,
                created_at=now - 86400 * 30,
                updated_at=now - 86400 * 30,
            ),
            value="value",
        )
        assert old_secret.should_rotate(86400 * 7) is True
        new_secret = Secret(
            metadata=SecretMetadata(
                id="new",
                name="new",
                type=SecretType.API_KEY,
                created_at=now,
                updated_at=now,
            ),
            value="value",
        )
        assert new_secret.should_rotate(86400 * 7) is False

    def test_secret_without_expiration_never_expires(self) -> None:
        """Verify secrets without expiration never expire."""
        secret = Secret(
            metadata=SecretMetadata(
                id="no-expire",
                name="no-expire",
                type=SecretType.API_KEY,
                created_at=0,
                updated_at=0,
            ),
            value="value",
        )
        assert secret.is_expired() is False

    def test_secret_type_enum_values(self) -> None:
        """Verify all secret type enum values."""
        expected = {
            "api_key", "database", "certificate", "token", "password",
            "encryption_key", "ssh_key", "oauth_credential", "custom",
        }
        actual = {t.value for t in SecretType}
        assert actual == expected

    def test_secret_status_enum_values(self) -> None:
        """Verify all secret status enum values."""
        expected = {"active", "rotating", "deprecated", "revoked", "expired"}
        actual = {s.value for s in SecretStatus}
        assert actual == expected

    def test_rotation_strategy_enum_values(self) -> None:
        """Verify all rotation strategy enum values."""
        expected = {"automatic", "manual", "scheduled", "on_demand", "event_driven"}
        actual = {s.value for s in RotationStrategy}
        assert actual == expected

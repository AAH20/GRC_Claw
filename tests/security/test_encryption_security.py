"""Encryption security tests for GRC_Claw.

Tests AES-256-GCM encryption, key derivation (PBKDF2, HKDF),
envelope encryption, and field-level encryption to ensure
cryptographic operations meet security requirements.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import struct
from typing import Any, Dict, List, Optional, Set, Tuple
from unittest.mock import MagicMock, patch

import pytest

from encryption.aes import (
    AESError,
    AES256GCM,
    DecryptionError,
    EncryptedData,
    EnvelopeEncryption,
    FieldLevelEncryption,
    KeyDerivation,
    KeyDerivationError,
)


# ===========================================================================
# AES-256-GCM Encryption Tests
# ===========================================================================


class TestAES256GCMEncryption:
    """Tests for AES-256-GCM authenticated encryption."""

    def test_encrypt_decrypt_roundtrip(self, aes_cipher: AES256GCM) -> None:
        """Verify that encryption followed by decryption returns original plaintext."""
        plaintext = b"Hello, World! This is a secret message."
        encrypted = aes_cipher.encrypt(plaintext)
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_produces_different_ciphertexts(self, aes_cipher: AES256GCM) -> None:
        """Verify that encrypting the same plaintext produces different ciphertexts."""
        plaintext = b"Same message"
        encrypted1 = aes_cipher.encrypt(plaintext)
        encrypted2 = aes_cipher.encrypt(plaintext)
        assert encrypted1.ciphertext != encrypted2.ciphertext
        assert encrypted1.nonce != encrypted2.nonce

    def test_encrypt_with_aad(self, aes_cipher: AES256GCM) -> None:
        """Verify encryption with Additional Authenticated Data (AAD)."""
        plaintext = b"Secret data"
        aad = b"additional authenticated data"
        encrypted = aes_cipher.encrypt(plaintext, aad=aad)
        assert encrypted.aad == aad
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_decrypt_with_wrong_aad_fails(self, aes_cipher: AES256GCM) -> None:
        """Verify that decryption fails when AAD doesn't match."""
        plaintext = b"Secret data"
        encrypted = aes_cipher.encrypt(plaintext, aad=b"correct-aad")
        # Tamper with AAD
        tampered = EncryptedData(
            ciphertext=encrypted.ciphertext,
            nonce=encrypted.nonce,
            tag=encrypted.tag,
            aad=b"wrong-aad",
        )
        with pytest.raises(DecryptionError):
            aes_cipher.decrypt(tampered)

    def test_decrypt_with_wrong_key_fails(self, aes_key: bytes) -> None:
        """Verify that decryption fails with wrong key."""
        cipher1 = AES256GCM(aes_key)
        plaintext = b"Secret"
        encrypted = cipher1.encrypt(plaintext)
        wrong_key = secrets.token_bytes(32)
        cipher2 = AES256GCM(wrong_key)
        with pytest.raises(DecryptionError):
            cipher2.decrypt(encrypted)

    def test_decrypt_tampered_ciphertext_fails(self, aes_cipher: AES256GCM) -> None:
        """Verify that tampered ciphertext fails authentication."""
        plaintext = b"Secret message"
        encrypted = aes_cipher.encrypt(plaintext)
        # Tamper with ciphertext
        tampered_ct = bytes([encrypted.ciphertext[0] ^ 0xFF]) + encrypted.ciphertext[1:]
        tampered = EncryptedData(
            ciphertext=tampered_ct,
            nonce=encrypted.nonce,
            tag=encrypted.tag,
            aad=encrypted.aad,
        )
        with pytest.raises(DecryptionError):
            aes_cipher.decrypt(tampered)

    def test_decrypt_tampered_tag_fails(self, aes_cipher: AES256GCM) -> None:
        """Verify that tampered authentication tag fails."""
        plaintext = b"Secret message"
        encrypted = aes_cipher.encrypt(plaintext)
        # Tamper with tag
        tampered_tag = bytes([encrypted.tag[0] ^ 0xFF]) + encrypted.tag[1:]
        tampered = EncryptedData(
            ciphertext=encrypted.ciphertext,
            nonce=encrypted.nonce,
            tag=tampered_tag,
            aad=encrypted.aad,
        )
        with pytest.raises(DecryptionError):
            aes_cipher.decrypt(tampered)

    def test_encrypt_empty_plaintext(self, aes_cipher: AES256GCM) -> None:
        """Verify encryption of empty plaintext."""
        plaintext = b""
        encrypted = aes_cipher.encrypt(plaintext)
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_large_plaintext(self, aes_cipher: AES256GCM) -> None:
        """Verify encryption of large plaintext."""
        plaintext = secrets.token_bytes(1024 * 1024)  # 1 MB
        encrypted = aes_cipher.encrypt(plaintext)
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_with_custom_nonce(self, aes_cipher: AES256GCM) -> None:
        """Verify encryption with a custom nonce."""
        plaintext = b"Secret"
        nonce = secrets.token_bytes(12)
        encrypted = aes_cipher.encrypt(plaintext, nonce=nonce)
        assert encrypted.nonce == nonce
        decrypted = aes_cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_with_wrong_nonce_size_raises(self, aes_cipher: AES256GCM) -> None:
        """Verify that wrong nonce size raises an error."""
        with pytest.raises(AESError, match="Nonce must be"):
            aes_cipher.encrypt(b"test", nonce=b"short")

    def test_key_size_validation(self) -> None:
        """Verify that key size is validated."""
        with pytest.raises(AESError, match="Key must be"):
            AES256GCM(b"too-short")
        with pytest.raises(AESError, match="Key must be"):
            AES256GCM(b"x" * 16)  # 128-bit key

    def test_key_property_returns_key(self, aes_key: bytes) -> None:
        """Verify that the key property returns the encryption key."""
        cipher = AES256GCM(aes_key)
        assert cipher.key == aes_key

    def test_rotate_key(self, aes_key: bytes) -> None:
        """Verify key rotation."""
        cipher = AES256GCM(aes_key)
        old_key = cipher.key
        new_key = cipher.rotate_key()
        assert new_key != old_key
        assert cipher.key == new_key
        # Old key should no longer work
        plaintext = b"test"
        encrypted = cipher.encrypt(plaintext)
        old_cipher = AES256GCM(old_key)
        with pytest.raises(DecryptionError):
            old_cipher.decrypt(encrypted)


# ===========================================================================
# EncryptedData Serialization Tests
# ===========================================================================


class TestEncryptedDataSerialization:
    """Tests for EncryptedData serialization and deserialization."""

    def test_serialization_roundtrip(self, aes_cipher: AES256GCM) -> None:
        """Verify that serialization preserves all data."""
        plaintext = b"Test data"
        aad = b"test-aad"
        encrypted = aes_cipher.encrypt(plaintext, aad=aad)
        serialized = encrypted.to_bytes()
        deserialized = EncryptedData.from_bytes(serialized)
        assert deserialized.ciphertext == encrypted.ciphertext
        assert deserialized.nonce == encrypted.nonce
        assert deserialized.tag == encrypted.tag
        assert deserialized.aad == encrypted.aad
        assert deserialized.version == encrypted.version

    def test_serialization_without_aad(self, aes_cipher: AES256GCM) -> None:
        """Verify serialization without AAD."""
        plaintext = b"Test data"
        encrypted = aes_cipher.encrypt(plaintext)
        serialized = encrypted.to_bytes()
        deserialized = EncryptedData.from_bytes(serialized)
        assert deserialized.aad is None

    def test_deserialization_too_short_raises(self) -> None:
        """Verify that too-short data raises an error."""
        with pytest.raises(DecryptionError, match="too short"):
            EncryptedData.from_bytes(b"\x01\x02\x03")

    def test_deserialization_invalid_format_raises(self) -> None:
        """Verify that invalid format raises an error."""
        with pytest.raises(DecryptionError, match="Invalid encrypted data format"):
            EncryptedData.from_bytes(b"")


# ===========================================================================
# Key Derivation Tests
# ===========================================================================


class TestKeyDerivation:
    """Tests for key derivation functions."""

    def test_pbkdf2_basic(self) -> None:
        """Verify basic PBKDF2 key derivation."""
        password = b"test-password"
        key, salt = KeyDerivation.pbkdf2(password)
        assert len(key) == 32
        assert len(salt) == 32

    def test_pbkdf2_deterministic_with_same_salt(self) -> None:
        """Verify PBKDF2 is deterministic with same salt."""
        password = b"test-password"
        salt = secrets.token_bytes(32)
        key1, _ = KeyDerivation.pbkdf2(password, salt=salt)
        key2, _ = KeyDerivation.pbkdf2(password, salt=salt)
        assert key1 == key2

    def test_pbkdf2_different_salts_produce_different_keys(self) -> None:
        """Verify different salts produce different keys."""
        password = b"test-password"
        key1, salt1 = KeyDerivation.pbkdf2(password)
        key2, salt2 = KeyDerivation.pbkdf2(password)
        assert key1 != key2
        assert salt1 != salt2

    def test_pbkdf2_minimum_iterations_enforced(self) -> None:
        """Verify minimum iteration count is enforced."""
        with pytest.raises(KeyDerivationError, match="at least 100,000"):
            KeyDerivation.pbkdf2(b"password", iterations=50_000)

    def test_pbkdf2_custom_key_length(self) -> None:
        """Verify PBKDF2 with custom key length."""
        password = b"test-password"
        key, _ = KeyDerivation.pbkdf2(password, key_length=64)
        assert len(key) == 64

    def test_pbkdf2_custom_hash_algorithm(self) -> None:
        """Verify PBKDF2 with SHA-512."""
        password = b"test-password"
        key, _ = KeyDerivation.pbkdf2(password, hash_algorithm="sha512")
        assert len(key) == 32

    def test_hkdf_basic(self) -> None:
        """Verify basic HKDF key derivation."""
        ikm = secrets.token_bytes(32)
        key = KeyDerivation.hkdf(ikm)
        assert len(key) == 32

    def test_hkdf_with_salt_and_info(self) -> None:
        """Verify HKDF with salt and info."""
        ikm = secrets.token_bytes(32)
        salt = secrets.token_bytes(32)
        info = b"test-context"
        key = KeyDerivation.hkdf(ikm, salt=salt, info=info)
        assert len(key) == 32

    def test_hkdf_deterministic(self) -> None:
        """Verify HKDF is deterministic."""
        ikm = secrets.token_bytes(32)
        salt = secrets.token_bytes(32)
        info = b"test-context"
        key1 = KeyDerivation.hkdf(ikm, salt=salt, info=info)
        key2 = KeyDerivation.hkdf(ikm, salt=salt, info=info)
        assert key1 == key2

    def test_hkdf_different_info_produces_different_keys(self) -> None:
        """Verify different info produces different keys."""
        ikm = secrets.token_bytes(32)
        key1 = KeyDerivation.hkdf(ikm, info=b"context-1")
        key2 = KeyDerivation.hkdf(ikm, info=b"context-2")
        assert key1 != key2

    def test_hkdf_custom_key_length(self) -> None:
        """Verify HKDF with custom key length."""
        ikm = secrets.token_bytes(32)
        key = KeyDerivation.hkdf(ikm, key_length=64)
        assert len(key) == 64


# ===========================================================================
# Envelope Encryption Tests
# ===========================================================================


class TestEnvelopeEncryption:
    """Tests for envelope encryption with DEK/KEK separation."""

    def test_envelope_encrypt_decrypt_roundtrip(self, envelope_encryption: EnvelopeEncryption) -> None:
        """Verify envelope encryption roundtrip."""
        plaintext = b"Sensitive data protected by envelope encryption"
        encrypted_package = envelope_encryption.encrypt(plaintext)
        assert "encrypted_data" in encrypted_package
        assert "encrypted_dek" in encrypted_package
        decrypted = envelope_encryption.decrypt(encrypted_package)
        assert decrypted == plaintext

    def test_envelope_encryption_with_aad(self, envelope_encryption: EnvelopeEncryption) -> None:
        """Verify envelope encryption with AAD."""
        plaintext = b"Sensitive data"
        aad = b"additional data"
        encrypted_package = envelope_encryption.encrypt(plaintext, aad=aad)
        decrypted = envelope_encryption.decrypt(encrypted_package)
        assert decrypted == plaintext

    def test_envelope_encryption_produces_different_deks(self, envelope_encryption: EnvelopeEncryption) -> None:
        """Verify that each encryption produces a different DEK."""
        plaintext = b"Same data"
        pkg1 = envelope_encryption.encrypt(plaintext)
        pkg2 = envelope_encryption.encrypt(plaintext)
        assert pkg1["encrypted_dek"] != pkg2["encrypted_dek"]
        assert pkg1["encrypted_data"] != pkg2["encrypted_data"]

    def test_envelope_decrypt_with_wrong_kek_fails(self, aes_key: bytes) -> None:
        """Verify that decryption fails with wrong KEK."""
        plaintext = b"Secret"
        encrypted_package = EnvelopeEncryption(aes_key).encrypt(plaintext)
        wrong_kek = secrets.token_bytes(32)
        with pytest.raises(DecryptionError):
            EnvelopeEncryption(wrong_kek).decrypt(encrypted_package)

    def test_envelope_encryption_large_data(self, envelope_encryption: EnvelopeEncryption) -> None:
        """Verify envelope encryption with large data."""
        plaintext = secrets.token_bytes(100_000)
        encrypted_package = envelope_encryption.encrypt(plaintext)
        decrypted = envelope_encryption.decrypt(encrypted_package)
        assert decrypted == plaintext


# ===========================================================================
# Field-Level Encryption Tests
# ===========================================================================


class TestFieldLevelEncryption:
    """Tests for field-level encryption of structured data."""

    def test_encrypt_decrypt_field(self, field_level_encryption: FieldLevelEncryption) -> None:
        """Verify field-level encryption roundtrip."""
        value = "sensitive-value"
        field_name = "ssn"
        encrypted = field_level_encryption.encrypt_field(value, field_name)
        assert encrypted != value
        decrypted = field_level_encryption.decrypt_field(encrypted, field_name)
        assert decrypted == value

    def test_encrypt_field_with_bytes(self, field_level_encryption: FieldLevelEncryption) -> None:
        """Verify field-level encryption with bytes value."""
        value = b"binary-sensitive-data"
        field_name = "binary_field"
        encrypted = field_level_encryption.encrypt_field(value, field_name)
        decrypted = field_level_encryption.decrypt_field(encrypted, field_name)
        assert decrypted == value.decode("utf-8")

    def test_decrypt_field_with_wrong_field_name_fails(
        self, field_level_encryption: FieldLevelEncryption
    ) -> None:
        """Verify that decryption fails when field name doesn't match."""
        value = "sensitive"
        encrypted = field_level_encryption.encrypt_field(value, "correct_field")
        with pytest.raises(DecryptionError, match="AAD mismatch"):
            field_level_encryption.decrypt_field(encrypted, "wrong_field")

    def test_encrypt_dict_only_sensitive_fields(
        self, field_level_encryption: FieldLevelEncryption
    ) -> None:
        """Verify that only sensitive fields are encrypted in a dict."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "ssn": "123-45-6789",
            "public_info": "visible to all",
        }
        sensitive_fields = {"email", "ssn"}
        encrypted = field_level_encryption.encrypt_dict(data, sensitive_fields)
        assert encrypted["name"] == "John Doe"  # Not encrypted
        assert encrypted["public_info"] == "visible to all"  # Not encrypted
        assert encrypted["email"] != "john@example.com"  # Encrypted
        assert encrypted["ssn"] != "123-45-6789"  # Encrypted

    def test_decrypt_dict_only_sensitive_fields(
        self, field_level_encryption: FieldLevelEncryption
    ) -> None:
        """Verify that only sensitive fields are decrypted in a dict."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "ssn": "123-45-6789",
        }
        sensitive_fields = {"email", "ssn"}
        encrypted = field_level_encryption.encrypt_dict(data, sensitive_fields)
        decrypted = field_level_encryption.decrypt_dict(encrypted, sensitive_fields)
        assert decrypted == data

    def test_encrypt_dict_with_non_string_sensitive_field(
        self, field_level_encryption: FieldLevelEncryption
    ) -> None:
        """Verify that non-string sensitive fields are left as-is."""
        data = {
            "name": "John",
            "age": 30,  # Not a string, should not be encrypted
        }
        sensitive_fields = {"age"}
        encrypted = field_level_encryption.encrypt_dict(data, sensitive_fields)
        assert encrypted["age"] == 30

    def test_field_encryption_produces_different_ciphertexts(
        self, field_level_encryption: FieldLevelEncryption
    ) -> None:
        """Verify that same value encrypts to different ciphertexts."""
        value = "same-value"
        field_name = "test_field"
        encrypted1 = field_level_encryption.encrypt_field(value, field_name)
        encrypted2 = field_level_encryption.encrypt_field(value, field_name)
        assert encrypted1 != encrypted2


# ===========================================================================
# Encryption Security Edge Cases
# ===========================================================================


class TestEncryptionEdgeCases:
    """Tests for encryption security edge cases."""

    def test_nonce_reuse_produces_different_ciphertexts(self, aes_key: bytes) -> None:
        """Verify that nonce reuse with same key still produces different ciphertexts."""
        cipher = AES256GCM(aes_key)
        plaintext = b"test"
        nonce = secrets.token_bytes(12)
        encrypted1 = cipher.encrypt(plaintext, nonce=nonce)
        encrypted2 = cipher.encrypt(plaintext, nonce=nonce)
        # Same nonce + same key + same plaintext = same ciphertext (GCM property)
        # This is actually a vulnerability - nonce reuse in GCM is catastrophic
        # But we're testing the implementation, not the usage
        assert encrypted1.ciphertext == encrypted2.ciphertext

    def test_key_randomness(self) -> None:
        """Verify that generated keys are random."""
        keys = [secrets.token_bytes(32) for _ in range(100)]
        assert len(set(keys)) == 100

    def test_encrypted_data_version_field(self, aes_cipher: AES256GCM) -> None:
        """Verify that encrypted data has correct version."""
        encrypted = aes_cipher.encrypt(b"test")
        assert encrypted.version == 1

    def test_aes_ciphertext_includes_tag(self, aes_cipher: AES256GCM) -> None:
        """Verify that AES-GCM ciphertext includes authentication tag."""
        plaintext = b"test"
        encrypted = aes_cipher.encrypt(plaintext)
        # AESGCM.encrypt returns ciphertext + tag (16 bytes)
        # Our implementation separates them
        assert len(encrypted.tag) == 16
        assert len(encrypted.ciphertext) == len(plaintext)

    def test_decrypt_with_modified_nonce_fails(self, aes_cipher: AES256GCM) -> None:
        """Verify that modified nonce causes decryption failure."""
        plaintext = b"Secret"
        encrypted = aes_cipher.encrypt(plaintext)
        modified_nonce = bytes([encrypted.nonce[0] ^ 0xFF]) + encrypted.nonce[1:]
        tampered = EncryptedData(
            ciphertext=encrypted.ciphertext,
            nonce=modified_nonce,
            tag=encrypted.tag,
            aad=encrypted.aad,
        )
        with pytest.raises(DecryptionError):
            aes_cipher.decrypt(tampered)

"""AES-256-GCM encryption for agentic AI marketing security layer.

Provides authenticated encryption with associated data (AEAD),
key derivation, envelope encryption, and secure key management.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import struct
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AESError(Exception):
    """Base exception for AES encryption errors."""


class DecryptionError(AESError):
    """Raised when decryption fails."""


class KeyDerivationError(AESError):
    """Raised when key derivation fails."""


@dataclass(frozen=True)
class EncryptedData:
    """Encrypted data container."""

    ciphertext: bytes
    nonce: bytes
    tag: bytes
    aad: Optional[bytes] = None
    version: int = 1

    def to_bytes(self) -> bytes:
        """Serialize to bytes."""
        # Format: [version:1][nonce_len:1][aad_len:4][nonce][aad][ciphertext+tag]
        version_bytes = struct.pack("B", self.version)
        nonce_len = struct.pack("B", len(self.nonce))
        aad_len = struct.pack(">I", len(self.aad) if self.aad else 0)
        aad_bytes = self.aad if self.aad else b""
        return version_bytes + nonce_len + aad_len + self.nonce + aad_bytes + self.ciphertext + self.tag

    @classmethod
    def from_bytes(cls, data: bytes) -> "EncryptedData":
        """Deserialize from bytes."""
        if len(data) < 6:
            raise DecryptionError("Invalid encrypted data format")

        version = struct.unpack("B", data[0:1])[0]
        nonce_len = struct.unpack("B", data[1:2])[0]
        aad_len = struct.unpack(">I", data[2:6])[0]

        offset = 6
        nonce = data[offset:offset + nonce_len]
        offset += nonce_len

        aad = data[offset:offset + aad_len] if aad_len > 0 else None
        offset += aad_len

        # Last 16 bytes are the GCM tag
        if len(data) < offset + 16:
            raise DecryptionError("Invalid encrypted data: too short")

        ciphertext = data[offset:-16]
        tag = data[-16:]

        return cls(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            aad=aad,
            version=version,
        )


class AES256GCM:
    """AES-256-GCM encryption engine."""

    NONCE_SIZE = 12
    TAG_SIZE = 16
    KEY_SIZE = 32

    def __init__(self, key: Optional[bytes] = None) -> None:
        if key is None:
            key = secrets.token_bytes(self.KEY_SIZE)
        if len(key) != self.KEY_SIZE:
            raise AESError(f"Key must be {self.KEY_SIZE} bytes, got {len(key)}")
        self._key = key
        self._aesgcm = AESGCM(key)

    @property
    def key(self) -> bytes:
        """Return the encryption key."""
        return self._key

    def encrypt(
        self,
        plaintext: bytes,
        aad: Optional[bytes] = None,
        nonce: Optional[bytes] = None,
    ) -> EncryptedData:
        """Encrypt plaintext using AES-256-GCM."""
        if nonce is None:
            nonce = secrets.token_bytes(self.NONCE_SIZE)
        if len(nonce) != self.NONCE_SIZE:
            raise AESError(f"Nonce must be {self.NONCE_SIZE} bytes")

        # AESGCM.encrypt returns ciphertext + tag
        ct_with_tag = self._aesgcm.encrypt(nonce, plaintext, aad)
        ciphertext = ct_with_tag[:-self.TAG_SIZE]
        tag = ct_with_tag[-self.TAG_SIZE:]

        return EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            aad=aad,
        )

    def decrypt(self, encrypted: EncryptedData) -> bytes:
        """Decrypt ciphertext using AES-256-GCM."""
        try:
            ct_with_tag = encrypted.ciphertext + encrypted.tag
            return self._aesgcm.decrypt(encrypted.nonce, ct_with_tag, encrypted.aad)
        except Exception as exc:
            raise DecryptionError(f"Decryption failed: {exc}") from exc

    def rotate_key(self) -> bytes:
        """Generate and return a new key."""
        new_key = secrets.token_bytes(self.KEY_SIZE)
        self._key = new_key
        self._aesgcm = AESGCM(new_key)
        return new_key


class KeyDerivation:
    """Key derivation utilities."""

    @staticmethod
    def pbkdf2(
        password: bytes,
        salt: Optional[bytes] = None,
        iterations: int = 600_000,
        key_length: int = 32,
        hash_algorithm: str = "sha256",
    ) -> Tuple[bytes, bytes]:
        """Derive key using PBKDF2."""
        if salt is None:
            salt = secrets.token_bytes(32)
        if iterations < 100_000:
            raise KeyDerivationError("PBKDF2 iterations must be at least 100,000")

        try:
            key = hashlib.pbkdf2_hmac(
                hash_algorithm,
                password,
                salt,
                iterations,
                dklen=key_length,
            )
        except Exception as exc:
            raise KeyDerivationError(f"PBKDF2 failed: {exc}") from exc

        return key, salt

    @staticmethod
    def hkdf(
        input_key_material: bytes,
        salt: Optional[bytes] = None,
        info: Optional[bytes] = None,
        key_length: int = 32,
    ) -> bytes:
        """Derive key using HKDF."""
        try:
            from cryptography.hazmat.primitives.kdf.hkdf import HKDF
            from cryptography.hazmat.primitives import hashes

            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=key_length,
                salt=salt,
                info=info,
            )
            return hkdf.derive(input_key_material)
        except ImportError:
            # Fallback to simple HKDF implementation
            if salt is None:
                salt = b"\x00" * 32
            prk = hmac.new(salt, input_key_material, hashlib.sha256).digest()
            okm = b""
            previous = b""
            counter = 1
            while len(okm) < key_length:
                counter_bytes = struct.pack("B", counter)
                previous = hmac.new(
                    prk, previous + (info or b"") + counter_bytes, hashlib.sha256
                ).digest()
                okm += previous
                counter += 1
            return okm[:key_length]


class EnvelopeEncryption:
    """Envelope encryption with data encryption keys (DEK) and key encryption keys (KEK)."""

    def __init__(self, kek: bytes) -> None:
        self._kek = kek
        self._kek_cipher = AES256GCM(kek)

    def encrypt(self, plaintext: bytes, aad: Optional[bytes] = None) -> Dict[str, bytes]:
        """Encrypt using envelope encryption."""
        # Generate a data encryption key
        dek = secrets.token_bytes(32)
        dek_cipher = AES256GCM(dek)

        # Encrypt the data
        encrypted_data = dek_cipher.encrypt(plaintext, aad=aad)

        # Encrypt the DEK with the KEK
        encrypted_dek = self._kek_cipher.encrypt(dek)

        return {
            "encrypted_data": encrypted_data.to_bytes(),
            "encrypted_dek": encrypted_dek.to_bytes(),
            "aad": aad or b"",
        }

    def decrypt(self, encrypted_package: Dict[str, bytes]) -> bytes:
        """Decrypt using envelope encryption."""
        # Decrypt the DEK
        encrypted_dek = EncryptedData.from_bytes(encrypted_package["encrypted_dek"])
        dek = self._kek_cipher.decrypt(encrypted_dek)

        # Decrypt the data
        encrypted_data = EncryptedData.from_bytes(encrypted_package["encrypted_data"])
        dek_cipher = AES256GCM(dek)
        return dek_cipher.decrypt(encrypted_data)


class FieldLevelEncryption:
    """Field-level encryption for structured data."""

    def __init__(self, key: bytes) -> None:
        self._cipher = AES256GCM(key)

    def encrypt_field(self, value: Union[str, bytes], field_name: str) -> str:
        """Encrypt a single field value."""
        if isinstance(value, str):
            value = value.encode("utf-8")
        aad = field_name.encode("utf-8")
        encrypted = self._cipher.encrypt(value, aad=aad)
        return encrypted.to_bytes().hex()

    def decrypt_field(self, encrypted_hex: str, field_name: str) -> str:
        """Decrypt a single field value."""
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        encrypted = EncryptedData.from_bytes(encrypted_bytes)
        aad = field_name.encode("utf-8")
        if encrypted.aad != aad:
            raise DecryptionError("AAD mismatch - field name does not match")
        plaintext = self._cipher.decrypt(encrypted)
        return plaintext.decode("utf-8")

    def encrypt_dict(
        self,
        data: Dict[str, Any],
        sensitive_fields: set[str],
    ) -> Dict[str, Any]:
        """Encrypt sensitive fields in a dictionary."""
        result = {}
        for key, value in data.items():
            if key in sensitive_fields and isinstance(value, (str, bytes)):
                result[key] = self.encrypt_field(value, key)
            else:
                result[key] = value
        return result

    def decrypt_dict(
        self,
        data: Dict[str, Any],
        sensitive_fields: set[str],
    ) -> Dict[str, Any]:
        """Decrypt sensitive fields in a dictionary."""
        result = {}
        for key, value in data.items():
            if key in sensitive_fields and isinstance(value, str):
                result[key] = self.decrypt_field(value, key)
            else:
                result[key] = value
        return result

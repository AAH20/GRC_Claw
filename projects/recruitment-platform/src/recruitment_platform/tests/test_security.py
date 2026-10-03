"""Tests for security module."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from recruitment_platform.security.auth import (
    create_access_token,
    generate_api_key,
    generate_secure_id,
    get_password_hash,
    sanitize_input,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Test password hashing."""

    def test_hash_and_verify(self) -> None:
        """Test password hashing and verification."""
        password = "test-password-123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrong-password", hashed) is False

    def test_different_hashes(self) -> None:
        """Test that same password produces different hashes."""
        password = "test-password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2


class TestJWT:
    """Test JWT token creation and verification."""

    def test_create_and_verify_token(self) -> None:
        """Test creating and verifying a JWT token."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)
        payload = verify_token(token)
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"

    def test_token_expiration(self) -> None:
        """Test that expired tokens are rejected."""
        from datetime import timedelta

        data = {"sub": "user-123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException):
            verify_token(token)


class TestInputSanitization:
    """Test input sanitization."""

    def test_sanitize_html(self) -> None:
        """Test HTML escaping."""
        assert (
            sanitize_input("<script>alert('xss')</script>")
            == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        )

    def test_sanitize_null_bytes(self) -> None:
        """Test null byte removal."""
        assert sanitize_input("test\x00input") == "testinput"


class TestSecureGeneration:
    """Test secure ID and key generation."""

    def test_generate_secure_id(self) -> None:
        """Test secure ID generation."""
        id1 = generate_secure_id()
        id2 = generate_secure_id()
        assert id1 != id2
        assert len(id1) == 32

    def test_generate_api_key(self) -> None:
        """Test API key generation."""
        key = generate_api_key()
        assert len(key) > 0
        assert isinstance(key, str)

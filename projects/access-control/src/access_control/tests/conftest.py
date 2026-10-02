"""Test fixtures and configuration for the access control test suite."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from access_control.config import Settings
from access_control.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        app_env="development",
        debug=True,
        secret_key="test-secret-key",
        openai_api_key="test-key",
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_access_request() -> dict:
    """Create a sample access request payload."""
    return {
        "principal_id": "user-123",
        "resource": "documents",
        "action": "read",
        "context": {"ip_address": "192.168.1.1", "time": "2024-01-01T12:00:00Z"},
        "roles": ["role-1"],
    }


@pytest.fixture
def sample_role_create() -> dict:
    """Create a sample role creation payload."""
    return {
        "name": "test-role",
        "description": "A test role",
        "permissions": [
            {"resource": "documents", "action": "read", "effect": "allow"},
        ],
    }

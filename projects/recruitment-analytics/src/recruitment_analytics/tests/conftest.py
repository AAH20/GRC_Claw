"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from recruitment_analytics.config.settings import Settings
from recruitment_analytics.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        environment="development",
        debug=True,
        secret_key="test-secret-key-12345",  # noqa: S106
        openai_api_key="test-key",
    )


@pytest.fixture
def test_app(test_settings: Settings):
    """Create test FastAPI app."""
    return create_app(settings=test_settings)


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)

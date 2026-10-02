"""Test configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from content_discovery.config import Settings
from content_discovery.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings.

    Returns:
        Settings: Test application settings.
    """
    return Settings(
        app_name="content-discovery-test",
        environment="testing",
        debug=True,
        redis_url="redis://localhost:6379/1",
        vector_store_url="http://localhost:8080",
        enable_metrics=True,
    )


@pytest.fixture
def test_app(test_settings: Settings):
    """Create test FastAPI application.

    Args:
        test_settings: Test settings.

    Yields:
        FastAPI: Test application.
    """
    app = create_app(settings=test_settings)
    yield app


@pytest.fixture
def test_client(test_app):
    """Create test client.

    Args:
        test_app: Test application.

    Yields:
        TestClient: Test client.
    """
    with TestClient(test_app) as client:
        yield client

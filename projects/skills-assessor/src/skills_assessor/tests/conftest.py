"""Test configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from skills_assessor.config.settings import Settings
from skills_assessor.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings.

    Returns:
        Settings: Test settings instance.
    """
    return Settings(
        app_name="skills-assessor-test",
        environment="development",
        debug=True,
        openai_api_key="test-key",
        llm_model="gpt-4o-mini",
    )


@pytest.fixture
def test_app(test_settings: Settings):
    """Create test FastAPI app.

    Args:
        test_settings: Test settings.

    Returns:
        FastAPI: Test application instance.
    """
    return create_app(test_settings)


@pytest.fixture
def test_client(test_app):
    """Create test client.

    Args:
        test_app: Test application.

    Returns:
        TestClient: Test client instance.
    """
    return TestClient(test_app)

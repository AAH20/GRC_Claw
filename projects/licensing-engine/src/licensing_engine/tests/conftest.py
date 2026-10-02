"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from licensing_engine.config.settings import Settings
from licensing_engine.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Create test settings.

    Returns:
        Settings instance configured for testing.
    """
    return Settings(
        app_env="development",
        debug=True,
        openai_api_key="test-key",
        llm_model="gpt-4o",
        llm_temperature=0.1,
        llm_max_tokens=1024,
        agent_timeout_seconds=30,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """Create a test client.

    Args:
        settings: Test settings.

    Returns:
        TestClient instance.
    """
    app = create_app()
    return TestClient(app)

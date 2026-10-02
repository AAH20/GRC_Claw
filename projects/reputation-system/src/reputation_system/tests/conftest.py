"""Test configuration and fixtures."""

from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient

from reputation_system.config.settings import Settings
from reputation_system.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        APP_ENV="testing",
        DEBUG=True,
        LOG_LEVEL="warning",
        OPENAI_API_KEY="",
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """Create test client."""
    app = create_app(settings=settings)
    return TestClient(app)


@pytest.fixture
async def async_client(settings: Settings) -> AsyncGenerator:
    """Create async test client."""
    from httpx import AsyncClient, ASGITransport

    app = create_app(settings=settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

"""Shared pytest fixtures for the test suite."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient

from onboarding_automator.config.settings import Settings
from onboarding_automator.integrations.store import InMemoryStore
from onboarding_automator.main import create_app
from onboarding_automator.models import EmployeeInfo


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        environment="test",
        debug=True,
        log_level="DEBUG",
        openai_api_key="test-key",
    )


@pytest.fixture
def store() -> InMemoryStore:
    """Create a fresh in-memory store."""
    return InMemoryStore()


@pytest.fixture
def employee_info() -> EmployeeInfo:
    """Create sample employee info for testing."""
    return EmployeeInfo(
        employee_id="EMP-001",
        full_name="Jane Smith",
        email="jane.smith@example.com",
        department="Engineering",
        role="Senior Software Engineer",
        start_date=datetime.utcnow() + timedelta(days=14),
        manager_id="MGR-001",
        location="San Francisco",
        employment_type="full_time",
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    """Create a test client for the FastAPI app."""
    app = create_app()
    app.state.settings = settings
    app.state.store = InMemoryStore()
    return TestClient(app)


@pytest.fixture
async def async_client(settings: Settings) -> AsyncGenerator:
    """Create an async test client."""
    from httpx import ASGITransport, AsyncClient

    app = create_app()
    app.state.settings = settings
    app.state.store = InMemoryStore()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

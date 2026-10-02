"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from content_moderation.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create test client fixture.

    Returns:
        FastAPI test client.
    """
    app = create_app()
    return TestClient(app)

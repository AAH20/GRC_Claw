"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from moderation_queue.main import create_app


@pytest.fixture
def app():
    """Create a test FastAPI application.

    Returns:
        FastAPI: Test application instance.
    """
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client.

    Args:
        app: FastAPI application fixture.

    Returns:
        TestClient: Test client instance.
    """
    return TestClient(app)

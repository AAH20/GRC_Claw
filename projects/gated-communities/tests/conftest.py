"""Pytest configuration and fixtures for integration tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from gated_communities.main import create_app


@pytest.fixture
def app():
    """Create a test FastAPI application."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)
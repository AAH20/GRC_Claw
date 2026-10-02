"""Test configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from compliance_monitor.main import create_app


@pytest.fixture
def app():
    """Create test application.

    Returns:
        FastAPI application instance.
    """
    return create_app()


@pytest.fixture
def client(app):
    """Create test client.

    Args:
        app: FastAPI application.

    Returns:
        TestClient instance.
    """
    return TestClient(app)

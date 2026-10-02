"""Test configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from rights_management.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application.

    Returns:
        A TestClient instance.
    """
    app = create_app()
    with TestClient(app) as client:
        yield client

"""Test configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from escalation_workflow.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the application.

    Returns:
        TestClient: FastAPI test client.
    """
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_escalation_data() -> dict:
    """Sample escalation data for testing.

    Returns:
        dict: Sample escalation creation data.
    """
    return {
        "title": "Test Escalation",
        "description": "This is a test escalation for testing purposes",
        "priority": "high",
        "category": "infrastructure",
        "source": "test",
        "requester": "test_user",
        "tags": ["test", "automation"],
        "metadata": {"test": True},
    }


@pytest.fixture
def sample_resolution_data() -> dict:
    """Sample resolution data for testing.

    Returns:
        dict: Sample resolution creation data.
    """
    return {
        "escalation_id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Test Resolution",
        "description": "This is a test resolution",
        "resolution_type": "manual",
        "steps": ["Step 1", "Step 2"],
        "automated": False,
        "confidence": 0.9,
    }

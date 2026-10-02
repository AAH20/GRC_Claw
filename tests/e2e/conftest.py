"""E2E test configuration and fixtures for GRC_Claw platform.

This module provides shared fixtures, helpers, and configuration for all
end-to-end tests that simulate real user workflows across multiple projects.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient


# ── Application Imports ─────────────────────────────────────────────────────


def _import_campaign_app() -> Any:
    """Import and return the Campaign Optimizer FastAPI app.

    Returns:
        The FastAPI application instance.

    Raises:
        ImportError: If the campaign-optimizer package is not available.
    """
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2] / "projects" / "campaign-optimizer"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from api.main import app

    return app


def _import_lead_scorer_app() -> Any:
    """Import and return the Lead Scorer FastAPI app.

    Returns:
        The FastAPI application instance.

    Raises:
        ImportError: If the lead-scorer package is not available.
    """
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2] / "projects" / "lead-scorer"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from api.main import app

    return app


def _import_journey_app() -> Any:
    """Import and return the Journey Orchestrator FastAPI app.

    Returns:
        The FastAPI application instance.

    Raises:
        ImportError: If the journey-orchestrator package is not available.
    """
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2] / "projects" / "journey-orchestrator"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from api.main import app

    return app


def _import_content_app() -> Any:
    """Import and return the Content Generator FastAPI app.

    Returns:
        The FastAPI application instance.

    Raises:
        ImportError: If the content-generator package is not available.
    """
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2] / "projects" / "content-generator" / "src"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from content_generator.main import app

    return app


def _import_sales_app() -> Any:
    """Import and return the Sales Automator FastAPI app.

    Returns:
        The FastAPI application instance.

    Raises:
        ImportError: If the sales-automator package is not available.
    """
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2] / "projects" / "sales-automator" / "src"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from sales_automator.main import app

    return app


def _import_customer_service_app() -> Any:
    """Import and return the Customer Service FastAPI app.

    Returns:
        The FastAPI application instance.

    Raises:
        ImportError: If the customer-service package is not available.
    """
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2] / "projects" / "customer-service" / "src"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from customer_service.main import app

    return app


def _import_analytics_app() -> Any:
    """Import and return the Analytics FastAPI app.

    Returns:
        The FastAPI application instance.

    Raises:
        ImportError: If the analytics package is not available.
    """
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2] / "projects" / "analytics" / "src"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from analytics.main import app

    return app


def _import_broker_app() -> Any:
    """Import and return the Broker Enablement FastAPI app.

    Returns:
        The FastAPI application instance.

    Raises:
        ImportError: If the broker-enablement package is not available.
    """
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2] / "projects" / "broker-enablement" / "src"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from broker_enablement.main import app

    return app


def _import_orchestrator_app() -> Any:
    """Import and return the Cross-Project Orchestrator FastAPI app.

    Returns:
        The FastAPI application instance.

    Raises:
        ImportError: If the cross-project-orchestrator package is not available.
    """
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2] / "projects" / "cross-project-orchestrator" / "src"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from cross_project_orchestrator.main import app

    return app


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def campaign_client() -> Generator[TestClient, None, None]:
    """Create a test client for the Campaign Optimizer API.

    Yields:
        FastAPI TestClient for the campaign-optimizer service.
    """
    app = _import_campaign_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def lead_scorer_client() -> Generator[TestClient, None, None]:
    """Create a test client for the Lead Scorer API.

    Yields:
        FastAPI TestClient for the lead-scorer service.
    """
    app = _import_lead_scorer_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def journey_client() -> Generator[TestClient, None, None]:
    """Create a test client for the Journey Orchestrator API.

    Yields:
        FastAPI TestClient for the journey-orchestrator service.
    """
    app = _import_journey_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def content_client() -> Generator[TestClient, None, None]:
    """Create a test client for the Content Generator API.

    Yields:
        FastAPI TestClient for the content-generator service.
    """
    app = _import_content_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sales_client() -> Generator[TestClient, None, None]:
    """Create a test client for the Sales Automator API.

    Yields:
        FastAPI TestClient for the sales-automator service.
    """
    app = _import_sales_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def customer_service_client() -> Generator[TestClient, None, None]:
    """Create a test client for the Customer Service API.

    Yields:
        FastAPI TestClient for the customer-service service.
    """
    app = _import_customer_service_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def analytics_client() -> Generator[TestClient, None, None]:
    """Create a test client for the Analytics API.

    Yields:
        FastAPI TestClient for the analytics service.
    """
    app = _import_analytics_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def broker_client() -> Generator[TestClient, None, None]:
    """Create a test client for the Broker Enablement API.

    Yields:
        FastAPI TestClient for the broker-enablement service.
    """
    app = _import_broker_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def orchestrator_client() -> Generator[TestClient, None, None]:
    """Create a test client for the Cross-Project Orchestrator API.

    Yields:
        FastAPI TestClient for the cross-project-orchestrator service.
    """
    app = _import_orchestrator_app()
    with TestClient(app) as client:
        yield client


# ── Sample Data Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def sample_campaign_data() -> dict[str, Any]:
    """Provide sample campaign creation data for E2E tests.

    Returns:
        Dictionary with valid campaign creation payload.
    """
    return {
        "name": f"E2E Test Campaign {uuid.uuid4().hex[:8]}",
        "description": "End-to-end test campaign for workflow validation",
        "goals": ["awareness", "conversion"],
        "total_budget": 50000.0,
        "daily_budget": 1666.67,
        "channels": ["search", "social"],
        "duration_days": 30,
        "target_audience": {
            "demographics": {"age_ranges": ["25-34", "35-44"], "locations": ["US", "CA"]},
        },
        "brand_voice": "professional",
        "key_message": "The future of productivity is here",
        "industry": "technology",
    }


@pytest.fixture
def sample_lead_data() -> dict[str, Any]:
    """Provide sample lead data for E2E tests.

    Returns:
        Dictionary with valid lead creation and scoring payload.
    """
    return {
        "company_name": f"E2E Test Company {uuid.uuid4().hex[:8]}",
        "domain": f"e2e-test-{uuid.uuid4().hex[:8]}.com",
        "industry": "technology",
        "company_size": "50-200",
        "location": "San Francisco, CA",
        "contact_name": "Jane Doe",
        "contact_email": "jane.doe@example.com",
        "contact_phone": "+1-555-0100",
        "notes": "Interested in enterprise plan",
        "metadata": {"source": "website", "campaign": "e2e_test"},
    }


@pytest.fixture
def sample_journey_data() -> dict[str, Any]:
    """Provide sample journey data for E2E tests.

    Returns:
        Dictionary with valid journey creation payload.
    """
    return {
        "name": f"E2E Test Journey {uuid.uuid4().hex[:8]}",
        "description": "End-to-end test journey for workflow validation",
        "target_audience": "enterprise_leads",
        "business_goal": "conversion",
        "channels": ["email", "push"],
        "metadata": {"test_run": True, "workflow": "e2e"},
    }


@pytest.fixture
def sample_content_request() -> dict[str, Any]:
    """Provide sample content generation request for E2E tests.

    Returns:
        Dictionary with valid content generation payload.
    """
    return {
        "query": "AI-powered marketing automation for enterprise",
        "content_type": "article",
        "language": "en",
        "location": "us",
        "platforms": ["twitter", "linkedin"],
    }


@pytest.fixture
def sample_prospect_data() -> dict[str, Any]:
    """Provide sample prospect data for E2E tests.

    Returns:
        Dictionary with valid prospect creation payload.
    """
    return {
        "name": "John Smith",
        "company": f"E2E Prospect Co {uuid.uuid4().hex[:8]}",
        "title": "VP of Marketing",
        "email": "john.smith@example.com",
        "linkedin_url": "https://linkedin.com/in/johnsmith",
        "company_size": 200,
        "industry": "technology",
        "source": "e2e_test",
        "metadata": {"test_run": True},
    }


@pytest.fixture
def sample_ticket_data() -> dict[str, Any]:
    """Provide sample ticket data for E2E tests.

    Returns:
        Dictionary with valid ticket creation payload.
    """
    return {
        "customer_id": f"cust_{uuid.uuid4().hex[:12]}",
        "subject": "E2E Test: Unable to access dashboard",
        "content": "I am unable to access my dashboard after the latest update. Please help.",
        "channel": "email",
        "metadata": {"test_run": True, "priority": "high"},
    }


@pytest.fixture
def sample_partner_data() -> dict[str, Any]:
    """Provide sample partner registration data for E2E tests.

    Returns:
        Dictionary with valid partner registration payload.
    """
    return {
        "business_name": f"E2E Partner LLC {uuid.uuid4().hex[:8]}",
        "contact_name": "Alice Johnson",
        "contact_email": "alice@e2epartner.com",
        "business_type": "reseller",
        "website": "https://e2epartner.com",
        "country": "US",
        "metadata": {"test_run": True, "onboarding": "e2e"},
    }


@pytest.fixture
def sample_project_data() -> dict[str, Any]:
    """Provide sample project data for E2E tests.

    Returns:
        Dictionary with valid project registration payload.
    """
    return {
        "name": f"e2e-test-project-{uuid.uuid4().hex[:8]}",
        "path": f"/tmp/e2e-test-project-{uuid.uuid4().hex[:8]}",
        "type": "python",
        "language": "python",
        "dependencies": [],
        "metadata": {"test_run": True, "workflow": "e2e"},
    }


# ── Helper Functions ────────────────────────────────────────────────────────


def generate_unique_id(prefix: str = "e2e") -> str:
    """Generate a unique identifier for test resources.

    Args:
        prefix: Prefix for the identifier.

    Returns:
        A unique identifier string.
    """
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def assert_health_check(client: TestClient, expected_status: str = "healthy") -> None:
    """Assert that a service health check passes.

    Args:
        client: The test client to use.
        expected_status: Expected health status string.

    Raises:
        AssertionError: If health check fails or returns unexpected status.
    """
    response = client.get("/health")
    assert response.status_code == 200, f"Health check failed: {response.text}"
    data = response.json()
    assert data.get("status") == expected_status, (
        f"Expected status '{expected_status}', got '{data.get('status')}'"
    )


def assert_response_success(response: Any, expected_status: int = 200) -> dict[str, Any]:
    """Assert that an API response is successful and return the JSON body.

    Args:
        response: The HTTP response object.
        expected_status: Expected HTTP status code.

    Returns:
        The JSON response body as a dictionary.

    Raises:
        AssertionError: If the response status code doesn't match.
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    )
    return response.json()


def assert_response_error(response: Any, expected_status: int = 400) -> dict[str, Any]:
    """Assert that an API response is an error and return the JSON body.

    Args:
        response: The HTTP response object.
        expected_status: Expected HTTP error status code.

    Returns:
        The JSON response body as a dictionary.

    Raises:
        AssertionError: If the response status code doesn't match.
    """
    assert response.status_code == expected_status, (
        f"Expected error status {expected_status}, got {response.status_code}: {response.text}"
    )
    return response.json()

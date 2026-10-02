"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.agents.analytics_collector import AnalyticsCollectorAgent
from app.agents.domain_router import DomainRouterAgent
from app.agents.error_handler import ErrorHandlerAgent
from app.agents.result_aggregator import ResultAggregatorAgent
from app.agents.workflow_orchestrator import WorkflowOrchestratorAgent
from app.models.domain import DomainRequest
from app.models.workflow import (
    Workflow,
    WorkflowExecutionRequest,
    WorkflowStep,
)
from main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app.

    Returns:
        TestClient instance.
    """
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_workflow() -> Workflow:
    """Create a sample workflow for testing.

    Returns:
        Sample workflow instance.
    """
    return Workflow(
        name="Test Workflow",
        description="A test workflow",
        steps=[
            WorkflowStep(
                name="Step 1",
                domain="security",
                action="scan",
                order=0,
            ),
            WorkflowStep(
                name="Step 2",
                domain="compliance",
                action="audit",
                order=1,
                depends_on=[],
            ),
        ],
    )


@pytest.fixture
def sample_domain_request() -> DomainRequest:
    """Create a sample domain request for testing.

    Returns:
        Sample domain request instance.
    """
    return DomainRequest(
        domain="security",
        action="threat_detection",
        payload={"target": "network"},
    )


@pytest.fixture
def sample_execution_request(sample_workflow: Workflow) -> WorkflowExecutionRequest:
    """Create a sample execution request for testing.

    Args:
        sample_workflow: Sample workflow fixture.

    Returns:
        Sample execution request.
    """
    return WorkflowExecutionRequest(workflow_id=sample_workflow.id)


@pytest.fixture
def domain_router() -> DomainRouterAgent:
    """Create a DomainRouterAgent instance.

    Returns:
        DomainRouterAgent instance.
    """
    return DomainRouterAgent()


@pytest.fixture
def workflow_orchestrator() -> WorkflowOrchestratorAgent:
    """Create a WorkflowOrchestratorAgent instance.

    Returns:
        WorkflowOrchestratorAgent instance.
    """
    return WorkflowOrchestratorAgent()


@pytest.fixture
def result_aggregator() -> ResultAggregatorAgent:
    """Create a ResultAggregatorAgent instance.

    Returns:
        ResultAggregatorAgent instance.
    """
    return ResultAggregatorAgent()


@pytest.fixture
def error_handler() -> ErrorHandlerAgent:
    """Create an ErrorHandlerAgent instance.

    Returns:
        ErrorHandlerAgent instance.
    """
    return ErrorHandlerAgent()


@pytest.fixture
def analytics_collector() -> AnalyticsCollectorAgent:
    """Create an AnalyticsCollectorAgent instance.

    Returns:
        AnalyticsCollectorAgent instance.
    """
    return AnalyticsCollectorAgent()

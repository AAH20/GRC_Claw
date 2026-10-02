"""Tests for Pydantic models."""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.analytics import AnalyticsEvent, CrossDomainAnalytics, DomainMetrics
from app.models.domain import DomainInfo, DomainRequest, DomainResponse, DomainType
from app.models.workflow import (
    Workflow,
    WorkflowExecutionRequest,
    WorkflowResult,
    WorkflowState,
    WorkflowStep,
    WorkflowStepResult,
)


class TestWorkflowModels:
    """Tests for workflow-related models."""

    def test_workflow_step_creation(self) -> None:
        """Test creating a workflow step."""
        step = WorkflowStep(name="Test Step", domain="security", action="scan")
        assert step.name == "Test Step"
        assert step.domain == "security"
        assert step.order == 0
        assert step.depends_on == []

    def test_workflow_creation(self) -> None:
        """Test creating a workflow."""
        workflow = Workflow(name="Test Workflow", description="Test")
        assert workflow.name == "Test Workflow"
        assert workflow.state == WorkflowState.PENDING
        assert workflow.steps == []

    def test_workflow_state_enum(self) -> None:
        """Test workflow state enumeration."""
        assert WorkflowState.PENDING == "pending"
        assert WorkflowState.RUNNING == "running"
        assert WorkflowState.COMPLETED == "completed"
        assert WorkflowState.FAILED == "failed"
        assert WorkflowState.CANCELLED == "cancelled"

    def test_workflow_step_result(self) -> None:
        """Test creating a workflow step result."""
        result = WorkflowStepResult(step_id="step-1", success=True)
        assert result.step_id == "step-1"
        assert result.success is True
        assert result.error is None

    def test_workflow_result(self) -> None:
        """Test creating a workflow result."""
        result = WorkflowResult(workflow_id="wf-1", success=True)
        assert result.workflow_id == "wf-1"
        assert result.success is True
        assert result.total_duration_ms == 0.0

    def test_workflow_execution_request(self) -> None:
        """Test creating a workflow execution request."""
        request = WorkflowExecutionRequest(workflow_id="wf-1")
        assert request.workflow_id == "wf-1"
        assert request.async_execution is False

    def test_workflow_step_validation_empty_name(self) -> None:
        """Test that empty step name raises validation error."""
        with pytest.raises(ValidationError):
            WorkflowStep(name="", domain="security", action="scan")

    def test_workflow_step_validation_order(self) -> None:
        """Test that negative order raises validation error."""
        with pytest.raises(ValidationError):
            WorkflowStep(name="Test", domain="security", action="scan", order=-1)


class TestDomainModels:
    """Tests for domain-related models."""

    def test_domain_type_enum(self) -> None:
        """Test domain type enumeration."""
        assert DomainType.SECURITY == "security"
        assert DomainType.COMPLIANCE == "compliance"
        assert DomainType.OPERATIONS == "operations"

    def test_domain_info_creation(self) -> None:
        """Test creating domain info."""
        info = DomainInfo(name="security", type=DomainType.SECURITY)
        assert info.name == "security"
        assert info.type == DomainType.SECURITY
        assert info.status == "active"

    def test_domain_request_creation(self) -> None:
        """Test creating a domain request."""
        request = DomainRequest(domain="security", action="scan")
        assert request.domain == "security"
        assert request.action == "scan"
        assert request.priority == 5

    def test_domain_request_priority_validation(self) -> None:
        """Test priority validation."""
        with pytest.raises(ValidationError):
            DomainRequest(domain="security", action="scan", priority=0)
        with pytest.raises(ValidationError):
            DomainRequest(domain="security", action="scan", priority=11)

    def test_domain_response_creation(self) -> None:
        """Test creating a domain response."""
        response = DomainResponse(request_id="req-1", domain="security", success=True)
        assert response.request_id == "req-1"
        assert response.success is True


class TestAnalyticsModels:
    """Tests for analytics-related models."""

    def test_analytics_event_creation(self) -> None:
        """Test creating an analytics event."""
        event = AnalyticsEvent(
            event_type="test_event",
            domain="security",
            agent="test_agent",
        )
        assert event.event_type == "test_event"
        assert event.domain == "security"
        assert event.agent == "test_agent"

    def test_domain_metrics_creation(self) -> None:
        """Test creating domain metrics."""
        metrics = DomainMetrics(domain="security")
        assert metrics.domain == "security"
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0

    def test_cross_domain_analytics_creation(self) -> None:
        """Test creating cross-domain analytics."""
        analytics = CrossDomainAnalytics()
        assert analytics.total_events == 0
        assert analytics.domain_metrics == {}
        assert analytics.agent_metrics == {}

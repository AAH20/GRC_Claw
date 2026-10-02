"""Tests for agent implementations."""

from __future__ import annotations

import pytest

from app.agents.analytics_collector import AnalyticsCollectorAgent
from app.agents.domain_router import DomainRouterAgent
from app.agents.error_handler import ErrorCategory, ErrorHandlerAgent, ErrorSeverity
from app.agents.result_aggregator import ResultAggregatorAgent
from app.agents.workflow_orchestrator import WorkflowOrchestratorAgent
from app.models.analytics import AnalyticsEvent
from app.models.domain import DomainInfo, DomainRequest, DomainType
from app.models.workflow import (
    Workflow,
    WorkflowExecutionRequest,
    WorkflowState,
    WorkflowStep,
    WorkflowStepResult,
)


class TestDomainRouterAgent:
    """Tests for the DomainRouterAgent."""

    def test_initialization(self, domain_router: DomainRouterAgent) -> None:
        """Test agent initialization with default domains."""
        assert len(domain_router.domains) > 0
        assert "security" in domain_router.domains
        assert "compliance" in domain_router.domains

    def test_register_domain(self, domain_router: DomainRouterAgent) -> None:
        """Test registering a new domain."""
        new_domain = DomainInfo(
            name="test_domain",
            type=DomainType.CUSTOM,
            description="Test domain",
        )
        domain_router.register_domain(new_domain)
        assert "test_domain" in domain_router.domains

    def test_unregister_domain(self, domain_router: DomainRouterAgent) -> None:
        """Test unregistering a domain."""
        result = domain_router.unregister_domain("security")
        assert result is True
        assert "security" not in domain_router.domains

    def test_unregister_nonexistent_domain(self, domain_router: DomainRouterAgent) -> None:
        """Test unregistering a domain that doesn't exist."""
        result = domain_router.unregister_domain("nonexistent")
        assert result is False

    def test_route_request_success(
        self,
        domain_router: DomainRouterAgent,
        sample_domain_request: DomainRequest,
    ) -> None:
        """Test successful request routing."""
        response = domain_router.route(sample_domain_request)
        assert response.success is True
        assert response.domain == "security"

    def test_route_request_invalid_domain(self, domain_router: DomainRouterAgent) -> None:
        """Test routing to a non-existent domain."""
        request = DomainRequest(domain="nonexistent", action="test")
        response = domain_router.route(request)
        assert response.success is False
        assert "not found" in response.error

    def test_find_best_domain(self, domain_router: DomainRouterAgent) -> None:
        """Test finding the best domain for capabilities."""
        best = domain_router.find_best_domain("scan", ["threat_detection"])
        assert best is not None

    def test_list_domains(self, domain_router: DomainRouterAgent) -> None:
        """Test listing all domains."""
        domains = domain_router.list_domains()
        assert len(domains) > 0
        assert all(isinstance(d, DomainInfo) for d in domains)


class TestWorkflowOrchestratorAgent:
    """Tests for the WorkflowOrchestratorAgent."""

    def test_register_workflow(
        self,
        workflow_orchestrator: WorkflowOrchestratorAgent,
        sample_workflow: Workflow,
    ) -> None:
        """Test registering a workflow."""
        workflow_orchestrator.register_workflow(sample_workflow)
        assert sample_workflow.id in workflow_orchestrator.workflows

    def test_get_workflow(
        self,
        workflow_orchestrator: WorkflowOrchestratorAgent,
        sample_workflow: Workflow,
    ) -> None:
        """Test getting a workflow by ID."""
        workflow_orchestrator.register_workflow(sample_workflow)
        retrieved = workflow_orchestrator.get_workflow(sample_workflow.id)
        assert retrieved is not None
        assert retrieved.id == sample_workflow.id

    def test_get_nonexistent_workflow(
        self,
        workflow_orchestrator: WorkflowOrchestratorAgent,
    ) -> None:
        """Test getting a workflow that doesn't exist."""
        result = workflow_orchestrator.get_workflow("nonexistent")
        assert result is None

    def test_delete_workflow(
        self,
        workflow_orchestrator: WorkflowOrchestratorAgent,
        sample_workflow: Workflow,
    ) -> None:
        """Test deleting a workflow."""
        workflow_orchestrator.register_workflow(sample_workflow)
        result = workflow_orchestrator.delete_workflow(sample_workflow.id)
        assert result is True
        assert sample_workflow.id not in workflow_orchestrator.workflows

    def test_execute_workflow(
        self,
        workflow_orchestrator: WorkflowOrchestratorAgent,
        sample_workflow: Workflow,
    ) -> None:
        """Test executing a workflow."""
        workflow_orchestrator.register_workflow(sample_workflow)
        request = WorkflowExecutionRequest(workflow_id=sample_workflow.id)
        result = workflow_orchestrator.execute_workflow(request)
        assert result.workflow_id == sample_workflow.id
        assert result.success is True
        assert len(result.step_results) == 2

    def test_execute_nonexistent_workflow(
        self,
        workflow_orchestrator: WorkflowOrchestratorAgent,
    ) -> None:
        """Test executing a workflow that doesn't exist."""
        request = WorkflowExecutionRequest(workflow_id="nonexistent")
        result = workflow_orchestrator.execute_workflow(request)
        assert result.success is False

    def test_list_workflows(
        self,
        workflow_orchestrator: WorkflowOrchestratorAgent,
        sample_workflow: Workflow,
    ) -> None:
        """Test listing all workflows."""
        workflow_orchestrator.register_workflow(sample_workflow)
        workflows = workflow_orchestrator.list_workflows()
        assert len(workflows) == 1


class TestResultAggregatorAgent:
    """Tests for the ResultAggregatorAgent."""

    def test_aggregate_merge(self, result_aggregator: ResultAggregatorAgent) -> None:
        """Test merge aggregation strategy."""
        step_results = [
            WorkflowStepResult(step_id="1", success=True, output={"key1": "value1"}),
            WorkflowStepResult(step_id="2", success=True, output={"key2": "value2"}),
        ]
        result = result_aggregator.aggregate(step_results, "merge")
        assert result == {"key1": "value1", "key2": "value2"}

    def test_aggregate_concat(self, result_aggregator: ResultAggregatorAgent) -> None:
        """Test concat aggregation strategy."""
        step_results = [
            WorkflowStepResult(step_id="1", success=True, output={"key": "value1"}),
            WorkflowStepResult(step_id="2", success=True, output={"key": "value2"}),
        ]
        result = result_aggregator.aggregate(step_results, "concat")
        assert result == {"key": ["value1", "value2"]}

    def test_aggregate_summary(self, result_aggregator: ResultAggregatorAgent) -> None:
        """Test summary aggregation strategy."""
        step_results = [
            WorkflowStepResult(step_id="1", success=True, output={}),
            WorkflowStepResult(step_id="2", success=False, error="Failed"),
        ]
        result = result_aggregator.aggregate(step_results, "summary")
        assert result["total_steps"] == 2
        assert result["successful_steps"] == 1
        assert result["failed_steps"] == 1

    def test_aggregate_invalid_strategy(
        self,
        result_aggregator: ResultAggregatorAgent,
    ) -> None:
        """Test aggregation with invalid strategy."""
        with pytest.raises(ValueError, match="Unsupported aggregation strategy"):
            result_aggregator.aggregate([], "invalid")

    def test_create_workflow_summary(
        self,
        result_aggregator: ResultAggregatorAgent,
    ) -> None:
        """Test creating a workflow summary."""
        from app.models.workflow import WorkflowResult

        result = WorkflowResult(
            workflow_id="wf-1",
            success=True,
            step_results=[
                WorkflowStepResult(step_id="1", success=True),
                WorkflowStepResult(step_id="2", success=True),
            ],
        )
        summary = result_aggregator.create_workflow_summary(result)
        assert summary["workflow_id"] == "wf-1"
        assert summary["success"] is True
        assert summary["total_steps"] == 2


class TestErrorHandlerAgent:
    """Tests for the ErrorHandlerAgent."""

    def test_classify_timeout_error(self, error_handler: ErrorHandlerAgent) -> None:
        """Test classifying a timeout error."""
        error = TimeoutError("Connection timed out")
        category, severity = error_handler.classify_error(error)
        assert category == ErrorCategory.TIMEOUT

    def test_classify_validation_error(self, error_handler: ErrorHandlerAgent) -> None:
        """Test classifying a validation error."""
        error = ValueError("Invalid input")
        category, severity = error_handler.classify_error(error)
        assert category == ErrorCategory.VALIDATION

    def test_handle_error(self, error_handler: ErrorHandlerAgent) -> None:
        """Test handling an error."""
        error = RuntimeError("Something went wrong")
        record = error_handler.handle_error(error, step_id="step-1", workflow_id="wf-1")
        assert record.message == "Something went wrong"
        assert record.step_id == "step-1"
        assert record.workflow_id == "wf-1"
        assert record.resolved is False

    def test_should_retry(self, error_handler: ErrorHandlerAgent) -> None:
        """Test retry policy check."""
        assert error_handler.should_retry(ErrorCategory.TIMEOUT) is True
        assert error_handler.should_retry(ErrorCategory.VALIDATION) is False

    def test_get_retry_delay(self, error_handler: ErrorHandlerAgent) -> None:
        """Test retry delay calculation."""
        delay = error_handler.get_retry_delay(ErrorCategory.TIMEOUT, 0)
        assert delay == 1.0
        delay = error_handler.get_retry_delay(ErrorCategory.TIMEOUT, 2)
        assert delay > 1.0

    def test_get_fallback_strategy(self, error_handler: ErrorHandlerAgent) -> None:
        """Test fallback strategy retrieval."""
        strategy = error_handler.get_fallback_strategy(ErrorCategory.TIMEOUT)
        assert strategy == "retry"

    def test_resolve_error(self, error_handler: ErrorHandlerAgent) -> None:
        """Test resolving an error."""
        error = RuntimeError("Test error")
        record = error_handler.handle_error(error)
        result = error_handler.resolve_error(record.id, "Fixed by retry")
        assert result is True
        assert record.resolved is True

    def test_get_error_summary(self, error_handler: ErrorHandlerAgent) -> None:
        """Test error summary generation."""
        error_handler.handle_error(RuntimeError("Error 1"))
        error_handler.handle_error(TimeoutError("Error 2"))
        summary = error_handler.get_error_summary()
        assert summary["total_errors"] == 2
        assert summary["unresolved_errors"] == 2


class TestAnalyticsCollectorAgent:
    """Tests for the AnalyticsCollectorAgent."""

    def test_collect_event(self, analytics_collector: AnalyticsCollectorAgent) -> None:
        """Test collecting an event."""
        event = AnalyticsEvent(
            event_type="test",
            domain="security",
            agent="test_agent",
            data={"success": True},
        )
        analytics_collector.collect_event(event)
        assert len(analytics_collector.events) == 1
        assert "security" in analytics_collector.domain_metrics

    def test_record_event(self, analytics_collector: AnalyticsCollectorAgent) -> None:
        """Test recording an event."""
        event = analytics_collector.record_event(
            event_type="test",
            domain="security",
            agent="test_agent",
        )
        assert event.event_type == "test"
        assert len(analytics_collector.events) == 1

    def test_get_domain_metrics(self, analytics_collector: AnalyticsCollectorAgent) -> None:
        """Test getting domain metrics."""
        analytics_collector.record_event("test", "security", "agent")
        metrics = analytics_collector.get_domain_metrics("security")
        assert metrics is not None
        assert metrics.total_requests == 1

    def test_get_cross_domain_analytics(
        self,
        analytics_collector: AnalyticsCollectorAgent,
    ) -> None:
        """Test getting cross-domain analytics."""
        analytics_collector.record_event("test", "security", "agent1")
        analytics_collector.record_event("test", "compliance", "agent2")
        analytics = analytics_collector.get_cross_domain_analytics()
        assert analytics.total_events == 2
        assert len(analytics.domain_metrics) == 2

    def test_get_events_by_domain(
        self,
        analytics_collector: AnalyticsCollectorAgent,
    ) -> None:
        """Test filtering events by domain."""
        analytics_collector.record_event("test", "security", "agent")
        analytics_collector.record_event("test", "compliance", "agent")
        events = analytics_collector.get_events_by_domain("security")
        assert len(events) == 1
        assert events[0].domain == "security"

    def test_clear_events(self, analytics_collector: AnalyticsCollectorAgent) -> None:
        """Test clearing all events."""
        analytics_collector.record_event("test", "security", "agent")
        analytics_collector.clear_events()
        assert len(analytics_collector.events) == 0
        assert len(analytics_collector.domain_metrics) == 0

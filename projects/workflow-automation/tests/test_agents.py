"""Tests for the agent implementations."""

from __future__ import annotations

from datetime import datetime

import pytest

from workflow_automation.agents.integration_automation import (
    IntegrationAutomationAgent,
    IntegrationConfig,
    IntegrationProvider,
    IntegrationStatus,
    SyncRequest,
)
from workflow_automation.agents.performance_analytics import (
    MetricType,
    MetricUnit,
    PerformanceAnalyticsAgent,
    ReportPeriod,
    TrackMetricRequest,
)
from workflow_automation.agents.process_automation import (
    ProcessAutomationAgent,
    ProcessCreateRequest,
    ProcessExecutionRequest,
    ProcessStatus,
    ProcessStep,
    ProcessType,
)
from workflow_automation.agents.workflow_discovery import (
    DiscoveryRequest,
    WorkflowDiscoveryAgent,
    WorkflowStatus,
    WorkflowType,
)
from workflow_automation.agents.workflow_optimization import (
    OptimizationRequest,
    OptimizationPriority,
    OptimizationType,
    WorkflowOptimizationAgent,
)


@pytest.fixture
async def discovery_agent() -> WorkflowDiscoveryAgent:
    """Create and initialize a workflow discovery agent."""
    agent = WorkflowDiscoveryAgent()
    await agent.initialize()
    return agent


@pytest.fixture
async def optimization_agent() -> WorkflowOptimizationAgent:
    """Create and initialize a workflow optimization agent."""
    agent = WorkflowOptimizationAgent()
    await agent.initialize()
    return agent


@pytest.fixture
async def process_agent() -> ProcessAutomationAgent:
    """Create and initialize a process automation agent."""
    agent = ProcessAutomationAgent()
    await agent.initialize()
    return agent


@pytest.fixture
async def integration_agent() -> IntegrationAutomationAgent:
    """Create and initialize an integration automation agent."""
    agent = IntegrationAutomationAgent()
    await agent.initialize()
    return agent


@pytest.fixture
async def analytics_agent() -> PerformanceAnalyticsAgent:
    """Create and initialize a performance analytics agent."""
    agent = PerformanceAnalyticsAgent()
    await agent.initialize()
    return agent


class TestWorkflowDiscoveryAgent:
    """Tests for the WorkflowDiscoveryAgent."""

    async def test_initialize(self, discovery_agent: WorkflowDiscoveryAgent) -> None:
        """Test agent initialization."""
        assert discovery_agent._is_initialized is True

    async def test_discover_workflows(self, discovery_agent: WorkflowDiscoveryAgent) -> None:
        """Test workflow discovery."""
        request = DiscoveryRequest(
            sources=["n8n"],
            workflow_types=[WorkflowType.LEAD_GENERATION],
            max_results=10,
        )
        result = await discovery_agent.discover(request)

        assert result.total_found >= 0
        assert result.duration_seconds >= 0
        assert "n8n" in result.sources_queried

    async def test_discover_multiple_sources(
        self, discovery_agent: WorkflowDiscoveryAgent
    ) -> None:
        """Test discovery from multiple sources."""
        request = DiscoveryRequest(sources=["n8n", "zapier", "make"])
        result = await discovery_agent.discover(request)

        assert len(result.sources_queried) == 3

    async def test_list_workflows_empty(
        self, discovery_agent: WorkflowDiscoveryAgent
    ) -> None:
        """Test listing workflows when none discovered."""
        workflows = await discovery_agent.list_workflows()
        assert workflows == []

    async def test_get_workflow_not_found(
        self, discovery_agent: WorkflowDiscoveryAgent
    ) -> None:
        """Test getting a non-existent workflow."""
        workflow = await discovery_agent.get_workflow("non-existent-id")
        assert workflow is None

    async def test_discover_and_retrieve(
        self, discovery_agent: WorkflowDiscoveryAgent
    ) -> None:
        """Test discovering and then retrieving a workflow."""
        request = DiscoveryRequest(sources=["n8n"])
        result = await discovery_agent.discover(request)

        if result.workflows:
            workflow_id = result.workflows[0].workflow_id
            retrieved = await discovery_agent.get_workflow(workflow_id)
            assert retrieved is not None
            assert retrieved.workflow_id == workflow_id

    async def test_refresh_workflow(
        self, discovery_agent: WorkflowDiscoveryAgent
    ) -> None:
        """Test refreshing a workflow."""
        request = DiscoveryRequest(sources=["n8n"])
        result = await discovery_agent.discover(request)

        if result.workflows:
            workflow_id = result.workflows[0].workflow_id
            refreshed = await discovery_agent.refresh_workflow(workflow_id)
            assert refreshed is not None
            assert refreshed.updated_at >= refreshed.created_at


class TestWorkflowOptimizationAgent:
    """Tests for the WorkflowOptimizationAgent."""

    async def test_initialize(self, optimization_agent: WorkflowOptimizationAgent) -> None:
        """Test agent initialization."""
        assert optimization_agent._is_initialized is True

    async def test_optimize_workflow_not_found(
        self, optimization_agent: WorkflowOptimizationAgent
    ) -> None:
        """Test optimizing a non-existent workflow."""
        request = OptimizationRequest(workflow_id="non-existent-id")
        with pytest.raises(ValueError, match="Workflow not found"):
            await optimization_agent.optimize(request)

    async def test_optimize_workflow(
        self, optimization_agent: WorkflowOptimizationAgent
    ) -> None:
        """Test optimizing an existing workflow."""
        # First discover a workflow
        discovery_request = DiscoveryRequest(sources=["n8n"])
        discovery_result = await optimization_agent.discovery_agent.discover(
            discovery_request
        )

        if discovery_result.workflows:
            workflow_id = discovery_result.workflows[0].workflow_id
            request = OptimizationRequest(workflow_id=workflow_id)
            report = await optimization_agent.optimize(request)

            assert report.workflow_id == workflow_id
            assert 0 <= report.overall_score <= 100
            assert isinstance(report.bottlenecks, list)
            assert isinstance(report.suggestions, list)

    async def test_optimization_history(
        self, optimization_agent: WorkflowOptimizationAgent
    ) -> None:
        """Test optimization history tracking."""
        discovery_request = DiscoveryRequest(sources=["n8n"])
        discovery_result = await optimization_agent.discovery_agent.discover(
            discovery_request
        )

        if discovery_result.workflows:
            workflow_id = discovery_result.workflows[0].workflow_id

            # Generate two reports
            await optimization_agent.optimize(OptimizationRequest(workflow_id=workflow_id))
            await optimization_agent.optimize(OptimizationRequest(workflow_id=workflow_id))

            history = await optimization_agent.get_optimization_history(workflow_id)
            assert len(history) == 2

    async def test_compare_optimizations_insufficient_history(
        self, optimization_agent: WorkflowOptimizationAgent
    ) -> None:
        """Test comparison with insufficient history."""
        comparison = await optimization_agent.compare_optimizations("non-existent")
        assert comparison is None


class TestProcessAutomationAgent:
    """Tests for the ProcessAutomationAgent."""

    async def test_initialize(self, process_agent: ProcessAutomationAgent) -> None:
        """Test agent initialization."""
        assert process_agent._is_initialized is True

    async def test_create_process(self, process_agent: ProcessAutomationAgent) -> None:
        """Test creating a process."""
        request = ProcessCreateRequest(
            name="Test Process",
            description="A test process",
            process_type=ProcessType.DATA_SYNC,
            steps=[
                ProcessStep(
                    name="step1",
                    action="http_request",
                    config={"url": "https://example.com"},
                    order=0,
                ),
            ],
        )
        process = await process_agent.create_process(request)

        assert process.name == "Test Process"
        assert process.process_type == ProcessType.DATA_SYNC
        assert len(process.steps) == 1
        assert process.is_active is True

    async def test_execute_process(
        self, process_agent: ProcessAutomationAgent
    ) -> None:
        """Test executing a process."""
        # Create a process first
        create_request = ProcessCreateRequest(
            name="Test Execute Process",
            process_type=ProcessType.CUSTOM,
            steps=[
                ProcessStep(
                    name="noop",
                    action="data_transform",
                    config={"transform_type": "identity"},
                    order=0,
                ),
            ],
        )
        process = await process_agent.create_process(create_request)

        # Execute it
        execution_request = ProcessExecutionRequest(
            process_id=process.process_id,
            parameters={"data": {"key": "value"}},
        )
        execution = await process_agent.execute_process(execution_request)

        assert execution.process_id == process.process_id
        assert execution.status in [ProcessStatus.PENDING, ProcessStatus.RUNNING]

    async def test_execute_nonexistent_process(
        self, process_agent: ProcessAutomationAgent
    ) -> None:
        """Test executing a non-existent process."""
        request = ProcessExecutionRequest(process_id="non-existent-id")
        with pytest.raises(ValueError, match="Process not found"):
            await process_agent.execute_process(request)

    async def test_list_processes(self, process_agent: ProcessAutomationAgent) -> None:
        """Test listing processes."""
        # Create a process
        await process_agent.create_process(
            ProcessCreateRequest(
                name="List Test Process",
                process_type=ProcessType.CUSTOM,
            )
        )

        processes = await process_agent.list_processes()
        assert len(processes) >= 1

    async def test_list_executions(self, process_agent: ProcessAutomationAgent) -> None:
        """Test listing executions."""
        # Create and execute a process
        process = await process_agent.create_process(
            ProcessCreateRequest(
                name="Execution Test Process",
                process_type=ProcessType.CUSTOM,
                steps=[
                    ProcessStep(
                        name="noop",
                        action="data_transform",
                        config={"transform_type": "identity"},
                        order=0,
                    ),
                ],
            )
        )
        await process_agent.execute_process(
            ProcessExecutionRequest(process_id=process.process_id)
        )

        executions = await process_agent.list_executions(process_id=process.process_id)
        assert len(executions) >= 1

    async def test_cancel_execution_not_running(
        self, process_agent: ProcessAutomationAgent
    ) -> None:
        """Test cancelling a non-running execution."""
        result = await process_agent.cancel_execution("non-existent-id")
        assert result is False


class TestIntegrationAutomationAgent:
    """Tests for the IntegrationAutomationAgent."""

    async def test_initialize(self, integration_agent: IntegrationAutomationAgent) -> None:
        """Test agent initialization."""
        assert integration_agent._is_initialized is True

    async def test_configure_integration(
        self, integration_agent: IntegrationAutomationAgent
    ) -> None:
        """Test configuring an integration."""
        config = IntegrationConfig(
            provider=IntegrationProvider.N8N,
            base_url="http://localhost:5678",
            api_key="test-key",
        )
        result = await integration_agent.configure_integration(config)

        assert result.provider == IntegrationProvider.N8N
        assert result.base_url == "http://localhost:5678"

    async def test_check_health_not_configured(
        self, integration_agent: IntegrationAutomationAgent
    ) -> None:
        """Test health check for unconfigured provider."""
        with pytest.raises(ValueError, match="Provider not configured"):
            await integration_agent.check_health(IntegrationProvider.ZAPIER)

    async def test_sync_not_configured(
        self, integration_agent: IntegrationAutomationAgent
    ) -> None:
        """Test sync with unconfigured provider."""
        request = SyncRequest(provider=IntegrationProvider.MAKE)
        with pytest.raises(ValueError, match="Provider not configured"):
            await integration_agent.sync(request)

    async def test_get_all_health_empty(
        self, integration_agent: IntegrationAutomationAgent
    ) -> None:
        """Test getting health for all integrations when none configured."""
        health = await integration_agent.get_all_health()
        assert health == {}

    async def test_disconnect(self, integration_agent: IntegrationAutomationAgent) -> None:
        """Test disconnecting an integration."""
        # Configure first
        await integration_agent.configure_integration(
            IntegrationConfig(
                provider=IntegrationProvider.N8N,
                base_url="http://localhost:5678",
                api_key="test-key",
            )
        )

        result = await integration_agent.disconnect(IntegrationProvider.N8N)
        assert result is True

        health = await integration_agent.get_all_health()
        assert health["n8n"].status == IntegrationStatus.DISCONNECTED


class TestPerformanceAnalyticsAgent:
    """Tests for the PerformanceAnalyticsAgent."""

    async def test_initialize(self, analytics_agent: PerformanceAnalyticsAgent) -> None:
        """Test agent initialization."""
        assert analytics_agent._is_initialized is True

    async def test_default_kpis_registered(
        self, analytics_agent: PerformanceAnalyticsAgent
    ) -> None:
        """Test that default KPIs are registered."""
        kpis = await analytics_agent.get_kpis()
        assert len(kpis) >= 5

        kpi_names = {kpi.name for kpi in kpis}
        assert "workflow_execution_rate" in kpi_names
        assert "average_execution_time" in kpi_names
        assert "leads_processed" in kpi_names

    async def test_track_metric(self, analytics_agent: PerformanceAnalyticsAgent) -> None:
        """Test tracking a metric event."""
        request = TrackMetricRequest(
            metric_name="workflow_execution_success",
            metric_type=MetricType.COUNTER,
            value=1.0,
            unit=MetricUnit.COUNT,
        )
        event = await analytics_agent.track_metric(request)

        assert event.metric_name == "workflow_execution_success"
        assert event.value == 1.0

    async def test_track_multiple_metrics(
        self, analytics_agent: PerformanceAnalyticsAgent
    ) -> None:
        """Test tracking multiple metrics."""
        for i in range(5):
            await analytics_agent.track_metric(
                TrackMetricRequest(
                    metric_name="workflow_execution_success",
                    metric_type=MetricType.COUNTER,
                    value=1.0 if i < 4 else 0.0,
                    unit=MetricUnit.COUNT,
                )
            )

        events = await analytics_agent.get_recent_events(
            metric_name="workflow_execution_success"
        )
        assert len(events) == 5

    async def test_generate_report(self, analytics_agent: PerformanceAnalyticsAgent) -> None:
        """Test generating a performance report."""
        # Track some metrics
        await analytics_agent.track_metric(
            TrackMetricRequest(
                metric_name="workflow_execution_success",
                metric_type=MetricType.COUNTER,
                value=1.0,
            )
        )

        report_period = ReportPeriod(
            start=datetime.utcnow().replace(hour=0, minute=0, second=0),
            end=datetime.utcnow(),
        )
        from workflow_automation.agents.performance_analytics import ReportRequest

        request = ReportRequest(period=report_period)
        report = await analytics_agent.generate_report(request)

        assert report.report_id
        assert len(report.kpis) >= 5
        assert isinstance(report.insights, list)
        assert isinstance(report.recommendations, list)

    async def test_get_recent_events(
        self, analytics_agent: PerformanceAnalyticsAgent
    ) -> None:
        """Test getting recent events."""
        await analytics_agent.track_metric(
            TrackMetricRequest(
                metric_name="test_metric",
                metric_type=MetricType.GAUGE,
                value=42.0,
            )
        )

        events = await analytics_agent.get_recent_events(metric_name="test_metric")
        assert len(events) == 1
        assert events[0].value == 42.0

    async def test_get_report_history(
        self, analytics_agent: PerformanceAnalyticsAgent
    ) -> None:
        """Test getting report history."""
        from workflow_automation.agents.performance_analytics import ReportRequest

        report_period = ReportPeriod(
            start=datetime.utcnow().replace(hour=0, minute=0, second=0),
            end=datetime.utcnow(),
        )
        await analytics_agent.generate_report(ReportRequest(period=report_period))

        history = await analytics_agent.get_report_history()
        assert len(history) >= 1

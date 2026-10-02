"""Orchestrator Service.

High-level service that coordinates between agents to provide
a unified orchestration interface.
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.analytics_collector import AnalyticsCollectorAgent
from app.agents.domain_router import DomainRouterAgent
from app.agents.error_handler import ErrorHandlerAgent
from app.agents.result_aggregator import ResultAggregatorAgent
from app.agents.workflow_orchestrator import WorkflowOrchestratorAgent
from app.models.analytics import AnalyticsEvent
from app.models.domain import DomainRequest, DomainResponse
from app.models.workflow import (
    Workflow,
    WorkflowExecutionRequest,
    WorkflowResult,
)

logger = logging.getLogger(__name__)


class OrchestratorService:
    """High-level service coordinating all agents.

    Provides a unified interface for workflow execution, domain routing,
    result aggregation, error handling, and analytics collection.

    Attributes:
        domain_router: Domain routing agent.
        workflow_orchestrator: Workflow orchestration agent.
        result_aggregator: Result aggregation agent.
        error_handler: Error handling agent.
        analytics_collector: Analytics collection agent.
    """

    def __init__(self) -> None:
        """Initialize the Orchestrator Service with all agents."""
        self.domain_router = DomainRouterAgent()
        self.workflow_orchestrator = WorkflowOrchestratorAgent()
        self.result_aggregator = ResultAggregatorAgent()
        self.error_handler = ErrorHandlerAgent()
        self.analytics_collector = AnalyticsCollectorAgent()

    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow.

        Args:
            workflow: Workflow to register.
        """
        self.workflow_orchestrator.register_workflow(workflow)

    def execute_workflow(self, request: WorkflowExecutionRequest) -> WorkflowResult:
        """Execute a workflow with full error handling and analytics.

        Args:
            request: Workflow execution request.

        Returns:
            Workflow execution result.
        """
        # Record start event
        self.analytics_collector.record_event(
            event_type="workflow_started",
            domain="orchestrator",
            agent="workflow_orchestrator",
            data={"workflow_id": request.workflow_id},
        )

        try:
            result = self.workflow_orchestrator.execute_workflow(request)

            # Record completion event
            self.analytics_collector.record_event(
                event_type="workflow_completed",
                domain="orchestrator",
                agent="workflow_orchestrator",
                data={
                    "workflow_id": request.workflow_id,
                    "success": result.success,
                    "duration_ms": result.total_duration_ms,
                },
            )

            return result
        except Exception as exc:
            self.error_handler.handle_error(exc, workflow_id=request.workflow_id)
            self.analytics_collector.record_event(
                event_type="workflow_failed",
                domain="orchestrator",
                agent="error_handler",
                data={"workflow_id": request.workflow_id, "error": str(exc)},
            )
            raise

    def route_request(self, request: DomainRequest) -> DomainResponse:
        """Route a domain request with analytics.

        Args:
            request: Domain request to route.

        Returns:
            Domain response.
        """
        self.analytics_collector.record_event(
            event_type="domain_request",
            domain=request.domain,
            agent="domain_router",
            data={"action": request.action, "priority": request.priority},
        )

        response = self.domain_router.route(request)

        self.analytics_collector.record_event(
            event_type="domain_response",
            domain=request.domain,
            agent="domain_router",
            data={"success": response.success},
        )

        return response

    def get_analytics(self) -> dict[str, Any]:
        """Get comprehensive analytics.

        Returns:
            Analytics summary.
        """
        return self.analytics_collector.get_cross_domain_analytics().model_dump()

    def get_system_status(self) -> dict[str, Any]:
        """Get overall system status.

        Returns:
            System status information.
        """
        return {
            "domains": len(self.domain_router.list_domains()),
            "workflows": len(self.workflow_orchestrator.list_workflows()),
            "errors": self.error_handler.get_error_summary(),
            "analytics": {
                "total_events": len(self.analytics_collector.events),
                "domains_tracked": len(self.analytics_collector.domain_metrics),
            },
        }

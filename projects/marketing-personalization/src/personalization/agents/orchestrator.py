"""Orchestrator Agent - Coordinates agent workflows and manages state."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

from personalization.agents.analysis import AnalysisAgent
from personalization.agents.data_collection import DataCollectionAgent
from personalization.agents.governance import GovernanceAgent
from personalization.agents.optimization import OptimizationAgent
from personalization.agents.performance_analytics import PerformanceAnalyticsAgent
from personalization.agents.personalization import PersonalizationAgent

logger = structlog.get_logger(__name__)


class WorkflowState(BaseModel):
    """Workflow state model."""

    workflow_id: str
    status: str = "pending"
    current_step: str | None = None
    completed_steps: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class Orchestrator:
    """Orchestrator agent that coordinates all other agents and manages workflow state."""

    def __init__(self) -> None:
        """Initialize the Orchestrator with all sub-agents."""
        self.name = "orchestrator"
        self.description = "Coordinates agent workflows and manages state"

        self.data_collection = DataCollectionAgent()
        self.analysis = AnalysisAgent()
        self.personalization = PersonalizationAgent()
        self.optimization = OptimizationAgent()
        self.governance = GovernanceAgent()
        self.performance_analytics = PerformanceAnalyticsAgent()

        logger.info("Orchestrator initialized with all agents")

    async def run_campaign_workflow(
        self,
        campaign_id: str,
        customer_segment: str | None = None,
    ) -> WorkflowState:
        """Run the complete campaign workflow."""
        logger.info("Starting campaign workflow", campaign_id=campaign_id)
        state = WorkflowState(workflow_id=f"workflow_{campaign_id}")

        try:
            state.current_step = "data_collection"
            customer_data = await self.data_collection.collect_customer_data()
            state.data["customer_data"] = [c.model_dump() for c in customer_data]
            state.completed_steps.append("data_collection")

            state.current_step = "analysis"
            analysis_results = await self.analysis.analyze_customer_segments(
                state.data["customer_data"]
            )
            state.data["analysis"] = [r.model_dump() for r in analysis_results]
            state.completed_steps.append("analysis")

            state.current_step = "personalization"
            for customer in customer_data:
                content = await self.personalization.generate_content(customer.customer_id, "email")
                state.data.setdefault("personalized_content", []).append(content.model_dump())
            state.completed_steps.append("personalization")

            state.current_step = "governance"
            compliance = await self.governance.check_compliance(campaign_id, {})
            state.data["compliance"] = compliance.model_dump()
            state.completed_steps.append("governance")

            state.current_step = "optimization"
            opt_result = await self.optimization.optimize_campaign(campaign_id, {})
            state.data["optimization"] = opt_result.model_dump()
            state.completed_steps.append("optimization")

            state.current_step = "performance_analytics"
            metrics = await self.performance_analytics.calculate_campaign_metrics(campaign_id, {})
            state.data["metrics"] = metrics.model_dump()
            state.completed_steps.append("performance_analytics")

            state.status = "completed"
            state.current_step = None
        except Exception as e:
            logger.error("Workflow failed", error=str(e), step=state.current_step)
            state.status = "failed"
            state.errors.append(str(e))

        logger.info("Campaign workflow completed", campaign_id=campaign_id, status=state.status)
        return state

    async def run_segmentation_workflow(
        self,
        customer_ids: list[str] | None = None,
    ) -> WorkflowState:
        """Run the customer segmentation workflow."""
        logger.info("Starting segmentation workflow")
        state = WorkflowState(workflow_id="segmentation_workflow")

        try:
            state.current_step = "data_collection"
            customer_data = await self.data_collection.collect_customer_data(customer_ids)
            state.data["customers"] = [c.model_dump() for c in customer_data]
            state.completed_steps.append("data_collection")

            state.current_step = "analysis"
            segments = await self.analysis.analyze_customer_segments(state.data["customers"])
            state.data["segments"] = [s.model_dump() for s in segments]
            state.completed_steps.append("analysis")

            state.status = "completed"
            state.current_step = None
        except Exception as e:
            logger.error("Segmentation workflow failed", error=str(e))
            state.status = "failed"
            state.errors.append(str(e))

        return state

    async def run_optimization_workflow(
        self,
        campaign_id: str,
    ) -> WorkflowState:
        """Run the campaign optimization workflow."""
        logger.info("Starting optimization workflow", campaign_id=campaign_id)
        state = WorkflowState(workflow_id=f"optimization_{campaign_id}")

        try:
            state.current_step = "performance_analytics"
            metrics = await self.performance_analytics.calculate_campaign_metrics(campaign_id, {})
            state.data["metrics"] = metrics.model_dump()
            state.completed_steps.append("performance_analytics")

            state.current_step = "optimization"
            opt_result = await self.optimization.optimize_campaign(campaign_id, {})
            state.data["optimization"] = opt_result.model_dump()
            state.completed_steps.append("optimization")

            state.status = "completed"
            state.current_step = None
        except Exception as e:
            logger.error("Optimization workflow failed", error=str(e))
            state.status = "failed"
            state.errors.append(str(e))

        return state

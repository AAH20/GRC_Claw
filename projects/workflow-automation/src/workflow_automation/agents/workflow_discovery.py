"""Workflow Discovery Agent - discovers and maps existing marketing workflows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class WorkflowStatus(StrEnum):
    """Workflow status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ERROR = "error"


class WorkflowType(StrEnum):
    """Workflow type enumeration."""

    LEAD_GENERATION = "lead_generation"
    EMAIL_CAMPAIGN = "email_campaign"
    SOCIAL_MEDIA = "social_media"
    ANALYTICS = "analytics"
    ONBOARDING = "onboarding"
    CUSTOM = "custom"


class WorkflowStep(BaseModel):
    """Represents a single step in a workflow."""

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    step_type: str
    config: dict[str, Any] = Field(default_factory=dict)
    order: int
    depends_on: list[str] = Field(default_factory=list)


class DiscoveredWorkflow(BaseModel):
    """A discovered marketing workflow."""

    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    workflow_type: WorkflowType
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    source: str
    steps: list[WorkflowStep] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DiscoveryRequest(BaseModel):
    """Request to discover workflows."""

    sources: list[str] = Field(default_factory=list)
    workflow_types: list[WorkflowType] = Field(default_factory=list)
    include_inactive: bool = False
    max_results: int = Field(default=100, ge=1, le=1000)


class DiscoveryResult(BaseModel):
    """Result of a workflow discovery operation."""

    discovery_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflows: list[DiscoveredWorkflow] = Field(default_factory=list)
    total_found: int = 0
    sources_queried: list[str] = Field(default_factory=list)
    duration_seconds: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class WorkflowDiscoveryAgent:
    """Agent responsible for discovering and mapping marketing workflows.

    This agent scans connected platforms (n8n, Zapier, Make) to identify
    existing marketing workflows, their steps, dependencies, and configurations.
    """

    _discovered_workflows: dict[str, DiscoveredWorkflow] = field(default_factory=dict)
    _is_initialized: bool = False

    async def initialize(self) -> None:
        """Initialize the discovery agent."""
        logger.info("Initializing WorkflowDiscoveryAgent")
        self._is_initialized = True

    async def discover(self, request: DiscoveryRequest) -> DiscoveryResult:
        """Discover workflows from configured sources.

        Args:
            request: Discovery request with filters and options.

        Returns:
            DiscoveryResult containing all discovered workflows.

        Raises:
            RuntimeError: If the agent is not initialized.
        """
        if not self._is_initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        start_time = datetime.utcnow()
        logger.info(
            "Starting workflow discovery",
            sources=request.sources,
            types=[t.value for t in request.workflow_types],
        )

        all_workflows: list[DiscoveredWorkflow] = []

        # Discover from each source
        for source in request.sources or ["n8n", "zapier", "make"]:
            try:
                workflows = await self._discover_from_source(source, request)
                all_workflows.extend(workflows)
                logger.info(
                    "Discovered workflows from source",
                    source=source,
                    count=len(workflows),
                )
            except Exception as e:
                logger.error(
                    "Failed to discover workflows from source",
                    source=source,
                    error=str(e),
                )

        # Filter by type if specified
        if request.workflow_types:
            type_values = {t.value for t in request.workflow_types}
            all_workflows = [w for w in all_workflows if w.workflow_type.value in type_values]

        # Filter inactive if not included
        if not request.include_inactive:
            all_workflows = [w for w in all_workflows if w.status == WorkflowStatus.ACTIVE]

        # Apply limit
        all_workflows = all_workflows[: request.max_results]

        # Store discovered workflows
        for workflow in all_workflows:
            self._discovered_workflows[workflow.workflow_id] = workflow

        duration = (datetime.utcnow() - start_time).total_seconds()

        result = DiscoveryResult(
            workflows=all_workflows,
            total_found=len(all_workflows),
            sources_queried=request.sources or ["n8n", "zapier", "make"],
            duration_seconds=duration,
        )

        logger.info(
            "Workflow discovery completed",
            total_found=result.total_found,
            duration_seconds=duration,
        )

        return result

    async def _discover_from_source(
        self, source: str, request: DiscoveryRequest
    ) -> list[DiscoveredWorkflow]:
        """Discover workflows from a specific source.

        Args:
            source: The source platform name.
            request: Discovery request parameters.

        Returns:
            List of discovered workflows from the source.
        """
        # This would integrate with actual n8n/Zapier/Make APIs
        # For now, return mock data for demonstration
        logger.info(f"Discovering workflows from {source}")

        mock_workflows = [
            DiscoveredWorkflow(
                name=f"{source}_lead_gen_workflow",
                description=f"Lead generation workflow from {source}",
                workflow_type=WorkflowType.LEAD_GENERATION,
                source=source,
                steps=[
                    WorkflowStep(
                        name="trigger",
                        description="Form submission trigger",
                        step_type="trigger",
                        order=0,
                    ),
                    WorkflowStep(
                        name="enrich",
                        description="Enrich lead data",
                        step_type="action",
                        order=1,
                        depends_on=["trigger"],
                    ),
                    WorkflowStep(
                        name="notify",
                        description="Send notification",
                        step_type="action",
                        order=2,
                        depends_on=["enrich"],
                    ),
                ],
            ),
        ]

        return mock_workflows

    async def get_workflow(self, workflow_id: str) -> DiscoveredWorkflow | None:
        """Get a discovered workflow by ID.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            The discovered workflow or None if not found.
        """
        return self._discovered_workflows.get(workflow_id)

    async def list_workflows(
        self,
        source: str | None = None,
        workflow_type: WorkflowType | None = None,
        status: WorkflowStatus | None = None,
    ) -> list[DiscoveredWorkflow]:
        """List all discovered workflows with optional filters.

        Args:
            source: Filter by source platform.
            workflow_type: Filter by workflow type.
            status: Filter by workflow status.

        Returns:
            List of matching workflows.
        """
        workflows = list(self._discovered_workflows.values())

        if source:
            workflows = [w for w in workflows if w.source == source]
        if workflow_type:
            workflows = [w for w in workflows if w.workflow_type == workflow_type]
        if status:
            workflows = [w for w in workflows if w.status == status]

        return workflows

    async def refresh_workflow(self, workflow_id: str) -> DiscoveredWorkflow | None:
        """Refresh a workflow's data from its source.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            The refreshed workflow or None if not found.
        """
        workflow = self._discovered_workflows.get(workflow_id)
        if not workflow:
            return None

        logger.info("Refreshing workflow", workflow_id=workflow_id)
        workflow.updated_at = datetime.utcnow()
        return workflow

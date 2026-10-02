"""Workflow API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from workflow_automation.agents.workflow_discovery import (
    DiscoveryRequest,
    WorkflowDiscoveryAgent,
    WorkflowStatus,
)
from workflow_automation.agents.workflow_optimization import (
    OptimizationRequest,
    WorkflowOptimizationAgent,
)

router = APIRouter()

# Module-level agents (initialized on first use)
_discovery_agent: WorkflowDiscoveryAgent | None = None
_optimization_agent: WorkflowOptimizationAgent | None = None


def _get_discovery_agent() -> WorkflowDiscoveryAgent:
    global _discovery_agent
    if _discovery_agent is None:
        _discovery_agent = WorkflowDiscoveryAgent()
    return _discovery_agent


def _get_optimization_agent() -> WorkflowOptimizationAgent:
    global _optimization_agent
    if _optimization_agent is None:
        _optimization_agent = WorkflowOptimizationAgent()
    return _optimization_agent


@router.post("/discover")
async def discover_workflows(request: DiscoveryRequest) -> dict:
    """Discover workflows from configured sources."""
    agent = _get_discovery_agent()
    if not agent._is_initialized:
        await agent.initialize()

    result = await agent.discover(request)
    return {
        "discovery_id": result.discovery_id,
        "workflows": [w.model_dump() for w in result.workflows],
        "total_found": result.total_found,
        "sources_queried": result.sources_queried,
    }


@router.get("")
async def list_workflows(
    source: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """List all discovered workflows."""
    agent = _get_discovery_agent()
    if not agent._is_initialized:
        await agent.initialize()

    workflows = await agent.list_workflows(
        source=source,
        status=WorkflowStatus(status) if status else None,
    )
    return [w.model_dump() for w in workflows]


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str) -> dict:
    """Get a specific workflow by ID."""
    agent = _get_discovery_agent()
    if not agent._is_initialized:
        await agent.initialize()

    workflow = await agent.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.model_dump()


@router.post("/{workflow_id}/optimize")
async def optimize_workflow(workflow_id: str, request: OptimizationRequest) -> dict:
    """Optimize a workflow."""
    agent = _get_optimization_agent()
    if not agent._is_initialized:
        await agent.initialize()

    request.workflow_id = workflow_id
    try:
        report = await agent.optimize(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return report.model_dump()


@router.post("/{workflow_id}/refresh")
async def refresh_workflow(workflow_id: str) -> dict:
    """Refresh a workflow's data."""
    agent = _get_discovery_agent()
    if not agent._is_initialized:
        await agent.initialize()

    workflow = await agent.refresh_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.model_dump()

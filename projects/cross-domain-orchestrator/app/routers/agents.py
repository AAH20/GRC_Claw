"""Agents router.

Provides endpoints for agent management and monitoring.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.agents.analytics_collector import AnalyticsCollectorAgent
from app.agents.domain_router import DomainRouterAgent
from app.agents.error_handler import ErrorHandlerAgent
from app.agents.result_aggregator import ResultAggregatorAgent
from app.agents.workflow_orchestrator import WorkflowOrchestratorAgent

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level agent instances (in production, use dependency injection)
_agents: dict[str, object] = {
    "domain_router": DomainRouterAgent(),
    "workflow_orchestrator": WorkflowOrchestratorAgent(),
    "result_aggregator": ResultAggregatorAgent(),
    "error_handler": ErrorHandlerAgent(),
    "analytics_collector": AnalyticsCollectorAgent(),
}


@router.get("")
async def list_agents() -> list[dict]:
    """List all registered agents.

    Returns:
        List of agent information.
    """
    return [
        {
            "name": name,
            "type": type(agent).__name__,
            "status": "active",
        }
        for name, agent in _agents.items()
    ]


@router.get("/{agent_name}/status")
async def get_agent_status(agent_name: str) -> dict:
    """Get status information for a specific agent.

    Args:
        agent_name: Agent name.

    Returns:
        Agent status information.

    Raises:
        HTTPException: If the agent is not found.
    """
    from fastapi import HTTPException, status

    if agent_name not in _agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found",
        )

    agent = _agents[agent_name]
    status_info: dict = {
        "name": agent_name,
        "type": type(agent).__name__,
        "status": "active",
    }

    # Add agent-specific status
    if isinstance(agent, DomainRouterAgent):
        status_info["registered_domains"] = len(agent.domains)
    elif isinstance(agent, WorkflowOrchestratorAgent):
        status_info["registered_workflows"] = len(agent.workflows)
        status_info["active_executions"] = len(agent.active_executions)
    elif isinstance(agent, ErrorHandlerAgent):
        status_info["error_summary"] = agent.get_error_summary()
    elif isinstance(agent, AnalyticsCollectorAgent):
        status_info["total_events"] = len(agent.events)
        status_info["domains_tracked"] = len(agent.domain_metrics)

    return status_info


@router.post("/{agent_name}/reset")
async def reset_agent(agent_name: str) -> dict:
    """Reset an agent's state.

    Args:
        agent_name: Agent name.

    Returns:
        Reset confirmation.

    Raises:
        HTTPException: If the agent is not found.
    """
    from fastapi import HTTPException, status

    if agent_name not in _agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found",
        )

    agent = _agents[agent_name]
    if isinstance(agent, AnalyticsCollectorAgent):
        agent.clear_events()
    elif isinstance(agent, ErrorHandlerAgent):
        agent.error_log.clear()

    return {"agent": agent_name, "reset": True}

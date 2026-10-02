"""Agent status routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from fraud_detection.agents.account_analyzer import AccountAnalyzerAgent
from fraud_detection.agents.anomaly_detector import AnomalyDetectorAgent
from fraud_detection.agents.pattern_detector import PatternDetectorAgent
from fraud_detection.agents.risk_scorer import RiskScorerAgent
from fraud_detection.agents.transaction_monitor import TransactionMonitorAgent
from fraud_detection.api.dependencies import verify_api_key
from fraud_detection.config.logging_config import get_logger
from fraud_detection.models.schemas import AgentStatus, AgentsStatusResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/agents", tags=["agents"])

_agents: list = []


def _get_agents() -> list:
    """Get or create agent instances.

    Returns:
        List of all agent instances.
    """
    global _agents
    if not _agents:
        _agents = [
            PatternDetectorAgent(),
            AnomalyDetectorAgent(),
            RiskScorerAgent(),
            AccountAnalyzerAgent(),
            TransactionMonitorAgent(),
        ]
    return _agents


@router.get("/status", response_model=AgentsStatusResponse)
async def get_agents_status(
    api_key: Annotated[str, Depends(verify_api_key)],
) -> AgentsStatusResponse:
    """Get status of all agents.

    Args:
        api_key: Verified API key.

    Returns:
        AgentsStatusResponse with all agent statuses.
    """
    agents = _get_agents()
    statuses = []
    for agent in agents:
        status = agent.get_status()
        statuses.append(
            AgentStatus(
                agent_name=status["agent_name"],
                status=status["status"],
                last_activity=status.get("last_activity"),
                tasks_processed=status.get("tasks_processed", 0),
                error_count=status.get("error_count", 0),
            )
        )

    overall = "healthy" if all(s.status != "error" for s in statuses) else "degraded"
    return AgentsStatusResponse(agents=statuses, overall_status=overall)

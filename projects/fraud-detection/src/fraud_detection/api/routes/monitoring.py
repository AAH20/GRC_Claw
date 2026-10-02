"""Transaction monitoring routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from fraud_detection.agents.transaction_monitor import TransactionMonitorAgent
from fraud_detection.api.dependencies import verify_api_key
from fraud_detection.config.logging_config import get_logger
from fraud_detection.models.schemas import MonitoringSession, Transaction

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/monitor", tags=["monitoring"])

_monitor_agent: TransactionMonitorAgent | None = None


def get_monitor_agent() -> TransactionMonitorAgent:
    """Get or create TransactionMonitorAgent singleton.

    Returns:
        TransactionMonitorAgent instance.
    """
    global _monitor_agent
    if _monitor_agent is None:
        _monitor_agent = TransactionMonitorAgent()
    return _monitor_agent


@router.post("/start", response_model=MonitoringSession)
async def start_monitoring(
    account_id: str,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> MonitoringSession:
    """Start monitoring an account's transaction stream.

    Args:
        account_id: Account to monitor.
        api_key: Verified API key.

    Returns:
        MonitoringSession for the new session.
    """
    agent = get_monitor_agent()
    return await agent.start_monitoring(account_id)


@router.post("/stop", response_model=MonitoringSession)
async def stop_monitoring(
    session_id: str,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> MonitoringSession:
    """Stop a monitoring session.

    Args:
        session_id: Session to stop.
        api_key: Verified API key.

    Returns:
        Updated MonitoringSession.

    Raises:
        HTTPException: If session not found.
    """
    agent = get_monitor_agent()
    try:
        return await agent.stop_monitoring(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

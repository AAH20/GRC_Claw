"""Account analysis routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from fraud_detection.agents.account_analyzer import AccountAnalyzerAgent
from fraud_detection.api.dependencies import verify_api_key
from fraud_detection.config.logging_config import get_logger
from fraud_detection.models.schemas import AccountAnalysis, Transaction

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/accounts", tags=["accounts"])

_account_agent: AccountAnalyzerAgent | None = None


def get_account_agent() -> AccountAnalyzerAgent:
    """Get or create AccountAnalyzerAgent singleton.

    Returns:
        AccountAnalyzerAgent instance.
    """
    global _account_agent
    if _account_agent is None:
        _account_agent = AccountAnalyzerAgent()
    return _account_agent


@router.post("/analyze", response_model=AccountAnalysis)
async def analyze_account(
    account_id: str,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> AccountAnalysis:
    """Analyze an account for fraud risk.

    Args:
        account_id: Account identifier.
        api_key: Verified API key.

    Returns:
        AccountAnalysis with profile and risk assessment.
    """
    agent = get_account_agent()
    return await agent.analyze(account_id)

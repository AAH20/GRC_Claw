"""Agent management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from member_verification.api.dependencies import verify_api_key
from member_verification.models.schemas import AgentInfo

router = APIRouter(prefix="/agents", tags=["agents"])


def _get_agents() -> dict[str, AgentInfo]:
    """Get all available agents.

    Returns:
        Dictionary of agent name to AgentInfo.
    """
    return {
        "identity_verifier": AgentInfo(
            name="identity_verifier",
            description="Verifies member identity using multiple data points and documents",
            status="available",
            capabilities=[
                "document_analysis",
                "biometric_matching",
                "database_cross_reference",
                "sanctions_screening",
                "address_verification",
            ],
        ),
        "trust_scorer": AgentInfo(
            name="trust_scorer",
            description="Calculates trust scores based on member behavior and history",
            status="available",
            capabilities=[
                "behavior_analysis",
                "history_evaluation",
                "reputation_scoring",
                "risk_assessment",
                "trend_analysis",
            ],
        ),
        "fraud_preventor": AgentInfo(
            name="fraud_preventor",
            description="Detects and prevents fraudulent verification attempts",
            status="available",
            capabilities=[
                "pattern_recognition",
                "anomaly_detection",
                "behavioral_analysis",
                "device_fingerprinting",
                "velocity_checking",
            ],
        ),
        "document_checker": AgentInfo(
            name="document_checker",
            description="Validates and verifies identity documents for authenticity",
            status="available",
            capabilities=[
                "ocr_extraction",
                "forgery_detection",
                "watermark_verification",
                "font_analysis",
                "metadata_inspection",
                "cross_reference",
            ],
        ),
        "verification_explainer": AgentInfo(
            name="verification_explainer",
            description="Explains verification decisions in human-readable format",
            status="available",
            capabilities=[
                "decision_explanation",
                "factor_analysis",
                "recommendation_generation",
                "appeal_guidance",
                "multi_language_support",
            ],
        ),
    }


@router.get("", response_model=list[AgentInfo])
async def list_agents(
    api_key: str = Depends(verify_api_key),
) -> list[AgentInfo]:
    """List all available agents.

    Args:
        api_key: Verified API key.

    Returns:
        List of agent information.
    """
    return list(_get_agents().values())


@router.get("/{agent_name}/status", response_model=AgentInfo)
async def get_agent_status(
    agent_name: str,
    api_key: str = Depends(verify_api_key),
) -> AgentInfo:
    """Get status of a specific agent.

    Args:
        agent_name: Name of the agent.
        api_key: Verified API key.

    Returns:
        Agent information.

    Raises:
        HTTPException: If the agent is not found.
    """
    agents = _get_agents()
    agent = agents.get(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found",
        )
    return agent

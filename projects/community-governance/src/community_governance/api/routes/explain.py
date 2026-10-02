"""Explain routes for governance decisions."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from community_governance.api.dependencies import get_governance_explainer
from community_governance.agents import GovernanceExplainerAgent
from community_governance.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/explain", tags=["explain"])


@router.post("")
async def explain_decision(
    explanation_request: dict,
    agent: GovernanceExplainerAgent = Depends(get_governance_explainer),
) -> dict:
    """Explain a governance decision.

    Args:
        explanation_request: The explanation request containing:
            - explanation_type: Type of explanation (action, rule, dispute, policy)
            - target_data: Data about the entity to explain
            - audience: Target audience (member, moderator, admin)
            - detail_level: Detail level (brief, standard, detailed)
        agent: The governance explainer agent.

    Returns:
        The generated explanation.
    """
    explanation = await agent.execute(explanation_request)
    logger.info(
        "Explanation generated",
        explanation_type=explanation_request.get("explanation_type"),
    )
    return explanation

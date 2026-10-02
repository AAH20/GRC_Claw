"""Next-best-action API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from agents.base import AgentContext
from agents.next_best_action import NextBestActionAgent, NextBestActionInput
from api.models.schemas import NextBestActionRequest, NextBestActionResponse
from core.database import get_db
from core.governance import get_governance
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/leads", tags=["next-best-action"])
nba_agent = NextBestActionAgent()


@router.post("/{lead_id}/next-action", response_model=NextBestActionResponse)
async def get_next_best_action(
    lead_id: str, request: NextBestActionRequest,
    db: AsyncSession = Depends(get_db), http_request: Request = None,
) -> NextBestActionResponse:
    """Get next best action recommendation for a lead."""
    trace_id = str(uuid.uuid4())
    governance = get_governance()
    logger.info("next_action_requested", lead_id=lead_id, trace_id=trace_id)
    try:
        nba_input = NextBestActionInput(
            lead_id=lead_id, company_name=request.company_name, lead_score=request.lead_score,
            grade=request.grade, qualified=request.qualified, industry=request.industry,
            company_size=request.company_size, current_stage=request.current_stage,
            last_interaction=request.last_interaction, preferred_channel=request.preferred_channel,
            pain_points=request.pain_points, interests=request.interests,
        )
        context = AgentContext(lead_id=lead_id, tenant_id="default", trace_id=trace_id)
        result = await nba_agent.execute(nba_input, context)
        if not result.success or result.data is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.error or "Next best action failed")
        output = result.data
        governance.audit_log(action="next_best_action", lead_id=lead_id, tenant_id="default", details={"strategy": output.overall_strategy, "urgency": output.urgency})
        return NextBestActionResponse(
            lead_id=output.lead_id, actions=[a.model_dump() for a in output.actions],
            overall_strategy=output.overall_strategy, urgency=output.urgency,
            next_review_date=output.next_review_date, summary=output.summary,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("next_action_failed", lead_id=lead_id, error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Next best action failed: {exc}")

"""Insight synthesis API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from agents.base import AgentContext
from agents.insight_synthesis import InsightSynthesisAgent, InsightSynthesisInput
from api.models.schemas import InsightResponse
from core.database import get_db
from core.governance import get_governance
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/insights", tags=["insights"])
synthesis_agent = InsightSynthesisAgent()


@router.post("/{lead_id}/synthesize", response_model=InsightResponse)
async def synthesize_insights(
    lead_id: str, db: AsyncSession = Depends(get_db), http_request: Request = None,
) -> InsightResponse:
    """Synthesize insights from all agent outputs for a lead."""
    trace_id = str(uuid.uuid4())
    governance = get_governance()
    logger.info("insight_synthesis_requested", lead_id=lead_id, trace_id=trace_id)
    try:
        synthesis_input = InsightSynthesisInput(lead_id=lead_id, company_name="")
        context = AgentContext(lead_id=lead_id, tenant_id="default", trace_id=trace_id)
        result = await synthesis_agent.execute(synthesis_input, context)
        if not result.success or result.data is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.error or "Insight synthesis failed")
        output = result.data
        governance.audit_log(action="insight_synthesis", lead_id=lead_id, tenant_id="default", details={"confidence": output.confidence})
        return InsightResponse(
            lead_id=output.lead_id, overall_assessment=output.overall_assessment,
            key_insights=[i.model_dump() for i in output.key_insights],
            action_items=[a.model_dump() for a in output.action_items],
            opportunities=output.opportunities, risks=output.risks,
            recommended_approach=output.recommended_approach, confidence=output.confidence, summary=output.summary,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("insight_synthesis_failed", lead_id=lead_id, error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Insight synthesis failed: {exc}")

"""Qualification API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from agents.base import AgentContext
from agents.qualification import QualificationAgent, QualificationInput
from api.models.schemas import QualificationRequest, QualificationResponse
from core.database import get_db
from core.governance import get_governance
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/leads", tags=["qualification"])
qualification_agent = QualificationAgent()


@router.post("/{lead_id}/qualify", response_model=QualificationResponse)
async def qualify_lead(
    lead_id: str, request: QualificationRequest,
    db: AsyncSession = Depends(get_db), http_request: Request = None,
) -> QualificationResponse:
    """Run qualification assessment on a lead."""
    trace_id = str(uuid.uuid4())
    governance = get_governance()
    logger.info("qualify_lead_requested", lead_id=lead_id, framework=request.framework, trace_id=trace_id)
    try:
        qual_input = QualificationInput(
            lead_id=lead_id, company_name=request.company_name, framework=request.framework.value,
            budget=request.budget, authority=request.authority, need=request.need,
            timeline=request.timeline, metrics=request.metrics, economic_buyer=request.economic_buyer,
            decision_criteria=request.decision_criteria, decision_process=request.decision_process,
            identify_pain=request.identify_pain, champion=request.champion,
        )
        context = AgentContext(lead_id=lead_id, tenant_id="default", trace_id=trace_id)
        result = await qualification_agent.execute(qual_input, context)
        if not result.success or result.data is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.error or "Qualification failed")
        output = result.data
        governance.audit_log(action="qualify_lead", lead_id=lead_id, tenant_id="default", details={"qualified": output.qualified, "score": output.qualification_score})
        return QualificationResponse(
            lead_id=output.lead_id, framework=output.framework, qualified=output.qualified,
            qualification_score=output.qualification_score, criteria=[c.model_dump() for c in output.criteria],
            next_steps=output.next_steps, risk_factors=output.risk_factors, summary=output.summary,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("qualify_lead_failed", lead_id=lead_id, error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Qualification failed: {exc}")

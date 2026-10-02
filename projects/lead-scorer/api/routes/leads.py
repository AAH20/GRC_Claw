"""Lead scoring API routes."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from agents.scoring import ScoringAgent, ScoringInput
from api.models.schemas import (
    BatchScoreRequest, BatchScoreResponse, LeadScoreRequest,
    LeadScoreResponse, ScoreBreakdownResponse,
)
from core.database import get_db
from core.governance import get_governance
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/leads", tags=["leads"])
scoring_agent = ScoringAgent()


@router.post("/score", response_model=LeadScoreResponse)
async def score_lead(
    request: LeadScoreRequest,
    db: AsyncSession = Depends(get_db),
    http_request: Request = None,
) -> LeadScoreResponse:
    """Score a single lead."""
    trace_id = str(uuid.uuid4())
    governance = get_governance()
    logger.info("score_lead_requested", lead_id=request.lead_id, trace_id=trace_id)
    try:
        scoring_input = ScoringInput(
            lead_id=request.lead_id,
            company_name=request.company_name,
            firmographic_score=request.firmographic_score,
            technographic_score=request.technographic_score,
            intent_score=request.intent_score,
            engagement_score=request.engagement_score,
            timing_score=request.timing_score,
            evidence_confidence=request.evidence_confidence,
        )
        from agents.base import AgentContext
        context = AgentContext(lead_id=request.lead_id, tenant_id="default", trace_id=trace_id)
        result = await scoring_agent.execute(scoring_input, context)
        if not result.success or result.data is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.error or "Scoring failed")
        output = result.data
        governance.audit_log(action="score_lead", lead_id=request.lead_id, tenant_id="default", details={"score": output.total_score, "grade": output.grade})
        return LeadScoreResponse(
            lead_id=output.lead_id, total_score=output.total_score, grade=output.grade,
            breakdown=[ScoreBreakdownResponse(dimension=b.dimension, score=b.score, weight=b.weight, weighted_score=b.weighted_score, rationale=b.rationale) for b in output.breakdown],
            confidence=output.confidence, scoring_model=output.scoring_model,
            timestamp=output.timestamp or datetime.now(timezone.utc).isoformat(), rationale=output.rationale,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("score_lead_failed", lead_id=request.lead_id, error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Scoring failed: {exc}")


@router.post("/score/batch", response_model=BatchScoreResponse)
async def batch_score_leads(request: BatchScoreRequest, db: AsyncSession = Depends(get_db)) -> BatchScoreResponse:
    """Batch score multiple leads."""
    logger.info("batch_score_requested", count=len(request.leads))
    results: list[LeadScoreResponse] = []
    failed = 0
    for lead_req in request.leads:
        try:
            scoring_input = ScoringInput(
                lead_id=lead_req.lead_id, company_name=lead_req.company_name,
                firmographic_score=lead_req.firmographic_score, technographic_score=lead_req.technographic_score,
                intent_score=lead_req.intent_score, engagement_score=lead_req.engagement_score,
                timing_score=lead_req.timing_score, evidence_confidence=lead_req.evidence_confidence,
            )
            from agents.base import AgentContext
            context = AgentContext(lead_id=lead_req.lead_id, tenant_id="default", trace_id=str(uuid.uuid4()))
            result = await scoring_agent.execute(scoring_input, context)
            if result.success and result.data:
                output = result.data
                results.append(LeadScoreResponse(
                    lead_id=output.lead_id, total_score=output.total_score, grade=output.grade,
                    breakdown=[ScoreBreakdownResponse(dimension=b.dimension, score=b.score, weight=b.weight, weighted_score=b.weighted_score, rationale=b.rationale) for b in output.breakdown],
                    confidence=output.confidence, scoring_model=output.scoring_model,
                    timestamp=output.timestamp or datetime.now(timezone.utc).isoformat(), rationale=output.rationale,
                ))
            else:
                failed += 1
        except Exception as exc:
            failed += 1
            logger.error("batch_item_exception", lead_id=lead_req.lead_id, error=str(exc))
    return BatchScoreResponse(results=results, total_processed=len(results), total_failed=failed)


@router.get("/{lead_id}", response_model=LeadScoreResponse)
async def get_lead_score(lead_id: str, db: AsyncSession = Depends(get_db)) -> LeadScoreResponse:
    """Get the latest score for a lead."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Lead {lead_id} not found. Score the lead first via POST /score.")

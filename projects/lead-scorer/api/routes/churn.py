"""Churn prediction API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from agents.base import AgentContext
from agents.churn_prediction import ChurnPredictionAgent, ChurnPredictionInput
from api.models.schemas import ChurnPredictionRequest, ChurnPredictionResponse
from core.database import get_db
from core.governance import get_governance
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/customers", tags=["churn"])
churn_agent = ChurnPredictionAgent()


@router.post("/{customer_id}/churn-predict", response_model=ChurnPredictionResponse)
async def predict_churn(
    customer_id: str, request: ChurnPredictionRequest,
    db: AsyncSession = Depends(get_db), http_request: Request = None,
) -> ChurnPredictionResponse:
    """Predict churn risk for a customer."""
    trace_id = str(uuid.uuid4())
    governance = get_governance()
    logger.info("churn_predict_requested", customer_id=customer_id, trace_id=trace_id)
    try:
        churn_input = ChurnPredictionInput(
            customer_id=customer_id, company_name=request.company_name,
            tenure_months=request.tenure_months, contract_value=request.contract_value,
            usage_trend=request.usage_trend, support_tickets_90d=request.support_tickets_90d,
            nps_score=request.nps_score, engagement_score=request.engagement_score,
            last_login_days=request.last_login_days, feature_adoption_rate=request.feature_adoption_rate,
            stakeholder_changes=request.stakeholder_changes,
            contract_renewal_date=request.contract_renewal_date,
            competitor_mentions=request.competitor_mentions,
        )
        context = AgentContext(lead_id=customer_id, tenant_id="default", trace_id=trace_id)
        result = await churn_agent.execute(churn_input, context)
        if not result.success or result.data is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.error or "Churn prediction failed")
        output = result.data
        governance.audit_log(action="churn_predict", lead_id=customer_id, tenant_id="default", details={"churn_probability": output.churn_probability, "risk_level": output.risk_level})
        return ChurnPredictionResponse(
            customer_id=output.customer_id, churn_probability=output.churn_probability,
            risk_level=output.risk_level, risk_factors=[f.model_dump() for f in output.risk_factors],
            protective_factors=output.protective_factors, recommended_actions=output.recommended_actions,
            confidence=output.confidence, prediction_window_days=output.prediction_window_days, summary=output.summary,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("churn_predict_failed", customer_id=customer_id, error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Churn prediction failed: {exc}")

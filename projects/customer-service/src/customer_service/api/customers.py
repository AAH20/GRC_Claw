"""API routes for customer management."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from customer_service.agents import CustomerSuccessAgent, SentimentAnalysisAgent

logger = structlog.get_logger(__name__)

router = APIRouter()


class CustomerResponse(BaseModel):
    """Response model for customer data."""

    customer_id: str = Field(..., description="Customer identifier")
    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email")
    tier: str = Field(default="standard", description="Customer tier")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SentimentRequest(BaseModel):
    """Request model for sentiment analysis."""

    text: str = Field(..., description="Text to analyze")
    interaction_history: list[dict[str, Any]] | None = Field(
        None, description="Optional interaction history"
    )


class SentimentResponse(BaseModel):
    """Response model for sentiment analysis results."""

    overall_sentiment: str = Field(..., description="Overall sentiment")
    sentiment_score: float = Field(..., description="Sentiment score")
    satisfaction_level: str = Field(..., description="Satisfaction level")
    frustration_level: str = Field(..., description="Frustration level")
    churn_risk: str = Field(..., description="Churn risk level")


class OutreachRequest(BaseModel):
    """Request model for proactive outreach."""

    customer_data: dict[str, Any] = Field(..., description="Customer data")
    interaction_history: list[dict[str, Any]] | None = Field(
        None, description="Optional interaction history"
    )
    usage_data: dict[str, Any] | None = Field(None, description="Optional usage data")


class OutreachResponse(BaseModel):
    """Response model for outreach recommendations."""

    health_score: float = Field(..., description="Customer health score")
    churn_risk: str = Field(..., description="Churn risk level")
    recommended_actions: list[str] = Field(..., description="Recommended actions")
    outreach_message: str | None = Field(None, description="Suggested outreach message")
    engagement_level: str = Field(..., description="Engagement level")


# In-memory customer store (replace with database in production)
_customers: dict[str, dict[str, Any]] = {}


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str) -> CustomerResponse:
    """Get customer profile by ID.

    Args:
        customer_id: The customer identifier.

    Returns:
        Customer profile.

    Raises:
        HTTPException: If customer is not found.
    """
    customer = _customers.get(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found",
        )
    return CustomerResponse(**customer)


@router.post("/{customer_id}/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(customer_id: str, request: SentimentRequest) -> SentimentResponse:
    """Analyze sentiment for a customer communication.

    Args:
        customer_id: The customer identifier.
        request: Sentiment analysis request.

    Returns:
        Sentiment analysis result.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        agent = SentimentAnalysisAgent()
        result = await agent.run(
            text=request.text,
            interaction_history=request.interaction_history,
        )
        return SentimentResponse(
            overall_sentiment=result.overall_sentiment,
            sentiment_score=result.sentiment_score,
            satisfaction_level=result.satisfaction_level,
            frustration_level=result.frustration_level,
            churn_risk=result.churn_risk,
        )
    except Exception as e:
        logger.error("Sentiment analysis failed", customer_id=customer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {e}",
        ) from e


@router.post("/{customer_id}/outreach", response_model=OutreachResponse)
async def trigger_outreach(customer_id: str, request: OutreachRequest) -> OutreachResponse:
    """Trigger proactive customer success outreach.

    Args:
        customer_id: The customer identifier.
        request: Outreach request with customer data.

    Returns:
        Outreach recommendations.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        agent = CustomerSuccessAgent()
        result = await agent.run(
            customer_id=customer_id,
            customer_data=request.customer_data,
            interaction_history=request.interaction_history,
            usage_data=request.usage_data,
        )
        return OutreachResponse(
            health_score=result.health_score,
            churn_risk=result.churn_risk,
            recommended_actions=result.recommended_actions,
            outreach_message=result.outreach_message,
            engagement_level=result.engagement_level,
        )
    except Exception as e:
        logger.error("Outreach analysis failed", customer_id=customer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Outreach analysis failed: {e}",
        ) from e

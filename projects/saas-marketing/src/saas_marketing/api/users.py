"""User API endpoints."""

from __future__ import annotations

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from saas_marketing.agents.churn_prevention import (
    AccountHealth,
    ChurnPreventionAgent,
)
from saas_marketing.agents.pql_scoring import PQLScoringAgent, UserBehavior

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Initialize agents (in production, use dependency injection)
_pql_agent = PQLScoringAgent()
_churn_agent = ChurnPreventionAgent()


class UserScoreRequest(BaseModel):
    """Request model for user PQL scoring."""

    user_id: str | None = Field(default=None, description="User identifier")
    feature_usage_count: int = Field(default=0, description="Features used")
    total_sessions: int = Field(default=0, description="Total sessions")
    avg_session_duration_seconds: float = Field(default=0.0, description="Avg session duration")
    days_since_signup: int = Field(default=0, description="Days since signup")
    key_actions_completed: list[str] = Field(default_factory=list, description="Key actions")
    team_size: int = Field(default=1, description="Team size")
    billing_page_visits: int = Field(default=0, description="Billing page visits")
    integration_attempts: int = Field(default=0, description="Integration attempts")
    nps_score: int | None = Field(default=None, description="NPS score")


class UserChurnRequest(BaseModel):
    """Request model for user churn assessment."""

    account_id: str = Field(..., description="Account identifier")
    mrr: float = Field(default=0.0, description="Monthly recurring revenue")
    active_users: int = Field(default=0, description="Active users")
    total_seats: int = Field(default=0, description="Total seats")
    days_since_last_login: int = Field(default=0, description="Days since last login")
    support_tickets_30d: int = Field(default=0, description="Support tickets in 30 days")
    nps_score: int | None = Field(default=None, description="NPS score")
    feature_adoption_rate: float = Field(default=0.0, description="Feature adoption rate")
    contract_end_days: int = Field(default=0, description="Days until contract ends")
    payment_failures: int = Field(default=0, description="Payment failures")
    engagement_trend: str = Field(default="stable", description="Engagement trend")


@router.post("/{user_id}/score")
async def score_user(user_id: str, request: UserScoreRequest) -> dict:
    """Score a user's PQL status.

    Args:
        user_id: User identifier.
        request: User behavioral data.

    Returns:
        PQL scoring result.
    """
    behavior = UserBehavior(
        user_id=user_id,
        feature_usage_count=request.feature_usage_count,
        total_sessions=request.total_sessions,
        avg_session_duration_seconds=request.avg_session_duration_seconds,
        days_since_signup=request.days_since_signup,
        key_actions_completed=request.key_actions_completed,
        team_size=request.team_size,
        billing_page_visits=request.billing_page_visits,
        integration_attempts=request.integration_attempts,
        nps_score=request.nps_score,
    )

    result = await _pql_agent.score(behavior)
    return result.model_dump()


@router.get("/{user_id}/churn-risk")
async def get_churn_risk(user_id: str) -> dict:
    """Get churn risk assessment for a user/account.

    Args:
        user_id: User or account identifier.

    Returns:
        Churn risk assessment.

    Raises:
        HTTPException: If user data cannot be retrieved.
    """
    # In production, fetch actual account health data from database
    health = AccountHealth(
        account_id=user_id,
        mrr=500.0,
        active_users=5,
        total_seats=10,
        days_since_last_login=3,
        support_tickets_30d=1,
        nps_score=8,
        feature_adoption_rate=0.6,
        contract_end_days=180,
        payment_failures=0,
        engagement_trend="stable",
    )

    result = await _churn_agent.assess(health)
    return result.model_dump()


@router.get("/{user_id}/health")
async def get_user_health(user_id: str) -> dict:
    """Get overall user health score combining PQL and churn signals.

    Args:
        user_id: User identifier.

    Returns:
        Combined health assessment.
    """
    # In production, fetch real data and compute combined score
    return {
        "user_id": user_id,
        "overall_health": "good",
        "pql_score": 72.5,
        "churn_risk": "low",
        "last_active": "2024-01-15T10:30:00Z",
        "recommendations": [
            "Continue current engagement pattern",
            "Consider upsell opportunity",
        ],
    }

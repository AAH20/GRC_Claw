"""API routes for moderation analytics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from moderation_analytics.agents import (
    AnalyticsExplainerAgent,
    ModerationPredictorAgent,
    ModeratorPerformanceAgent,
    PolicyEffectivenessAgent,
    TrendAnalyzerAgent,
)
from moderation_analytics.config import Settings, get_settings
from moderation_analytics.models import (
    AnalyticsSummary,
    HealthResponse,
    ModerationAnalytics,
    ModerationPrediction,
    ModeratorPerformance,
    PolicyEffectiveness,
    Trend,
)

router = APIRouter()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "moderation_analytics_requests_total",
    "Total requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "moderation_analytics_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)


def get_trend_analyzer() -> TrendAnalyzerAgent:
    """Dependency to get TrendAnalyzerAgent instance."""
    return TrendAnalyzerAgent()


def get_moderator_performance() -> ModeratorPerformanceAgent:
    """Dependency to get ModeratorPerformanceAgent instance."""
    return ModeratorPerformanceAgent()


def get_policy_effectiveness() -> PolicyEffectivenessAgent:
    """Dependency to get PolicyEffectivenessAgent instance."""
    return PolicyEffectivenessAgent()


def get_moderation_predictor() -> ModerationPredictorAgent:
    """Dependency to get ModerationPredictorAgent instance."""
    return ModerationPredictorAgent()


def get_analytics_explainer() -> AnalyticsExplainerAgent:
    """Dependency to get AnalyticsExplainerAgent instance."""
    return AnalyticsExplainerAgent()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse: Service health status.
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        checks={"api": True, "agents": True},
    )


@router.get("/ready", tags=["health"])
async def readiness_check() -> dict[str, bool]:
    """Readiness probe for Kubernetes.

    Returns:
        dict: Readiness status.
    """
    return {"ready": True}


@router.get("/metrics", tags=["observability"])
async def metrics() -> Response:
    """Prometheus metrics endpoint.

    Returns:
        Response: Prometheus-formatted metrics.
    """
    return Response(content=generate_latest(), media_type="text/plain")


@router.post(
    "/api/v1/analytics/summary",
    response_model=AnalyticsSummary,
    tags=["analytics"],
    status_code=status.HTTP_200_OK,
)
async def get_analytics_summary(
    days: int = Query(default=30, ge=1, le=365),
    settings: Settings = Depends(get_settings),
) -> AnalyticsSummary:
    """Get complete analytics summary.

    Args:
        days: Number of days to analyze.
        settings: Application settings.

    Returns:
        AnalyticsSummary: Complete analytics summary.
    """
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    # Generate sample data for demonstration
    analytics = ModerationAnalytics(
        total_events=15000,
        total_actions=12500,
        action_breakdown={"approve": 8000, "reject": 3000, "flag": 1500},
        severity_distribution={"low": 5000, "medium": 4000, "high": 2000, "critical": 500},
        average_response_time_seconds=2.5,
        period_start=start,
        period_end=end,
    )

    return AnalyticsSummary(
        analytics=analytics,
        trends=[],
        top_moderators=[],
        policy_scores=[],
        predictions=[],
        summary_text="Analytics summary generated successfully.",
    )


@router.get("/api/v1/trends", response_model=list[Trend], tags=["trends"])
async def get_trends(
    days: int = Query(default=30, ge=1, le=365),
    agent: TrendAnalyzerAgent = Depends(get_trend_analyzer),
) -> list[Trend]:
    """Get moderation trends.

    Args:
        days: Number of days to analyze.
        agent: Trend analyzer agent.

    Returns:
        list[Trend]: Identified trends.
    """
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    # Generate sample data
    sample_data = [
        {"date": (start + timedelta(days=i)).isoformat(), "count": 100 + i * 5, "avg_severity": 2.0 + i * 0.1}
        for i in range(days)
    ]

    return await agent.run(data=sample_data, start_date=start, end_date=end)


@router.post("/api/v1/trends/analyze", response_model=list[Trend], tags=["trends"])
async def analyze_trends(
    data: list[dict[str, Any]],
    agent: TrendAnalyzerAgent = Depends(get_trend_analyzer),
) -> list[Trend]:
    """Analyze trends with AI agent.

    Args:
        data: Moderation data to analyze.
        agent: Trend analyzer agent.

    Returns:
        list[Trend]: AI-analyzed trends.
    """
    return await agent.run(data=data)


@router.get("/api/v1/moderators", response_model=list[dict[str, Any]], tags=["moderators"])
async def list_moderators() -> list[dict[str, Any]]:
    """List all moderators.

    Returns:
        list: List of moderators.
    """
    return [
        {"id": "mod_001", "name": "Alice Johnson", "active": True},
        {"id": "mod_002", "name": "Bob Smith", "active": True},
        {"id": "mod_003", "name": "Carol White", "active": False},
    ]


@router.get(
    "/api/v1/moderators/{moderator_id}/performance",
    response_model=ModeratorPerformance,
    tags=["moderators"],
)
async def get_moderator_performance(
    moderator_id: str,
    days: int = Query(default=30, ge=1, le=365),
    agent: ModeratorPerformanceAgent = Depends(get_moderator_performance),
) -> ModeratorPerformance:
    """Get performance metrics for a specific moderator.

    Args:
        moderator_id: Moderator identifier.
        days: Number of days to analyze.
        agent: Moderator performance agent.

    Returns:
        ModeratorPerformance: Moderator performance metrics.
    """
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    sample_data = [
        {
            "moderator_id": moderator_id,
            "moderator_name": f"Moderator {moderator_id}",
            "total_reviews": 500,
            "correct_decisions": 475,
            "escalations": 25,
            "avg_response_time": 1.8,
            "consistency_score": 0.92,
        }
    ]

    results = await agent.run(moderator_data=sample_data, period_start=start, period_end=end)
    return results[0]


@router.post(
    "/api/v1/moderators/evaluate",
    response_model=list[ModeratorPerformance],
    tags=["moderators"],
)
async def evaluate_moderators(
    moderator_data: list[dict[str, Any]],
    agent: ModeratorPerformanceAgent = Depends(get_moderator_performance),
) -> list[ModeratorPerformance]:
    """Evaluate moderators with AI agent.

    Args:
        moderator_data: Moderator data to evaluate.
        agent: Moderator performance agent.

    Returns:
        list[ModeratorPerformance]: Evaluation results.
    """
    return await agent.run(moderator_data=moderator_data)


@router.get("/api/v1/policies", response_model=list[dict[str, Any]], tags=["policies"])
async def list_policies() -> list[dict[str, Any]]:
    """List all moderation policies.

    Returns:
        list: List of policies.
    """
    return [
        {"id": "policy_001", "name": "Hate Speech Policy", "version": "2.1", "active": True},
        {"id": "policy_002", "name": "Spam Policy", "version": "1.5", "active": True},
        {"id": "policy_003", "name": "Harassment Policy", "version": "3.0", "active": True},
    ]


@router.get(
    "/api/v1/policies/{policy_id}/effectiveness",
    response_model=PolicyEffectiveness,
    tags=["policies"],
)
async def get_policy_effectiveness(
    policy_id: str,
    days: int = Query(default=30, ge=1, le=365),
    agent: PolicyEffectivenessAgent = Depends(get_policy_effectiveness),
) -> PolicyEffectiveness:
    """Get effectiveness metrics for a specific policy.

    Args:
        policy_id: Policy identifier.
        days: Number of days to analyze.
        agent: Policy effectiveness agent.

    Returns:
        PolicyEffectiveness: Policy effectiveness metrics.
    """
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    sample_data = [
        {
            "policy_id": policy_id,
            "policy_name": f"Policy {policy_id}",
            "policy_version": "1.0",
            "total_violations": 1000,
            "total_enforcements": 950,
            "false_positives": 50,
            "false_negatives": 30,
            "user_appeals": 100,
            "successful_appeals": 20,
        }
    ]

    results = await agent.run(policy_data=sample_data, period_start=start, period_end=end)
    return results[0]


@router.post(
    "/api/v1/policies/assess",
    response_model=list[PolicyEffectiveness],
    tags=["policies"],
)
async def assess_policies(
    policy_data: list[dict[str, Any]],
    agent: PolicyEffectivenessAgent = Depends(get_policy_effectiveness),
) -> list[PolicyEffectiveness]:
    """Assess policies with AI agent.

    Args:
        policy_data: Policy data to assess.
        agent: Policy effectiveness agent.

    Returns:
        list[PolicyEffectiveness]: Assessment results.
    """
    return await agent.run(policy_data=policy_data)


@router.post(
    "/api/v1/predictions",
    response_model=list[ModerationPrediction],
    tags=["predictions"],
)
async def generate_predictions(
    historical_data: list[dict[str, Any]],
    target_date: datetime | None = None,
    prediction_types: list[str] | None = None,
    agent: ModerationPredictorAgent = Depends(get_moderation_predictor),
) -> list[ModerationPrediction]:
    """Generate predictions with AI agent.

    Args:
        historical_data: Historical data for prediction.
        target_date: Target date for prediction.
        prediction_types: Types of predictions to generate.
        agent: Moderation predictor agent.

    Returns:
        list[ModerationPrediction]: Generated predictions.
    """
    return await agent.run(
        historical_data=historical_data,
        target_date=target_date,
        prediction_types=prediction_types,
    )


@router.post("/api/v1/explain", tags=["analytics"])
async def explain_analytics(
    analytics_data: dict[str, Any],
    audience: str = Query(default="general"),
    agent: AnalyticsExplainerAgent = Depends(get_analytics_explainer),
) -> dict[str, str]:
    """Explain analytics results with AI agent.

    Args:
        analytics_data: Analytics data to explain.
        audience: Target audience.
        agent: Analytics explainer agent.

    Returns:
        dict: Explanation result.
    """
    explanation = await agent.run(analytics_data=analytics_data, audience=audience)
    return {"explanation": explanation}

"""Forecasting API routes."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from analytics.agents.predictive_analytics import (
    ModelType,
    PredictiveAnalyticsAgent,
)

router = APIRouter()

_agent = PredictiveAnalyticsAgent()


@router.post("/revenue")
async def forecast_revenue(
    horizon_days: int = Query(default=30, ge=1, le=365),
    model_type: ModelType = ModelType.GRADIENT_BOOSTING,
) -> dict[str, Any]:
    """Generate a revenue forecast."""
    historical_data = _generate_sample_historical_data()

    try:
        result = _agent.forecast_revenue(
            historical_data=historical_data,
            horizon_days=horizon_days,
            model_type=model_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "model_type": result.model_type.value,
        "horizon_days": result.forecast_horizon_days,
        "metrics": result.metrics,
        "forecast": [
            {
                "date": p.date.isoformat(),
                "predicted_value": p.predicted_value,
                "lower_bound": p.lower_bound,
                "upper_bound": p.upper_bound,
            }
            for p in result.points
        ],
        "summary": {
            "total_predicted": sum(p.predicted_value for p in result.points),
            "average_daily": (
                sum(p.predicted_value for p in result.points) / len(result.points)
                if result.points
                else 0
            ),
        },
    }


@router.post("/churn")
async def predict_churn(
    model_type: ModelType = ModelType.GRADIENT_BOOSTING,
) -> dict[str, Any]:
    """Predict churn for users."""
    user_features = _generate_sample_user_features()

    try:
        result = _agent.predict_churn(
            user_features=user_features,
            model_type=model_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "model_metrics": result.model_metrics,
        "predictions": [
            {
                "user_id": p.user_id,
                "churn_probability": p.churn_probability,
                "risk_tier": p.risk_tier,
                "top_factors": p.top_factors,
            }
            for p in result.predictions
        ],
        "summary": {
            "total_users": len(result.predictions),
            "high_risk": sum(1 for p in result.predictions if p.risk_tier == "high"),
            "medium_risk": sum(1 for p in result.predictions if p.risk_tier == "medium"),
            "low_risk": sum(1 for p in result.predictions if p.risk_tier == "low"),
        },
    }


@router.get("/models")
async def list_forecast_models() -> dict[str, Any]:
    """List available forecasting models."""
    return {
        "models": [
            {
                "id": model.value,
                "name": model.value.replace("_", " ").title(),
                "description": _get_model_description(model),
            }
            for model in ModelType
        ],
    }


def _get_model_description(model: ModelType) -> str:
    """Get a human-readable description of a forecasting model."""
    descriptions = {
        ModelType.LINEAR_REGRESSION: "Simple linear regression for trend-based forecasting.",
        ModelType.RANDOM_FOREST: "Ensemble of decision trees for non-linear patterns.",
        ModelType.GRADIENT_BOOSTING: "Gradient-boosted trees for high-accuracy predictions.",
    }
    return descriptions.get(model, "")


def _generate_sample_historical_data() -> list[dict[str, Any]]:
    """Generate sample historical revenue data."""
    import numpy as np

    np.random.seed(42)
    data: list[dict[str, Any]] = []
    base_date = datetime.utcnow() - timedelta(days=90)

    for i in range(90):
        date = base_date + timedelta(days=i)
        trend = 1000 + i * 5
        seasonality = 200 * np.sin(2 * np.pi * i / 7)
        noise = np.random.normal(0, 100)
        revenue = max(0, trend + seasonality + noise)

        data.append(
            {
                "date": date.isoformat(),
                "revenue": float(revenue),
            }
        )

    return data


def _generate_sample_user_features() -> list[dict[str, Any]]:
    """Generate sample user features for churn prediction."""
    import numpy as np

    np.random.seed(42)
    users: list[dict[str, Any]] = []

    for i in range(20):
        users.append(
            {
                "user_id": f"user_{i}",
                "days_since_last_active": int(np.random.exponential(10)),
                "total_sessions": int(np.random.poisson(50)),
                "avg_session_duration": float(np.random.normal(300, 100)),
                "total_revenue": float(np.random.exponential(500)),
                "support_tickets": int(np.random.poisson(2)),
                "email_open_rate": float(np.random.beta(2, 5)),
            }
        )

    return users

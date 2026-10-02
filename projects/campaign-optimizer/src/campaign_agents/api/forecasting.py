"""Forecasting API routes — Time-series forecasting endpoints."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from campaign_agents.agents.forecaster import TimeSeriesForecaster
from campaign_agents.models.optimization import (
    ForecastConfig,
    ForecastGranularity,
    ForecastMethod,
    TimeSeriesPoint,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


# ─── Request/Response Models ────────────────────────────────────────


class DataPointRequest(BaseModel):
    """Request model for a single data point."""

    timestamp: str
    value: float = Field(..., ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ForecastRequest(BaseModel):
    """Request model for generating a forecast."""

    campaign_id: str = Field(..., min_length=1)
    metric: str = Field(default="conversions")
    method: ForecastMethod = Field(default=ForecastMethod.EXPONENTIAL_SMOOTHING)
    granularity: ForecastGranularity = Field(default=ForecastGranularity.DAILY)
    horizon: int = Field(default=7, ge=1, le=365)
    seasonality_period: int | None = Field(default=None, ge=1)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.99)
    smoothing_alpha: float = Field(default=0.3, ge=0.0, le=1.0)
    smoothing_beta: float = Field(default=0.1, ge=0.0, le=1.0)
    data_points: list[DataPointRequest] = Field(..., min_length=3)


class ForecastResponse(BaseModel):
    """Response model for forecast results."""

    campaign_id: str
    metric: str
    method: str
    granularity: str
    historical_points: int
    forecast_points: list[dict[str, Any]]
    mape: float | None = None
    rmse: float | None = None
    trend_direction: str
    seasonality_detected: bool
    timestamp: str


class BulkDataRequest(BaseModel):
    """Request model for bulk data ingestion."""

    campaign_id: str = Field(..., min_length=1)
    data_points: list[DataPointRequest] = Field(..., min_length=1)


# ─── In-Memory Store ────────────────────────────────────────────────

_forecasters: dict[str, TimeSeriesForecaster] = {}


# ─── Routes ─────────────────────────────────────────────────────────


@router.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(request: ForecastRequest) -> ForecastResponse:
    """Generate a time-series forecast for campaign metrics.

    Args:
        request: Forecast configuration and historical data.

    Returns:
        ForecastResponse with predicted values.

    Raises:
        HTTPException: If forecasting fails.
    """
    try:
        config = ForecastConfig(
            method=request.method,
            granularity=request.granularity,
            horizon=request.horizon,
            seasonality_period=request.seasonality_period,
            confidence_level=request.confidence_level,
            smoothing_alpha=request.smoothing_alpha,
            smoothing_beta=request.smoothing_beta,
        )

        forecaster = TimeSeriesForecaster(config)

        for dp in request.data_points:
            forecaster.add_data_point(
                TimeSeriesPoint(
                    timestamp=dp.timestamp,
                    value=dp.value,
                    metadata=dp.metadata,
                )
            )

        result = forecaster.forecast(request.campaign_id, request.metric)
        _forecasters[request.campaign_id] = forecaster

        return ForecastResponse(
            campaign_id=result.campaign_id,
            metric=result.metric,
            method=result.method.value,
            granularity=result.granularity.value,
            historical_points=result.historical_points,
            forecast_points=[fp.model_dump() for fp in result.forecast_points],
            mape=result.mape,
            rmse=result.rmse,
            trend_direction=result.trend_direction,
            seasonality_detected=result.seasonality_detected,
            timestamp=result.timestamp,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Forecast generation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast generation failed: {str(e)}",
        ) from e


@router.post("/forecast/{campaign_id}/data")
async def add_forecast_data(
    campaign_id: str, request: BulkDataRequest
) -> dict[str, Any]:
    """Add historical data points to an existing forecaster.

    Args:
        campaign_id: The campaign identifier.
        request: Bulk data points to add.

    Returns:
        Confirmation with updated data count.

    Raises:
        HTTPException: If forecaster not found.
    """
    forecaster = _forecasters.get(campaign_id)
    if not forecaster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No forecaster found for campaign {campaign_id}",
        )

    for dp in request.data_points:
        forecaster.add_data_point(
            TimeSeriesPoint(
                timestamp=dp.timestamp,
                value=dp.value,
                metadata=dp.metadata,
            )
        )

    return {
        "status": "data_added",
        "campaign_id": campaign_id,
        "total_points": len(forecaster.get_historical_data()),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/forecast/{campaign_id}/history")
async def get_forecast_history(campaign_id: str) -> dict[str, Any]:
    """Get forecast history for a campaign.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        List of previous forecasts.

    Raises:
        HTTPException: If forecaster not found.
    """
    forecaster = _forecasters.get(campaign_id)
    if not forecaster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No forecaster found for campaign {campaign_id}",
        )

    history = forecaster.get_forecast_history()
    return {
        "campaign_id": campaign_id,
        "forecast_count": len(history),
        "forecasts": [h.model_dump() for h in history],
    }


@router.delete("/forecast/{campaign_id}/data")
async def clear_forecast_data(campaign_id: str) -> dict[str, str]:
    """Clear all historical data for a forecaster.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Confirmation of data clearance.

    Raises:
        HTTPException: If forecaster not found.
    """
    forecaster = _forecasters.get(campaign_id)
    if not forecaster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No forecaster found for campaign {campaign_id}",
        )

    forecaster.clear_data()
    return {"status": "cleared", "campaign_id": campaign_id}

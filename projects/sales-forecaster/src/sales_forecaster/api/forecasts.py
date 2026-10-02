"""Forecast API routes."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from sales_forecaster.agents.analysis import AnalysisAgent
from sales_forecaster.agents.data_collection import DataCollectionAgent
from sales_forecaster.agents.prediction import PredictionAgent
from sales_forecaster.core.exceptions import (
    AnalysisError,
    DataCollectionError,
    PredictionError,
)
from sales_forecaster.core.models import (
    ApiResponse,
    DataSource,
    ForecastPeriod,
    ForecastResult,
    SalesRecord,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/forecasts", tags=["forecasts"])

# In-memory store for demo purposes - use database in production
_forecast_store: dict[str, ForecastResult] = {}


def get_data_collection_agent() -> DataCollectionAgent:
    """Dependency to get data collection agent."""
    return DataCollectionAgent()


def get_analysis_agent() -> AnalysisAgent:
    """Dependency to get analysis agent."""
    return AnalysisAgent()


def get_prediction_agent() -> PredictionAgent:
    """Dependency to get prediction agent."""
    return PredictionAgent()


@router.post("", response_model=ApiResponse[ForecastResult], status_code=status.HTTP_201_CREATED)
async def create_forecast(
    sources: list[DataSource] | None = None,
    period: ForecastPeriod = ForecastPeriod.MONTHLY,
    horizon_days: int = Query(default=90, ge=1, le=365),
    data_agent: DataCollectionAgent = Depends(get_data_collection_agent),  # noqa: B008
    analysis_agent: AnalysisAgent = Depends(get_analysis_agent),  # noqa: B008
    prediction_agent: PredictionAgent = Depends(get_prediction_agent),  # noqa: B008
) -> ApiResponse[ForecastResult]:
    """Generate a new sales forecast.

    Collects data from configured sources, analyzes trends, and generates
    a forecast with confidence intervals.

    Args:
        sources: Data sources to use. Defaults to all configured sources.
        period: Forecast period granularity.
        horizon_days: Number of days to forecast (1-365).
        data_agent: Data collection agent dependency.
        analysis_agent: Analysis agent dependency.
        prediction_agent: Prediction agent dependency.

    Returns:
        API response with the generated forecast.

    Raises:
        HTTPException: If forecast generation fails.
    """
    request_id = str(uuid.uuid4())
    logger.info(
        "Forecast request received",
        request_id=request_id,
        period=period.value,
        horizon_days=horizon_days,
    )

    try:
        records: list[SalesRecord] = await data_agent.collect_all(sources=sources)

        if not records:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No data available from configured sources",
            )

        analysis = await analysis_agent.analyze(records, period=period.value)
        forecast = await prediction_agent.predict(records, analysis, period)

        _forecast_store[forecast.id] = forecast

        logger.info(
            "Forecast generated successfully",
            request_id=request_id,
            forecast_id=forecast.id,
        )

        return ApiResponse(success=True, data=forecast, request_id=request_id)

    except DataCollectionError as exc:
        logger.error("Data collection failed", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data collection failed: {exc}",
        ) from exc
    except AnalysisError as exc:
        logger.error("Analysis failed", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {exc}",
        ) from exc
    except PredictionError as exc:
        logger.error("Prediction failed", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        ) from exc


@router.get("/{forecast_id}", response_model=ApiResponse[ForecastResult])
async def get_forecast(forecast_id: str) -> ApiResponse[ForecastResult]:
    """Get a forecast by ID.

    Args:
        forecast_id: The forecast ID.

    Returns:
        API response with the forecast.

    Raises:
        HTTPException: If forecast is not found.
    """
    forecast = _forecast_store.get(forecast_id)
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast {forecast_id} not found",
        )
    return ApiResponse(success=True, data=forecast)


@router.get("", response_model=ApiResponse[list[ForecastResult]])
async def list_forecasts(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ApiResponse[list[ForecastResult]]:
    """List all forecasts.

    Args:
        limit: Maximum number of results.
        offset: Number of results to skip.

    Returns:
        API response with list of forecasts.
    """
    forecasts = list(_forecast_store.values())
    forecasts.sort(key=lambda f: f.created_at, reverse=True)
    return ApiResponse(success=True, data=forecasts[offset : offset + limit])


@router.delete("/{forecast_id}", response_model=ApiResponse[dict[str, str]])
async def delete_forecast(forecast_id: str) -> ApiResponse[dict[str, str]]:
    """Delete a forecast by ID.

    Args:
        forecast_id: The forecast ID.

    Returns:
        API response confirming deletion.

    Raises:
        HTTPException: If forecast is not found.
    """
    if forecast_id not in _forecast_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast {forecast_id} not found",
        )
    del _forecast_store[forecast_id]
    return ApiResponse(success=True, data={"deleted": forecast_id})

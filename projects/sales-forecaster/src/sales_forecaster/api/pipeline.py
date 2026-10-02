"""Pipeline API routes."""

from __future__ import annotations

import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from sales_forecaster.agents.action import ActionAgent
from sales_forecaster.agents.analysis import AnalysisAgent
from sales_forecaster.agents.data_collection import DataCollectionAgent
from sales_forecaster.agents.performance_analytics import PerformanceAnalyticsAgent
from sales_forecaster.agents.prediction import PredictionAgent
from sales_forecaster.core.exceptions import PipelineError
from sales_forecaster.core.metrics import record_pipeline_complete, record_pipeline_start
from sales_forecaster.core.models import (
    ActionRecommendation,
    AnalysisResult,
    ApiResponse,
    DataSource,
    ForecastPeriod,
    ForecastResult,
    PerformanceMetrics,
    PipelineRun,
    PipelineStage,
    PipelineStatus,
    SalesRecord,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

# In-memory store for demo purposes
_pipeline_store: dict[str, PipelineRun] = {}


def get_data_collection_agent() -> DataCollectionAgent:
    """Dependency to get data collection agent."""
    return DataCollectionAgent()


def get_analysis_agent() -> AnalysisAgent:
    """Dependency to get analysis agent."""
    return AnalysisAgent()


def get_prediction_agent() -> PredictionAgent:
    """Dependency to get prediction agent."""
    return PredictionAgent()


def get_action_agent() -> ActionAgent:
    """Dependency to get action agent."""
    return ActionAgent()


def get_performance_agent() -> PerformanceAnalyticsAgent:
    """Dependency to get performance analytics agent."""
    return PerformanceAnalyticsAgent()


async def _run_pipeline(
    run_id: str,
    sources: list[DataSource] | None,
    period: ForecastPeriod,
    data_agent: DataCollectionAgent,
    analysis_agent: AnalysisAgent,
    prediction_agent: PredictionAgent,
    action_agent: ActionAgent,
    performance_agent: PerformanceAnalyticsAgent,
) -> None:
    """Execute the full pipeline asynchronously.

    Args:
        run_id: Pipeline run ID.
        sources: Data sources to use.
        period: Forecast period.
        data_agent: Data collection agent.
        analysis_agent: Analysis agent.
        prediction_agent: Prediction agent.
        action_agent: Action agent.
        performance_agent: Performance analytics agent.
    """
    record_pipeline_start()
    run = _pipeline_store.get(run_id)
    if not run:
        return

    run.status = PipelineStatus.RUNNING
    run.started_at = datetime.now()

    try:
        # Stage 1: Data Collection
        logger.info("Pipeline stage: data_collection", run_id=run_id)
        run.stages[PipelineStage.DATA_COLLECTION] = {"status": "running"}
        records: list[SalesRecord] = await data_agent.collect_all(sources=sources)
        run.stages[PipelineStage.DATA_COLLECTION] = {
            "status": "completed",
            "record_count": len(records),
        }

        if not records:
            raise PipelineError("No data collected from any source")

        # Stage 2: Analysis
        logger.info("Pipeline stage: analysis", run_id=run_id)
        run.stages[PipelineStage.ANALYSIS] = {"status": "running"}
        analysis: AnalysisResult = await analysis_agent.analyze(records, period=period.value)
        run.stages[PipelineStage.ANALYSIS] = {
            "status": "completed",
            "trend": analysis.trend,
            "seasonality_detected": analysis.seasonality_detected,
        }

        # Stage 3: Prediction
        logger.info("Pipeline stage: prediction", run_id=run_id)
        run.stages[PipelineStage.PREDICTION] = {"status": "running"}
        forecast: ForecastResult = await prediction_agent.predict(records, analysis, period)
        run.stages[PipelineStage.PREDICTION] = {
            "status": "completed",
            "forecast_id": forecast.id,
            "model_used": forecast.model_used,
        }

        # Stage 4: Action
        logger.info("Pipeline stage: action", run_id=run_id)
        run.stages[PipelineStage.ACTION] = {"status": "running"}
        recommendations: list[ActionRecommendation] = (
            await action_agent.generate_recommendations(forecast, analysis)
        )
        run.stages[PipelineStage.ACTION] = {
            "status": "completed",
            "recommendation_count": len(recommendations),
        }

        # Stage 5: Performance Analytics
        logger.info("Pipeline stage: performance_analytics", run_id=run_id)
        run.stages[PipelineStage.PERFORMANCE_ANALYTICS] = {"status": "running"}
        metrics: PerformanceMetrics = await performance_agent.evaluate(records, forecast)
        run.stages[PipelineStage.PERFORMANCE_ANALYTICS] = {
            "status": "completed",
            "forecast_accuracy": metrics.forecast_accuracy,
            "alert_count": len(metrics.alerts),
        }

        run.status = PipelineStatus.COMPLETED
        run.completed_at = datetime.now()
        run.metadata = {
            "forecast_id": forecast.id,
            "recommendation_count": len(recommendations),
            "total_revenue": metrics.total_revenue,
        }

        record_pipeline_complete(success=True)
        logger.info("Pipeline completed successfully", run_id=run_id)

    except Exception as exc:
        run.status = PipelineStatus.FAILED
        run.completed_at = datetime.now()
        run.error = str(exc)
        record_pipeline_complete(success=False)
        logger.error("Pipeline failed", run_id=run_id, error=str(exc), exc_info=True)


@router.post("/run", response_model=ApiResponse[PipelineRun], status_code=status.HTTP_202_ACCEPTED)
async def run_pipeline(
    background_tasks: BackgroundTasks,
    sources: list[DataSource] | None = None,
    period: ForecastPeriod = ForecastPeriod.MONTHLY,
    data_agent: DataCollectionAgent = Depends(get_data_collection_agent),  # noqa: B008
    analysis_agent: AnalysisAgent = Depends(get_analysis_agent),  # noqa: B008
    prediction_agent: PredictionAgent = Depends(get_prediction_agent),  # noqa: B008
    action_agent: ActionAgent = Depends(get_action_agent),  # noqa: B008
    performance_agent: PerformanceAnalyticsAgent = Depends(get_performance_agent),  # noqa: B008
) -> ApiResponse[PipelineRun]:
    """Start a full pipeline run in the background.

    Args:
        background_tasks: FastAPI background tasks.
        sources: Data sources to use.
        period: Forecast period.
        data_agent: Data collection agent.
        analysis_agent: Analysis agent.
        prediction_agent: Prediction agent.
        action_agent: Action agent.
        performance_agent: Performance analytics agent.

    Returns:
        API response with the pipeline run info.
    """
    run_id = str(uuid.uuid4())
    run = PipelineRun(
        id=run_id,
        status=PipelineStatus.PENDING,
        started_at=datetime.now(),
    )
    _pipeline_store[run_id] = run

    background_tasks.add_task(
        _run_pipeline,
        run_id,
        sources,
        period,
        data_agent,
        analysis_agent,
        prediction_agent,
        action_agent,
        performance_agent,
    )

    logger.info("Pipeline run started", run_id=run_id)
    return ApiResponse(success=True, data=run, request_id=run_id)


@router.get("/status/{run_id}", response_model=ApiResponse[PipelineRun])
async def get_pipeline_status(run_id: str) -> ApiResponse[PipelineRun]:
    """Get the status of a pipeline run.

    Args:
        run_id: The pipeline run ID.

    Returns:
        API response with the pipeline run status.

    Raises:
        HTTPException: If pipeline run is not found.
    """
    run = _pipeline_store.get(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run {run_id} not found",
        )
    return ApiResponse(success=True, data=run)


@router.get("", response_model=ApiResponse[list[PipelineRun]])
async def list_pipeline_runs(
    limit: int = 10,
    offset: int = 0,
) -> ApiResponse[list[PipelineRun]]:
    """List pipeline runs.

    Args:
        limit: Maximum number of results.
        offset: Number of results to skip.

    Returns:
        API response with list of pipeline runs.
    """
    runs = list(_pipeline_store.values())
    runs.sort(key=lambda r: r.started_at, reverse=True)
    return ApiResponse(success=True, data=runs[offset : offset + limit])

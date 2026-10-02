"""API routes for the Sales Forecaster."""

from sales_forecaster.api.forecasts import router as forecasts_router
from sales_forecaster.api.pipeline import router as pipeline_router

__all__ = ["forecasts_router", "pipeline_router"]

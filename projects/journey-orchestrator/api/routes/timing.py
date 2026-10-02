"""Timing optimization API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from api.models import OptimizeTimingRequest, OptimizeTimingResponse
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/optimize-timing", response_model=OptimizeTimingResponse)
async def optimize_timing(request: OptimizeTimingRequest) -> OptimizeTimingResponse:
    """Get optimal send times for a customer.

    Args:
        request: The timing optimization request.

    Returns:
        Timing recommendations per channel.
    """
    try:
        # In production, this would call the TimingOptimizerAgent
        logger.info(
            "timing_optimization_requested",
            customer_id=request.customer_id,
            channels=[c.value for c in request.channels],
        )

        channel_timings = []
        for channel in request.channels:
            channel_timings.append(
                {
                    "channel": channel.value,
                    "optimal_send_time": "10:00",
                    "optimal_day": "Tuesday",
                    "frequency_cap": 3,
                    "min_interval_hours": 24,
                    "expected_open_rate": 0.25,
                    "expected_conversion_rate": 0.05,
                }
            )

        return OptimizeTimingResponse(
            customer_id=request.customer_id,
            timezone=request.timezone or "UTC",
            channel_timings=channel_timings,
            best_overall_time="10:00",
            global_frequency_cap=5,
        )

    except Exception as e:
        logger.error("timing_optimization_failed", customer_id=request.customer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Timing optimization failed: {e}",
        ) from e

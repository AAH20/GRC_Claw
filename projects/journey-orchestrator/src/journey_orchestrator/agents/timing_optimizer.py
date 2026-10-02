"""Timing Optimizer agent - determines optimal send times and cadence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class TimingRequest(BaseModel):
    """Request for timing optimization."""

    customer_id: str
    channel: str
    customer_timezone: str = "UTC"
    historical_engagement: list[dict[str, Any]] = Field(default_factory=list)
    preferred_window_start: int = 9  # Hour of day (0-23)
    preferred_window_end: int = 17  # Hour of day (0-23)


class OptimalTiming(BaseModel):
    """Output of the Timing Optimizer."""

    optimal_send_time: datetime
    timezone: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""


class TimingOptimizer:
    """Agent that determines the optimal time to send messages to customers.

    Analyzes historical engagement data, timezone, and customer preferences
    to maximize open rates and engagement.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the Timing Optimizer.

        Args:
            llm_client: Optional LLM client for AI-powered optimization.
        """
        self.llm_client = llm_client
        self.logger = logger.bind(agent="timing_optimizer")

    async def optimize(self, request: TimingRequest) -> OptimalTiming:
        """Determine the optimal send time for a customer.

        Args:
            request: The timing optimization request.

        Returns:
            The optimal send time with confidence score.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.customer_id:
            raise ValueError("customer_id must not be empty")
        if not request.channel.strip():
            raise ValueError("channel must not be empty")
        if request.preferred_window_start < 0 or request.preferred_window_start > 23:
            raise ValueError("preferred_window_start must be between 0 and 23")
        if request.preferred_window_end < 0 or request.preferred_window_end > 23:
            raise ValueError("preferred_window_end must be between 0 and 23")

        self.logger.info(
            "Optimizing timing",
            customer_id=request.customer_id,
            channel=request.channel,
        )

        # Simple heuristic: next preferred window start
        now = datetime.now(UTC)
        optimal_time = now + timedelta(hours=1)
        optimal_time = optimal_time.replace(
            hour=request.preferred_window_start,
            minute=0,
            second=0,
            microsecond=0,
        )
        if optimal_time <= now:
            optimal_time += timedelta(days=1)

        result = OptimalTiming(
            optimal_send_time=optimal_time,
            timezone=request.customer_timezone,
            confidence_score=0.75,
            reasoning=(
                f"Based on preferred window "
                f"{request.preferred_window_start}:00-"
                f"{request.preferred_window_end}:00 "
                f"{request.customer_timezone}"
            ),
        )

        self.logger.info(
            "Timing optimized",
            customer_id=request.customer_id,
            optimal_time=optimal_time.isoformat(),
        )
        return result

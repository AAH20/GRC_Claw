"""Cross-Channel Coordinator agent - orchestrates execution across channels."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ChannelExecutionRequest(BaseModel):
    """Request for cross-channel execution."""

    journey_id: str
    customer_id: str
    steps: list[dict[str, Any]]
    channel_preferences: dict[str, bool] = Field(default_factory=dict)
    fallback_order: list[str] = Field(default=["email", "push", "sms", "in_app"])


class ChannelExecutionResult(BaseModel):
    """Result of a single channel execution."""

    channel: str
    success: bool
    message_id: str = ""
    error: str = ""
    timestamp: str = ""


class CrossChannelResult(BaseModel):
    """Output of the Cross-Channel Coordinator."""

    journey_id: str
    customer_id: str
    results: list[ChannelExecutionResult]
    overall_success: bool
    completed_channels: list[str] = Field(default_factory=list)
    failed_channels: list[str] = Field(default_factory=list)


class CrossChannelCoordinator:
    """Agent that orchestrates journey execution across multiple channels.

    Manages channel selection, fallback logic, and execution tracking
    to ensure customers receive messages through their preferred channels.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the Cross-Channel Coordinator.

        Args:
            llm_client: Optional LLM client for AI-powered coordination.
        """
        self.llm_client = llm_client
        self.logger = logger.bind(agent="cross_channel_coordinator")

    async def execute(self, request: ChannelExecutionRequest) -> CrossChannelResult:
        """Execute a journey across channels for a customer.

        Args:
            request: The cross-channel execution request.

        Returns:
            The execution result with per-channel status.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.journey_id.strip():
            raise ValueError("journey_id must not be empty")
        if not request.customer_id.strip():
            raise ValueError("customer_id must not be empty")

        self.logger.info(
            "Executing cross-channel journey",
            journey_id=request.journey_id,
            customer_id=request.customer_id,
        )

        results: list[ChannelExecutionResult] = []
        completed: list[str] = []
        failed: list[str] = []

        for step in request.steps:
            channel = step.get("channel", "")
            if not channel:
                continue

            # Check if channel is preferred
            if request.channel_preferences and not request.channel_preferences.get(channel, True):
                self.logger.debug("Skipping non-preferred channel", channel=channel)
                continue

            # Simulate execution
            result = ChannelExecutionResult(
                channel=channel,
                success=True,
                message_id=f"msg_{request.journey_id}_{channel}",
                timestamp="2024-01-01T00:00:00Z",
            )
            results.append(result)
            completed.append(channel)

        overall_success = len(completed) > 0

        result = CrossChannelResult(
            journey_id=request.journey_id,
            customer_id=request.customer_id,
            results=results,
            overall_success=overall_success,
            completed_channels=completed,
            failed_channels=failed,
        )

        self.logger.info(
            "Cross-channel execution complete",
            journey_id=request.journey_id,
            completed=len(completed),
            failed=len(failed),
        )
        return result

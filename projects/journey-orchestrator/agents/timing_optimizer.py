"""Timing Optimizer Agent — determines optimal send times and cadence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentResult, BaseAgent
from core.logging import get_logger

logger = get_logger(__name__)


class ChannelTiming(BaseModel):
    """Optimal timing for a specific channel."""

    channel: str = Field(..., description="Channel name")
    optimal_send_time: str = Field(..., description="Optimal time to send (HH:MM in customer timezone)")
    optimal_day: str = Field(..., description="Optimal day of week")
    frequency_cap: int = Field(..., description="Max messages per week for this channel")
    min_interval_hours: float = Field(..., description="Minimum hours between messages on this channel")
    expected_open_rate: float = Field(default=0.0, description="Expected engagement rate")
    expected_conversion_rate: float = Field(default=0.0, description="Expected conversion rate")


class TimingRecommendation(BaseModel):
    """Complete timing optimization output."""

    customer_id: str = Field(..., description="Customer identifier")
    timezone: str = Field(..., description="Customer timezone")
    channel_timings: list[ChannelTiming] = Field(..., description="Per-channel timing recommendations")
    global_frequency_cap: int = Field(default=5, description="Max total messages across all channels per week")
    quiet_hours_start: str = Field(default="22:00", description="Start of quiet hours")
    quiet_hours_end: str = Field(default="08:00", description="End of quiet hours")
    best_overall_time: str = Field(default="", description="Best overall time to reach this customer")
    reasoning: str = Field(default="", description="Explanation of timing decisions")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TimingOptimizerAgent(BaseAgent[TimingRecommendation]):
    """Agent that determines optimal send times, frequency caps, and cadence.

    Analyzes customer behavioral patterns, engagement history, and preferences
    to recommend the best times and frequencies for each channel.
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        """Initialize the Timing Optimizer agent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
        """
        if config is None:
            config = AgentConfig(
                name="timing_optimizer",
                temperature=0.3,
                system_prompt=(
                    "You are an expert timing optimizer. You analyze customer behavior "
                    "patterns and engagement data to determine the optimal times, "
                    "frequencies, and cadence for marketing communications across "
                    "all channels. You respect quiet hours and avoid over-messaging."
                ),
            )
        super().__init__(config)
        self._parser = PydanticOutputParser(pydantic_object=TimingRecommendation)

    async def run(self, input_data: dict[str, Any]) -> AgentResult[TimingRecommendation]:
        """Optimize timing for a customer's communications.

        Args:
            input_data: Must contain:
                - customer_id: Unique customer identifier
                - Optional: engagement_history, timezone, channel_preferences,
                          behavioral_patterns, quiet_hours

        Returns:
            AgentResult containing the TimingRecommendation or an error.
        """
        try:
            messages = self._build_messages(input_data)
            messages.append(
                HumanMessage(
                    content=f"\n\n{self._parser.get_format_instructions()}"
                )
            )

            response = await self.llm.ainvoke(messages)
            result = self._parser.parse(response.content)

            logger.info(
                "timing_optimized",
                customer_id=result.customer_id,
                num_channels=len(result.channel_timings),
                best_time=result.best_overall_time,
            )

            return AgentResult(
                success=True,
                data=result,
                agent_name=self.config.name,
                tokens_used=response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0,
            )

        except Exception as e:
            logger.error("timing_optimization_failed", error=str(e))
            return AgentResult(
                success=False,
                error=f"Failed to optimize timing: {e}",
                agent_name=self.config.name,
            )

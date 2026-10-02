"""Journey Designer Agent — designs end-to-end customer journey maps."""

from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentResult, BaseAgent
from core.exceptions import AgentError
from core.logging import get_logger

logger = get_logger(__name__)


class JourneyStage(BaseModel):
    """A single stage in a customer journey."""

    name: str = Field(..., description="Stage name (e.g., 'awareness', 'consideration', 'conversion')")
    description: str = Field(..., description="What happens in this stage")
    entry_conditions: list[str] = Field(default_factory=list, description="Conditions to enter this stage")
    exit_conditions: list[str] = Field(default_factory=list, description="Conditions to exit this stage")
    actions: list[str] = Field(default_factory=list, description="Actions to take in this stage")
    channels: list[str] = Field(default_factory=list, description="Channels to use (email, sms, push, etc.)")
    next_stages: list[str] = Field(default_factory=list, description="Possible next stage names")
    estimated_duration_hours: float = Field(default=24.0, description="Estimated time in this stage")


class JourneyDesign(BaseModel):
    """A complete customer journey design."""

    name: str = Field(..., description="Journey name")
    description: str = Field(..., description="Journey description")
    target_audience: str = Field(..., description="Target audience segment")
    business_goal: str = Field(..., description="Primary business goal")
    stages: list[JourneyStage] = Field(..., description="Ordered list of journey stages")
    success_metrics: list[str] = Field(default_factory=list, description="KPIs to track")
    estimated_total_duration_hours: float = Field(default=0.0, description="Total estimated duration")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class JourneyDesignerAgent(BaseAgent[JourneyDesign]):
    """Agent that designs customer journey maps from business goals and audience segments.

    This agent takes high-level business objectives and audience information,
    then produces a structured journey design with stages, transitions,
    actions, and success metrics.
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        """Initialize the Journey Designer agent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
        """
        if config is None:
            config = AgentConfig(
                name="journey_designer",
                system_prompt=(
                    "You are an expert customer journey designer. You create detailed, "
                    "actionable journey maps that guide customers from awareness to "
                    "conversion. Each stage should have clear entry/exit conditions, "
                    "specific actions, and appropriate channel selections."
                ),
            )
        super().__init__(config)
        self._parser = PydanticOutputParser(pydantic_object=JourneyDesign)

    async def run(self, input_data: dict[str, Any]) -> AgentResult[JourneyDesign]:
        """Design a customer journey from the given input.

        Args:
            input_data: Must contain:
                - business_goal: The primary business objective
                - target_audience: Description of the target audience
                - Optional: constraints, existing_journeys, brand_voice

        Returns:
            AgentResult containing the JourneyDesign or an error.
        """
        try:
            messages = self._build_messages(input_data)
            messages.append(
                HumanMessage(
                    content=f"\n\n{self._parser.get_format_instructions()}"
                )
            )

            response = await self.llm.ainvoke(messages)
            journey_design = self._parser.parse(response.content)

            # Calculate total duration
            journey_design.estimated_total_duration_hours = sum(
                stage.estimated_duration_hours for stage in journey_design.stages
            )

            logger.info(
                "journey_designed",
                journey_name=journey_design.name,
                num_stages=len(journey_design.stages),
                total_duration=journey_design.estimated_total_duration_hours,
            )

            return AgentResult(
                success=True,
                data=journey_design,
                agent_name=self.config.name,
                tokens_used=response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0,
            )

        except Exception as e:
            logger.error("journey_design_failed", error=str(e))
            return AgentResult(
                success=False,
                error=f"Failed to design journey: {e}",
                agent_name=self.config.name,
            )

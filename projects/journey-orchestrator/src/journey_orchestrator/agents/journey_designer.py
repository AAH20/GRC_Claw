"""Journey Designer agent - creates journey blueprints from business goals."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class JourneyDesignRequest(BaseModel):
    """Request model for journey design."""

    business_goal: str = Field(..., description="The business objective for this journey")
    target_audience: str = Field(..., description="Description of the target audience")
    channels: list[str] = Field(default=["email"], description="Channels to use")
    constraints: dict[str, Any] = Field(default_factory=dict, description="Design constraints")


class JourneyStep(BaseModel):
    """A single step in a journey."""

    step_number: int
    channel: str
    action: str
    delay_hours: float = 0.0
    content_template: str = ""
    exit_conditions: list[str] = Field(default_factory=list)


class JourneyBlueprint(BaseModel):
    """Output of the Journey Designer agent."""

    name: str
    description: str
    steps: list[JourneyStep]
    success_metrics: list[str] = Field(default_factory=list)
    estimated_duration_days: int = 7


class JourneyDesigner:
    """Agent responsible for designing customer journey blueprints.

    Takes business goals and audience definitions, then produces a structured
    journey blueprint with steps, channels, timing, and success metrics.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the Journey Designer.

        Args:
            llm_client: Optional LLM client for AI-powered design.
        """
        self.llm_client = llm_client
        self.logger = logger.bind(agent="journey_designer")

    async def design(self, request: JourneyDesignRequest) -> JourneyBlueprint:
        """Design a journey blueprint from the given request.

        Args:
            request: The journey design request with business goals and audience.

        Returns:
            A complete journey blueprint.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.business_goal.strip():
            raise ValueError("business_goal must not be empty")
        if not request.target_audience.strip():
            raise ValueError("target_audience must not be empty")

        self.logger.info(
            "Designing journey",
            goal=request.business_goal,
            audience=request.target_audience,
            channels=request.channels,
        )

        # In production, this would use the LLM to generate the blueprint
        blueprint = JourneyBlueprint(
            name=f"{request.business_goal} Journey",
            description=f"Journey to {request.business_goal} for {request.target_audience}",
            steps=[
                JourneyStep(
                    step_number=1,
                    channel=request.channels[0],
                    action="send_welcome",
                    delay_hours=0,
                    content_template="Welcome! We're excited to have you.",
                ),
                JourneyStep(
                    step_number=2,
                    channel=request.channels[0],
                    action="send_educational_content",
                    delay_hours=24,
                    content_template="Here's something useful for you...",
                ),
                JourneyStep(
                    step_number=3,
                    channel=(
                        request.channels[0]
                        if len(request.channels) == 1
                        else request.channels[1]
                    ),
                    action="send_offer",
                    delay_hours=72,
                    content_template="Special offer just for you!",
                    exit_conditions=["converted", "unsubscribed"],
                ),
            ],
            success_metrics=["conversion_rate", "engagement_rate", "revenue_per_customer"],
            estimated_duration_days=7,
        )

        self.logger.info("Journey designed", steps=len(blueprint.steps))
        return blueprint

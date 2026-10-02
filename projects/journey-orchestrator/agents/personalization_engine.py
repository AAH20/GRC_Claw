"""Personalization Engine Agent — generates personalized content and offers."""

from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentResult, BaseAgent
from core.logging import get_logger

logger = get_logger(__name__)


class PersonalizedContent(BaseModel):
    """A piece of personalized content."""

    channel: str = Field(..., description="Target channel (email, sms, push, etc.)")
    subject: str = Field(..., description="Content subject line")
    body: str = Field(..., description="Main content body")
    call_to_action: str = Field(..., description="CTA text")
    cta_url: str = Field(default="", description="CTA destination URL")
    personalization_tokens: dict[str, str] = Field(
        default_factory=dict, description="Token-value pairs used for personalization"
    )


class PersonalizationResult(BaseModel):
    """Complete personalization output for a customer."""

    customer_id: str = Field(..., description="Customer identifier")
    segment: str = Field(..., description="Customer segment")
    contents: list[PersonalizedContent] = Field(..., description="Personalized content pieces")
    recommended_offers: list[str] = Field(default_factory=list, description="Recommended offer IDs")
    next_best_action: str = Field(default="", description="Recommended next best action")
    confidence_score: float = Field(default=0.0, description="Confidence in personalization (0-1)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PersonalizationEngineAgent(BaseAgent[PersonalizationResult]):
    """Agent that generates personalized content, offers, and recommendations.

    Takes customer profile data, behavioral signals, and context to produce
    channel-specific personalized content with recommended offers and actions.
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        """Initialize the Personalization Engine agent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
        """
        if config is None:
            config = AgentConfig(
                name="personalization_engine",
                temperature=0.8,
                system_prompt=(
                    "You are an expert personalization engine. You create highly "
                    "personalized content tailored to individual customer profiles, "
                    "behaviors, and preferences. Content should be relevant, timely, "
                    "and drive engagement while respecting brand voice."
                ),
            )
        super().__init__(config)
        self._parser = PydanticOutputParser(pydantic_object=PersonalizationResult)

    async def run(self, input_data: dict[str, Any]) -> AgentResult[PersonalizationResult]:
        """Generate personalized content for a customer.

        Args:
            input_data: Must contain:
                - customer_id: Unique customer identifier
                - customer_profile: Dict of customer attributes
                - Optional: behavioral_signals, context, channel_preferences

        Returns:
            AgentResult containing the PersonalizationResult or an error.
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
                "personalization_generated",
                customer_id=result.customer_id,
                num_contents=len(result.contents),
                num_offers=len(result.recommended_offers),
                confidence=result.confidence_score,
            )

            return AgentResult(
                success=True,
                data=result,
                agent_name=self.config.name,
                tokens_used=response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0,
            )

        except Exception as e:
            logger.error("personalization_failed", error=str(e))
            return AgentResult(
                success=False,
                error=f"Failed to generate personalization: {e}",
                agent_name=self.config.name,
            )

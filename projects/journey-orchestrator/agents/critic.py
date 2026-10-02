"""Critic Agent — validates journey quality and provides governance feedback."""

from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentResult, BaseAgent
from core.exceptions import GovernanceError
from core.logging import get_logger

logger = get_logger(__name__)


class CriticFinding(BaseModel):
    """A single finding from the critic review."""

    severity: str = Field(..., description="Severity: info, warning, error, critical")
    category: str = Field(..., description="Category: compliance, brand, effectiveness, technical")
    description: str = Field(..., description="Description of the finding")
    recommendation: str = Field(default="", description="Recommended fix")
    location: str = Field(default="", description="Where in the journey this applies")


class CriticReview(BaseModel):
    """Complete critic review of a journey design."""

    journey_id: str = Field(..., description="Journey being reviewed")
    overall_score: float = Field(..., description="Overall quality score (0-1)")
    passed: bool = Field(..., description="Whether the journey passes review")
    findings: list[CriticFinding] = Field(default_factory=list, description="All findings")
    summary: str = Field(default="", description="Executive summary of the review")
    approved: bool = Field(default=False, description="Whether the journey is approved for deployment")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CriticAgent(BaseAgent[CriticReview]):
    """Agent that validates journey quality, checks compliance, and provides feedback.

    Reviews journey designs for:
    - Brand safety and voice consistency
    - Regulatory compliance (GDPR, CAN-SPAM, etc.)
    - Technical feasibility
    - Effectiveness and logical flow
    - Customer experience quality
    """

    def __init__(self, config: AgentConfig | None = None) -> None:
        """Initialize the Critic agent.

        Args:
            config: Optional agent configuration. Uses defaults if not provided.
        """
        if config is None:
            config = AgentConfig(
                name="critic",
                temperature=0.2,
                system_prompt=(
                    "You are an expert marketing governance critic. You review customer "
                    "journey designs for compliance, brand safety, technical feasibility, "
                    "and effectiveness. You are thorough, fair, and provide actionable "
                    "feedback. You flag issues that could harm customers or the brand."
                ),
            )
        super().__init__(config)
        self._parser = PydanticOutputParser(pydantic_object=CriticReview)

    async def run(self, input_data: dict[str, Any]) -> AgentResult[CriticReview]:
        """Review a journey design.

        Args:
            input_data: Must contain:
                - journey_id: The journey identifier
                - journey_design: The journey design to review
                - Optional: brand_guidelines, compliance_requirements, previous_reviews

        Returns:
            AgentResult containing the CriticReview or an error.
        """
        try:
            messages = self._build_messages(input_data)
            messages.append(
                HumanMessage(
                    content=f"\n\n{self._parser.get_format_instructions()}"
                )
            )

            response = await self.llm.ainvoke(messages)
            review = self._parser.parse(response.content)

            # Apply governance threshold
            from core.config import get_settings
            settings = get_settings()
            review.approved = review.overall_score >= settings.orchestration.critic_threshold

            if not review.approved:
                logger.warning(
                    "journey_rejected_by_critic",
                    journey_id=review.journey_id,
                    score=review.overall_score,
                    threshold=settings.orchestration.critic_threshold,
                    num_findings=len(review.findings),
                )
            else:
                logger.info(
                    "journey_approved_by_critic",
                    journey_id=review.journey_id,
                    score=review.overall_score,
                )

            return AgentResult(
                success=True,
                data=review,
                agent_name=self.config.name,
                tokens_used=response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0,
            )

        except Exception as e:
            logger.error("critic_review_failed", error=str(e))
            return AgentResult(
                success=False,
                error=f"Failed to review journey: {e}",
                agent_name=self.config.name,
            )

    async def validate_compliance(
        self, journey_id: str, journey_design: dict[str, Any]
    ) -> AgentResult[bool]:
        """Quick compliance check for a journey design.

        Args:
            journey_id: The journey identifier.
            journey_design: The journey design to check.

        Returns:
            AgentResult containing True if compliant, False otherwise.
        """
        try:
            input_data = {
                "journey_id": journey_id,
                "journey_design": journey_design,
                "check_type": "compliance_only",
            }
            messages = self._build_messages(input_data)

            response = await self.llm.ainvoke(messages)
            # Simple boolean check
            is_complied = "compliant" in response.content.lower() and "non-compliant" not in response.content.lower()

            if not is_complied:
                raise GovernanceError(
                    f"Journey {journey_id} failed compliance check",
                    code="COMPLIANCE_VIOLATION",
                )

            return AgentResult(
                success=True,
                data=is_complied,
                agent_name=self.config.name,
            )

        except GovernanceError:
            raise
        except Exception as e:
            logger.error("compliance_check_failed", journey_id=journey_id, error=str(e))
            return AgentResult(
                success=False,
                error=f"Compliance check failed: {e}",
                agent_name=self.config.name,
            )

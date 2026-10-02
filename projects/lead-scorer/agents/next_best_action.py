"""Next-Best-Action agent — recommends optimal outreach actions per lead."""

from __future__ import annotations

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentContext, AgentResult, BaseAgent


class NextBestActionInput(BaseModel):
    """Input for the Next-Best-Action agent."""

    lead_id: str = Field(..., description="Lead identifier")
    company_name: str = Field(..., description="Company name")
    lead_score: float = Field(..., ge=0.0, le=100.0, description="Overall lead score")
    grade: str = Field(..., description="Lead grade (A+ through F)")
    qualified: bool = Field(..., description="Whether lead is qualified")
    industry: str | None = Field(None, description="Industry vertical")
    company_size: str | None = Field(None, description="Company size")
    current_stage: str = Field(
        default="new",
        description="Current funnel stage: new, engaged, qualified, opportunity",
    )
    last_interaction: str | None = Field(
        None,
        description="Description of last interaction",
    )
    preferred_channel: str | None = Field(
        None,
        description="Preferred communication channel",
    )
    pain_points: list[str] = Field(
        default_factory=list,
        description="Identified pain points",
    )
    interests: list[str] = Field(
        default_factory=list,
        description="Identified interests/topics",
    )


class RecommendedAction(BaseModel):
    """A single recommended action."""

    action: str = Field(..., description="Action description")
    channel: str = Field(..., description="Communication channel")
    priority: int = Field(..., ge=1, le=5, description="Priority (1=highest)")
    timing: str = Field(..., description="When to execute")
    expected_outcome: str = Field(..., description="Expected outcome")
    template: str | None = Field(None, description="Message template or talking points")
    rationale: str = Field(..., description="Why this action is recommended")


class NextBestActionOutput(BaseModel):
    """Output from the Next-Best-Action agent."""

    lead_id: str
    actions: list[RecommendedAction] = Field(default_factory=list)
    overall_strategy: str = ""
    urgency: str = Field(..., description="high, medium, or low")
    next_review_date: str = ""
    summary: str = ""


class NextBestActionAgent(BaseAgent[NextBestActionInput, NextBestActionOutput]):
    """Recommends optimal outreach actions per lead.

    Based on lead score, qualification status, and engagement history,
    recommends the most effective next action to move the lead forward.
    """

    name = "next_best_action"
    description = "Recommends optimal outreach actions per lead"

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        default_config = AgentConfig(
            enabled=True,
            timeout_seconds=30.0,
            max_retries=1,
        )
        if config:
            default_config = config
        super().__init__(llm=llm, config=default_config)

    @property
    def input_model(self) -> type[NextBestActionInput]:
        return NextBestActionInput

    @property
    def output_model(self) -> type[NextBestActionOutput]:
        return NextBestActionOutput

    async def run(
        self, input_data: NextBestActionInput, context: AgentContext
    ) -> AgentResult[NextBestActionOutput]:
        """Generate next best action recommendations.

        Args:
            input_data: Lead context and scoring data.
            context: Execution context.

        Returns:
            Next best action recommendations.
        """
        try:
            actions = self._generate_actions(input_data)
            strategy = self._determine_strategy(input_data)
            urgency = self._determine_urgency(input_data)

            output = NextBestActionOutput(
                lead_id=input_data.lead_id,
                actions=actions,
                overall_strategy=strategy,
                urgency=urgency,
                next_review_date="7_days",
                summary=self._build_summary(actions, strategy, urgency),
            )
            return AgentResult(success=True, data=output)

        except Exception as exc:
            return AgentResult(
                success=False,
                error=f"Next-best-action generation failed: {exc}",
            )

    def _generate_actions(
        self, data: NextBestActionInput
    ) -> list[RecommendedAction]:
        """Generate recommended actions based on lead profile.

        Args:
            data: Lead context data.

        Returns:
            List of recommended actions sorted by priority.
        """
        actions: list[RecommendedAction] = []

        if data.lead_score >= 80:
            # High-score leads
            actions.append(
                RecommendedAction(
                    action="Schedule executive demo",
                    channel="email",
                    priority=1,
                    timing="Within 24 hours",
                    expected_outcome="Book product demo with decision maker",
                    template="Personalized demo invitation referencing their "
                              "specific use case and industry",
                    rationale="High lead score indicates strong fit and readiness",
                )
            )
            actions.append(
                RecommendedAction(
                    action="Send case study",
                    channel="email",
                    priority=2,
                    timing="Same day",
                    expected_outcome="Build credibility and social proof",
                    template=f"Case study from {data.industry or 'similar industry'} "
                              f"company of similar size",
                    rationale="Relevant case studies accelerate high-intent leads",
                )
            )

        elif data.lead_score >= 50:
            # Medium-score leads
            actions.append(
                RecommendedAction(
                    action="Send educational content",
                    channel=data.preferred_channel or "email",
                    priority=1,
                    timing="Within 48 hours",
                    expected_outcome="Increase engagement and nurture toward qualification",
                    template="Curated content addressing their identified pain points",
                    rationale="Medium-score leads need nurturing to build trust",
                )
            )
            if data.pain_points:
                actions.append(
                    RecommendedAction(
                        action="Pain point assessment call",
                        channel="phone",
                        priority=2,
                        timing="Within 1 week",
                        expected_outcome="Deepen understanding of challenges",
                        template=f"Discovery call focusing on: {', '.join(data.pain_points[:3])}",
                        rationale="Direct conversation helps qualify and build relationship",
                    )
                )

        else:
            # Low-score leads
            actions.append(
                RecommendedAction(
                    action="Add to nurture campaign",
                    channel="email",
                    priority=1,
                    timing="Immediate",
                    expected_outcome="Maintain touch until score improves",
                    template="Monthly newsletter with educational content",
                    rationale="Low-score leads need long-term nurturing",
                )
            )

        # Add channel-specific actions
        if data.preferred_channel == "linkedin":
            actions.append(
                RecommendedAction(
                    action="Connect on LinkedIn",
                    channel="linkedin",
                    priority=3,
                    timing="Within 24 hours",
                    expected_outcome="Establish social connection",
                    template="Personalized connection request",
                    rationale="Meeting leads on their preferred channel increases response rate",
                )
            )

        return sorted(actions, key=lambda a: a.priority)

    def _determine_strategy(self, data: NextBestActionInput) -> str:
        """Determine overall outreach strategy.

        Args:
            data: Lead context data.

        Returns:
            Strategy description.
        """
        if data.lead_score >= 80 and data.qualified:
            return "accelerate"
        if data.lead_score >= 80:
            return "qualify"
        if data.lead_score >= 50:
            return "nurture"
        if data.lead_score >= 30:
            return "educate"
        return "monitor"

    def _determine_urgency(self, data: NextBestActionInput) -> str:
        """Determine outreach urgency.

        Args:
            data: Lead context data.

        Returns:
            Urgency level.
        """
        if data.lead_score >= 80:
            return "high"
        if data.lead_score >= 50:
            return "medium"
        return "low"

    def _build_summary(
        self, actions: list[RecommendedAction], strategy: str, urgency: str
    ) -> str:
        """Build action plan summary.

        Args:
            actions: Recommended actions.
            strategy: Overall strategy.
            urgency: Urgency level.

        Returns:
            Summary string.
        """
        return (
            f"Strategy: {strategy}. Urgency: {urgency}. "
            f"{len(actions)} recommended actions. "
            f"Top priority: {actions[0].action if actions else 'None'}."
        )

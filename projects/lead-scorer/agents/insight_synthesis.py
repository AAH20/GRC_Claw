"""Insight Synthesis agent — aggregates all agent outputs into actionable insights."""

from __future__ import annotations

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentContext, AgentResult, BaseAgent


class InsightSynthesisInput(BaseModel):
    """Input for the Insight Synthesis agent."""

    lead_id: str = Field(..., description="Lead identifier")
    company_name: str = Field(..., description="Company name")
    research_summary: str = Field(default="", description="Research agent output summary")
    evidence_summary: str = Field(default="", description="Evidence agent output summary")
    scoring_summary: str = Field(default="", description="Scoring agent output summary")
    qualification_summary: str = Field(
        default="", description="Qualification agent output summary"
    )
    churn_summary: str = Field(
        default="", description="Churn prediction output summary (if existing customer)"
    )
    next_action_summary: str = Field(
        default="", description="Next-best-action output summary"
    )
    lead_score: float | None = Field(None, ge=0.0, le=100.0)
    grade: str | None = Field(None)
    qualified: bool | None = None
    churn_risk: str | None = Field(None, description="high, medium, or low")


class KeyInsight(BaseModel):
    """A single key insight."""

    category: str = Field(
        ...,
        description="e.g., 'opportunity', 'risk', 'recommendation', 'observation'",
    )
    insight: str = Field(..., description="The insight itself")
    impact: str = Field(..., description="high, medium, or low")
    confidence: float = Field(ge=0.0, le=1.0)
    source_agents: list[str] = Field(
        default_factory=list,
        description="Agents that contributed to this insight",
    )


class ActionItem(BaseModel):
    """A single action item."""

    action: str
    owner: str = Field(..., description="Recommended owner (sales, marketing, cs)")
    priority: int = Field(..., ge=1, le=5)
    due_date: str = Field(..., description="Suggested due date or timeframe")
    expected_impact: str = ""


class InsightSynthesisOutput(BaseModel):
    """Output from the Insight Synthesis agent."""

    lead_id: str
    overall_assessment: str = ""
    key_insights: list[KeyInsight] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommended_approach: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = ""


class InsightSynthesisAgent(BaseAgent[InsightSynthesisInput, InsightSynthesisOutput]):
    """Aggregates all agent outputs into actionable insights.

    Synthesizes outputs from all other agents to provide a unified
    view of the lead with actionable recommendations.
    """

    name = "insight_synthesis"
    description = "Aggregates all agent outputs into actionable insights"

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        default_config = AgentConfig(
            enabled=True,
            timeout_seconds=60.0,
            max_retries=2,
        )
        if config:
            default_config = config
        super().__init__(llm=llm, config=default_config)

    @property
    def input_model(self) -> type[InsightSynthesisInput]:
        return InsightSynthesisInput

    @property
    def output_model(self) -> type[InsightSynthesisOutput]:
        return InsightSynthesisOutput

    async def run(
        self, input_data: InsightSynthesisInput, context: AgentContext
    ) -> AgentResult[InsightSynthesisOutput]:
        """Synthesize insights from all agent outputs.

        Args:
            input_data: Summaries from all other agents.
            context: Execution context.

        Returns:
            Synthesized insights with key findings and action items.
        """
        try:
            key_insights = self._extract_key_insights(input_data)
            action_items = self._generate_action_items(input_data, key_insights)
            opportunities = self._identify_opportunities(input_data)
            risks = self._identify_risks(input_data)
            approach = self._recommend_approach(input_data)
            confidence = self._compute_confidence(input_data)

            output = InsightSynthesisOutput(
                lead_id=input_data.lead_id,
                overall_assessment=self._build_overall_assessment(input_data),
                key_insights=key_insights,
                action_items=action_items,
                opportunities=opportunities,
                risks=risks,
                recommended_approach=approach,
                confidence=round(confidence, 2),
                summary=self._build_summary(key_insights, action_items, opportunities, risks),
            )
            return AgentResult(success=True, data=output)

        except Exception as exc:
            return AgentResult(
                success=False,
                error=f"Insight synthesis failed: {exc}",
            )

    def _extract_key_insights(
        self, data: InsightSynthesisInput
    ) -> list[KeyInsight]:
        """Extract key insights from all agent outputs.

        Args:
            data: Agent output summaries.

        Returns:
            List of key insights.
        """
        insights: list[KeyInsight] = []

        # Scoring insight
        if data.lead_score is not None:
            if data.lead_score >= 80:
                insights.append(
                    KeyInsight(
                        category="opportunity",
                        insight=f"High-value lead with score {data.lead_score}/100 "
                                f"(Grade: {data.grade or 'N/A'})",
                        impact="high",
                        confidence=0.9,
                        source_agents=["scoring"],
                    )
                )
            elif data.lead_score >= 50:
                insights.append(
                    KeyInsight(
                        category="observation",
                        insight=f"Moderate-value lead with score {data.lead_score}/100 "
                                f"(Grade: {data.grade or 'N/A'})",
                        impact="medium",
                        confidence=0.85,
                        source_agents=["scoring"],
                    )
                )
            else:
                insights.append(
                    KeyInsight(
                        category="observation",
                        insight=f"Low-value lead with score {data.lead_score}/100 "
                                f"(Grade: {data.grade or 'N/A'}). Needs nurturing.",
                        impact="low",
                        confidence=0.85,
                        source_agents=["scoring"],
                    )
                )

        # Qualification insight
        if data.qualified is not None:
            if data.qualified:
                insights.append(
                    KeyInsight(
                        category="opportunity",
                        insight="Lead meets qualification criteria — ready for sales engagement",
                        impact="high",
                        confidence=0.85,
                        source_agents=["qualification"],
                    )
                )
            else:
                insights.append(
                    KeyInsight(
                        category="risk",
                        insight="Lead does not yet meet qualification criteria",
                        impact="medium",
                        confidence=0.8,
                        source_agents=["qualification"],
                    )
                )

        # Churn insight (for existing customers)
        if data.churn_risk:
            if data.churn_risk == "high":
                insights.append(
                    KeyInsight(
                        category="risk",
                        insight="HIGH churn risk detected — immediate intervention required",
                        impact="high",
                        confidence=0.8,
                        source_agents=["churn_prediction"],
                    )
                )
            elif data.churn_risk == "medium":
                insights.append(
                    KeyInsight(
                        category="risk",
                        insight="Medium churn risk — proactive retention recommended",
                        impact="medium",
                        confidence=0.75,
                        source_agents=["churn_prediction"],
                    )
                )

        return insights

    def _generate_action_items(
        self,
        data: InsightSynthesisInput,
        insights: list[KeyInsight],
    ) -> list[ActionItem]:
        """Generate action items from insights.

        Args:
            data: Agent output summaries.
            insights: Extracted key insights.

        Returns:
            List of action items.
        """
        actions: list[ActionItem] = []

        if data.lead_score and data.lead_score >= 80:
            actions.append(
                ActionItem(
                    action="Route to sales for immediate follow-up",
                    owner="sales",
                    priority=1,
                    due_date="24_hours",
                    expected_impact="Accelerate pipeline progression",
                )
            )

        if data.qualified is False:
            actions.append(
                ActionItem(
                    action="Continue nurturing campaign",
                    owner="marketing",
                    priority=2,
                    due_date="ongoing",
                    expected_impact="Improve lead score over time",
                )
            )

        if data.churn_risk == "high":
            actions.append(
                ActionItem(
                    action="Schedule executive business review",
                    owner="customer_success",
                    priority=1,
                    due_date="7_days",
                    expected_impact="Reduce churn risk",
                )
            )

        if not actions:
            actions.append(
                ActionItem(
                    action="Monitor and re-evaluate in 30 days",
                    owner="marketing",
                    priority=3,
                    due_date="30_days",
                    expected_impact="Maintain engagement",
                )
            )

        return sorted(actions, key=lambda a: a.priority)

    def _identify_opportunities(
        self, data: InsightSynthesisInput
    ) -> list[str]:
        """Identify opportunities from agent outputs.

        Args:
            data: Agent output summaries.

        Returns:
            List of opportunity descriptions.
        """
        opportunities: list[str] = []

        if data.lead_score and data.lead_score >= 80:
            opportunities.append("High-intent lead ready for sales engagement")
        if data.qualified:
            opportunities.append("Qualified lead with confirmed budget and need")
        if data.churn_risk == "low":
            opportunities.append("Strong retention — potential for upsell/expansion")

        return opportunities

    def _identify_risks(self, data: InsightSynthesisInput) -> list[str]:
        """Identify risks from agent outputs.

        Args:
            data: Agent output summaries.

        Returns:
            List of risk descriptions.
        """
        risks: list[str] = []

        if data.lead_score and data.lead_score < 30:
            risks.append("Low engagement — lead may go cold")
        if data.qualified is False:
            risks.append("Unqualified lead — may waste sales resources")
        if data.churn_risk == "high":
            risks.append("High churn risk — revenue at risk")

        return risks

    def _recommend_approach(self, data: InsightSynthesisInput) -> str:
        """Recommend overall approach.

        Args:
            data: Agent output summaries.

        Returns:
            Recommended approach description.
        """
        if data.churn_risk == "high":
            return "retention_first"
        if data.lead_score and data.lead_score >= 80 and data.qualified:
            return "accelerate_to_close"
        if data.lead_score and data.lead_score >= 50:
            return "nurture_and_qualify"
        return "long_term_nurture"

    def _compute_confidence(self, data: InsightSynthesisInput) -> float:
        """Compute overall confidence in synthesized insights.

        Args:
            data: Agent output summaries.

        Returns:
            Confidence score between 0 and 1.
        """
        # More agent inputs = higher confidence
        sources = [
            data.research_summary,
            data.evidence_summary,
            data.scoring_summary,
            data.qualification_summary,
            data.next_action_summary,
        ]
        filled = sum(1 for s in sources if s)
        return min(0.95, 0.4 + (filled * 0.1))

    def _build_overall_assessment(self, data: InsightSynthesisInput) -> str:
        """Build overall assessment text.

        Args:
            data: Agent output summaries.

        Returns:
            Overall assessment string.
        """
        parts: list[str] = []

        if data.lead_score is not None:
            parts.append(f"Lead Score: {data.lead_score}/100 (Grade: {data.grade or 'N/A'})")
        if data.qualified is not None:
            parts.append(f"Qualified: {'Yes' if data.qualified else 'No'}")
        if data.churn_risk:
            parts.append(f"Churn Risk: {data.churn_risk}")

        return ". ".join(parts) if parts else "Insufficient data for assessment"

    def _build_summary(
        self,
        insights: list[KeyInsight],
        actions: list[ActionItem],
        opportunities: list[str],
        risks: list[str],
    ) -> str:
        """Build synthesis summary.

        Args:
            insights: Key insights.
            actions: Action items.
            opportunities: Opportunities.
            risks: Risks.

        Returns:
            Summary string.
        """
        return (
            f"Synthesized {len(insights)} insights, {len(actions)} action items. "
            f"{len(opportunities)} opportunities, {len(risks)} risks identified."
        )

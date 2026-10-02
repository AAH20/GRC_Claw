"""Insight synthesis agent for aggregating insights across all agents."""

from __future__ import annotations

import time
from datetime import UTC
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from lead_scorer.agents.churn_prediction import ChurnPredictionResult
    from lead_scorer.agents.evidence import EvidenceResult
    from lead_scorer.agents.next_best_action import NextBestActionResult
    from lead_scorer.agents.qualification import QualificationResult
    from lead_scorer.agents.research import ResearchResult
    from lead_scorer.agents.scoring import ScoringResult


logger = structlog.get_logger(__name__)


class Insight(BaseModel):
    """A single synthesized insight."""

    category: str
    title: str
    description: str
    impact: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    source_agents: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SynthesizedInsights(BaseModel):
    """Result from the insight synthesis agent."""

    lead_id: str
    overall_assessment: str = ""
    insights: list[Insight] = Field(default_factory=list)
    key_strengths: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)
    recommended_focus: str = ""
    synthesized_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class InsightSynthesisAgent:
    """Agent responsible for synthesizing insights from all other agents.

    Aggregates results from research, evidence, scoring, qualification,
    churn prediction, and next-best-action agents into cohesive insights.
    """

    def __init__(self, timeout_seconds: int = 60, max_retries: int = 2) -> None:
        """Initialize the insight synthesis agent.

        Args:
            timeout_seconds: Maximum time allowed for synthesis.
            max_retries: Number of retry attempts on failure.
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def synthesize(
        self,
        lead_id: str,
        research: ResearchResult | None = None,
        evidence: EvidenceResult | None = None,
        scoring: ScoringResult | None = None,
        qualification: QualificationResult | None = None,
        churn_prediction: ChurnPredictionResult | None = None,
        next_best_action: NextBestActionResult | None = None,
        **kwargs: Any,
    ) -> SynthesizedInsights:
        """Synthesize insights from all agent results.

        Args:
            lead_id: Unique identifier for the lead.
            research: Optional research result.
            evidence: Optional evidence result.
            scoring: Optional scoring result.
            qualification: Optional qualification result.
            churn_prediction: Optional churn prediction result.
            next_best_action: Optional next best action result.
            **kwargs: Additional context.

        Returns:
            SynthesizedInsights with aggregated insights.

        Raises:
            ValueError: If lead_id is empty.
            TimeoutError: If synthesis exceeds timeout.
        """
        if not lead_id:
            raise ValueError("lead_id is required")

        logger.info("synthesizing_insights", lead_id=lead_id)
        start_time = time.monotonic()

        try:
            insights: list[Insight] = []
            strengths: list[str] = []
            risks: list[str] = []

            # Synthesize from research
            if research:
                research_insights = self._synthesize_research(research)
                insights.extend(research_insights)

            # Synthesize from evidence
            if evidence:
                evidence_insights = self._synthesize_evidence(evidence)
                insights.extend(evidence_insights)

            # Synthesize from scoring
            if scoring:
                scoring_insights, scoring_strengths, scoring_risks = self._synthesize_scoring(
                    scoring
                )
                insights.extend(scoring_insights)
                strengths.extend(scoring_strengths)
                risks.extend(scoring_risks)

            # Synthesize from qualification
            if qualification:
                qual_insights, qual_strengths, qual_risks = self._synthesize_qualification(
                    qualification
                )
                insights.extend(qual_insights)
                strengths.extend(qual_strengths)
                risks.extend(qual_risks)

            # Synthesize from churn prediction
            if churn_prediction:
                churn_insights = self._synthesize_churn(churn_prediction)
                insights.extend(churn_insights)

            # Synthesize from next best action
            if next_best_action:
                nba_insights = self._synthesize_nba(next_best_action)
                insights.extend(nba_insights)

            elapsed = time.monotonic() - start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(f"Insight synthesis timed out after {elapsed:.1f}s")

            overall = self._generate_overall_assessment(
                scoring, qualification, insights
            )
            focus = self._determine_focus(insights, risks)

            from datetime import datetime

            result = SynthesizedInsights(
                lead_id=lead_id,
                overall_assessment=overall,
                insights=insights,
                key_strengths=strengths,
                key_risks=risks,
                recommended_focus=focus,
                synthesized_at=datetime.now(UTC).isoformat(),
                metadata={
                    "elapsed_seconds": elapsed,
                    "agent_count": sum(
                        x is not None
                        for x in [
                            research,
                            evidence,
                            scoring,
                            qualification,
                            churn_prediction,
                            next_best_action,
                        ]
                    ),
                },
            )

            logger.info(
                "insights_synthesized",
                lead_id=lead_id,
                insight_count=len(insights),
                strength_count=len(strengths),
                risk_count=len(risks),
            )
            return result

        except Exception as exc:
            logger.error("insight_synthesis_failed", lead_id=lead_id, error=str(exc))
            raise

    def _synthesize_research(self, research: ResearchResult) -> list[Insight]:
        """Synthesize insights from research data."""
        insights: list[Insight] = []
        firm = research.firmographic
        tech = research.technographic

        if firm.company_size > 100:
            insights.append(
                Insight(
                    category="firmographic",
                    title="Enterprise-scale prospect",
                    description=(
                        f"Company size of {firm.company_size} "
                        f"indicates enterprise potential"
                    ),
                    impact="Higher deal value potential",
                    confidence=research.confidence,
                    source_agents=["research"],
                )
            )

        if tech.technologies:
            insights.append(
                Insight(
                    category="technographic",
                    title="Modern tech stack detected",
                    description=f"Uses {', '.join(tech.technologies[:3])}",
                    impact="Likely receptive to technical solutions",
                    confidence=research.confidence * 0.8,
                    source_agents=["research"],
                )
            )

        return insights

    def _synthesize_evidence(self, evidence: EvidenceResult) -> list[Insight]:
        """Synthesize insights from evidence data."""
        insights: list[Insight] = []

        if evidence.engagement_score > 0.5:
            insights.append(
                Insight(
                    category="engagement",
                    title="High engagement detected",
                    description=f"Engagement score: {evidence.engagement_score:.0%}",
                    impact="Strong buying signal",
                    confidence=evidence.engagement_score,
                    source_agents=["evidence"],
                )
            )

        if evidence.intent_signals:
            signal_types = [s.signal_type for s in evidence.intent_signals]
            insights.append(
                Insight(
                    category="intent",
                    title="Multiple intent signals",
                    description=f"Detected: {', '.join(signal_types)}",
                    impact="Active evaluation in progress",
                    confidence=evidence.intent_score,
                    source_agents=["evidence"],
                )
            )

        if evidence.recency_score < 0.3:
            insights.append(
                Insight(
                    category="recency",
                    title="Engagement declining",
                    description="No recent engagement detected",
                    impact="Risk of going cold",
                    confidence=0.7,
                    source_agents=["evidence"],
                )
            )

        return insights

    def _synthesize_scoring(
        self, scoring: ScoringResult
    ) -> tuple[list[Insight], list[str], list[str]]:
        """Synthesize insights from scoring result."""
        insights: list[Insight] = []
        strengths: list[str] = []
        risks: list[str] = []

        insights.append(
            Insight(
                category="scoring",
                title=f"Lead scored {scoring.total_score:.0f}/100 ({scoring.grade.value})",
                description=f"Confidence: {scoring.confidence:.0%}",
                impact="Determines priority and routing",
                confidence=scoring.confidence,
                source_agents=["scoring"],
            )
        )

        if scoring.grade.value == "hot":
            strengths.append("High overall lead score")
        elif scoring.grade.value == "cold":
            risks.append("Low overall lead score")

        for component in scoring.components:
            if component.weighted_score * 100 >= 20:
                strengths.append(f"Strong {component.name} signals")
            elif component.weighted_score * 100 < 5:
                risks.append(f"Weak {component.name} signals")

        return insights, strengths, risks

    def _synthesize_qualification(
        self, qualification: QualificationResult
    ) -> tuple[list[Insight], list[str], list[str]]:
        """Synthesize insights from qualification result."""
        insights: list[Insight] = []
        strengths: list[str] = []
        risks: list[str] = []

        insights.append(
            Insight(
                category="qualification",
                title=f"Qualification: {qualification.status.value}",
                description=(
                    f"Score: {qualification.total_score:.0%} "
                    f"using {qualification.framework.value}"
                ),
                impact="Determines sales readiness",
                confidence=qualification.total_score,
                source_agents=["qualification"],
            )
        )

        if qualification.status.value == "qualified":
            strengths.append("Fully qualified lead")
        elif qualification.status.value == "disqualified":
            risks.append("Lead does not meet qualification criteria")

        for gap in qualification.gaps:
            risks.append(f"Missing: {gap}")

        return insights, strengths, risks

    def _synthesize_churn(
        self, churn: ChurnPredictionResult
    ) -> list[Insight]:
        """Synthesize insights from churn prediction."""
        insights: list[Insight] = []

        if churn.risk_level.value in ("high", "critical"):
            insights.append(
                Insight(
                    category="churn_risk",
                    title=f"Churn risk: {churn.risk_level.value}",
                    description=f"Probability: {churn.churn_probability:.0%}",
                    impact="Immediate retention action needed",
                    confidence=churn.confidence,
                    source_agents=["churn_prediction"],
                )
            )

        return insights

    def _synthesize_nba(
        self, nba: NextBestActionResult
    ) -> list[Insight]:
        """Synthesize insights from next best action."""
        insights: list[Insight] = []

        insights.append(
            Insight(
                category="action",
                title=f"Recommended: {nba.primary_action.title}",
                description=nba.primary_action.description,
                impact=nba.primary_action.expected_outcome,
                confidence=0.8,
                source_agents=["next_best_action"],
            )
        )

        return insights

    def _generate_overall_assessment(
        self,
        scoring: ScoringResult | None,
        qualification: QualificationResult | None,
        insights: list[Insight],
    ) -> str:
        """Generate overall assessment text."""
        if not scoring:
            return "Insufficient data for assessment"

        parts: list[str] = []
        parts.append(f"Lead scores {scoring.total_score:.0f}/100 ({scoring.grade.value})")

        if qualification:
            parts.append(f"qualification: {qualification.status.value}")

        high_impact = [i for i in insights if i.impact]
        if high_impact:
            parts.append(f"{len(high_impact)} key insights identified")

        return ". ".join(parts) + "."

    def _determine_focus(self, insights: list[Insight], risks: list[str]) -> str:
        """Determine recommended focus area."""
        if risks:
            return f"Address risks: {', '.join(risks[:3])}"
        if insights:
            return f"Capitalize on: {insights[0].title}"
        return "Gather more data"

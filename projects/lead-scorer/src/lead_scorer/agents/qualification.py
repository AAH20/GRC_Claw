"""Qualification agent for applying BANT/MEDDIC criteria."""

from __future__ import annotations

import time
from datetime import UTC
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class QualificationFramework(StrEnum):
    """Supported qualification frameworks."""

    BANT = "bant"
    MEDDIC = "meddic"
    CHAMP = "champ"


class QualificationStatus(StrEnum):
    """Qualification status of a lead."""

    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    PENDING = "pending"


class QualificationCriteria(BaseModel):
    """Individual qualification criterion result."""

    name: str
    met: bool
    score: float = Field(ge=0.0, le=1.0)
    evidence: str = ""
    weight: float = Field(ge=0.0, le=1.0, default=1.0)


class QualificationResult(BaseModel):
    """Result from the qualification agent."""

    lead_id: str
    framework: QualificationFramework
    status: QualificationStatus
    total_score: float = Field(ge=0.0, le=1.0)
    criteria: list[QualificationCriteria] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    qualified_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualificationAgent:
    """Agent responsible for qualifying leads using BANT/MEDDIC.

    Evaluates leads against qualification criteria and determines
    if they are ready for sales engagement.
    """

    def __init__(
        self,
        framework: QualificationFramework = QualificationFramework.MEDDIC,
        timeout_seconds: int = 30,
        max_retries: int = 1,
    ) -> None:
        """Initialize the qualification agent.

        Args:
            framework: Qualification framework to use.
            timeout_seconds: Maximum time allowed for qualification.
            max_retries: Number of retry attempts on failure.
        """
        self.framework = framework
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def qualify(
        self,
        lead_id: str,
        budget: float | None = None,
        authority: bool | None = None,
        need: bool | None = None,
        timeline_days: int | None = None,
        **kwargs: Any,
    ) -> QualificationResult:
        """Qualify a lead.

        Args:
            lead_id: Unique identifier for the lead.
            budget: Available budget in USD.
            authority: Whether lead has decision-making authority.
            need: Whether a clear need exists.
            timeline_days: Expected timeline to purchase in days.
            **kwargs: Additional framework-specific criteria.

        Returns:
            QualificationResult with status and criteria breakdown.

        Raises:
            ValueError: If lead_id is empty.
            TimeoutError: If qualification exceeds timeout.
        """
        if not lead_id:
            raise ValueError("lead_id is required")

        logger.info("qualifying_lead", lead_id=lead_id, framework=self.framework.value)
        start_time = time.monotonic()

        try:
            if self.framework == QualificationFramework.BANT:
                criteria = self._evaluate_bant(budget, authority, need, timeline_days)
            elif self.framework == QualificationFramework.MEDDIC:
                criteria = self._evaluate_meddic(
                    budget, authority, need, timeline_days, **kwargs
                )
            else:
                criteria = self._evaluate_champ(budget, authority, need, timeline_days)

            elapsed = time.monotonic() - start_time
            if elapsed > self.timeout_seconds:
                raise TimeoutError(f"Qualification timed out after {elapsed:.1f}s")

            total_score = self._compute_total_score(criteria)
            status = self._determine_status(total_score, criteria)
            gaps = [c.name for c in criteria if not c.met]
            recommendations = self._generate_recommendations(criteria, gaps)

            from datetime import datetime

            result = QualificationResult(
                lead_id=lead_id,
                framework=self.framework,
                status=status,
                total_score=total_score,
                criteria=criteria,
                gaps=gaps,
                recommendations=recommendations,
                qualified_at=datetime.now(UTC).isoformat(),
                metadata={"elapsed_seconds": elapsed},
            )

            logger.info(
                "lead_qualified",
                lead_id=lead_id,
                status=status.value,
                score=total_score,
            )
            return result

        except Exception as exc:
            logger.error("qualification_failed", lead_id=lead_id, error=str(exc))
            raise

    def _evaluate_bant(
        self,
        budget: float | None,
        authority: bool | None,
        need: bool | None,
        timeline_days: int | None,
    ) -> list[QualificationCriteria]:
        """Evaluate BANT criteria."""
        criteria: list[QualificationCriteria] = []

        # Budget
        budget_met = budget is not None and budget >= 10000
        budget_score = min((budget or 0) / 50000, 1.0)
        criteria.append(
            QualificationCriteria(
                name="budget",
                met=budget_met,
                score=budget_score,
                evidence=f"Budget: ${budget:,.0f}" if budget else "No budget info",
                weight=0.25,
            )
        )

        # Authority
        criteria.append(
            QualificationCriteria(
                name="authority",
                met=authority is True,
                score=1.0 if authority else 0.0,
                evidence="Has authority" if authority else "No authority confirmed",
                weight=0.25,
            )
        )

        # Need
        criteria.append(
            QualificationCriteria(
                name="need",
                met=need is True,
                score=1.0 if need else 0.0,
                evidence="Need identified" if need else "Need not confirmed",
                weight=0.25,
            )
        )

        # Timeline
        timeline_met = timeline_days is not None and timeline_days <= 90
        timeline_score = 0.0
        if timeline_days is not None:
            timeline_score = max(0.0, 1.0 - (timeline_days / 365))
        criteria.append(
            QualificationCriteria(
                name="timeline",
                met=timeline_met,
                score=timeline_score,
                evidence=f"Timeline: {timeline_days} days" if timeline_days else "No timeline",
                weight=0.25,
            )
        )

        return criteria

    def _evaluate_meddic(
        self,
        budget: float | None,
        authority: bool | None,
        need: bool | None,
        timeline_days: int | None,
        **kwargs: Any,
    ) -> list[QualificationCriteria]:
        """Evaluate MEDDIC criteria."""
        criteria: list[QualificationCriteria] = []

        # Metrics
        metrics_score = kwargs.get("metrics_score", 0.5)
        criteria.append(
            QualificationCriteria(
                name="metrics",
                met=metrics_score >= 0.5,
                score=metrics_score,
                evidence=kwargs.get("metrics_evidence", "No metrics data"),
                weight=0.15,
            )
        )

        # Economic Buyer
        criteria.append(
            QualificationCriteria(
                name="economic_buyer",
                met=authority is True,
                score=1.0 if authority else 0.0,
                evidence="Economic buyer identified" if authority else "No economic buyer",
                weight=0.20,
            )
        )

        # Decision Criteria
        decision_score = kwargs.get("decision_criteria_score", 0.5)
        criteria.append(
            QualificationCriteria(
                name="decision_criteria",
                met=decision_score >= 0.5,
                score=decision_score,
                evidence=kwargs.get("decision_evidence", "No decision criteria"),
                weight=0.15,
            )
        )

        # Decision Process
        process_score = kwargs.get("decision_process_score", 0.5)
        criteria.append(
            QualificationCriteria(
                name="decision_process",
                met=process_score >= 0.5,
                score=process_score,
                evidence=kwargs.get("process_evidence", "No process data"),
                weight=0.15,
            )
        )

        # Identify Pain / Need
        criteria.append(
            QualificationCriteria(
                name="identify_pain",
                met=need is True,
                score=1.0 if need else 0.0,
                evidence="Pain identified" if need else "Pain not identified",
                weight=0.20,
            )
        )

        # Champion
        champion_score = kwargs.get("champion_score", 0.5)
        criteria.append(
            QualificationCriteria(
                name="champion",
                met=champion_score >= 0.5,
                score=champion_score,
                evidence=kwargs.get("champion_evidence", "No champion data"),
                weight=0.15,
            )
        )

        # Timeline (bonus)
        if timeline_days is not None:
            timeline_score = max(0.0, 1.0 - (timeline_days / 365))
            criteria.append(
                QualificationCriteria(
                    name="timeline",
                    met=timeline_days <= 90,
                    score=timeline_score,
                    evidence=f"Timeline: {timeline_days} days",
                    weight=0.10,
                )
            )

        return criteria

    def _evaluate_champ(
        self,
        budget: float | None,
        authority: bool | None,
        need: bool | None,
        timeline_days: int | None,
    ) -> list[QualificationCriteria]:
        """Evaluate CHAMP criteria."""
        criteria: list[QualificationCriteria] = []

        # Challenge (Need)
        criteria.append(
            QualificationCriteria(
                name="challenge",
                met=need is True,
                score=1.0 if need else 0.0,
                evidence="Challenge identified" if need else "No challenge",
                weight=0.30,
            )
        )

        # Authority
        criteria.append(
            QualificationCriteria(
                name="authority",
                met=authority is True,
                score=1.0 if authority else 0.0,
                evidence="Has authority" if authority else "No authority",
                weight=0.25,
            )
        )

        # Money (Budget)
        budget_met = budget is not None and budget >= 10000
        budget_score = min((budget or 0) / 50000, 1.0)
        criteria.append(
            QualificationCriteria(
                name="money",
                met=budget_met,
                score=budget_score,
                evidence=f"Budget: ${budget:,.0f}" if budget else "No budget",
                weight=0.25,
            )
        )

        # Priority (Timeline)
        timeline_met = timeline_days is not None and timeline_days <= 90
        timeline_score = 0.0
        if timeline_days is not None:
            timeline_score = max(0.0, 1.0 - (timeline_days / 365))
        criteria.append(
            QualificationCriteria(
                name="priority",
                met=timeline_met,
                score=timeline_score,
                evidence=f"Timeline: {timeline_days} days" if timeline_days else "No timeline",
                weight=0.20,
            )
        )

        return criteria

    def _compute_total_score(self, criteria: list[QualificationCriteria]) -> float:
        """Compute weighted total score from criteria."""
        if not criteria:
            return 0.0
        total_weight = sum(c.weight for c in criteria)
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(c.score * c.weight for c in criteria)
        return round(weighted_sum / total_weight, 2)

    def _determine_status(
        self, total_score: float, criteria: list[QualificationCriteria]
    ) -> QualificationStatus:
        """Determine qualification status."""
        if total_score >= 0.7:
            return QualificationStatus.QUALIFIED
        if total_score >= 0.4:
            return QualificationStatus.PENDING
        return QualificationStatus.DISQUALIFIED

    def _generate_recommendations(
        self, criteria: list[QualificationCriteria], gaps: list[str]
    ) -> list[str]:
        """Generate recommendations based on gaps."""
        recommendations: list[str] = []
        for gap in gaps:
            if gap == "budget":
                recommendations.append("Schedule discovery call to understand budget")
            elif gap == "authority":
                recommendations.append("Identify and engage economic buyer")
            elif gap == "need":
                recommendations.append("Conduct pain-point analysis workshop")
            elif gap == "timeline":
                recommendations.append("Nurture campaign until timeline matures")
            elif gap == "champion":
                recommendations.append("Develop internal champion through value demos")
            elif gap == "metrics":
                recommendations.append("Quantify ROI with metrics workshop")
        return recommendations

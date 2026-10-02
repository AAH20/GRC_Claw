"""Relationship Management agent for long-term influencer relationships."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog

from influencer_marketing.agents.base import AgentConfig, AgentResult, BaseAgent
from influencer_marketing.agents.performance import PerformanceReport

logger = structlog.get_logger(__name__)


class RelationshipTier(StrEnum):
    """Tier classification for influencer relationships."""

    NEW = "new"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class RelationshipStatus(StrEnum):
    """Status of an influencer relationship."""

    PROSPECT = "prospect"
    ACTIVE = "active"
    ENGAGED = "engaged"
    DORMANT = "dormant"
    CHURNED = "churned"
    ADVOCATE = "advocate"


@dataclass
class RelationshipRecord:
    """Record of an influencer relationship."""

    influencer_id: str
    tier: RelationshipTier
    status: RelationshipStatus
    total_campaigns: int = 0
    total_spend: float = 0.0
    average_roas: float = 0.0
    last_interaction: datetime | None = None
    next_check_in: datetime | None = None
    notes: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


@dataclass
class RelationshipInsight:
    """Insight about an influencer relationship."""

    influencer_id: str
    relationship_health: float  # 0-1 score
    churn_risk: float  # 0-1 probability
    lifetime_value_estimate: float
    recommended_actions: list[str] = field(default_factory=list)
    tier_progression: RelationshipTier | None = None


class RelationshipManagementAgent(
    BaseAgent[tuple[RelationshipRecord, list[PerformanceReport]], RelationshipInsight]
):
    """Agent responsible for maintaining long-term influencer relationships and retention."""

    def __init__(self) -> None:
        config = AgentConfig(
            name="relationship_management",
            description="Maintains long-term influencer relationships and retention",
            max_retries=3,
            timeout_seconds=60,
        )
        super().__init__(config)
        self.check_in_interval_days = 30

    async def validate_input(
        self, input_data: tuple[RelationshipRecord, list[PerformanceReport]]
    ) -> bool:
        """Validate relationship management input."""
        record, reports = input_data
        if not record.influencer_id:
            self.logger.warning("Influencer ID missing")
            return False
        return True

    async def execute(
        self, input_data: tuple[RelationshipRecord, list[PerformanceReport]]
    ) -> AgentResult[RelationshipInsight]:
        """Execute relationship analysis and generate insights."""
        record, reports = input_data
        self.logger.info(
            "Analyzing relationship",
            influencer_id=record.influencer_id,
            tier=record.tier.value,
        )

        try:
            # Calculate relationship health
            health = self._calculate_health(record, reports)

            # Assess churn risk
            churn_risk = self._assess_churn_risk(record, reports)

            # Estimate lifetime value
            ltv = self._estimate_ltv(record, reports)

            # Generate recommended actions
            actions = self._generate_actions(record, health, churn_risk)

            # Determine tier progression
            tier_progression = self._evaluate_tier_progression(record, reports)

            insight = RelationshipInsight(
                influencer_id=record.influencer_id,
                relationship_health=health,
                churn_risk=churn_risk,
                lifetime_value_estimate=ltv,
                recommended_actions=actions,
                tier_progression=tier_progression,
            )

            self.logger.info(
                "Relationship analysis completed",
                influencer_id=record.influencer_id,
                health=health,
                churn_risk=churn_risk,
            )
            return AgentResult(success=True, data=insight)

        except Exception as exc:
            self.logger.error("Relationship analysis failed", error=str(exc))
            return AgentResult(success=False, error=str(exc))

    def _calculate_health(
        self, record: RelationshipRecord, reports: list[PerformanceReport]
    ) -> float:
        """Calculate overall relationship health score."""
        score = 0.5  # Base score

        # Factor: campaign frequency
        if record.total_campaigns > 5:
            score += 0.15
        elif record.total_campaigns > 2:
            score += 0.08

        # Factor: performance consistency
        if reports:
            roas_values = [r.metrics.roas for r in reports if r.metrics.roas > 0]
            if roas_values:
                avg_roas = sum(roas_values) / len(roas_values)
                if avg_roas > 2.0:
                    score += 0.15
                elif avg_roas > 1.0:
                    score += 0.08

        # Factor: recency of interaction
        if record.last_interaction:
            days_since = (datetime.utcnow() - record.last_interaction).days
            if days_since < 30:
                score += 0.1
            elif days_since < 60:
                score += 0.05
            else:
                score -= 0.1

        return max(0.0, min(1.0, score))

    def _assess_churn_risk(
        self, record: RelationshipRecord, reports: list[PerformanceReport]
    ) -> float:
        """Assess the risk of losing the influencer."""
        risk = 0.1  # Base risk

        # Long time since last interaction
        if record.last_interaction:
            days_since = (datetime.utcnow() - record.last_interaction).days
            if days_since > 90:
                risk += 0.3
            elif days_since > 60:
                risk += 0.15

        # Declining performance
        if len(reports) >= 2:
            recent = reports[-1].metrics.roas
            previous = reports[-2].metrics.roas
            if recent < previous * 0.5:
                risk += 0.2

        # Low engagement history
        if record.total_campaigns == 0:
            risk += 0.2

        return max(0.0, min(1.0, risk))

    def _estimate_ltv(
        self, record: RelationshipRecord, reports: list[PerformanceReport]
    ) -> float:
        """Estimate lifetime value of the relationship."""
        if not reports or record.total_campaigns == 0:
            return 0.0

        avg_campaign_value = record.total_spend / record.total_campaigns
        avg_roas = sum(r.metrics.roas for r in reports) / len(reports)

        # Simple LTV: expected campaigns per year * avg value * relationship duration
        expected_campaigns_per_year = max(2, record.total_campaigns)
        estimated_relationship_years = 2.0  # Conservative estimate

        return (
            avg_campaign_value
            * avg_roas
            * expected_campaigns_per_year
            * estimated_relationship_years
        )

    def _generate_actions(
        self, record: RelationshipRecord, health: float, churn_risk: float
    ) -> list[str]:
        """Generate recommended actions based on relationship analysis."""
        actions: list[str] = []

        if churn_risk > 0.5:
            actions.append("Schedule immediate check-in call")
            actions.append("Offer exclusive campaign opportunity")

        if health < 0.4:
            actions.append("Review and improve collaboration terms")
            actions.append("Request feedback on partnership experience")

        if record.next_check_in and record.next_check_in < datetime.utcnow():
            actions.append("Overdue for routine check-in - schedule now")

        if not actions:
            actions.append("Continue regular engagement schedule")

        return actions

    def _evaluate_tier_progression(
        self, record: RelationshipRecord, reports: list[PerformanceReport]
    ) -> RelationshipTier | None:
        """Evaluate if influencer qualifies for tier progression."""
        if record.total_campaigns >= 10 and record.average_roas > 3.0:
            return RelationshipTier.PLATINUM
        elif record.total_campaigns >= 5 and record.average_roas > 2.0:
            return RelationshipTier.GOLD
        elif record.total_campaigns >= 3 and record.average_roas > 1.5:
            return RelationshipTier.SILVER
        elif record.total_campaigns >= 1:
            return RelationshipTier.BRONZE
        return None

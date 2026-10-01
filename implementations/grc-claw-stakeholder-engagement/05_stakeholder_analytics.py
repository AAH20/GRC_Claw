"""
GRC_Claw Stakeholder Analytics
===============================
Implements the stakeholder analytics engine from the GRC_Claw Stakeholder
Engagement Specification v2.0 (Section 8).

Covers:
- Multi-dimensional sentiment analysis (5 dimensions per Spec §8.3.1)
- Sentiment scoring with weighting (Spec §8.3.2, §8.3.3)
- Stakeholder behavior analytics (7 metrics per Spec §8.4.1)
- Stakeholder journey mapping (5 stages per Spec §8.4.2)
- Churn prediction (6 risk factors per Spec §8.5.1)
- Advocacy prediction (6 indicators per Spec §8.5.2)
- Sentiment alerts (5 types per Spec §8.6.2)
- Three-layer dashboard data (Executive, Program, Operating per Spec §8.6.1)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from collections import defaultdict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SentimentCategory(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class EngagementSentiment(str, Enum):
    ENTHUSIASTIC = "enthusiastic"
    ENGAGED = "engaged"
    NEUTRAL = "neutral"
    DISENGAGED = "disengaged"
    RESISTANT = "resistant"


class TrustSentiment(str, Enum):
    HIGH_TRUST = "high_trust"
    TRUSTING = "trusting"
    NEUTRAL = "neutral"
    SKEPTICAL = "skeptical"
    DISTRUSTING = "distrusting"


class UrgencySentiment(str, Enum):
    SUPPORTIVE = "supportive"
    NEUTRAL = "neutral"
    CONCERNED = "concerned"
    ALARMED = "alarmed"


class SatisfactionSentiment(str, Enum):
    SATISFIED = "satisfied"
    NEUTRAL = "neutral"
    DISSATISFIED = "dissatisfied"
    FRUSTRATED = "frustrated"


class JourneyStage(str, Enum):
    AWARENESS = "awareness"
    INTEREST = "interest"
    ENGAGEMENT = "engagement"
    ADVOCACY = "advocacy"
    PARTNERSHIP = "partnership"


class AlertType(str, Enum):
    SENTIMENT_DROP = "sentiment_drop"
    GROUP_SENTIMENT_DECLINE = "group_sentiment_decline"
    NEGATIVE_FEEDBACK_SPIKE = "negative_feedback_spike"
    ADVOCACY_OPPORTUNITY = "advocacy_opportunity"
    CHURN_RISK = "churn_risk"


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class SentimentSignal:
    """A single sentiment signal from any source."""

    signal_id: str
    stakeholder_id: str
    source: str  # survey, interview, feedback, communication, social, support
    timestamp: str
    overall: SentimentCategory
    engagement: EngagementSentiment = EngagementSentiment.NEUTRAL
    trust: TrustSentiment = TrustSentiment.NEUTRAL
    urgency: UrgencySentiment = UrgencySentiment.NEUTRAL
    satisfaction: SatisfactionSentiment = SatisfactionSentiment.NEUTRAL
    weight: float = 1.0
    specificity: str = "general"  # specific / general
    text: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["overall"] = self.overall.value
        d["engagement"] = self.engagement.value
        d["trust"] = self.trust.value
        d["urgency"] = self.urgency.value
        d["satisfaction"] = self.satisfaction.value
        return d


@dataclass
class BehaviorMetrics:
    """Engagement behavior metrics for a stakeholder (Spec §8.4.1)."""

    stakeholder_id: str
    period_start: str
    period_end: str
    engagement_frequency: int = 0  # interactions per period
    engagement_depth: str = "surface"  # surface / moderate / deep
    response_latency_hours: float = 0.0
    channel_preferences: dict[str, int] = field(default_factory=dict)
    content_open_rate: float = 0.0
    content_click_rate: float = 0.0
    participation_rate: float = 0.0
    initiative_rate: float = 0.0  # stakeholder-initiated vs GRC_Claw-initiated
    feedback_specificity: str = "low"  # low / medium / high

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChurnRiskAssessment:
    """Churn prediction result (Spec §8.5.1)."""

    stakeholder_id: str
    risk_score: float  # 0-1
    risk_factors: list[str] = field(default_factory=list)
    indicators: dict[str, bool] = field(default_factory=dict)
    recommended_action: str = ""
    assessment_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AdvocacyScore:
    """Advocacy prediction result (Spec §8.5.2)."""

    stakeholder_id: str
    score: float  # 0-1
    indicators: dict[str, float] = field(default_factory=dict)
    recommended_action: str = ""
    assessment_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SentimentAlert:
    """Sentiment alert (Spec §8.6.2)."""

    alert_id: str
    alert_type: AlertType
    stakeholder_id: str
    message: str
    severity: str  # low / medium / high / critical
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    acknowledged: bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["alert_type"] = self.alert_type.value
        return d


# ---------------------------------------------------------------------------
# Sentiment Analysis Engine
# ---------------------------------------------------------------------------

class SentimentAnalysisEngine:
    """
    Multi-dimensional sentiment analysis engine (Spec §8.3).

    Dimensions:
    - Overall Sentiment: Positive / Neutral / Negative / Mixed
    - Engagement Sentiment: Enthusiastic / Engaged / Neutral / Disengaged / Resistant
    - Trust Sentiment: High Trust / Trusting / Neutral / Skeptical / Distrusting
    - Urgency Sentiment: Supportive / Neutral / Concerned / Alarmed
    - Satisfaction Sentiment: Satisfied / Neutral / Dissatisfied / Frustrated
    """

    # Source weights (Spec §8.3.3)
    SOURCE_WEIGHTS = {
        "interview": 1.5,
        "survey": 1.2,
        "feedback": 1.3,
        "communication": 1.0,
        "social": 0.8,
        "support": 1.1,
    }

    # Priority weights (Spec §8.3.3)
    PRIORITY_WEIGHTS = {
        "P1": 3.0,
        "P2": 2.0,
        "P3": 1.0,
    }

    # Specificity weights (Spec §8.3.3)
    SPECIFICITY_WEIGHTS = {
        "specific": 1.3,
        "general": 1.0,
    }

    # Half-life for recency decay (days)
    RECENCY_HALF_LIFE = 90

    def __init__(self):
        self._signals: dict[str, SentimentSignal] = {}
        self._stakeholder_priorities: dict[str, str] = {}
        self._alerts: dict[str, SentimentAlert] = {}
        self._next_id = 1

    def set_stakeholder_priority(self, stakeholder_id: str, priority: str) -> None:
        self._stakeholder_priorities[stakeholder_id] = priority

    def add_signal(self, signal: SentimentSignal) -> SentimentSignal:
        """Add a sentiment signal."""
        if not signal.signal_id:
            signal.signal_id = f"SIG-{self._next_id:04d}"
            self._next_id += 1
        self._signals[signal.signal_id] = signal
        return signal

    def calculate_sentiment_score(self, stakeholder_id: str,
                                   as_of: Optional[str] = None) -> dict:
        """
        Calculate weighted sentiment score for a stakeholder (Spec §8.3.2).

        Sentiment Score = (Positive × 1.0 + Neutral × 0.0 + Negative × -1.0) / Total
        Normalized to: -1.0 (very negative) to +1.0 (very positive)
        """
        priority = self._stakeholder_priorities.get(stakeholder_id, "P3")
        priority_weight = self.PRIORITY_WEIGHTS.get(priority, 1.0)

        as_of_dt = datetime.fromisoformat(as_of.replace("Z", "+00:00")) if as_of else datetime.utcnow()

        weighted_sum = 0.0
        total_weight = 0.0
        positive_count = 0
        neutral_count = 0
        negative_count = 0

        for signal in self._signals.values():
            if signal.stakeholder_id != stakeholder_id:
                continue

            # Recency decay
            try:
                signal_dt = datetime.fromisoformat(signal.timestamp.replace("Z", "+00:00"))
                days_old = (as_of_dt - signal_dt).days
                recency_weight = 0.5 ** (days_old / self.RECENCY_HALF_LIFE)
            except (ValueError, AttributeError):
                recency_weight = 1.0

            # Source weight
            source_weight = self.SOURCE_WEIGHTS.get(signal.source, 1.0)

            # Specificity weight
            spec_weight = self.SPECIFICITY_WEIGHTS.get(signal.specificity, 1.0)

            # Combined weight
            combined_weight = (signal.weight * priority_weight * source_weight *
                               spec_weight * recency_weight)

            # Sentiment value
            if signal.overall == SentimentCategory.POSITIVE:
                sentiment_value = 1.0
                positive_count += 1
            elif signal.overall == SentimentCategory.NEGATIVE:
                sentiment_value = -1.0
                negative_count += 1
            else:
                sentiment_value = 0.0
                neutral_count += 1

            weighted_sum += sentiment_value * combined_weight
            total_weight += combined_weight

        if total_weight == 0:
            score = 0.0
        else:
            score = weighted_sum / total_weight

        return {
            "stakeholder_id": stakeholder_id,
            "sentiment_score": round(score, 3),
            "positive_signals": positive_count,
            "neutral_signals": neutral_count,
            "negative_signals": negative_count,
            "total_signals": positive_count + neutral_count + negative_count,
            "priority": priority,
        }

    def get_group_sentiment(self, stakeholder_ids: list[str]) -> dict:
        """Calculate average sentiment for a group of stakeholders."""
        scores = []
        for sid in stakeholder_ids:
            result = self.calculate_sentiment_score(sid)
            scores.append(result["sentiment_score"])

        if not scores:
            return {"average": 0.0, "count": 0}

        return {
            "average": round(sum(scores) / len(scores), 3),
            "count": len(scores),
            "min": round(min(scores), 3),
            "max": round(max(scores), 3),
        }

    def get_sentiment_trend(self, stakeholder_id: str,
                            periods: int = 6) -> list[dict]:
        """Get sentiment trend over time periods."""
        trend = []
        now = datetime.utcnow()

        for i in range(periods - 1, -1, -1):
            period_end = now - timedelta(days=i * 30)
            result = self.calculate_sentiment_score(stakeholder_id, as_of=period_end.isoformat())
            trend.append({
                "period": period_end.strftime("%Y-%m"),
                "score": result["sentiment_score"],
            })

        return trend

    # ---- Behavior Analytics ----

    def analyze_behavior(self, metrics: BehaviorMetrics) -> dict:
        """
        Analyze stakeholder behavior metrics (Spec §8.4.1).
        """
        analysis = {
            "stakeholder_id": metrics.stakeholder_id,
            "engagement_frequency": metrics.engagement_frequency,
            "engagement_depth": metrics.engagement_depth,
            "response_latency_hours": metrics.response_latency_hours,
            "content_open_rate": metrics.content_open_rate,
            "content_click_rate": metrics.content_click_rate,
            "participation_rate": metrics.participation_rate,
            "initiative_rate": metrics.initiative_rate,
            "feedback_specificity": metrics.feedback_specificity,
        }

        # Assess against targets
        assessments = {}
        if metrics.content_open_rate > 0:
            assessments["open_rate"] = "good" if metrics.content_open_rate > 0.40 else "needs_improvement"
        if metrics.content_click_rate > 0:
            assessments["click_rate"] = "good" if metrics.content_click_rate > 0.15 else "needs_improvement"
        if metrics.participation_rate > 0:
            assessments["participation"] = "good" if metrics.participation_rate > 0.75 else "needs_improvement"
        if metrics.initiative_rate > 0:
            assessments["initiative"] = "good" if metrics.initiative_rate > 0.30 else "needs_improvement"

        analysis["assessments"] = assessments
        return analysis

    def get_journey_stage(self, stakeholder_id: str,
                          behavior: BehaviorMetrics,
                          sentiment_score: float) -> JourneyStage:
        """
        Determine stakeholder journey stage (Spec §8.4.2).

        AWARENESS → INTEREST → ENGAGEMENT → ADVOCACY → PARTNERSHIP
        """
        if behavior.engagement_frequency == 0:
            return JourneyStage.AWARENESS
        elif behavior.engagement_frequency < 3 and sentiment_score < 0.3:
            return JourneyStage.INTEREST
        elif behavior.engagement_frequency >= 3 and sentiment_score >= 0.3:
            if behavior.initiative_rate > 0.5 and sentiment_score > 0.7:
                return JourneyStage.PARTNERSHIP
            elif behavior.initiative_rate > 0.3 and sentiment_score > 0.5:
                return JourneyStage.ADVOCACY
            return JourneyStage.ENGAGEMENT
        return JourneyStage.INTEREST

    # ---- Churn Prediction ----

    def predict_churn_risk(self, stakeholder_id: str,
                           behavior: BehaviorMetrics,
                           sentiment_score: float,
                           last_engagement_days: int,
                           unresolved_feedback_count: int,
                           missed_engagements: int) -> ChurnRiskAssessment:
        """
        Predict churn risk (Spec §8.5.1).

        Risk Factors:
        - Declining engagement: 3+ months without interaction
        - Negative sentiment trend: score declining 2+ periods
        - Unresolved feedback: open >60 days
        - Missed engagements: 2+ consecutive missed
        """
        risk_factors = []
        indicators = {}
        risk_score = 0.0

        # Declining engagement
        if last_engagement_days > 90:
            risk_factors.append("declining_engagement")
            indicators["declining_engagement"] = True
            risk_score += 0.25
        else:
            indicators["declining_engagement"] = False

        # Negative sentiment
        if sentiment_score < -0.3:
            risk_factors.append("negative_sentiment")
            indicators["negative_sentiment"] = True
            risk_score += 0.25
        else:
            indicators["negative_sentiment"] = False

        # Unresolved feedback
        if unresolved_feedback_count > 0:
            risk_factors.append("unresolved_feedback")
            indicators["unresolved_feedback"] = True
            risk_score += 0.20
        else:
            indicators["unresolved_feedback"] = False

        # Missed engagements
        if missed_engagements >= 2:
            risk_factors.append("missed_engagements")
            indicators["missed_engagements"] = True
            risk_score += 0.20
        else:
            indicators["missed_engagements"] = False

        # Low engagement frequency
        if behavior.engagement_frequency < 2:
            risk_factors.append("low_frequency")
            indicators["low_frequency"] = True
            risk_score += 0.10
        else:
            indicators["low_frequency"] = False

        # Determine action
        if risk_score > 0.6:
            action = "Immediate re-engagement campaign + executive outreach"
        elif risk_score > 0.4:
            action = "Re-engagement campaign + personal outreach"
        elif risk_score > 0.2:
            action = "Monitor + targeted communication"
        else:
            action = "No action needed"

        return ChurnRiskAssessment(
            stakeholder_id=stakeholder_id,
            risk_score=round(risk_score, 3),
            risk_factors=risk_factors,
            indicators=indicators,
            recommended_action=action,
        )

    # ---- Advocacy Prediction ----

    def predict_advocacy(self, stakeholder_id: str,
                         sentiment_score: float,
                         engagement_frequency: int,
                         feedback_specificity: str,
                         community_participation: bool,
                         referral_count: int,
                         public_endorsements: int) -> AdvocacyScore:
        """
        Predict advocacy potential (Spec §8.5.2).

        Indicators and weights:
        - Consistently positive sentiment: 0.25
        - High engagement frequency: 0.20
        - Specific, constructive feedback: 0.20
        - Active community participation: 0.15
        - Referral behavior: 0.10
        - Public endorsement: 0.10

        Advocacy Score > 0.70 → Invite to advocacy program
        """
        indicators = {}

        # Positive sentiment (0.25)
        if sentiment_score > 0.5:
            indicators["positive_sentiment"] = 0.25
        elif sentiment_score > 0.3:
            indicators["positive_sentiment"] = 0.15
        else:
            indicators["positive_sentiment"] = 0.0

        # High engagement frequency (0.20)
        if engagement_frequency > 10:
            indicators["high_engagement"] = 0.20
        elif engagement_frequency > 5:
            indicators["high_engagement"] = 0.12
        else:
            indicators["high_engagement"] = 0.0

        # Specific feedback (0.20)
        if feedback_specificity == "high":
            indicators["specific_feedback"] = 0.20
        elif feedback_specificity == "medium":
            indicators["specific_feedback"] = 0.10
        else:
            indicators["specific_feedback"] = 0.0

        # Community participation (0.15)
        indicators["community_participation"] = 0.15 if community_participation else 0.0

        # Referral behavior (0.10)
        if referral_count > 2:
            indicators["referral_behavior"] = 0.10
        elif referral_count > 0:
            indicators["referral_behavior"] = 0.05
        else:
            indicators["referral_behavior"] = 0.0

        # Public endorsement (0.10)
        if public_endorsements > 1:
            indicators["public_endorsement"] = 0.10
        elif public_endorsements > 0:
            indicators["public_endorsement"] = 0.05
        else:
            indicators["public_endorsement"] = 0.0

        total_score = sum(indicators.values())

        if total_score > 0.70:
            action = "Invite to advocacy program / advisory board"
        elif total_score > 0.50:
            action = "Nurture toward advocacy — increase engagement"
        else:
            action = "Continue regular engagement"

        return AdvocacyScore(
            stakeholder_id=stakeholder_id,
            score=round(total_score, 3),
            indicators=indicators,
            recommended_action=action,
        )

    # ---- Alerts ----

    def check_alerts(self, stakeholder_id: str,
                     current_sentiment: float,
                     previous_sentiment: float,
                     negative_feedback_count: int,
                     advocacy_score: float,
                     churn_risk: float) -> list[SentimentAlert]:
        """Check for sentiment alerts (Spec §8.6.2)."""
        alerts = []

        # Sentiment drop > 0.3 in 30 days
        if previous_sentiment - current_sentiment > 0.3:
            alerts.append(SentimentAlert(
                alert_id=f"ALT-{len(self._alerts) + 1:04d}",
                alert_type=AlertType.SENTIMENT_DROP,
                stakeholder_id=stakeholder_id,
                message=f"Sentiment dropped by {previous_sentiment - current_sentiment:.2f} in 30 days",
                severity="high",
            ))

        # Negative feedback spike
        if negative_feedback_count > 3:
            alerts.append(SentimentAlert(
                alert_id=f"ALT-{len(self._alerts) + 2:04d}",
                alert_type=AlertType.NEGATIVE_FEEDBACK_SPIKE,
                stakeholder_id=stakeholder_id,
                message=f"{negative_feedback_count} negative feedback items in 7 days",
                severity="medium",
            ))

        # Advocacy opportunity
        if advocacy_score > 0.70:
            alerts.append(SentimentAlert(
                alert_id=f"ALT-{len(self._alerts) + 3:04d}",
                alert_type=AlertType.ADVOCACY_OPPORTUNITY,
                stakeholder_id=stakeholder_id,
                message=f"Advocacy score {advocacy_score:.2f} — invite to advocacy program",
                severity="low",
            ))

        # Churn risk
        if churn_risk > 0.60:
            alerts.append(SentimentAlert(
                alert_id=f"ALT-{len(self._alerts) + 4:04d}",
                alert_type=AlertType.CHURN_RISK,
                stakeholder_id=stakeholder_id,
                message=f"Churn risk {churn_risk:.2f} — retention action needed",
                severity="critical",
            ))

        for alert in alerts:
            self._alerts[alert.alert_id] = alert

        return alerts

    # ---- Dashboard Data ----

    def get_executive_dashboard(self, stakeholder_ids: list[str]) -> dict:
        """Executive sentiment dashboard (Spec §8.6.1)."""
        group = self.get_group_sentiment(stakeholder_ids)
        trends = []
        for sid in stakeholder_ids[:5]:  # Top 5
            trend = self.get_sentiment_trend(sid, periods=3)
            trends.append({"stakeholder_id": sid, "trend": trend})

        return {
            "view": "executive",
            "audience": "Exec sponsors, governance committee",
            "group_average": group["average"],
            "group_count": group["count"],
            "top_trends": trends,
            "alerts": [a.to_dict() for a in self._alerts.values()
                       if a.severity in ("high", "critical")],
        }

    def get_program_dashboard(self, stakeholder_ids: list[str]) -> dict:
        """Program sentiment dashboard (Spec §8.6.1)."""
        by_priority = defaultdict(list)
        for sid in stakeholder_ids:
            priority = self._stakeholder_priorities.get(sid, "P3")
            by_priority[priority].append(sid)

        group_sentiment = {}
        for priority, sids in by_priority.items():
            group_sentiment[priority] = self.get_group_sentiment(sids)

        return {
            "view": "program",
            "audience": "Engagement leads",
            "sentiment_by_priority": group_sentiment,
            "total_alerts": len(self._alerts),
            "unacknowledged_alerts": len([a for a in self._alerts.values() if not a.acknowledged]),
        }

    def get_operating_dashboard(self, stakeholder_id: str) -> dict:
        """Operating sentiment dashboard (Spec §8.6.1)."""
        sentiment = self.calculate_sentiment_score(stakeholder_id)
        trend = self.get_sentiment_trend(stakeholder_id, periods=6)
        recent_signals = [s.to_dict() for s in self._signals.values()
                          if s.stakeholder_id == stakeholder_id][-10:]

        return {
            "view": "operating",
            "audience": "Engagement team",
            "stakeholder_id": stakeholder_id,
            "current_sentiment": sentiment,
            "trend": trend,
            "recent_signals": recent_signals,
        }


# ---------------------------------------------------------------------------
# Demo / Self-test
# ---------------------------------------------------------------------------

def _demo():
    """Demonstrate stakeholder analytics."""
    engine = SentimentAnalysisEngine()

    # Set up stakeholder priorities
    engine.set_stakeholder_priority("STK-001", "P1")
    engine.set_stakeholder_priority("STK-002", "P1")
    engine.set_stakeholder_priority("STK-003", "P2")
    engine.set_stakeholder_priority("STK-004", "P3")

    # Add sentiment signals
    print("--- Adding Sentiment Signals ---")
    signals = [
        SentimentSignal("", "STK-001", "survey", "2026-09-01T10:00:00",
                        SentimentCategory.POSITIVE, EngagementSentiment.ENGAGED,
                        TrustSentiment.TRUSTING, UrgencySentiment.SUPPORTIVE,
                        SatisfactionSentiment.SATISFIED, 1.0, "specific"),
        SentimentSignal("", "STK-001", "feedback", "2026-09-15T14:00:00",
                        SentimentCategory.POSITIVE, EngagementSentiment.ENTHUSIASTIC,
                        TrustSentiment.HIGH_TRUST, UrgencySentiment.SUPPORTIVE,
                        SatisfactionSentiment.SATISFIED, 1.0, "specific"),
        SentimentSignal("", "STK-002", "interview", "2026-09-10T09:00:00",
                        SentimentCategory.NEUTRAL, EngagementSentiment.ENGAGED,
                        TrustSentiment.NEUTRAL, UrgencySentiment.NEUTRAL,
                        SatisfactionSentiment.NEUTRAL, 1.0, "general"),
        SentimentSignal("", "STK-003", "support", "2026-09-20T16:00:00",
                        SentimentCategory.NEGATIVE, EngagementSentiment.DISENGAGED,
                        TrustSentiment.SKEPTICAL, UrgencySentiment.CONCERNED,
                        SatisfactionSentiment.DISSATISFIED, 1.0, "specific"),
        SentimentSignal("", "STK-004", "social", "2026-09-25T11:00:00",
                        SentimentCategory.NEUTRAL, EngagementSentiment.NEUTRAL,
                        TrustSentiment.NEUTRAL, UrgencySentiment.NEUTRAL,
                        SatisfactionSentiment.NEUTRAL, 1.0, "general"),
    ]

    for sig in signals:
        engine.add_signal(sig)
        print(f"  Added: {sig.signal_id} | {sig.stakeholder_id} | {sig.overall.value}")

    # Calculate sentiment scores
    print("\n--- Sentiment Scores ---")
    for sid in ["STK-001", "STK-002", "STK-003", "STK-004"]:
        result = engine.calculate_sentiment_score(sid)
        print(f"  {sid}: score={result['sentiment_score']} "
              f"(+{result['positive_signals']} / -{result['negative_signals']})")

    # Group sentiment
    print("\n--- Group Sentiment ---")
    group = engine.get_group_sentiment(["STK-001", "STK-002", "STK-003", "STK-004"])
    print(f"  Average: {group['average']} across {group['count']} stakeholders")

    # Behavior analysis
    print("\n--- Behavior Analysis ---")
    behavior = BehaviorMetrics(
        stakeholder_id="STK-001",
        period_start="2026-09-01",
        period_end="2026-09-30",
        engagement_frequency=12,
        engagement_depth="deep",
        response_latency_hours=4.5,
        content_open_rate=0.65,
        content_click_rate=0.28,
        participation_rate=0.85,
        initiative_rate=0.40,
        feedback_specificity="high",
    )
    analysis = engine.analyze_behavior(behavior)
    print(f"  {behavior.stakeholder_id}: freq={analysis['engagement_frequency']}, "
          f"depth={analysis['engagement_depth']}")
    print(f"  Assessments: {analysis['assessments']}")

    # Journey stage
    sentiment = engine.calculate_sentiment_score("STK-001")
    stage = engine.get_journey_stage("STK-001", behavior, sentiment["sentiment_score"])
    print(f"  Journey stage: {stage.value}")

    # Churn prediction
    print("\n--- Churn Prediction ---")
    churn = engine.predict_churn_risk(
        "STK-003", behavior, -0.4, 120, 2, 3
    )
    print(f"  {churn.stakeholder_id}: risk={churn.risk_score} factors={churn.risk_factors}")
    print(f"  Action: {churn.recommended_action}")

    # Advocacy prediction
    print("\n--- Advocacy Prediction ---")
    advocacy = engine.predict_advocacy(
        "STK-001", 0.8, 15, "high", True, 3, 2
    )
    print(f"  {advocacy.stakeholder_id}: score={advocacy.score}")
    print(f"  Indicators: {advocacy.indicators}")
    print(f"  Action: {advocacy.recommended_action}")

    # Alerts
    print("\n--- Sentiment Alerts ---")
    alerts = engine.check_alerts("STK-003", -0.4, 0.1, 5, 0.3, 0.7)
    for alert in alerts:
        print(f"  {alert.alert_id}: {alert.alert_type.value} — {alert.message}")

    # Dashboard data
    print("\n--- Executive Dashboard ---")
    exec_dash = engine.get_executive_dashboard(["STK-001", "STK-002", "STK-003", "STK-004"])
    print(f"  Group average: {exec_dash['group_average']}")
    print(f"  Alerts: {len(exec_dash['alerts'])}")

    print("\n--- Program Dashboard ---")
    prog_dash = engine.get_program_dashboard(["STK-001", "STK-002", "STK-003", "STK-004"])
    print(f"  Sentiment by priority: {prog_dash['sentiment_by_priority']}")

    print("\n--- Operating Dashboard ---")
    ops_dash = engine.get_operating_dashboard("STK-001")
    print(f"  Current sentiment: {ops_dash['current_sentiment']['sentiment_score']}")
    print(f"  Recent signals: {len(ops_dash['recent_signals'])}")

    print("\n✓ Stakeholder Analytics demo complete")


if __name__ == "__main__":
    _demo()

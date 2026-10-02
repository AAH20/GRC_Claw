"""
Retention Agent - Predicts churn risk and generates retention actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class RiskLevel(str, Enum):
    """Churn risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(str, Enum):
    """Types of retention actions."""
    EMAIL = "email"
    DISCOUNT = "discount"
    CALL = "call"
    IN_APP = "in_app"


@dataclass
class CustomerHealth:
    """Customer health metrics."""
    customer_id: str
    health_score: float  # 0-100
    risk_level: RiskLevel
    days_since_last_active: int
    total_spend: float
    engagement_trend: str  # improving, stable, declining
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RetentionAction:
    """A retention action to be taken."""
    action_id: str
    customer_id: str
    action_type: ActionType
    description: str
    priority: int  # 1-10
    due_date: datetime
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


class RetentionAgent:
    """Agent for predicting churn and generating retention actions."""

    def __init__(self, risk_threshold: float = 0.5) -> None:
        self.risk_threshold = risk_threshold
        self.logger = logger.bind(agent="retention")

    def assess_health(
        self,
        customer_id: str,
        days_since_last_active: int,
        total_spend: float,
        engagement_trend: str = "stable",
    ) -> CustomerHealth:
        """Assess customer health based on activity and spend."""
        # Simple heuristic
        score = 100.0
        score -= min(days_since_last_active * 2, 50)
        score += min(total_spend / 100, 20)
        if engagement_trend == "declining":
            score -= 20
        elif engagement_trend == "improving":
            score += 10
        score = max(0, min(100, score))

        if score >= 70:
            risk = RiskLevel.LOW
        elif score >= 50:
            risk = RiskLevel.MEDIUM
        elif score >= 30:
            risk = RiskLevel.HIGH
        else:
            risk = RiskLevel.CRITICAL

        return CustomerHealth(
            customer_id=customer_id,
            health_score=score,
            risk_level=risk,
            days_since_last_active=days_since_last_active,
            total_spend=total_spend,
            engagement_trend=engagement_trend,
        )

    def generate_actions(self, health: CustomerHealth) -> list[RetentionAction]:
        """Generate retention actions based on customer health."""
        actions: list[RetentionAction] = []
        now = datetime.utcnow()

        if health.risk_level == RiskLevel.CRITICAL:
            actions.append(
                RetentionAction(
                    action_id=f"act_{health.customer_id}_call",
                    customer_id=health.customer_id,
                    action_type=ActionType.CALL,
                    description="Urgent: Schedule personal outreach call",
                    priority=10,
                    due_date=now + timedelta(days=1),
                )
            )
            actions.append(
                RetentionAction(
                    action_id=f"act_{health.customer_id}_discount",
                    customer_id=health.customer_id,
                    action_type=ActionType.DISCOUNT,
                    description="Offer 20% discount to prevent churn",
                    priority=9,
                    due_date=now + timedelta(days=2),
                )
            )
        elif health.risk_level == RiskLevel.HIGH:
            actions.append(
                RetentionAction(
                    action_id=f"act_{health.customer_id}_email",
                    customer_id=health.customer_id,
                    action_type=ActionType.EMAIL,
                    description="Send re-engagement email campaign",
                    priority=7,
                    due_date=now + timedelta(days=3),
                )
            )
        elif health.risk_level == RiskLevel.MEDIUM:
            actions.append(
                RetentionAction(
                    action_id=f"act_{health.customer_id}_inapp",
                    customer_id=health.customer_id,
                    action_type=ActionType.IN_APP,
                    description="Trigger in-app engagement prompt",
                    priority=4,
                    due_date=now + timedelta(days=7),
                )
            )

        return actions

    def should_intervene(self, health: CustomerHealth) -> bool:
        """Determine if intervention is needed."""
        return health.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

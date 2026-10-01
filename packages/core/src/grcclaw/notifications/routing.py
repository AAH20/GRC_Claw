"""
Alert routing engine for GRC_Claw — routes alerts to appropriate responders.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from .models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    Notification,
    NotificationPriority,
    NotificationType,
    RoutingRule,
)

logger = logging.getLogger(__name__)


class AlertRouter:
    """
    Routes alerts to the right teams and individuals based on severity,
    framework, entity type, and custom routing rules.

    Supports:
    - Severity-based escalation
    - Framework-specific routing (SOC2, ISO27001, PCI-DSS, HIPAA, GDPR)
    - Entity-type routing (policy, control, evidence, framework)
    - Time-based routing (business hours vs. after-hours)
    - On-call rotation integration
    - Escalation chains
    """

    def __init__(self):
        self._routing_rules: list[RoutingRule] = []
        self._escalation_chains: dict[str, list[str]] = {}
        self._on_call: dict[str, str] = {}
        self._team_mappings: dict[str, list[str]] = defaultdict(list)
        self._framework_owners: dict[str, str] = {}
        self._severity_channels: dict[str, list[str]] = {
            "critical": ["slack", "email", "teams", "webhook"],
            "high": ["slack", "email"],
            "medium": ["slack"],
            "low": ["email"],
            "info": ["email"],
        }
        self._business_hours = {"start": 9, "end": 17}  # 9 AM - 5 PM
        self._business_days = {0, 1, 2, 3, 4}  # Mon-Fri
        self._escalation_history: list[dict[str, Any]] = []

    # ─── Configuration ───────────────────────────────────────────────────────

    def add_routing_rule(self, rule: RoutingRule) -> None:
        """Add a custom routing rule."""
        self._routing_rules.append(rule)
        self._routing_rules.sort(key=lambda r: r.priority)

    def set_escalation_chain(self, severity: str, chain: list[str]) -> None:
        """Set an escalation chain for a severity level.

        Chain is an ordered list of recipients. If the first doesn't respond
        within the escalation timeout, it goes to the next, and so on.
        """
        self._escalation_chains[severity] = chain

    def set_on_call(self, team: str, recipient: str) -> None:
        """Set the current on-call person for a team."""
        self._on_call[team] = recipient

    def add_team_member(self, team: str, member: str) -> None:
        """Add a member to a team."""
        self._team_mappings[team].append(member)

    def set_framework_owner(self, framework: str, owner: str) -> None:
        """Set the owner for a compliance framework."""
        self._framework_owners[framework] = owner

    def set_severity_channels(self, severity: str, channels: list[str]) -> None:
        """Override the default channels for a severity level."""
        self._severity_channels[severity] = channels

    def set_business_hours(self, start: int, end: int, days: set[int]) -> None:
        """Configure business hours for time-based routing."""
        self._business_hours = {"start": start, "end": end}
        self._business_days = days

    # ─── Routing Logic ───────────────────────────────────────────────────────

    def route(self, alert: Alert) -> dict[str, Any]:
        """
        Determine the routing plan for an alert.

        Returns a dict with:
        - channels: list of channels to use
        - recipients: list of recipients
        - priority: notification priority
        - escalation_target: who to escalate to if unacknowledged
        - escalation_delay_minutes: how long to wait before escalation
        """
        routing_plan = {
            "channels": [],
            "recipients": [],
            "priority": self._severity_to_priority(alert.severity),
            "escalation_target": None,
            "escalation_delay_minutes": 60,
            "reasoning": [],
        }

        # Apply custom routing rules first
        for rule in self._routing_rules:
            if not rule.enabled:
                continue
            if self._matches_rule(alert, rule):
                routing_plan["channels"].extend(rule.channels)
                routing_plan["recipients"].extend(rule.recipients)
                routing_plan["reasoning"].append(f"Matched rule: {rule.name}")

        # Apply severity-based defaults
        severity_channels = self._severity_channels.get(alert.severity.value, ["email"])
        for ch in severity_channels:
            if ch not in routing_plan["channels"]:
                routing_plan["channels"].append(ch)

        # Framework-specific routing
        if alert.framework:
            owner = self._framework_owners.get(alert.framework)
            if owner and owner not in routing_plan["recipients"]:
                routing_plan["recipients"].append(owner)
                routing_plan["reasoning"].append(f"Framework owner: {alert.framework}")

        # Entity-type routing
        entity_recipients = self._route_by_entity_type(alert)
        for r in entity_recipients:
            if r not in routing_plan["recipients"]:
                routing_plan["recipients"].append(r)

        # Time-based routing
        if not self._is_business_hours():
            # After hours: route to on-call
            on_call = self._get_on_call(alert)
            if on_call and on_call not in routing_plan["recipients"]:
                routing_plan["recipients"].append(on_call)
                routing_plan["reasoning"].append("After-hours: routed to on-call")
            # After hours: escalate critical alerts faster
            if alert.severity == AlertSeverity.CRITICAL:
                routing_plan["escalation_delay_minutes"] = 15
                routing_plan["reasoning"].append("After-hours critical: faster escalation")

        # Escalation chain
        chain = self._escalation_chains.get(alert.severity.value, [])
        if chain:
            routing_plan["escalation_target"] = chain[0] if chain else None
            routing_plan["reasoning"].append(f"Escalation chain: {len(chain)} levels")

        # Deduplicate
        routing_plan["channels"] = list(dict.fromkeys(routing_plan["channels"]))
        routing_plan["recipients"] = list(dict.fromkeys(routing_plan["recipients"]))

        return routing_plan

    def create_notification(self, alert: Alert) -> Notification:
        """Create a notification from an alert using the routing plan."""
        plan = self.route(alert)

        priority_map = {
            "critical": NotificationPriority.CRITICAL,
            "high": NotificationPriority.HIGH,
            "medium": NotificationPriority.MEDIUM,
            "low": NotificationPriority.LOW,
            "info": NotificationPriority.INFO,
        }

        notification = Notification(
            type=NotificationType.COMPLIANCE_VIOLATION,
            priority=priority_map.get(alert.severity.value, NotificationPriority.MEDIUM),
            title=f"[{alert.severity.value.upper()}] {alert.title}",
            body=alert.description,
            summary=alert.title,
            source="alert_router",
            source_id=alert.id,
            tags=alert.tags + [alert.framework] if alert.framework else alert.tags,
            channels=plan["channels"],
            recipients=plan["recipients"],
            metadata={
                "alert_id": alert.id,
                "severity": alert.severity.value,
                "framework": alert.framework,
                "entity_type": alert.entity_type,
                "entity_id": alert.entity_id,
                "control_id": alert.control_id,
                "runbook_url": alert.runbook_url,
                "routing_reasoning": plan["reasoning"],
            },
            correlation_id=alert.id,
        )

        return notification

    def should_escalate(self, alert: Alert) -> bool:
        """Check if an alert should be escalated based on time and status."""
        if alert.status not in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED):
            return False

        if not alert.acknowledged_at:
            # Never acknowledged — check creation time
            created = datetime.fromisoformat(alert.created_at.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - created).total_seconds() / 60
            threshold = self._get_escalation_threshold(alert.severity)
            return elapsed >= threshold

        # Acknowledged but not resolved — check ack time
        ack_time = datetime.fromisoformat(alert.acknowledged_at.replace("Z", "+00:00"))
        elapsed = (datetime.now(timezone.utc) - ack_time).total_seconds() / 60
        threshold = self._get_escalation_threshold(alert.severity) * 2
        return elapsed >= threshold

    def escalate(self, alert: Alert) -> Optional[Alert]:
        """Escalate an alert to the next level in the escalation chain."""
        chain = self._escalation_chains.get(alert.severity.value, [])
        if not chain:
            return None

        current_target = alert.escalated_to or alert.assigned_to
        next_target = None

        if current_target in chain:
            idx = chain.index(current_target)
            if idx + 1 < len(chain):
                next_target = chain[idx + 1]
        else:
            next_target = chain[0]

        if next_target:
            alert.escalated_to = next_target
            alert.status = AlertStatus.ESCALATED
            alert.updated_at = datetime.now(timezone.utc).isoformat()

            self._escalation_history.append({
                "alert_id": alert.id,
                "from": current_target,
                "to": next_target,
                "timestamp": alert.updated_at,
                "severity": alert.severity.value,
            })

            logger.warning(f"Escalated alert {alert.id} to {next_target}")
            return alert

        return None

    # ─── Helper Methods ──────────────────────────────────────────────────────

    def _severity_to_priority(self, severity: AlertSeverity) -> str:
        """Map alert severity to notification priority."""
        mapping = {
            AlertSeverity.CRITICAL: "critical",
            AlertSeverity.HIGH: "high",
            AlertSeverity.MEDIUM: "medium",
            AlertSeverity.LOW: "low",
            AlertSeverity.INFO: "info",
        }
        return mapping.get(severity, "medium")

    def _matches_rule(self, alert: Alert, rule: RoutingRule) -> bool:
        """Check if an alert matches a routing rule."""
        conditions = rule.conditions
        if not conditions:
            return True

        for key, value in conditions.items():
            if key == "severity":
                if alert.severity.value not in (value if isinstance(value, list) else [value]):
                    return False
            elif key == "framework":
                if alert.framework != value:
                    return False
            elif key == "entity_type":
                if alert.entity_type != value:
                    return False
            elif key == "status":
                if alert.status.value not in (value if isinstance(value, list) else [value]):
                    return False
            elif key == "tags":
                tags = value if isinstance(value, list) else [value]
                if not any(t in alert.tags for t in tags):
                    return False
        return True

    def _route_by_entity_type(self, alert: Alert) -> list[str]:
        """Route based on the entity type of the alert."""
        recipients = []
        entity_type = alert.entity_type

        if entity_type == "policy":
            recipients.extend(self._team_mappings.get("policy_team", []))
        elif entity_type == "control":
            recipients.extend(self._team_mappings.get("control_team", []))
        elif entity_type == "evidence":
            recipients.extend(self._team_mappings.get("compliance_team", []))
        elif entity_type == "framework":
            recipients.extend(self._team_mappings.get("governance_team", []))
        elif entity_type == "incident":
            recipients.extend(self._team_mappings.get("incident_response", []))
            if alert.severity in (AlertSeverity.CRITICAL, AlertSeverity.HIGH):
                recipients.extend(self._team_mappings.get("security_team", []))

        return recipients

    def _is_business_hours(self) -> bool:
        """Check if current time is within business hours."""
        now = datetime.now(timezone.utc)
        if now.weekday() not in self._business_days:
            return False
        return self._business_hours["start"] <= now.hour < self._business_hours["end"]

    def _get_on_call(self, alert: Alert) -> Optional[str]:
        """Get the on-call person for the alert's team."""
        if alert.entity_type == "incident":
            return self._on_call.get("incident_response")
        elif alert.entity_type == "policy":
            return self._on_call.get("policy_team")
        elif alert.entity_type == "control":
            return self._on_call.get("control_team")
        return self._on_call.get("default")

    def _get_escalation_threshold(self, severity: AlertSeverity) -> int:
        """Get the escalation threshold in minutes for a severity."""
        thresholds = {
            AlertSeverity.CRITICAL: 15,
            AlertSeverity.HIGH: 60,
            AlertSeverity.MEDIUM: 240,
            AlertSeverity.LOW: 1440,
            AlertSeverity.INFO: 10080,
        }
        return thresholds.get(severity, 60)

    # ─── Analytics ───────────────────────────────────────────────────────────

    def get_routing_summary(self) -> dict[str, Any]:
        """Get a summary of routing configuration."""
        return {
            "routing_rules": len(self._routing_rules),
            "escalation_chains": {k: len(v) for k, v in self._escalation_chains.items()},
            "on_call": dict(self._on_call),
            "team_mappings": {k: len(v) for k, v in self._team_mappings.items()},
            "framework_owners": dict(self._framework_owners),
            "severity_channels": dict(self._severity_channels),
            "escalation_history_count": len(self._escalation_history),
        }

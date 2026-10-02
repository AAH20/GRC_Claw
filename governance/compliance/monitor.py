"""Real-time compliance monitoring for agent governance.

Provides continuous monitoring of agent activities against compliance
policies, with event tracking, alerting, and status reporting.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ComplianceStatus(str, Enum):
    """Compliance status levels."""

    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComplianceEvent(str, Enum):
    """Types of compliance events."""

    POLICY_VIOLATION = "policy_violation"
    POLICY_WARNING = "policy_warning"
    TRUST_DROP = "trust_drop"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH_RISK = "data_breach_risk"
    BUDGET_OVERRUN = "budget_overrun"
    CONTENT_VIOLATION = "content_violation"
    CHANNEL_VIOLATION = "channel_violation"
    ANOMALY_DETECTED = "anomaly_detected"
    CERT_EXPIRING = "cert_expiring"


@dataclass
class ComplianceIncident:
    """A compliance incident record."""

    id: str
    event_type: ComplianceEvent
    agent_id: str
    severity: ComplianceStatus
    description: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolution: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "severity": self.severity.value,
            "description": self.description,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at,
            "resolution": self.resolution,
            "metadata": self.metadata,
        }


class ComplianceMonitor:
    """Real-time compliance monitor.

    Tracks agent activities, detects compliance violations,
    and maintains compliance status across the agent fleet.
    """

    def __init__(
        self,
        alert_threshold: int = 5,
        window_seconds: float = 3600.0,
    ) -> None:
        """Initialize the compliance monitor.

        Args:
            alert_threshold: Events before triggering an alert.
            window_seconds: Time window for event counting.
        """
        self._alert_threshold = alert_threshold
        self._window_seconds = window_seconds
        self._incidents: Dict[str, ComplianceIncident] = {}
        self._agent_events: Dict[str, List[ComplianceIncident]] = {}
        self._agent_status: Dict[str, ComplianceStatus] = {}
        self._alert_handlers: List[Callable[[ComplianceIncident], None]] = []
        self._event_counts: Dict[str, List[float]] = {}

    @property
    def alert_threshold(self) -> int:
        """Get the alert threshold."""
        return self._alert_threshold

    def record_event(
        self,
        event_type: ComplianceEvent,
        agent_id: str,
        severity: ComplianceStatus,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ComplianceIncident:
        """Record a compliance event.

        Args:
            event_type: Type of compliance event.
            agent_id: The agent identifier.
            severity: Severity level.
            description: Event description.
            metadata: Optional metadata.

        Returns:
            The created compliance incident.
        """
        import uuid

        incident = ComplianceIncident(
            id=str(uuid.uuid4()),
            event_type=event_type,
            agent_id=agent_id,
            severity=severity,
            description=description,
            timestamp=time.time(),
            metadata=metadata or {},
        )

        self._incidents[incident.id] = incident
        self._agent_events.setdefault(agent_id, []).append(incident)
        self._event_counts.setdefault(agent_id, []).append(time.time())

        # Update agent status
        self._update_agent_status(agent_id)

        # Check alert threshold
        self._check_alert_threshold(agent_id)

        # Notify handlers
        for handler in self._alert_handlers:
            try:
                handler(incident)
            except Exception as exc:
                logger.warning("Alert handler failed: %s", exc)

        return incident

    def _update_agent_status(self, agent_id: str) -> None:
        """Update the compliance status for an agent."""
        events = self._agent_events.get(agent_id, [])
        if not events:
            self._agent_status[agent_id] = ComplianceStatus.COMPLIANT
            return

        # Count recent events by severity
        now = time.time()
        recent = [
            e for e in events
            if now - e.timestamp < self._window_seconds
        ]

        critical_count = sum(
            1 for e in recent if e.severity == ComplianceStatus.CRITICAL
        )
        violation_count = sum(
            1 for e in recent if e.severity == ComplianceStatus.VIOLATION
        )
        warning_count = sum(
            1 for e in recent if e.severity == ComplianceStatus.WARNING
        )

        if critical_count > 0:
            self._agent_status[agent_id] = ComplianceStatus.CRITICAL
        elif violation_count >= self._alert_threshold:
            self._agent_status[agent_id] = ComplianceStatus.VIOLATION
        elif warning_count >= self._alert_threshold:
            self._agent_status[agent_id] = ComplianceStatus.WARNING
        else:
            self._agent_status[agent_id] = ComplianceStatus.COMPLIANT

    def _check_alert_threshold(self, agent_id: str) -> None:
        """Check if an agent has exceeded the alert threshold."""
        now = time.time()
        events = self._event_counts.get(agent_id, [])
        recent = [t for t in events if now - t < self._window_seconds]

        if len(recent) >= self._alert_threshold:
            logger.warning(
                "Agent %s exceeded compliance alert threshold: %d events",
                agent_id,
                len(recent),
            )

    def resolve_incident(
        self,
        incident_id: str,
        resolution: str,
    ) -> Optional[ComplianceIncident]:
        """Resolve a compliance incident.

        Args:
            incident_id: The incident identifier.
            resolution: Resolution description.

        Returns:
            The resolved incident or None.
        """
        incident = self._incidents.get(incident_id)
        if not incident:
            return None

        incident.resolved = True
        incident.resolved_at = time.time()
        incident.resolution = resolution

        self._update_agent_status(incident.agent_id)
        return incident

    def get_agent_status(self, agent_id: str) -> ComplianceStatus:
        """Get the compliance status for an agent.

        Args:
            agent_id: The agent identifier.

        Returns:
            The compliance status.
        """
        return self._agent_status.get(agent_id, ComplianceStatus.UNKNOWN)

    def get_incidents(
        self,
        agent_id: Optional[str] = None,
        severity: Optional[ComplianceStatus] = None,
        resolved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[ComplianceIncident]:
        """Get compliance incidents with optional filtering.

        Args:
            agent_id: Filter by agent.
            severity: Filter by severity.
            resolved: Filter by resolution status.
            limit: Maximum results.

        Returns:
            List of compliance incidents.
        """
        results = list(self._incidents.values())

        if agent_id:
            results = [i for i in results if i.agent_id == agent_id]
        if severity:
            results = [i for i in results if i.severity == severity]
        if resolved is not None:
            results = [i for i in results if i.resolved == resolved]

        results.sort(key=lambda i: i.timestamp, reverse=True)
        return results[:limit]

    def on_alert(self, handler: Callable[[ComplianceIncident], None]) -> None:
        """Register an alert handler.

        Args:
            handler: Callable to invoke on alerts.
        """
        self._alert_handlers.append(handler)

    def get_summary(self) -> Dict[str, Any]:
        """Get a compliance summary.

        Returns:
            Summary statistics.
        """
        total = len(self._incidents)
        unresolved = sum(1 for i in self._incidents.values() if not i.resolved)
        by_severity: Dict[str, int] = {}
        by_agent: Dict[str, int] = {}

        for incident in self._incidents.values():
            sev = incident.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_agent[incident.agent_id] = by_agent.get(incident.agent_id, 0) + 1

        return {
            "total_incidents": total,
            "unresolved_incidents": unresolved,
            "by_severity": by_severity,
            "by_agent": by_agent,
            "agent_statuses": {
                aid: status.value
                for aid, status in self._agent_status.items()
            },
        }

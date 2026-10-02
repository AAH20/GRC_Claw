"""UEBA and agent anomaly detection for agentic AI marketing security layer.

Provides user and entity behavior analytics, agent anomaly detection,
behavioral baselining, and threat detection.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from audit.events import AuditEvent, AuditEventType


class DetectionError(Exception):
    """Base exception for detection errors."""


class ModelNotTrainedError(DetectionError):
    """Raised when model is not trained."""


class ThreatLevel(str, Enum):
    """Threat severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Types of anomalies."""

    STATISTICAL = "statistical"
    BEHAVIORAL = "behavioral"
    TEMPORAL = "temporal"
    GEOGRAPHIC = "geographic"
    VOLUME = "volume"
    PATTERN = "pattern"
    SIGNATURE = "signature"


@dataclass(frozen=True)
class BehavioralProfile:
    """Behavioral profile for an entity."""

    entity_id: str
    entity_type: str
    created_at: float
    updated_at: float
    features: Dict[str, Any] = field(default_factory=dict)
    baselines: Dict[str, Dict[str, float]] = field(default_factory=dict)
    typical_hours: List[int] = field(default_factory=list)
    typical_locations: List[str] = field(default_factory=list)
    common_actions: List[str] = field(default_factory=list)
    peer_group: Optional[str] = None
    risk_score: float = 0.0


@dataclass(frozen=True)
class Anomaly:
    """Detected anomaly."""

    id: str
    entity_id: str
    anomaly_type: AnomalyType
    threat_level: ThreatLevel
    score: float
    timestamp: float
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    related_events: List[str] = field(default_factory=list)
    recommended_action: Optional[str] = None


@dataclass(frozen=True)
class ThreatIndicator:
    """Threat indicator."""

    id: str
    type: str
    value: str
    confidence: float
    first_seen: float
    last_seen: float
    source: str
    description: str
    related_entities: List[str] = field(default_factory=list)


class StatisticalBaseline:
    """Statistical baseline for anomaly detection."""

    def __init__(self, window_size: int = 100) -> None:
        self.window_size = window_size
        self._values: List[float] = []
        self._mean: float = 0.0
        self._std: float = 0.0
        self._min: float = float("inf")
        self._max: float = float("-inf")

    def update(self, value: float) -> None:
        """Update baseline with a new value."""
        self._values.append(value)
        if len(self._values) > self.window_size:
            self._values.pop(0)

        if len(self._values) >= 2:
            self._mean = statistics.mean(self._values)
            self._std = statistics.stdev(self._values) if len(self._values) > 1 else 0.0
        else:
            self._mean = value
            self._std = 0.0

        self._min = min(self._min, value)
        self._max = max(self._max, value)

    def is_anomaly(self, value: float, threshold: float = 3.0) -> Tuple[bool, float]:
        """Check if a value is anomalous."""
        if self._std == 0:
            return False, 0.0

        z_score = abs(value - self._mean) / self._std
        return z_score > threshold, z_score

    def get_stats(self) -> Dict[str, float]:
        """Get baseline statistics."""
        return {
            "mean": self._mean,
            "std": self._std,
            "min": self._min,
            "max": self._max,
            "count": len(self._values),
        }


class UEBAEngine:
    """User and Entity Behavior Analytics engine."""

    def __init__(self) -> None:
        self._profiles: Dict[str, BehavioralProfile] = {}
        self._baselines: Dict[str, StatisticalBaseline] = defaultdict(
            lambda: StatisticalBaseline()
        )
        self._anomalies: List[Anomaly] = []
        self._event_counts: Dict[str, List[float]] = defaultdict(list)

    def process_event(self, event: AuditEvent) -> Optional[Anomaly]:
        """Process an audit event and detect anomalies."""
        if not event.actor:
            return None

        entity_id = event.actor.id
        self._update_event_count(entity_id, event.timestamp)

        # Update or create profile
        profile = self._get_or_create_profile(entity_id, event.actor.type)

        # Check for anomalies
        anomaly = self._detect_anomalies(event, profile)
        if anomaly:
            self._anomalies.append(anomaly)

        return anomaly

    def _get_or_create_profile(
        self,
        entity_id: str,
        entity_type: str,
    ) -> BehavioralProfile:
        """Get or create a behavioral profile."""
        if entity_id not in self._profiles:
            self._profiles[entity_id] = BehavioralProfile(
                entity_id=entity_id,
                entity_type=entity_type,
                created_at=time.time(),
                updated_at=time.time(),
            )
        return self._profiles[entity_id]

    def _update_event_count(self, entity_id: str, timestamp: float) -> None:
        """Update event count for rate-based detection."""
        self._event_counts[entity_id].append(timestamp)
        # Keep only last hour
        cutoff = timestamp - 3600
        self._event_counts[entity_id] = [
            t for t in self._event_counts[entity_id] if t > cutoff
        ]

    def _detect_anomalies(
        self,
        event: AuditEvent,
        profile: BehavioralProfile,
    ) -> Optional[Anomaly]:
        """Detect anomalies for an event."""
        # Check event rate
        rate = len(self._event_counts.get(event.actor.id, []))
        rate_baseline = self._baselines[f"{event.actor.id}:rate"]
        rate_baseline.update(rate)

        is_anomalous, z_score = rate_baseline.is_anomaly(rate)
        if is_anomalous and z_score > 3.0:
            return Anomaly(
                id=self._generate_id(),
                entity_id=event.actor.id,
                anomaly_type=AnomalyType.VOLUME,
                threat_level=ThreatLevel.HIGH if z_score > 5 else ThreatLevel.MEDIUM,
                score=min(z_score / 10, 1.0),
                timestamp=event.timestamp,
                description=f"Unusual event rate: {rate} events/hour (z-score: {z_score:.2f})",
                evidence={"event_count": rate, "z_score": z_score},
                related_events=[event.id],
            )

        # Check for off-hours activity
        hour = time.localtime(event.timestamp).tm_hour
        if profile.typical_hours and hour not in profile.typical_hours:
            return Anomaly(
                id=self._generate_id(),
                entity_id=event.actor.id,
                anomaly_type=AnomalyType.TEMPORAL,
                threat_level=ThreatLevel.LOW,
                score=0.3,
                timestamp=event.timestamp,
                description=f"Activity outside typical hours: {hour}:00",
                evidence={"hour": hour, "typical_hours": profile.typical_hours},
                related_events=[event.id],
            )

        return None

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique anomaly ID."""
        return hashlib.sha256(
            f"{time.time()}-{id(object())}".encode()
        ).hexdigest()[:16]


class AgentAnomalyDetector:
    """Anomaly detection specifically for AI agents."""

    def __init__(self) -> None:
        self._agent_profiles: Dict[str, Dict[str, Any]] = {}
        self._action_sequences: Dict[str, List[str]] = defaultdict(list)
        self._suspicious_patterns: List[Dict[str, Any]] = []

    def analyze_agent_action(self, event: AuditEvent) -> Optional[Anomaly]:
        """Analyze an agent action for anomalies."""
        if not event.actor or event.actor.type != "agent":
            return None

        agent_id = event.actor.id

        # Track action sequence
        if event.action:
            self._action_sequences[agent_id].append(event.action.name)

        # Check for suspicious patterns
        anomaly = self._check_suspicious_patterns(agent_id, event)
        if anomaly:
            return anomaly

        # Check for privilege escalation
        anomaly = self._check_privilege_escalation(agent_id, event)
        if anomaly:
            return anomaly

        # Check for data exfiltration patterns
        anomaly = self._check_data_exfiltration(agent_id, event)
        if anomaly:
            return anomaly

        return None

    def _check_suspicious_patterns(
        self,
        agent_id: str,
        event: AuditEvent,
    ) -> Optional[Anomaly]:
        """Check for suspicious action patterns."""
        sequence = self._action_sequences[agent_id]

        # Check for rapid repeated actions
        if len(sequence) >= 10:
            recent = sequence[-10:]
            if len(set(recent)) == 1:
                return Anomaly(
                    id=hashlib.sha256(f"{agent_id}-{time.time()}".encode()).hexdigest()[:16],
                    entity_id=agent_id,
                    anomaly_type=AnomalyType.PATTERN,
                    threat_level=ThreatLevel.MEDIUM,
                    score=0.6,
                    timestamp=event.timestamp,
                    description=f"Repetitive action pattern detected: {recent[0]}",
                    evidence={"pattern": recent},
                    related_events=[event.id],
                )

        return None

    def _check_privilege_escalation(
        self,
        agent_id: str,
        event: AuditEvent,
    ) -> Optional[Anomaly]:
        """Check for privilege escalation attempts."""
        if event.type == AuditEventType.AUTHORIZATION and event.outcome.value == "failure":
            profile = self._agent_profiles.setdefault(agent_id, {
                "failed_auth_count": 0,
                "last_failed_auth": 0,
            })
            profile["failed_auth_count"] += 1
            profile["last_failed_auth"] = event.timestamp

            if profile["failed_auth_count"] >= 5:
                return Anomaly(
                    id=hashlib.sha256(f"{agent_id}-priv-esc-{time.time()}".encode()).hexdigest()[:16],
                    entity_id=agent_id,
                    anomaly_type=AnomalyType.BEHAVIORAL,
                    threat_level=ThreatLevel.HIGH,
                    score=0.8,
                    timestamp=event.timestamp,
                    description=f"Multiple authorization failures: {profile['failed_auth_count']}",
                    evidence={"failed_count": profile["failed_auth_count"]},
                    related_events=[event.id],
                    recommended_action="Review agent permissions and investigate",
                )

        return None

    def _check_data_exfiltration(
        self,
        agent_id: str,
        event: AuditEvent,
    ) -> Optional[Anomaly]:
        """Check for data exfiltration patterns."""
        if event.type != AuditEventType.DATA_ACCESS:
            return None

        profile = self._agent_profiles.setdefault(agent_id, {
            "data_access_count": 0,
            "data_access_volume": 0,
            "last_access": 0,
        })

        profile["data_access_count"] += 1
        profile["last_access"] = event.timestamp

        # Check for unusual data access volume
        if profile["data_access_count"] > 100:
            return Anomaly(
                id=hashlib.sha256(f"{agent_id}-exfil-{time.time()}".encode()).hexdigest()[:16],
                entity_id=agent_id,
                anomaly_type=AnomalyType.VOLUME,
                threat_level=ThreatLevel.HIGH,
                score=0.7,
                timestamp=event.timestamp,
                description=f"High data access volume: {profile['data_access_count']} accesses",
                evidence={"access_count": profile["data_access_count"]},
                related_events=[event.id],
                recommended_action="Review data access patterns",
            )

        return None


class ThreatDetectionEngine:
    """Main threat detection engine."""

    def __init__(self) -> None:
        self.ueba = UEBAEngine()
        self.agent_detector = AgentAnomalyDetector()
        self._threat_indicators: Dict[str, ThreatIndicator] = {}
        self._detection_rules: List[Dict[str, Any]] = []

    def add_detection_rule(self, rule: Dict[str, Any]) -> None:
        """Add a detection rule."""
        self._detection_rules.append(rule)

    def process_event(self, event: AuditEvent) -> List[Anomaly]:
        """Process an event through all detection engines."""
        anomalies: List[Anomaly] = []

        # UEBA detection
        ueba_anomaly = self.ueba.process_event(event)
        if ueba_anomaly:
            anomalies.append(ueba_anomaly)

        # Agent-specific detection
        agent_anomaly = self.agent_detector.analyze_agent_action(event)
        if agent_anomaly:
            anomalies.append(agent_anomaly)

        # Custom rule detection
        for rule in self._detection_rules:
            if self._evaluate_rule(rule, event):
                anomalies.append(
                    Anomaly(
                        id=hashlib.sha256(f"{rule['name']}-{time.time()}".encode()).hexdigest()[:16],
                        entity_id=event.actor.id if event.actor else "unknown",
                        anomaly_type=AnomalyType.SIGNATURE,
                        threat_level=ThreatLevel(rule.get("severity", "medium")),
                        score=rule.get("score", 0.5),
                        timestamp=event.timestamp,
                        description=rule.get("description", "Rule match"),
                        evidence={"rule": rule["name"]},
                        related_events=[event.id],
                    )
                )

        return anomalies

    def _evaluate_rule(self, rule: Dict[str, Any], event: AuditEvent) -> bool:
        """Evaluate a detection rule against an event."""
        conditions = rule.get("conditions", [])
        return all(self._evaluate_condition(c, event) for c in conditions)

    def _evaluate_condition(self, condition: Dict[str, Any], event: AuditEvent) -> bool:
        """Evaluate a single condition."""
        field = condition.get("field", "")
        operator = condition.get("operator", "eq")
        value = condition.get("value")

        # Get field value from event
        event_dict = event.to_dict()
        field_value = event_dict.get(field)

        if operator == "eq":
            return field_value == value
        elif operator == "ne":
            return field_value != value
        elif operator == "contains":
            return value in str(field_value)
        elif operator == "gt":
            return field_value is not None and field_value > value
        elif operator == "lt":
            return field_value is not None and field_value < value

        return False

    def get_threat_summary(self) -> Dict[str, Any]:
        """Get summary of detected threats."""
        return {
            "total_anomalies": len(self.ueba._anomalies),
            "active_threat_indicators": len(self._threat_indicators),
            "detection_rules": len(self._detection_rules),
            "profiles_tracked": len(self.ueba._profiles),
        }

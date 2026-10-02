"""Trust scoring engine for AI agents.

Computes and manages trust scores based on behavioral history,
compliance record, and operational metrics.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TrustError(Exception):
    """Base exception for trust operations."""


class TrustLevel(str, Enum):
    """Trust level classifications."""

    UNTRUSTED = "untrusted"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


@dataclass
class TrustFactor:
    """A single trust factor with weight and score."""

    name: str
    weight: float
    score: float  # 0.0 to 1.0
    description: str = ""
    last_updated: float = field(default_factory=time.time)

    @property
    def weighted_score(self) -> float:
        """Get the weighted contribution to the trust score."""
        return self.weight * self.score


@dataclass
class TrustScore:
    """Composite trust score for an agent."""

    agent_id: str
    overall_score: float  # 0.0 to 1.0
    level: TrustLevel
    factors: Dict[str, TrustFactor]
    computed_at: float
    expires_at: float
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "agent_id": self.agent_id,
            "overall_score": self.overall_score,
            "level": self.level.value,
            "factors": {
                name: {
                    "name": f.name,
                    "weight": f.weight,
                    "score": f.score,
                    "description": f.description,
                    "last_updated": f.last_updated,
                }
                for name, f in self.factors.items()
            },
            "computed_at": self.computed_at,
            "expires_at": self.expires_at,
            "history": self.history,
        }


class TrustEngine:
    """Engine for computing and managing agent trust scores.

    Uses a weighted multi-factor model to compute trust scores
    that determine an agent's operational privileges.
    """

    DEFAULT_FACTORS: Dict[str, Dict[str, Any]] = {
        "behavioral": {
            "weight": 0.30,
            "description": "Historical behavior patterns and anomaly rate",
        },
        "compliance": {
            "weight": 0.25,
            "description": "Policy compliance and violation history",
        },
        "operational": {
            "weight": 0.20,
            "description": "Uptime, latency, and reliability metrics",
        },
        "security": {
            "weight": 0.15,
            "description": "Security posture and incident history",
        },
        "verification": {
            "weight": 0.10,
            "description": "Identity verification and attestation status",
        },
    }

    LEVEL_THRESHOLDS: Dict[TrustLevel, float] = {
        TrustLevel.UNTRUSTED: 0.0,
        TrustLevel.LOW: 0.25,
        TrustLevel.MEDIUM: 0.50,
        TrustLevel.HIGH: 0.75,
        TrustLevel.VERIFIED: 0.90,
    }

    def __init__(
        self,
        ttl_seconds: float = 3600.0,
        decay_rate: float = 0.01,
        factor_config: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """Initialize the trust engine.

        Args:
            ttl_seconds: Time-to-live for computed trust scores.
            decay_rate: Rate at which trust decays over time.
            factor_config: Custom factor configuration.
        """
        self._ttl = ttl_seconds
        self._decay_rate = decay_rate
        self._factor_config = factor_config or self.DEFAULT_FACTORS
        self._scores: Dict[str, TrustScore] = {}
        self._violation_counts: Dict[str, List[float]] = {}
        self._behavioral_events: Dict[str, List[Dict[str, Any]]] = {}

    def compute_score(self, agent_id: str) -> TrustScore:
        """Compute the trust score for an agent.

        Args:
            agent_id: The agent identifier.

        Returns:
            The computed trust score.
        """
        now = time.time()
        factors: Dict[str, TrustFactor] = {}

        for name, config in self._factor_config.items():
            score = self._compute_factor_score(agent_id, name, now)
            factors[name] = TrustFactor(
                name=name,
                weight=config["weight"],
                score=score,
                description=config.get("description", ""),
                last_updated=now,
            )

        overall = self._compute_overall(factors)
        level = self._classify_level(overall)

        # Apply time decay
        if agent_id in self._scores:
            old_score = self._scores[agent_id]
            elapsed = now - old_score.computed_at
            decay = math.exp(-self._decay_rate * elapsed / 3600.0)
            overall *= decay
            level = self._classify_level(overall)

        trust_score = TrustScore(
            agent_id=agent_id,
            overall_score=round(overall, 4),
            level=level,
            factors=factors,
            computed_at=now,
            expires_at=now + self._ttl,
            history=self._scores.get(agent_id, TrustScore(
                agent_id=agent_id,
                overall_score=0.0,
                level=TrustLevel.UNTRUSTED,
                factors={},
                computed_at=0,
                expires_at=0,
            )).history[-10:] if agent_id in self._scores else [],
        )

        self._scores[agent_id] = trust_score
        return trust_score

    def _compute_factor_score(
        self, agent_id: str, factor_name: str, now: float
    ) -> float:
        """Compute a single factor score."""
        if factor_name == "behavioral":
            return self._behavioral_score(agent_id, now)
        elif factor_name == "compliance":
            return self._compliance_score(agent_id, now)
        elif factor_name == "operational":
            return self._operational_score(agent_id, now)
        elif factor_name == "security":
            return self._security_score(agent_id, now)
        elif factor_name == "verification":
            return self._verification_score(agent_id, now)
        return 0.5

    def _behavioral_score(self, agent_id: str, now: float) -> float:
        """Compute behavioral score from event history."""
        events = self._behavioral_events.get(agent_id, [])
        if not events:
            return 0.5

        # Score based on recent anomaly rate
        recent = [e for e in events if now - e["timestamp"] < 86400]
        if not recent:
            return 0.7

        anomalies = sum(1 for e in recent if e.get("is_anomaly", False))
        anomaly_rate = anomalies / len(recent)
        return max(0.0, 1.0 - anomaly_rate * 2.0)

    def _compliance_score(self, agent_id: str, now: float) -> float:
        """Compute compliance score from violation history."""
        violations = self._violation_counts.get(agent_id, [])
        if not violations:
            return 1.0

        # Count violations in last 30 days
        recent = [v for v in violations if now - v < 30 * 86400]
        if not recent:
            return 0.9

        # Exponential decay based on violation count
        return max(0.0, math.exp(-0.1 * len(recent)))

    def _operational_score(self, agent_id: str, now: float) -> float:
        """Compute operational reliability score."""
        # Placeholder: would integrate with monitoring data
        return 0.8

    def _security_score(self, agent_id: str, now: float) -> float:
        """Compute security posture score."""
        # Placeholder: would integrate with security events
        return 0.9

    def _verification_score(self, agent_id: str, now: float) -> float:
        """Compute identity verification score."""
        # Placeholder: would check DID verification status
        return 0.85

    def _compute_overall(self, factors: Dict[str, TrustFactor]) -> float:
        """Compute the overall trust score from factors."""
        total_weight = sum(f.weight for f in factors.values())
        if total_weight == 0:
            return 0.0
        weighted_sum = sum(f.weighted_score for f in factors.values())
        return min(1.0, max(0.0, weighted_sum / total_weight))

    def _classify_level(self, score: float) -> TrustLevel:
        """Classify a numeric score into a trust level."""
        for level in reversed(TrustLevel):
            threshold = self.LEVEL_THRESHOLDS[level]
            if score >= threshold:
                return level
        return TrustLevel.UNTRUSTED

    def record_violation(
        self, agent_id: str, violation_type: str, severity: float = 1.0
    ) -> None:
        """Record a compliance violation.

        Args:
            agent_id: The agent identifier.
            violation_type: Type of violation.
            severity: Severity weight (0.0 to 1.0).
        """
        now = time.time()
        self._violation_counts.setdefault(agent_id, []).append(now)

        # Record as behavioral event too
        self._behavioral_events.setdefault(agent_id, []).append(
            {
                "timestamp": now,
                "type": "violation",
                "violation_type": violation_type,
                "severity": severity,
                "is_anomaly": severity > 0.5,
            }
        )

    def record_behavioral_event(
        self,
        agent_id: str,
        event_type: str,
        is_anomaly: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a behavioral event.

        Args:
            agent_id: The agent identifier.
            event_type: Type of event.
            is_anomaly: Whether the event is anomalous.
            metadata: Optional event metadata.
        """
        self._behavioral_events.setdefault(agent_id, []).append(
            {
                "timestamp": time.time(),
                "type": event_type,
                "is_anomaly": is_anomaly,
                "metadata": metadata or {},
            }
        )

    def get_score(self, agent_id: str) -> Optional[TrustScore]:
        """Get the cached trust score if valid.

        Args:
            agent_id: The agent identifier.

        Returns:
            The cached trust score or None if expired/missing.
        """
        score = self._scores.get(agent_id)
        if score and time.time() < score.expires_at:
            return score
        return None

    def is_trusted(
        self, agent_id: str, minimum_level: TrustLevel = TrustLevel.MEDIUM
    ) -> bool:
        """Check if an agent meets a minimum trust level.

        Args:
            agent_id: The agent identifier.
            minimum_level: Minimum required trust level.

        Returns:
            True if the agent meets the minimum trust level.
        """
        score = self.get_score(agent_id)
        if not score:
            score = self.compute_score(agent_id)
        return score.overall_score >= self.LEVEL_THRESHOLDS[minimum_level]

    def reset(self, agent_id: str) -> None:
        """Reset trust data for an agent.

        Args:
            agent_id: The agent identifier.
        """
        self._scores.pop(agent_id, None)
        self._violation_counts.pop(agent_id, None)
        self._behavioral_events.pop(agent_id, None)

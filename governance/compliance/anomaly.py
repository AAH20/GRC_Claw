"""ML-based anomaly detection for agent governance.

Provides statistical and ML-based anomaly detection for identifying
unusual agent behavior patterns that may indicate security threats
or policy violations.
"""

from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AnomalyType(str, Enum):
    """Types of anomalies."""

    BEHAVIORAL = "behavioral"
    STATISTICAL = "statistical"
    TEMPORAL = "temporal"
    VOLUME = "volume"
    PATTERN = "pattern"


class AnomalySeverity(str, Enum):
    """Anomaly severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""

    is_anomaly: bool
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    description: str
    features: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "is_anomaly": self.is_anomaly,
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "score": self.score,
            "confidence": self.confidence,
            "description": self.description,
            "features": self.features,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class AnomalyDetector:
    """ML-based anomaly detector for agent behavior.

    Uses statistical methods (z-score, IQR) and behavioral profiling
    to detect anomalous agent activities.
    """

    def __init__(
        self,
        z_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
        min_samples: int = 10,
        window_size: int = 100,
    ) -> None:
        """Initialize the anomaly detector.

        Args:
            z_threshold: Z-score threshold for statistical anomalies.
            iqr_multiplier: IQR multiplier for outlier detection.
            min_samples: Minimum samples before detection is reliable.
            window_size: Sliding window size for behavioral profiles.
        """
        self._z_threshold = z_threshold
        self._iqr_multiplier = iqr_multiplier
        self._min_samples = min_samples
        self._window_size = window_size
        self._profiles: Dict[str, Dict[str, List[float]]] = {}
        self._baselines: Dict[str, Dict[str, Tuple[float, float]]] = {}

    def update_profile(
        self,
        agent_id: str,
        feature: str,
        value: float,
    ) -> None:
        """Update the behavioral profile for an agent.

        Args:
            agent_id: The agent identifier.
            feature: The feature name.
            value: The observed value.
        """
        profile = self._profiles.setdefault(agent_id, {})
        values = profile.setdefault(feature, [])
        values.append(value)

        # Keep only the window
        if len(values) > self._window_size:
            values.pop(0)

        # Update baseline statistics
        if len(values) >= self._min_samples:
            mean = statistics.mean(values)
            std = statistics.stdev(values) if len(values) > 1 else 0.0
            self._baselines.setdefault(agent_id, {})[feature] = (mean, std)

    def detect(
        self,
        agent_id: str,
        features: Dict[str, float],
    ) -> List[AnomalyResult]:
        """Detect anomalies in observed features.

        Args:
            agent_id: The agent identifier.
            features: Observed feature values.

        Returns:
            List of anomaly results.
        """
        results: List[AnomalyResult] = []

        for feature_name, value in features.items():
            # Update profile
            self.update_profile(agent_id, feature_name, value)

            # Statistical anomaly detection
            stat_result = self._statistical_check(
                agent_id, feature_name, value
            )
            if stat_result:
                results.append(stat_result)

            # Volume anomaly detection
            vol_result = self._volume_check(agent_id, feature_name, value)
            if vol_result:
                results.append(vol_result)

        return results

    def _statistical_check(
        self,
        agent_id: str,
        feature: str,
        value: float,
    ) -> Optional[AnomalyResult]:
        """Check for statistical anomalies using z-score."""
        baselines = self._baselines.get(agent_id, {})
        baseline = baselines.get(feature)
        if not baseline:
            return None

        mean, std = baseline
        if std == 0:
            return None

        z_score = abs(value - mean) / std
        if z_score < self._z_threshold:
            return None

        severity = self._zscore_to_severity(z_score)
        score = min(1.0, z_score / (self._z_threshold * 2))

        return AnomalyResult(
            is_anomaly=True,
            anomaly_type=AnomalyType.STATISTICAL,
            severity=severity,
            score=round(score, 4),
            confidence=round(min(1.0, z_score / 10.0), 4),
            description=(
                f"Statistical anomaly in {feature}: "
                f"z-score={z_score:.2f}, value={value:.2f}, "
                f"mean={mean:.2f}, std={std:.2f}"
            ),
            features={feature: value, "z_score": z_score},
        )

    def _volume_check(
        self,
        agent_id: str,
        feature: str,
        value: float,
    ) -> Optional[AnomalyResult]:
        """Check for volume-based anomalies."""
        profile = self._profiles.get(agent_id, {})
        values = profile.get(feature, [])
        if len(values) < self._min_samples:
            return None

        sorted_vals = sorted(values)
        q1 = sorted_vals[len(sorted_vals) // 4]
        q3 = sorted_vals[3 * len(sorted_vals) // 4]
        iqr = q3 - q1

        if iqr == 0:
            return None

        lower = q1 - self._iqr_multiplier * iqr
        upper = q3 + self._iqr_multiplier * iqr

        if lower <= value <= upper:
            return None

        severity = AnomalySeverity.HIGH if value > upper * 2 or value < lower * 0.5 else AnomalySeverity.MEDIUM

        return AnomalyResult(
            is_anomaly=True,
            anomaly_type=AnomalyType.VOLUME,
            severity=severity,
            score=round(min(1.0, abs(value - statistics.median(values)) / (iqr + 1e-9)), 4),
            confidence=0.8,
            description=(
                f"Volume anomaly in {feature}: "
                f"value={value:.2f}, IQR range=[{lower:.2f}, {upper:.2f}]"
            ),
            features={feature: value, "q1": q1, "q3": q3, "iqr": iqr},
        )

    def _zscore_to_severity(self, z_score: float) -> AnomalySeverity:
        """Convert z-score to severity level."""
        if z_score > 6:
            return AnomalySeverity.CRITICAL
        elif z_score > 4.5:
            return AnomalySeverity.HIGH
        elif z_score > 3.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    def get_profile_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get a summary of an agent's behavioral profile.

        Args:
            agent_id: The agent identifier.

        Returns:
            Profile summary.
        """
        profile = self._profiles.get(agent_id, {})
        baselines = self._baselines.get(agent_id, {})

        summary: Dict[str, Any] = {}
        for feature, values in profile.items():
            if not values:
                continue
            baseline = baselines.get(feature, (0.0, 0.0))
            summary[feature] = {
                "count": len(values),
                "mean": round(baseline[0], 4),
                "std": round(baseline[1], 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "last": round(values[-1], 4),
            }
        return summary

    def reset(self, agent_id: str) -> None:
        """Reset the profile for an agent.

        Args:
            agent_id: The agent identifier.
        """
        self._profiles.pop(agent_id, None)
        self._baselines.pop(agent_id, None)

"""Pattern Detector Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Any

from langchain_deepagents import create_deep_agent

from bias_detector.agents.base import BaseBiasAgent
from bias_detector.config import get_settings
from bias_detector.models import DemographicData, HiringDecision

logger = logging.getLogger(__name__)


class PatternDetectorAgent(BaseBiasAgent[dict[str, Any]]):
    """Agent that identifies patterns of bias across hiring decisions.

    This agent analyzes sequences of hiring decisions to detect patterns
    such as temporal bias, interviewer bias, and systematic exclusion.

    Attributes:
        name: Agent identifier.
        description: Agent description.
    """

    name = "pattern_detector"
    description = "Identifies patterns of bias across hiring decisions"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Pattern Detector Agent.

        Args:
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self._settings = get_settings()
        self._agent = self._create_agent()

    def _create_agent(self) -> Any:
        """Create the LangChain DeepAgent for pattern detection.

        Returns:
            Configured DeepAgent instance.
        """
        return create_deep_agent(
            name=self.name,
            description=self.description,
            system_prompt=self._get_system_prompt(),
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for pattern detection.

        Returns:
            System prompt string.
        """
        return (
            "You are a pattern detection expert specializing in hiring bias. "
            "Analyze hiring decisions to identify systematic patterns of bias "
            "including temporal bias, interviewer bias, and demographic clustering."
        )

    async def analyze(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Detect bias patterns in hiring decisions.

        Args:
            data: Dictionary containing hiring_decisions and demographic_data.

        Returns:
            List of detected bias patterns.
        """
        logger.info("Starting pattern detection analysis")

        decisions: list[HiringDecision] = data.get("hiring_decisions", [])
        demo: DemographicData = data.get("demographic_data", DemographicData())

        patterns: list[dict[str, Any]] = []

        # Detect interviewer bias
        interviewer_patterns = self._detect_interviewer_bias(decisions)
        patterns.extend(interviewer_patterns)

        # Detect temporal bias
        temporal_patterns = self._detect_temporal_bias(decisions)
        patterns.extend(temporal_patterns)

        # Detect demographic clustering
        clustering_patterns = self._detect_demographic_clustering(decisions, demo)
        patterns.extend(clustering_patterns)

        # Detect decision consistency patterns
        consistency_patterns = self._detect_consistency_patterns(decisions)
        patterns.extend(consistency_patterns)

        logger.info("Pattern detection complete: %d patterns found", len(patterns))
        return patterns

    def _detect_interviewer_bias(self, decisions: list[HiringDecision]) -> list[dict[str, Any]]:
        """Detect bias patterns by interviewer.

        Args:
            decisions: Hiring decisions.

        Returns:
            List of interviewer bias patterns.
        """
        patterns: list[dict[str, Any]] = []
        interviewer_stats: dict[str, Counter] = defaultdict(Counter)

        for d in decisions:
            if d.interviewer_id:
                interviewer_stats[d.interviewer_id][d.decision.value] += 1

        for interviewer_id, counts in interviewer_stats.items():
            total = sum(counts.values())
            if total < 5:
                continue

            hire_rate = counts.get("hired", 0) / total
            reject_rate = counts.get("rejected", 0) / total

            if hire_rate > 0.8 or reject_rate > 0.8:
                patterns.append({
                    "type": "interviewer_bias",
                    "interviewer_id": interviewer_id,
                    "confidence": min(1.0, total / 20.0),
                    "details": {
                        "total_decisions": total,
                        "hire_rate": hire_rate,
                        "reject_rate": reject_rate,
                    },
                    "severity": "high" if hire_rate > 0.9 or reject_rate > 0.9 else "medium",
                })

        return patterns

    def _detect_temporal_bias(self, decisions: list[HiringDecision]) -> list[dict[str, Any]]:
        """Detect temporal bias patterns.

        Args:
            decisions: Hiring decisions.

        Returns:
            List of temporal bias patterns.
        """
        patterns: list[dict[str, Any]] = []
        if not decisions:
            return patterns

        # Sort by timestamp
        sorted_decisions = sorted(decisions, key=lambda d: d.timestamp)

        # Check for time-based clustering of rejections
        rejection_times = [d.timestamp.hour for d in sorted_decisions if d.decision.value == "rejected"]
        if len(rejection_times) >= 5:
            hour_counts = Counter(rejection_times)
            most_common_hour, count = hour_counts.most_common(1)[0]
            if count / len(rejection_times) > 0.5:
                patterns.append({
                    "type": "temporal_bias",
                    "details": {
                        "most_common_rejection_hour": most_common_hour,
                        "rejection_count_at_hour": count,
                        "total_rejections": len(rejection_times),
                    },
                    "confidence": count / len(rejection_times),
                    "severity": "medium",
                })

        return patterns

    def _detect_demographic_clustering(
        self, decisions: list[HiringDecision], demo: DemographicData
    ) -> list[dict[str, Any]]:
        """Detect demographic clustering in decisions.

        Args:
            decisions: Hiring decisions.
            demo: Demographic data.

        Returns:
            List of demographic clustering patterns.
        """
        patterns: list[dict[str, Any]] = []
        if not decisions:
            return patterns

        # Check for demographic clustering in rejections
        rejection_demographics: dict[str, Counter] = defaultdict(Counter)
        for d in decisions:
            if d.decision.value == "rejected":
                for key, value in d.demographic_data.items():
                    rejection_demographics[key][value] += 1

        for dim, counts in rejection_demographics.items():
            total_rejections = sum(counts.values())
            if total_rejections < 5:
                continue

            most_common, count = counts.most_common(1)[0]
            ratio = count / total_rejections
            if ratio > 0.7:
                patterns.append({
                    "type": "demographic_clustering",
                    "dimension": dim,
                    "details": {
                        "most_common_group": most_common,
                        "group_rejection_count": count,
                        "total_rejections": total_rejections,
                        "ratio": ratio,
                    },
                    "confidence": ratio,
                    "severity": "high" if ratio > 0.85 else "medium",
                })

        return patterns

    def _detect_consistency_patterns(self, decisions: list[HiringDecision]) -> list[dict[str, Any]]:
        """Detect decision consistency patterns.

        Args:
            decisions: Hiring decisions.

        Returns:
            List of consistency patterns.
        """
        patterns: list[dict[str, Any]] = []
        if len(decisions) < 10:
            return patterns

        # Check for identical decisions across different demographics
        decision_by_demo: dict[tuple, list[str]] = defaultdict(list)
        for d in decisions:
            demo_key = tuple(sorted(d.demographic_data.items()))
            decision_by_demo[demo_key].append(d.decision.value)

        for demo_key, decision_list in decision_by_demo.items():
            if len(decision_list) < 3:
                continue
            unique_decisions = set(decision_list)
            if len(unique_decisions) == 1:
                patterns.append({
                    "type": "consistency_pattern",
                    "details": {
                        "demographic_profile": dict(demo_key),
                        "decision": decision_list[0],
                        "count": len(decision_list),
                    },
                    "confidence": min(1.0, len(decision_list) / 10.0),
                    "severity": "low",
                })

        return patterns

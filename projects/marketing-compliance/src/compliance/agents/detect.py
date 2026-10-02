"""Detect agent: identifies compliance violations in marketing content."""

from __future__ import annotations

import re
from typing import Any

from compliance.agents.base import AgentResult, BaseAgent, Severity

# Lightweight, deterministic rule set used as a first-pass detector.
# A LangChain/LLM classifier can be layered on top via ``config["model"]``.
_RULES: list[dict[str, Any]] = [
    {
        "name": "unsubscribe_missing",
        "pattern": None,
        "severity": Severity.HIGH,
        "description": "Email content must include an unsubscribe mechanism",
    },
    {
        "name": "guaranteed_claims",
        "pattern": r"\b(guaranteed?|risk[- ]free|100% safe)\b",
        "severity": Severity.MEDIUM,
        "description": "Absolute claims may breach FTC advertising guidance",
    },
    {
        "name": "pii_leak",
        "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
        "severity": Severity.CRITICAL,
        "description": "Content appears to contain an unredacted SSN",
    },
]


class DetectAgent(BaseAgent):
    """Analyses content and flags potential compliance violations."""

    name = "detect"

    async def run(self, payload: dict[str, Any]) -> AgentResult:
        """Detect violations within the supplied content items.

        Args:
            payload: Mapping containing an ``items`` list (as produced by the
                monitor agent) and an optional ``confidence_threshold``.

        Returns:
            An :class:`AgentResult` whose ``items`` are violation records.
        """
        items: list[dict[str, Any]] = payload.get("items", [])
        threshold: float = float(
            payload.get("confidence_threshold", self.config.get("confidence_threshold", 0.75))
        )

        violations: list[dict[str, Any]] = []
        for item in items:
            for violation in self._scan(item):
                if violation["confidence"] >= threshold:
                    violations.append(violation)

        return AgentResult(
            agent=self.name,
            items=violations,
            metrics={
                "items_scanned": float(len(items)),
                "violations_found": float(len(violations)),
                "violation_rate": (len(violations) / len(items)) if items else 0.0,
            },
        )

    def _scan(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        """Apply detection rules to a single content item.

        Args:
            item: A normalised content record.

        Returns:
            A list of violation records for the item.
        """
        content = str(item.get("content", ""))
        results: list[dict[str, Any]] = []

        for rule in _RULES:
            pattern = rule["pattern"]
            if pattern is None:
                # Structural rule: email campaigns must carry unsubscribe text.
                if item.get("channel") == "email" and "unsubscribe" not in content.lower():
                    results.append(self._violation(item, rule, 0.9))
                continue
            if re.search(pattern, content, re.IGNORECASE):
                results.append(self._violation(item, rule, 0.85))

        return results

    @staticmethod
    def _violation(item: dict[str, Any], rule: dict[str, Any], confidence: float) -> dict[str, Any]:
        """Build a violation record.

        Args:
            item: Source content record.
            rule: The rule that matched.
            confidence: Detection confidence in the range ``[0, 1]``.

        Returns:
            A violation dictionary.
        """
        return {
            "content_id": item.get("id"),
            "source": item.get("source"),
            "rule": rule["name"],
            "severity": rule["severity"].value,
            "description": rule["description"],
            "confidence": confidence,
            "excerpt": str(item.get("content", ""))[:280],
        }

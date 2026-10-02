"""Data access policies for agent governance.

Defines policies controlling what data agents can access, modify,
and export based on data classification and agent trust level.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from .engine import PolicyEngine, PolicyRule, PolicyEffect


class DataClassification(str, Enum):
    """Data classification levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PII = "pii"
    PHI = "phi"


class DataAccessPolicy:
    """Data access policy manager.

    Enforces data access controls based on classification, agent
    trust level, and purpose limitation.
    """

    DEFAULT_RULES: List[Dict[str, Any]] = [
        {
            "id": "deny-untrusted-pii",
            "name": "Deny untrusted agents PII access",
            "description": "Agents with low trust cannot access PII data",
            "effect": "deny",
            "conditions": [
                {"field": "data.classification", "op": "equals", "value": "pii"},
                {"field": "agent.trust_score", "op": "lt", "value": 0.5},
            ],
            "actions": ["read", "write", "export"],
            "resources": ["*"],
            "priority": 100,
        },
        {
            "id": "deny-restricted-unverified",
            "name": "Deny unverified agents restricted data",
            "description": "Only verified agents can access restricted data",
            "effect": "deny",
            "conditions": [
                {"field": "data.classification", "op": "equals", "value": "restricted"},
                {"field": "agent.trust_level", "op": "not_equals", "value": "verified"},
            ],
            "actions": ["read", "write", "export"],
            "resources": ["*"],
            "priority": 90,
        },
        {
            "id": "obligate-pii-audit",
            "name": "Obligate PII access auditing",
            "description": "All PII access must be audited",
            "effect": "obligate",
            "conditions": [
                {"field": "data.classification", "op": "equals", "value": "pii"},
            ],
            "actions": ["read", "write", "export"],
            "resources": ["*"],
            "priority": 80,
            "metadata": {"obligation:audit": "Full audit trail required for PII access"},
        },
        {
            "id": "deny-phi-unauthorized",
            "name": "Deny unauthorized PHI access",
            "description": "PHI data requires explicit authorization",
            "effect": "deny",
            "conditions": [
                {"field": "data.classification", "op": "equals", "value": "phi"},
                {"field": "agent.authorized_phi", "op": "equals", "value": False},
            ],
            "actions": ["read", "write", "export"],
            "resources": ["*"],
            "priority": 95,
        },
        {
            "id": "allow-public-read",
            "name": "Allow public data read",
            "description": "Any active agent can read public data",
            "effect": "allow",
            "conditions": [
                {"field": "data.classification", "op": "equals", "value": "public"},
                {"field": "agent.state", "op": "equals", "value": "active"},
            ],
            "actions": ["read"],
            "resources": ["*"],
            "priority": 10,
        },
        {
            "id": "deny-export-confidential",
            "name": "Deny confidential data export",
            "description": "Confidential data cannot be exported by agents",
            "effect": "deny",
            "conditions": [
                {"field": "data.classification", "op": "in", "value": ["confidential", "restricted"]},
            ],
            "actions": ["export"],
            "resources": ["*"],
            "priority": 85,
        },
    ]

    def __init__(self, engine: Optional[PolicyEngine] = None) -> None:
        """Initialize data access policy.

        Args:
            engine: Optional policy engine instance.
        """
        self._engine = engine or PolicyEngine()
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default data access rules."""
        for rule_data in self.DEFAULT_RULES:
            rule = PolicyRule.from_dict(rule_data)
            self._engine.add_rule(rule)

    def check_access(
        self,
        agent_id: str,
        action: str,
        data_classification: DataClassification,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Check if an agent can access data.

        Args:
            agent_id: The agent identifier.
            action: The requested action (read, write, export).
            data_classification: The data classification level.
            context: Additional context.

        Returns:
            Policy decision result.
        """
        ctx = context or {}
        ctx["data"] = {"classification": data_classification.value}
        ctx.setdefault("agent", {})["id"] = agent_id

        decision = self._engine.evaluate(action, "*", ctx)
        return decision.to_dict()

    def add_custom_rule(self, rule: PolicyRule) -> None:
        """Add a custom data access rule.

        Args:
            rule: The policy rule to add.
        """
        self._engine.add_rule(rule)

    @property
    def engine(self) -> PolicyEngine:
        """Get the underlying policy engine."""
        return self._engine

"""Content generation policies for agent governance.

Defines policies for AI-generated content including tone, style,
prohibited content, and approval workflows.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from .engine import PolicyEngine, PolicyRule, PolicyEffect


class ContentTone(str, Enum):
    """Content tone classifications."""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    PERSUASIVE = "persuasive"
    INFORMATIVE = "informative"


class ContentPolicy:
    """Content generation policy manager.

    Enforces content generation rules including tone requirements,
    prohibited content patterns, and approval workflows.
    """

    DEFAULT_RULES: List[Dict[str, Any]] = [
        {
            "id": "deny-prohibited-content",
            "name": "Deny prohibited content",
            "description": "Block content with prohibited patterns",
            "effect": "deny",
            "conditions": [
                {"field": "content.has_prohibited_patterns", "op": "equals", "value": True},
            ],
            "actions": ["generate", "publish"],
            "resources": ["*"],
            "priority": 100,
        },
        {
            "id": "obligate-legal-review",
            "name": "Obligate legal review for claims",
            "description": "Content with legal claims requires legal review",
            "effect": "obligate",
            "conditions": [
                {"field": "content.has_legal_claims", "op": "equals", "value": True},
            ],
            "actions": ["publish"],
            "resources": ["*"],
            "priority": 90,
            "metadata": {"obligation:legal_review": "Legal review required before publishing"},
        },
        {
            "id": "deny-misleading-stats",
            "name": "Deny misleading statistics",
            "description": "Block content with unverified statistics",
            "effect": "deny",
            "conditions": [
                {"field": "content.has_unverified_stats", "op": "equals", "value": True},
            ],
            "actions": ["generate", "publish"],
            "resources": ["*"],
            "priority": 95,
        },
        {
            "id": "obligate-approval-high-reach",
            "name": "Obligate approval for high-reach content",
            "description": "Content reaching >100k audience requires approval",
            "effect": "obligate",
            "conditions": [
                {"field": "content.estimated_reach", "op": "gt", "value": 100000},
            ],
            "actions": ["publish"],
            "resources": ["*"],
            "priority": 85,
            "metadata": {"obligation:approval": "Manager approval required for high-reach content"},
        },
        {
            "id": "deny-off-brand",
            "name": "Deny off-brand content",
            "description": "Block content that doesn't match brand voice",
            "effect": "deny",
            "conditions": [
                {"field": "content.brand_score", "op": "lt", "value": 0.6},
            ],
            "actions": ["publish"],
            "resources": ["*"],
            "priority": 80,
        },
        {
            "id": "allow-standard-content",
            "name": "Allow standard content generation",
            "description": "Standard content within brand guidelines is allowed",
            "effect": "allow",
            "conditions": [
                {"field": "content.brand_score", "op": "gte", "value": 0.6},
                {"field": "content.has_prohibited_patterns", "op": "equals", "value": False},
            ],
            "actions": ["generate"],
            "resources": ["*"],
            "priority": 10,
        },
    ]

    def __init__(self, engine: Optional[PolicyEngine] = None) -> None:
        """Initialize content policy.

        Args:
            engine: Optional policy engine instance.
        """
        self._engine = engine or PolicyEngine()
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default content rules."""
        for rule_data in self.DEFAULT_RULES:
            rule = PolicyRule.from_dict(rule_data)
            self._engine.add_rule(rule)

    def check_content(
        self,
        agent_id: str,
        action: str,
        content_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Check if content action is allowed.

        Args:
            agent_id: The agent identifier.
            action: The content action (generate, publish).
            content_metadata: Content metadata for evaluation.

        Returns:
            Policy decision result.
        """
        ctx = content_metadata or {}
        ctx.setdefault("agent", {})["id"] = agent_id

        decision = self._engine.evaluate(action, "*", ctx)
        return decision.to_dict()

    def add_custom_rule(self, rule: PolicyRule) -> None:
        """Add a custom content rule.

        Args:
            rule: The policy rule to add.
        """
        self._engine.add_rule(rule)

    @property
    def engine(self) -> PolicyEngine:
        """Get the underlying policy engine."""
        return self._engine

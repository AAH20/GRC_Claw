"""Budget policies for agent governance.

Defines spending limits, budget enforcement, and cost control
policies for AI marketing agents.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from .engine import PolicyEngine, PolicyRule, PolicyEffect


class BudgetPeriod(str, Enum):
    """Budget period types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CAMPAIGN = "campaign"


class BudgetPolicy:
    """Budget policy manager.

    Enforces spending limits and budget controls for agent-driven
    marketing activities.
    """

    DEFAULT_RULES: List[Dict[str, Any]] = [
        {
            "id": "deny-over-daily-limit",
            "name": "Deny over daily spending limit",
            "description": "Block actions that would exceed daily budget",
            "effect": "deny",
            "conditions": [
                {"field": "budget.daily_spend_plus_action", "op": "gt", "value": 10000},
            ],
            "actions": ["spend", "allocate"],
            "resources": ["*"],
            "priority": 100,
        },
        {
            "id": "deny-over-monthly-limit",
            "name": "Deny over monthly spending limit",
            "description": "Block actions that would exceed monthly budget",
            "effect": "deny",
            "conditions": [
                {"field": "budget.monthly_spend_plus_action", "op": "gt", "value": 100000},
            ],
            "actions": ["spend", "allocate"],
            "resources": ["*"],
            "priority": 95,
        },
        {
            "id": "obligate-approval-large-spend",
            "name": "Obligate approval for large spend",
            "description": "Spend over $5000 requires manager approval",
            "effect": "obligate",
            "conditions": [
                {"field": "budget.action_amount", "op": "gt", "value": 5000},
            ],
            "actions": ["spend"],
            "resources": ["*"],
            "priority": 85,
            "metadata": {"obligation:approval": "Manager approval required for spend > $5000"},
        },
        {
            "id": "deny-campaign-overrun",
            "name": "Deny campaign budget overrun",
            "description": "Prevent campaign spend from exceeding allocation",
            "effect": "deny",
            "conditions": [
                {"field": "budget.campaign_remaining", "op": "lt", "value": 0},
            ],
            "actions": ["spend", "allocate"],
            "resources": ["*"],
            "priority": 90,
        },
        {
            "id": "allow-within-budget",
            "name": "Allow spend within budget",
            "description": "Spend within budget limits is allowed",
            "effect": "allow",
            "conditions": [
                {"field": "budget.daily_spend_plus_action", "op": "lte", "value": 10000},
                {"field": "budget.monthly_spend_plus_action", "op": "lte", "value": 100000},
            ],
            "actions": ["spend"],
            "resources": ["*"],
            "priority": 10,
        },
    ]

    def __init__(self, engine: Optional[PolicyEngine] = None) -> None:
        """Initialize budget policy.

        Args:
            engine: Optional policy engine instance.
        """
        self._engine = engine or PolicyEngine()
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default budget rules."""
        for rule_data in self.DEFAULT_RULES:
            rule = PolicyRule.from_dict(rule_data)
            self._engine.add_rule(rule)

    def check_spend(
        self,
        agent_id: str,
        amount: float,
        budget_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Check if a spend action is allowed.

        Args:
            agent_id: The agent identifier.
            amount: The spend amount.
            budget_context: Budget state information.

        Returns:
            Policy decision result.
        """
        ctx = budget_context or {}
        ctx["budget"] = ctx.get("budget", {})
        ctx["budget"]["action_amount"] = amount
        ctx.setdefault("agent", {})["id"] = agent_id

        decision = self._engine.evaluate("spend", "*", ctx)
        return decision.to_dict()

    def add_custom_rule(self, rule: PolicyRule) -> None:
        """Add a custom budget rule.

        Args:
            rule: The policy rule to add.
        """
        self._engine.add_rule(rule)

    @property
    def engine(self) -> PolicyEngine:
        """Get the underlying policy engine."""
        return self._engine

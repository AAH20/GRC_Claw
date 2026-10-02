"""OPA/Rego-compatible policy enforcement engine.

Provides a policy engine that evaluates rules against agent actions,
supporting Rego-like semantics with JSON-based rule definitions.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class PolicyEffect(str, Enum):
    """Policy decision effect."""

    ALLOW = "allow"
    DENY = "deny"
    OBLIGATE = "obligate"


class PolicyError(Exception):
    """Base exception for policy operations."""


class PolicyEvaluationError(PolicyError):
    """Raised when policy evaluation fails."""


class PolicyNotFoundError(PolicyError):
    """Raised when a policy is not found."""


@dataclass
class PolicyRule:
    """A single policy rule."""

    id: str
    name: str
    description: str
    effect: PolicyEffect
    conditions: List[Dict[str, Any]]
    actions: List[str]
    resources: List[str]
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "effect": self.effect.value,
            "conditions": self.conditions,
            "actions": self.actions,
            "resources": self.resources,
            "priority": self.priority,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PolicyRule:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            effect=PolicyEffect(data["effect"]),
            conditions=data.get("conditions", []),
            actions=data.get("actions", []),
            resources=data.get("resources", []),
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PolicyDecision:
    """Result of a policy evaluation."""

    allowed: bool
    effect: PolicyEffect
    rule_id: Optional[str]
    reason: str
    obligations: List[str] = field(default_factory=list)
    evaluated_at: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "allowed": self.allowed,
            "effect": self.effect.value,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "obligations": self.obligations,
            "evaluated_at": self.evaluated_at,
            "context": self.context,
        }


class PolicyEngine:
    """Policy enforcement engine with Rego-compatible semantics.

    Evaluates policy rules against agent actions using condition matching,
    supporting allow/deny/obligate effects with priority-based resolution.
    """

    def __init__(self) -> None:
        """Initialize the policy engine."""
        self._rules: Dict[str, PolicyRule] = {}
        self._rego_policies: Dict[str, str] = {}
        self._custom_evaluators: Dict[str, Callable] = {}
        self._decision_log: List[PolicyDecision] = []

    def add_rule(self, rule: PolicyRule) -> None:
        """Add a policy rule.

        Args:
            rule: The policy rule to add.
        """
        self._rules[rule.id] = rule

    def remove_rule(self, rule_id: str) -> None:
        """Remove a policy rule.

        Args:
            rule_id: The rule identifier.
        """
        self._rules.pop(rule_id, None)

    def add_rego_policy(self, name: str, rego_source: str) -> None:
        """Add a Rego policy.

        Args:
            name: Policy name.
            rego_source: Rego policy source code.
        """
        self._rego_policies[name] = rego_source

    def register_evaluator(
        self, name: str, evaluator: Callable[[Dict[str, Any]], bool]
    ) -> None:
        """Register a custom condition evaluator.

        Args:
            name: Evaluator name.
            evaluator: Callable that evaluates a condition.
        """
        self._custom_evaluators[name] = evaluator

    def evaluate(
        self,
        action: str,
        resource: str,
        context: Dict[str, Any],
    ) -> PolicyDecision:
        """Evaluate policies for an action on a resource.

        Args:
            action: The action being attempted.
            resource: The target resource.
            context: Evaluation context (agent, environment, etc.).

        Returns:
            The policy decision.
        """
        matching_rules = self._find_matching_rules(action, resource)

        if not matching_rules:
            return PolicyDecision(
                allowed=True,
                effect=PolicyEffect.ALLOW,
                rule_id=None,
                reason="No matching policy rules; default allow",
                context=context,
            )

        # Sort by priority (highest first)
        matching_rules.sort(key=lambda r: r.priority, reverse=True)

        for rule in matching_rules:
            if not self._evaluate_conditions(rule.conditions, context):
                continue

            if rule.effect == PolicyEffect.DENY:
                decision = PolicyDecision(
                    allowed=False,
                    effect=PolicyEffect.DENY,
                    rule_id=rule.id,
                    reason=f"Denied by rule: {rule.name}",
                    context=context,
                )
                self._decision_log.append(decision)
                return decision

            if rule.effect == PolicyEffect.OBLIGATE:
                obligations = self._extract_obligations(rule, context)
                decision = PolicyDecision(
                    allowed=True,
                    effect=PolicyEffect.OBLIGATE,
                    rule_id=rule.id,
                    reason=f"Allowed with obligations: {rule.name}",
                    obligations=obligations,
                    context=context,
                )
                self._decision_log.append(decision)
                return decision

            # ALLOW
            decision = PolicyDecision(
                allowed=True,
                effect=PolicyEffect.ALLOW,
                rule_id=rule.id,
                reason=f"Allowed by rule: {rule.name}",
                context=context,
            )
            self._decision_log.append(decision)
            return decision

        # No rule matched conditions
        return PolicyDecision(
            allowed=True,
            effect=PolicyEffect.ALLOW,
            rule_id=None,
            reason="No rule conditions matched; default allow",
            context=context,
        )

    def _find_matching_rules(
        self, action: str, resource: str
    ) -> List[PolicyRule]:
        """Find rules matching an action and resource."""
        matching = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            if action not in rule.actions and "*" not in rule.actions:
                continue
            if resource not in rule.resources and "*" not in rule.resources:
                continue
            matching.append(rule)
        return matching

    def _evaluate_conditions(
        self, conditions: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> bool:
        """Evaluate conditions against context.

        Supports: equals, not_equals, contains, regex, gt, lt, in, exists.
        """
        for condition in conditions:
            if not self._evaluate_single_condition(condition, context):
                return False
        return True

    def _evaluate_single_condition(
        self, condition: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Evaluate a single condition."""
        op = condition.get("op", "equals")
        field = condition.get("field", "")
        value = condition.get("value")

        actual = self._resolve_field(field, context)

        if op == "equals":
            return actual == value
        elif op == "not_equals":
            return actual != value
        elif op == "contains":
            return value in actual if actual is not None else False
        elif op == "regex":
            return bool(re.match(str(value), str(actual))) if actual else False
        elif op == "gt":
            return actual is not None and actual > value
        elif op == "lt":
            return actual is not None and actual < value
        elif op == "gte":
            return actual is not None and actual >= value
        elif op == "lte":
            return actual is not None and actual <= value
        elif op == "in":
            return actual in value if value else False
        elif op == "exists":
            return actual is not None
        elif op == "not_exists":
            return actual is None
        elif op in self._custom_evaluators:
            return self._custom_evaluators[op](context)
        else:
            logger.warning("Unknown condition operator: %s", op)
            return False

    def _resolve_field(self, field: str, context: Dict[str, Any]) -> Any:
        """Resolve a dotted field path in context."""
        parts = field.split(".")
        current: Any = context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _extract_obligations(
        self, rule: PolicyRule, context: Dict[str, Any]
    ) -> List[str]:
        """Extract obligations from a rule."""
        obligations = []
        for meta_key, meta_val in rule.metadata.items():
            if meta_key.startswith("obligation:"):
                obligations.append(meta_val)
        return obligations

    def get_decision_log(
        self, limit: int = 100
    ) -> List[PolicyDecision]:
        """Get recent policy decisions.

        Args:
            limit: Maximum number of decisions to return.

        Returns:
            List of recent policy decisions.
        """
        return self._decision_log[-limit:]

    def clear_decision_log(self) -> None:
        """Clear the decision log."""
        self._decision_log.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize engine state to dictionary."""
        return {
            "rules": {rid: r.to_dict() for rid, r in self._rules.items()},
            "rego_policies": list(self._rego_policies.keys()),
            "custom_evaluators": list(self._custom_evaluators.keys()),
        }

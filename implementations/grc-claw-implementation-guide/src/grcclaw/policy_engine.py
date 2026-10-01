"""Policy engine — abstract interface and Cedar/Rego implementations."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from .models import Action, Policy, PolicyRule


@dataclass
class PolicyDecision:
    """Result of a policy evaluation."""
    effect: Action
    reason: str
    matched_rule: Optional[str] = None
    policy_id: str = ""


@dataclass
class ValidationResult:
    """Result of policy validation."""
    valid: bool
    errors: list[str]
    warnings: list[str]


class PolicyEngine(ABC):
    """Abstract policy engine interface."""

    @abstractmethod
    def evaluate(
        self,
        principal: dict[str, Any],
        action: str,
        resource: dict[str, Any],
        context: dict[str, Any],
    ) -> PolicyDecision:
        """Evaluate policies against an action."""
        ...

    @abstractmethod
    def validate_policy(self, policy: Policy) -> ValidationResult:
        """Validate a policy definition for syntax and semantics."""
        ...

    @abstractmethod
    def load_policies(self, source: str) -> list[Policy]:
        """Load policies from a source (Git, DB, file)."""
        ...

    @abstractmethod
    def get_policy(self, policy_id: str, version: Optional[str] = None) -> Policy:
        """Retrieve a specific policy by ID and optional version."""
        ...


class CedarEngine(PolicyEngine):
    """Cedar-based policy engine implementation.

    Uses the cedar-policy Rust crate via FFI for deterministic evaluation.
    This is the primary policy engine for GRC_Claw.
    """

    def __init__(self, schema: Optional[dict] = None):
        self.schema = schema or {}
        self._policies: dict[str, Policy] = {}
        self._compiled: dict[str, Any] = {}

    def evaluate(
        self,
        principal: dict[str, Any],
        action: str,
        resource: dict[str, Any],
        context: dict[str, Any],
    ) -> PolicyDecision:
        """Evaluate Cedar policies against an action.

        In production, this invokes the Cedar Rust engine via FFI.
        """
        # Reference implementation — production uses cedar-policy crate
        for policy in self._policies.values():
            for rule in policy.sorted_rules():
                if rule.condition.get("type") != "cedar":
                    continue
                if self._evaluate_cedar_rule(rule, principal, action, resource, context):
                    return PolicyDecision(
                        effect=rule.effect,
                        reason=f"Matched rule '{rule.name}': {rule.description}",
                        matched_rule=rule.name,
                        policy_id=policy.id,
                    )
        return PolicyDecision(
            effect=Action.DENY,
            reason="No matching Cedar policy — default deny",
        )

    def _evaluate_cedar_rule(
        self,
        rule: PolicyRule,
        principal: dict[str, Any],
        action: str,
        resource: dict[str, Any],
        context: dict[str, Any],
    ) -> bool:
        """Evaluate a single Cedar rule.

        Placeholder for actual Cedar evaluation.
        Production: cedar_policy::is_authorized()
        """
        expression = rule.condition.get("expression", "")
        # Simplified evaluation for reference
        if 'principal.action ==' in expression:
            parts = expression.split('==')
            if len(parts) >= 2:
                expected = parts[1].strip().strip('"').strip("'")
                return action == expected
        return False

    def validate_policy(self, policy: Policy) -> ValidationResult:
        """Validate a Cedar policy definition."""
        errors: list[str] = []
        warnings: list[str] = []

        if not policy.name:
            errors.append("Policy name is required")
        if not policy.version:
            errors.append("Policy version is required")
        if not policy.rules:
            errors.append("Policy must have at least one rule")

        for rule in policy.rules:
            if not rule.name:
                errors.append(f"Rule name is required (rule: {rule})")
            if rule.condition.get("type") == "cedar":
                expr = rule.condition.get("expression", "")
                if not expr:
                    errors.append(f"Cedar rule '{rule.name}' missing expression")
                # Check for common Cedar syntax issues
                if "permit(" in expr and "forbid(" in expr:
                    warnings.append(f"Rule '{rule.name}' mixes permit and forbid — verify intent")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def load_policies(self, source: str) -> list[Policy]:
        """Load policies from a source."""
        # In production: load from Git, DB, or file system
        return list(self._policies.values())

    def get_policy(self, policy_id: str, version: Optional[str] = None) -> Policy:
        """Retrieve a specific policy by ID and optional version."""
        if policy_id not in self._policies:
            raise KeyError(f"Policy not found: {policy_id}")
        return self._policies[policy_id]

    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine."""
        self._policies[policy.id] = policy

    def compile_policy(self, policy: Policy) -> dict[str, Any]:
        """Compile a policy to enforcement rules.

        In production, this invokes the Cedar compiler.
        """
        compiled = {
            "policy_id": policy.id,
            "version": policy.version,
            "rules": [
                {
                    "name": r.name,
                    "effect": r.effect.value,
                    "condition": r.condition,
                    "priority": r.priority,
                }
                for r in policy.sorted_rules()
            ],
            "default_action": policy.default_action.value,
            "on_timeout": policy.on_timeout.value,
        }
        self._compiled[policy.id] = compiled
        return compiled


class RegoEngine(PolicyEngine):
    """OPA Rego-based policy engine implementation.

    Uses OPA WASM or sidecar for compatibility with existing Rego policies.
    """

    def __init__(self, opa_url: Optional[str] = None):
        self.opa_url = opa_url
        self._policies: dict[str, Policy] = {}

    def evaluate(
        self,
        principal: dict[str, Any],
        action: str,
        resource: dict[str, Any],
        context: dict[str, Any],
    ) -> PolicyDecision:
        """Evaluate Rego policies against an action.

        In production, this invokes OPA via WASM or HTTP sidecar.
        """
        for policy in self._policies.values():
            for rule in policy.sorted_rules():
                if rule.condition.get("type") != "rego":
                    continue
                if self._evaluate_rego_rule(rule, principal, action, resource, context):
                    return PolicyDecision(
                        effect=rule.effect,
                        reason=f"Matched Rego rule '{rule.name}': {rule.description}",
                        matched_rule=rule.name,
                        policy_id=policy.id,
                    )
        return PolicyDecision(
            effect=Action.DENY,
            reason="No matching Rego policy — default deny",
        )

    def _evaluate_rego_rule(
        self,
        rule: PolicyRule,
        principal: dict[str, Any],
        action: str,
        resource: dict[str, Any],
        context: dict[str, Any],
    ) -> bool:
        """Evaluate a single Rego rule.

        Placeholder for actual OPA evaluation.
        Production: OPA WASM or HTTP query
        """
        query = rule.condition.get("query", "")
        if not query:
            return False
        # Simplified: check if action matches
        if f'input.action == "{action}"' in query:
            return True
        return False

    def validate_policy(self, policy: Policy) -> ValidationResult:
        """Validate a Rego policy definition."""
        errors: list[str] = []
        warnings: list[str] = []

        if not policy.name:
            errors.append("Policy name is required")
        if not policy.rules:
            errors.append("Policy must have at least one rule")

        for rule in policy.rules:
            if rule.condition.get("type") == "rego":
                query = rule.condition.get("query", "")
                if not query:
                    errors.append(f"Rego rule '{rule.name}' missing query")
                if not query.startswith("data."):
                    warnings.append(f"Rego rule '{rule.name}' query should start with 'data.'")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def load_policies(self, source: str) -> list[Policy]:
        """Load policies from a source."""
        return list(self._policies.values())

    def get_policy(self, policy_id: str, version: Optional[str] = None) -> Policy:
        """Retrieve a specific policy by ID and optional version."""
        if policy_id not in self._policies:
            raise KeyError(f"Policy not found: {policy_id}")
        return self._policies[policy_id]

    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine."""
        self._policies[policy.id] = policy

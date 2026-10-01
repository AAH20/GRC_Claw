"""Enforcement engine — deterministic policy enforcement at the application layer."""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any, Callable, Optional

from .models import (
    Action,
    AgentAction,
    Enforcement,
    EnforcementContext,
    EnforcementResult,
    EnforcementStrategy,
    Policy,
    PolicyRule,
)


class EnforcementEngine:
    """Deterministic enforcement engine.

    Evaluates policies against agent actions and returns enforcement decisions.
    Supports multiple enforcement strategies and fail-closed defaults.
    """

    def __init__(
        self,
        strategy: EnforcementStrategy = EnforcementStrategy.DENY_OVERRIDES,
        default_action: Action = Action.DENY,
        on_timeout: Action = Action.DENY,
        timeout_ms: int = 5000,
    ):
        self.strategy = strategy
        self.default_action = default_action
        self.on_timeout = on_timeout
        self.timeout_ms = timeout_ms
        self._hooks: dict[str, list[Callable]] = {}
        self._audit_log: list[Enforcement] = []

    def register_hook(self, point: str, callback: Callable) -> None:
        """Register an enforcement hook at a specific intervention point."""
        if point not in self._hooks:
            self._hooks[point] = []
        self._hooks[point].append(callback)

    def enforce(
        self,
        action: AgentAction,
        context: EnforcementContext,
        policies: list[Policy],
    ) -> EnforcementResult:
        """Evaluate policies against an agent action.

        Args:
            action: The action the agent wants to take
            context: Full context (agent identity, session, environment)
            policies: Applicable policies (filtered by scope)

        Returns:
            EnforcementResult with the decision and evidence reference
        """
        start_time = time.monotonic()

        # 1. Sort policies by priority (descending)
        sorted_policies = sorted(
            policies,
            key=lambda p: max((r.priority for r in p.rules), default=0),
            reverse=True,
        )

        # 2. Evaluate each policy's rules
        matched_rules: list[tuple[Policy, PolicyRule]] = []
        for policy in sorted_policies:
            for rule in policy.sorted_rules():
                if self._evaluate_rule(rule, action, context):
                    matched_rules.append((policy, rule))

        # 3. Apply enforcement strategy
        result = self._apply_strategy(matched_rules, action, context)

        # 4. Generate evidence reference
        evidence_id = f"EVD-{uuid.uuid4().hex[:12].upper()}"

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        enforcement_result = EnforcementResult(
            effect=result.effect,
            reason=result.reason,
            policy_id=result.policy_id,
            rule_id=result.rule_id,
            evidence_id=evidence_id,
            transformed_input=result.transformed_input,
            approval_ticket=result.approval_ticket,
            metadata={
                "strategy": self.strategy.value,
                "policies_evaluated": len(policies),
                "rules_matched": len(matched_rules),
            },
            evaluation_latency_ms=elapsed_ms,
            total_latency_ms=elapsed_ms,
        )

        # 5. Record in audit log
        self._record_enforcement(enforcement_result, action, context)

        return enforcement_result

    def _evaluate_rule(
        self,
        rule: PolicyRule,
        action: AgentAction,
        context: EnforcementContext,
    ) -> bool:
        """Evaluate a single rule condition against an action.

        In production, this would invoke Cedar/Rego engines.
        For the reference implementation, we use a simplified matcher.
        """
        condition = rule.condition
        cond_type = condition.get("type", "cedar")
        expression = condition.get("expression", "")

        if not expression:
            return False

        # Simplified condition evaluation for reference implementation
        # In production, this calls the Cedar/Rego engine
        return self._evaluate_expression(expression, action, context)

    def _evaluate_expression(
        self,
        expression: str,
        action: AgentAction,
        context: EnforcementContext,
    ) -> bool:
        """Evaluate a policy expression against an action.

        This is a simplified reference implementation.
        Production uses Cedar/Rego for deterministic evaluation.
        """
        # Parse simple conditions like 'principal.action == "export"'
        # This is a placeholder for the actual Cedar/Rego evaluation
        expr = expression.strip()

        # Handle action matching
        if 'principal.action ==' in expr:
            # Extract the action value from the expression
            parts = expr.split('==')
            if len(parts) >= 2:
                expected = parts[1].strip().strip('"').strip("'")
                return action.action == expected

        # Handle tool matching
        if 'principal.tool ==' in expr:
            parts = expr.split('==')
            if len(parts) >= 2:
                expected = parts[1].strip().strip('"').strip("'")
                return action.tool == expected

        # Handle resource matching
        if 'resource ==' in expr:
            parts = expr.split('==')
            if len(parts) >= 2:
                expected = parts[1].strip().strip('"').strip("'")
                return action.resource == expected

        # Default: no match
        return False

    def _apply_strategy(
        self,
        matched_rules: list[tuple[Policy, PolicyRule]],
        action: AgentAction,
        context: EnforcementContext,
    ) -> EnforcementResult:
        """Apply the enforcement strategy to matched rules."""
        if not matched_rules:
            return EnforcementResult(
                effect=self.default_action,
                reason="No matching rules — default action applied",
            )

        if self.strategy == EnforcementStrategy.DENY_OVERRIDES:
            # Any deny rule wins over allow rules
            for policy, rule in matched_rules:
                if rule.effect == Action.DENY:
                    return EnforcementResult(
                        effect=Action.DENY,
                        reason=f"Denied by rule '{rule.name}': {rule.description}",
                        policy_id=policy.id,
                        rule_id=rule.name,
                    )
            # No deny found, use first match
            policy, rule = matched_rules[0]
            return EnforcementResult(
                effect=rule.effect,
                reason=f"Matched rule '{rule.name}': {rule.description}",
                policy_id=policy.id,
                rule_id=rule.name,
            )

        elif self.strategy == EnforcementStrategy.ALLOW_OVERRIDES:
            # Any allow rule wins over deny rules
            for policy, rule in matched_rules:
                if rule.effect == Action.ALLOW:
                    return EnforcementResult(
                        effect=Action.ALLOW,
                        reason=f"Allowed by rule '{rule.name}': {rule.description}",
                        policy_id=policy.id,
                        rule_id=rule.name,
                    )
            # No allow found, use first match
            policy, rule = matched_rules[0]
            return EnforcementResult(
                effect=rule.effect,
                reason=f"Matched rule '{rule.name}': {rule.description}",
                policy_id=policy.id,
                rule_id=rule.name,
            )

        elif self.strategy == EnforcementStrategy.FIRST_MATCH:
            policy, rule = matched_rules[0]
            return EnforcementResult(
                effect=rule.effect,
                reason=f"First match rule '{rule.name}': {rule.description}",
                policy_id=policy.id,
                rule_id=rule.name,
            )

        elif self.strategy == EnforcementStrategy.PRIORITY_ORDER:
            # Already sorted by priority, use first
            policy, rule = matched_rules[0]
            return EnforcementResult(
                effect=rule.effect,
                reason=f"Highest priority rule '{rule.name}': {rule.description}",
                policy_id=policy.id,
                rule_id=rule.name,
            )

        # Fallback
        policy, rule = matched_rules[0]
        return EnforcementResult(
            effect=rule.effect,
            reason=f"Matched rule '{rule.name}': {rule.description}",
            policy_id=policy.id,
            rule_id=rule.name,
        )

    def _record_enforcement(
        self,
        result: EnforcementResult,
        action: AgentAction,
        context: EnforcementContext,
    ) -> None:
        """Record enforcement decision in the audit log."""
        enforcement = Enforcement(
            decision=result.effect,
            agent_id=action.agent_id,
            action_type=action.action,
            tool_name=action.tool,
            resource=action.resource,
            parameters=action.arguments,
            policy_id=result.policy_id,
            decision_reason=result.reason,
            confidence_score=1.0,
            deterministic=True,
            evidence_ids=[result.evidence_id] if result.evidence_id else [],
            evaluation_latency_ms=result.evaluation_latency_ms,
            total_latency_ms=result.total_latency_ms,
        )
        self._audit_log.append(enforcement)

    def get_audit_trail(
        self,
        agent_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> list[Enforcement]:
        """Retrieve audit trail entries matching the filter."""
        results = self._audit_log
        if agent_id:
            results = [e for e in results if e.agent_id == agent_id]
        if policy_id:
            results = [e for e in results if e.policy_id == policy_id]
        return results

    def get_stats(self) -> dict[str, Any]:
        """Get enforcement statistics."""
        total = len(self._audit_log)
        if total == 0:
            return {"total": 0}
        by_decision: dict[str, int] = {}
        for e in self._audit_log:
            key = e.decision.value
            by_decision[key] = by_decision.get(key, 0) + 1
        return {
            "total": total,
            "by_decision": by_decision,
            "avg_latency_ms": sum(e.evaluation_latency_ms for e in self._audit_log) / total,
        }

"""Rule Enforcer Agent for community governance."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseLanguageModel

from community_governance.agents.base import BaseAgent
from community_governance.config.logging_config import get_logger
from community_governance.exceptions import AgentExecutionException, RuleNotFoundException
from community_governance.models.governance_action import GovernanceAction
from community_governance.models.rule import Rule, RuleEnforcementResult, RuleSeverity

logger = get_logger(__name__)


class RuleEnforcerAgent(BaseAgent[dict[str, Any], list[RuleEnforcementResult]]):
    """Agent responsible for enforcing community rules against actions.

    Uses LangChain DeepAgents to evaluate governance actions against
    active rules and determine violations with appropriate severity
    and recommended actions.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        rules: list[Rule] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Rule Enforcer Agent.

        Args:
            llm: Language model for rule evaluation reasoning.
            rules: List of active rules to enforce.
            **kwargs: Additional configuration options.
        """
        super().__init__(llm=llm, name="rule_enforcer", **kwargs)
        self.rules = rules or []
        self._rule_index: dict[UUID, Rule] = {rule.id: rule for rule in self.rules}

    async def _setup(self) -> None:
        """Setup the rule index for efficient lookups."""
        self._rule_index = {rule.id: rule for rule in self.rules}
        logger.info(
            f"Rule Enforcer Agent loaded with {len(self.rules)} rules",
            agent_name=self.name,
            rule_count=len(self.rules),
        )

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the enforcement set.

        Args:
            rule: The rule to add.
        """
        self.rules.append(rule)
        self._rule_index[rule.id] = rule
        logger.info(f"Rule '{rule.name}' added to enforcement set", rule_id=str(rule.id))

    def remove_rule(self, rule_id: UUID) -> None:
        """Remove a rule from the enforcement set.

        Args:
            rule_id: The ID of the rule to remove.

        Raises:
            RuleNotFoundException: If the rule is not found.
        """
        if rule_id not in self._rule_index:
            raise RuleNotFoundException(str(rule_id))
        self.rules = [r for r in self.rules if r.id != rule_id]
        del self._rule_index[rule_id]
        logger.info(f"Rule removed from enforcement set", rule_id=str(rule_id))

    async def execute(self, input_data: dict[str, Any]) -> list[RuleEnforcementResult]:
        """Evaluate an action against all active rules.

        Args:
            input_data: Dictionary containing:
                - action: The GovernanceAction to evaluate
                - context: Optional additional context for evaluation

        Returns:
            List of enforcement results for each evaluated rule.

        Raises:
            AgentExecutionException: If rule enforcement fails.
        """
        try:
            action = input_data.get("action")
            if not isinstance(action, GovernanceAction):
                raise ValueError("Input must contain a valid 'action' of type GovernanceAction")

            context = input_data.get("context", {})
            results: list[RuleEnforcementResult] = []

            logger.info(
                f"Evaluating action '{action.id}' against {len(self.rules)} rules",
                action_id=str(action.id),
                rule_count=len(self.rules),
            )

            for rule in self.rules:
                if not rule.is_active:
                    continue
                result = await self._evaluate_rule(rule, action, context)
                results.append(result)

            violations = [r for r in results if r.is_violation]
            logger.info(
                f"Rule enforcement complete: {len(violations)} violations found",
                action_id=str(action.id),
                violation_count=len(violations),
            )

            return results

        except Exception as e:
            logger.error(f"Rule enforcement failed: {e}", error=str(e))
            raise AgentExecutionException(self.name, str(e)) from e

    async def _evaluate_rule(
        self, rule: Rule, action: GovernanceAction, context: dict[str, Any]
    ) -> RuleEnforcementResult:
        """Evaluate a single rule against an action."""
        if self.llm:
            return await self._evaluate_with_llm(rule, action, context)
        return self._evaluate_programmatically(rule, action, context)

    async def _evaluate_with_llm(
        self, rule: Rule, action: GovernanceAction, context: dict[str, Any]
    ) -> RuleEnforcementResult:
        """Evaluate a rule using the LLM."""
        system_prompt = self._build_system_prompt()
        user_message = self._build_evaluation_prompt(rule, action, context)

        messages = self._build_messages(system_prompt, user_message)
        response = await self.llm.ainvoke(messages)

        try:
            result_data = json.loads(response.content)
            return RuleEnforcementResult(
                rule_id=rule.id,
                rule_name=rule.name,
                action_id=action.id,
                is_violation=result_data.get("is_violation", False),
                severity=RuleSeverity(result_data.get("severity", rule.severity.value)),
                message=result_data.get("message", ""),
                details=result_data.get("details", {}),
                recommended_actions=result_data.get("recommended_actions", []),
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                f"Failed to parse LLM response for rule '{rule.name}': {e}",
                rule_id=str(rule.id),
            )
            return self._evaluate_programmatically(rule, action, context)

    def _evaluate_programmatically(
        self, rule: Rule, action: GovernanceAction, context: dict[str, Any]
    ) -> RuleEnforcementResult:
        """Evaluate a rule using programmatic logic."""
        is_violation = self._check_conditions(rule.conditions, action, context)

        return RuleEnforcementResult(
            rule_id=rule.id,
            rule_name=rule.name,
            action_id=action.id,
            is_violation=is_violation,
            severity=rule.severity if is_violation else RuleSeverity.LOW,
            message=(
                f"Action violates rule '{rule.name}': {rule.description}"
                if is_violation
                else f"Action complies with rule '{rule.name}'"
            ),
            details={"rule_category": rule.category.value, "action_type": action.action_type.value},
            recommended_actions=rule.actions if is_violation else [],
        )

    def _check_conditions(
        self, conditions: dict[str, Any], action: GovernanceAction, context: dict[str, Any]
    ) -> bool:
        """Check if an action violates the rule conditions."""
        if not conditions:
            return False

        action_type_match = conditions.get("action_types")
        if action_type_match and action.action_type.value not in action_type_match:
            return False

        target_type_match = conditions.get("target_types")
        if target_type_match and action.target_type not in target_type_match:
            return False

        metadata_conditions = conditions.get("metadata", {})
        for key, expected_value in metadata_conditions.items():
            if action.metadata.get(key) != expected_value:
                return False

        return True

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        return (
            "You are a community governance rule enforcer. Your job is to evaluate "
            "whether a given action violates community rules. You must respond with "
            "a JSON object containing: is_violation (boolean), severity (string), "
            "message (string), details (object), and recommended_actions (array of strings). "
            "Be fair, consistent, and consider the context of each action."
        )

    def _build_evaluation_prompt(
        self, rule: Rule, action: GovernanceAction, context: dict[str, Any]
    ) -> str:
        """Build the evaluation prompt for the LLM."""
        return f"""Evaluate the following action against the community rule.

Rule:
- Name: {rule.name}
- Description: {rule.description}
- Category: {rule.category.value}
- Severity: {rule.severity.value}
- Conditions: {json.dumps(rule.conditions, indent=2)}

Action:
- Type: {action.action_type.value}
- Target: {action.target_type} ({action.target_id})
- Actor: {action.actor_id}
- Reason: {action.reason or 'N/A'}
- Metadata: {json.dumps(action.metadata, indent=2)}

Context:
{json.dumps(context, indent=2)}

Determine if this action violates the rule. Respond with JSON only."""

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the Rule Enforcer Agent."""
        base_health = await super().health_check()
        base_health.update(
            {
                "active_rules": len([r for r in self.rules if r.is_active]),
                "total_rules": len(self.rules),
            }
        )
        return base_health

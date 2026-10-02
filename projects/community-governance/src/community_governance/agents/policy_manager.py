"""Policy Manager Agent for community governance."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseLanguageModel

from community_governance.agents.base import BaseAgent
from community_governance.config.logging_config import get_logger
from community_governance.exceptions import (
    AgentExecutionException,
    PolicyEnforcementException,
    PolicyNotFoundException,
)
from community_governance.models.policy import Policy, PolicyCreate, PolicyStatus, PolicyUpdate
from community_governance.models.rule import Rule

logger = get_logger(__name__)


class PolicyManagerAgent(BaseAgent[dict[str, Any], Policy]):
    """Agent responsible for creating, updating, and managing governance policies.

    Uses LangChain DeepAgents to draft policy language, ensure consistency
    across policies, manage policy lifecycle, and recommend policy updates
    based on governance analytics.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        policies: list[Policy] | None = None,
        rules: list[Rule] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Policy Manager Agent.

        Args:
            llm: Language model for policy management reasoning.
            policies: List of existing policies.
            rules: List of available rules for policy association.
            **kwargs: Additional configuration options.
        """
        super().__init__(llm=llm, name="policy_manager", **kwargs)
        self.policies = policies or []
        self.rules = rules or []
        self._policy_index: dict[UUID, Policy] = {p.id: p for p in self.policies}
        self._rule_index: dict[UUID, Rule] = {r.id: r for r in self.rules}

    async def _setup(self) -> None:
        """Setup policy and rule indices."""
        self._policy_index = {p.id: p for p in self.policies}
        self._rule_index = {r.id: r for r in self.rules}
        logger.info(
            f"Policy Manager Agent loaded with {len(self.policies)} policies "
            f"and {len(self.rules)} rules",
            agent_name=self.name,
            policy_count=len(self.policies),
            rule_count=len(self.rules),
        )

    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the manager.

        Args:
            policy: The policy to add.
        """
        self.policies.append(policy)
        self._policy_index[policy.id] = policy
        logger.info(f"Policy '{policy.name}' added", policy_id=str(policy.id))

    def remove_policy(self, policy_id: UUID) -> None:
        """Remove a policy from the manager.

        Args:
            policy_id: The ID of the policy to remove.

        Raises:
            PolicyNotFoundException: If the policy is not found.
        """
        if policy_id not in self._policy_index:
            raise PolicyNotFoundException(str(policy_id))
        self.policies = [p for p in self.policies if p.id != policy_id]
        del self._policy_index[policy_id]

    async def execute(self, input_data: dict[str, Any]) -> Policy:
        """Execute a policy management operation.

        Supports creating new policies, updating existing ones, and
        recommending policy changes.

        Args:
            input_data: Dictionary containing:
                - operation: One of 'create', 'update', 'recommend'
                - policy_data: Policy data for create/update operations
                - policy_id: Required for update operations
                - analytics: Optional analytics data for recommendations

        Returns:
            The created, updated, or recommended policy.

        Raises:
            PolicyNotFoundException: If the target policy is not found.
            PolicyEnforcementException: If the operation fails.
            AgentExecutionException: If the agent execution fails.
        """
        try:
            operation = input_data.get("operation", "create")
            logger.info(f"Executing policy operation: {operation}", agent_name=self.name)

            if operation == "create":
                return await self._create_policy(input_data)
            elif operation == "update":
                return await self._update_policy(input_data)
            elif operation == "recommend":
                return await self._recommend_policy(input_data)
            else:
                raise ValueError(f"Unknown policy operation: {operation}")

        except (PolicyNotFoundException, PolicyEnforcementException):
            raise
        except Exception as e:
            logger.error(f"Policy management failed: {e}", error=str(e))
            raise AgentExecutionException(self.name, str(e)) from e

    async def _create_policy(self, input_data: dict[str, Any]) -> Policy:
        """Create a new governance policy.

        Args:
            input_data: Dictionary containing policy_data.

        Returns:
            The newly created policy.
        """
        policy_data = input_data.get("policy_data", {})
        if isinstance(policy_data, dict):
            policy_create = PolicyCreate(**policy_data)
        else:
            policy_create = policy_data

        if self.llm:
            enhanced_data = await self._enhance_policy_with_llm(policy_create)
            policy_create = PolicyCreate(**enhanced_data)

        policy = Policy(
            name=policy_create.name,
            description=policy_create.description,
            scope=policy_create.scope,
            scope_target=policy_create.scope_target,
            rules=policy_create.rules,
            guidelines=policy_create.guidelines,
            enforcement_level=policy_create.enforcement_level,
            effective_date=policy_create.effective_date,
            expiration_date=policy_create.expiration_date,
            created_by=policy_create.created_by,
            status=PolicyStatus.DRAFT,
        )

        self.add_policy(policy)
        logger.info(f"Policy '{policy.name}' created", policy_id=str(policy.id))
        return policy

    async def _update_policy(self, input_data: dict[str, Any]) -> Policy:
        """Update an existing governance policy.

        Args:
            input_data: Dictionary containing policy_id and policy_data.

        Returns:
            The updated policy.

        Raises:
            PolicyNotFoundException: If the policy is not found.
        """
        policy_id = input_data.get("policy_id")
        if not policy_id:
            raise ValueError("policy_id is required for update operations")

        policy = self._policy_index.get(policy_id)
        if not policy:
            raise PolicyNotFoundException(str(policy_id))

        update_data = input_data.get("policy_data", {})
        if isinstance(update_data, dict):
            policy_update = PolicyUpdate(**update_data)
        else:
            policy_update = update_data

        update_dict = policy_update.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(policy, field, value)

        policy.version += 1
        policy.updated_at = datetime.utcnow()

        logger.info(
            f"Policy '{policy.name}' updated to version {policy.version}",
            policy_id=str(policy.id),
            version=policy.version,
        )
        return policy

    async def _recommend_policy(self, input_data: dict[str, Any]) -> Policy:
        """Recommend a new policy based on governance analytics.

        Args:
            input_data: Dictionary containing analytics data.

        Returns:
            A recommended policy draft.
        """
        analytics = input_data.get("analytics", {})

        if self.llm:
            recommendation = await self._recommend_with_llm(analytics)
        else:
            recommendation = self._recommend_programmatically(analytics)

        policy_create = PolicyCreate(**recommendation)
        return Policy(
            name=policy_create.name,
            description=policy_create.description,
            scope=policy_create.scope,
            guidelines=policy_create.guidelines,
            status=PolicyStatus.DRAFT,
            created_by="policy_manager_agent",
        )

    async def _enhance_policy_with_llm(self, policy_create: PolicyCreate) -> dict[str, Any]:
        """Enhance policy data using the LLM.

        Args:
            policy_create: The policy creation data.

        Returns:
            Enhanced policy data dictionary.
        """
        system_prompt = (
            "You are a community governance policy expert. Your job is to review "
            "and enhance policy drafts to ensure they are clear, comprehensive, and "
            "aligned with community values. Respond with a JSON object containing "
            "the enhanced policy fields."
        )
        user_message = f"""Review and enhance the following policy draft:

Name: {policy_create.name}
Description: {policy_create.description}
Scope: {policy_create.scope.value}
Guidelines: {json.dumps(policy_create.guidelines, indent=2)}

Provide an enhanced version with improved clarity and completeness."""

        messages = self._build_messages(system_prompt, user_message)
        response = await self.llm.ainvoke(messages)

        try:
            result_data = json.loads(response.content)
            return result_data
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse LLM policy enhancement response")
            return policy_create.model_dump()

    async def _recommend_with_llm(self, analytics: dict[str, Any]) -> dict[str, Any]:
        """Generate a policy recommendation using the LLM.

        Args:
            analytics: Governance analytics data.

        Returns:
            Recommended policy data.
        """
        system_prompt = (
            "You are a community governance policy advisor. Based on governance "
            "analytics, recommend new policies or policy updates to improve community "
            "governance. Respond with a JSON object containing: name, description, "
            "scope, and guidelines."
        )
        user_message = f"""Based on the following governance analytics, recommend a policy:

{json.dumps(analytics, indent=2)}

Provide a policy recommendation that addresses the identified issues."""

        messages = self._build_messages(system_prompt, user_message)
        response = await self.llm.ainvoke(messages)

        try:
            return json.loads(response.content)
        except (json.JSONDecodeError, ValueError):
            return self._recommend_programmatically(analytics)

    def _recommend_programmatically(self, analytics: dict[str, Any]) -> dict[str, Any]:
        """Generate a policy recommendation using programmatic logic.

        Args:
            analytics: Governance analytics data.

        Returns:
            Recommended policy data.
        """
        violations = analytics.get("violations_by_category", {})
        top_category = max(violations, key=violations.get) if violations else "general"

        return {
            "name": f"Enhanced {top_category.replace('_', ' ').title()} Policy",
            "description": (
                f"Automatically generated policy to address elevated {top_category} "
                "violations detected in governance analytics."
            ),
            "scope": "global",
            "guidelines": [
                f"Review all {top_category} related actions for compliance",
                "Escalate repeated violations to community moderators",
                "Document all enforcement actions for transparency",
            ],
        }

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the Policy Manager Agent.

        Returns:
            Health status dictionary.
        """
        base_health = await super().health_check()
        active_policies = len([p for p in self.policies if p.status == PolicyStatus.ACTIVE])
        base_health.update(
            {
                "total_policies": len(self.policies),
                "active_policies": active_policies,
                "available_rules": len(self.rules),
            }
        )
        return base_health

"""Access Controller Agent - Enforces access control policies.

Uses LangChain DeepAgents to evaluate access requests against
configured policies and make grant/deny decisions with reasoning.
"""

from __future__ import annotations

from datetime import UTC
from typing import Any
from uuid import UUID

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from tier_management.agents.base import BaseAgent
from tier_management.config.logging_config import get_logger
from tier_management.models.schemas import (
    AccessCheckRequest,
    AccessCheckResponse,
    AccessDecision,
    AccessPolicy,
)

logger = get_logger(__name__)


class AccessControllerAgent(BaseAgent[AccessCheckRequest, AccessCheckResponse]):
    """Agent that controls access to gated community resources.

    This agent uses LangChain DeepAgents to evaluate access requests
    against a hierarchy of policies, considering member tier, resource
    sensitivity, time-based rules, and contextual factors.
    """

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Access Controller Agent.

        Args:
            llm: LangChain language model for access decision reasoning.
            tools: Tools available to the agent (e.g., policy lookup).
            **kwargs: Additional configuration parameters.
        """
        super().__init__(name="AccessControllerAgent", llm=llm, tools=tools, **kwargs)
        self.policies: dict[UUID, AccessPolicy] = {}
        self.default_decision = AccessDecision.DENIED

    async def execute(self, input_data: AccessCheckRequest) -> AccessCheckResponse:
        """Evaluate an access request and return a decision.

        Args:
            input_data: The access check request containing member_id,
                resource, action, and context.

        Returns:
            AccessCheckResponse with the decision and explanation.

        Raises:
            ValueError: If required fields are missing.
        """
        if not input_data.member_id or not input_data.resource:
            raise ValueError("member_id and resource are required")

        logger.info(
            "checking_access",
            member_id=str(input_data.member_id),
            resource=input_data.resource,
            action=input_data.action,
        )

        response = await self._evaluate_access(input_data)

        logger.info(
            "access_check_complete",
            member_id=str(input_data.member_id),
            resource=input_data.resource,
            decision=str(response.decision),
        )

        return response

    async def _evaluate_access(
        self,
        request: AccessCheckRequest,
    ) -> AccessCheckResponse:
        """Evaluate access request against policies.

        Args:
            request: The access check request.

        Returns:
            AccessCheckResponse with decision.
        """
        from datetime import datetime

        # Find applicable policies
        applicable = self._find_applicable_policies(request.resource, request.action)

        if not applicable:
            # Default deny if no policies match
            return AccessCheckResponse(
                member_id=request.member_id,
                resource=request.resource,
                action=request.action,
                decision=self.default_decision,
                reason="No applicable policy found",
                checked_at=datetime.now(UTC),
            )

        # Evaluate policies by priority
        decision = self._apply_policies(applicable, request)

        return AccessCheckResponse(
            member_id=request.member_id,
            resource=request.resource,
            action=request.action,
            decision=decision,
            reason=f"Access {decision.value} based on policy evaluation",
            checked_at=datetime.now(UTC),
            policy_id=applicable[0].id if applicable else None,
        )

    def _find_applicable_policies(
        self,
        resource: str,
        action: str,
    ) -> list[AccessPolicy]:
        """Find policies applicable to the resource and action.

        Args:
            resource: The resource being accessed.
            action: The action being performed.

        Returns:
            List of applicable policies sorted by priority.
        """
        applicable = [
            p for p in self.policies.values()
            if p.resource == resource and p.action == action and p.enabled
        ]
        return sorted(applicable, key=lambda p: p.priority, reverse=True)

    def _apply_policies(
        self,
        policies: list[AccessPolicy],
        request: AccessCheckRequest,
    ) -> AccessDecision:
        """Apply policies to determine access decision.

        Args:
            policies: Applicable policies sorted by priority.
            request: The access check request.

        Returns:
            Final access decision.
        """
        for policy in policies:
            if policy.effect == AccessDecision.GRANTED:
                # Check conditions
                if self._check_conditions(policy.conditions, request.context):
                    return AccessDecision.GRANTED
            elif policy.effect == AccessDecision.DENIED:
                return AccessDecision.DENIED

        return self.default_decision

    def _check_conditions(
        self,
        conditions: dict[str, Any],
        context: dict[str, Any],
    ) -> bool:
        """Check if request context satisfies policy conditions.

        Args:
            conditions: Policy conditions to check.
            context: Request context data.

        Returns:
            True if all conditions are satisfied.
        """
        for key, value in conditions.items():
            if key not in context:
                return False
            if context[key] != value:
                return False
        return True

    def add_policy(self, policy: AccessPolicy) -> None:
        """Add a policy to the agent's policy set.

        Args:
            policy: The access policy to add.
        """
        self.policies[policy.id] = policy
        logger.info("policy_added", policy_id=str(policy.id), resource=policy.resource)

    def remove_policy(self, policy_id: UUID) -> None:
        """Remove a policy from the agent's policy set.

        Args:
            policy_id: The policy identifier to remove.
        """
        if policy_id in self.policies:
            del self.policies[policy_id]
            logger.info("policy_removed", policy_id=str(policy_id))

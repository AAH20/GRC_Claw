"""Policy Enforcer Agent — enforces access policies in real-time."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from langchain_core.prompts import ChatPromptTemplate

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel
from access_control.agents.base import AgentContext, BaseAgent
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from access_control.config import Settings
from access_control.models.enums import AccessDecision, PolicyEffect
from access_control.models.schemas import AccessRequest, AccessResult, Policy


class PolicyEnforcerInput(BaseModel):
    """Input for the policy enforcer agent."""

    request: AccessRequest
    policies: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class PolicyEnforcerOutput(BaseModel):
    """Output from the policy enforcer agent."""

    decision: AccessDecision
    enforced_policies: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    obligations: list[str] = Field(default_factory=list)
    reason: str = ""


class PolicyEnforcerAgent(BaseAgent[PolicyEnforcerInput, PolicyEnforcerOutput]):
    """Agent that enforces access policies in real-time.

    Uses LangChain DeepAgents to evaluate policies against access requests,
    detect violations, and determine appropriate enforcement actions.
    """

    def __init__(self, llm: BaseLanguageModel, settings: Settings) -> None:
        super().__init__(
            llm=llm,
            settings=settings,
            name="policy_enforcer",
            description="Enforces access policies with real-time evaluation and violation detection",  # noqa: E501
        )

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgents instance for policy enforcement."""
        system_prompt = """You are a policy enforcement engine for an access control system.
Evaluate the given access request against the provided policies.
Detect any policy violations and determine enforcement actions.
Consider policy priority, deny-override semantics, and obligation requirements.
Respond with a JSON object containing: decision, enforced_policies, violations, obligations,
        reason."""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        chain = prompt | self.llm
        return chain

    async def run(
        self, payload: PolicyEnforcerInput, context: AgentContext | None = None
    ) -> PolicyEnforcerOutput:
        """Enforce policies against an access request.

        Args:
            payload: The access request and policies to enforce.
            context: Optional execution context.

        Returns:
            The enforcement result.
        """
        agent = self._build_agent()

        input_data = {
            "input": json.dumps(
                {
                    "request": payload.request.model_dump(mode="json"),
                    "policies": payload.policies,
                    "context": payload.context,
                }
            )
        }

        response = await agent.ainvoke(input_data)

        content = response.content if hasattr(response, "content") else str(response)

        try:
            parsed = json.loads(content)
            return PolicyEnforcerOutput(**parsed)
        except (json.JSONDecodeError, TypeError):
            return PolicyEnforcerOutput(
                decision=AccessDecision.DENY,
                violations=["Failed to parse agent response"],
                reason="Policy enforcement failed due to parsing error",
            )

    async def enforce(
        self, request: AccessRequest, policies: list[Policy] | None = None
    ) -> AccessResult:
        """Enforce policies against an access request.

        Args:
            request: The access request to evaluate.
            policies: Optional list of policies to enforce.

        Returns:
            An AccessResult with the enforcement outcome.
        """
        policy_dicts = [p.model_dump(mode="json") for p in (policies or [])]

        payload = PolicyEnforcerInput(
            request=request,
            policies=policy_dicts,
        )
        output = await self.run(payload)

        return AccessResult(
            request=request,
            decision=output.decision,
            reason=output.reason,
            obligations=output.obligations,
            policy_ids=output.enforced_policies,
        )

    async def check_compliance(self, policies: list[Policy]) -> list[str]:
        """Check a set of policies for compliance issues.

        Args:
            policies: The policies to check.

        Returns:
            A list of compliance issue descriptions.
        """
        issues: list[str] = []

        for policy in policies:
            if not policy.enabled:
                continue

            for rule in policy.rules:
                if rule.effect == PolicyEffect.DENY and not rule.conditions:
                    issues.append(
                        f"Policy '{policy.name}' has an unconditional deny rule for "
                        f"{rule.action} on {rule.resource}"
                    )

        return issues

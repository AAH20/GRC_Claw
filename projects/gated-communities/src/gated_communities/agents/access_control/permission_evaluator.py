"""Permission Evaluator Agent — evaluates access requests using AI reasoning."""

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
from access_control.models.enums import AccessDecision
from access_control.models.schemas import AccessRequest, AccessResult


class PermissionEvaluatorInput(BaseModel):
    """Input for the permission evaluator agent."""

    request: AccessRequest
    policies: list[dict[str, Any]] = Field(default_factory=list)
    roles: list[dict[str, Any]] = Field(default_factory=list)


class PermissionEvaluatorOutput(BaseModel):
    """Output from the permission evaluator agent."""

    decision: AccessDecision
    reason: str = ""
    obligations: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    policy_ids: list[str] = Field(default_factory=list)


class PermissionEvaluatorAgent(
    BaseAgent[PermissionEvaluatorInput, PermissionEvaluatorOutput]
):
    """Agent that evaluates whether a principal should be granted access.

    Uses LangChain DeepAgents to perform contextual reasoning about the
    access request, taking into account policies, roles, and environmental
    context such as time of day, location, and device posture.
    """

    def __init__(self, llm: BaseLanguageModel, settings: Settings) -> None:
        super().__init__(
            llm=llm,
            settings=settings,
            name="permission_evaluator",
            description="Evaluates access requests using AI-driven contextual reasoning",
        )

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgents instance for permission evaluation."""
        system_prompt = """You are a permission evaluation engine for an access control system.
Analyze the given access request against the provided policies and roles.
Consider contextual factors such as time, location, and risk indicators.
Respond with a JSON object containing: decision, reason, obligations, confidence, policy_ids.
Decisions must be one of: allow, deny, conditional, abstain."""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        chain = prompt | self.llm
        return chain

    async def run(
        self, payload: PermissionEvaluatorInput, context: AgentContext | None = None
    ) -> PermissionEvaluatorOutput:
        """Evaluate an access request and return the decision.

        Args:
            payload: The access request plus policy and role context.
            context: Optional execution context.

        Returns:
            The evaluation result with decision, reason, and obligations.
        """
        agent = self._build_agent()

        input_data = {
            "input": json.dumps(
                {
                    "request": payload.request.model_dump(mode="json"),
                    "policies": payload.policies,
                    "roles": payload.roles,
                }
            )
        }

        response = await agent.ainvoke(input_data)

        # Parse the LLM response
        content = response.content if hasattr(response, "content") else str(response)

        try:
            parsed = json.loads(content)
            return PermissionEvaluatorOutput(**parsed)
        except (json.JSONDecodeError, TypeError):
            # Fallback: try to extract JSON from the response
            return PermissionEvaluatorOutput(
                decision=AccessDecision.ABSTAIN,
                reason="Failed to parse agent response",
                confidence=0.0,
            )

    async def evaluate(
        self,
        request: AccessRequest,
        policies: list[dict[str, Any]] | None = None,
        roles: list[dict[str, Any]] | None = None,
    ) -> AccessResult:
        """Convenience method to evaluate a request and return a full AccessResult.

        Args:
            request: The access request to evaluate.
            policies: Optional list of policy dicts for context.
            roles: Optional list of role dicts for context.

        Returns:
            A complete AccessResult with the evaluation outcome.
        """
        payload = PermissionEvaluatorInput(
            request=request,
            policies=policies or [],
            roles=roles or [],
        )
        output = await self.run(payload)

        return AccessResult(
            request=request,
            decision=output.decision,
            reason=output.reason,
            obligations=output.obligations,
            policy_ids=output.policy_ids,
            confidence=output.confidence,
        )

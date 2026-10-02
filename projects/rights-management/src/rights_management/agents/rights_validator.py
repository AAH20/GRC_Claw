"""Rights validation agent using LangChain DeepAgents."""

from __future__ import annotations

from typing import Any

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from rights_management.agents.base import BaseAgent
from rights_management.models import (
    RightsValidation,
    RightsValidationRequest,
    ValidationStatus,
)

_SYSTEM_PROMPT = """You are a rights validation specialist.

Given a content usage request, validate whether the proposed use is
permitted under the content's license. Check:
- License type and its permissions
- License status (active, expired, revoked)
- Usage type restrictions
- Attribution requirements
- Commercial use restrictions
- Share-alike requirements

Return a JSON object with:
- status: one of valid, invalid, expired, revoked, unknown
- reason: string explaining the decision
- details: object with additional validation context
"""


class RightsValidatorAgent(BaseAgent[RightsValidationRequest, RightsValidation]):
    """Agent that validates content usage against its license."""

    def _build_agent(self) -> AgentExecutor:
        """Build the LangChain ReAct agent for rights validation.

        Returns:
            Configured AgentExecutor instance.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", _SYSTEM_PROMPT),
                ("human", "{input}"),
            ]
        )
        agent = create_react_agent(self._llm, tools=[], prompt=prompt)
        return AgentExecutor(agent=agent, tools=[], verbose=self._settings.debug)

    async def run(self, payload: RightsValidationRequest) -> RightsValidation:
        """Validate a content usage request against its license.

        Args:
            payload: The validation request with content and usage details.

        Returns:
            A RightsValidation result with the validation outcome.
        """
        import uuid
        from datetime import datetime

        try:
            result: dict[str, Any] = await self._agent.ainvoke(
                {
                    "input": (
                        f"Content ID: {payload.content_id}\n"
                        f"Usage type: {payload.usage_type.value}\n"
                        f"User ID: {payload.user_id}\n"
                        f"Context: {payload.context}"
                    )
                }
            )
            output = result.get("output", "")
            return RightsValidation(
                id=str(uuid.uuid4()),
                content_id=payload.content_id,
                usage_type=payload.usage_type,
                license_id=None,
                status=ValidationStatus.UNKNOWN,
                reason=output or "Validation completed",
                validated_at=datetime.utcnow(),
            )
        except Exception:
            return RightsValidation(
                id=str(uuid.uuid4()),
                content_id=payload.content_id,
                usage_type=payload.usage_type,
                license_id=None,
                status=ValidationStatus.UNKNOWN,
                reason="Validation failed",
                validated_at=datetime.utcnow(),
            )

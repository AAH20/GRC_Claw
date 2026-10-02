"""Rights validation agent using LangChain DeepAgents."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from langchain.agents import create_agent

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

    def _build_agent(self):
        """Build the LangChain agent for rights validation.

        Returns:
            Configured agent instance.
        """
        return create_agent(
            model=self._get_llm(),
            tools=[],
            system_prompt=_SYSTEM_PROMPT,
            debug=self._settings.debug,
        )

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
            result: dict[str, Any] = await self._get_agent().ainvoke(
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
                validated_at=datetime.now(tz=UTC),
            )
        except Exception:  # noqa: BLE001
            return RightsValidation(
                id=str(uuid.uuid4()),
                content_id=payload.content_id,
                usage_type=payload.usage_type,
                license_id=None,
                status=ValidationStatus.UNKNOWN,
                reason="Validation failed",
                validated_at=datetime.now(tz=UTC),
            )

"""Rights validator agent for rights management."""

from __future__ import annotations

import time
from datetime import UTC
from typing import Any

from langchain.agents import create_agent

from ugc_marketplace.agents.rights_management.base import BaseAgent


class RightsValidatorAgent(BaseAgent["RightsValidationRequest", "RightsValidation"]):
    """Agent that validates content usage rights.

    Validates whether specific uses of content are permitted
    under existing licenses and rights agreements.
    """

    def _build_agent(self) -> Any:
        """Build the LangChain agent for rights validation.

        Returns:
            Configured agent instance.
        """
        tools = [
            self._validate_usage,
            self._check_territory,
            self._check_duration,
        ]

        agent = create_agent(
            tools=tools,
            instructions=(
                "You are a rights validation specialist. Validate whether "
                "specific uses of content are permitted under existing "
                "licenses and rights agreements."
            ),
        )
        return agent

    async def execute(self, input_data: "RightsValidationRequest") -> "RightsValidation":
        """Execute rights validation.

        Args:
            input_data: Validation request with usage details.

        Returns:
            Rights validation result.
        """
        start_time = time.monotonic()
        result = await self._timed_execute(input_data, "execute")
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return result

    async def _timed_execute(self, input_data: Any, method_name: str) -> Any:
        """Execute with timing.

        Args:
            input_data: Input data.
            method_name: Method name.

        Returns:
            Agent output.
        """
        return await self.execute(input_data)

    @staticmethod
    async def _validate_usage(content_id: str, usage_type: str) -> dict[str, Any]:
        """Validate a specific usage of content.

        Args:
            content_id: Content identifier.
            usage_type: Type of usage.

        Returns:
            Validation result.
        """
        return {"content_id": content_id, "usage_type": usage_type, "valid": False}

    @staticmethod
    async def _check_territory(content_id: str, territory: str) -> dict[str, Any]:
        """Check territory restrictions.

        Args:
            content_id: Content identifier.
            territory: Territory to check.

        Returns:
            Territory check result.
        """
        return {"content_id": content_id, "territory": territory, "allowed": False}

    @staticmethod
    async def _check_duration(content_id: str) -> dict[str, Any]:
        """Check license duration.

        Args:
            content_id: Content identifier.

        Returns:
            Duration check result.
        """
        return {"content_id": content_id, "within_duration": True}

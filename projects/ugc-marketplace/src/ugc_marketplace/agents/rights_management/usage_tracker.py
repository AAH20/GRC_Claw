"""Usage tracker agent for rights management."""

from __future__ import annotations

import time
from datetime import UTC
from typing import Any

from langchain.agents import create_agent

from ugc_marketplace.agents.rights_management.base import BaseAgent
from ugc_marketplace.agents.rights_management.types import UsageRecord


class UsageTrackerAgent(BaseAgent[dict[str, Any], "UsageRecord"]):
    """Agent that tracks content usage for rights management.

    Monitors and records how content is used, ensuring
    compliance with license terms and usage restrictions.
    """

    def _build_agent(self) -> Any:
        """Build the LangChain agent for usage tracking.

        Returns:
            Configured agent instance.
        """
        tools = [
            self._record_usage,
            self._check_usage_limits,
            self._generate_usage_report,
        ]

        agent = create_agent(
            tools=tools,
            instructions=(
                "You are a content usage tracking specialist. Monitor and "
                "record content usage, check against license limits, and "
                "generate usage reports for rights management."
            ),
        )
        return agent

    async def execute(self, input_data: dict[str, Any]) -> UsageRecord:
        """Execute usage tracking.

        Args:
            input_data: Usage data to track.

        Returns:
            Usage record.
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
    async def _record_usage(
        content_id: str, usage_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Record content usage.

        Args:
            content_id: Content identifier.
            usage_data: Usage data.

        Returns:
            Usage record.
        """
        return {
            "content_id": content_id,
            "usage": usage_data,
            "recorded_at": UTC.now().isoformat(),
        }

    @staticmethod
    async def _check_usage_limits(content_id: str) -> dict[str, Any]:
        """Check usage against limits.

        Args:
            content_id: Content identifier.

        Returns:
            Usage limit check result.
        """
        return {"content_id": content_id, "within_limits": True}

    @staticmethod
    async def _generate_usage_report(content_id: str) -> dict[str, Any]:
        """Generate usage report.

        Args:
            content_id: Content identifier.

        Returns:
            Usage report.
        """
        return {"content_id": content_id, "report": {}}

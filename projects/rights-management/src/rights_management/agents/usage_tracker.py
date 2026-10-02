"""Usage tracking agent using LangChain DeepAgents."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from langchain.agents import create_agent

from rights_management.agents.base import BaseAgent
from rights_management.models import UsageRecord, UsageSummary

_SYSTEM_PROMPT = """You are a content usage tracking specialist.

Your job is to record and analyze content usage events. Given a usage
event, validate it, enrich it with context, and return a structured
usage record.

Return a JSON object representing the usage record with fields:
- id: unique identifier
- content_id: string
- usage_type: one of view, download, reproduce, distribute, modify, commercial
- user_id: string
- timestamp: ISO 8601 datetime
- context: object with additional details
- license_id: string or null
"""


class UsageTrackerAgent(BaseAgent[dict[str, Any], UsageRecord]):
    """Agent that records and analyzes content usage events."""

    def _build_agent(self):
        """Build the LangChain agent for usage tracking.

        Returns:
            Configured agent instance.
        """
        return create_agent(
            model=self._get_llm(),
            tools=[],
            system_prompt=_SYSTEM_PROMPT,
            debug=self._settings.debug,
        )

    async def run(self, payload: dict[str, Any]) -> UsageRecord:
        """Process a usage event and return a structured record.

        Args:
            payload: Raw usage event data.

        Returns:
            A validated UsageRecord.
        """
        import uuid
        from datetime import datetime

        try:
            result: dict[str, Any] = await self._get_agent().ainvoke(
                {"input": str(payload)}
            )
            output = result.get("output", "{}")
            usage_type = payload.get("usage_type", "view")
            if hasattr(usage_type, "value"):
                usage_type = usage_type.value
            return UsageRecord(
                id=str(uuid.uuid4()),
                content_id=str(payload.get("content_id", "")),
                usage_type=str(usage_type),
                user_id=str(payload.get("user_id", "")),
                timestamp=datetime.now(tz=UTC),
                context={"raw_output": output},
            )
        except Exception:  # noqa: BLE001
            usage_type = payload.get("usage_type", "view")
            if hasattr(usage_type, "value"):
                usage_type = usage_type.value
            return UsageRecord(
                id=str(uuid.uuid4()),
                content_id=str(payload.get("content_id", "")),
                usage_type=str(usage_type),
                user_id=str(payload.get("user_id", "")),
                timestamp=datetime.now(tz=UTC),
                context={"error": "Usage tracking failed"},
            )

    async def summarize(self, content_id: str, records: list[UsageRecord]) -> UsageSummary:
        """Generate a usage summary for a piece of content.

        Args:
            content_id: The content identifier.
            records: List of usage records to summarize.

        Returns:
            Aggregated UsageSummary.
        """
        from collections import Counter
        from datetime import datetime

        by_type: Counter[str] = Counter()
        users: set[str] = set()
        timestamps: list[datetime] = []

        for record in records:
            by_type[record.usage_type.value] += 1
            users.add(record.user_id)
            timestamps.append(record.timestamp)

        return UsageSummary(
            content_id=content_id,
            total_uses=len(records),
            by_type=dict(by_type),
            unique_users=len(users),
            first_used=min(timestamps) if timestamps else None,
            last_used=max(timestamps) if timestamps else None,
        )

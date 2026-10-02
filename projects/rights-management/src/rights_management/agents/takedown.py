"""Takedown processing agent using LangChain DeepAgents."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from langchain.agents import create_agent

from rights_management.agents.base import BaseAgent
from rights_management.models import TakedownProcessRequest, TakedownRequest, TakedownStatus

_SYSTEM_PROMPT = """You are a content takedown processing specialist.

Review takedown requests and determine the appropriate action. Consider:
- Validity of the legal basis
- Evidence provided
- Content license status
- Jurisdictional requirements (DMCA, GDPR, etc.)
- Fair use considerations

Return a JSON object with:
- action: one of approved, rejected, pending
- notes: string with reasoning
- additional_actions: list of strings with follow-up steps
"""


class TakedownAgent(BaseAgent[dict[str, Any], TakedownRequest]):
    """Agent that processes content takedown requests."""

    def _build_agent(self):
        """Build the LangChain agent for takedown processing.

        Returns:
            Configured agent instance.
        """
        return create_agent(
            model=self._get_llm(),
            tools=[],
            system_prompt=_SYSTEM_PROMPT,
            debug=self._settings.debug,
        )

    async def run(self, payload: dict[str, Any]) -> TakedownRequest:
        """Process a takedown request.

        Args:
            payload: The takedown request data with processing instructions.

        Returns:
            The updated TakedownRequest with the processing outcome.
        """
        import uuid
        from datetime import datetime

        try:
            result: dict[str, Any] = await self._get_agent().ainvoke(
                {"input": str(payload)}
            )
            output = result.get("output", "")
            return TakedownRequest(
                id=str(payload.get("id", uuid.uuid4())),
                content_id=str(payload.get("content_id", "")),
                requester_id=str(payload.get("requester_id", "")),
                reason=str(payload.get("reason", "")),
                legal_basis=payload.get("legal_basis"),
                status=TakedownStatus.PENDING,
                created_at=datetime.now(tz=UTC),
                processed_at=None,
                metadata={"agent_output": output} if output else {},
            )
        except Exception:  # noqa: BLE001
            return TakedownRequest(
                id=str(payload.get("id", uuid.uuid4())),
                content_id=str(payload.get("content_id", "")),
                requester_id=str(payload.get("requester_id", "")),
                reason=str(payload.get("reason", "")),
                legal_basis=payload.get("legal_basis"),
                status=TakedownStatus.PENDING,
                created_at=datetime.now(tz=UTC),
                processed_at=None,
                metadata={"error": "Takedown processing failed"},
            )

    async def process(
        self,
        request: TakedownRequest,
        process_req: TakedownProcessRequest,
    ) -> TakedownRequest:
        """Apply a processing decision to a takedown request.

        Args:
            request: The takedown request to process.
            process_req: The processing decision.

        Returns:
            The updated TakedownRequest.
        """
        from datetime import datetime

        request.status = process_req.action
        request.processed_at = datetime.now(tz=UTC)
        request.metadata["reviewer_id"] = process_req.reviewer_id
        if process_req.notes:
            request.metadata["review_notes"] = process_req.notes
        return request

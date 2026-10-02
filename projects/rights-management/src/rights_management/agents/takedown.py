"""Takedown processing agent using LangChain DeepAgents."""

from __future__ import annotations

from typing import Any

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate

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

    def _build_agent(self) -> AgentExecutor:
        """Build the LangChain ReAct agent for takedown processing.

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
            result: dict[str, Any] = await self._agent.ainvoke(
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
                created_at=datetime.utcnow(),
                processed_at=None,
                metadata={"agent_output": output} if output else {},
            )
        except Exception:
            return TakedownRequest(
                id=str(payload.get("id", uuid.uuid4())),
                content_id=str(payload.get("content_id", "")),
                requester_id=str(payload.get("requester_id", "")),
                reason=str(payload.get("reason", "")),
                legal_basis=payload.get("legal_basis"),
                status=TakedownStatus.PENDING,
                created_at=datetime.utcnow(),
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
        request.processed_at = datetime.utcnow()
        request.metadata["reviewer_id"] = process_req.reviewer_id
        if process_req.notes:
            request.metadata["review_notes"] = process_req.notes
        return request

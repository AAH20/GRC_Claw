"""Access Auditor Agent — audits access events and detects anomalies."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from langchain_core.prompts import ChatPromptTemplate

if TYPE_CHECKING:
    from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

from access_control.agents.base import AgentContext, BaseAgent

if TYPE_CHECKING:
    from access_control.config import Settings
from access_control.models.enums import AccessDecision, AuditSeverity
from access_control.models.schemas import AccessAudit, AccessRequest


class AccessAuditorInput(BaseModel):
    """Input for the access auditor agent."""

    event_type: str = Field(
        ..., description="Type of event: access_attempt, policy_violation, anomaly"
    )
    audit_entry: dict[str, Any] = Field(default_factory=dict)
    historical_events: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class AccessAuditorOutput(BaseModel):
    """Output from the access auditor agent."""

    severity: AuditSeverity
    flagged: bool = False
    anomaly_score: float = Field(default=0.0, ge=0.0, le=1.0)
    findings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class AccessAuditorAgent(BaseAgent[AccessAuditorInput, AccessAuditorOutput]):
    """Agent that audits access events and detects anomalies.

    Uses LangChain DeepAgents to analyze access patterns, identify
    suspicious behavior, and generate audit entries with appropriate
    severity levels.
    """

    def __init__(self, llm: BaseLanguageModel, settings: Settings) -> None:
        super().__init__(
            llm=llm,
            settings=settings,
            name="access_auditor",
            description="Audits access events and detects anomalies using AI analysis",
        )

    def _build_agent(self) -> Any:
        """Build the LangChain DeepAgents instance for access auditing."""
        system_prompt = """You are an access auditing engine for a security-focused access control system.
Analyze the given access event and historical context to detect anomalies and security issues.
Consider factors like: unusual time patterns, privilege escalation attempts, access from new locations,
brute force patterns, and policy violations.
Respond with a JSON object containing: severity, flagged, anomaly_score, findings, recommended_actions."""  # noqa: E501

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        chain = prompt | self.llm
        return chain

    async def run(
        self, payload: AccessAuditorInput, context: AgentContext | None = None
    ) -> AccessAuditorOutput:
        """Audit an access event.

        Args:
            payload: The event data and historical context.
            context: Optional execution context.

        Returns:
            The audit analysis result.
        """
        agent = self._build_agent()

        input_data = {
            "input": json.dumps({
                "event_type": payload.event_type,
                "audit_entry": payload.audit_entry,
                "historical_events": payload.historical_events,
                "context": payload.context,
            })
        }

        response = await agent.ainvoke(input_data)

        content = response.content if hasattr(response, "content") else str(response)

        try:
            parsed = json.loads(content)
            return AccessAuditorOutput(**parsed)
        except (json.JSONDecodeError, TypeError):
            return AccessAuditorOutput(
                severity=AuditSeverity.INFO,
                findings=["Failed to parse agent response"],
            )

    async def audit_access(
        self,
        request: AccessRequest,
        decision: AccessDecision,
        historical_events: list[dict[str, Any]] | None = None,
    ) -> AccessAudit:
        """Audit an access attempt and create an audit entry.

        Args:
            request: The access request that was evaluated.
            decision: The access decision that was made.
            historical_events: Optional historical events for anomaly detection.

        Returns:
            An audit entry for the access attempt.
        """
        payload = AccessAuditorInput(
            event_type="access_attempt",
            audit_entry={
                "principal_id": request.principal_id,
                "resource": request.resource,
                "action": request.action,
                "decision": decision.value,
                "context": request.context,
            },
            historical_events=historical_events or [],
        )
        output = await self.run(payload)

        return AccessAudit(
            principal_id=request.principal_id,
            action=request.action,
            resource=request.resource,
            decision=decision,
            severity=output.severity,
            details={
                "anomaly_score": output.anomaly_score,
                "flagged": output.flagged,
                "findings": output.findings,
                "recommended_actions": output.recommended_actions,
            },
            ip_address=request.context.get("ip_address"),
            user_agent=request.context.get("user_agent"),
        )

    async def detect_anomalies(
        self, events: list[dict[str, Any]]
    ) -> list[AccessAuditorOutput]:
        """Detect anomalies across a batch of access events.

        Args:
            events: A list of access event dicts to analyze.

        Returns:
            A list of audit outputs for anomalous events.
        """
        results: list[AccessAuditorOutput] = []

        for event in events:
            payload = AccessAuditorInput(
                event_type="anomaly_detection",
                audit_entry=event,
                historical_events=[e for e in events if e != event],
            )
            output = await self.run(payload)
            if output.flagged:
                results.append(output)

        return results

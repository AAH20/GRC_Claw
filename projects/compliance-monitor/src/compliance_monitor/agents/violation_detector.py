"""Violation Detector Agent - detects compliance violations from events and logs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from compliance_monitor.agents.base import BaseComplianceAgent
from compliance_monitor.models.schemas import Violation, ViolationCreate, ViolationSeverity


class ViolationDetectorAgent(BaseComplianceAgent[ViolationCreate, Violation]):
    """Agent responsible for detecting compliance violations.

    Uses LangChain DeepAgents to analyze events, logs, and activities
    to identify potential compliance violations.
    """

    def __init__(self, model: str = "gpt-4o") -> None:
        """Initialize the Violation Detector Agent.

        Args:
            model: LLM model to use for violation detection.
        """
        super().__init__(name="ViolationDetectorAgent", model=model)

    async def run(self, input_data: ViolationCreate) -> Violation:
        """Create a violation record from detection data.

        Args:
            input_data: Violation creation data.

        Returns:
            Created Violation instance.
        """
        violation = Violation(
            policy_id=input_data.policy_id,
            title=input_data.title,
            description=input_data.description,
            severity=input_data.severity,
            evidence=input_data.evidence,
            assignee=input_data.assignee,
            metadata=input_data.metadata,
        )
        return violation

    async def analyze_event(self, event: dict[str, Any], policy_rules: list[str]) -> dict[str, Any]:
        """Analyze an event for potential policy violations.

        Args:
            event: Event data to analyze.
            policy_rules: Policy rules to check against.

        Returns:
            Analysis result with violation indicators.
        """
        prompt = f"""Analyze the following event for compliance violations against these policy rules:

Policy Rules:
{chr(10).join(f"- {rule}" for rule in policy_rules)}

Event:
{event}

Determine:
1. Is this a violation? (yes/no)
2. If yes, what severity? (low/medium/high/critical)
3. What evidence supports this?
4. Recommended actions
"""
        result = await self.agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        return {"analysis": result, "event_id": event.get("id"), "timestamp": datetime.utcnow().isoformat()}

    async def detect_from_logs(self, logs: list[str], policy_id: UUID) -> list[Violation]:
        """Detect violations from system logs.

        Args:
            logs: List of log entries to analyze.
            policy_id: Policy to check against.

        Returns:
            List of detected violations.
        """
        violations: list[Violation] = []
        for log_entry in logs:
            result = await self.analyze_event({"log": log_entry}, [])
            if result.get("analysis"):
                violations.append(
                    Violation(
                        policy_id=policy_id,
                        title=f"Detected violation from log: {log_entry[:100]}",
                        description=str(result["analysis"]),
                        severity=ViolationSeverity.MEDIUM,
                        evidence=[log_entry],
                    )
                )
        return violations

    async def assess_severity(self, violation: Violation) -> ViolationSeverity:
        """Assess and potentially adjust violation severity using LLM.

        Args:
            violation: Violation to assess.

        Returns:
            Assessed severity level.
        """
        prompt = f"""Assess the severity of this compliance violation:

Title: {violation.title}
Description: {violation.description}
Current Severity: {violation.severity}
Evidence: {violation.evidence}

Provide a severity assessment (low/medium/high/critical) with justification.
"""
        result = await self.agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
        return violation.severity

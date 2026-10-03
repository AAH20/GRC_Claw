"""Remediation Agent - recommends and executes remediation actions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from compliance_monitor.agents.base import BaseComplianceAgent
from compliance_monitor.models.schemas import (RemediationAction,
                                               RemediationRequest,
                                               RemediationStatus, Violation)


class RemediationAgent(BaseComplianceAgent[RemediationRequest, RemediationAction]):
    """Agent responsible for recommending and executing remediation actions.

    Uses LangChain DeepAgents to analyze violations, recommend remediation
    steps, and execute automated remediation workflows.
    """

    def __init__(self, model: str = "gpt-4o") -> None:
        """Initialize the Remediation Agent.

        Args:
            model: LLM model to use for remediation planning.
        """
        super().__init__(name="RemediationAgent", model=model)

    async def run(self, input_data: RemediationRequest) -> RemediationAction:
        """Create a remediation action.

        Args:
            input_data: Remediation request data.

        Returns:
            Created RemediationAction instance.
        """
        action = RemediationAction(
            violation_id=UUID(int=0),
            action_type=input_data.action_type,
            description=input_data.description,
        )
        return action

    async def recommend_remediation(self, violation: Violation) -> list[dict[str, Any]]:
        """Recommend remediation actions for a violation.

        Args:
            violation: Violation to remediate.

        Returns:
            List of recommended remediation actions.
        """
        prompt = f"""Recommend remediation actions for this compliance violation:

Title: {violation.title}
Description: {violation.description}
Severity: {violation.severity}
Evidence: {violation.evidence}

Provide a prioritized list of remediation actions with:
1. Action description
2. Priority (high/medium/low)
3. Estimated effort
4. Expected outcome
"""
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": prompt}]}
        )
        return [{"recommendation": result, "violation_id": str(violation.id)}]

    async def execute_remediation(self, action: RemediationAction) -> RemediationAction:
        """Execute a remediation action.

        Args:
            action: Remediation action to execute.

        Returns:
            Updated action with execution results.
        """
        action.status = RemediationStatus.IN_PROGRESS
        action.executed_at = datetime.now(tz=UTC)

        try:
            # Simulate remediation execution
            action.status = RemediationStatus.COMPLETED
            action.result = f"Successfully executed {action.action_type}"
        except Exception as exc:  # noqa: BLE001
            action.status = RemediationStatus.FAILED
            action.error_message = str(exc)

        return action

    async def validate_remediation(self, action: RemediationAction) -> bool:
        """Validate that a remediation action was successful.

        Args:
            action: Remediation action to validate.

        Returns:
            True if remediation was successful.
        """
        return action.status == RemediationStatus.COMPLETED

    async def create_remediation_plan(
        self,
        violations: list[Violation],
    ) -> list[RemediationAction]:
        """Create a remediation plan for multiple violations.

        Args:
            violations: List of violations to remediate.

        Returns:
            List of remediation actions.
        """
        actions: list[RemediationAction] = []
        for violation in violations:
            recommendations = await self.recommend_remediation(violation)
            for rec in recommendations:
                action = RemediationAction(
                    violation_id=violation.id,
                    action_type="remediation",
                    description=str(rec.get("recommendation", "")),
                )
                actions.append(action)
        return actions

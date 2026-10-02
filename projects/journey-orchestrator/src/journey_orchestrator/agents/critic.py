"""Critic agent - reviews journey designs for compliance and effectiveness."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CriticRequest(BaseModel):
    """Request for journey review."""

    journey_blueprint: dict[str, Any]
    brand_guidelines: dict[str, Any] = Field(default_factory=dict)
    compliance_requirements: list[str] = Field(default_factory=list)


class CriticFinding(BaseModel):
    """A single finding from the Critic review."""

    severity: str  # "info", "warning", "error"
    category: str
    message: str
    recommendation: str = ""


class CriticReview(BaseModel):
    """Output of the Critic agent."""

    approved: bool
    findings: list[CriticFinding]
    overall_score: float = Field(ge=0.0, le=1.0)
    summary: str = ""


class CriticAgent:
    """Agent that reviews journey designs for quality, compliance, and brand safety.

    Acts as a quality gate before journeys are activated, checking for
    potential issues and ensuring adherence to brand guidelines.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the Critic Agent.

        Args:
            llm_client: Optional LLM client for AI-powered review.
        """
        self.llm_client = llm_client
        self.logger = logger.bind(agent="critic")

    async def review(self, request: CriticRequest) -> CriticReview:
        """Review a journey blueprint.

        Args:
            request: The critic request with journey blueprint.

        Returns:
            A review with findings and approval decision.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.journey_blueprint:
            raise ValueError("journey_blueprint must not be empty")

        self.logger.info("Reviewing journey blueprint")

        findings: list[CriticFinding] = []

        # Check for common issues
        steps = request.journey_blueprint.get("steps", [])
        if not steps:
            findings.append(
                CriticFinding(
                    severity="error",
                    category="structure",
                    message="Journey has no steps",
                    recommendation="Add at least one step to the journey",
                )
            )

        channels = set()
        for step in steps:
            channel = step.get("channel", "")
            channels.add(channel)
            if not channel:
                findings.append(
                    CriticFinding(
                        severity="error",
                        category="channel",
                        message=f"Step {step.get('step_number', '?')} has no channel",
                        recommendation="Specify a channel for each step",
                    )
                )

        if len(channels) > 5:
            findings.append(
                CriticFinding(
                    severity="warning",
                    category="complexity",
                    message=f"Journey uses {len(channels)} channels which may be complex",
                    recommendation="Consider simplifying to fewer channels",
                )
            )

        # Check for compliance
        if "gdpr" in request.compliance_requirements:
            has_opt_out = any(
                "unsubscribed" in step.get("exit_conditions", []) for step in steps
            )
            if not has_opt_out:
                findings.append(
                    CriticFinding(
                        severity="error",
                        category="compliance",
                        message="GDPR requires opt-out mechanism",
                        recommendation="Add 'unsubscribed' exit condition to at least one step",
                    )
                )

        approved = not any(f.severity == "error" for f in findings)
        score = max(0.0, 1.0 - len([f for f in findings if f.severity == "error"]) * 0.3
                  - len([f for f in findings if f.severity == "warning"]) * 0.1)

        review = CriticReview(
            approved=approved,
            findings=findings,
            overall_score=score,
            summary=(
                f"Review complete: {len(findings)} findings, "
                f"{'approved' if approved else 'rejected'}"
            ),
        )

        self.logger.info(
            "Review complete",
            approved=approved,
            findings=len(findings),
            score=score,
        )
        return review

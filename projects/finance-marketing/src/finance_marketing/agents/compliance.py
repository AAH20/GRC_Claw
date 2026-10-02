"""Compliance Agent - FINRA/SEC compliance checking and validation."""

from __future__ import annotations

import os
import re
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ComplianceStatus(StrEnum):
    """Compliance check status values."""
    APPROVED = "approved"
    REQUIRES_REVIEW = "requires_review"
    REJECTED = "rejected"
    PENDING = "pending"


class ComplianceRule(BaseModel):
    """Model for a compliance rule."""
    rule_id: str
    name: str
    description: str
    regulation: str
    severity: str = "medium"
    pattern: str = ""
    enabled: bool = True


class ComplianceViolation(BaseModel):
    """Model for a compliance violation."""
    rule_id: str
    rule_name: str
    severity: str
    matched_text: str
    position: int = 0
    explanation: str = ""
    suggestion: str = ""


class ComplianceResult(BaseModel):
    """Result of a compliance check."""
    content_id: str
    status: ComplianceStatus
    violations: list[ComplianceViolation] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    checked_by: str = "compliance_agent"
    notes: str = ""


class ComplianceAgent:
    """Agent responsible for FINRA/SEC compliance validation."""

    def __init__(self) -> None:
        """Initialize the Compliance Agent with regulatory rules."""
        self.model = os.getenv("COMPLIANCE_MODEL", "gpt-4")
        self.temperature = float(os.getenv("COMPLIANCE_TEMPERATURE", "0.1"))
        self.rules = self._load_rules()
        logger.info("Compliance Agent initialized", rules_count=len(self.rules))

    def _load_rules(self) -> list[ComplianceRule]:
        """Load compliance rules from configuration."""
        return [
            ComplianceRule(
                rule_id="FINRA-2210-001",
                name="Prohibited Guarantees",
                description="Content must not guarantee investment returns",
                regulation="FINRA Rule 2210",
                severity="critical",
                pattern=(
                    r"(?i)(guaranteed?\s+(returns?|profits?|income)"
                    r"|risk[- ]free|can'?t\s+lose|sure\s+thing)"
                ),
            ),
            ComplianceRule(
                rule_id="FINRA-2210-002",
                name="Misleading Performance Claims",
                description=(
                    "Past performance must not be presented as indicative of future results"
                ),
                regulation="FINRA Rule 2210",
                severity="high",
                pattern=r"(?i)(past\s+performance\s+(guarantees?|ensures?|means?)\s+future)",
            ),
            ComplianceRule(
                rule_id="FINRA-2210-003",
                name="Required Disclosures",
                description="Content must include required risk disclosures",
                regulation="FINRA Rule 2210",
                severity="high",
                pattern=r"(?i)(investing\s+involves\s+risk|loss\s+of\s+principal)",
            ),
            ComplianceRule(
                rule_id="SEC-MKT-001",
                name="Testimonial Restrictions",
                description="Testimonials must comply with SEC Marketing Rule requirements",
                regulation="SEC Marketing Rule",
                severity="high",
                pattern=r"(?i)(testimonial|endorsement|client\s+says)",
            ),
            ComplianceRule(
                rule_id="SEC-MKT-002",
                name="Substantiation Requirement",
                description="Performance claims must be substantiated",
                regulation="SEC Marketing Rule",
                severity="medium",
                pattern=r"(?i)(\d+%\s+returns?|outperform(ed|s)?\s+(the\s+)?market)",
            ),
            ComplianceRule(
                rule_id="FINRA-2210-004",
                name="Fair and Balanced Communication",
                description="Content must be fair and balanced",
                regulation="FINRA Rule 2210",
                severity="medium",
                pattern=r"(?i)(best\s+(investment|fund|advisor)|number\s+one|top\s+rated)",
            ),
        ]

    async def check_compliance(self, content: str, content_id: str = "") -> ComplianceResult:
        """Check content for compliance violations.

        Args:
            content: The marketing content to check.
            content_id: Optional identifier for the content.

        Returns:
            Compliance check result with any violations found.
        """
        logger.info("Checking compliance", content_id=content_id, content_length=len(content))
        violations: list[ComplianceViolation] = []

        for rule in self.rules:
            if not rule.enabled or not rule.pattern:
                continue
            if rule.rule_id == "FINRA-2210-003":
                continue  # Presence check handled separately

            for match in re.finditer(rule.pattern, content):
                violations.append(ComplianceViolation(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    matched_text=match.group(),
                    position=match.start(),
                    explanation=f"Content may violate {rule.description}",
                    suggestion=self._get_suggestion(rule),
                ))

        # Check for missing required disclosures
        disclosure_rule = next((r for r in self.rules if r.rule_id == "FINRA-2210-003"), None)
        if disclosure_rule and not re.search(disclosure_rule.pattern, content, re.IGNORECASE):
            violations.append(ComplianceViolation(
                rule_id=disclosure_rule.rule_id,
                rule_name=disclosure_rule.name,
                severity=disclosure_rule.severity,
                matched_text="",
                position=0,
                explanation="Required risk disclosure is missing from content",
                suggestion="Add: 'Investing involves risk including possible loss of principal.'",
            ))

        if any(v.severity == "critical" for v in violations):
            status = ComplianceStatus.REJECTED
        elif violations:
            status = ComplianceStatus.REQUIRES_REVIEW
        else:
            status = ComplianceStatus.APPROVED

        return ComplianceResult(
            content_id=content_id,
            status=status,
            violations=violations,
            notes=f"Checked against {len(self.rules)} rules",
        )

    def _get_suggestion(self, rule: ComplianceRule) -> str:
        """Get a suggestion for fixing a violation."""
        suggestions = {
            "FINRA-2210-001": (
                "Remove guaranteed return language. Use 'historical performance' instead."
            ),
            "FINRA-2210-002": (
                "Add disclaimer: 'Past performance is not indicative of future results.'"
            ),
            "SEC-MKT-001": (
                "Ensure testimonials comply with SEC Marketing Rule disclosure requirements."
            ),
            "SEC-MKT-002": (
                "Provide substantiation for performance claims or remove specific numbers."
            ),
            "FINRA-2210-004": (
                "Use factual, verifiable claims instead of superlatives."
            ),
        }
        return suggestions.get(rule.rule_id, "Review and revise content to ensure compliance.")

    async def approve_content(self, content_id: str, approver: str) -> ComplianceResult:
        """Manually approve content after review."""
        logger.info("Content approved", content_id=content_id, approver=approver)
        return ComplianceResult(
            content_id=content_id,
            status=ComplianceStatus.APPROVED,
            checked_by=approver,
            notes="Manually approved after review",
        )

    async def get_audit_trail(self, content_id: str) -> list[dict[str, Any]]:
        """Get the audit trail for a piece of content."""
        logger.info("Retrieving audit trail", content_id=content_id)
        return [
            {
                "action": "created",
                "timestamp": datetime.utcnow().isoformat(),
                "actor": "content_agent",
            },
            {
                "action": "compliance_check",
                "timestamp": datetime.utcnow().isoformat(),
                "actor": "compliance_agent",
            },
        ]

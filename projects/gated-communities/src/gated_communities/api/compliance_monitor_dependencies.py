"""API dependencies."""

from __future__ import annotations

from compliance_monitor.agents import (
    AuditReporterAgent,
    ComplianceScorerAgent,
    PolicyTrackerAgent,
    RemediationAgent,
    ViolationDetectorAgent,
)


def get_policy_tracker() -> PolicyTrackerAgent:
    """Get PolicyTrackerAgent instance.

    Returns:
        PolicyTrackerAgent instance.
    """
    return PolicyTrackerAgent()


def get_violation_detector() -> ViolationDetectorAgent:
    """Get ViolationDetectorAgent instance.

    Returns:
        ViolationDetectorAgent instance.
    """
    return ViolationDetectorAgent()


def get_audit_reporter() -> AuditReporterAgent:
    """Get AuditReporterAgent instance.

    Returns:
        AuditReporterAgent instance.
    """
    return AuditReporterAgent()


def get_compliance_scorer() -> ComplianceScorerAgent:
    """Get ComplianceScorerAgent instance.

    Returns:
        ComplianceScorerAgent instance.
    """
    return ComplianceScorerAgent()


def get_remediation_agent() -> RemediationAgent:
    """Get RemediationAgent instance.

    Returns:
        RemediationAgent instance.
    """
    return RemediationAgent()

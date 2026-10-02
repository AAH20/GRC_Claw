"""
GRC_Claw Audit & Compliance Tracking System

Comprehensive audit trail, compliance tracking, reporting, evidence
management, and analytics for GRC (Governance, Risk, Compliance) operations.

Modules:
    models: Data models for audit events, controls, findings, evidence, etc.
    audit_trail: Immutable, hash-chained audit event logging engine
    compliance: Framework control mapping, assessment, and scoring
    reporting: Structured audit report generation with opinions
    evidence: Evidence collection, chain of custody, and lifecycle management
    analytics: Aggregation, trend analysis, and risk identification
"""

from .analytics import AuditAnalyticsEngine
from .audit_trail import AuditTrailEngine
from .compliance import ComplianceTracker
from .evidence import EvidenceManager
from .models import (
    CAPA,
    # Core models
    Actor,
    AuditAnalytics,
    AuditEngagement,
    AuditEvent,
    AuditEventSeverity,
    # Enums
    AuditEventType,
    AuditReport,
    AuditStatus,
    AuditType,
    CAPAStatus,
    CAPAType,
    ChainOfCustodyStatus,
    ComplianceAssessment,
    ComplianceControl,
    ComplianceFramework,
    ControlStatus,
    ControlType,
    Evidence,
    EvidenceStatus,
    EvidenceType,
    Finding,
    FindingSeverity,
    FindingStatus,
    OverallOpinion,
    Resource,
    Workpaper,
)
from .reporting import AuditReporter

__all__ = [
    # Enums
    "AuditEventType",
    "AuditEventSeverity",
    "ComplianceFramework",
    "ControlStatus",
    "ControlType",
    "FindingSeverity",
    "FindingStatus",
    "EvidenceType",
    "EvidenceStatus",
    "AuditStatus",
    "AuditType",
    "OverallOpinion",
    "CAPAType",
    "CAPAStatus",
    "ChainOfCustodyStatus",
    # Core models
    "Actor",
    "Resource",
    "AuditEvent",
    "ComplianceControl",
    "Finding",
    "Evidence",
    "AuditEngagement",
    "Workpaper",
    "CAPA",
    "AuditReport",
    "ComplianceAssessment",
    "AuditAnalytics",
    # Engines
    "AuditTrailEngine",
    "ComplianceTracker",
    "AuditReporter",
    "EvidenceManager",
    "AuditAnalyticsEngine",
]

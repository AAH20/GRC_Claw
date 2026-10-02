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

from .models import (
    # Enums
    AuditEventType,
    AuditEventSeverity,
    ComplianceFramework,
    ControlStatus,
    ControlType,
    FindingSeverity,
    FindingStatus,
    EvidenceType,
    EvidenceStatus,
    AuditStatus,
    AuditType,
    OverallOpinion,
    CAPAType,
    CAPAStatus,
    ChainOfCustodyStatus,
    # Core models
    Actor,
    Resource,
    AuditEvent,
    ComplianceControl,
    Finding,
    Evidence,
    AuditEngagement,
    Workpaper,
    CAPA,
    AuditReport,
    ComplianceAssessment,
    AuditAnalytics,
)
from .audit_trail import AuditTrailEngine
from .compliance import ComplianceTracker
from .reporting import AuditReporter
from .evidence import EvidenceManager
from .analytics import AuditAnalyticsEngine

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

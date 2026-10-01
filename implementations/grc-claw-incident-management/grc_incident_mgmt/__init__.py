"""
GRC_Claw AI Incident Management Implementation
==============================================

Complete implementation of the GRC_Claw AI Incident Management Specification (GRC-AIM-001 v2.0).

Modules:
    taxonomy      — Incident taxonomy constants (8 categories, 44 subcategories)
    models        — Data models for incidents, signals, and reports
    detection     — Automated incident detection pipeline (§12)
    classification — Severity auto-classification engine (§14)
    orchestration — Response orchestration with runbooks (§13)
    reporting     — Incident reporting and formatting (§6)
    learning      — Post-incident learning loop (§15)
    trends        — Trend analysis and prediction (§16)
    regulatory    — Regulatory reporting automation (§17)
"""

from .taxonomy import IncidentCategory, Severity, SUBCATEGORIES, MINIMUM_SEVERITY
from .models import (
    DetectionSignal,
    Incident,
    IncidentStatus,
    IncidentReport,
    ImpactAssessment,
    RootCause,
    ResponseAction,
    Evidence,
    Recommendation,
    RegulatoryAssessment,
    AffectedAsset,
    AssetType,
    Environment,
)

__version__ = "2.0.0"
__all__ = [
    "IncidentCategory",
    "Severity",
    "SUBCATEGORIES",
    "MINIMUM_SEVERITY",
    "DetectionSignal",
    "Incident",
    "IncidentStatus",
    "IncidentReport",
    "ImpactAssessment",
    "RootCause",
    "ResponseAction",
    "Evidence",
    "Recommendation",
    "RegulatoryAssessment",
    "AffectedAsset",
    "AssetType",
    "Environment",
]

"""
GRC_Claw Data Models for Incident Management (§6 of GRC-AIM-001)

Defines the core data structures used throughout the incident lifecycle.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from .taxonomy import IncidentCategory, Severity


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IncidentStatus(str, Enum):
    """Incident lifecycle states (§13.6)."""
    DETECTED = "DETECTED"
    TRIAGED = "TRIAGED"
    CONTAINED = "CONTAINED"
    ERADICATED = "ERADICATED"
    RECOVERED = "RECOVERED"
    CLOSED = "CLOSED"


class AssetType(str, Enum):
    MODEL = "model"
    AGENT = "agent"
    DATASET = "dataset"
    PIPELINE = "pipeline"
    API = "api"
    INFRASTRUCTURE = "infrastructure"


class Environment(str, Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    EDGE = "edge"


class RootCauseCategory(str, Enum):
    MODEL_DEFECT = "model_defect"
    DATA_ISSUE = "data_issue"
    POLICY_GAP = "policy_gap"
    ATTACK = "attack"
    CONFIGURATION_ERROR = "configuration_error"
    SUPPLY_CHAIN = "supply_chain"
    HUMAN_ERROR = "human_error"
    UNKNOWN = "unknown"


class RecommendationPriority(str, Enum):
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class RecommendationStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEFERRED = "deferred"


class EvidenceType(str, Enum):
    LOG = "log"
    SCREENSHOT = "screenshot"
    MODEL_OUTPUT = "model_output"
    AUDIT_TRAIL = "audit_trail"
    CONFIG_SNAPSHOT = "config_snapshot"
    COMMUNICATION = "communication"


@dataclass
class AffectedAsset:
    asset_id: str
    asset_type: AssetType
    asset_name: str
    environment: Environment
    version: str = ""


@dataclass
class ImpactAssessment:
    individuals_affected: int = 0
    records_affected: int = 0
    data_types: list[str] = field(default_factory=list)
    financial_impact_usd: float = 0.0
    operational_impact: str = ""
    reputational_impact: str = ""


@dataclass
class RootCause:
    category: RootCauseCategory = RootCauseCategory.UNKNOWN
    description: str = ""
    contributing_factors: list[str] = field(default_factory=list)
    whys_analysis: list[str] = field(default_factory=list)


@dataclass
class ResponseAction:
    timestamp: str = field(default_factory=_now)
    action: str = ""
    actor: str = ""
    result: str = ""


@dataclass
class Evidence:
    evidence_id: str = field(default_factory=_uuid)
    type: EvidenceType = EvidenceType.LOG
    description: str = ""
    hash: str = ""
    collected_at: str = field(default_factory=_now)
    collected_by: str = ""


@dataclass
class Recommendation:
    recommendation_id: str = field(default_factory=_uuid)
    description: str = ""
    priority: RecommendationPriority = RecommendationPriority.SHORT_TERM
    owner: str = ""
    due_date: str = ""
    status: RecommendationStatus = RecommendationStatus.OPEN


@dataclass
class RegulatoryAssessment:
    eu_ai_act_applicable: bool = False
    article_73_triggered: bool = False
    notification_deadline: str = ""
    notification_submitted: bool = False
    notification_date: str = ""
    other_regulations: list[str] = field(default_factory=list)


@dataclass
class DetectionSignal:
    """A single detection signal from any source (§12.2)."""
    signal_id: str = field(default_factory=_uuid)
    source: str = ""  # e.g., "ai_risk_radar", "policy_engine", "user_report"
    category: Optional[IncidentCategory] = None
    subcategory_code: str = ""
    confidence: float = 0.0  # 0.0–1.0
    raw_data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now)
    asset_id: str = ""
    environment: Environment = Environment.PRODUCTION
    correlated: bool = False
    correlation_group_id: str = ""


@dataclass
class Incident:
    """Core incident record (§6.1)."""
    incident_id: str = field(default_factory=_uuid)
    report_id: str = field(default_factory=_uuid)
    status: IncidentStatus = IncidentStatus.DETECTED
    category: Optional[IncidentCategory] = None
    subcategory_code: str = ""
    severity: Severity = Severity.S5_INFORMATIONAL
    confidence: float = 0.0
    detected_at: str = field(default_factory=_now)
    detected_by: str = ""
    triaged_at: str = ""
    contained_at: str = ""
    eradicated_at: str = ""
    recovered_at: str = ""
    closed_at: str = ""
    affected_assets: list[AffectedAsset] = field(default_factory=list)
    impact_assessment: ImpactAssessment = field(default_factory=ImpactAssessment)
    root_cause: RootCause = field(default_factory=RootCause)
    response_actions: list[ResponseAction] = field(default_factory=list)
    containment_actions: list[str] = field(default_factory=list)
    eradication_actions: list[str] = field(default_factory=list)
    recovery_actions: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    regulatory_assessment: RegulatoryAssessment = field(default_factory=RegulatoryAssessment)
    lessons_learned: list[str] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    signals: list[DetectionSignal] = field(default_factory=list)
    summary: str = ""

    def transition_to(self, new_status: IncidentStatus) -> None:
        """Transition incident to a new lifecycle state."""
        now = _now()
        self.status = new_status
        if new_status == IncidentStatus.TRIAGED:
            self.triaged_at = now
        elif new_status == IncidentStatus.CONTAINED:
            self.contained_at = now
        elif new_status == IncidentStatus.ERADICATED:
            self.eradicated_at = now
        elif new_status == IncidentStatus.RECOVERED:
            self.recovered_at = now
        elif new_status == IncidentStatus.CLOSED:
            self.closed_at = now

    def add_signal(self, signal: DetectionSignal) -> None:
        self.signals.append(signal)

    def add_response_action(self, action: ResponseAction) -> None:
        self.response_actions.append(action)

    def add_evidence(self, evidence: Evidence) -> None:
        self.evidence.append(evidence)

    def add_recommendation(self, rec: Recommendation) -> None:
        self.recommendations.append(rec)

    def to_report(self) -> "IncidentReport":
        """Convert to a formal incident report (§6.1)."""
        return IncidentReport(
            report_id=self.report_id,
            incident_id=self.incident_id,
            version="1.0",
            status="final" if self.status == IncidentStatus.CLOSED else "draft",
            category=self.category.value if self.category else "",
            subcategory=self.subcategory_code,
            severity=self.severity.value,
            confidence=self.confidence,
            detected_at=self.detected_at,
            detected_by=self.detected_by,
            triaged_at=self.triaged_at,
            contained_at=self.contained_at,
            eradicated_at=self.eradicated_at,
            recovered_at=self.recovered_at,
            closed_at=self.closed_at,
            affected_assets=[a.__dict__ for a in self.affected_assets],
            impact_assessment=self.impact_assessment.__dict__,
            root_cause=self.root_cause.__dict__,
            response_actions=[a.__dict__ for a in self.response_actions],
            containment_actions=self.containment_actions,
            eradication_actions=self.eradication_actions,
            recovery_actions=self.recovery_actions,
            evidence=[e.__dict__ for e in self.evidence],
            regulatory_assessment=self.regulatory_assessment.__dict__,
            lessons_learned=self.lessons_learned,
            recommendations=[r.__dict__ for r in self.recommendations],
        )


@dataclass
class IncidentReport:
    """Standardized incident report format (§6.1)."""
    report_id: str = field(default_factory=_uuid)
    incident_id: str = ""
    version: str = "1.0"
    status: str = "draft"  # draft | final | amended
    category: str = ""
    subcategory: str = ""
    severity: str = ""
    confidence: float = 0.0
    detected_at: str = ""
    detected_by: str = ""
    triaged_at: str = ""
    contained_at: str = ""
    eradicated_at: str = ""
    recovered_at: str = ""
    closed_at: str = ""
    affected_assets: list[dict[str, Any]] = field(default_factory=list)
    impact_assessment: dict[str, Any] = field(default_factory=dict)
    root_cause: dict[str, Any] = field(default_factory=dict)
    response_actions: list[dict[str, Any]] = field(default_factory=list)
    containment_actions: list[str] = field(default_factory=list)
    eradication_actions: list[str] = field(default_factory=list)
    recovery_actions: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    regulatory_assessment: dict[str, Any] = field(default_factory=dict)
    lessons_learned: list[str] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_report": {
                "report_id": self.report_id,
                "incident_id": self.incident_id,
                "version": self.version,
                "status": self.status,
                "classification": {
                    "category": self.category,
                    "subcategory": self.subcategory,
                    "severity": self.severity,
                    "confidence": self.confidence,
                },
                "timeline": {
                    "detected_at": self.detected_at,
                    "detected_by": self.detected_by,
                    "triaged_at": self.triaged_at,
                    "contained_at": self.contained_at,
                    "eradicated_at": self.eradicated_at,
                    "recovered_at": self.recovered_at,
                    "closed_at": self.closed_at,
                },
                "affected_assets": self.affected_assets,
                "impact_assessment": self.impact_assessment,
                "root_cause": self.root_cause,
                "response_actions": self.response_actions,
                "containment_actions": self.containment_actions,
                "eradication_actions": self.eradication_actions,
                "recovery_actions": self.recovery_actions,
                "evidence": self.evidence,
                "regulatory_assessment": self.regulatory_assessment,
                "lessons_learned": self.lessons_learned,
                "recommendations": self.recommendations,
            }
        }

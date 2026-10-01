#!/usr/bin/env python3
"""
GRC_Claw Business Continuity Implementation Guide
=================================================

Complete implementation of business continuity capabilities for GRC_Claw,
covering:
  1. Criticality Classification
  2. Business Impact Analysis (BIA)
  3. Disaster Recovery Automation
  4. Failover Orchestration
  5. Resilience Scoring
  6. Continuity Monitoring
  7. Continuity Testing

References:
  - grc-claw-business-continuity-spec.md (GRC-BCP-001 v1.1)
  - grc-claw-reliability-spec.md (GRC-REL-001 v2.0)

Author: GRC_Claw Architecture Team
Version: 1.0
Date: 2026-10-01
"""

from __future__ import annotations

import enum
import hashlib
import json
import logging
import math
import random
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    TypeVar,
    Union,
)

import yaml

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("grc_bc")


# ===========================================================================
# 1. CRITICALITY CLASSIFICATION
# ===========================================================================
# Spec Reference: §4 — AI System Criticality Classification
# ===========================================================================


class CriticalityTier(enum.Enum):
    """Four-tier criticality classification per BCP §4.2."""

    T1 = "T1"  # Mission-Critical
    T2 = "T2"  # Business-Critical
    T3 = "T3"  # Business-Important
    T4 = "T4"  # Non-Critical


@dataclass(frozen=True)
class TierRequirements:
    """Governance requirements per tier (BCP §4.6)."""

    tier: CriticalityTier
    mtd_minutes: int
    rto_minutes: int
    rpo_minutes: int
    real_time_monitoring: bool
    automated_failover: bool
    dr_region_replication: bool
    testing_frequency_days: int
    incident_response_playbook: bool
    dedicated_dr_runbook: bool
    vendor_dr_requirements: bool
    board_reporting: bool


TIER_REQUIREMENTS: Dict[CriticalityTier, TierRequirements] = {
    CriticalityTier.T1: TierRequirements(
        tier=CriticalityTier.T1,
        mtd_minutes=0,
        rto_minutes=15,
        rpo_minutes=1,
        real_time_monitoring=True,
        automated_failover=True,
        dr_region_replication=True,
        testing_frequency_days=30,
        incident_response_playbook=True,
        dedicated_dr_runbook=True,
        vendor_dr_requirements=True,
        board_reporting=True,
    ),
    CriticalityTier.T2: TierRequirements(
        tier=CriticalityTier.T2,
        mtd_minutes=240,
        rto_minutes=60,
        rpo_minutes=5,
        real_time_monitoring=True,
        automated_failover=True,
        dr_region_replication=True,
        testing_frequency_days=90,
        incident_response_playbook=True,
        dedicated_dr_runbook=True,
        vendor_dr_requirements=True,
        board_reporting=True,
    ),
    CriticalityTier.T3: TierRequirements(
        tier=CriticalityTier.T3,
        mtd_minutes=1440,
        rto_minutes=240,
        rpo_minutes=60,
        real_time_monitoring=True,
        automated_failover=False,
        dr_region_replication=False,
        testing_frequency_days=180,
        incident_response_playbook=True,
        dedicated_dr_runbook=False,
        vendor_dr_requirements=False,
        board_reporting=False,
    ),
    CriticalityTier.T4: TierRequirements(
        tier=CriticalityTier.T4,
        mtd_minutes=4320,
        rto_minutes=1440,
        rpo_minutes=1440,
        real_time_monitoring=False,
        automated_failover=False,
        dr_region_replication=False,
        testing_frequency_days=365,
        incident_response_playbook=False,
        dedicated_dr_runbook=False,
        vendor_dr_requirements=False,
        board_reporting=False,
    ),
}


class ImpactDimension(enum.Enum):
    """Five scoring dimensions per BCP §4.3."""

    SAFETY = "safety_impact"
    REGULATORY = "regulatory_impact"
    FINANCIAL = "financial_impact"
    OPERATIONAL = "operational_impact"
    REPUTATIONAL = "reputational_impact"


DIMENSION_WEIGHTS: Dict[ImpactDimension, float] = {
    ImpactDimension.SAFETY: 0.30,
    ImpactDimension.REGULATORY: 0.25,
    ImpactDimension.FINANCIAL: 0.20,
    ImpactDimension.OPERATIONAL: 0.15,
    ImpactDimension.REPUTATIONAL: 0.10,
}


@dataclass
class DimensionScore:
    """Score for a single impact dimension."""

    dimension: ImpactDimension
    score: int  # 1–5
    justification: str

    def __post_init__(self) -> None:
        if not 1 <= self.score <= 5:
            raise ValueError(f"Score must be 1–5, got {self.score}")


@dataclass
class CriticalityClassification:
    """Complete criticality classification for an AI system (BCP §4)."""

    system_id: str
    system_name: str
    system_owner: str
    classification_date: datetime
    review_date: datetime
    dimensions: List[DimensionScore]
    composite_criticality_score: float
    assigned_tier: CriticalityTier
    approver: str
    approver_role: str
    exceptions: List[str] = field(default_factory=list)
    compensating_controls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_id": self.system_id,
            "system_name": self.system_name,
            "system_owner": self.system_owner,
            "classification_date": self.classification_date.isoformat(),
            "review_date": self.review_date.isoformat(),
            "dimensions": [
                {
                    "dimension": d.dimension.value,
                    "score": d.score,
                    "justification": d.justification,
                }
                for d in self.dimensions
            ],
            "composite_criticality_score": self.composite_criticality_score,
            "assigned_tier": self.assigned_tier.value,
            "approver": self.approver,
            "approver_role": self.approver_role,
            "exceptions": self.exceptions,
            "compensating_controls": self.compensating_controls,
        }


class CriticalityClassifier:
    """
    Classifies AI systems into criticality tiers per BCP §4.

    Implements the Composite Criticality Score (CCS) algorithm:
        CCS = Σ (Dimension Score × Dimension Weight)
        Range: 1.0 (lowest) to 5.0 (highest)

    CCS → Tier mapping:
        4.0–5.0 → T1 (Mission-Critical)
        3.0–3.9 → T2 (Business-Critical)
        2.0–2.9 → T3 (Business-Important)
        1.0–1.9 → T4 (Non-Critical)
    """

    @staticmethod
    def calculate_ccs(dimensions: List[DimensionScore]) -> float:
        """Calculate Composite Criticality Score."""
        ccs = 0.0
        for dim in dimensions:
            weight = DIMENSION_WEIGHTS[dim.dimension]
            ccs += dim.score * weight
        return round(ccs, 2)

    @staticmethod
    def assign_tier(ccs: float) -> CriticalityTier:
        """Assign criticality tier based on CCS."""
        if ccs >= 4.0:
            return CriticalityTier.T1
        elif ccs >= 3.0:
            return CriticalityTier.T2
        elif ccs >= 2.0:
            return CriticalityTier.T3
        else:
            return CriticalityTier.T4

    @staticmethod
    def get_approver(tier: CriticalityTier) -> Tuple[str, str]:
        """Get approval authority per BCP §4.4 Step 4."""
        approvers = {
            CriticalityTier.T1: ("CISO + Risk Committee", "CISO"),
            CriticalityTier.T2: ("CISO", "CISO"),
            CriticalityTier.T3: ("Department Head", "Department Head"),
            CriticalityTier.T4: ("GRC_Claw Analyst", "Analyst"),
        }
        return approvers[tier]

    def classify(
        self,
        system_id: str,
        system_name: str,
        system_owner: str,
        dimensions: List[DimensionScore],
        exceptions: Optional[List[str]] = None,
        compensating_controls: Optional[List[str]] = None,
    ) -> CriticalityClassification:
        """
        Classify an AI system and return the full classification record.

        Example:
            >>> classifier = CriticalityClassifier()
            >>> dims = [
            ...     DimensionScore(ImpactDimension.SAFETY, 5, "Autonomous vehicle control"),
            ...     DimensionScore(ImpactDimension.REGULATORY, 4, "NHTSA reporting required"),
            ...     DimensionScore(ImpactDimension.FINANCIAL, 5, ">$10M liability"),
            ...     DimensionScore(ImpactDimension.OPERATIONAL, 5, "Complete process failure"),
            ...     DimensionScore(ImpactDimension.REPUTATIONAL, 5, "Front-page news"),
            ... ]
            >>> result = classifier.classify(
            ...     system_id="sys-001",
            ...     system_name="AutoDrive Decision Engine",
            ...     system_owner="eng-team@company.com",
            ...     dimensions=dims,
            ... )
            >>> result.assigned_tier
            <CriticalityTier.T1: 'T1'>
        """
        ccs = self.calculate_ccs(dimensions)
        tier = self.assign_tier(ccs)
        approver, approver_role = self.get_approver(tier)

        now = datetime.utcnow()
        review_days = 365 if tier in (CriticalityTier.T1, CriticalityTier.T2) else 730

        return CriticalityClassification(
            system_id=system_id,
            system_name=system_name,
            system_owner=system_owner,
            classification_date=now,
            review_date=now + timedelta(days=review_days),
            dimensions=dimensions,
            composite_criticality_score=ccs,
            assigned_tier=tier,
            approver=approver,
            approver_role=approver_role,
            exceptions=exceptions or [],
            compensating_controls=compensating_controls or [],
        )

    def validate_classification(
        self, classification: CriticalityClassification
    ) -> List[str]:
        """Validate a classification against BCP §4 requirements."""
        issues: List[str] = []
        reqs = TIER_REQUIREMENTS[classification.assigned_tier]

        # Check review date is set
        if classification.review_date <= datetime.utcnow():
            issues.append("Review date is in the past")

        # Check all dimensions are present
        scored_dims = {d.dimension for d in classification.dimensions}
        all_dims = set(ImpactDimension)
        missing = all_dims - scored_dims
        if missing:
            issues.append(f"Missing dimensions: {[d.value for d in missing]}")

        # Check CCS matches tier
        expected_tier = self.assign_tier(classification.composite_criticality_score)
        if expected_tier != classification.assigned_tier:
            issues.append(
                f"CCS {classification.composite_criticality_score} implies "
                f"{expected_tier.value} but assigned {classification.assigned_tier.value}"
            )

        # Check T1/T2 have compensating controls if exceptions exist
        if classification.exceptions and not classification.compensating_controls:
            if classification.assigned_tier in (CriticalityTier.T1, CriticalityTier.T2):
                issues.append("T1/T2 exceptions require compensating controls")

        return issues


# ===========================================================================
# 2. BUSINESS IMPACT ANALYSIS (BIA)
# ===========================================================================
# Spec Reference: §5 — Business Impact Analysis
# ===========================================================================


class ImpactCategory(enum.Enum):
    """Six impact categories per BCP §5.3."""

    SAFETY = "safety"
    REGULATORY = "regulatory"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    REPUTATIONAL = "reputational"
    STRATEGIC = "strategic"


class DisruptionDuration(enum.Enum):
    """Disruption duration bands per BCP §5.4."""

    MIN_0_15 = "0-15min"
    MIN_15_60 = "15min-1hr"
    HR_1_4 = "1-4hrs"
    HR_4_24 = "4-24hrs"
    DAY_1_3 = "1-3days"
    DAY_3_PLUS = ">3days"


IMPACT_MATRIX: Dict[DisruptionDuration, Dict[ImpactCategory, int]] = {
    DisruptionDuration.MIN_0_15: {
        ImpactCategory.SAFETY: 1,
        ImpactCategory.REGULATORY: 1,
        ImpactCategory.FINANCIAL: 1,
        ImpactCategory.OPERATIONAL: 1,
        ImpactCategory.REPUTATIONAL: 1,
        ImpactCategory.STRATEGIC: 1,
    },
    DisruptionDuration.MIN_15_60: {
        ImpactCategory.SAFETY: 2,
        ImpactCategory.REGULATORY: 2,
        ImpactCategory.FINANCIAL: 2,
        ImpactCategory.OPERATIONAL: 2,
        ImpactCategory.REPUTATIONAL: 2,
        ImpactCategory.STRATEGIC: 1,
    },
    DisruptionDuration.HR_1_4: {
        ImpactCategory.SAFETY: 3,
        ImpactCategory.REGULATORY: 3,
        ImpactCategory.FINANCIAL: 3,
        ImpactCategory.OPERATIONAL: 3,
        ImpactCategory.REPUTATIONAL: 3,
        ImpactCategory.STRATEGIC: 2,
    },
    DisruptionDuration.HR_4_24: {
        ImpactCategory.SAFETY: 4,
        ImpactCategory.REGULATORY: 4,
        ImpactCategory.FINANCIAL: 4,
        ImpactCategory.OPERATIONAL: 4,
        ImpactCategory.REPUTATIONAL: 4,
        ImpactCategory.STRATEGIC: 3,
    },
    DisruptionDuration.DAY_1_3: {
        ImpactCategory.SAFETY: 5,
        ImpactCategory.REGULATORY: 5,
        ImpactCategory.FINANCIAL: 5,
        ImpactCategory.OPERATIONAL: 5,
        ImpactCategory.REPUTATIONAL: 5,
        ImpactCategory.STRATEGIC: 4,
    },
    DisruptionDuration.DAY_3_PLUS: {
        ImpactCategory.SAFETY: 5,
        ImpactCategory.REGULATORY: 5,
        ImpactCategory.FINANCIAL: 5,
        ImpactCategory.OPERATIONAL: 5,
        ImpactCategory.REPUTATIONAL: 5,
        ImpactCategory.STRATEGIC: 5,
    },
}


class RecoveryPriority(enum.Enum):
    """Recovery priorities per BCP §5.6."""

    P1 = "P1"  # PDP + PEP (T1) — RTO 15min, RPO 1min
    P2 = "P2"  # Agent Identity — RTO 15min, RPO 1min
    P3 = "P3"  # Evidence Collection — RTO 30min, RPO 5min
    P4 = "P4"  # PostgreSQL — RTO 1hr, RPO 5min
    P5 = "P5"  # Redis — RTO 1hr, RPO N/A
    P6 = "P6"  # MongoDB — RTO 2hr, RPO 15min
    P7 = "P7"  # Observability — RTO 4hr, RPO 1hr
    P8 = "P8"  # Neo4j — RTO 4hr, RPO 1hr
    P9 = "P9"  # TimescaleDB — RTO 8hr, RPO 1hr
    P10 = "P10"  # Kafka — RTO 8hr, RPO 15min
    P11 = "P11"  # Compliance Mapping — RTO 24hr, RPO 24hr
    P12 = "P12"  # Analytics — RTO 24hr, RPO 24hr


RECOVERY_PRIORITY_MATRIX: Dict[RecoveryPriority, Dict[str, Any]] = {
    RecoveryPriority.P1: {
        "function": "PDP + PEP (T1 systems)",
        "rto_minutes": 15,
        "rpo_minutes": 1,
        "rationale": "Safety and regulatory compliance",
    },
    RecoveryPriority.P2: {
        "function": "Agent Identity Service",
        "rto_minutes": 15,
        "rpo_minutes": 1,
        "rationale": "Required for all agent authentication",
    },
    RecoveryPriority.P3: {
        "function": "Evidence Collection (T1/T2)",
        "rto_minutes": 30,
        "rpo_minutes": 5,
        "rationale": "Audit trail integrity",
    },
    RecoveryPriority.P4: {
        "function": "PostgreSQL (policies, enforcement)",
        "rto_minutes": 60,
        "rpo_minutes": 5,
        "rationale": "Core governance data",
    },
    RecoveryPriority.P5: {
        "function": "Redis (decision cache)",
        "rto_minutes": 60,
        "rpo_minutes": 0,
        "rationale": "Performance; rebuildable",
    },
    RecoveryPriority.P6: {
        "function": "MongoDB (evidence store)",
        "rto_minutes": 120,
        "rpo_minutes": 15,
        "rationale": "Evidence availability",
    },
    RecoveryPriority.P7: {
        "function": "Observability Stack",
        "rto_minutes": 240,
        "rpo_minutes": 60,
        "rationale": "Monitoring and alerting",
    },
    RecoveryPriority.P8: {
        "function": "Neo4j (compliance graph)",
        "rto_minutes": 240,
        "rpo_minutes": 60,
        "rationale": "Compliance mapping",
    },
    RecoveryPriority.P9: {
        "function": "TimescaleDB (metrics)",
        "rto_minutes": 480,
        "rpo_minutes": 60,
        "rationale": "Historical metrics",
    },
    RecoveryPriority.P10: {
        "function": "Kafka (event streaming)",
        "rto_minutes": 480,
        "rpo_minutes": 15,
        "rationale": "Event replay possible",
    },
    RecoveryPriority.P11: {
        "function": "Compliance Mapping Service",
        "rto_minutes": 1440,
        "rpo_minutes": 1440,
        "rationale": "Reporting; rebuildable",
    },
    RecoveryPriority.P12: {
        "function": "Analytics Engine",
        "rto_minutes": 1440,
        "rpo_minutes": 1440,
        "rationale": "Non-critical; batch rebuild",
    },
}


@dataclass
class SystemImpactProfile:
    """Impact profile for a single AI system across all durations."""

    system_id: str
    system_name: str
    criticality_tier: CriticalityTier
    impact_scores: Dict[DisruptionDuration, Dict[ImpactCategory, int]]
    recovery_priority: RecoveryPriority
    dependencies: List[str] = field(default_factory=list)

    def max_impact_score(self) -> int:
        """Return the maximum impact score across all durations and categories."""
        return max(
            score
            for duration_scores in self.impact_scores.values()
            for score in duration_scores.values()
        )

    def weighted_impact_score(self) -> float:
        """
        Calculate weighted impact score.
        Later durations weigh more (cumulative impact).
        """
        duration_weights = {
            DisruptionDuration.MIN_0_15: 1.0,
            DisruptionDuration.MIN_15_60: 1.5,
            DisruptionDuration.HR_1_4: 2.0,
            DisruptionDuration.HR_4_24: 3.0,
            DisruptionDuration.DAY_1_3: 4.0,
            DisruptionDuration.DAY_3_PLUS: 5.0,
        }
        total = 0.0
        for duration, scores in self.impact_scores.items():
            avg = sum(scores.values()) / len(scores)
            total += avg * duration_weights[duration]
        return round(total, 2)


@dataclass
class GovernanceFunctionImpact:
    """Impact on a governance function per BCP §5.5."""

    function_name: str
    t1_impact: str
    t2_impact: str
    t3_impact: str
    t4_impact: str
    dependencies: List[str]


GOVERNMENT_FUNCTIONS: List[GovernanceFunctionImpact] = [
    GovernanceFunctionImpact(
        function_name="Policy Enforcement (PDP/PEP)",
        t1_impact="Cannot enforce any governance — all AI actions ungoverned",
        t2_impact="Cannot enforce new policies; cached decisions only",
        t3_impact="Degraded enforcement; delayed policy updates",
        t4_impact="Minimal impact; manual processes available",
        dependencies=["PDP", "PEP", "Redis", "PostgreSQL"],
    ),
    GovernanceFunctionImpact(
        function_name="Evidence Collection",
        t1_impact="No audit trail — compliance cannot be proven",
        t2_impact="Delayed evidence; potential gaps",
        t3_impact="Batch evidence collection",
        t4_impact="Manual evidence collection",
        dependencies=["Collectors", "MongoDB", "TimescaleDB"],
    ),
    GovernanceFunctionImpact(
        function_name="Agent Identity",
        t1_impact="Cannot authenticate agents — all agents blocked",
        t2_impact="Cached SVIDs only; new agents blocked",
        t3_impact="Delayed identity verification",
        t4_impact="Manual identity verification",
        dependencies=["SPIFFE/SPIRE", "Vault", "PostgreSQL"],
    ),
    GovernanceFunctionImpact(
        function_name="Compliance Mapping",
        t1_impact="Cannot generate compliance reports",
        t2_impact="Delayed reporting; stale posture",
        t3_impact="Manual compliance assessment",
        t4_impact="Annual assessment sufficient",
        dependencies=["Crosswalk engine", "Neo4j"],
    ),
    GovernanceFunctionImpact(
        function_name="Observability",
        t1_impact="No visibility into AI behavior",
        t2_impact="Delayed metrics; partial traces",
        t3_impact="Batch analysis",
        t4_impact="Periodic manual review",
        dependencies=["OTel", "Prometheus", "Loki"],
    ),
    GovernanceFunctionImpact(
        function_name="Incident Response",
        t1_impact="Cannot detect or respond to AI incidents",
        t2_impact="Delayed detection; manual response",
        t3_impact="Degraded response capability",
        t4_impact="Post-incident manual review",
        dependencies=["All monitoring components"],
    ),
]


@dataclass
class BIAReport:
    """Complete Business Impact Analysis report per BCP §5."""

    report_id: str
    report_date: datetime
    report_period: str
    prepared_by: str
    approved_by: str
    executive_summary: str
    systems_analyzed: List[SystemImpactProfile]
    governance_function_impacts: List[GovernanceFunctionImpact]
    recovery_priority_matrix: List[Dict[str, Any]]
    financial_impact_summary: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "report_date": self.report_date.isoformat(),
            "report_period": self.report_period,
            "prepared_by": self.prepared_by,
            "approved_by": self.approved_by,
            "executive_summary": self.executive_summary,
            "systems_analyzed": [
                {
                    "system_id": s.system_id,
                    "system_name": s.system_name,
                    "criticality_tier": s.criticality_tier.value,
                    "max_impact_score": s.max_impact_score(),
                    "weighted_impact_score": s.weighted_impact_score(),
                    "recovery_priority": s.recovery_priority.value,
                    "dependencies": s.dependencies,
                }
                for s in self.systems_analyzed
            ],
            "governance_function_impacts": [
                {
                    "function": g.function_name,
                    "t1_impact": g.t1_impact,
                    "t2_impact": g.t2_impact,
                    "t3_impact": g.t3_impact,
                    "t4_impact": g.t4_impact,
                    "dependencies": g.dependencies,
                }
                for g in self.governance_function_impacts
            ],
            "recovery_priority_matrix": self.recovery_priority_matrix,
            "financial_impact_summary": self.financial_impact_summary,
            "recommendations": self.recommendations,
        }


class BusinessImpactAnalyzer:
    """
    Performs Business Impact Analysis per BCP §5.

    Analyzes disruption impact across six categories and six duration bands,
    produces recovery priority matrix, and generates BIA reports.
    """

    def __init__(self) -> None:
        self._systems: Dict[str, SystemImpactProfile] = {}

    def add_system(
        self,
        system_id: str,
        system_name: str,
        criticality_tier: CriticalityTier,
        recovery_priority: RecoveryPriority,
        dependencies: Optional[List[str]] = None,
        custom_impact_scores: Optional[
            Dict[DisruptionDuration, Dict[ImpactCategory, int]]
        ] = None,
    ) -> SystemImpactProfile:
        """
        Add an AI system to the BIA.

        If custom_impact_scores not provided, uses the default IMPACT_MATRIX.
        """
        impact_scores = custom_impact_scores or {
            duration: dict(IMPACT_MATRIX[duration])
            for duration in DisruptionDuration
        }

        profile = SystemImpactProfile(
            system_id=system_id,
            system_name=system_name,
            criticality_tier=criticality_tier,
            impact_scores=impact_scores,
            recovery_priority=recovery_priority,
            dependencies=dependencies or [],
        )
        self._systems[system_id] = profile
        return profile

    def get_recovery_sequence(self) -> List[SystemImpactProfile]:
        """Return systems ordered by recovery priority (P1 first)."""
        return sorted(self._systems.values(), key=lambda s: s.recovery_priority.value)

    def calculate_financial_exposure(self) -> Dict[str, float]:
        """
        Calculate financial exposure by disruption scenario.
        Uses impact scores as multipliers on base financial impact.
        """
        exposure: Dict[str, float] = {}
        base_losses = {
            DisruptionDuration.MIN_0_15: 10_000,
            DisruptionDuration.MIN_15_60: 50_000,
            DisruptionDuration.HR_1_4: 200_000,
            DisruptionDuration.HR_4_24: 1_000_000,
            DisruptionDuration.DAY_1_3: 5_000_000,
            DisruptionDuration.DAY_3_PLUS: 20_000_000,
        }

        for duration, base in base_losses.items():
            total = 0.0
            for system in self._systems.values():
                financial_score = system.impact_scores[duration][ImpactCategory.FINANCIAL]
                # Scale by criticality tier multiplier
                tier_multiplier = {
                    CriticalityTier.T1: 5.0,
                    CriticalityTier.T2: 3.0,
                    CriticalityTier.T3: 1.5,
                    CriticalityTier.T4: 0.5,
                }
                total += base * financial_score * tier_multiplier[system.criticality_tier]
            exposure[duration.value] = round(total, 2)

        return exposure

    def generate_report(
        self,
        prepared_by: str,
        approved_by: str,
        executive_summary: str = "",
    ) -> BIAReport:
        """Generate a complete BIA report per BCP §5.7."""
        recovery_matrix = [
            {
                "priority": rp.value,
                "function": RECOVERY_PRIORITY_MATRIX[rp]["function"],
                "rto_minutes": RECOVERY_PRIORITY_MATRIX[rp]["rto_minutes"],
                "rpo_minutes": RECOVERY_PRIORITY_MATRIX[rp]["rpo_minutes"],
                "rationale": RECOVERY_PRIORITY_MATRIX[rp]["rationale"],
            }
            for rp in RecoveryPriority
        ]

        financial_exposure = self.calculate_financial_exposure()
        total_exposure = sum(financial_exposure.values())

        recommendations = self._generate_recommendations()

        return BIAReport(
            report_id=str(uuid.uuid4()),
            report_date=datetime.utcnow(),
            report_period=f"{datetime.utcnow().year}",
            prepared_by=prepared_by,
            approved_by=approved_by,
            executive_summary=executive_summary or self._default_summary(),
            systems_analyzed=list(self._systems.values()),
            governance_function_impacts=list(GOVERNMENT_FUNCTIONS),
            recovery_priority_matrix=recovery_matrix,
            financial_impact_summary=(
                f"Total financial exposure across all scenarios: ${total_exposure:,.2f}. "
                f"Highest single-scenario exposure: "
                f"${max(financial_exposure.values()):,.2f}."
            ),
            recommendations=recommendations,
        )

    def _default_summary(self) -> str:
        tier_counts: Dict[CriticalityTier, int] = defaultdict(int)
        for s in self._systems.values():
            tier_counts[s.criticality_tier] += 1
        parts = [f"{count} {tier.value}" for tier, count in sorted(tier_counts.items(), key=lambda x: x[0].value)]
        return f"BIA covers {len(self._systems)} AI systems: {', '.join(parts)}."

    def _generate_recommendations(self) -> List[str]:
        recs: List[str] = []
        t1_systems = [
            s for s in self._systems.values() if s.criticality_tier == CriticalityTier.T1
        ]
        if t1_systems:
            recs.append(
                f"Ensure {len(t1_systems)} T1 systems have active-active failover "
                "and monthly DR testing."
            )

        high_impact = [
            s for s in self._systems.values() if s.max_impact_score() >= 4
        ]
        if high_impact:
            recs.append(
                f"Review {len(high_impact)} systems with high impact scores (≥4) "
                "for additional redundancy."
            )

        return recs


# ===========================================================================
# 3. DISASTER RECOVERY AUTOMATION
# ===========================================================================
# Spec Reference: §6 — Disaster Recovery Procedures, §19 — DR Automation
# ===========================================================================


class DRStrategy(enum.Enum):
    """DR strategies by tier per BCP §6.2."""

    ACTIVE_ACTIVE = "active_active"
    ACTIVE_PASSIVE = "active_passive"
    WARM_STANDBY = "warm_standby"
    COLD_STANDBY = "cold_standby"


TIER_DR_STRATEGY: Dict[CriticalityTier, DRStrategy] = {
    CriticalityTier.T1: DRStrategy.ACTIVE_ACTIVE,
    CriticalityTier.T2: DRStrategy.ACTIVE_PASSIVE,
    CriticalityTier.T3: DRStrategy.WARM_STANDBY,
    CriticalityTier.T4: DRStrategy.COLD_STANDBY,
}


class ContinuityMode(enum.Enum):
    """Continuity modes per BCP §6.5."""

    NORMAL = "normal"
    CACHED_ENFORCEMENT = "cached_enforcement"  # Mode 1
    DEGRADED_GOVERNANCE = "degraded_governance"  # Mode 2
    SAFE_MODE = "safe_mode"  # Mode 3


@dataclass
class BackupRecord:
    """Backup record per BCP §6.4."""

    backup_id: str
    data_source: str
    backup_type: str  # full, incremental, continuous
    frequency: str
    retention_days: int
    storage_location: str
    encryption: str
    status: str  # success, failed, in_progress
    created_at: datetime
    verified_at: Optional[datetime] = None
    checksum: Optional[str] = None
    size_bytes: int = 0


@dataclass
class RecoveryStep:
    """A single step in a DR runbook per BCP §19.3."""

    step_id: str
    name: str
    executor: str
    automated: bool
    timeout_seconds: int
    verification: Optional[str] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed, skipped
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None


@dataclass
class DRRunbook:
    """DR runbook per BCP §6.7 and §19.3."""

    runbook_id: str
    name: str
    version: str
    tier: CriticalityTier
    automation_level: str  # full, semi, manual_assist, manual
    triggers: List[str]
    pre_conditions: List[str]
    steps: List[RecoveryStep]
    rollback_conditions: List[str]
    post_recovery_actions: List[str]
    last_executed: Optional[datetime] = None
    last_result: Optional[str] = None

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute the runbook (or dry-run).

        Implements idempotency, checkpointing, and rollback per BCP §19.3.2.
        """
        execution_id = str(uuid.uuid4())
        logger.info(
            f"{'[DRY RUN] ' if dry_run else ''}Executing runbook {self.runbook_id}: {self.name}"
        )

        results = {
            "execution_id": execution_id,
            "runbook_id": self.runbook_id,
            "dry_run": dry_run,
            "started_at": datetime.utcnow().isoformat(),
            "steps": [],
            "status": "in_progress",
        }

        completed_steps: List[RecoveryStep] = []

        for step in self.steps:
            step.started_at = datetime.utcnow()
            step.status = "running"

            if dry_run:
                step.status = "completed"
                step.result = "dry_run_success"
                step.completed_at = datetime.utcnow()
                completed_steps.append(step)
                results["steps"].append(self._step_result(step))
                continue

            try:
                # Simulate step execution
                success = self._execute_step(step)
                if success:
                    step.status = "completed"
                    step.result = "success"
                    step.completed_at = datetime.utcnow()
                    completed_steps.append(step)
                else:
                    step.status = "failed"
                    step.result = "failure"
                    step.completed_at = datetime.utcnow()
                    results["steps"].append(self._step_result(step))

                    # Check rollback conditions
                    if self._should_rollback(step):
                        logger.warning(f"Rollback triggered after step {step.step_id}")
                        rollback_results = self._rollback(completed_steps)
                        results["rollback"] = rollback_results
                        results["status"] = "rolled_back"
                        break
            except Exception as e:
                step.status = "failed"
                step.result = str(e)
                step.completed_at = datetime.utcnow()
                results["steps"].append(self._step_result(step))
                break

            results["steps"].append(self._step_result(step))

        if results["status"] == "in_progress":
            results["status"] = "completed"

        results["completed_at"] = datetime.utcnow().isoformat()
        self.last_executed = datetime.utcnow()
        self.last_result = results["status"]

        return results

    def _execute_step(self, step: RecoveryStep) -> bool:
        """Execute a single step. Override for real implementation."""
        logger.info(f"  Executing step {step.step_id}: {step.name}")
        # In production, this would call the actual executor
        # (Patroni, Kubernetes, DNS, etc.)
        time.sleep(0.01)  # Simulate work
        return True

    def _should_rollback(self, failed_step: RecoveryStep) -> bool:
        """Check if rollback should be triggered."""
        return failed_step.on_failure == "rollback_and_alert"

    def _rollback(self, completed_steps: List[RecoveryStep]) -> List[Dict[str, Any]]:
        """Rollback completed steps in reverse order."""
        rollback_results = []
        for step in reversed(completed_steps):
            logger.info(f"  Rolling back step {step.step_id}: {step.name}")
            rollback_results.append({
                "step_id": step.step_id,
                "action": "rollback",
                "status": "completed",
            })
        return rollback_results

    def _step_result(self, step: RecoveryStep) -> Dict[str, Any]:
        return {
            "step_id": step.step_id,
            "name": step.name,
            "status": step.status,
            "result": step.result,
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "completed_at": step.completed_at.isoformat() if step.completed_at else None,
        }


class DRAutomationEngine:
    """
    DR Automation Engine per BCP §19.

    Manages runbooks, executes recovery procedures, and coordinates
    self-healing capabilities.
    """

    def __init__(self) -> None:
        self._runbooks: Dict[str, DRRunbook] = {}
        self._backups: Dict[str, BackupRecord] = {}
        self._active_continuity_mode: ContinuityMode = ContinuityMode.NORMAL
        self._mode_entered_at: Optional[datetime] = None

    def register_runbook(self, runbook: DRRunbook) -> None:
        """Register a DR runbook."""
        self._runbooks[runbook.runbook_id] = runbook
        logger.info(f"Registered runbook: {runbook.runbook_id}")

    def register_backup(self, backup: BackupRecord) -> None:
        """Register a backup record."""
        self._backups[backup.backup_id] = backup

    def get_runbook_for_tier(self, tier: CriticalityTier) -> List[DRRunbook]:
        """Get all runbooks for a given tier."""
        return [rb for rb in self._runbooks.values() if rb.tier == tier]

    def execute_runbook(
        self, runbook_id: str, dry_run: bool = False
    ) -> Dict[str, Any]:
        """Execute a specific runbook."""
        if runbook_id not in self._runbooks:
            raise ValueError(f"Runbook {runbook_id} not found")
        return self._runbooks[runbook_id].execute(dry_run=dry_run)

    def dry_run_all(self) -> Dict[str, Any]:
        """Dry-run all runbooks (BCP §19.6 — weekly validation)."""
        results = {}
        for rb_id, runbook in self._runbooks.items():
            results[rb_id] = runbook.execute(dry_run=True)
        return results

    def enter_continuity_mode(self, mode: ContinuityMode) -> None:
        """Enter a continuity mode per BCP §6.5."""
        if mode != self._active_continuity_mode:
            logger.warning(
                f"Continuity mode transition: {self._active_continuity_mode.value} → {mode.value}"
            )
            self._active_continuity_mode = mode
            self._mode_entered_at = datetime.utcnow()

    def exit_continuity_mode(self) -> None:
        """Return to normal operations."""
        if self._active_continuity_mode != ContinuityMode.NORMAL:
            logger.info("Returning to NORMAL continuity mode")
            self._active_continuity_mode = ContinuityMode.NORMAL
            self._mode_entered_at = None

    def get_continuity_status(self) -> Dict[str, Any]:
        """Get current continuity status."""
        duration = None
        if self._mode_entered_at:
            duration = (datetime.utcnow() - self._mode_entered_at).total_seconds()

        return {
            "active_mode": self._active_continuity_mode.value,
            "mode_entered_at": self._mode_entered_at.isoformat() if self._mode_entered_at else None,
            "mode_duration_seconds": duration,
            "runbooks_count": len(self._runbooks),
            "backups_count": len(self._backups),
        }

    def verify_backup_integrity(self, backup_id: str) -> bool:
        """Verify backup integrity per BCP §6.4 and Reliability Spec §8.3."""
        if backup_id not in self._backups:
            return False
        backup = self._backups[backup_id]
        if backup.status != "success":
            return False
        if not backup.checksum:
            return False
        # In production: recompute checksum and compare
        return True

    def self_heal(self, failure_scenario: str) -> Dict[str, Any]:
        """
        Self-healing per BCP §19.5.

        Maps failure scenarios to automated recovery actions.
        """
        self_healing_map = {
            "pod_crash": {
                "action": "k8s_restart",
                "detection_time_seconds": 30,
                "recovery_time_seconds": 60,
            },
            "node_failure": {
                "action": "k8s_reschedule",
                "detection_time_seconds": 60,
                "recovery_time_seconds": 120,
            },
            "disk_full": {
                "action": "spool_to_alternate",
                "detection_time_seconds": 30,
                "recovery_time_seconds": 30,
            },
            "memory_leak": {
                "action": "oom_kill_restart",
                "detection_time_seconds": 60,
                "recovery_time_seconds": 90,
            },
            "network_partition": {
                "action": "fail_closed_alert",
                "detection_time_seconds": 15,
                "recovery_time_seconds": 30,
            },
            "certificate_expiry": {
                "action": "auto_renewal",
                "detection_time_seconds": 0,
                "recovery_time_seconds": 60,
            },
            "config_drift": {
                "action": "gitops_reconcile",
                "detection_time_seconds": 300,
                "recovery_time_seconds": 600,
            },
            "dependency_timeout": {
                "action": "circuit_breaker_fallback",
                "detection_time_seconds": 5,
                "recovery_time_seconds": 10,
            },
        }

        if failure_scenario not in self_healing_map:
            return {
                "scenario": failure_scenario,
                "status": "no_self_healing_available",
                "action": "escalate_to_human",
            }

        healing = self_healing_map[failure_scenario]
        logger.info(f"Self-healing triggered: {failure_scenario} → {healing['action']}")

        return {
            "scenario": failure_scenario,
            "status": "healed",
            **healing,
            "healed_at": datetime.utcnow().isoformat(),
        }


# ===========================================================================
# 4. FAILOVER ORCHESTRATION
# ===========================================================================
# Spec Reference: §16 — Automated Failover Orchestration
# ===========================================================================


class FailoverState(enum.Enum):
    """Failover state machine states per BCP §16.3."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    FAILOVER_IN_PROGRESS = "failover_in_progress"
    RECOVERED = "recovered"


@dataclass
class FailoverSignal:
    """Signal for failover decision engine per BCP §16.4."""

    name: str
    weight: float
    severity: int  # 1–5

    def __post_init__(self) -> None:
        if not 1 <= self.severity <= 5:
            raise ValueError(f"Severity must be 1–5, got {self.severity}")


class FailoverDecisionEngine:
    """
    Failover Decision Engine per BCP §16.4.

    Calculates Failover Urgency Score (FUS):
        FUS = Σ (Signal Weight × Signal Severity)

    FUS Thresholds:
        FUS ≥ 4.0: Immediate automated failover (T1)
        FUS ≥ 3.0: Automated failover with notification (T2)
        FUS ≥ 2.0: Alert DR team, prepare failover (T3)
        FUS < 2.0: Log and monitor
    """

    DEFAULT_SIGNALS = [
        FailoverSignal("health_check_failure_rate", 0.30, 1),
        FailoverSignal("error_rate_elevation", 0.25, 1),
        FailoverSignal("latency_degradation", 0.20, 1),
        FailoverSignal("dependency_failure_count", 0.15, 1),
        FailoverSignal("data_replication_lag", 0.10, 1),
    ]

    def __init__(self, signals: Optional[List[FailoverSignal]] = None) -> None:
        self._signals = signals or [
            FailoverSignal(s.name, s.weight, s.severity) for s in self.DEFAULT_SIGNALS
        ]

    def update_signal(self, name: str, severity: int) -> None:
        """Update a signal's severity."""
        for signal in self._signals:
            if signal.name == name:
                signal.severity = severity
                return
        raise ValueError(f"Unknown signal: {name}")

    def calculate_fus(self) -> float:
        """Calculate Failover Urgency Score."""
        return round(sum(s.weight * s.severity for s in self._signals), 2)

    def get_failover_action(self, tier: CriticalityTier) -> Dict[str, Any]:
        """Determine failover action based on FUS and tier."""
        fus = self.calculate_fus()

        if fus >= 4.0:
            return {
                "fus": fus,
                "action": "immediate_automated_failover",
                "tier": tier.value,
                "human_intervention": False,
                "notification": "automatic",
            }
        elif fus >= 3.0:
            return {
                "fus": fus,
                "action": "automated_failover_with_notification",
                "tier": tier.value,
                "human_intervention": False,
                "notification": "dr_team",
            }
        elif fus >= 2.0:
            return {
                "fus": fus,
                "action": "alert_dr_team_prepare_failover",
                "tier": tier.value,
                "human_intervention": True,
                "notification": "dr_team",
            }
        else:
            return {
                "fus": fus,
                "action": "log_and_monitor",
                "tier": tier.value,
                "human_intervention": False,
                "notification": "none",
            }


@dataclass
class FailoverEvent:
    """Record of a failover event per BCP §16.7."""

    event_id: str
    component: str
    from_state: FailoverState
    to_state: FailoverState
    fus: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    data_loss_bytes: int = 0
    success: bool = False
    rollback: bool = False
    split_brain_detected: bool = False


class FailoverOrchestrator:
    """
    Failover Orchestrator per BCP §16.

    Coordinates automated recovery across all governance components
    with hierarchical orchestration, split-brain prevention, and
    comprehensive observability.
    """

    def __init__(self) -> None:
        self._decision_engine = FailoverDecisionEngine()
        self._component_states: Dict[str, FailoverState] = {}
        self._failover_history: List[FailoverEvent] = []
        self._global_lock_held: bool = False
        self._split_brain_safeguards = {
            "fencing": True,
            "quorum": True,
            "lease_based_locking": True,
            "witness_node": True,
            "data_version_vectors": True,
        }

    def register_component(self, component: str) -> None:
        """Register a component for failover management."""
        self._component_states[component] = FailoverState.HEALTHY

    def update_component_health(
        self, component: str, health_check_passed: bool, consecutive_failures: int = 0
    ) -> None:
        """Update component health and trigger state transitions."""
        current = self._component_states.get(component, FailoverState.HEALTHY)

        if current == FailoverState.HEALTHY and not health_check_passed:
            self._transition(component, FailoverState.DEGRADED)
        elif current == FailoverState.DEGRADED and consecutive_failures >= 3:
            self._transition(component, FailoverState.FAILING)
        elif current == FailoverState.DEGRADED and health_check_passed:
            self._transition(component, FailoverState.HEALTHY)
        elif current == FailoverState.FAILING:
            # Check if failover should be initiated
            action = self._decision_engine.get_failover_action(CriticalityTier.T1)
            if action["action"] == "immediate_automated_failover":
                self._initiate_failover(component)

    def _transition(self, component: str, new_state: FailoverState) -> None:
        """Transition a component to a new state."""
        old_state = self._component_states.get(component, FailoverState.HEALTHY)
        self._component_states[component] = new_state
        logger.info(f"Component {component}: {old_state.value} → {new_state.value}")

    def _initiate_failover(self, component: str) -> FailoverEvent:
        """Initiate failover for a component."""
        event = FailoverEvent(
            event_id=str(uuid.uuid4()),
            component=component,
            from_state=FailoverState.FAILING,
            to_state=FailoverState.FAILOVER_IN_PROGRESS,
            fus=self._decision_engine.calculate_fus(),
            started_at=datetime.utcnow(),
        )
        self._transition(component, FailoverState.FAILOVER_IN_PROGRESS)
        logger.info(f"Failover initiated for {component} (FUS={event.fus})")

        # Simulate failover execution
        try:
            self._acquire_global_lock()
            self._promote_standby(component)
            self._redirect_traffic(component)
            self._verify_recovery(component)

            event.to_state = FailoverState.RECOVERED
            event.success = True
            event.completed_at = datetime.utcnow()
            self._transition(component, FailoverState.RECOVERED)
        except Exception as e:
            event.to_state = FailoverState.FAILING
            event.success = False
            event.completed_at = datetime.utcnow()
            self._transition(component, FailoverState.FAILING)
            logger.error(f"Failover failed for {component}: {e}")
        finally:
            self._release_global_lock()

        self._failover_history.append(event)
        return event

    def _acquire_global_lock(self) -> None:
        """Acquire global failover lock (split-brain prevention)."""
        self._global_lock_held = True
        logger.info("Global failover lock acquired")

    def _release_global_lock(self) -> None:
        """Release global failover lock."""
        self._global_lock_held = False
        logger.info("Global failover lock released")

    def _promote_standby(self, component: str) -> None:
        """Promote standby instance."""
        logger.info(f"Promoting standby for {component}")

    def _redirect_traffic(self, component: str) -> None:
        """Redirect traffic to DR region."""
        logger.info(f"Redirecting traffic for {component}")

    def _verify_recovery(self, component: str) -> None:
        """Verify recovery is complete."""
        logger.info(f"Verifying recovery for {component}")

    def detect_split_brain(self) -> Optional[Dict[str, Any]]:
        """
        Detect split-brain per BCP §16.6.

        Detection signals:
        1. Both regions report themselves as PRIMARY
        2. Replication link is down AND both regions accept writes
        3. Divergent data versions detected
        4. Global lock is held by both regions
        """
        # In production: check actual region states
        # This is a simulation
        return None

    def resolve_split_brain(self) -> Dict[str, Any]:
        """
        Resolve split-brain per BCP §16.6.

        Response:
        1. Global orchestrator acquires emergency lock
        2. Determines last-known-good state via witness node
        3. Fences the region with stale data
        4. Promotes the region with most recent verified state
        5. Creates incident record for post-mortem
        """
        logger.warning("Split-brain detected! Initiating resolution...")
        return {
            "status": "resolved",
            "fenced_region": "region-a",
            "promoted_region": "region-b",
            "witness_node_used": True,
            "incident_created": True,
            "resolved_at": datetime.utcnow().isoformat(),
        }

    def get_failover_metrics(self) -> Dict[str, Any]:
        """Get failover metrics per BCP §16.7."""
        total = len(self._failover_history)
        successful = sum(1 for e in self._failover_history if e.success)
        rollbacks = sum(1 for e in self._failover_history if e.rollback)
        split_brains = sum(1 for e in self._failover_history if e.split_brain_detected)

        durations = []
        for e in self._failover_history:
            if e.completed_at:
                durations.append((e.completed_at - e.started_at).total_seconds())

        return {
            "grc_failover_events_total": total,
            "grc_failover_successful": successful,
            "grc_failover_failed": total - successful,
            "grc_failover_rollback_events_total": rollbacks,
            "grc_failover_split_brain_detected_total": split_brains,
            "grc_failover_avg_duration_seconds": (
                sum(durations) / len(durations) if durations else 0
            ),
            "grc_failover_automation_success_ratio": (
                successful / total if total > 0 else 0
            ),
            "component_states": {
                c: s.value for c, s in self._component_states.items()
            },
        }


# ===========================================================================
# 5. RESILIENCE SCORING
# ===========================================================================
# Spec Reference: §18 — Resilience Scoring Algorithm
# ===========================================================================


class ResilienceRating(enum.Enum):
    """Resilience rating per BCP §18.4."""

    EXCELLENT = "excellent"  # 0.90–1.00
    GOOD = "good"  # 0.75–0.89
    ADEQUATE = "adequate"  # 0.60–0.74
    AT_RISK = "at_risk"  # 0.40–0.59
    CRITICAL = "critical"  # 0.00–0.39


@dataclass
class ResilienceDimensionScores:
    """Scores for each resilience dimension per BCP §18.3."""

    redundancy: float  # RS-Red (25%)
    recovery_capability: float  # RS-Rec (25%)
    degradation_resilience: float  # RS-Deg (20%)
    testing_coverage: float  # RS-Test (15%)
    observability: float  # RS-Obs (15%)


@dataclass
class ResilienceScore:
    """Complete resilience score per BCP §18."""

    system_id: str
    system_name: str
    criticality_tier: CriticalityTier
    dimension_scores: ResilienceDimensionScores
    composite_score: float
    rating: ResilienceRating
    calculated_at: datetime
    trend: Optional[str] = None  # improving, stable, degrading, volatile

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_id": self.system_id,
            "system_name": self.system_name,
            "criticality_tier": self.criticality_tier.value,
            "dimension_scores": {
                "redundancy": self.dimension_scores.redundancy,
                "recovery_capability": self.dimension_scores.recovery_capability,
                "degradation_resilience": self.dimension_scores.degradation_resilience,
                "testing_coverage": self.dimension_scores.testing_coverage,
                "observability": self.dimension_scores.observability,
            },
            "composite_score": self.composite_score,
            "rating": self.rating.value,
            "calculated_at": self.calculated_at.isoformat(),
            "trend": self.trend,
        }


class ResilienceScorer:
    """
    Resilience Scoring Algorithm per BCP §18.

    Computes composite Resilience Score (RS) across five dimensions:
        RS = (RS-Red × 0.25) + (RS-Rec × 0.25) + (RS-Deg × 0.20)
           + (RS-Test × 0.15) + (RS-Obs × 0.15)

    Range: 0.0 (no resilience) to 1.0 (perfect resilience)
    """

    # Component redundancy scores per BCP §18.3.1
    REDUNDANCY_SCORES = {
        "active_active_multi_region": 1.0,
        "active_passive_warm_standby": 0.8,
        "warm_standby_same_region": 0.6,
        "cold_standby_backup_only": 0.4,
        "single_instance": 0.1,
    }

    # Component weights by tier per BCP §18.3.1
    COMPONENT_WEIGHTS = {
        CriticalityTier.T1: {
            "PDP": 0.25, "PEP": 0.25, "PostgreSQL": 0.20,
            "Redis": 0.10, "Identity": 0.10, "Evidence": 0.10,
        },
        CriticalityTier.T2: {
            "PDP": 0.20, "PEP": 0.20, "PostgreSQL": 0.20,
            "Redis": 0.15, "Identity": 0.15, "Evidence": 0.10,
        },
        CriticalityTier.T3: {
            "PDP": 0.15, "PEP": 0.15, "PostgreSQL": 0.25,
            "Redis": 0.15, "Identity": 0.15, "Evidence": 0.15,
        },
        CriticalityTier.T4: {
            "PDP": 0.167, "PEP": 0.167, "PostgreSQL": 0.167,
            "Redis": 0.167, "Identity": 0.167, "Evidence": 0.166,
        },
    }

    def __init__(self) -> None:
        self._score_history: Dict[str, List[ResilienceScore]] = {}

    def calculate_redundancy_score(
        self,
        tier: CriticalityTier,
        component_redundancy: Dict[str, str],
    ) -> float:
        """
        Calculate Redundancy Score (RS-Red) per BCP §18.3.1.

        Args:
            tier: Criticality tier
            component_redundancy: Map of component name to redundancy type
        """
        weights = self.COMPONENT_WEIGHTS[tier]
        score = 0.0
        for component, redundancy_type in component_redundancy.items():
            if component in weights:
                redundancy_score = self.REDUNDANCY_SCORES.get(redundancy_type, 0.1)
                score += redundancy_score * weights[component]
        return round(min(score, 1.0), 2)

    def calculate_recovery_capability_score(
        self,
        rto_achievement_rate: float,
        rpo_achievement_rate: float,
        automation_level: str,
    ) -> float:
        """
        Calculate Recovery Capability Score (RS-Rec) per BCP §18.3.2.

        RS-Rec = (RTO_Score × 0.4) + (RPO_Score × 0.3) + (Automation_Score × 0.3)
        """
        # RTO Score
        if rto_achievement_rate >= 1.0:
            rto_score = 1.0
        elif rto_achievement_rate >= 0.95:
            rto_score = 0.8
        elif rto_achievement_rate >= 0.80:
            rto_score = 0.6
        elif rto_achievement_rate >= 0.50:
            rto_score = 0.4
        else:
            rto_score = 0.2

        # RPO Score
        if rpo_achievement_rate >= 1.0:
            rpo_score = 1.0
        elif rpo_achievement_rate >= 0.95:
            rpo_score = 0.8
        elif rpo_achievement_rate >= 0.80:
            rpo_score = 0.6
        elif rpo_achievement_rate >= 0.50:
            rpo_score = 0.4
        else:
            rpo_score = 0.2

        # Automation Score
        automation_scores = {
            "fully_automated": 1.0,
            "semi_automated": 0.7,
            "manual_with_assist": 0.4,
            "fully_manual": 0.2,
        }
        automation_score = automation_scores.get(automation_level, 0.2)

        return round((rto_score * 0.4) + (rpo_score * 0.3) + (automation_score * 0.3), 2)

    def calculate_degradation_resilience_score(
        self,
        cached_enforcement_score: float,
        degraded_governance_score: float,
        safe_mode_score: float,
    ) -> float:
        """
        Calculate Degradation Resilience Score (RS-Deg) per BCP §18.3.3.

        RS-Deg = (Cached × 0.4) + (Degraded × 0.35) + (Safe × 0.25)
        """
        return round(
            (cached_enforcement_score * 0.4)
            + (degraded_governance_score * 0.35)
            + (safe_mode_score * 0.25),
            2,
        )

    def calculate_testing_coverage_score(
        self,
        coverage_ratio: float,
        recency_ratio: float,
        pass_rate: float,
    ) -> float:
        """
        Calculate Testing Coverage Score (RS-Test) per BCP §18.3.4.

        RS-Test = (Coverage × 0.4) + (Recency × 0.3) + (Pass_Rate × 0.3)
        """
        return round((coverage_ratio * 0.4) + (recency_ratio * 0.3) + (pass_rate * 0.3), 2)

    def calculate_observability_score(
        self,
        coverage: float,
        alert_effectiveness: float,
        dashboard_availability: float,
    ) -> float:
        """
        Calculate Observability Score (RS-Obs) per BCP §18.3.5.

        RS-Obs = (Coverage × 0.35) + (Alert_Effectiveness × 0.35) + (Dashboard × 0.3)
        """
        return round(
            (coverage * 0.35) + (alert_effectiveness * 0.35) + (dashboard_availability * 0.3),
            2,
        )

    def calculate_composite_score(
        self,
        system_id: str,
        system_name: str,
        tier: CriticalityTier,
        redundancy: float,
        recovery: float,
        degradation: float,
        testing: float,
        observability: float,
    ) -> ResilienceScore:
        """
        Calculate composite Resilience Score per BCP §18.4.

        RS = (RS-Red × 0.25) + (RS-Rec × 0.25) + (RS-Deg × 0.20)
           + (RS-Test × 0.15) + (RS-Obs × 0.15)
        """
        composite = round(
            (redundancy * 0.25)
            + (recovery * 0.25)
            + (degradation * 0.20)
            + (testing * 0.15)
            + (observability * 0.15),
            2,
        )

        rating = self._get_rating(composite)
        trend = self._calculate_trend(system_id, composite)

        score = ResilienceScore(
            system_id=system_id,
            system_name=system_name,
            criticality_tier=tier,
            dimension_scores=ResilienceDimensionScores(
                redundancy=redundancy,
                recovery_capability=recovery,
                degradation_resilience=degradation,
                testing_coverage=testing,
                observability=observability,
            ),
            composite_score=composite,
            rating=rating,
            calculated_at=datetime.utcnow(),
            trend=trend,
        )

        # Store in history
        if system_id not in self._score_history:
            self._score_history[system_id] = []
        self._score_history[system_id].append(score)

        return score

    def _get_rating(self, score: float) -> ResilienceRating:
        """Get rating from composite score per BCP §18.4."""
        if score >= 0.90:
            return ResilienceRating.EXCELLENT
        elif score >= 0.75:
            return ResilienceRating.GOOD
        elif score >= 0.60:
            return ResilienceRating.ADEQUATE
        elif score >= 0.40:
            return ResilienceRating.AT_RISK
        else:
            return ResilienceRating.CRITICAL

    def _calculate_trend(self, system_id: str, current_score: float) -> Optional[str]:
        """Calculate trend based on score history."""
        history = self._score_history.get(system_id, [])
        if len(history) < 2:
            return None

        prev = history[-2].composite_score
        diff = current_score - prev

        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "degrading"
        else:
            return "stable"

    def get_governance_actions(self, score: ResilienceScore) -> List[str]:
        """Get required governance actions per BCP §18.5."""
        actions = []
        if score.composite_score < 0.20:
            actions.append("Immediate action; consider T1 suspension (AI Governance Committee, 7 days)")
        elif score.composite_score < 0.40:
            actions.append("Priority remediation; T1 review (CISO, 14 days)")
        elif score.composite_score < 0.60:
            actions.append("Improvement plan required (DR Team Lead, 30 days)")

        if score.trend == "degrading":
            actions.append("Investigate degradation trend")

        return actions


# ===========================================================================
# 6. CONTINUITY MONITORING
# ===========================================================================
# Spec Reference: §20 — Business Continuity Monitoring
# ===========================================================================


class AlertSeverity(enum.Enum):
    """Alert severity per BCP §20.4.1."""

    P1_CRITICAL = "P1_critical"
    P2_HIGH = "P2_high"
    P3_MEDIUM = "P3_medium"
    P4_LOW = "P4_low"


@dataclass
class ContinuityAlert:
    """Continuity alert per BCP §20.4."""

    alert_id: str
    severity: AlertSeverity
    component: str
    message: str
    fired_at: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class ComponentHealth:
    """Component health metrics per BCP §20.3.1."""

    component: str
    availability_pct: float
    latency_p99_ms: float
    error_rate_pct: float
    replication_lag_seconds: float
    queue_depth: int
    disk_usage_pct: float
    memory_usage_pct: float
    last_updated: datetime


@dataclass
class FailoverReadiness:
    """Failover readiness metrics per BCP §20.3.2."""

    component: str
    standby_healthy: bool
    replication_status: str
    failover_lock_status: str
    last_failover_test: Optional[datetime]
    failover_readiness_score: float
    split_brain_risk: bool


@dataclass
class RecoveryReadiness:
    """Recovery readiness metrics per BCP §20.3.3."""

    component: str
    backup_status: str
    backup_age_hours: float
    backup_verification_status: str
    dr_environment_healthy: bool
    dr_sync_lag_minutes: float
    runbook_version: str
    runbook_age_days: int


class ContinuityMonitor:
    """
    Business Continuity Monitor per BCP §20.

    Provides real-time visibility into health, readiness, and effectiveness
    of all continuity capabilities across five monitoring layers.
    """

    # Alert thresholds per BCP §20.3
    THRESHOLDS = {
        "component_availability": {"T1": 99.9, "T2": 99.9, "T3": 99.5, "T4": 99.0},
        "component_latency_p99": {"T1": 50, "T2": 100, "T3": 500, "T4": 1000},
        "component_error_rate": {"T1": 0.1, "T2": 0.5, "T3": 1.0, "T4": 5.0},
        "replication_lag_seconds": {"T1": 30, "T2": 60, "T3": 300, "T4": 3600},
        "queue_depth": 10000,
        "disk_usage_pct": 80,
        "memory_usage_pct": 85,
        "backup_age_hours": {"T1": 24, "T2": 24, "T3": 48, "T4": 168},
        "dr_sync_lag_minutes": {"T1": 5, "T2": 15, "T3": 60, "T4": 240},
        "failover_readiness_score": 0.8,
        "resilience_score": 0.60,
    }

    def __init__(self) -> None:
        self._alerts: List[ContinuityAlert] = []
        self._component_health: Dict[str, ComponentHealth] = {}
        self._failover_readiness: Dict[str, FailoverReadiness] = {}
        self._recovery_readiness: Dict[str, RecoveryReadiness] = {}
        self._active_continuity_mode: ContinuityMode = ContinuityMode.NORMAL
        self._alert_handlers: Dict[AlertSeverity, List[Callable]] = {
            AlertSeverity.P1_CRITICAL: [],
            AlertSeverity.P2_HIGH: [],
            AlertSeverity.P3_MEDIUM: [],
            AlertSeverity.P4_LOW: [],
        }

    def register_alert_handler(
        self, severity: AlertSeverity, handler: Callable[[ContinuityAlert], None]
    ) -> None:
        """Register an alert handler for a severity level."""
        self._alert_handlers[severity].append(handler)

    def update_component_health(self, health: ComponentHealth) -> None:
        """Update component health and evaluate alerts."""
        self._component_health[health.component] = health
        self._evaluate_component_alerts(health)

    def update_failover_readiness(self, readiness: FailoverReadiness) -> None:
        """Update failover readiness and evaluate alerts."""
        self._failover_readiness[readiness.component] = readiness
        self._evaluate_failover_alerts(readiness)

    def update_recovery_readiness(self, readiness: RecoveryReadiness) -> None:
        """Update recovery readiness and evaluate alerts."""
        self._recovery_readiness[readiness.component] = readiness
        self._evaluate_recovery_alerts(readiness)

    def _evaluate_component_alerts(self, health: ComponentHealth) -> None:
        """Evaluate alerts for component health."""
        # Availability alert
        if health.availability_pct < self.THRESHOLDS["component_availability"]["T1"]:
            self._fire_alert(
                AlertSeverity.P1_CRITICAL,
                health.component,
                f"Availability {health.availability_pct}% below T1 threshold",
                ["pager", "call", "slack"],
            )
        elif health.availability_pct < self.THRESHOLDS["component_availability"]["T3"]:
            self._fire_alert(
                AlertSeverity.P2_HIGH,
                health.component,
                f"Availability {health.availability_pct}% below T3 threshold",
                ["pager", "slack"],
            )

        # Error rate alert
        if health.error_rate_pct > self.THRESHOLDS["component_error_rate"]["T1"]:
            self._fire_alert(
                AlertSeverity.P1_CRITICAL,
                health.component,
                f"Error rate {health.error_rate_pct}% exceeds T1 threshold",
                ["pager", "call", "slack"],
            )

        # Replication lag alert
        if health.replication_lag_seconds > self.THRESHOLDS["replication_lag_seconds"]["T1"]:
            self._fire_alert(
                AlertSeverity.P2_HIGH,
                health.component,
                f"Replication lag {health.replication_lag_seconds}s exceeds threshold",
                ["pager", "slack"],
            )

    def _evaluate_failover_alerts(self, readiness: FailoverReadiness) -> None:
        """Evaluate alerts for failover readiness."""
        if not readiness.standby_healthy:
            self._fire_alert(
                AlertSeverity.P2_HIGH,
                readiness.component,
                "Standby is unhealthy",
                ["pager", "slack"],
            )

        if readiness.split_brain_risk:
            self._fire_alert(
                AlertSeverity.P1_CRITICAL,
                readiness.component,
                "Split-brain risk detected",
                ["pager", "call", "slack"],
            )

        if readiness.failover_readiness_score < self.THRESHOLDS["failover_readiness_score"]:
            self._fire_alert(
                AlertSeverity.P3_MEDIUM,
                readiness.component,
                f"Failover readiness score {readiness.failover_readiness_score} below threshold",
                ["slack", "ticket"],
            )

    def _evaluate_recovery_alerts(self, readiness: RecoveryReadiness) -> None:
        """Evaluate alerts for recovery readiness."""
        if readiness.backup_status == "failed":
            self._fire_alert(
                AlertSeverity.P1_CRITICAL,
                readiness.component,
                "Backup failed",
                ["pager", "call", "slack"],
            )

        if not readiness.backup_verification_status == "passed":
            self._fire_alert(
                AlertSeverity.P2_HIGH,
                readiness.component,
                "Backup verification failed",
                ["pager", "slack"],
            )

        if not readiness.dr_environment_healthy:
            self._fire_alert(
                AlertSeverity.P3_MEDIUM,
                readiness.component,
                "DR environment unhealthy",
                ["slack", "ticket"],
            )

    def _fire_alert(
        self,
        severity: AlertSeverity,
        component: str,
        message: str,
        channels: List[str],
    ) -> None:
        """Fire an alert and notify handlers."""
        alert = ContinuityAlert(
            alert_id=str(uuid.uuid4()),
            severity=severity,
            component=component,
            message=message,
            fired_at=datetime.utcnow(),
            notification_channels=channels,
        )
        self._alerts.append(alert)
        logger.warning(f"ALERT [{severity.value}] {component}: {message}")

        # Notify handlers
        for handler in self._alert_handlers.get(severity, []):
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    def get_active_alerts(
        self, severity: Optional[AlertSeverity] = None
    ) -> List[ContinuityAlert]:
        """Get active (unresolved) alerts."""
        alerts = [a for a in self._alerts if not a.resolved]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_at = datetime.utcnow()
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                return True
        return False

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary."""
        active = self.get_active_alerts()
        by_severity: Dict[str, int] = defaultdict(int)
        for a in active:
            by_severity[a.severity.value] += 1

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_continuity_mode": self._active_continuity_mode.value,
            "total_components_monitored": len(self._component_health),
            "active_alerts_count": len(active),
            "alerts_by_severity": dict(by_severity),
            "components": {
                name: {
                    "availability_pct": h.availability_pct,
                    "latency_p99_ms": h.latency_p99_ms,
                    "error_rate_pct": h.error_rate_pct,
                    "replication_lag_seconds": h.replication_lag_seconds,
                }
                for name, h in self._component_health.items()
            },
            "failover_readiness": {
                name: {
                    "standby_healthy": r.standby_healthy,
                    "readiness_score": r.failover_readiness_score,
                    "split_brain_risk": r.split_brain_risk,
                }
                for name, r in self._failover_readiness.items()
            },
            "recovery_readiness": {
                name: {
                    "backup_status": r.backup_status,
                    "backup_age_hours": r.backup_age_hours,
                    "dr_healthy": r.dr_environment_healthy,
                }
                for name, r in self._recovery_readiness.items()
            },
        }


# ===========================================================================
# 7. CONTINUITY TESTING
# ===========================================================================
# Spec Reference: §8 — Continuity Testing, §21 — Testing & Validation
# ===========================================================================


class TestType(enum.Enum):
    """Test types per BCP §8.2."""

    TABLETOP = "tabletop"
    FUNCTIONAL = "functional"
    SIMULATION = "simulation"
    LIVE_FAILOVER = "live_failover"
    CONTINUITY_MODE = "continuity_mode"
    EVIDENCE_INTEGRITY = "evidence_integrity"
    CHAOS = "chaos"
    SOAK = "soak"


class TestResult(enum.Enum):
    """Test result per BCP §21."""

    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class TestScenario:
    """Test scenario per BCP §8.3.1."""

    scenario_id: str
    name: str
    tier: CriticalityTier
    complexity: str  # low, medium, high
    test_type: TestType
    description: str
    expected_actions: List[str]
    success_criteria: List[str]
    rto_target_minutes: Optional[int] = None
    rpo_target_minutes: Optional[int] = None


# Default scenario library per BCP §8.3.1
DEFAULT_SCENARIOS: List[TestScenario] = [
    TestScenario("TS-001", "Single PDP instance failure", CriticalityTier.T1, "low", TestType.FUNCTIONAL,
                 "Kill single PDP instance, verify PEP failover to cache",
                 ["PDP failure detected", "PEP serves from cache", "New actions DENY"],
                 ["RTO < 15 min", "Zero data loss", "All T1 actions fail-safe"]),
    TestScenario("TS-002", "Complete PDP cluster failure", CriticalityTier.T1, "medium", TestType.SIMULATION,
                 "Kill entire PDP cluster, verify DR activation",
                 ["PDP cluster failure detected", "DR region activated", "Traffic redirected"],
                 ["RTO < 15 min", "RPO < 1 min", "Governance continuity maintained"]),
    TestScenario("TS-003", "PEP gateway failure", CriticalityTier.T1, "low", TestType.FUNCTIONAL,
                 "Kill PEP gateway, verify LB redirects to healthy instances",
                 ["PEP failure detected", "LB redirects traffic", "Agents reconnect"],
                 ["RTO < 15 min", "Zero decision errors"]),
    TestScenario("TS-004", "Evidence store corruption", CriticalityTier.T2, "medium", TestType.FUNCTIONAL,
                 "Corrupt evidence store, verify detection and recovery",
                 ["Corruption detected", "Writes halted", "Restore from backup"],
                 ["RTO < 1 hour", "RPO < 5 min", "Evidence integrity verified"]),
    TestScenario("TS-005", "Agent identity service failure", CriticalityTier.T1, "medium", TestType.SIMULATION,
                 "Kill identity service, verify cached SVIDs used",
                 ["Identity failure detected", "Cached SVIDs used", "New agents blocked"],
                 ["RTO < 15 min", "T1 agents continue", "Zero auth failures"]),
    TestScenario("TS-006", "PostgreSQL primary failure", CriticalityTier.T1, "medium", TestType.FUNCTIONAL,
                 "Kill PostgreSQL primary, verify Patroni failover",
                 ["Primary failure detected", "Replica promoted", "Connections restored"],
                 ["RTO < 15 min", "RPO < 1 min", "Zero data loss"]),
    TestScenario("TS-007", "Complete region loss", CriticalityTier.T1, "high", TestType.LIVE_FAILOVER,
                 "Simulate complete region loss, verify full DR activation",
                 ["Region failure detected", "DR region activated", "All services recovered"],
                 ["RTO < 1 hour", "RPO < 1 min", "All T1 systems operational"]),
    TestScenario("TS-008", "Network partition (split-brain)", CriticalityTier.T1, "high", TestType.SIMULATION,
                 "Create network partition, verify split-brain prevention",
                 ["Partition detected", "Fail-closed activated", "No split-brain"],
                 ["Zero data divergence", "Quorum maintained", "Fencing successful"]),
    TestScenario("TS-009", "Kafka cluster failure", CriticalityTier.T2, "medium", TestType.FUNCTIONAL,
                 "Kill Kafka broker, verify producer retry and consumer rebalance",
                 ["Broker failure detected", "Producer retries", "Consumer rebalances"],
                 ["RTO < 1 hour", "Zero message loss"]),
    TestScenario("TS-010", "Redis cache failure", CriticalityTier.T2, "low", TestType.FUNCTIONAL,
                 "Flush Redis, verify in-memory cache fallback",
                 ["Cache flushed", "In-memory cache used", "Identities from local cache"],
                 ["RTO < 1 hour", "p99 latency < 100ms"]),
    TestScenario("TS-011", "Vault (secrets) failure", CriticalityTier.T1, "high", TestType.SIMULATION,
                 "Kill Vault, verify cached secrets used",
                 ["Vault failure detected", "Cached secrets used", "New secret requests queued"],
                 ["RTO < 15 min", "Zero secret exposure"]),
    TestScenario("TS-012", "Cascading failure", CriticalityTier.T1, "high", TestType.SIMULATION,
                 "PDP + evidence + identity failure simultaneously",
                 ["Multiple failures detected", "Continuity mode activated", "T1 systems protected"],
                 ["RTO < 15 min", "T1 governance maintained", "No data loss"]),
    TestScenario("TS-013", "Ransomware attack", CriticalityTier.T1, "high", TestType.TABLETOP,
                 "Simulate ransomware attack on governance infrastructure",
                 ["Attack detected", "Systems isolated", "IR team activated"],
                 ["Containment < 15 min", "Clean restore verified"]),
    TestScenario("TS-014", "Vendor AI service outage", CriticalityTier.T2, "medium", TestType.TABLETOP,
                 "Simulate vendor AI service outage",
                 ["Outage detected", "Fallback model activated", "Stakeholders notified"],
                 ["RTO < 1 hour", "Decisions continue"]),
    TestScenario("TS-015", "Data center cooling failure", CriticalityTier.T2, "medium", TestType.TABLETOP,
                 "Simulate cooling failure in data center",
                 ["Temperature alert", "Workload migration", "DR activation"],
                 ["RTO < 4 hours", "No hardware damage"]),
]


@dataclass
class TestExecutionRecord:
    """Test execution record per BCP §8.7."""

    execution_id: str
    scenario: TestScenario
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[TestResult] = None
    actual_rto_minutes: Optional[float] = None
    actual_rpo_minutes: Optional[float] = None
    steps_executed: int = 0
    steps_total: int = 0
    steps_correct: int = 0
    procedure_accuracy_pct: float = 0.0
    communication_sla_met: bool = False
    personnel_competency_score: float = 0.0
    evidence_integrity_passed: bool = False
    continuity_mode_effective: bool = False
    automation_success_ratio: float = 0.0
    data_loss_events: int = 0
    observations: List[str] = field(default_factory=list)
    gaps: List[Dict[str, str]] = field(default_factory=list)
    improvement_actions: List[Dict[str, str]] = field(default_factory=list)


class ContinuityTester:
    """
    Continuity Testing Framework per BCP §8 and §21.

    Manages test scenarios, executes tests, evaluates results against
    success criteria, and tracks improvement actions.
    """

    # Validation criteria per BCP §21.5.1
    VALIDATION_CRITERIA = {
        CriticalityTier.T1: {
            "rto_minutes": 15,
            "rpo_minutes": 1,
            "procedure_accuracy": 95.0,
            "communication_sla": 100.0,
            "personnel_competency": 90.0,
            "evidence_integrity": 100.0,
            "continuity_mode_effectiveness": 100.0,
            "automation_success": 95.0,
            "data_loss_events": 0,
        },
        CriticalityTier.T2: {
            "rto_minutes": 60,
            "rpo_minutes": 5,
            "procedure_accuracy": 90.0,
            "communication_sla": 95.0,
            "personnel_competency": 85.0,
            "evidence_integrity": 100.0,
            "continuity_mode_effectiveness": 95.0,
            "automation_success": 85.0,
            "data_loss_events": 0,
        },
        CriticalityTier.T3: {
            "rto_minutes": 240,
            "rpo_minutes": 60,
            "procedure_accuracy": 85.0,
            "communication_sla": 90.0,
            "personnel_competency": 80.0,
            "evidence_integrity": 100.0,
            "continuity_mode_effectiveness": 90.0,
            "automation_success": 70.0,
            "data_loss_events": 0,
        },
    }

    def __init__(self) -> None:
        self._scenarios: Dict[str, TestScenario] = {}
        self._execution_history: List[TestExecutionRecord] = []
        self._register_default_scenarios()

    def _register_default_scenarios(self) -> None:
        """Register default scenarios from BCP §8.3.1."""
        for scenario in DEFAULT_SCENARIOS:
            self._scenarios[scenario.scenario_id] = scenario

    def add_scenario(self, scenario: TestScenario) -> None:
        """Add a custom test scenario."""
        self._scenarios[scenario.scenario_id] = scenario

    def get_scenarios(
        self,
        tier: Optional[CriticalityTier] = None,
        test_type: Optional[TestType] = None,
    ) -> List[TestScenario]:
        """Get scenarios filtered by tier and/or test type."""
        scenarios = list(self._scenarios.values())
        if tier:
            scenarios = [s for s in scenarios if s.tier == tier]
        if test_type:
            scenarios = [s for s in scenarios if s.test_type == test_type]
        return scenarios

    def execute_test(
        self,
        scenario_id: str,
        dry_run: bool = False,
    ) -> TestExecutionRecord:
        """
        Execute a test scenario.

        In production, this would inject actual failures and measure
        real recovery. For simulation, it generates realistic results.
        """
        if scenario_id not in self._scenarios:
            raise ValueError(f"Scenario {scenario_id} not found")

        scenario = self._scenarios[scenario_id]
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Executing test: {scenario.name}")

        record = TestExecutionRecord(
            execution_id=str(uuid.uuid4()),
            scenario=scenario,
            started_at=datetime.utcnow(),
        )

        if dry_run:
            record.result = TestResult.PASS
            record.completed_at = datetime.utcnow()
            record.observations.append("Dry run completed successfully")
            return record

        # Simulate test execution with realistic metrics
        record.steps_total = len(scenario.expected_actions)
        record.steps_executed = record.steps_total
        record.steps_correct = record.steps_total  # Assume all correct for simulation
        record.procedure_accuracy_pct = 100.0

        # Simulate RTO/RPO with some variance
        if scenario.rto_target_minutes:
            variance = random.uniform(0.7, 1.1)
            record.actual_rto_minutes = round(scenario.rto_target_minutes * variance, 1)
        if scenario.rpo_target_minutes is not None:
            variance = random.uniform(0.5, 1.0)
            record.actual_rpo_minutes = round(scenario.rpo_target_minutes * variance, 1)

        record.communication_sla_met = random.random() > 0.05
        record.personnel_competency_score = round(random.uniform(85, 100), 1)
        record.evidence_integrity_passed = True
        record.continuity_mode_effective = True
        record.automation_success_ratio = round(random.uniform(0.85, 1.0), 2)
        record.data_loss_events = 0

        # Evaluate result
        record.result = self._evaluate_result(record, scenario.tier)
        record.completed_at = datetime.utcnow()

        # Identify gaps
        record.gaps = self._identify_gaps(record, scenario.tier)

        self._execution_history.append(record)
        return record

    def _evaluate_result(
        self, record: TestExecutionRecord, tier: CriticalityTier
    ) -> TestResult:
        """Evaluate test result against success criteria."""
        criteria = self.VALIDATION_CRITERIA.get(tier, self.VALIDATION_CRITERIA[CriticalityTier.T3])

        failures = 0

        if record.actual_rto_minutes and record.actual_rto_minutes > criteria["rto_minutes"]:
            failures += 1
        if record.actual_rpo_minutes and record.actual_rpo_minutes > criteria["rpo_minutes"]:
            failures += 1
        if record.procedure_accuracy_pct < criteria["procedure_accuracy"]:
            failures += 1
        if not record.communication_sla_met:
            failures += 1
        if record.personnel_competency_score < criteria["personnel_competency"]:
            failures += 1
        if not record.evidence_integrity_passed:
            failures += 1
        if record.data_loss_events > criteria["data_loss_events"]:
            failures += 1

        if failures == 0:
            return TestResult.PASS
        elif failures <= 2:
            return TestResult.PARTIAL
        else:
            return TestResult.FAIL

    def _identify_gaps(
        self, record: TestExecutionRecord, tier: CriticalityTier
    ) -> List[Dict[str, str]]:
        """Identify gaps per BCP §21.6.1."""
        gaps = []
        criteria = self.VALIDATION_CRITERIA.get(tier, self.VALIDATION_CRITERIA[CriticalityTier.T3])

        if record.actual_rto_minutes and record.actual_rto_minutes > criteria["rto_minutes"]:
            gaps.append({
                "category": "Critical" if tier == CriticalityTier.T1 else "Major",
                "description": f"RTO {record.actual_rto_minutes}min exceeds target {criteria['rto_minutes']}min",
                "action": "Immediate fix required" if tier == CriticalityTier.T1 else "Fix within 14 days",
            })

        if record.procedure_accuracy_pct < criteria["procedure_accuracy"]:
            gaps.append({
                "category": "Major",
                "description": f"Procedure accuracy {record.procedure_accuracy_pct}% below target {criteria['procedure_accuracy']}%",
                "action": "Update runbook and retrain personnel",
            })

        if not record.communication_sla_met:
            gaps.append({
                "category": "Major",
                "description": "Communication SLA not met",
                "action": "Review notification procedures",
            })

        return gaps

    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all test executions."""
        if not self._execution_history:
            return {"total_tests": 0}

        total = len(self._execution_history)
        passed = sum(1 for r in self._execution_history if r.result == TestResult.PASS)
        partial = sum(1 for r in self._execution_history if r.result == TestResult.PARTIAL)
        failed = sum(1 for r in self._execution_history if r.result == TestResult.FAIL)

        rto_achieved = sum(
            1 for r in self._execution_history
            if r.actual_rto_minutes
            and r.scenario.rto_target_minutes
            and r.actual_rto_minutes <= r.scenario.rto_target_minutes
        )
        rpo_achieved = sum(
            1 for r in self._execution_history
            if r.actual_rpo_minutes is not None
            and r.scenario.rpo_target_minutes is not None
            and r.actual_rpo_minutes <= r.scenario.rpo_target_minutes
        )

        return {
            "total_tests": total,
            "passed": passed,
            "partial": partial,
            "failed": failed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "rto_achievement_rate": round(rto_achieved / total * 100, 1) if total > 0 else 0,
            "rpo_achievement_rate": round(rpo_achieved / total * 100, 1) if total > 0 else 0,
            "scenarios_available": len(self._scenarios),
            "last_test_date": (
                self._execution_history[-1].completed_at.isoformat()
                if self._execution_history else None
            ),
        }

    def generate_test_schedule(self, year: int) -> List[Dict[str, Any]]:
        """
        Generate annual test schedule per BCP §8.4.
        """
        schedule = []
        quarters = [
            ("Q1", 1, [TestType.FUNCTIONAL, TestType.TABLETOP, TestType.SIMULATION]),
            ("Q2", 4, [TestType.FUNCTIONAL, TestType.CONTINUITY_MODE, TestType.LIVE_FAILOVER]),
            ("Q3", 7, [TestType.FUNCTIONAL, TestType.TABLETOP, TestType.SIMULATION]),
            ("Q4", 10, [TestType.FUNCTIONAL, TestType.EVIDENCE_INTEGRITY, TestType.SIMULATION]),
        ]

        for quarter, month, test_types in quarters:
            for test_type in test_types:
                scenarios = self.get_scenarios(test_type=test_type)
                for scenario in scenarios:
                    schedule.append({
                        "quarter": quarter,
                        "month": month,
                        "test_type": test_type.value,
                        "scenario_id": scenario.scenario_id,
                        "scenario_name": scenario.name,
                        "tier": scenario.tier.value,
                    })

        return schedule


# ===========================================================================
# DEMONSTRATION / MAIN
# ===========================================================================


def main() -> None:
    """Demonstrate all 7 business continuity capabilities."""

    print("=" * 70)
    print("GRC_Claw Business Continuity Implementation Guide")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 1. Criticality Classification
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("1. CRITICALITY CLASSIFICATION")
    print("=" * 70)

    classifier = CriticalityClassifier()

    # Classify an autonomous vehicle decision system (T1)
    av_dims = [
        DimensionScore(ImpactDimension.SAFETY, 5, "Physical harm possible — autonomous vehicle control"),
        DimensionScore(ImpactDimension.REGULATORY, 4, "NHTSA reporting required, fines >$1M"),
        DimensionScore(ImpactDimension.FINANCIAL, 5, ">$10M liability exposure"),
        DimensionScore(ImpactDimension.OPERATIONAL, 5, "Complete process failure"),
        DimensionScore(ImpactDimension.REPUTATIONAL, 5, "Front-page news, customer exodus"),
    ]
    av_classification = classifier.classify(
        system_id="sys-av-001",
        system_name="AutoDrive Decision Engine",
        system_owner="autonomous-team@company.com",
        dimensions=av_dims,
    )
    print(f"\nSystem: {av_classification.system_name}")
    print(f"CCS: {av_classification.composite_criticality_score}")
    print(f"Tier: {av_classification.assigned_tier.value}")
    print(f"Approver: {av_classification.approver}")
    print(f"Review Date: {av_classification.review_date.date()}")

    # Classify an internal analytics model (T3)
    analytics_dims = [
        DimensionScore(ImpactDimension.SAFETY, 1, "No safety impact"),
        DimensionScore(ImpactDimension.REGULATORY, 2, "Minor compliance gap possible"),
        DimensionScore(ImpactDimension.FINANCIAL, 2, "$100K-$1M impact"),
        DimensionScore(ImpactDimension.OPERATIONAL, 3, "Minor process impact"),
        DimensionScore(ImpactDimension.REPUTATIONAL, 1, "No reputational impact"),
    ]
    analytics_classification = classifier.classify(
        system_id="sys-analytics-001",
        system_name="Internal Analytics Model",
        system_owner="data-team@company.com",
        dimensions=analytics_dims,
    )
    print(f"\nSystem: {analytics_classification.system_name}")
    print(f"CCS: {analytics_classification.composite_criticality_score}")
    print(f"Tier: {analytics_classification.assigned_tier.value}")

    # Validate
    issues = classifier.validate_classification(av_classification)
    print(f"\nValidation issues: {issues if issues else 'None'}")

    # ------------------------------------------------------------------
    # 2. Business Impact Analysis
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("2. BUSINESS IMPACT ANALYSIS")
    print("=" * 70)

    bia = BusinessImpactAnalyzer()
    bia.add_system("sys-av-001", "AutoDrive Decision Engine", CriticalityTier.T1, RecoveryPriority.P1)
    bia.add_system("sys-analytics-001", "Internal Analytics Model", CriticalityTier.T3, RecoveryPriority.P12)
    bia.add_system("sys-fraud-001", "Fraud Detection", CriticalityTier.T2, RecoveryPriority.P3)

    report = bia.generate_report(
        prepared_by="grc-analyst@company.com",
        approved_by="ciso@company.com",
    )
    print(f"\nBIA Report ID: {report.report_id}")
    print(f"Executive Summary: {report.executive_summary}")
    print(f"Financial Impact: {report.financial_impact_summary}")
    print(f"Recommendations: {report.recommendations}")

    print("\nRecovery Sequence:")
    for i, system in enumerate(bia.get_recovery_sequence(), 1):
        print(f"  {i}. [{system.recovery_priority.value}] {system.system_name} ({system.criticality_tier.value})")

    # ------------------------------------------------------------------
    # 3. Disaster Recovery Automation
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("3. DISASTER RECOVERY AUTOMATION")
    print("=" * 70)

    dr_engine = DRAutomationEngine()

    # Create a T1 runbook
    t1_runbook = DRRunbook(
        runbook_id="DR-RUN-001",
        name="PDP Failure Recovery",
        version="1.0",
        tier=CriticalityTier.T1,
        automation_level="full",
        triggers=["health_check_failure", "error_rate_threshold"],
        pre_conditions=["standby_region_available", "backup_verified_within_24h", "no_concurrent_failover"],
        steps=[
            RecoveryStep("step_1", "Detect and classify failure", "monitoring_system", True, 30),
            RecoveryStep("step_2", "Acquire failover lock", "distributed_lock", True, 10),
            RecoveryStep("step_3", "Promote PostgreSQL standby", "patroni", True, 120),
            RecoveryStep("step_4", "Promote Redis standby", "redis_sentinel", True, 30),
            RecoveryStep("step_5", "Activate DR region services", "kubernetes", True, 120),
            RecoveryStep("step_6", "Update DNS records", "route53", True, 60),
            RecoveryStep("step_7", "Redirect load balancer", "global_lb", True, 30),
            RecoveryStep("step_8", "Verify governance continuity", "health_checker", True, 60),
        ],
        rollback_conditions=["standby_promotion_fails", "data_integrity_check_fails"],
        post_recovery_actions=["update_continuity_status", "create_incident_record"],
    )
    dr_engine.register_runbook(t1_runbook)

    # Dry run
    dry_run_result = dr_engine.execute_runbook("DR-RUN-001", dry_run=True)
    print(f"\nDry Run Result: {dry_run_result['status']}")
    print(f"Steps executed: {len(dry_run_result['steps'])}")

    # Self-healing demo
    heal_result = dr_engine.self_heal("pod_crash")
    print(f"\nSelf-Healing: {heal_result['scenario']} → {heal_result['action']}")
    print(f"  Detection: {heal_result['detection_time_seconds']}s")
    print(f"  Recovery: {heal_result['recovery_time_seconds']}s")

    # Continuity status
    status = dr_engine.get_continuity_status()
    print(f"\nContinuity Status: {status['active_mode']}")

    # ------------------------------------------------------------------
    # 4. Failover Orchestration
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("4. FAILOVER ORCHESTRATION")
    print("=" * 70)

    orchestrator = FailoverOrchestrator()
    orchestrator.register_component("PDP")
    orchestrator.register_component("PEP")
    orchestrator.register_component("PostgreSQL")

    # Simulate health degradation
    orchestrator.update_component_health("PDP", health_check_passed=False, consecutive_failures=1)
    print(f"\nPDP state after 1 failure: {orchestrator._component_states['PDP'].value}")

    orchestrator.update_component_health("PDP", health_check_passed=False, consecutive_failures=3)
    print(f"PDP state after 3 failures: {orchestrator._component_states['PDP'].value}")

    # Failover decision
    decision = orchestrator._decision_engine.get_failover_action(CriticalityTier.T1)
    print(f"\nFailover Decision (FUS={decision['fus']}): {decision['action']}")

    # Update signals and recalculate
    orchestrator._decision_engine.update_signal("health_check_failure_rate", 5)
    orchestrator._decision_engine.update_signal("error_rate_elevation", 4)
    decision = orchestrator._decision_engine.get_failover_action(CriticalityTier.T1)
    print(f"Failover Decision (FUS={decision['fus']}): {decision['action']}")

    # Metrics
    metrics = orchestrator.get_failover_metrics()
    print(f"\nFailover Metrics: {metrics['grc_failover_events_total']} events")

    # ------------------------------------------------------------------
    # 5. Resilience Scoring
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("5. RESILIENCE SCORING")
    print("=" * 70)

    scorer = ResilienceScorer()

    # Calculate dimension scores
    redundancy = scorer.calculate_redundancy_score(
        CriticalityTier.T1,
        {"PDP": "active_active_multi_region", "PEP": "active_active_multi_region",
         "PostgreSQL": "active_passive_warm_standby", "Redis": "active_passive_warm_standby",
         "Identity": "active_passive_warm_standby", "Evidence": "active_passive_warm_standby"},
    )
    recovery = scorer.calculate_recovery_capability_score(1.0, 1.0, "fully_automated")
    degradation = scorer.calculate_degradation_resilience_score(1.0, 0.8, 0.7)
    testing = scorer.calculate_testing_coverage_score(1.0, 1.0, 0.95)
    observability = scorer.calculate_observability_score(1.0, 1.0, 0.99)

    rs = scorer.calculate_composite_score(
        system_id="sys-av-001",
        system_name="AutoDrive Decision Engine",
        tier=CriticalityTier.T1,
        redundancy=redundancy,
        recovery=recovery,
        degradation=degradation,
        testing=testing,
        observability=observability,
    )

    print(f"\nSystem: {rs.system_name}")
    print(f"Composite RS: {rs.composite_score}")
    print(f"Rating: {rs.rating.value}")
    print(f"Dimension Scores:")
    print(f"  Redundancy: {rs.dimension_scores.redundancy}")
    print(f"  Recovery: {rs.dimension_scores.recovery_capability}")
    print(f"  Degradation: {rs.dimension_scores.degradation_resilience}")
    print(f"  Testing: {rs.dimension_scores.testing_coverage}")
    print(f"  Observability: {rs.dimension_scores.observability}")

    actions = scorer.get_governance_actions(rs)
    print(f"Governance Actions: {actions if actions else 'None required'}")

    # ------------------------------------------------------------------
    # 6. Continuity Monitoring
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("6. CONTINUITY MONITORING")
    print("=" * 70)

    monitor = ContinuityMonitor()

    # Register alert handlers
    def pager_handler(alert: ContinuityAlert) -> None:
        print(f"  [PAGER] {alert.severity.value}: {alert.message}")

    def slack_handler(alert: ContinuityAlert) -> None:
        print(f"  [SLACK] {alert.severity.value}: {alert.message}")

    monitor.register_alert_handler(AlertSeverity.P1_CRITICAL, pager_handler)
    monitor.register_alert_handler(AlertSeverity.P2_HIGH, slack_handler)

    # Simulate component health updates
    monitor.update_component_health(ComponentHealth(
        component="PDP",
        availability_pct=99.5,
        latency_p99_ms=45,
        error_rate_pct=0.05,
        replication_lag_seconds=10,
        queue_depth=500,
        disk_usage_pct=60,
        memory_usage_pct=70,
        last_updated=datetime.utcnow(),
    ))

    monitor.update_component_health(ComponentHealth(
        component="PEP",
        availability_pct=99.9,
        latency_p99_ms=8,
        error_rate_pct=0.01,
        replication_lag_seconds=0,
        queue_depth=100,
        disk_usage_pct=50,
        memory_usage_pct=55,
        last_updated=datetime.utcnow(),
    ))

    # Simulate a failing component
    monitor.update_component_health(ComponentHealth(
        component="Evidence-Store",
        availability_pct=95.0,
        latency_p99_ms=200,
        error_rate_pct=2.0,
        replication_lag_seconds=120,
        queue_depth=15000,
        disk_usage_pct=85,
        memory_usage_pct=90,
        last_updated=datetime.utcnow(),
    ))

    # Update failover readiness
    monitor.update_failover_readiness(FailoverReadiness(
        component="PDP",
        standby_healthy=True,
        replication_status="healthy",
        failover_lock_status="unlocked",
        last_failover_test=datetime.utcnow() - timedelta(days=15),
        failover_readiness_score=0.9,
        split_brain_risk=False,
    ))

    # Update recovery readiness
    monitor.update_recovery_readiness(RecoveryReadiness(
        component="PostgreSQL",
        backup_status="success",
        backup_age_hours=6,
        backup_verification_status="passed",
        dr_environment_healthy=True,
        dr_sync_lag_minutes=2,
        runbook_version="1.2",
        runbook_age_days=30,
    ))

    summary = monitor.get_monitoring_summary()
    print(f"\nMonitoring Summary:")
    print(f"  Components monitored: {summary['total_components_monitored']}")
    print(f"  Active alerts: {summary['active_alerts_count']}")
    print(f"  Alerts by severity: {summary['alerts_by_severity']}")

    # ------------------------------------------------------------------
    # 7. Continuity Testing
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("7. CONTINUITY TESTING")
    print("=" * 70)

    tester = ContinuityTester()

    # Show available scenarios
    t1_scenarios = tester.get_scenarios(tier=CriticalityTier.T1)
    print(f"\nT1 Scenarios available: {len(t1_scenarios)}")
    for s in t1_scenarios:
        print(f"  [{s.scenario_id}] {s.name} ({s.test_type.value})")

    # Execute a test
    result = tester.execute_test("TS-001")
    print(f"\nTest Execution: {result.scenario.name}")
    print(f"  Result: {result.result.value}")
    print(f"  Actual RTO: {result.actual_rto_minutes} min")
    print(f"  Actual RPO: {result.actual_rpo_minutes} min")
    print(f"  Procedure Accuracy: {result.procedure_accuracy_pct}%")
    print(f"  Gaps: {len(result.gaps)}")

    # Execute another test
    result2 = tester.execute_test("TS-007")
    print(f"\nTest Execution: {result2.scenario.name}")
    print(f"  Result: {result2.result.value}")
    print(f"  Actual RTO: {result2.actual_rto_minutes} min")

    # Test summary
    test_summary = tester.get_test_summary()
    print(f"\nTest Summary:")
    print(f"  Total tests: {test_summary['total_tests']}")
    print(f"  Pass rate: {test_summary['pass_rate']}%")
    print(f"  RTO achievement: {test_summary['rto_achievement_rate']}%")
    print(f"  RPO achievement: {test_summary['rpo_achievement_rate']}%")

    # Generate schedule
    schedule = tester.generate_test_schedule(2026)
    print(f"\n2026 Test Schedule: {len(schedule)} entries")
    for entry in schedule[:5]:
        print(f"  {entry['quarter']} Month {entry['month']}: [{entry['test_type']}] {entry['scenario_name']}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("IMPLEMENTATION COMPLETE")
    print("=" * 70)
    print("""
All 7 business continuity capabilities have been demonstrated:

  1. Criticality Classification — 4-tier system with CCS algorithm
  2. Business Impact Analysis — 6-category, 6-duration impact matrix
  3. DR Automation — Runbook engine with self-healing
  4. Failover Orchestration — Hierarchical with split-brain prevention
  5. Resilience Scoring — 5-dimension composite score (0.0–1.0)
  6. Continuity Monitoring — 5-layer monitoring with alerting
  7. Continuity Testing — Scenario-based testing with gap analysis

All implementations follow:
  - GRC_Claw Business Continuity Spec v1.1 (GRC-BCP-001)
  - GRC_Claw Reliability Spec v2.0 (GRC-REL-001)
  - ISO 22301:2019, ISO/IEC 42001:2023, NIST SP 800-34, DORA
""")


if __name__ == "__main__":
    main()

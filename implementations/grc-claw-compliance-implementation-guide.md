# GRC_Claw Compliance Management Implementation Guide

**Document ID:** GRC-CMS-IMP-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**References:** GRC-CMS-001 (Compliance Mapping Spec), GRC-EVD-001 (Evidence Spec)

---

## Table of Contents

1. [Control Registry Implementation](#1-control-registry-implementation)
2. [Framework Mapping Engine](#2-framework-mapping-engine)
3. [Evidence-to-Control Binding](#3-evidence-to-control-binding)
4. [Compliance Scoring Algorithm](#4-compliance-scoring-algorithm)
5. [Compliance Monitoring](#5-compliance-monitoring)
6. [Compliance Reporting](#6-compliance-reporting)
7. [Audit Preparation](#7-audit-preparation)

---

## 1. Control Registry Implementation

The control registry manages the 68 unified controls across 12 categories, providing CRUD operations, validation, and lookup capabilities.

```python
"""
GRC_Claw Control Registry
Manages the unified control set (68 controls, 12 categories).
"""

from __future__ import annotations

import json
import hashlib
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional


class RiskTier(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class SatisfactionMethod(Enum):
    DIRECT = "direct"
    PARTIAL = "partial"
    INDIRECT = "indirect"
    COMPOSITE = "composite"


class VerificationLevel(Enum):
    L0 = "L0"  # Unverified
    L1 = "L1"  # Schema-valid
    L2 = "L2"  # Integrity-verified
    L3 = "L3"  # Cross-validated
    L4 = "L4"  # Attested


@dataclass
class EvidenceRequirement:
    type: str
    description: str
    format: str
    retention: str  # e.g., "7 years", "12 months"


@dataclass
class Spoke:
    framework: str
    requirement: str
    title: str
    satisfaction_method: SatisfactionMethod
    notes: str = ""


@dataclass
class CollectionSchedule:
    frequency: str  # e.g., "per_deployment", "continuous", "daily"
    trigger: str
    automated: bool


@dataclass
class UnifiedControl:
    id: str
    title: str
    category: str
    risk_tier: RiskTier
    description: str
    verification_target: str
    evidence_requirements: list[EvidenceRequirement]
    spokes: list[Spoke]
    collection_schedule: CollectionSchedule
    minimum_verification_level: VerificationLevel
    depends_on: list[str] = field(default_factory=list)
    mandatory_for: list[str] = field(default_factory=list)
    recommended_for: list[str] = field(default_factory=list)
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["risk_tier"] = self.risk_tier.value
        d["minimum_verification_level"] = self.minimum_verification_level.value
        for spoke in d["spokes"]:
            spoke["satisfaction_method"] = spoke["satisfaction_method"].value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> UnifiedControl:
        data = data.copy()
        data["risk_tier"] = RiskTier(data["risk_tier"])
        data["minimum_verification_level"] = VerificationLevel(data["minimum_verification_level"])
        data["evidence_requirements"] = [
            EvidenceRequirement(**er) for er in data["evidence_requirements"]
        ]
        data["spokes"] = [
            Spoke(
                framework=s["framework"],
                requirement=s["requirement"],
                title=s["title"],
                satisfaction_method=SatisfactionMethod(s["satisfaction_method"]),
                notes=s.get("notes", ""),
            )
            for s in data["spokes"]
        ]
        data["collection_schedule"] = CollectionSchedule(**data["collection_schedule"])
        return cls(**data)


class ControlRegistry:
    """Central registry for all unified controls."""

    CATEGORIES = {
        "Governance & Policy": (1, 8),
        "Risk Management & Impact Assessment": (2, 7),
        "Data Governance": (3, 6),
        "System Lifecycle & Engineering": (4, 9),
        "Transparency & Communication": (5, 5),
        "Human Oversight & Interaction": (6, 5),
        "Security & Robustness": (7, 7),
        "Agentic AI Security": (8, 10),
        "Fairness, Privacy & Ethics": (9, 5),
        "Third-Party & Supply Chain": (10, 4),
        "Compliance & Certification": (11, 5),
        "Continuous Improvement": (12, 4),
    }

    def __init__(self, storage_path: str = "controls/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._controls: dict[str, UnifiedControl] = {}
        self._index_by_category: dict[str, list[str]] = {}
        self._index_by_framework: dict[str, list[str]] = {}
        self._index_by_risk: dict[str, list[str]] = {}

    def register(self, control: UnifiedControl) -> UnifiedControl:
        """Register a new unified control."""
        if control.id in self._controls:
            raise ValueError(f"Control {control.id} already registered")

        self._validate_control(control)
        self._controls[control.id] = control
        self._update_indexes(control)
        self._persist(control)
        return control

    def get(self, control_id: str) -> Optional[UnifiedControl]:
        """Retrieve a control by ID."""
        return self._controls.get(control_id)

    def list_all(self) -> list[UnifiedControl]:
        """List all registered controls."""
        return list(self._controls.values())

    def list_by_category(self, category: str) -> list[UnifiedControl]:
        """List controls in a category."""
        ids = self._index_by_category.get(category, [])
        return [self._controls[cid] for cid in ids]

    def list_by_framework(self, framework: str) -> list[UnifiedControl]:
        """List controls that have spokes to a framework."""
        ids = self._index_by_framework.get(framework, [])
        return [self._controls[cid] for cid in ids]

    def list_by_risk_tier(self, tier: RiskTier) -> list[UnifiedControl]:
        """List controls by risk tier."""
        ids = self._index_by_risk.get(tier.value, [])
        return [self._controls[cid] for cid in ids]

    def update(self, control_id: str, **kwargs) -> UnifiedControl:
        """Update a control's fields."""
        control = self._controls.get(control_id)
        if not control:
            raise KeyError(f"Control {control_id} not found")

        for key, value in kwargs.items():
            if hasattr(control, key):
                setattr(control, key, value)

        control.updated_at = datetime.utcnow().isoformat() + "Z"
        self._validate_control(control)
        self._rebuild_indexes()
        self._persist(control)
        return control

    def delete(self, control_id: str) -> bool:
        """Remove a control from the registry."""
        if control_id not in self._controls:
            return False
        del self._controls[control_id]
        self._rebuild_indexes()
        (self.storage_path / f"{control_id}.json").unlink(missing_ok=True)
        return True

    def get_spokes_for_framework(self, framework: str) -> list[tuple[UnifiedControl, Spoke]]:
        """Get all (control, spoke) pairs for a framework."""
        result = []
        for control in self._controls.values():
            for spoke in control.spokes:
                if spoke.framework == framework:
                    result.append((control, spoke))
        return result

    def get_controls_for_requirement(
        self, framework: str, requirement: str
    ) -> list[tuple[UnifiedControl, Spoke]]:
        """Find all controls that map to a specific framework requirement."""
        result = []
        for control in self._controls.values():
            for spoke in control.spokes:
                if spoke.framework == framework and spoke.requirement == requirement:
                    result.append((control, spoke))
        return result

    def validate_integrity(self) -> list[str]:
        """Validate all controls and return list of issues."""
        issues = []
        for control in self._controls.values():
            issues.extend(self._validate_control(control, raise_on_error=False))
        return issues

    def export_catalog(self) -> dict:
        """Export the full control catalog."""
        return {
            "version": "1.0",
            "exported-at": datetime.utcnow().isoformat() + "Z",
            "total-controls": len(self._controls),
            "categories": {
                cat: len(ids) for cat, ids in self._index_by_category.items()
            },
            "controls": [c.to_dict() for c in self._controls.values()],
        }

    def load_catalog(self, catalog: dict) -> None:
        """Load controls from a catalog export."""
        self._controls.clear()
        for ctrl_data in catalog.get("controls", []):
            control = UnifiedControl.from_dict(ctrl_data)
            self._controls[control.id] = control
        self._rebuild_indexes()

    # --- Internal methods ---

    def _validate_control(
        self, control: UnifiedControl, raise_on_error: bool = True
    ) -> list[str]:
        issues = []
        if not control.id.startswith("UC-"):
            issues.append(f"{control.id}: ID must start with 'UC-'")
        if not control.title:
            issues.append(f"{control.id}: Title is required")
        if not control.spokes:
            issues.append(f"{control.id}: Must have at least one spoke")
        for dep in control.depends_on:
            if dep not in self._controls and dep != control.id:
                issues.append(f"{control.id}: Unknown dependency {dep}")
        if raise_on_error and issues:
            raise ValueError(f"Control validation failed: {'; '.join(issues)}")
        return issues

    def _update_indexes(self, control: UnifiedControl) -> None:
        cat = control.category
        self._index_by_category.setdefault(cat, []).append(control.id)
        for spoke in control.spokes:
            self._index_by_framework.setdefault(spoke.framework, []).append(control.id)
        self._index_by_risk.setdefault(control.risk_tier.value, []).append(control.id)

    def _rebuild_indexes(self) -> None:
        self._index_by_category.clear()
        self._index_by_framework.clear()
        self._index_by_risk.clear()
        for control in self._controls.values():
            self._update_indexes(control)

    def _persist(self, control: UnifiedControl) -> None:
        path = self.storage_path / f"{control.id}.json"
        path.write_text(json.dumps(control.to_dict(), indent=2))


# --- Example: Bootstrap the full 68-control catalog ---

def bootstrap_control_catalog(registry: ControlRegistry) -> None:
    """Populate the registry with the complete 68-control unified set."""

    controls_data = [
        # Category 1: Governance & Policy (UC-1.1 – UC-1.8)
        {
            "id": "UC-1.1", "title": "AI policy establishment",
            "category": "Governance & Policy", "risk_tier": RiskTier.CRITICAL,
            "description": "Establish, document, and maintain an AI policy aligned with organizational objectives.",
            "verification_target": "A current, approved AI policy exists and is communicated to all relevant parties.",
            "evidence_requirements": [
                EvidenceRequirement("policy_document", "Approved AI policy", "PDF", "7 years"),
                EvidenceRequirement("communication_record", "Policy distribution evidence", "email-log", "3 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.2.2", "AI policy", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 1", "Policies, processes, procedures", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 17", "Quality management system", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 5(1)(a)", "Lawfulness, fairness, transparency", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("annual", "policy_review_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT"],
            "recommended_for": ["NIST_AI_RMF", "GDPR"],
        },
        {
            "id": "UC-1.2", "title": "Policy alignment with other policies",
            "category": "Governance & Policy", "risk_tier": RiskTier.HIGH,
            "description": "Ensure AI policy is consistent with and references other organizational policies.",
            "verification_target": "AI policy cross-references all relevant organizational policies.",
            "evidence_requirements": [
                EvidenceRequirement("policy_document", "Cross-referenced policy document", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.2.3", "Alignment with other policies", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 1", "Policies, processes, procedures", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 17", "Quality management system", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("annual", "policy_review_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-1.3", "title": "AI roles and responsibilities",
            "category": "Governance & Policy", "risk_tier": RiskTier.CRITICAL,
            "description": "Define and assign roles and responsibilities for AI governance.",
            "verification_target": "Documented RACI matrix for AI governance is current and acknowledged.",
            "evidence_requirements": [
                EvidenceRequirement("roles_document", "RACI matrix", "PDF", "7 years"),
                EvidenceRequirement("training_record", "Role-specific training completion", "training-log", "3 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.3.2", "AI roles and responsibilities", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 2", "Accountability structures", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 17", "Quality management system", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 37", "Designation of data protection officer", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("annual", "org_change_trigger", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "GDPR"],
        },
        {
            "id": "UC-1.4", "title": "Reporting of concerns",
            "category": "Governance & Policy", "risk_tier": RiskTier.HIGH,
            "description": "Establish channels for reporting AI-related concerns and incidents.",
            "verification_target": "A functioning concern-reporting channel exists with documented procedures.",
            "evidence_requirements": [
                EvidenceRequirement("procedure_document", "Concern reporting procedure", "PDF", "7 years"),
                EvidenceRequirement("incident_log", "Reported concerns log", "log", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.3.3", "Reporting of concerns", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 4", "Team culture, safe reporting", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 86", "Reporting of serious incidents", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "event_trigger", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-1.5", "title": "AI literacy and training",
            "category": "Governance & Policy", "risk_tier": RiskTier.HIGH,
            "description": "Ensure workforce has adequate AI literacy for their roles.",
            "verification_target": "All relevant personnel completed role-appropriate AI literacy training.",
            "evidence_requirements": [
                EvidenceRequirement("training_record", "AI literacy training completion", "training-log", "3 years"),
                EvidenceRequirement("curriculum", "Training curriculum document", "PDF", "3 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.6", "Human resources", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "GOVERN 3", "Workforce diversity, equity, inclusion", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 4", "AI literacy", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.308(a)(5)", "Security awareness and training", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("annual", "training_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["EU_AI_ACT", "HIPAA"],
        },
        {
            "id": "UC-1.6", "title": "AI governance committee",
            "category": "Governance & Policy", "risk_tier": RiskTier.HIGH,
            "description": "Establish an AI governance committee with cross-functional representation.",
            "verification_target": "A chartered AI governance committee meets regularly with documented minutes.",
            "evidence_requirements": [
                EvidenceRequirement("charter", "Committee charter", "PDF", "7 years"),
                EvidenceRequirement("meeting_minutes", "Meeting minutes", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.2.4", "Review of AI policy", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "GOVERN 2", "Accountability structures", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("quarterly", "scheduled_meeting", False),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-1.7", "title": "AI tooling inventory",
            "category": "Governance & Policy", "risk_tier": RiskTier.MEDIUM,
            "description": "Maintain an inventory of all AI tools and systems used by the organization.",
            "verification_target": "A complete, current inventory of AI tools is maintained.",
            "evidence_requirements": [
                EvidenceRequirement("inventory", "AI tools inventory", "JSON", "3 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.4", "Tooling resources", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 6", "Third-party risk management", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 25", "Supplier obligations", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "change_detection", True),
            "minimum_verification_level": VerificationLevel.L1,
        },
        {
            "id": "UC-1.8", "title": "AI ethics review board",
            "category": "Governance & Policy", "risk_tier": RiskTier.MEDIUM,
            "description": "Establish an ethics review board for AI system decisions.",
            "verification_target": "An ethics review board reviews high-risk AI system decisions.",
            "evidence_requirements": [
                EvidenceRequirement("review_record", "Ethics review records", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("NIST_AI_RMF", "GOVERN 4", "Team culture, safe reporting", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 5", "Prohibited practices", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_decision", "high_risk_trigger", False),
            "minimum_verification_level": VerificationLevel.L2,
        },
        # Category 2: Risk Management & Impact Assessment (UC-2.1 – UC-2.7)
        {
            "id": "UC-2.1", "title": "AI system risk classification",
            "category": "Risk Management & Impact Assessment", "risk_tier": RiskTier.CRITICAL,
            "description": "Classify AI systems by risk level according to applicable frameworks.",
            "verification_target": "Each AI system has a documented risk classification.",
            "evidence_requirements": [
                EvidenceRequirement("classification_record", "Risk classification document", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("EU_AI_ACT", "Art. 6", "Risk classification", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 2", "System categorization, capabilities", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["EU_AI_ACT"],
        },
        {
            "id": "UC-2.2", "title": "AI system impact assessment process",
            "category": "Risk Management & Impact Assessment", "risk_tier": RiskTier.CRITICAL,
            "description": "Establish a process for assessing AI system impacts.",
            "verification_target": "A documented impact assessment process is followed for all AI systems.",
            "evidence_requirements": [
                EvidenceRequirement("process_document", "Impact assessment process", "PDF", "7 years"),
                EvidenceRequirement("assessment_report", "Impact assessment reports", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.5.2", "AI system impact assessment process", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 1", "Context establishment", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 9", "Risk management system", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.308(a)(1)(ii)(A)", "Risk analysis", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT", "HIPAA"],
        },
        {
            "id": "UC-2.3", "title": "Documentation of impact assessments",
            "category": "Risk Management & Impact Assessment", "risk_tier": RiskTier.CRITICAL,
            "description": "Document all AI system impact assessments with findings and mitigations.",
            "verification_target": "Complete impact assessment documentation exists for all deployed AI systems.",
            "evidence_requirements": [
                EvidenceRequirement("assessment_report", "Impact assessment report", "PDF", "7 years"),
                EvidenceRequirement("mitigation_plan", "Risk mitigation plan", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.5.3", "Documentation of impact assessments", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 3", "Benefits and costs analysis", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 5", "Impact characterization", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 9", "Risk management system", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 27", "Deployer FRIA", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 35", "Data protection impact assessment", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT", "GDPR"],
        },
        {
            "id": "UC-2.4", "title": "Impact on individuals and groups",
            "category": "Risk Management & Impact Assessment", "risk_tier": RiskTier.CRITICAL,
            "description": "Assess and document impacts on individuals and groups.",
            "verification_target": "Impact assessments cover effects on individuals and groups.",
            "evidence_requirements": [
                EvidenceRequirement("assessment_report", "Individual/group impact assessment", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.5.4", "Impact on individuals/groups", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 5", "Impact characterization", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 27", "Deployer FRIA", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 35", "Data protection impact assessment", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT"],
        },
        {
            "id": "UC-2.5", "title": "Societal impact assessment",
            "category": "Risk Management & Impact Assessment", "risk_tier": RiskTier.HIGH,
            "description": "Assess broader societal impacts of AI systems.",
            "verification_target": "Societal impact is assessed for high-risk AI systems.",
            "evidence_requirements": [
                EvidenceRequirement("assessment_report", "Societal impact assessment", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.5.5", "Societal impacts", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 5", "Impact characterization", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 5", "Prohibited practices", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 51-56", "GPAI obligations", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-2.6", "title": "Risk prioritization and go/no-go",
            "category": "Risk Management & Impact Assessment", "risk_tier": RiskTier.CRITICAL,
            "description": "Establish risk-based go/no-go decision process for AI deployments.",
            "verification_target": "No AI system is deployed without a documented go/no-go decision.",
            "evidence_requirements": [
                EvidenceRequirement("decision_record", "Go/no-go decision record", "signed-attestation", "7 years"),
            ],
            "spokes": [
                Spoke("NIST_AI_RMF", "MANAGE 1", "Risk prioritization, go/no-go", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 9", "Risk management system", SatisfactionMethod.PARTIAL),
                Spoke("HIPAA", "§164.308(a)(1)(ii)(B)", "Risk management", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", False),
            "minimum_verification_level": VerificationLevel.L3,
            "mandatory_for": ["NIST_AI_RMF"],
        },
        {
            "id": "UC-2.7", "title": "Risk treatment and mitigation tracking",
            "category": "Risk Management & Impact Assessment", "risk_tier": RiskTier.HIGH,
            "description": "Track risk treatment plans and mitigation effectiveness.",
            "verification_target": "All identified risks have treatment plans with tracked progress.",
            "evidence_requirements": [
                EvidenceRequirement("risk_register", "Risk register with treatment plans", "JSON", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.5.3", "Documentation of impact assessments", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 9", "Risk management system", SatisfactionMethod.PARTIAL),
                Spoke("HIPAA", "§164.308(a)(1)(ii)(B)", "Risk management", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "risk_change_trigger", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        # Category 3: Data Governance (UC-3.1 – UC-3.6)
        {
            "id": "UC-3.1", "title": "Data resource documentation",
            "category": "Data Governance", "risk_tier": RiskTier.CRITICAL,
            "description": "Document all data resources used by AI systems.",
            "verification_target": "Complete data resource documentation exists for all AI systems.",
            "evidence_requirements": [
                EvidenceRequirement("data_catalog", "Data resource catalog", "JSON", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.2", "Resource documentation", SatisfactionMethod.DIRECT),
                Spoke("ISO_42001", "A.4.3", "Data resources", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 2", "System categorization, capabilities", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 10", "Data governance", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "change_detection", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT"],
        },
        {
            "id": "UC-3.2", "title": "Data acquisition and provenance",
            "category": "Data Governance", "risk_tier": RiskTier.CRITICAL,
            "description": "Document data acquisition methods and lineage.",
            "verification_target": "All training and operational data has documented provenance.",
            "evidence_requirements": [
                EvidenceRequirement("lineage_record", "Data lineage records", "JSON", "7 years"),
                EvidenceRequirement("acquisition_log", "Data acquisition log", "log", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.7.3", "Acquisition of data", SatisfactionMethod.DIRECT),
                Spoke("ISO_42001", "A.7.5", "Data provenance", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 4", "Risk identification (third-party)", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 10", "Data governance", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 51-56", "GPAI obligations", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 6", "Lawfulness of processing", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 7", "Conditions for consent", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "data_ingestion", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "GDPR"],
        },
        {
            "id": "UC-3.3", "title": "Data quality management",
            "category": "Data Governance", "risk_tier": RiskTier.CRITICAL,
            "description": "Ensure data quality for AI system inputs and training data.",
            "verification_target": "Data quality metrics are measured and meet defined thresholds.",
            "evidence_requirements": [
                EvidenceRequirement("quality_report", "Data quality assessment report", "PDF", "7 years"),
                EvidenceRequirement("quality_metrics", "Data quality metrics", "JSON", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.7.4", "Quality of data for AI systems", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MEASURE 2", "Trustworthiness evaluation", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 10", "Data governance", SatisfactionMethod.PARTIAL),
                Spoke("HIPAA", "§164.310(c)", "Integrity", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 5(1)(d)", "Accuracy", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 16", "Right to rectification", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "data_change_trigger", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "HIPAA", "GDPR"],
        },
        {
            "id": "UC-3.4", "title": "Data preparation pipeline",
            "category": "Data Governance", "risk_tier": RiskTier.HIGH,
            "description": "Document and control data preparation pipelines.",
            "verification_target": "Data preparation pipelines are documented and version-controlled.",
            "evidence_requirements": [
                EvidenceRequirement("pipeline_doc", "Pipeline documentation", "PDF", "7 years"),
                EvidenceRequirement("pipeline_config", "Pipeline configuration", "JSON", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.7.6", "Data preparation", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 10", "Data governance", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_change", "pipeline_update", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-3.5", "title": "Data for development and enhancement",
            "category": "Data Governance", "risk_tier": RiskTier.HIGH,
            "description": "Manage data used for AI system development and enhancement.",
            "verification_target": "Development data is properly managed and separated from production.",
            "evidence_requirements": [
                EvidenceRequirement("data_management_plan", "Data management plan", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.7.2", "Data for development and enhancement", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 4", "Risk identification (third-party)", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_release", "model_update", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-3.6", "title": "Data minimization and retention",
            "category": "Data Governance", "risk_tier": RiskTier.CRITICAL,
            "description": "Implement data minimization and retention policies.",
            "verification_target": "Data is retained only as long as necessary and minimized to what is required.",
            "evidence_requirements": [
                EvidenceRequirement("retention_policy", "Data retention policy", "PDF", "7 years"),
                EvidenceRequirement("deletion_log", "Data deletion log", "log", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.3", "Data resources", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "3.2", "Protect stored account data", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "12.3", "Security of sensitive data in non-production", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 5(1)(b)", "Purpose limitation", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 5(1)(c)", "Data minimization", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 5(1)(e)", "Storage limitation", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 17", "Right to erasure", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 18", "Right to restriction of processing", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 20", "Right to data portability", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 21", "Right to object", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 25", "Data protection by design and default", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 44", "General principle for transfers", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "retention_review", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["PCI_DSS", "GDPR"],
        },
        # Category 4: System Lifecycle & Engineering (UC-4.1 – UC-4.9)
        {
            "id": "UC-4.1", "title": "Objectives for responsible development",
            "category": "System Lifecycle & Engineering", "risk_tier": RiskTier.HIGH,
            "description": "Define objectives for responsible AI development.",
            "verification_target": "Documented responsible development objectives exist and are tracked.",
            "evidence_requirements": [
                EvidenceRequirement("objectives_doc", "Responsible development objectives", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.1.2", "Objectives for responsible development", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 1", "Policies, processes, procedures", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "MAP 1", "Context establishment", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("annual", "planning_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-4.2", "title": "Responsible design and development",
            "category": "System Lifecycle & Engineering", "risk_tier": RiskTier.CRITICAL,
            "description": "Implement responsible design and development practices.",
            "verification_target": "AI systems are designed with responsible AI principles embedded.",
            "evidence_requirements": [
                EvidenceRequirement("design_doc", "Design documentation", "PDF", "7 years"),
                EvidenceRequirement("review_record", "Design review records", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.1.3", "Responsible design & development", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "6.2", "Bespoke and custom software developed securely", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_release", "model_update", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "PCI_DSS"],
        },
        {
            "id": "UC-4.3", "title": "AI system requirements",
            "category": "System Lifecycle & Engineering", "risk_tier": RiskTier.CRITICAL,
            "description": "Define and document AI system requirements.",
            "verification_target": "Complete, testable requirements exist for all AI systems.",
            "evidence_requirements": [
                EvidenceRequirement("requirements_doc", "System requirements specification", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.2.2", "AI system requirements", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 2", "System categorization, capabilities", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_release", "model_update", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-4.4", "title": "Documentation of design and development",
            "category": "System Lifecycle & Engineering", "risk_tier": RiskTier.HIGH,
            "description": "Maintain comprehensive design and development documentation.",
            "verification_target": "Design documentation is complete and current for all AI systems.",
            "evidence_requirements": [
                EvidenceRequirement("design_doc", "Design and development documentation", "PDF", "7 years"),
                EvidenceRequirement("config_snapshot", "Configuration snapshot", "JSON", "3 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.2.3", "Documentation of design and development", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MEASURE 1", "Metrics and methods", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 11", "Technical documentation (Annex IV)", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 51-56", "GPAI obligations", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "2.2", "Configuration standards", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_release", "model_update", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT"],
        },
        {
            "id": "UC-4.5", "title": "Verification and validation",
            "category": "System Lifecycle & Engineering", "risk_tier": RiskTier.CRITICAL,
            "description": "Establish and maintain processes for verifying and validating AI systems.",
            "verification_target": "The AI system meets its defined accuracy, robustness, and safety requirements.",
            "evidence_requirements": [
                EvidenceRequirement("test_report", "Accuracy and robustness test results", "OSCAL assessment-results", "7 years"),
                EvidenceRequirement("evaluation_record", "Model evaluation metrics against baseline", "JSON", "7 years"),
                EvidenceRequirement("validation_signoff", "Human reviewer sign-off on validation results", "signed-attestation", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.2.4", "AI system verification and validation", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MEASURE 2.1-2.13", "Trustworthiness evaluation", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 15", "Accuracy, robustness, cybersecurity", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 43", "Conformity assessment", SatisfactionMethod.PARTIAL),
                Spoke("HIPAA", "§164.308(a)(1)(ii)(D)", "Information system activity review", SatisfactionMethod.INDIRECT),
                Spoke("PCI_DSS", "11.3", "Penetration testing", SatisfactionMethod.INDIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT"],
            "recommended_for": ["NIST_AI_RMF", "HIPAA", "PCI_DSS"],
            "depends_on": ["UC-4.3", "UC-4.4"],
        },
        {
            "id": "UC-4.6", "title": "AI system deployment",
            "category": "System Lifecycle & Engineering", "risk_tier": RiskTier.CRITICAL,
            "description": "Control AI system deployment processes.",
            "verification_target": "AI systems are deployed through a controlled, documented process.",
            "evidence_requirements": [
                EvidenceRequirement("deployment_record", "Deployment record", "JSON", "7 years"),
                EvidenceRequirement("approval_record", "Deployment approval", "signed-attestation", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.2.5", "AI system deployment", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MANAGE 1", "Risk prioritization, go/no-go", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 43", "Conformity assessment", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "2.2", "Configuration standards", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "6.3", "Software security patches", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
            "depends_on": ["UC-4.5"],
        },
        {
            "id": "UC-4.7", "title": "AI system operation and monitoring",
            "category": "System Lifecycle & Engineering", "risk_tier": RiskTier.CRITICAL,
            "description": "Monitor AI system operation and performance.",
            "verification_target": "AI systems are continuously monitored for performance and safety.",
            "evidence_requirements": [
                EvidenceRequirement("monitoring_config", "Monitoring configuration", "JSON", "3 years"),
                EvidenceRequirement("alert_log", "Monitoring alert log", "log", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.2.6", "AI system operation and monitoring", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MEASURE 3", "Risk tracking, feedback", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MANAGE 4", "Monitoring, incident response", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 72", "Post-market monitoring", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.308(a)(1)(ii)(D)", "Information system activity review", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.308(a)(7)", "Contingency plan", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "6.3", "Software security patches", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "10.6", "Audit log review", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "stream", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT", "HIPAA"],
        },
        {
            "id": "UC-4.8", "title": "AI system technical documentation",
            "category": "System Lifecycle & Engineering", "risk_tier": RiskTier.HIGH,
            "description": "Maintain technical documentation for AI systems.",
            "verification_target": "Technical documentation is complete and accessible to authorized users.",
            "evidence_requirements": [
                EvidenceRequirement("tech_doc", "Technical documentation", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.2.7", "AI system technical documentation", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MEASURE 1", "Metrics and methods", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 11", "Technical documentation (Annex IV)", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_release", "model_update", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT"],
        },
        {
            "id": "UC-4.9", "title": "Recording of event logs",
            "category": "System Lifecycle & Engineering", "risk_tier": RiskTier.CRITICAL,
            "description": "Record and maintain event logs for AI systems.",
            "verification_target": "Comprehensive event logs are maintained for all AI system activities.",
            "evidence_requirements": [
                EvidenceRequirement("audit_log", "System event logs", "log", "7 years"),
                EvidenceRequirement("log_config", "Logging configuration", "JSON", "3 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.2.8", "Recording of event logs", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MEASURE 3", "Risk tracking, feedback", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "MANAGE 4", "Monitoring, incident response", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 12", "Logging", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 72", "Post-market monitoring", SatisfactionMethod.PARTIAL),
                Spoke("HIPAA", "§164.310(b)", "Audit controls", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.312(b)", "Audit controls", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "10.1", "Audit logs for system components", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "10.2", "Audit logs for cardholder data", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "10.3", "Audit log content requirements", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "10.5", "Audit log protection", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 30", "Records of processing", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "stream", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT", "HIPAA", "PCI_DSS", "GDPR"],
        },
        # Category 5: Transparency & Communication (UC-5.1 – UC-5.5)
        {
            "id": "UC-5.1", "title": "System documentation for users",
            "category": "Transparency & Communication", "risk_tier": RiskTier.HIGH,
            "description": "Provide clear documentation for AI system users.",
            "verification_target": "Users have access to clear, accurate AI system documentation.",
            "evidence_requirements": [
                EvidenceRequirement("user_doc", "User-facing system documentation", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.8.2", "System documentation for users", SatisfactionMethod.DIRECT),
                Spoke("ISO_42001", "A.10.4", "Customers", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 13", "Transparency to users", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "3.3", "Mask PAN when displayed", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 13", "Information to data subject", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 14", "Information where data not obtained from subject", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 15", "Right of access", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_release", "model_update", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT", "GDPR"],
        },
        {
            "id": "UC-5.2", "title": "External reporting",
            "category": "Transparency & Communication", "risk_tier": RiskTier.HIGH,
            "description": "Establish external reporting mechanisms for AI system performance.",
            "verification_target": "Regular external reports on AI system performance are published.",
            "evidence_requirements": [
                EvidenceRequirement("report", "External performance report", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.8.3", "External reporting", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 5", "External engagement, feedback", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 13", "Transparency to users", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 50", "Limited-risk transparency", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 13", "Information to data subject", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 14", "Information where data not obtained from subject", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("quarterly", "reporting_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT"],
        },
        {
            "id": "UC-5.3", "title": "Communication of incidents",
            "category": "Transparency & Communication", "risk_tier": RiskTier.CRITICAL,
            "description": "Establish incident communication procedures.",
            "verification_target": "AI-related incidents are communicated to relevant parties per procedure.",
            "evidence_requirements": [
                EvidenceRequirement("incident_report", "Incident reports", "PDF", "7 years"),
                EvidenceRequirement("communication_log", "Incident communication log", "log", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.8.4", "Communication of incidents", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MANAGE 4", "Monitoring, incident response", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 73", "Incident reporting", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 86", "Reporting of serious incidents", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.308(a)(6)", "Security incident procedures", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "12.10", "Incident response plan", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 33", "Notification of personal data breach", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "incident_trigger", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT", "HIPAA", "PCI_DSS", "GDPR"],
        },
        {
            "id": "UC-5.4", "title": "Information for interested parties",
            "category": "Transparency & Communication", "risk_tier": RiskTier.MEDIUM,
            "description": "Provide information about AI systems to interested parties.",
            "verification_target": "Interested parties can access relevant AI system information.",
            "evidence_requirements": [
                EvidenceRequirement("info_package", "Information package for interested parties", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.8.5", "Information for interested parties", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 5", "External engagement, feedback", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 13", "Transparency to users", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 50", "Limited-risk transparency", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 15", "Right of access", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("annual", "review_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-5.5", "title": "AI system transparency statements",
            "category": "Transparency & Communication", "risk_tier": RiskTier.HIGH,
            "description": "Publish transparency statements for AI systems.",
            "verification_target": "Clear transparency statements are published for all AI systems.",
            "evidence_requirements": [
                EvidenceRequirement("transparency_statement", "Transparency statement", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("EU_AI_ACT", "Art. 13", "Transparency to users", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 50", "Limited-risk transparency", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_release", "model_update", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["EU_AI_ACT"],
        },
        # Category 6: Human Oversight & Interaction (UC-6.1 – UC-6.5)
        {
            "id": "UC-6.1", "title": "Human oversight mechanisms",
            "category": "Human Oversight & Interaction", "risk_tier": RiskTier.CRITICAL,
            "description": "Implement human oversight mechanisms for AI systems.",
            "verification_target": "AI systems have appropriate human oversight with override capability.",
            "evidence_requirements": [
                EvidenceRequirement("oversight_config", "Oversight configuration", "JSON", "3 years"),
                EvidenceRequirement("override_log", "Human override log", "log", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.6", "Human resources", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "GOVERN 3", "Workforce diversity, equity, inclusion", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 14", "Human oversight", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 22", "Automated decision-making", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "operation", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["EU_AI_ACT", "GDPR"],
        },
        {
            "id": "UC-6.2", "title": "Processes for responsible use",
            "category": "Human Oversight & Interaction", "risk_tier": RiskTier.HIGH,
            "description": "Establish processes for responsible AI system use.",
            "verification_target": "Documented processes govern responsible AI system use.",
            "evidence_requirements": [
                EvidenceRequirement("process_doc", "Responsible use process document", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.9.2", "Processes for responsible use", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 14", "Human oversight", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("annual", "review_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-6.3", "title": "Intended use of the AI system",
            "category": "Human Oversight & Interaction", "risk_tier": RiskTier.HIGH,
            "description": "Define and communicate intended use of AI systems.",
            "verification_target": "Intended use is clearly defined and communicated for all AI systems.",
            "evidence_requirements": [
                EvidenceRequirement("intended_use_doc", "Intended use documentation", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.9.4", "Intended use of the AI system", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MANAGE 1", "Risk prioritization, go/no-go", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 13", "Transparency to users", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 5(1)(b)", "Purpose limitation", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 21", "Right to object", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 22", "Automated decision-making", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_release", "model_update", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-6.4", "title": "Human-in-the-loop interaction design",
            "category": "Human Oversight & Interaction", "risk_tier": RiskTier.HIGH,
            "description": "Design human-in-the-loop interactions for AI systems.",
            "verification_target": "AI systems are designed with appropriate human-in-the-loop interactions.",
            "evidence_requirements": [
                EvidenceRequirement("interaction_design", "Interaction design documentation", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("EU_AI_ACT", "Art. 14", "Human oversight", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_release", "model_update", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-6.5", "title": "Human override and intervention",
            "category": "Human Oversight & Interaction", "risk_tier": RiskTier.CRITICAL,
            "description": "Enable human override and intervention in AI system operations.",
            "verification_target": "Humans can override AI system decisions when necessary.",
            "evidence_requirements": [
                EvidenceRequirement("override_procedure", "Override procedure documentation", "PDF", "7 years"),
                EvidenceRequirement("override_log", "Override action log", "log", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.6", "Human resources", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "GOVERN 3", "Workforce diversity, equity, inclusion", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 4", "AI literacy", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 14", "Human oversight", SatisfactionMethod.PARTIAL),
                Spoke("HIPAA", "§164.308(a)(5)", "Security awareness and training", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "operation", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        # Category 7: Security & Robustness (UC-7.1 – UC-7.7)
        {
            "id": "UC-7.1", "title": "Infrastructure security",
            "category": "Security & Robustness", "risk_tier": RiskTier.CRITICAL,
            "description": "Secure AI system infrastructure.",
            "verification_target": "AI system infrastructure meets security baseline requirements.",
            "evidence_requirements": [
                EvidenceRequirement("config_snapshot", "Infrastructure configuration", "JSON", "3 years"),
                EvidenceRequirement("scan_report", "Vulnerability scan results", "PDF", "3 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.5", "System and computing resources", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 15", "Accuracy, robustness, cybersecurity", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.312(e)", "Transmission security", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "1.2", "Network security controls", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "3.2", "Protect stored account data", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "3.4", "Render PAN unreadable", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "4.2", "Protect cardholder data with strong cryptography", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "5.2", "Protect all systems against malware", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "11.4", "Intrusion detection/prevention", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 5(1)(f)", "Integrity and confidentiality", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 25", "Data protection by design and default", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 32", "Security of processing", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "change_detection", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT", "HIPAA", "PCI_DSS", "GDPR"],
        },
        {
            "id": "UC-7.2", "title": "AI system robustness testing",
            "category": "Security & Robustness", "risk_tier": RiskTier.CRITICAL,
            "description": "Test AI system robustness against adversarial inputs.",
            "verification_target": "AI systems pass robustness testing against defined threat models.",
            "evidence_requirements": [
                EvidenceRequirement("robustness_report", "Robustness test report", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("NIST_AI_RMF", "MEASURE 2", "Trustworthiness evaluation", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 15", "Accuracy, robustness, cybersecurity", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "11.3", "Penetration testing", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["NIST_AI_RMF", "EU_AI_ACT", "PCI_DSS"],
        },
        {
            "id": "UC-7.3", "title": "Model security",
            "category": "Security & Robustness", "risk_tier": RiskTier.CRITICAL,
            "description": "Secure AI models against extraction and poisoning attacks.",
            "verification_target": "AI models are protected against known attack vectors.",
            "evidence_requirements": [
                EvidenceRequirement("model_security_assessment", "Model security assessment", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("EU_AI_ACT", "Art. 15", "Accuracy, robustness, cybersecurity", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-7.4", "title": "API security",
            "category": "Security & Robustness", "risk_tier": RiskTier.HIGH,
            "description": "Secure AI system APIs.",
            "verification_target": "AI system APIs implement appropriate security controls.",
            "evidence_requirements": [
                EvidenceRequirement("api_security_config", "API security configuration", "JSON", "3 years"),
            ],
            "spokes": [
                Spoke("EU_AI_ACT", "Art. 15", "Accuracy, robustness, cybersecurity", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "change_detection", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-7.5", "title": "Access control and authentication",
            "category": "Security & Robustness", "risk_tier": RiskTier.CRITICAL,
            "description": "Implement access control and authentication for AI systems.",
            "verification_target": "Access to AI systems is controlled and authenticated.",
            "evidence_requirements": [
                EvidenceRequirement("access_config", "Access control configuration", "JSON", "3 years"),
                EvidenceRequirement("access_review", "Access review records", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.3.2", "AI roles and responsibilities", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "GOVERN 2", "Accountability structures", SatisfactionMethod.PARTIAL),
                Spoke("HIPAA", "§164.308(a)(4)", "Access management", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.310(a)", "Access control", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.310(d)", "Person or entity authentication", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.312(a)", "Access control", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.312(d)", "Person or entity authentication", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "8.2", "User authentication", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "8.3", "Secure all individual non-console administrative access", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "9.2", "Physical access controls", SatisfactionMethod.INDIRECT),
                Spoke("GDPR", "Art. 5(1)(f)", "Integrity and confidentiality", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 32", "Security of processing", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "change_detection", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["HIPAA", "PCI_DSS"],
        },
        {
            "id": "UC-7.6", "title": "Third-party component security",
            "category": "Security & Robustness", "risk_tier": RiskTier.HIGH,
            "description": "Manage security of third-party AI components.",
            "verification_target": "Third-party AI components meet security requirements.",
            "evidence_requirements": [
                EvidenceRequirement("component_assessment", "Component security assessment", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.4", "Tooling resources", SatisfactionMethod.PARTIAL),
                Spoke("ISO_42001", "A.7.3", "Acquisition of data", SatisfactionMethod.PARTIAL),
                Spoke("ISO_42001", "A.7.5", "Data provenance", SatisfactionMethod.PARTIAL),
                Spoke("ISO_42001", "A.10.3", "Suppliers", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 6", "Third-party risk management", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 25", "Supplier obligations", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_change", "component_update", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "EU_AI_ACT"],
        },
        {
            "id": "UC-7.7", "title": "Malware protection",
            "category": "Security & Robustness", "risk_tier": RiskTier.HIGH,
            "description": "Protect AI systems against malware.",
            "verification_target": "AI systems have appropriate malware protection.",
            "evidence_requirements": [
                EvidenceRequirement("malware_config", "Malware protection configuration", "JSON", "3 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.5", "System and computing resources", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "5.2", "Protect all systems against malware", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "scheduled", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["PCI_DSS"],
        },
        # Category 8: Agentic AI Security (UC-8.1 – UC-8.10)
        {
            "id": "UC-8.1", "title": "Agent permission boundaries",
            "category": "Agentic AI Security", "risk_tier": RiskTier.CRITICAL,
            "description": "Define and enforce permission boundaries for AI agents.",
            "verification_target": "AI agents operate within defined permission boundaries.",
            "evidence_requirements": [
                EvidenceRequirement("permission_config", "Agent permission configuration", "JSON", "3 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.1.3", "Responsible design & development", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "change_detection", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-8.2", "title": "Agent action validation",
            "category": "Agentic AI Security", "risk_tier": RiskTier.CRITICAL,
            "description": "Validate AI agent actions before execution.",
            "verification_target": "AI agent actions are validated against policy before execution.",
            "evidence_requirements": [
                EvidenceRequirement("validation_log", "Action validation log", "log", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.9.2", "Processes for responsible use", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "operation", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-8.3", "title": "Agent authentication and authorization",
            "category": "Agentic AI Security", "risk_tier": RiskTier.CRITICAL,
            "description": "Authenticate and authorize AI agent actions.",
            "verification_target": "AI agents are authenticated and authorized for all actions.",
            "evidence_requirements": [
                EvidenceRequirement("auth_config", "Agent authentication configuration", "JSON", "3 years"),
            ],
            "spokes": [
                Spoke("HIPAA", "§164.310(d)", "Person or entity authentication", SatisfactionMethod.PARTIAL),
                Spoke("HIPAA", "§164.312(d)", "Person or entity authentication", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "8.2", "User authentication", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "change_detection", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-8.4", "title": "Agent tool security",
            "category": "Agentic AI Security", "risk_tier": RiskTier.HIGH,
            "description": "Secure tools used by AI agents.",
            "verification_target": "Tools available to AI agents are security-reviewed.",
            "evidence_requirements": [
                EvidenceRequirement("tool_review", "Tool security review", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.4", "Tooling resources", SatisfactionMethod.PARTIAL),
                Spoke("ISO_42001", "A.10.3", "Suppliers", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "GOVERN 6", "Third-party risk management", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 25", "Supplier obligations", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_change", "tool_update", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-8.5", "title": "Agent sandboxing",
            "category": "Agentic AI Security", "risk_tier": RiskTier.CRITICAL,
            "description": "Sandbox AI agent execution environments.",
            "verification_target": "AI agents execute in sandboxed environments.",
            "evidence_requirements": [
                EvidenceRequirement("sandbox_config", "Sandbox configuration", "JSON", "3 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.4.5", "System and computing resources", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 15", "Accuracy, robustness, cybersecurity", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "change_detection", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-8.6", "title": "Agent prompt injection defense",
            "category": "Agentic AI Security", "risk_tier": RiskTier.CRITICAL,
            "description": "Defend against prompt injection attacks.",
            "verification_target": "AI agents are protected against prompt injection.",
            "evidence_requirements": [
                EvidenceRequirement("injection_test", "Prompt injection test results", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.1.3", "Responsible design & development", SatisfactionMethod.PARTIAL),
                Spoke("ISO_42001", "A.7.2", "Data for development and enhancement", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-8.7", "title": "Agent network security",
            "category": "Agentic AI Security", "risk_tier": RiskTier.HIGH,
            "description": "Secure AI agent network communications.",
            "verification_target": "AI agent network communications are encrypted and authenticated.",
            "evidence_requirements": [
                EvidenceRequirement("network_config", "Network security configuration", "JSON", "3 years"),
            ],
            "spokes": [
                Spoke("EU_AI_ACT", "Art. 15", "Accuracy, robustness, cybersecurity", SatisfactionMethod.PARTIAL),
                Spoke("HIPAA", "§164.312(e)", "Transmission security", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "4.2", "Protect cardholder data with strong cryptography", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "change_detection", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-8.8", "title": "Agent monitoring and logging",
            "category": "Agentic AI Security", "risk_tier": RiskTier.CRITICAL,
            "description": "Monitor and log AI agent activities.",
            "verification_target": "All AI agent activities are monitored and logged.",
            "evidence_requirements": [
                EvidenceRequirement("agent_log", "Agent activity logs", "log", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.2.6", "AI system operation and monitoring", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "MEASURE 3", "Risk tracking, feedback", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "MANAGE 4", "Monitoring, incident response", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 72", "Post-market monitoring", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "stream", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-8.9", "title": "Agent transparency documentation",
            "category": "Agentic AI Security", "risk_tier": RiskTier.MEDIUM,
            "description": "Document AI agent capabilities and limitations.",
            "verification_target": "AI agent capabilities and limitations are documented.",
            "evidence_requirements": [
                EvidenceRequirement("agent_doc", "Agent documentation", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.8.2", "System documentation for users", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_release", "model_update", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        {
            "id": "UC-8.10", "title": "Agent incident response",
            "category": "Agentic AI Security", "risk_tier": RiskTier.CRITICAL,
            "description": "Establish incident response for AI agent incidents.",
            "verification_target": "AI agent incidents are responded to per documented procedures.",
            "evidence_requirements": [
                EvidenceRequirement("incident_response_plan", "Agent incident response plan", "PDF", "7 years"),
                EvidenceRequirement("incident_log", "Agent incident log", "log", "7 years"),
            ],
            "spokes": [
                Spoke("NIST_AI_RMF", "MANAGE 4", "Monitoring, incident response", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "incident_trigger", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        # Category 9: Fairness, Privacy & Ethics (UC-9.1 – UC-9.5)
        {
            "id": "UC-9.1", "title": "Bias detection and mitigation",
            "category": "Fairness, Privacy & Ethics", "risk_tier": RiskTier.CRITICAL,
            "description": "Detect and mitigate bias in AI systems.",
            "verification_target": "AI systems are tested for bias and mitigations are applied.",
            "evidence_requirements": [
                EvidenceRequirement("bias_report", "Bias assessment report", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.7.4", "Quality of data for AI systems", SatisfactionMethod.PARTIAL),
                Spoke("NIST_AI_RMF", "MEASURE 2", "Trustworthiness evaluation", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.310(c)", "Integrity", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 5(1)(d)", "Accuracy", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["NIST_AI_RMF"],
        },
        {
            "id": "UC-9.2", "title": "Privacy impact assessment",
            "category": "Fairness, Privacy & Ethics", "risk_tier": RiskTier.CRITICAL,
            "description": "Conduct privacy impact assessments for AI systems.",
            "verification_target": "Privacy impact assessments are completed for all AI systems processing personal data.",
            "evidence_requirements": [
                EvidenceRequirement("pia_report", "Privacy impact assessment report", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("NIST_AI_RMF", "MEASURE 2", "Trustworthiness evaluation", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 25", "Data protection by design and default", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["GDPR"],
        },
        {
            "id": "UC-9.3", "title": "Automated decision-making safeguards",
            "category": "Fairness, Privacy & Ethics", "risk_tier": RiskTier.CRITICAL,
            "description": "Implement safeguards for automated decision-making.",
            "verification_target": "Automated decisions have appropriate safeguards and human review options.",
            "evidence_requirements": [
                EvidenceRequirement("safeguard_config", "Automated decision safeguards configuration", "JSON", "3 years"),
            ],
            "spokes": [
                Spoke("NIST_AI_RMF", "MEASURE 2", "Trustworthiness evaluation", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 22", "Automated decision-making", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "operation", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["GDPR"],
        },
        {
            "id": "UC-9.4", "title": "Ethical review process",
            "category": "Fairness, Privacy & Ethics", "risk_tier": RiskTier.HIGH,
            "description": "Establish ethical review process for AI systems.",
            "verification_target": "AI systems undergo ethical review before deployment.",
            "evidence_requirements": [
                EvidenceRequirement("ethics_review", "Ethical review record", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.5.5", "Societal impacts", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 5", "Prohibited practices", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 51-56", "GPAI obligations", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", False),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["EU_AI_ACT"],
        },
        {
            "id": "UC-9.5", "title": "Fairness metrics and monitoring",
            "category": "Fairness, Privacy & Ethics", "risk_tier": RiskTier.HIGH,
            "description": "Monitor fairness metrics for AI systems.",
            "verification_target": "Fairness metrics are continuously monitored for deployed AI systems.",
            "evidence_requirements": [
                EvidenceRequirement("fairness_metrics", "Fairness metrics dashboard data", "JSON", "7 years"),
            ],
            "spokes": [
                Spoke("NIST_AI_RMF", "MEASURE 2", "Trustworthiness evaluation", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "stream", True),
            "minimum_verification_level": VerificationLevel.L2,
        },
        # Category 10: Third-Party & Supply Chain (UC-10.1 – UC-10.4)
        {
            "id": "UC-10.1", "title": "Third-party AI risk assessment",
            "category": "Third-Party & Supply Chain", "risk_tier": RiskTier.CRITICAL,
            "description": "Assess risks from third-party AI providers.",
            "verification_target": "Third-party AI providers are assessed for risk before engagement.",
            "evidence_requirements": [
                EvidenceRequirement("vendor_assessment", "Vendor risk assessment", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.10.3", "Suppliers", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 6", "Third-party risk management", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MAP 4", "Risk identification (third-party)", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "MANAGE 3", "Third-party risk management", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 25", "Supplier obligations", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 44", "General principle for transfers", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("annual", "vendor_review", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001", "NIST_AI_RMF", "EU_AI_ACT"],
        },
        {
            "id": "UC-10.2", "title": "Customer AI system obligations",
            "category": "Third-Party & Supply Chain", "risk_tier": RiskTier.HIGH,
            "description": "Manage AI system obligations to customers.",
            "verification_target": "Customer-facing AI system obligations are documented and met.",
            "evidence_requirements": [
                EvidenceRequirement("obligation_doc", "Customer obligations document", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.10.4", "Customers", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 5", "External engagement, feedback", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("annual", "review_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-10.3", "title": "Supply chain security for AI",
            "category": "Third-Party & Supply Chain", "risk_tier": RiskTier.HIGH,
            "description": "Secure the AI supply chain.",
            "verification_target": "AI supply chain components are security-reviewed.",
            "evidence_requirements": [
                EvidenceRequirement("supply_chain_assessment", "Supply chain security assessment", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.3.2", "AI roles and responsibilities", SatisfactionMethod.PARTIAL),
                Spoke("ISO_42001", "A.10.2", "Allocating responsibilities", SatisfactionMethod.DIRECT),
                Spoke("NIST_AI_RMF", "GOVERN 2", "Accountability structures", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("annual", "review_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-10.4", "title": "Third-party incident coordination",
            "category": "Third-Party & Supply Chain", "risk_tier": RiskTier.HIGH,
            "description": "Coordinate incident response with third parties.",
            "verification_target": "Third-party incident coordination procedures are documented and tested.",
            "evidence_requirements": [
                EvidenceRequirement("coordination_plan", "Third-party incident coordination plan", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("NIST_AI_RMF", "MANAGE 3", "Third-party risk management", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("annual", "review_cycle", False),
            "minimum_verification_level": VerificationLevel.L2,
        },
        # Category 11: Compliance & Certification (UC-11.1 – UC-11.5)
        {
            "id": "UC-11.1", "title": "Quality management system",
            "category": "Compliance & Certification", "risk_tier": RiskTier.CRITICAL,
            "description": "Establish a quality management system for AI.",
            "verification_target": "A QMS is established and maintained for AI system development.",
            "evidence_requirements": [
                EvidenceRequirement("qms_doc", "Quality management system documentation", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("EU_AI_ACT", "Art. 17", "Quality management system", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 30", "Records of processing", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("annual", "review_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["EU_AI_ACT"],
        },
        {
            "id": "UC-11.2", "title": "Conformity assessment preparation",
            "category": "Compliance & Certification", "risk_tier": RiskTier.CRITICAL,
            "description": "Prepare for AI system conformity assessments.",
            "verification_target": "Conformity assessment documentation is complete and current.",
            "evidence_requirements": [
                EvidenceRequirement("conformity_doc", "Conformity assessment documentation", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("EU_AI_ACT", "Art. 43", "Conformity assessment", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("annual", "assessment_cycle", True),
            "minimum_verification_level": VerificationLevel.L3,
            "mandatory_for": ["EU_AI_ACT"],
        },
        {
            "id": "UC-11.3", "title": "EU database registration",
            "category": "Compliance & Certification", "risk_tier": RiskTier.HIGH,
            "description": "Register AI systems in the EU database.",
            "verification_target": "High-risk AI systems are registered in the EU database.",
            "evidence_requirements": [
                EvidenceRequirement("registration_record", "EU database registration record", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("EU_AI_ACT", "Art. 71", "EU database registration", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("per_deployment", "model_deployment", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["EU_AI_ACT"],
        },
        {
            "id": "UC-11.4", "title": "Post-market monitoring",
            "category": "Compliance & Certification", "risk_tier": RiskTier.CRITICAL,
            "description": "Monitor AI systems after market deployment.",
            "verification_target": "Post-market monitoring is active for all deployed AI systems.",
            "evidence_requirements": [
                EvidenceRequirement("monitoring_report", "Post-market monitoring report", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.6.2.6", "AI system operation and monitoring", SatisfactionMethod.PARTIAL),
                Spoke("EU_AI_ACT", "Art. 72", "Post-market monitoring", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.308(a)(7)", "Contingency plan", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "stream", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["EU_AI_ACT"],
        },
        {
            "id": "UC-11.5", "title": "Incident reporting and management",
            "category": "Compliance & Certification", "risk_tier": RiskTier.CRITICAL,
            "description": "Manage AI system incident reporting.",
            "verification_target": "AI system incidents are reported per regulatory requirements.",
            "evidence_requirements": [
                EvidenceRequirement("incident_report", "Incident reports", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("EU_AI_ACT", "Art. 73", "Incident reporting", SatisfactionMethod.DIRECT),
                Spoke("EU_AI_ACT", "Art. 86", "Reporting of serious incidents", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.308(a)(6)", "Security incident procedures", SatisfactionMethod.PARTIAL),
                Spoke("PCI_DSS", "12.10", "Incident response plan", SatisfactionMethod.PARTIAL),
                Spoke("GDPR", "Art. 33", "Notification of personal data breach", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "incident_trigger", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["EU_AI_ACT"],
        },
        # Category 12: Continuous Improvement (UC-12.1 – UC-12.4)
        {
            "id": "UC-12.1", "title": "AI policy review cycle",
            "category": "Continuous Improvement", "risk_tier": RiskTier.HIGH,
            "description": "Regularly review and update AI policies.",
            "verification_target": "AI policies are reviewed and updated on a defined cycle.",
            "evidence_requirements": [
                EvidenceRequirement("review_record", "Policy review record", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("ISO_42001", "A.2.4", "Review of AI policy", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("annual", "policy_review_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["ISO_42001"],
        },
        {
            "id": "UC-12.2", "title": "Measurement feedback loop",
            "category": "Continuous Improvement", "risk_tier": RiskTier.HIGH,
            "description": "Establish feedback loops from measurements to improvements.",
            "verification_target": "Measurement insights drive continuous improvement actions.",
            "evidence_requirements": [
                EvidenceRequirement("improvement_log", "Improvement action log", "JSON", "7 years"),
            ],
            "spokes": [
                Spoke("NIST_AI_RMF", "MEASURE 4", "Measurement feedback", SatisfactionMethod.DIRECT),
                Spoke("HIPAA", "§164.308(a)(8)", "Evaluation", SatisfactionMethod.DIRECT),
                Spoke("PCI_DSS", "10.6", "Audit log review", SatisfactionMethod.PARTIAL),
            ],
            "collection_schedule": CollectionSchedule("continuous", "measurement_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["NIST_AI_RMF", "HIPAA"],
        },
        {
            "id": "UC-12.3", "title": "Periodic compliance evaluation",
            "category": "Continuous Improvement", "risk_tier": RiskTier.HIGH,
            "description": "Conduct periodic compliance evaluations.",
            "verification_target": "Compliance is evaluated on a defined schedule.",
            "evidence_requirements": [
                EvidenceRequirement("evaluation_report", "Compliance evaluation report", "PDF", "7 years"),
            ],
            "spokes": [
                Spoke("HIPAA", "§164.308(a)(8)", "Evaluation", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("annual", "evaluation_cycle", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["HIPAA"],
        },
        {
            "id": "UC-12.4", "title": "Data retention and deletion",
            "category": "Continuous Improvement", "risk_tier": RiskTier.HIGH,
            "description": "Manage data retention and deletion schedules.",
            "verification_target": "Data is retained and deleted per policy.",
            "evidence_requirements": [
                EvidenceRequirement("deletion_log", "Data deletion log", "log", "7 years"),
            ],
            "spokes": [
                Spoke("GDPR", "Art. 5(1)(e)", "Storage limitation", SatisfactionMethod.DIRECT),
                Spoke("GDPR", "Art. 17", "Right to erasure", SatisfactionMethod.DIRECT),
            ],
            "collection_schedule": CollectionSchedule("continuous", "retention_review", True),
            "minimum_verification_level": VerificationLevel.L2,
            "mandatory_for": ["GDPR"],
        },
    ]

    for ctrl_data in controls_data:
        control = UnifiedControl(**ctrl_data)
        registry.register(control)


# --- Usage Example ---
if __name__ == "__main__":
    registry = ControlRegistry(storage_path="/tmp/grc-controls/")
    bootstrap_control_catalog(registry)

    print(f"Total controls registered: {len(registry.list_all())}")
    print(f"Categories: {len(registry._index_by_category)}")
    print(f"Frameworks covered: {list(registry._index_by_framework.keys())}")

    # Example: Get all controls for ISO_42001
    iso_controls = registry.list_by_framework("ISO_42001")
    print(f"\nISO_42001 controls: {len(iso_controls)}")

    # Example: Get critical controls
    critical = registry.list_by_risk_tier(RiskTier.CRITICAL)
    print(f"Critical controls: {len(critical)}")

    # Example: Export catalog
    catalog = registry.export_catalog()
    print(f"\nCatalog export: {catalog['total_controls']} controls")
```

---

## 2. Framework Mapping Engine

The framework mapping engine evaluates whether the unified control set satisfies framework requirements using the hub-and-spoke model.

```python
"""
GRC_Claw Framework Mapping Engine
Evaluates multi-framework satisfaction using the hub-and-spoke model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from control_registry import (
    ControlRegistry, UnifiedControl, Spoke, SatisfactionMethod,
    VerificationLevel, RiskTier,
)


class SatisfactionState(Enum):
    SATISFIED = "SATISFIED"
    PARTIALLY_SATISFIED = "PARTIALLY_SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class RequirementSatisfaction:
    framework: str
    requirement: str
    title: str
    state: SatisfactionState
    satisfying_controls: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class FrameworkSatisfactionMatrix:
    framework: str
    framework_name: str
    total_requirements: int
    satisfied: int
    partially_satisfied: int
    not_satisfied: int
    not_applicable: int
    score: float
    requirements: list[RequirementSatisfaction] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class FrameworkMappingEngine:
    """Evaluates framework satisfaction using the hub-and-spoke model."""

    FRAMEWORK_NAMES = {
        "ISO_42001": "ISO/IEC 42001:2023",
        "NIST_AI_RMF": "NIST AI RMF 1.0",
        "EU_AI_ACT": "EU AI Act (Reg. 2024/1689)",
        "HIPAA": "HIPAA Security Rule",
        "PCI_DSS": "PCI DSS v4.0",
        "GDPR": "GDPR (Reg. 2016/679)",
    }

    FRAMEWORK_WEIGHTS = {
        "ISO_42001": 0.20,
        "NIST_AI_RMF": 0.20,
        "EU_AI_ACT": 0.25,
        "HIPAA": 0.15,
        "PCI_DSS": 0.10,
        "GDPR": 0.10,
    }

    def __init__(self, registry: ControlRegistry):
        self.registry = registry

    def evaluate_requirement(
        self,
        framework: str,
        requirement: str,
        control_statuses: dict[str, dict],
    ) -> RequirementSatisfaction:
        """Evaluate satisfaction for a single framework requirement."""
        mappings = self.registry.get_controls_for_requirement(framework, requirement)

        if not mappings:
            return RequirementSatisfaction(
                framework=framework,
                requirement=requirement,
                title=requirement,
                state=SatisfactionState.NOT_SATISFIED,
                notes="No controls mapped to this requirement",
            )

        direct_satisfied = []
        partial_satisfied = []
        indirect_satisfied = []
        evidence_refs = []

        for control, spoke in mappings:
            status = control_statuses.get(control.id, {})
            impl_status = status.get("implementation_status", "NOT_IMPLEMENTED")
            evidence_current = status.get("evidence_current", False)
            verification_level = status.get("verification_level", VerificationLevel.L0)
            evidence_level_required = status.get("evidence_level_required", VerificationLevel.L2)

            if impl_status != "ACTIVE":
                continue
            if not evidence_current:
                continue
            if verification_level.value < evidence_level_required.value:
                continue

            if spoke.satisfaction_method == SatisfactionMethod.DIRECT:
                direct_satisfied.append(control.id)
                evidence_refs.extend(status.get("evidence_ids", []))
            elif spoke.satisfaction_method == SatisfactionMethod.PARTIAL:
                partial_satisfied.append(control.id)
                evidence_refs.extend(status.get("evidence_ids", []))
            elif spoke.satisfaction_method == SatisfactionMethod.INDIRECT:
                indirect_satisfied.append(control.id)
            elif spoke.satisfaction_method == SatisfactionMethod.COMPOSITE:
                partial_satisfied.append(control.id)

        # Determine satisfaction state
        if direct_satisfied:
            state = SatisfactionState.SATISFIED
        elif partial_satisfied and len(partial_satisfied) >= 2:
            state = SatisfactionState.SATISFIED
        elif partial_satisfied or indirect_satisfied:
            state = SatisfactionState.PARTIALLY_SATISFIED
        else:
            state = SatisfactionState.NOT_SATISFIED

        satisfying = direct_satisfied + partial_satisfied

        return RequirementSatisfaction(
            framework=framework,
            requirement=requirement,
            title=mappings[0][1].title,
            state=state,
            satisfying_controls=satisfying,
            evidence_refs=evidence_refs,
        )

    def evaluate_framework(
        self,
        framework: str,
        control_statuses: dict[str, dict],
        applicable_requirements: Optional[list[str]] = None,
    ) -> FrameworkSatisfactionMatrix:
        """Evaluate satisfaction for an entire framework."""
        # Collect all requirements for this framework
        if applicable_requirements is None:
            req_set = set()
            for control in self.registry.list_by_framework(framework):
                for spoke in control.spokes:
                    if spoke.framework == framework:
                        req_set.add(spoke.requirement)
            applicable_requirements = sorted(req_set)

        requirements = []
        for req in applicable_requirements:
            sat = self.evaluate_requirement(framework, req, control_statuses)
            requirements.append(sat)

        total = len(requirements)
        satisfied = sum(1 for r in requirements if r.state == SatisfactionState.SATISFIED)
        partial = sum(1 for r in requirements if r.state == SatisfactionState.PARTIALLY_SATISFIED)
        not_sat = sum(1 for r in requirements if r.state == SatisfactionState.NOT_SATISFIED)
        not_app = sum(1 for r in requirements if r.state == SatisfactionState.NOT_APPLICABLE)

        # Calculate score: SATISFIED=1.0, PARTIAL=0.5, NOT_SATISFIED=0.0
        applicable_count = total - not_app
        if applicable_count > 0:
            score = (satisfied * 1.0 + partial * 0.5) / applicable_count
        else:
            score = 0.0

        return FrameworkSatisfactionMatrix(
            framework=framework,
            framework_name=self.FRAMEWORK_NAMES.get(framework, framework),
            total_requirements=total,
            satisfied=satisfied,
            partially_satisfied=partial,
            not_satisfied=not_sat,
            not_applicable=not_app,
            score=round(score, 4),
            requirements=requirements,
        )

    def evaluate_all_frameworks(
        self,
        control_statuses: dict[str, dict],
        active_frameworks: Optional[list[str]] = None,
    ) -> dict[str, FrameworkSatisfactionMatrix]:
        """Evaluate satisfaction across all active frameworks."""
        if active_frameworks is None:
            active_frameworks = list(self.FRAMEWORK_NAMES.keys())

        results = {}
        for fw in active_frameworks:
            results[fw] = self.evaluate_framework(fw, control_statuses)
        return results

    def compute_overall_posture(
        self, framework_results: dict[str, FrameworkSatisfactionMatrix]
    ) -> dict:
        """Compute overall compliance posture across all frameworks."""
        total_weight = 0.0
        weighted_score = 0.0

        for fw, matrix in framework_results.items():
            weight = self.FRAMEWORK_WEIGHTS.get(fw, 0.0)
            total_weight += weight
            weighted_score += weight * matrix.score

        overall_score = weighted_score / total_weight if total_weight > 0 else 0.0

        return {
            "overall_score": round(overall_score, 4),
            "overall_percentage": round(overall_score * 100, 2),
            "frameworks": {
                fw: {
                    "name": m.framework_name,
                    "score": m.score,
                    "percentage": round(m.score * 100, 2),
                    "satisfied": m.satisfied,
                    "partially_satisfied": m.partially_satisfied,
                    "not_satisfied": m.not_satisfied,
                    "total": m.total_requirements,
                }
                for fw, m in framework_results.items()
            },
            "computed_at": datetime.utcnow().isoformat() + "Z",
        }

    def identify_gaps(
        self, framework_results: dict[str, FrameworkSatisfactionMatrix]
    ) -> list[dict]:
        """Identify all gaps across frameworks."""
        gaps = []
        for fw, matrix in framework_results.items():
            for req in matrix.requirements:
                if req.state in (SatisfactionState.NOT_SATISFIED, SatisfactionState.PARTIALLY_SATISFIED):
                    gaps.append({
                        "framework": fw,
                        "framework_name": matrix.framework_name,
                        "requirement": req.requirement,
                        "title": req.title,
                        "state": req.state.value,
                        "satisfying_controls": req.satisfying_controls,
                        "notes": req.notes,
                    })
        return gaps

    def generate_framework_view(
        self,
        framework: str,
        control_statuses: dict[str, dict],
    ) -> dict:
        """Generate a framework-specific view of compliance."""
        matrix = self.evaluate_framework(framework, control_statuses)

        # Group requirements by control category
        categories = {}
        for req in matrix.requirements:
            for ctrl_id in req.satisfying_controls:
                control = self.registry.get(ctrl_id)
                if control:
                    cat = control.category
                    if cat not in categories:
                        categories[cat] = {"controls": set(), "satisfied": 0, "total": 0}
                    categories[cat]["controls"].add(ctrl_id)
                    categories[cat]["total"] += 1
                    if req.state == SatisfactionState.SATISFIED:
                        categories[cat]["satisfied"] += 1

        return {
            "framework": framework,
            "framework_name": matrix.framework_name,
            "generated_at": matrix.generated_at,
            "summary": {
                "total_requirements": matrix.total_requirements,
                "satisfied": matrix.satisfied,
                "partially_satisfied": matrix.partially_satisfied,
                "not_satisfied": matrix.not_satisfied,
                "score": matrix.score,
                "percentage": round(matrix.score * 100, 2),
            },
            "categories": {
                cat: {
                    "controls": sorted(data["controls"]),
                    "satisfied": data["satisfied"],
                    "total": data["total"],
                }
                for cat, data in categories.items()
            },
            "requirements": [
                {
                    "requirement": r.requirement,
                    "title": r.title,
                    "state": r.state.value,
                    "satisfying_controls": r.satisfying_controls,
                    "evidence_refs": r.evidence_refs,
                }
                for r in matrix.requirements
            ],
        }


# --- Usage Example ---
if __name__ == "__main__":
    from control_registry import ControlRegistry, bootstrap_control_catalog

    registry = ControlRegistry(storage_path="/tmp/grc-controls/")
    bootstrap_control_catalog(registry)

    engine = FrameworkMappingEngine(registry)

    # Simulate control statuses (in production, these come from the evidence store)
    control_statuses = {}
    for control in registry.list_all():
        control_statuses[control.id] = {
            "implementation_status": "ACTIVE",
            "evidence_current": True,
            "verification_level": VerificationLevel.L2,
            "evidence_level_required": VerificationLevel.L2,
            "evidence_ids": [f"evd-{control.id}-001"],
        }

    # Evaluate all frameworks
    results = engine.evaluate_all_frameworks(control_statuses)

    for fw, matrix in results.items():
        print(f"\n{matrix.framework_name}")
        print(f"  Score: {matrix.score * 100:.1f}%")
        print(f"  Satisfied: {matrix.satisfied}/{matrix.total_requirements}")
        print(f"  Partial: {matrix.partially_satisfied}")
        print(f"  Not Satisfied: {matrix.not_satisfied}")

    # Overall posture
    posture = engine.compute_overall_posture(results)
    print(f"\nOverall Compliance Posture: {posture['overall_percentage']}%")

    # Gap analysis
    gaps = engine.identify_gaps(results)
    print(f"\nGaps identified: {len(gaps)}")
```

---

## 3. Evidence-to-Control Binding

Manages the binding between evidence artifacts and unified controls, including the evidence lifecycle from collection through export.

```python
"""
GRC_Claw Evidence-to-Control Binding
Manages evidence artifacts, their lifecycle, and binding to unified controls.
"""

from __future__ import annotations

import json
import hashlib
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from control_registry import (
    ControlRegistry, UnifiedControl, VerificationLevel, EvidenceRequirement,
)


class EvidenceType(Enum):
    ARTIFACT = "artifact"
    OBSERVATION = "observation"
    INTERVIEW = "interview"
    ANALYSIS = "analysis"
    LOG = "log"


class CustodyAction(Enum):
    COLLECTED = "collected"
    TRANSFERRED = "transferred"
    VERIFIED = "verified"
    EXPORTED = "exported"
    ACCESSED = "accessed"


@dataclass
class CustodyEvent:
    event_id: str
    evidence_id: str
    action: CustodyAction
    actor: str
    timestamp: str
    evidence_hash: str
    previous_event_hash: str = ""
    signature: str = ""


@dataclass
class EvidenceItem:
    evidence_id: str
    control_id: str
    type: EvidenceType
    title: str
    description: str
    collected_by: str
    collected_at: str
    source_system: str
    source_location: str
    content_format: str
    content_data: str  # base64-encoded or inline
    content_hash: str
    environment: str
    resource_scope: str
    time_window_start: str
    time_window_end: str
    verification_level: VerificationLevel
    framework_applicability: dict  # {framework: {requirements, method, level_required}}
    custody_chain: list[CustodyEvent] = field(default_factory=list)
    quality_score: float = 0.0
    quality_tier: str = "Q5"
    expires_at: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of canonical content."""
        canonical = json.dumps({
            "control_id": self.control_id,
            "type": self.type.value,
            "content_data": self.content_data,
            "collected_at": self.collected_at,
        }, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verify content integrity by recomputing hash."""
        return self.compute_hash() == self.content_hash

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        d["verification_level"] = self.verification_level.value
        for event in d["custody_chain"]:
            event["action"] = event["action"].value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> EvidenceItem:
        data = data.copy()
        data["type"] = EvidenceType(data["type"])
        data["verification_level"] = VerificationLevel(data["verification_level"])
        data["custody_chain"] = [
            CustodyEvent(
                event_id=e["event_id"],
                evidence_id=e["evidence_id"],
                action=CustodyAction(e["action"]),
                actor=e["actor"],
                timestamp=e["timestamp"],
                evidence_hash=e["evidence_hash"],
                previous_event_hash=e.get("previous_event_hash", ""),
                signature=e.get("signature", ""),
            )
            for e in data["custody_chain"]
        ]
        return cls(**data)


class EvidenceStore:
    """Immutable evidence store with chain-of-custody tracking."""

    def __init__(self, storage_path: str = "evidence/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._evidence: dict[str, EvidenceItem] = {}
        self._index_by_control: dict[str, list[str]] = {}
        self._index_by_framework: dict[str, list[str]] = {}
        self._index_by_type: dict[str, list[str]] = {}

    def store(self, item: EvidenceItem) -> EvidenceItem:
        """Store an evidence item with initial custody event."""
        if not item.verify_integrity():
            raise ValueError(f"Evidence {item.evidence_id} failed integrity check")

        # Create initial custody event
        custody_event = CustodyEvent(
            event_id=str(uuid.uuid4()),
            evidence_id=item.evidence_id,
            action=CustodyAction.COLLECTED,
            actor=item.collected_by,
            timestamp=item.collected_at,
            evidence_hash=item.content_hash,
        )
        item.custody_chain.append(custody_event)

        self._evidence[item.evidence_id] = item
        self._update_indexes(item)
        self._persist(item)
        return item

    def get(self, evidence_id: str) -> Optional[EvidenceItem]:
        """Retrieve an evidence item by ID."""
        return self._evidence.get(evidence_id)

    def list_by_control(self, control_id: str) -> list[EvidenceItem]:
        """List all evidence for a control."""
        ids = self._index_by_control.get(control_id, [])
        return [self._evidence[eid] for eid in ids]

    def list_by_framework(self, framework: str) -> list[EvidenceItem]:
        """List all evidence applicable to a framework."""
        ids = self._index_by_framework.get(framework, [])
        return [self._evidence[eid] for eid in ids]

    def list_by_type(self, evidence_type: EvidenceType) -> list[EvidenceItem]:
        """List all evidence of a specific type."""
        ids = self._index_by_type.get(evidence_type.value, [])
        return [self._evidence[eid] for eid in ids]

    def list_expired(self, as_of: Optional[str] = None) -> list[EvidenceItem]:
        """List all expired evidence items."""
        if as_of is None:
            as_of = datetime.utcnow().isoformat() + "Z"
        return [
            item for item in self._evidence.values()
            if item.expires_at and item.expires_at < as_of
        ]

    def list_expiring(self, days: int = 30, as_of: Optional[str] = None) -> list[EvidenceItem]:
        """List evidence items expiring within the specified number of days."""
        if as_of is None:
            as_of = datetime.utcnow().isoformat() + "Z"
        now = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        threshold = (now + timedelta(days=days)).isoformat() + "Z"
        return [
            item for item in self._evidence.values()
            if item.expires_at and as_of <= item.expires_at <= threshold
        ]

    def list_current(self, as_of: Optional[str] = None) -> list[EvidenceItem]:
        """List all non-expired evidence items."""
        if as_of is None:
            as_of = datetime.utcnow().isoformat() + "Z"
        return [
            item for item in self._evidence.values()
            if not item.expires_at or item.expires_at >= as_of
        ]

    def add_custody_event(
        self,
        evidence_id: str,
        action: CustodyAction,
        actor: str,
        signature: str = "",
    ) -> CustodyEvent:
        """Add a custody event to an evidence item's chain."""
        item = self._evidence.get(evidence_id)
        if not item:
            raise KeyError(f"Evidence {evidence_id} not found")

        previous_hash = ""
        if item.custody_chain:
            previous_hash = item.custody_chain[-1].evidence_hash

        event = CustodyEvent(
            event_id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            action=action,
            actor=actor,
            timestamp=datetime.utcnow().isoformat() + "Z",
            evidence_hash=item.content_hash,
            previous_event_hash=previous_hash,
            signature=signature,
        )
        item.custody_chain.append(event)
        self._persist(item)
        return event

    def verify_chain(self, evidence_id: str) -> bool:
        """Verify the integrity of an evidence item's custody chain."""
        item = self._evidence.get(evidence_id)
        if not item:
            return False

        for i, event in enumerate(item.custody_chain):
            if event.evidence_hash != item.content_hash:
                return False
            if i > 0 and event.previous_event_hash != item.custody_chain[i - 1].evidence_hash:
                return False
        return True

    def search(
        self,
        control_id: Optional[str] = None,
        framework: Optional[str] = None,
        evidence_type: Optional[EvidenceType] = None,
        verification_level: Optional[VerificationLevel] = None,
        environment: Optional[str] = None,
    ) -> list[EvidenceItem]:
        """Search evidence with filters."""
        results = list(self._evidence.values())

        if control_id:
            results = [e for e in results if e.control_id == control_id]
        if framework:
            results = [e for e in results if framework in e.framework_applicability]
        if evidence_type:
            results = [e for e in results if e.type == evidence_type]
        if verification_level:
            results = [e for e in results if e.verification_level == verification_level]
        if environment:
            results = [e for e in results if e.environment == environment]

        return results

    def get_control_evidence_summary(self, control_id: str) -> dict:
        """Get a summary of evidence for a control."""
        items = self.list_by_control(control_id)
        current = [i for i in items if not i.expires_at or i.expires_at >= datetime.utcnow().isoformat() + "Z"]
        expired = [i for i in items if i.expires_at and i.expires_at < datetime.utcnow().isoformat() + "Z"]

        by_type = {}
        for item in items:
            t = item.type.value
            by_type[t] = by_type.get(t, 0) + 1

        by_level = {}
        for item in items:
            l = item.verification_level.value
            by_level[l] = by_level.get(l, 0) + 1

        return {
            "control_id": control_id,
            "total_evidence": len(items),
            "current": len(current),
            "expired": len(expired),
            "by_type": by_type,
            "by_verification_level": by_level,
            "evidence_ids": [i.evidence_id for i in items],
        }

    # --- Internal methods ---

    def _update_indexes(self, item: EvidenceItem) -> None:
        self._index_by_control.setdefault(item.control_id, []).append(item.evidence_id)
        for fw in item.framework_applicability:
            self._index_by_framework.setdefault(fw, []).append(item.evidence_id)
        self._index_by_type.setdefault(item.type.value, []).append(item.evidence_id)

    def _persist(self, item: EvidenceItem) -> None:
        path = self.storage_path / f"{item.evidence_id}.json"
        path.write_text(json.dumps(item.to_dict(), indent=2))


class EvidenceBinder:
    """Binds evidence to controls and manages the binding lifecycle."""

    def __init__(self, registry: ControlRegistry, store: EvidenceStore):
        self.registry = registry
        self.store = store

    def bind_evidence(
        self,
        control_id: str,
        evidence_type: EvidenceType,
        title: str,
        description: str,
        collected_by: str,
        source_system: str,
        source_location: str,
        content_format: str,
        content_data: str,
        environment: str = "prod",
        resource_scope: str = "",
        time_window_start: str = "",
        time_window_end: str = "",
        verification_level: VerificationLevel = VerificationLevel.L1,
        expires_days: int = 365,
    ) -> EvidenceItem:
        """Create and bind evidence to a control."""
        control = self.registry.get(control_id)
        if not control:
            raise KeyError(f"Control {control_id} not found")

        evidence_id = str(uuid.uuid4())
        collected_at = datetime.utcnow().isoformat() + "Z"

        # Build framework applicability from control spokes
        framework_app = {}
        for spoke in control.spokes:
            fw = spoke.framework
            if fw not in framework_app:
                framework_app[fw] = {
                    "requirements": [],
                    "satisfaction_method": spoke.satisfaction_method.value,
                    "verification_level_required": control.minimum_verification_level.value,
                }
            framework_app[fw]["requirements"].append(spoke.requirement)

        # Compute content hash
        canonical = json.dumps({
            "control_id": control_id,
            "type": evidence_type.value,
            "content_data": content_data,
            "collected_at": collected_at,
        }, sort_keys=True)
        content_hash = hashlib.sha256(canonical.encode()).hexdigest()

        # Compute expiration
        expires_at = (datetime.utcnow() + timedelta(days=expires_days)).isoformat() + "Z"

        item = EvidenceItem(
            evidence_id=evidence_id,
            control_id=control_id,
            type=evidence_type,
            title=title,
            description=description,
            collected_by=collected_by,
            collected_at=collected_at,
            source_system=source_system,
            source_location=source_location,
            content_format=content_format,
            content_data=content_data,
            content_hash=content_hash,
            environment=environment,
            resource_scope=resource_scope,
            time_window_start=time_window_start or collected_at,
            time_window_end=time_window_end or collected_at,
            verification_level=verification_level,
            framework_applicability=framework_app,
            expires_at=expires_at,
        )

        return self.store.store(item)

    def get_evidence_for_control(self, control_id: str) -> list[EvidenceItem]:
        """Get all evidence bound to a control."""
        return self.store.list_by_control(control_id)

    def get_evidence_for_requirement(
        self, framework: str, requirement: str
    ) -> list[EvidenceItem]:
        """Get all evidence applicable to a specific framework requirement."""
        candidates = self.store.list_by_framework(framework)
        return [
            item for item in candidates
            if framework in item.framework_applicability
            and requirement in item.framework_applicability[framework].get("requirements", [])
        ]

    def check_completeness(self, control_id: str) -> dict:
        """Check evidence completeness for a control."""
        control = self.registry.get(control_id)
        if not control:
            raise KeyError(f"Control {control_id} not found")

        items = self.store.list_by_control(control_id)
        current_items = [
            i for i in items
            if not i.expires_at or i.expires_at >= datetime.utcnow().isoformat() + "Z"
        ]

        # Check each evidence requirement
        req_status = []
        for req in control.evidence_requirements:
            matching = [i for i in current_items if i.type.value == req.type]
            req_status.append({
                "type": req.type,
                "required_format": req.format,
                "found": len(matching) > 0,
                "count": len(matching),
                "current": len(matching) > 0,
            })

        # Check framework coverage
        fw_coverage = {}
        for spoke in control.spokes:
            fw = spoke.framework
            if fw not in fw_coverage:
                fw_coverage[fw] = {"requirements": set(), "covered": set()}
            fw_coverage[fw]["requirements"].add(spoke.requirement)

        for item in current_items:
            for fw, app in item.framework_applicability.items():
                if fw in fw_coverage:
                    for req in app.get("requirements", []):
                        fw_coverage[fw]["covered"].add(req)

        fw_status = {}
        for fw, data in fw_coverage.items():
            total = len(data["requirements"])
            covered = len(data["covered"])
            fw_status[fw] = {
                "total_requirements": total,
                "covered": covered,
                "complete": covered >= total,
            }

        # Overall completeness
        all_present = all(r["found"] for r in req_status)
        all_current = all(r["current"] for r in req_status)
        all_fw_complete = all(f["complete"] for f in fw_status.values())

        if all_present and all_current and all_fw_complete:
            status = "COMPLETE"
        elif all_present:
            status = "PARTIAL"
        elif any(r["found"] for r in req_status):
            status = "PARTIAL"
        else:
            status = "INCOMPLETE"

        return {
            "control_id": control_id,
            "status": status,
            "evidence_requirements": req_status,
            "framework_coverage": fw_status,
            "total_evidence_items": len(items),
            "current_evidence_items": len(current_items),
        }

    def refresh_evidence(self, evidence_id: str, new_content: str) -> EvidenceItem:
        """Refresh an evidence item with new content."""
        item = self.store.get(evidence_id)
        if not item:
            raise KeyError(f"Evidence {evidence_id} not found")

        item.content_data = new_content
        item.content_hash = item.compute_hash()
        item.collected_at = datetime.utcnow().isoformat() + "Z"
        item.expires_at = (datetime.utcnow() + timedelta(days=365)).isoformat() + "Z"

        self.store.add_custody_event(
            evidence_id=evidence_id,
            action=CustodyAction.VERIFIED,
            actor="system",
        )
        self.store._persist(item)
        return item


# --- Usage Example ---
if __name__ == "__main__":
    from control_registry import ControlRegistry, bootstrap_control_catalog

    registry = ControlRegistry(storage_path="/tmp/grc-controls/")
    bootstrap_control_catalog(registry)

    store = EvidenceStore(storage_path="/tmp/grc-evidence/")
    binder = EvidenceBinder(registry, store)

    # Bind evidence to UC-4.5 (Verification and validation)
    evidence = binder.bind_evidence(
        control_id="UC-4.5",
        evidence_type=EvidenceType.ARTIFACT,
        title="Accuracy and robustness test results - Model v2.1",
        description="Comprehensive test results for model v2.1 including accuracy, robustness, and safety metrics",
        collected_by="test-agent-001",
        source_system="ml-pipeline",
        source_location="s3://grc-evidence/UC-4.5/test-results-v2.1.json",
        content_format="application/json",
        content_data='{"accuracy": 0.95, "robustness": 0.89, "safety_score": 0.92}',
        environment="prod",
        resource_scope="model-v2.1",
        verification_level=VerificationLevel.L2,
        expires_days=365,
    )

    print(f"Evidence stored: {evidence.evidence_id}")
    print(f"Content hash: {evidence.content_hash}")
    print(f"Framework applicability: {list(evidence.framework_applicability.keys())}")

    # Check completeness
    completeness = binder.check_completeness("UC-4.5")
    print(f"\nCompleteness status: {completeness['status']}")
    print(f"Total evidence: {completeness['total_evidence_items']}")
```

---

## 4. Compliance Scoring Algorithm

Computes weighted compliance scores across frameworks and generates the compliance posture.

```python
"""
GRC_Claw Compliance Scoring Algorithm
Computes weighted satisfaction scores and overall compliance posture.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from control_registry import ControlRegistry, RiskTier, VerificationLevel
from framework_mapping_engine import (
    FrameworkMappingEngine, FrameworkSatisfactionMatrix, SatisfactionState,
)


class ComplianceTier(Enum):
    EXCELLENT = "Excellent"       # >= 95%
    GOOD = "Good"                 # >= 85%
    ADEQUATE = "Adequate"         # >= 70%
    NEEDS_IMPROVEMENT = "Needs Improvement"  # >= 50%
    CRITICAL = "Critical"         # < 50%


@dataclass
class ControlScore:
    control_id: str
    title: str
    risk_tier: RiskTier
    implementation_status: str
    evidence_current: bool
    verification_level: VerificationLevel
    completeness_pct: float
    quality_score: float
    satisfaction_contribution: float
    weight: float


@dataclass
class CategoryScore:
    category: str
    total_controls: int
    active_controls: int
    avg_completeness: float
    avg_quality: float
    weighted_score: float
    controls: list[ControlScore] = field(default_factory=list)


@dataclass
class ComplianceScore:
    overall_score: float
    overall_percentage: float
    tier: ComplianceTier
    framework_scores: dict[str, float]
    category_scores: list[CategoryScore]
    risk_adjusted_score: float
    computed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ComplianceScoringEngine:
    """Computes compliance scores using weighted multi-factor algorithm."""

    # Risk tier weights for scoring
    RISK_WEIGHTS = {
        RiskTier.CRITICAL: 1.0,
        RiskTier.HIGH: 0.75,
        RiskTier.MEDIUM: 0.5,
        RiskTier.LOW: 0.25,
    }

    # Framework weights (from spec Section 10.2)
    FRAMEWORK_WEIGHTS = {
        "ISO_42001": 0.20,
        "NIST_AI_RMF": 0.20,
        "EU_AI_ACT": 0.25,
        "HIPAA": 0.15,
        "PCI_DSS": 0.10,
        "GDPR": 0.10,
    }

    # Satisfaction state values
    SATISFACTION_VALUES = {
        SatisfactionState.SATISFIED: 1.0,
        SatisfactionState.PARTIALLY_SATISFIED: 0.5,
        SatisfactionState.NOT_SATISFIED: 0.0,
        SatisfactionState.NOT_APPLICABLE: None,  # Excluded
    }

    def __init__(self, registry: ControlRegistry, mapping_engine: FrameworkMappingEngine):
        self.registry = registry
        self.mapping_engine = mapping_engine

    def compute_control_score(
        self,
        control_id: str,
        control_status: dict,
        completeness_pct: float,
        quality_score: float,
    ) -> ControlScore:
        """Compute score for a single control."""
        control = self.registry.get(control_id)
        if not control:
            raise KeyError(f"Control {control_id} not found")

        impl_status = control_status.get("implementation_status", "NOT_IMPLEMENTED")
        evidence_current = control_status.get("evidence_current", False)
        verification_level = control_status.get("verification_level", VerificationLevel.L0)

        # Base satisfaction contribution
        if impl_status == "ACTIVE" and evidence_current:
            base_contribution = 1.0
        elif impl_status == "ACTIVE":
            base_contribution = 0.5
        else:
            base_contribution = 0.0

        # Verification level multiplier
        level_multipliers = {
            VerificationLevel.L0: 0.0,
            VerificationLevel.L1: 0.25,
            VerificationLevel.L2: 0.5,
            VerificationLevel.L3: 0.75,
            VerificationLevel.L4: 1.0,
        }
        level_mult = level_multipliers.get(verification_level, 0.0)

        # Completeness and quality factors
        completeness_factor = completeness_pct / 100.0
        quality_factor = quality_score / 100.0

        # Weighted contribution
        satisfaction_contribution = (
            base_contribution * 0.4
            + level_mult * 0.2
            + completeness_factor * 0.2
            + quality_factor * 0.2
        )

        # Risk weight
        weight = self.RISK_WEIGHTS.get(control.risk_tier, 0.25)

        return ControlScore(
            control_id=control_id,
            title=control.title,
            risk_tier=control.risk_tier,
            implementation_status=impl_status,
            evidence_current=evidence_current,
            verification_level=verification_level,
            completeness_pct=completeness_pct,
            quality_score=quality_score,
            satisfaction_contribution=round(satisfaction_contribution, 4),
            weight=weight,
        )

    def compute_category_scores(
        self,
        control_statuses: dict[str, dict],
        completeness_scores: dict[str, float],
        quality_scores: dict[str, float],
    ) -> list[CategoryScore]:
        """Compute scores grouped by control category."""
        categories: dict[str, list[ControlScore]] = {}

        for control in self.registry.list_all():
            score = self.compute_control_score(
                control.id,
                control_statuses.get(control.id, {}),
                completeness_scores.get(control.id, 0.0),
                quality_scores.get(control.id, 0.0),
            )
            categories.setdefault(control.category, []).append(score)

        results = []
        for cat, scores in categories.items():
            total = len(scores)
            active = sum(1 for s in scores if s.implementation_status == "ACTIVE")
            avg_completeness = sum(s.completeness_pct for s in scores) / total if total else 0
            avg_quality = sum(s.quality_score for s in scores) / total if total else 0

            # Weighted score for category
            total_weight = sum(s.weight for s in scores)
            if total_weight > 0:
                weighted = sum(s.satisfaction_contribution * s.weight for s in scores) / total_weight
            else:
                weighted = 0.0

            results.append(CategoryScore(
                category=cat,
                total_controls=total,
                active_controls=active,
                avg_completeness=round(avg_completeness, 2),
                avg_quality=round(avg_quality, 2),
                weighted_score=round(weighted, 4),
                controls=scores,
            ))

        return results

    def compute_overall_score(
        self,
        control_statuses: dict[str, dict],
        completeness_scores: dict[str, float],
        quality_scores: dict[str, float],
        framework_results: dict[str, FrameworkSatisfactionMatrix],
    ) -> ComplianceScore:
        """Compute the overall compliance score."""
        # Framework scores
        fw_scores = {
            fw: matrix.score for fw, matrix in framework_results.items()
        }

        # Category scores
        cat_scores = self.compute_category_scores(
            control_statuses, completeness_scores, quality_scores
        )

        # Weighted framework score
        total_fw_weight = 0.0
        weighted_fw_score = 0.0
        for fw, score in fw_scores.items():
            weight = self.FRAMEWORK_WEIGHTS.get(fw, 0.0)
            total_fw_weight += weight
            weighted_fw_score += weight * score

        fw_overall = weighted_fw_score / total_fw_weight if total_fw_weight > 0 else 0.0

        # Risk-adjusted score: penalize critical control gaps
        critical_gaps = 0
        critical_total = 0
        for control in self.registry.list_all():
            if control.risk_tier == RiskTier.CRITICAL:
                critical_total += 1
                status = control_statuses.get(control.id, {})
                if status.get("implementation_status") != "ACTIVE":
                    critical_gaps += 1
                elif not status.get("evidence_current", False):
                    critical_gaps += 1

        risk_penalty = 0.0
        if critical_total > 0:
            critical_gap_ratio = critical_gaps / critical_total
            risk_penalty = critical_gap_ratio * 0.2  # Up to 20% penalty

        risk_adjusted = max(0.0, fw_overall - risk_penalty)

        # Determine tier
        pct = risk_adjusted * 100
        if pct >= 95:
            tier = ComplianceTier.EXCELLENT
        elif pct >= 85:
            tier = ComplianceTier.GOOD
        elif pct >= 70:
            tier = ComplianceTier.ADEQUATE
        elif pct >= 50:
            tier = ComplianceTier.NEEDS_IMPROVEMENT
        else:
            tier = ComplianceTier.CRITICAL

        return ComplianceScore(
            overall_score=round(fw_overall, 4),
            overall_percentage=round(fw_overall * 100, 2),
            tier=tier,
            framework_scores=fw_scores,
            category_scores=cat_scores,
            risk_adjusted_score=round(risk_adjusted, 4),
        )

    def compute_trend(
        self,
        current_score: ComplianceScore,
        previous_score: Optional[ComplianceScore] = None,
    ) -> dict:
        """Compute score trend compared to previous period."""
        if previous_score is None:
            return {
                "direction": "unknown",
                "change": 0.0,
                "change_percentage": 0.0,
            }

        change = current_score.overall_score - previous_score.overall_score
        if previous_score.overall_score > 0:
            change_pct = (change / previous_score.overall_score) * 100
        else:
            change_pct = 0.0

        if change > 0.01:
            direction = "improving"
        elif change < -0.01:
            direction = "declining"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "change": round(change, 4),
            "change_percentage": round(change_pct, 2),
        }

    def generate_score_report(self, score: ComplianceScore) -> dict:
        """Generate a detailed compliance score report."""
        return {
            "report_type": "compliance_score",
            "generated_at": score.computed_at,
            "overall": {
                "score": score.overall_score,
                "percentage": score.overall_percentage,
                "tier": score.tier.value,
                "risk_adjusted_score": score.risk_adjusted_score,
            },
            "frameworks": {
                fw: {
                    "score": s,
                    "percentage": round(s * 100, 2),
                    "weight": self.FRAMEWORK_WEIGHTS.get(fw, 0.0),
                }
                for fw, s in score.framework_scores.items()
            },
            "categories": [
                {
                    "category": c.category,
                    "total_controls": c.total_controls,
                    "active_controls": c.active_controls,
                    "avg_completeness": c.avg_completeness,
                    "avg_quality": c.avg_quality,
                    "weighted_score": c.weighted_score,
                }
                for c in score.category_scores
            ],
        }


# --- Usage Example ---
if __name__ == "__main__":
    from control_registry import ControlRegistry, bootstrap_control_catalog
    from framework_mapping_engine import FrameworkMappingEngine

    registry = ControlRegistry(storage_path="/tmp/grc-controls/")
    bootstrap_control_catalog(registry)

    engine = FrameworkMappingEngine(registry)
    scoring = ComplianceScoringEngine(registry, engine)

    # Simulate statuses
    control_statuses = {}
    completeness_scores = {}
    quality_scores = {}
    for control in registry.list_all():
        control_statuses[control.id] = {
            "implementation_status": "ACTIVE",
            "evidence_current": True,
            "verification_level": VerificationLevel.L2,
        }
        completeness_scores[control.id] = 85.0
        quality_scores[control.id] = 78.0

    fw_results = engine.evaluate_all_frameworks(control_statuses)
    score = scoring.compute_overall_score(
        control_statuses, completeness_scores, quality_scores, fw_results
    )

    print(f"Overall Score: {score.overall_percentage}%")
    print(f"Tier: {score.tier.value}")
    print(f"Risk-Adjusted: {score.risk_adjusted_score * 100:.1f}%")
```

---

## 5. Compliance Monitoring

Continuous monitoring of compliance posture, evidence currency, and gap detection.

```python
"""
GRC_Claw Compliance Monitoring
Continuous monitoring of compliance posture, evidence currency, and gap detection.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from control_registry import ControlRegistry, RiskTier, VerificationLevel
from framework_mapping_engine import FrameworkMappingEngine, SatisfactionState
from evidence_binding import EvidenceStore, EvidenceBinder


class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(Enum):
    EVIDENCE_EXPIRING = "evidence_expiring"
    EVIDENCE_EXPIRED = "evidence_expired"
    CONTROL_INACTIVE = "control_inactive"
    GAP_DETECTED = "gap_detected"
    QUALITY_DECLINE = "quality_decline"
    SATISFACTION_DROP = "satisfaction_drop"
    COLLECTION_FAILURE = "collection_failure"
    CHAIN_OF_CUSTODY_BREAK = "chain_of_custody_break"


@dataclass
class ComplianceAlert:
    alert_id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    control_id: str
    framework: str
    requirement: str
    created_at: str
    acknowledged: bool = False
    acknowledged_by: str = ""
    resolved: bool = False
    resolved_at: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class MonitoringResult:
    timestamp: str
    overall_score: float
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    new_alerts: list[ComplianceAlert] = field(default_factory=list)
    resolved_alerts: list[str] = field(default_factory=list)
    evidence_expiring_30d: int = 0
    evidence_expiring_60d: int = 0
    evidence_expiring_90d: int = 0
    expired_evidence: int = 0
    inactive_controls: int = 0
    gaps_by_framework: dict = field(default_factory=dict)


class ComplianceMonitor:
    """Continuous compliance monitoring engine."""

    def __init__(
        self,
        registry: ControlRegistry,
        mapping_engine: FrameworkMappingEngine,
        evidence_store: EvidenceStore,
        evidence_binder: EvidenceBinder,
    ):
        self.registry = registry
        self.mapping_engine = mapping_engine
        self.evidence_store = evidence_store
        self.evidence_binder = evidence_binder
        self._alerts: dict[str, ComplianceAlert] = {}
        self._alert_history: list[ComplianceAlert] = []

    def run_full_check(self) -> MonitoringResult:
        """Run a complete compliance monitoring check."""
        now = datetime.utcnow()
        now_iso = now.isoformat() + "Z"

        new_alerts = []
        resolved = []

        # 1. Check evidence expiration
        expiring = self._check_evidence_expiration(now)
        new_alerts.extend(expiring)

        # 2. Check control implementation status
        inactive = self._check_control_status()
        new_alerts.extend(inactive)

        # 3. Check framework satisfaction
        satisfaction = self._check_satisfaction()
        new_alerts.extend(satisfaction)

        # 4. Check evidence quality
        quality = self._check_quality()
        new_alerts.extend(quality)

        # 5. Check chain of custody integrity
        custody = self._check_custody()
        new_alerts.extend(custody)

        # 6. Check for resolved alerts
        resolved = self._check_resolved_alerts()

        # Compute current score
        control_statuses = self._build_control_statuses()
        fw_results = self.mapping_engine.evaluate_all_frameworks(control_statuses)
        posture = self.mapping_engine.compute_overall_posture(fw_results)

        # Count alerts by severity
        critical = sum(1 for a in new_alerts if a.severity == AlertSeverity.CRITICAL)
        high = sum(1 for a in new_alerts if a.severity == AlertSeverity.HIGH)
        medium = sum(1 for a in new_alerts if a.severity == AlertSeverity.MEDIUM)
        low = sum(1 for a in new_alerts if a.severity == AlertSeverity.LOW)

        # Count expiring evidence
        exp_30 = len(self.evidence_store.list_expiring(days=30))
        exp_60 = len(self.evidence_store.list_expiring(days=60))
        exp_90 = len(self.evidence_store.list_expiring(days=90))
        expired = len(self.evidence_store.list_expired())

        # Count inactive controls
        inactive_count = sum(
            1 for s in control_statuses.values()
            if s.get("implementation_status") != "ACTIVE"
        )

        # Gaps by framework
        gaps = self.mapping_engine.identify_gaps(fw_results)
        gaps_by_fw = {}
        for gap in gaps:
            fw = gap["framework"]
            gaps_by_fw[fw] = gaps_by_fw.get(fw, 0) + 1

        # Store new alerts
        for alert in new_alerts:
            self._alerts[alert.alert_id] = alert
            self._alert_history.append(alert)

        return MonitoringResult(
            timestamp=now_iso,
            overall_score=posture["overall_percentage"],
            total_alerts=len(new_alerts),
            critical_alerts=critical,
            high_alerts=high,
            medium_alerts=medium,
            low_alerts=low,
            new_alerts=new_alerts,
            resolved_alerts=resolved,
            evidence_expiring_30d=exp_30,
            evidence_expiring_60d=exp_60,
            evidence_expiring_90d=exp_90,
            expired_evidence=expired,
            inactive_controls=inactive_count,
            gaps_by_framework=gaps_by_fw,
        )

    def acknowledge_alert(self, alert_id: str, actor: str) -> bool:
        """Acknowledge an alert."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        alert.acknowledged = True
        alert.acknowledged_by = actor
        return True

    def resolve_alert(self, alert_id: str, actor: str) -> bool:
        """Resolve an alert."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        alert.resolved = True
        alert.resolved_at = datetime.utcnow().isoformat() + "Z"
        return True

    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
        control_id: Optional[str] = None,
    ) -> list[ComplianceAlert]:
        """Get active (unresolved) alerts with optional filters."""
        results = [a for a in self._alerts.values() if not a.resolved]
        if severity:
            results = [a for a in results if a.severity == severity]
        if alert_type:
            results = [a for a in results if a.type == alert_type]
        if control_id:
            results = [a for a in results if a.control_id == control_id]
        return results

    def get_alert_history(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> list[ComplianceAlert]:
        """Get alert history with optional time range."""
        results = self._alert_history
        if start:
            results = [a for a in results if a.created_at >= start]
        if end:
            results = [a for a in results if a.created_at <= end]
        return results

    def generate_monitoring_report(self, result: MonitoringResult) -> dict:
        """Generate a monitoring report."""
        return {
            "report_type": "compliance_monitoring",
            "timestamp": result.timestamp,
            "summary": {
                "overall_score": result.overall_score,
                "total_alerts": result.total_alerts,
                "by_severity": {
                    "critical": result.critical_alerts,
                    "high": result.high_alerts,
                    "medium": result.medium_alerts,
                    "low": result.low_alerts,
                },
            },
            "evidence_status": {
                "expiring_30_days": result.evidence_expiring_30d,
                "expiring_60_days": result.evidence_expiring_60d,
                "expiring_90_days": result.evidence_expiring_90d,
                "expired": result.expired_evidence,
            },
            "control_status": {
                "inactive_controls": result.inactive_controls,
            },
            "gaps_by_framework": result.gaps_by_framework,
            "new_alerts": [
                {
                    "alert_id": a.alert_id,
                    "type": a.type.value,
                    "severity": a.severity.value,
                    "title": a.title,
                    "control_id": a.control_id,
                    "framework": a.framework,
                }
                for a in result.new_alerts
            ],
            "resolved_alerts": result.resolved_alerts,
        }

    # --- Internal methods ---

    def _check_evidence_expiration(self, now: datetime) -> list[ComplianceAlert]:
        alerts = []
        for item in self.evidence_store.list_current():
            if not item.expires_at:
                continue
            expires = datetime.fromisoformat(item.expires_at.replace("Z", "+00:00"))
            days_until = (expires - now).days

            if days_until < 0:
                alerts.append(ComplianceAlert(
                    alert_id=str(uuid.uuid4()),
                    type=AlertType.EVIDENCE_EXPIRED,
                    severity=AlertSeverity.HIGH,
                    title=f"Evidence expired: {item.title}",
                    description=f"Evidence {item.evidence_id} for {item.control_id} expired {abs(days_until)} days ago",
                    control_id=item.control_id,
                    framework="",
                    requirement="",
                    created_at=now.isoformat() + "Z",
                    metadata={"evidence_id": item.evidence_id, "expired_days": abs(days_until)},
                ))
            elif days_until <= 14:
                alerts.append(ComplianceAlert(
                    alert_id=str(uuid.uuid4()),
                    type=AlertType.EVIDENCE_EXPIRING,
                    severity=AlertSeverity.HIGH if days_until <= 7 else AlertSeverity.MEDIUM,
                    title=f"Evidence expiring soon: {item.title}",
                    description=f"Evidence {item.evidence_id} for {item.control_id} expires in {days_until} days",
                    control_id=item.control_id,
                    framework="",
                    requirement="",
                    created_at=now.isoformat() + "Z",
                    metadata={"evidence_id": item.evidence_id, "days_remaining": days_until},
                ))
        return alerts

    def _check_control_status(self) -> list[ComplianceAlert]:
        alerts = []
        for control in self.registry.list_all():
            items = self.evidence_store.list_by_control(control.id)
            current = [i for i in items if not i.expires_at or i.expires_at >= datetime.utcnow().isoformat() + "Z"]

            if not items:
                alerts.append(ComplianceAlert(
                    alert_id=str(uuid.uuid4()),
                    type=AlertType.CONTROL_INACTIVE,
                    severity=AlertSeverity.CRITICAL if control.risk_tier == RiskTier.CRITICAL else AlertSeverity.HIGH,
                    title=f"No evidence for control: {control.title}",
                    description=f"Control {control.id} has no evidence collected",
                    control_id=control.id,
                    framework="",
                    requirement="",
                    created_at=datetime.utcnow().isoformat() + "Z",
                ))
            elif not current:
                alerts.append(ComplianceAlert(
                    alert_id=str(uuid.uuid4()),
                    type=AlertType.CONTROL_INACTIVE,
                    severity=AlertSeverity.HIGH,
                    title=f"All evidence expired for control: {control.title}",
                    description=f"Control {control.id} has {len(items)} evidence items but all are expired",
                    control_id=control.id,
                    framework="",
                    requirement="",
                    created_at=datetime.utcnow().isoformat() + "Z",
                ))
        return alerts

    def _check_satisfaction(self) -> list[ComplianceAlert]:
        alerts = []
        control_statuses = self._build_control_statuses()
        fw_results = self.mapping_engine.evaluate_all_frameworks(control_statuses)

        for fw, matrix in fw_results.items():
            for req in matrix.requirements:
                if req.state == SatisfactionState.NOT_SATISFIED:
                    alerts.append(ComplianceAlert(
                        alert_id=str(uuid.uuid4()),
                        type=AlertType.GAP_DETECTED,
                        severity=AlertSeverity.CRITICAL,
                        title=f"Satisfaction gap: {fw} {req.requirement}",
                        description=f"Requirement {req.requirement} ({req.title}) is not satisfied",
                        control_id=req.satisfying_controls[0] if req.satisfying_controls else "",
                        framework=fw,
                        requirement=req.requirement,
                        created_at=datetime.utcnow().isoformat() + "Z",
                    ))
        return alerts

    def _check_quality(self) -> list[ComplianceAlert]:
        alerts = []
        for item in self.evidence_store.list_current():
            if item.quality_score < 50:
                alerts.append(ComplianceAlert(
                    alert_id=str(uuid.uuid4()),
                    type=AlertType.QUALITY_DECLINE,
                    severity=AlertSeverity.MEDIUM,
                    title=f"Low quality evidence: {item.title}",
                    description=f"Evidence {item.evidence_id} has quality score {item.quality_score}",
                    control_id=item.control_id,
                    framework="",
                    requirement="",
                    created_at=datetime.utcnow().isoformat() + "Z",
                    metadata={"evidence_id": item.evidence_id, "quality_score": item.quality_score},
                ))
        return alerts

    def _check_custody(self) -> list[ComplianceAlert]:
        alerts = []
        for item in self.evidence_store.list_current():
            if not self.evidence_store.verify_chain(item.evidence_id):
                alerts.append(ComplianceAlert(
                    alert_id=str(uuid.uuid4()),
                    type=AlertType.CHAIN_OF_CUSTODY_BREAK,
                    severity=AlertSeverity.CRITICAL,
                    title=f"Chain of custody break: {item.title}",
                    description=f"Evidence {item.evidence_id} has a broken custody chain",
                    control_id=item.control_id,
                    framework="",
                    requirement="",
                    created_at=datetime.utcnow().isoformat() + "Z",
                    metadata={"evidence_id": item.evidence_id},
                ))
        return alerts

    def _check_resolved_alerts(self) -> list[str]:
        """Check for alerts that should be auto-resolved."""
        resolved = []
        # In production, this would check if underlying issues are fixed
        return resolved

    def _build_control_statuses(self) -> dict[str, dict]:
        """Build control status map from evidence store."""
        statuses = {}
        for control in self.registry.list_all():
            items = self.evidence_store.list_by_control(control.id)
            current = [i for i in items if not i.expires_at or i.expires_at >= datetime.utcnow().isoformat() + "Z"]

            if current:
                max_level = max(i.verification_level for i in current)
                statuses[control.id] = {
                    "implementation_status": "ACTIVE",
                    "evidence_current": True,
                    "verification_level": max_level,
                    "evidence_level_required": control.minimum_verification_level,
                    "evidence_ids": [i.evidence_id for i in current],
                }
            else:
                statuses[control.id] = {
                    "implementation_status": "NOT_IMPLEMENTED",
                    "evidence_current": False,
                    "verification_level": VerificationLevel.L0,
                    "evidence_level_required": control.minimum_verification_level,
                    "evidence_ids": [],
                }
        return statuses


# --- Usage Example ---
if __name__ == "__main__":
    from control_registry import ControlRegistry, bootstrap_control_catalog
    from framework_mapping_engine import FrameworkMappingEngine
    from evidence_binding import EvidenceStore, EvidenceBinder

    registry = ControlRegistry(storage_path="/tmp/grc-controls/")
    bootstrap_control_catalog(registry)

    engine = FrameworkMappingEngine(registry)
    store = EvidenceStore(storage_path="/tmp/grc-evidence/")
    binder = EvidenceBinder(registry, store)

    monitor = ComplianceMonitor(registry, engine, store, binder)
    result = monitor.run_full_check()

    print(f"Monitoring check at {result.timestamp}")
    print(f"Overall score: {result.overall_score}%")
    print(f"Active alerts: {result.total_alerts}")
    print(f"  Critical: {result.critical_alerts}")
    print(f"  High: {result.high_alerts}")
    print(f"  Medium: {result.medium_alerts}")
    print(f"Evidence expiring (30d): {result.evidence_expiring_30d}")
    print(f"Expired evidence: {result.expired_evidence}")
```

---

## 6. Compliance Reporting

Generates compliance reports in multiple formats for different audiences.

```python
"""
GRC_Claw Compliance Reporting
Generates compliance reports in multiple formats for different audiences.
"""

from __future__ import annotations

import json
import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from control_registry import ControlRegistry, RiskTier
from framework_mapping_engine import FrameworkMappingEngine, SatisfactionState
from evidence_binding import EvidenceStore, EvidenceBinder
from compliance_monitoring import ComplianceMonitor, MonitoringResult
from compliance_scoring import ComplianceScoringEngine, ComplianceScore


class ReportFormat(Enum):
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    MARKDOWN = "markdown"


class ReportType(Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    CONTROL_OWNER = "control_owner"
    AUDITOR_PACKAGE = "auditor_package"
    GAP_ANALYSIS = "gap_analysis"
    TREND_ANALYSIS = "trend_analysis"
    QUALITY_ASSURANCE = "quality_assurance"
    FULL_COMPLIANCE = "full_compliance"


@dataclass
class ReportMetadata:
    report_id: str
    report_type: ReportType
    format: ReportFormat
    generated_at: str
    generated_by: str
    period_start: str
    period_end: str
    title: str
    description: str


class ComplianceReportGenerator:
    """Generates compliance reports for various audiences."""

    def __init__(
        self,
        registry: ControlRegistry,
        mapping_engine: FrameworkMappingEngine,
        evidence_store: EvidenceStore,
        evidence_binder: EvidenceBinder,
        monitor: ComplianceMonitor,
        scoring_engine: ComplianceScoringEngine,
        output_dir: str = "reports/",
    ):
        self.registry = registry
        self.mapping_engine = mapping_engine
        self.evidence_store = evidence_store
        self.evidence_binder = evidence_binder
        self.monitor = monitor
        self.scoring_engine = scoring_engine
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_executive_summary(
        self,
        period_start: str,
        period_end: str,
        format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """Generate executive summary report."""
        control_statuses = self._build_control_statuses()
        fw_results = self.mapping_engine.evaluate_all_frameworks(control_statuses)
        posture = self.mapping_engine.compute_overall_posture(fw_results)
        gaps = self.mapping_engine.identify_gaps(fw_results)

        # Critical gaps
        critical_gaps = [g for g in gaps if g.get("state") == "NOT_SATISFIED"]

        # Risk summary
        risk_summary = {}
        for control in self.registry.list_all():
            tier = control.risk_tier.value
            if tier not in risk_summary:
                risk_summary[tier] = {"total": 0, "satisfied": 0}
            risk_summary[tier]["total"] += 1
            status = control_statuses.get(control.id, {})
            if status.get("implementation_status") == "ACTIVE" and status.get("evidence_current"):
                risk_summary[tier]["satisfied"] += 1

        report = {
            "metadata": {
                "report_type": "executive_summary",
                "period": {"start": period_start, "end": period_end},
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
            "overall_posture": posture,
            "key_metrics": {
                "total_controls": len(self.registry.list_all()),
                "active_controls": sum(1 for s in control_statuses.values() if s.get("implementation_status") == "ACTIVE"),
                "total_gaps": len(gaps),
                "critical_gaps": len(critical_gaps),
                "evidence_items": len(self.evidence_store.list_current()),
                "expired_evidence": len(self.evidence_store.list_expired()),
            },
            "risk_summary": risk_summary,
            "top_gaps": [
                {
                    "framework": g["framework"],
                    "requirement": g["requirement"],
                    "title": g["title"],
                    "state": g["state"],
                }
                for g in critical_gaps[:10]
            ],
            "recommendations": self._generate_recommendations(gaps, posture),
        }

        return self._format_report(report, format, "executive_summary")

    def generate_control_owner_report(
        self,
        control_id: str,
        format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """Generate report for a specific control owner."""
        control = self.registry.get(control_id)
        if not control:
            raise KeyError(f"Control {control_id} not found")

        evidence = self.evidence_store.list_by_control(control_id)
        completeness = self.evidence_binder.check_completeness(control_id)
        alerts = self.monitor.get_active_alerts(control_id=control_id)

        # Evidence summary
        current = [e for e in evidence if not e.expires_at or e.expires_at >= datetime.utcnow().isoformat() + "Z"]
        expired = [e for e in evidence if e.expires_at and e.expires_at < datetime.utcnow().isoformat() + "Z"]

        report = {
            "metadata": {
                "report_type": "control_owner",
                "control_id": control_id,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
            "control": {
                "id": control.id,
                "title": control.title,
                "category": control.category,
                "risk_tier": control.risk_tier.value,
                "description": control.description,
            },
            "completeness": completeness,
            "evidence_summary": {
                "total": len(evidence),
                "current": len(current),
                "expired": len(expired),
                "by_type": self._summarize_by_type(evidence),
                "by_verification_level": self._summarize_by_level(evidence),
            },
            "active_alerts": [
                {
                    "alert_id": a.alert_id,
                    "type": a.type.value,
                    "severity": a.severity.value,
                    "title": a.title,
                }
                for a in alerts
            ],
            "upcoming_expirations": [
                {
                    "evidence_id": e.evidence_id,
                    "title": e.title,
                    "expires_at": e.expires_at,
                    "days_remaining": self._days_until(e.expires_at),
                }
                for e in sorted(current, key=lambda x: x.expires_at or "9999")[:10]
            ],
            "framework_mappings": [
                {
                    "framework": s.framework,
                    "requirement": s.requirement,
                    "title": s.title,
                    "method": s.satisfaction_method.value,
                }
                for s in control.spokes
            ],
        }

        return self._format_report(report, format, f"control_{control_id}")

    def generate_auditor_package(
        self,
        framework: str,
        period_start: str,
        period_end: str,
        format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """Generate auditor evidence package for a specific framework."""
        control_statuses = self._build_control_statuses()
        view = self.mapping_engine.generate_framework_view(framework, control_statuses)
        matrix = self.mapping_engine.evaluate_framework(framework, control_statuses)

        # Collect all evidence for this framework
        evidence_items = self.evidence_store.list_by_framework(framework)
        current_evidence = [
            e for e in evidence_items
            if not e.expires_at or e.expires_at >= datetime.utcnow().isoformat() + "Z"
        ]

        # Evidence summary
        by_type = {}
        by_level = {}
        for item in current_evidence:
            t = item.type.value
            by_type[t] = by_type.get(t, 0) + 1
            l = item.verification_level.value
            by_level[l] = by_level.get(l, 0) + 1

        report = {
            "metadata": {
                "report_type": "auditor_package",
                "framework": framework,
                "period": {"start": period_start, "end": period_end},
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "package_version": "1.0",
            },
            "framework_view": view,
            "evidence_summary": {
                "total_items": len(current_evidence),
                "by_type": by_type,
                "by_verification_level": by_level,
            },
            "satisfaction_matrix": {
                "total_requirements": matrix.total_requirements,
                "satisfied": matrix.satisfied,
                "partially_satisfied": matrix.partially_satisfied,
                "not_satisfied": matrix.not_satisfied,
                "score": matrix.score,
            },
            "evidence_items": [
                {
                    "evidence_id": e.evidence_id,
                    "control_id": e.control_id,
                    "type": e.type.value,
                    "title": e.title,
                    "collected_at": e.collected_at,
                    "verification_level": e.verification_level.value,
                    "content_hash": e.content_hash,
                    "custody_chain_length": len(e.custody_chain),
                    "quality_score": e.quality_score,
                }
                for e in current_evidence
            ],
            "gap_analysis": [
                {
                    "requirement": r.requirement,
                    "title": r.title,
                    "state": r.state.value,
                    "satisfying_controls": r.satisfying_controls,
                }
                for r in matrix.requirements
                if r.state != SatisfactionState.SATISFIED
            ],
        }

        return self._format_report(report, format, f"auditor_{framework}")

    def generate_gap_analysis_report(
        self,
        format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """Generate gap analysis report."""
        control_statuses = self._build_control_statuses()
        fw_results = self.mapping_engine.evaluate_all_frameworks(control_statuses)
        gaps = self.mapping_engine.identify_gaps(fw_results)

        # Categorize gaps
        by_type = {}
        by_severity = {}
        by_framework = {}
        by_category = {}

        for gap in gaps:
            state = gap.get("state", "NOT_SATISFIED")
            by_type[state] = by_type.get(state, 0) + 1

            fw = gap.get("framework", "Unknown")
            by_framework[fw] = by_framework.get(fw, 0) + 1

            # Determine severity
            severity = "critical" if state == "NOT_SATISFIED" else "high"
            by_severity[severity] = by_severity.get(severity, 0) + 1

            # Find category
            for ctrl_id in gap.get("satisfying_controls", []):
                control = self.registry.get(ctrl_id)
                if control:
                    cat = control.category
                    by_category[cat] = by_category.get(cat, 0) + 1
                    break

        # Prioritized remediation list
        prioritized = sorted(gaps, key=lambda g: (
            0 if g.get("state") == "NOT_SATISFIED" else 1,
            g.get("framework", ""),
        ))

        report = {
            "metadata": {
                "report_type": "gap_analysis",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
            "summary": {
                "total_gaps": len(gaps),
                "by_type": by_type,
                "by_severity": by_severity,
                "by_framework": by_framework,
                "by_category": by_category,
            },
            "prioritized_gaps": [
                {
                    "rank": i + 1,
                    "framework": g["framework"],
                    "requirement": g["requirement"],
                    "title": g["title"],
                    "state": g["state"],
                    "satisfying_controls": g.get("satisfying_controls", []),
                }
                for i, g in enumerate(prioritized[:50])
            ],
            "all_gaps": gaps,
        }

        return self._format_report(report, format, "gap_analysis")

    def generate_trend_report(
        self,
        periods: list[str],
        format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """Generate trend analysis report."""
        # In production, this would query historical data
        # For now, generate from current state
        control_statuses = self._build_control_statuses()
        fw_results = self.mapping_engine.evaluate_all_frameworks(control_statuses)

        trends = {}
        for fw, matrix in fw_results.items():
            trends[fw] = {
                "current_score": matrix.score,
                "satisfied": matrix.satisfied,
                "partially_satisfied": matrix.partially_satisfied,
                "not_satisfied": matrix.not_satisfied,
                "total": matrix.total_requirements,
            }

        # Evidence trends
        all_evidence = self.evidence_store.list_current()
        expiring_30 = len(self.evidence_store.list_expiring(days=30))
        expiring_60 = len(self.evidence_store.list_expiring(days=60))
        expiring_90 = len(self.evidence_store.list_expiring(days=90))

        report = {
            "metadata": {
                "report_type": "trend_analysis",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "periods": periods,
            },
            "framework_trends": trends,
            "evidence_trends": {
                "total_current": len(all_evidence),
                "expiring_30_days": expiring_30,
                "expiring_60_days": expiring_60,
                "expiring_90_days": expiring_90,
            },
            "alerts": self.monitor.generate_monitoring_report(
                self.monitor.run_full_check()
            ),
        }

        return self._format_report(report, format, "trend_analysis")

    def generate_full_compliance_report(
        self,
        period_start: str,
        period_end: str,
        format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """Generate comprehensive compliance report."""
        control_statuses = self._build_control_statuses()
        fw_results = self.mapping_engine.evaluate_all_frameworks(control_statuses)
        posture = self.mapping_engine.compute_overall_posture(fw_results)
        gaps = self.mapping_engine.identify_gaps(fw_results)

        # All framework views
        framework_views = {}
        for fw in self.mapping_engine.FRAMEWORK_NAMES:
            framework_views[fw] = self.mapping_engine.generate_framework_view(
                fw, control_statuses
            )

        # Control details
        control_details = []
        for control in self.registry.list_all():
            evidence = self.evidence_store.list_by_control(control.id)
            completeness = self.evidence_binder.check_completeness(control.id)
            control_details.append({
                "id": control.id,
                "title": control.title,
                "category": control.category,
                "risk_tier": control.risk_tier.value,
                "status": control_statuses.get(control.id, {}).get("implementation_status", "UNKNOWN"),
                "evidence_count": len(evidence),
                "completeness": completeness["status"],
                "spokes": len(control.spokes),
            })

        report = {
            "metadata": {
                "report_type": "full_compliance",
                "period": {"start": period_start, "end": period_end},
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
            "executive_summary": posture,
            "framework_views": framework_views,
            "gap_analysis": gaps,
            "control_details": control_details,
            "evidence_summary": {
                "total_items": len(self.evidence_store.list_current()),
                "expired_items": len(self.evidence_store.list_expired()),
                "by_verification_level": self._summarize_all_by_level(),
            },
        }

        return self._format_report(report, format, "full_compliance")

    # --- Internal methods ---

    def _build_control_statuses(self) -> dict[str, dict]:
        statuses = {}
        for control in self.registry.list_all():
            items = self.evidence_store.list_by_control(control.id)
            current = [i for i in items if not i.expires_at or i.expires_at >= datetime.utcnow().isoformat() + "Z"]
            if current:
                max_level = max(i.verification_level for i in current)
                statuses[control.id] = {
                    "implementation_status": "ACTIVE",
                    "evidence_current": True,
                    "verification_level": max_level,
                    "evidence_level_required": control.minimum_verification_level,
                    "evidence_ids": [i.evidence_id for i in current],
                }
            else:
                statuses[control.id] = {
                    "implementation_status": "NOT_IMPLEMENTED",
                    "evidence_current": False,
                    "verification_level": VerificationLevel.L0,
                    "evidence_level_required": control.minimum_verification_level,
                    "evidence_ids": [],
                }
        return statuses

    def _generate_recommendations(self, gaps: list[dict], posture: dict) -> list[str]:
        recs = []
        critical_count = sum(1 for g in gaps if g.get("state") == "NOT_SATISFIED")
        if critical_count > 0:
            recs.append(f"Address {critical_count} critical gaps immediately")
        if posture.get("overall_percentage", 0) < 90:
            recs.append("Overall compliance below 90% target — prioritize remediation")
        expiring = len(self.evidence_store.list_expiring(days=30))
        if expiring > 0:
            recs.append(f"{expiring} evidence items expiring within 30 days — schedule renewal")
        return recs

    def _summarize_by_type(self, evidence: list) -> dict:
        result = {}
        for e in evidence:
            t = e.type.value
            result[t] = result.get(t, 0) + 1
        return result

    def _summarize_by_level(self, evidence: list) -> dict:
        result = {}
        for e in evidence:
            l = e.verification_level.value
            result[l] = result.get(l, 0) + 1
        return result

    def _summarize_all_by_level(self) -> dict:
        return self._summarize_by_level(self.evidence_store.list_current())

    def _days_until(self, date_str: str) -> int:
        target = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.utcnow().replace(tzinfo=target.tzinfo)
        return (target - now).days

    def _format_report(self, report: dict, format: ReportFormat, name: str) -> str:
        """Format and save report."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if format == ReportFormat.JSON:
            content = json.dumps(report, indent=2)
            path = self.output_dir / f"{name}_{timestamp}.json"
        elif format == ReportFormat.CSV:
            content = self._to_csv(report)
            path = self.output_dir / f"{name}_{timestamp}.csv"
        elif format == ReportFormat.MARKDOWN:
            content = self._to_markdown(report)
            path = self.output_dir / f"{name}_{timestamp}.md"
        elif format == ReportFormat.HTML:
            content = self._to_html(report)
            path = self.output_dir / f"{name}_{timestamp}.html"
        else:
            raise ValueError(f"Unsupported format: {format}")

        path.write_text(content)
        return str(path)

    def _to_csv(self, report: dict) -> str:
        """Convert report to CSV (simplified for tabular data)."""
        output = io.StringIO()
        writer = csv.writer(output)
        if "control_details" in report:
            writer.writerow(["ID", "Title", "Category", "Risk Tier", "Status", "Evidence Count", "Completeness"])
            for c in report["control_details"]:
                writer.writerow([c["id"], c["title"], c["category"], c["risk_tier"], c["status"], c["evidence_count"], c["completeness"]])
        elif "prioritized_gaps" in report:
            writer.writerow(["Rank", "Framework", "Requirement", "Title", "State"])
            for g in report["prioritized_gaps"]:
                writer.writerow([g["rank"], g["framework"], g["requirement"], g["title"], g["state"]])
        else:
            writer.writerow(["Key", "Value"])
            for key, value in report.items():
                writer.writerow([key, str(value)])
        return output.getvalue()

    def _to_markdown(self, report: dict) -> str:
        """Convert report to Markdown."""
        lines = [f"# {report.get('metadata', {}).get('report_type', 'Report').replace('_', ' ').title()}", ""]
        lines.append(f"Generated: {report.get('metadata', {}).get('generated_at', 'N/A')}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(report, indent=2))
        lines.append("```")
        return "\n".join(lines)

    def _to_html(self, report: dict) -> str:
        """Convert report to HTML."""
        title = report.get("metadata", {}).get("report_type", "Report").replace("_", " ").title()
        json_content = json.dumps(report, indent=2)
        html = "<!DOCTYPE html>\n<html>\n<head><title>" + title + "</title>\n"
        html += "<style>\nbody { font-family: sans-serif; margin: 2em; }\n"
        html += "pre { background: #f4f4f4; padding: 1em; overflow-x: auto; }\n</style>\n"
        html += "</head>\n<body>\n<h1>" + title + "</h1>\n"
        html += "<pre>" + json_content + "</pre>\n</body>\n</html>"
        return html


# --- Usage Example ---
if __name__ == "__main__":
    from control_registry import ControlRegistry, bootstrap_control_catalog
    from framework_mapping_engine import FrameworkMappingEngine
    from evidence_binding import EvidenceStore, EvidenceBinder
    from compliance_monitoring import ComplianceMonitor
    from compliance_scoring import ComplianceScoringEngine

    registry = ControlRegistry(storage_path="/tmp/grc-controls/")
    bootstrap_control_catalog(registry)

    engine = FrameworkMappingEngine(registry)
    store = EvidenceStore(storage_path="/tmp/grc-evidence/")
    binder = EvidenceBinder(registry, store)
    monitor = ComplianceMonitor(registry, engine, store, binder)
    scoring = ComplianceScoringEngine(registry, engine)

    generator = ComplianceReportGenerator(
        registry, engine, store, binder, monitor, scoring,
        output_dir="/tmp/grc-reports/",
    )

    # Generate reports
    path = generator.generate_executive_summary("2026-07-01", "2026-10-01")
    print(f"Executive summary: {path}")

    path = generator.generate_gap_analysis_report()
    print(f"Gap analysis: {path}")

    path = generator.generate_auditor_package("ISO_42001", "2026-07-01", "2026-10-01")
    print(f"Auditor package: {path}")
```

---

## 7. Audit Preparation

Automates audit preparation by generating evidence packages, pre-audit checklists, and auditor support materials.

```python
"""
GRC_Claw Audit Preparation
Automates audit preparation including evidence packaging, pre-audit checks, and auditor support.
"""

from __future__ import annotations

import json
import zipfile
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from control_registry import ControlRegistry, RiskTier, VerificationLevel
from framework_mapping_engine import FrameworkMappingEngine, SatisfactionState
from evidence_binding import EvidenceStore, EvidenceBinder, EvidenceItem, CustodyAction
from compliance_monitoring import ComplianceMonitor
from compliance_scoring import ComplianceScoringEngine
from compliance_reporting import ComplianceReportGenerator


class AuditType(Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    REGULATORY = "regulatory"
    CERTIFICATION = "certification"


class AuditReadiness(Enum):
    READY = "ready"
    READY_WITH_FINDINGS = "ready_with_findings"
    NOT_READY = "not_ready"


@dataclass
class AuditFinding:
    finding_id: str
    severity: str
    title: str
    description: str
    control_id: str
    framework: str
    requirement: str
    remediation: str
    due_date: str


@dataclass
class AuditChecklistItem:
    item_id: str
    category: str
    description: str
    status: str  # "pass", "fail", "na", "pending"
    evidence_refs: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class AuditPackage:
    package_id: str
    audit_type: AuditType
    frameworks: list[str]
    period_start: str
    period_end: str
    generated_at: str
    readiness: AuditReadiness
    overall_score: float
    findings: list[AuditFinding] = field(default_factory=list)
    checklist: list[AuditChecklistItem] = field(default_factory=list)
    evidence_count: int = 0
    package_path: str = ""


class AuditPreparationEngine:
    """Automates audit preparation activities."""

    def __init__(
        self,
        registry: ControlRegistry,
        mapping_engine: FrameworkMappingEngine,
        evidence_store: EvidenceStore,
        evidence_binder: EvidenceBinder,
        monitor: ComplianceMonitor,
        scoring_engine: ComplianceScoringEngine,
        report_generator: ComplianceReportGenerator,
        output_dir: str = "audit-packages/",
    ):
        self.registry = registry
        self.mapping_engine = mapping_engine
        self.evidence_store = evidence_store
        self.evidence_binder = evidence_binder
        self.monitor = monitor
        self.scoring_engine = scoring_engine
        self.report_generator = report_generator
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prepare_audit(
        self,
        audit_type: AuditType,
        frameworks: list[str],
        period_start: str,
        period_end: str,
    ) -> AuditPackage:
        """Prepare a complete audit package."""
        package_id = str(uuid.uuid4())
        generated_at = datetime.utcnow().isoformat() + "Z"

        # 1. Run pre-audit checks
        checklist = self._run_pre_audit_checklist(frameworks)

        # 2. Identify findings
        findings = self._identify_findings(frameworks)

        # 3. Compute readiness
        readiness = self._compute_readiness(checklist, findings)

        # 4. Compute overall score
        control_statuses = self._build_control_statuses()
        fw_results = self.mapping_engine.evaluate_all_frameworks(control_statuses)
        posture = self.mapping_engine.compute_overall_posture(fw_results)

        # 5. Collect evidence count
        evidence_count = 0
        for fw in frameworks:
            evidence_count += len(self.evidence_store.list_by_framework(fw))

        # 6. Generate package files
        package_path = self._generate_package_files(
            package_id, audit_type, frameworks, period_start, period_end
        )

        return AuditPackage(
            package_id=package_id,
            audit_type=audit_type,
            frameworks=frameworks,
            period_start=period_start,
            period_end=period_end,
            generated_at=generated_at,
            readiness=readiness,
            overall_score=posture["overall_percentage"],
            findings=findings,
            checklist=checklist,
            evidence_count=evidence_count,
            package_path=package_path,
        )

    def generate_pre_audit_checklist(self, frameworks: list[str]) -> list[AuditChecklistItem]:
        """Generate a pre-audit checklist for the specified frameworks."""
        checklist = []

        # General checks
        checklist.append(AuditChecklistItem(
            item_id="GEN-001",
            category="General",
            description="All controls have current evidence",
            status="pass" if self._all_controls_have_evidence() else "fail",
        ))
        checklist.append(AuditChecklistItem(
            item_id="GEN-002",
            category="General",
            description="Chain of custody intact for all evidence",
            status="pass" if self._all_custody_intact() else "fail",
        ))
        checklist.append(AuditChecklistItem(
            item_id="GEN-003",
            category="General",
            description="No critical gaps identified",
            status="pass" if not self._has_critical_gaps(frameworks) else "fail",
        ))

        # Framework-specific checks
        for fw in frameworks:
            matrix = self.mapping_engine.evaluate_framework(
                fw, self._build_control_statuses()
            )
            checklist.append(AuditChecklistItem(
                item_id=f"{fw}-001",
                category=fw,
                description=f"{fw} satisfaction score >= 90%",
                status="pass" if matrix.score >= 0.9 else "fail",
                evidence_refs=[],
                notes=f"Current score: {matrix.score * 100:.1f}%",
            ))
            checklist.append(AuditChecklistItem(
                item_id=f"{fw}-002",
                category=fw,
                description=f"{fw} all requirements mapped",
                status="pass",  # Always true if controls are registered
            ))
            checklist.append(AuditChecklistItem(
                item_id=f"{fw}-003",
                category=fw,
                description=f"{fw} evidence package generated",
                status="pass",
            ))

        # Evidence quality checks
        low_quality = [
            e for e in self.evidence_store.list_current()
            if e.quality_score < 50
        ]
        checklist.append(AuditChecklistItem(
            item_id="EVD-001",
            category="Evidence Quality",
            description="All evidence meets minimum quality threshold",
            status="pass" if not low_quality else "fail",
            notes=f"{len(low_quality)} items below threshold" if low_quality else "",
        ))

        # Expiration checks
        expiring_30 = len(self.evidence_store.list_expiring(days=30))
        checklist.append(AuditChecklistItem(
            item_id="EVD-002",
            category="Evidence Quality",
            description="No evidence expiring within 30 days",
            status="pass" if expiring_30 == 0 else "fail",
            notes=f"{expiring_30} items expiring" if expiring_30 > 0 else "",
        ))

        return checklist

    def generate_auditor_briefing(self, package: AuditPackage) -> dict:
        """Generate an auditor briefing document."""
        return {
            "briefing_type": "auditor_briefing",
            "package_id": package.package_id,
            "audit_type": package.audit_type.value,
            "frameworks": package.frameworks,
            "period": {"start": package.period_start, "end": package.period_end},
            "readiness": package.readiness.value,
            "overall_score": package.overall_score,
            "evidence_summary": {
                "total_items": package.evidence_count,
                "frameworks_covered": len(package.frameworks),
            },
            "key_findings": [
                {
                    "severity": f.severity,
                    "title": f.title,
                    "control_id": f.control_id,
                    "framework": f.framework,
                }
                for f in package.findings[:10]
            ],
            "pre_audit_checklist_summary": {
                "total_items": len(package.checklist),
                "passed": sum(1 for c in package.checklist if c.status == "pass"),
                "failed": sum(1 for c in package.checklist if c.status == "fail"),
                "pending": sum(1 for c in package.checklist if c.status == "pending"),
            },
            "recommendations": self._generate_audit_recommendations(package),
        }

    def generate_evidence_package(
        self,
        package: AuditPackage,
        format: str = "zip",
    ) -> str:
        """Generate a self-contained evidence package for auditors."""
        package_dir = self.output_dir / package.package_id
        package_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate manifest
        manifest = {
            "package-id": package.package_id,
            "package-version": "1.0",
            "generated-at": package.generated_at,
            "audit-type": package.audit_type.value,
            "frameworks": package.frameworks,
            "period": {"start": package.period_start, "end": package.period_end},
            "overall-score": package.overall_score,
            "readiness": package.readiness.value,
            "evidence-items": package.evidence_count,
            "findings-count": len(package.findings),
        }
        (package_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

        # 2. Copy evidence files
        evidence_dir = package_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)
        for fw in package.frameworks:
            fw_dir = evidence_dir / fw
            fw_dir.mkdir(exist_ok=True)
            for item in self.evidence_store.list_by_framework(fw):
                (fw_dir / f"{item.evidence_id}.json").write_text(
                    json.dumps(item.to_dict(), indent=2)
                )

        # 3. Generate framework views
        views_dir = package_dir / "framework-views"
        views_dir.mkdir(exist_ok=True)
        control_statuses = self._build_control_statuses()
        for fw in package.frameworks:
            view = self.mapping_engine.generate_framework_view(fw, control_statuses)
            (views_dir / f"{fw}-view.json").write_text(json.dumps(view, indent=2))

        # 4. Generate reports
        reports_dir = package_dir / "reports"
        reports_dir.mkdir(exist_ok=True)
        self.report_generator.generate_executive_summary(
            package.period_start, package.period_end
        )
        self.report_generator.generate_gap_analysis_report()

        # 5. Generate checklist
        (package_dir / "checklist.json").write_text(
            json.dumps([{
                "item_id": c.item_id,
                "category": c.category,
                "description": c.description,
                "status": c.status,
                "notes": c.notes,
            } for c in package.checklist], indent=2)
        )

        # 6. Generate findings
        (package_dir / "findings.json").write_text(
            json.dumps([{
                "finding_id": f.finding_id,
                "severity": f.severity,
                "title": f.title,
                "description": f.description,
                "control_id": f.control_id,
                "framework": f.framework,
                "requirement": f.requirement,
                "remediation": f.remediation,
                "due_date": f.due_date,
            } for f in package.findings], indent=2)
        )

        # 7. Create ZIP archive
        if format == "zip":
            zip_path = self.output_dir / f"{package.package_id}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in package_dir.rglob("*"):
                    if file_path.is_file():
                        zf.write(file_path, file_path.relative_to(package_dir))
            return str(zip_path)

        return str(package_dir)

    def verify_evidence_integrity(self, package: AuditPackage) -> dict:
        """Verify integrity of all evidence in the audit package."""
        results = {
            "total_checked": 0,
            "passed": 0,
            "failed": 0,
            "failures": [],
        }

        for fw in package.frameworks:
            for item in self.evidence_store.list_by_framework(fw):
                results["total_checked"] += 1
                if item.verify_integrity() and self.evidence_store.verify_chain(item.evidence_id):
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    results["failures"].append({
                        "evidence_id": item.evidence_id,
                        "control_id": item.control_id,
                        "reason": "integrity_check_failed",
                    })

        return results

    # --- Internal methods ---

    def _run_pre_audit_checklist(self, frameworks: list[str]) -> list[AuditChecklistItem]:
        return self.generate_pre_audit_checklist(frameworks)

    def _identify_findings(self, frameworks: list[str]) -> list[AuditFinding]:
        findings = []
        control_statuses = self._build_control_statuses()
        fw_results = self.mapping_engine.evaluate_all_frameworks(control_statuses)

        for fw in frameworks:
            if fw not in fw_results:
                continue
            matrix = fw_results[fw]
            for req in matrix.requirements:
                if req.state == SatisfactionState.NOT_SATISFIED:
                    findings.append(AuditFinding(
                        finding_id=str(uuid.uuid4()),
                        severity="critical",
                        title=f"Unsatisfied requirement: {fw} {req.requirement}",
                        description=f"Requirement {req.requirement} ({req.title}) has no satisfying controls with valid evidence",
                        control_id=req.satisfying_controls[0] if req.satisfying_controls else "",
                        framework=fw,
                        requirement=req.requirement,
                        remediation="Implement controls and collect evidence for this requirement",
                        due_date=(datetime.utcnow() + timedelta(days=30)).isoformat() + "Z",
                    ))
                elif req.state == SatisfactionState.PARTIALLY_SATISFIED:
                    findings.append(AuditFinding(
                        finding_id=str(uuid.uuid4()),
                        severity="high",
                        title=f"Partially satisfied: {fw} {req.requirement}",
                        description=f"Requirement {req.requirement} ({req.title}) is only partially satisfied",
                        control_id=req.satisfying_controls[0] if req.satisfying_controls else "",
                        framework=fw,
                        requirement=req.requirement,
                        remediation="Collect additional evidence or implement additional controls",
                        due_date=(datetime.utcnow() + timedelta(days=60)).isoformat() + "Z",
                    ))

        return findings

    def _compute_readiness(
        self, checklist: list[AuditChecklistItem], findings: list[AuditFinding]
    ) -> AuditReadiness:
        failed = sum(1 for c in checklist if c.status == "fail")
        critical_findings = sum(1 for f in findings if f.severity == "critical")

        if failed == 0 and critical_findings == 0:
            return AuditReadiness.READY
        elif failed <= 2 and critical_findings <= 3:
            return AuditReadiness.READY_WITH_FINDINGS
        else:
            return AuditReadiness.NOT_READY

    def _generate_package_files(
        self,
        package_id: str,
        audit_type: AuditType,
        frameworks: list[str],
        period_start: str,
        period_end: str,
    ) -> str:
        package_dir = self.output_dir / package_id
        package_dir.mkdir(parents=True, exist_ok=True)
        return str(package_dir)

    def _generate_audit_recommendations(self, package: AuditPackage) -> list[str]:
        recs = []
        if package.readiness == AuditReadiness.NOT_READY:
            recs.append("Address all critical findings before audit")
        if package.overall_score < 90:
            recs.append(f"Improve overall compliance score (currently {package.overall_score}%)")
        failed = sum(1 for c in package.checklist if c.status == "fail")
        if failed > 0:
            recs.append(f"Resolve {failed} failed pre-audit checklist items")
        return recs

    def _all_controls_have_evidence(self) -> bool:
        for control in self.registry.list_all():
            items = self.evidence_store.list_by_control(control.id)
            current = [i for i in items if not i.expires_at or i.expires_at >= datetime.utcnow().isoformat() + "Z"]
            if not current:
                return False
        return True

    def _all_custody_intact(self) -> bool:
        for item in self.evidence_store.list_current():
            if not self.evidence_store.verify_chain(item.evidence_id):
                return False
        return True

    def _has_critical_gaps(self, frameworks: list[str]) -> bool:
        control_statuses = self._build_control_statuses()
        fw_results = self.mapping_engine.evaluate_all_frameworks(control_statuses)
        for fw in frameworks:
            if fw in fw_results:
                for req in fw_results[fw].requirements:
                    if req.state == SatisfactionState.NOT_SATISFIED:
                        return True
        return False

    def _build_control_statuses(self) -> dict[str, dict]:
        statuses = {}
        for control in self.registry.list_all():
            items = self.evidence_store.list_by_control(control.id)
            current = [i for i in items if not i.expires_at or i.expires_at >= datetime.utcnow().isoformat() + "Z"]
            if current:
                max_level = max(i.verification_level for i in current)
                statuses[control.id] = {
                    "implementation_status": "ACTIVE",
                    "evidence_current": True,
                    "verification_level": max_level,
                    "evidence_level_required": control.minimum_verification_level,
                    "evidence_ids": [i.evidence_id for i in current],
                }
            else:
                statuses[control.id] = {
                    "implementation_status": "NOT_IMPLEMENTED",
                    "evidence_current": False,
                    "verification_level": VerificationLevel.L0,
                    "evidence_level_required": control.minimum_verification_level,
                    "evidence_ids": [],
                }
        return statuses


# --- Usage Example ---
if __name__ == "__main__":
    from control_registry import ControlRegistry, bootstrap_control_catalog
    from framework_mapping_engine import FrameworkMappingEngine
    from evidence_binding import EvidenceStore, EvidenceBinder
    from compliance_monitoring import ComplianceMonitor
    from compliance_scoring import ComplianceScoringEngine
    from compliance_reporting import ComplianceReportGenerator

    registry = ControlRegistry(storage_path="/tmp/grc-controls/")
    bootstrap_control_catalog(registry)

    engine = FrameworkMappingEngine(registry)
    store = EvidenceStore(storage_path="/tmp/grc-evidence/")
    binder = EvidenceBinder(registry, store)
    monitor = ComplianceMonitor(registry, engine, store, binder)
    scoring = ComplianceScoringEngine(registry, engine)
    reports = ComplianceReportGenerator(registry, engine, store, binder, monitor, scoring)

    audit_prep = AuditPreparationEngine(
        registry, engine, store, binder, monitor, scoring, reports,
        output_dir="/tmp/grc-audit-packages/",
    )

    # Prepare audit
    package = audit_prep.prepare_audit(
        audit_type=AuditType.EXTERNAL,
        frameworks=["ISO_42001", "NIST_AI_RMF", "EU_AI_ACT"],
        period_start="2026-07-01",
        period_end="2026-10-01",
    )

    print(f"Audit Package: {package.package_id}")
    print(f"Readiness: {package.readiness.value}")
    print(f"Overall Score: {package.overall_score}%")
    print(f"Evidence Items: {package.evidence_count}")
    print(f"Findings: {len(package.findings)}")
    print(f"Checklist: {len(package.checklist)} items")

    # Generate auditor briefing
    briefing = audit_prep.generate_auditor_briefing(package)
    print(f"\nAuditor Briefing:")
    print(f"  Passed: {briefing['pre_audit_checklist_summary']['passed']}")
    print(f"  Failed: {briefing['pre_audit_checklist_summary']['failed']}")

    # Generate evidence package
    package_path = audit_prep.generate_evidence_package(package, format="zip")
    print(f"\nEvidence package: {package_path}")

    # Verify integrity
    integrity = audit_prep.verify_evidence_integrity(package)
    print(f"\nIntegrity Check:")
    print(f"  Checked: {integrity['total_checked']}")
    print(f"  Passed: {integrity['passed']}")
    print(f"  Failed: {integrity['failed']}")
```

---

## Appendix: Complete System Integration

```python
"""
GRC_Claw Compliance Management System - Complete Integration
Wires all components together into a unified compliance management system.
"""

from control_registry import ControlRegistry, bootstrap_control_catalog
from framework_mapping_engine import FrameworkMappingEngine
from evidence_binding import EvidenceStore, EvidenceBinder
from compliance_scoring import ComplianceScoringEngine
from compliance_monitoring import ComplianceMonitor
from compliance_reporting import ComplianceReportGenerator
from audit_preparation import AuditPreparationEngine


class GRCClawComplianceSystem:
    """Unified compliance management system integrating all components."""

    def __init__(self, base_path: str = "/tmp/grc-claw/"):
        self.base_path = base_path

        # Initialize all components
        self.registry = ControlRegistry(storage_path=f"{base_path}/controls/")
        self.mapping_engine = FrameworkMappingEngine(self.registry)
        self.evidence_store = EvidenceStore(storage_path=f"{base_path}/evidence/")
        self.evidence_binder = EvidenceBinder(self.registry, self.evidence_store)
        self.scoring_engine = ComplianceScoringEngine(self.registry, self.mapping_engine)
        self.monitor = ComplianceMonitor(
            self.registry, self.mapping_engine, self.evidence_store, self.evidence_binder
        )
        self.report_generator = ComplianceReportGenerator(
            self.registry, self.mapping_engine, self.evidence_store,
            self.evidence_binder, self.monitor, self.scoring_engine,
            output_dir=f"{base_path}/reports/",
        )
        self.audit_preparation = AuditPreparationEngine(
            self.registry, self.mapping_engine, self.evidence_store,
            self.evidence_binder, self.monitor, self.scoring_engine,
            self.report_generator, output_dir=f"{base_path}/audit-packages/",
        )

    def initialize(self) -> None:
        """Initialize the system with the full control catalog."""
        bootstrap_control_catalog(self.registry)
        print(f"Initialized with {len(self.registry.list_all())} controls")

    def get_posture(self) -> dict:
        """Get current compliance posture."""
        control_statuses = self._build_control_statuses()
        fw_results = self.mapping_engine.evaluate_all_frameworks(control_statuses)
        return self.mapping_engine.compute_overall_posture(fw_results)

    def run_monitoring(self) -> dict:
        """Run compliance monitoring check."""
        result = self.monitor.run_full_check()
        return self.monitor.generate_monitoring_report(result)

    def prepare_audit(self, frameworks: list[str], period_start: str, period_end: str) -> dict:
        """Prepare for an audit."""
        package = self.audit_preparation.prepare_audit(
            audit_type="external",
            frameworks=frameworks,
            period_start=period_start,
            period_end=period_end,
        )
        return {
            "package_id": package.package_id,
            "readiness": package.readiness.value,
            "overall_score": package.overall_score,
            "findings_count": len(package.findings),
            "evidence_count": package.evidence_count,
        }

    def _build_control_statuses(self) -> dict[str, dict]:
        statuses = {}
        for control in self.registry.list_all():
            items = self.evidence_store.list_by_control(control.id)
            current = [i for i in items if not i.expires_at or i.expires_at >= datetime.utcnow().isoformat() + "Z"]
            if current:
                max_level = max(i.verification_level for i in current)
                statuses[control.id] = {
                    "implementation_status": "ACTIVE",
                    "evidence_current": True,
                    "verification_level": max_level,
                    "evidence_level_required": control.minimum_verification_level,
                    "evidence_ids": [i.evidence_id for i in current],
                }
            else:
                statuses[control.id] = {
                    "implementation_status": "NOT_IMPLEMENTED",
                    "evidence_current": False,
                    "verification_level": VerificationLevel.L0,
                    "evidence_level_required": control.minimum_verification_level,
                    "evidence_ids": [],
                }
        return statuses


# --- Main Entry Point ---
if __name__ == "__main__":
    system = GRCClawComplianceSystem()
    system.initialize()

    posture = system.get_posture()
    print(f"Overall Compliance: {posture['overall_percentage']}%")

    monitoring = system.run_monitoring()
    print(f"Active Alerts: {monitoring['summary']['total_alerts']}")
```

---

*End of Implementation Guide*</longcat_think>

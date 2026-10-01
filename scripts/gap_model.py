#!/usr/bin/env python3
"""
GRC_Claw Gap Management — Shared Data Model

Defines the canonical Gap dataclass, status enums, and serialization helpers
used by all gap management scripts (dashboard, detector, reporter, scorer, tracker).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class GapStatus(str, Enum):
    """Lifecycle status of a gap."""
    IDENTIFIED = "identified"
    ANALYZING = "analyzing"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    MITIGATED = "mitigated"
    CLOSED = "closed"
    DEFERRED = "deferred"
    ACCEPTED = "accepted"


class GapCategory(str, Enum):
    """Category of a gap."""
    PLATFORM = "platform"
    STANDARD = "standard"
    TOOLING = "tooling"
    FRAMEWORK = "framework"
    LANGUAGE = "language"
    PROCESS = "process"


class GapSeverity(str, Enum):
    """Severity level."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Valid status transitions
VALID_TRANSITIONS: dict[GapStatus, set[GapStatus]] = {
    GapStatus.IDENTIFIED: {GapStatus.ANALYZING, GapStatus.DEFERRED, GapStatus.ACCEPTED},
    GapStatus.ANALYZING: {GapStatus.PLANNED, GapStatus.DEFERRED, GapStatus.ACCEPTED},
    GapStatus.PLANNED: {GapStatus.IN_PROGRESS, GapStatus.DEFERRED, GapStatus.ACCEPTED},
    GapStatus.IN_PROGRESS: {GapStatus.IMPLEMENTING, GapStatus.PLANNED, GapStatus.DEFERRED},
    GapStatus.IMPLEMENTING: {GapStatus.VALIDATING, GapStatus.IN_PROGRESS},
    GapStatus.VALIDATING: {GapStatus.MITIGATED, GapStatus.IMPLEMENTING},
    GapStatus.MITIGATED: {GapStatus.CLOSED, GapStatus.VALIDATING},
    GapStatus.CLOSED: set(),
    GapStatus.DEFERRED: {GapStatus.IDENTIFIED, GapStatus.ANALYZING},
    GapStatus.ACCEPTED: {GapStatus.IDENTIFIED, GapStatus.ANALYZING},
}


@dataclass
class Gap:
    """Canonical representation of a governance gap."""
    id: str
    name: str
    description: str
    category: GapCategory
    impact: int  # 1-10
    feasibility: int  # 1-10
    priority_score: float  # impact * feasibility
    status: GapStatus = GapStatus.IDENTIFIED
    severity: GapSeverity = GapSeverity.MEDIUM
    owner: str = ""
    created_date: str = ""
    target_date: str = ""
    progress: int = 0  # 0-100
    remediation_plan: str = ""
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    last_updated: str = ""
    blueprint_ref: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now(timezone.utc).isoformat()
        if not self.last_updated:
            self.last_updated = self.created_date
        # Auto-compute priority score if not set
        if self.priority_score == 0 and self.impact and self.feasibility:
            self.priority_score = round(self.impact * self.feasibility, 1)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["category"] = self.category.value if isinstance(self.category, GapCategory) else self.category
        d["status"] = self.status.value if isinstance(self.status, GapStatus) else self.status
        d["severity"] = self.severity.value if isinstance(self.severity, GapSeverity) else self.severity
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Gap":
        d = dict(d)
        d.setdefault("description", "")
        d.setdefault("owner", "")
        d.setdefault("created_date", "")
        d.setdefault("target_date", "")
        d.setdefault("progress", 0)
        d.setdefault("remediation_plan", "")
        d.setdefault("dependencies", [])
        d.setdefault("tags", [])
        d.setdefault("notes", "")
        d.setdefault("last_updated", "")
        d.setdefault("blueprint_ref", "")
        d.setdefault("metrics", {})
        d["category"] = GapCategory(d.get("category", "tooling"))
        d["status"] = GapStatus(d.get("status", "identified"))
        d["severity"] = GapSeverity(d.get("severity", "medium"))
        return cls(**d)

    def can_transition_to(self, new_status: GapStatus) -> bool:
        return new_status in VALID_TRANSITIONS.get(self.status, set())


@dataclass
class RemediationAction:
    """A single remediation action for a gap."""
    id: str
    gap_id: str
    title: str
    description: str
    owner: str
    status: GapStatus = GapStatus.PLANNED
    priority: int = 5  # 1-10
    estimated_effort: str = ""  # e.g., "2 weeks", "40 hours"
    actual_effort: str = ""
    created_date: str = ""
    due_date: str = ""
    completed_date: str = ""
    progress: int = 0
    dependencies: list[str] = field(default_factory=list)
    deliverables: list[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, GapStatus) else self.status
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "RemediationAction":
        d = dict(d)
        d["status"] = GapStatus(d.get("status", "planned"))
        return cls(**d)


def load_gaps(path: str | Path) -> list[Gap]:
    """Load gaps from a JSON file."""
    p = Path(path)
    if not p.exists():
        return []
    with open(p) as f:
        data = json.load(f)
    if isinstance(data, list):
        return [Gap.from_dict(d) for d in data]
    if isinstance(data, dict) and "gaps" in data:
        return [Gap.from_dict(d) for d in data["gaps"]]
    return []


def save_gaps(gaps: list[Gap], path: str | Path) -> None:
    """Save gaps to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump([g.to_dict() for g in gaps], f, indent=2, default=str)


def load_actions(path: str | Path) -> list[RemediationAction]:
    """Load remediation actions from a JSON file."""
    p = Path(path)
    if not p.exists():
        return []
    with open(p) as f:
        data = json.load(f)
    if isinstance(data, list):
        return [RemediationAction.from_dict(d) for d in data]
    if isinstance(data, dict) and "actions" in data:
        return [RemediationAction.from_dict(d) for d in data["actions"]]
    return []


def save_actions(actions: list[RemediationAction], path: str | Path) -> None:
    """Save remediation actions to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump([a.to_dict() for a in actions], f, indent=2, default=str)


# Canonical gap registry — the 20 gaps from the blueprints
CANONICAL_GAPS: list[dict[str, Any]] = [
    {"id": "GAP-001", "name": "Unified Open-Source AI Governance Stack", "category": "platform", "impact": 10, "feasibility": 9.6, "priority_score": 96, "severity": "critical", "blueprint_ref": "grc-claw-gap-analysis.md#gap-1"},
    {"id": "GAP-002", "name": "Agentic AI Governance Standard", "category": "standard", "impact": 10, "feasibility": 9.3, "priority_score": 93, "severity": "critical", "blueprint_ref": "grc-claw-gap-analysis.md#gap-2"},
    {"id": "GAP-003", "name": "Universal AI Policy Language", "category": "language", "impact": 10, "feasibility": 9.0, "priority_score": 90, "severity": "critical", "blueprint_ref": "grc-claw-gap-analysis.md#gap-3"},
    {"id": "GAP-004", "name": "Unified CI/CD Compliance Framework", "category": "tooling", "impact": 9, "feasibility": 9.8, "priority_score": 88, "severity": "high", "blueprint_ref": "grc-claw-gap-analysis.md#gap-4"},
    {"id": "GAP-005", "name": "Standardized AI Governance Metrics", "category": "framework", "impact": 9, "feasibility": 9.6, "priority_score": 86, "severity": "high", "blueprint_ref": "grc-claw-gap-analysis.md#gap-5"},
    {"id": "GAP-006", "name": "Real-Time AI Risk Monitoring", "category": "tooling", "impact": 9, "feasibility": 9.3, "priority_score": 84, "severity": "high", "blueprint_ref": "grc-claw-gap-analysis.md#gap-6"},
    {"id": "GAP-007", "name": "AI Supply Chain Security (AI-SBOM)", "category": "standard", "impact": 9, "feasibility": 9.1, "priority_score": 82, "severity": "high", "blueprint_ref": "grc-claw-gap-analysis.md#gap-7"},
    {"id": "GAP-008", "name": "Automated Compliance Mapping", "category": "tooling", "impact": 8, "feasibility": 10.0, "priority_score": 80, "severity": "high", "blueprint_ref": "grc-claw-gap-analysis.md#gap-8"},
    {"id": "GAP-009", "name": "AI Incident Response Playbooks", "category": "process", "impact": 9, "feasibility": 8.7, "priority_score": 78, "severity": "high", "blueprint_ref": "grc-claw-gap-analysis.md#gap-9"},
    {"id": "GAP-010", "name": "Model Versioning with Governance State", "category": "tooling", "impact": 8, "feasibility": 9.5, "priority_score": 76, "severity": "high", "blueprint_ref": "grc-claw-gap-analysis.md#gap-10"},
    {"id": "GAP-011", "name": "Cross-Border AI Compliance Engine", "category": "tooling", "impact": 8, "feasibility": 9.3, "priority_score": 74, "severity": "medium", "blueprint_ref": "grc-claw-gap-analysis.md#gap-11"},
    {"id": "GAP-012", "name": "AI Audit Trail Standardization", "category": "standard", "impact": 8, "feasibility": 9.0, "priority_score": 72, "severity": "medium", "blueprint_ref": "grc-claw-gap-analysis.md#gap-12"},
    {"id": "GAP-013", "name": "Automated Bias and Fairness Testing", "category": "tooling", "impact": 8, "feasibility": 8.8, "priority_score": 70, "severity": "medium", "blueprint_ref": "grc-claw-gap-analysis.md#gap-13"},
    {"id": "GAP-014", "name": "AI Governance for Edge and IoT", "category": "platform", "impact": 7, "feasibility": 9.4, "priority_score": 66, "severity": "medium", "blueprint_ref": "grc-claw-gap-analysis.md#gap-14"},
    {"id": "GAP-015", "name": "Unified AI Asset Inventory", "category": "tooling", "impact": 8, "feasibility": 8.0, "priority_score": 64, "severity": "medium", "blueprint_ref": "grc-claw-gap-analysis.md#gap-15"},
    {"id": "GAP-016", "name": "Runtime AI Policy Enforcement", "category": "platform", "impact": 8, "feasibility": 7.8, "priority_score": 62, "severity": "medium", "blueprint_ref": "grc-claw-gap-analysis.md#gap-16"},
    {"id": "GAP-017", "name": "AI Vendor Risk Management", "category": "framework", "impact": 7, "feasibility": 8.6, "priority_score": 60, "severity": "medium", "blueprint_ref": "grc-claw-gap-analysis.md#gap-17"},
    {"id": "GAP-018", "name": "AI Governance Dashboard Standard", "category": "tooling", "impact": 7, "feasibility": 8.3, "priority_score": 58, "severity": "low", "blueprint_ref": "grc-claw-gap-analysis.md#gap-18"},
    {"id": "GAP-019", "name": "AI Regulatory Change Management", "category": "tooling", "impact": 7, "feasibility": 8.0, "priority_score": 56, "severity": "low", "blueprint_ref": "grc-claw-gap-analysis.md#gap-19"},
    {"id": "GAP-020", "name": "AI Governance Skills and Certification", "category": "framework", "impact": 6, "feasibility": 9.0, "priority_score": 54, "severity": "low", "blueprint_ref": "grc-claw-gap-analysis.md#gap-20"},
]


def initialize_gap_registry(path: str | Path) -> list[Gap]:
    """Create the canonical gap registry from blueprint data."""
    p = Path(path)
    if p.exists():
        return load_gaps(p)
    gaps = [Gap.from_dict(d) for d in CANONICAL_GAPS]
    save_gaps(gaps, p)
    return gaps

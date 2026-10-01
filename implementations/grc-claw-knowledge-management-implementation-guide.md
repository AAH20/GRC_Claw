# GRC_Claw Knowledge Management Implementation Guide

**Document ID:** GRC-KMS-IMPL-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Implementation Ready  
**References:** GRC-KMS-001 v2.0, GRC_Claw AI Training Framework v1.0

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Knowledge Capture Pipeline](#2-knowledge-capture-pipeline)
3. [Knowledge Storage (MongoDB/Neo4j)](#3-knowledge-storage)
4. [Knowledge Graph Analytics](#4-knowledge-graph-analytics)
5. [Knowledge Quality Scoring](#5-knowledge-quality-scoring)
6. [Knowledge Gap Analysis](#6-knowledge-gap-analysis)
7. [Knowledge Recommendation Engine](#7-knowledge-recommendation-engine)
8. [Knowledge Lifecycle Automation](#8-knowledge-lifecycle-automation)
9. [Integration & Deployment](#9-integration--deployment)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   GRC_Claw Knowledge Management Stack                     │
│                                                                           │
│  Capture → Validate → Classify → Store → Link → Analyze → Share → Apply │
│                                                                           │
│  Storage Layer:                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ MongoDB  │  │  Neo4j   │  │Elasticsearch│ │TimescaleDB│             │
│  │Artifacts │  │  Graph   │  │  Search   │  │ Metrics  │              │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
│                                                                           │
│  Processing Layer (Python):                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Capture  │  │ Quality  │  │   Gap    │  │Recommend │              │
│  │ Pipeline │  │ Scoring  │  │ Analysis │  │  Engine  │              │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                            │
│  │  Graph   │  │ Lifecycle│  │ Discovery│                            │
│  │Analytics │  │Automation│  │  Engine  │                            │
│  └──────────┘  └──────────┘  └──────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Artifact Store | MongoDB 7 | Flexible schema for heterogeneous artifacts |
| Knowledge Graph | Neo4j 5 | Relationship traversal and graph analytics |
| Search Index | Elasticsearch 8 | Full-text and semantic search |
| Metrics Store | TimescaleDB 2 | Time-series knowledge metrics |
| ML/Analytics | scikit-learn, networkx | Classification, clustering, centrality |
| Task Queue | Celery + Redis | Async pipeline processing |
| API Framework | FastAPI | REST API layer |

---

## 2. Knowledge Capture Pipeline

### 2.1 Core Data Models

```python
# models/knowledge_artifact.py
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    INCIDENT_LESSONS_LEARNED = "INCIDENT_LESSONS_LEARNED"
    AUDIT_FINDING = "AUDIT_FINDING"
    ASSESSMENT_RESULT = "ASSESSMENT_RESULT"
    POLICY_DECISION = "POLICY_DECISION"
    AGENT_BEHAVIOR_PATTERN = "AGENT_BEHAVIOR_PATTERN"
    BEST_PRACTICE = "BEST_PRACTICE"
    CROSS_ORG_INTELLIGENCE = "CROSS_ORG_INTELLIGENCE"


class Domain(str, Enum):
    INCIDENT = "INCIDENT"
    AUDIT = "AUDIT"
    ASSESSMENT = "ASSESSMENT"
    POLICY = "POLICY"
    AGENT_BEHAVIOR = "AGENT_BEHAVIOR"
    REGULATORY = "REGULATORY"
    BEST_PRACTICE = "BEST_PRACTICE"
    CROSS_ORG = "CROSS_ORG"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class LifecycleStage(str, Enum):
    IDENTIFIED = "identified"
    VALIDATED = "validated"
    CLASSIFIED = "classified"
    SHARED = "shared"
    APPLIED = "applied"
    ARCHIVED = "archived"
    RETIRED = "retired"


class ClassificationLevel(str, Enum):
    L1 = "L1"  # Public
    L2 = "L2"  # Internal
    L3 = "L3"  # Confidential
    L4 = "L4"  # Restricted


class RetentionClass(str, Enum):
    EPHEMERAL = "ephemeral"
    STANDARD = "standard"
    EXTENDED = "extended"
    PERMANENT = "permanent"


class KnowledgeLinks(BaseModel):
    related_policies: list[str] = Field(default_factory=list)
    related_controls: list[str] = Field(default_factory=list)
    related_agents: list[str] = Field(default_factory=list)
    related_datasets: list[str] = Field(default_factory=list)
    related_incidents: list[str] = Field(default_factory=list)
    related_assessments: list[str] = Field(default_factory=list)
    related_audits: list[str] = Field(default_factory=list)
    related_artifacts: list[str] = Field(default_factory=list)
    related_regulations: list[str] = Field(default_factory=list)


class Lineage(BaseModel):
    source_event_id: str
    source_event_type: str
    captured_by: str
    captured_at: datetime
    validated_by: Optional[str] = None
    validated_at: Optional[datetime] = None
    version: int = 1


class Governance(BaseModel):
    classification: ClassificationLevel
    data_owner: str
    data_steward: str
    retention_class: RetentionClass
    retention_until: Optional[datetime] = None
    legal_hold: bool = False
    legal_hold_reason: Optional[str] = None


class Sharing(BaseModel):
    visibility: str = "private"  # private | team | organization | public
    shared_with: list[str] = Field(default_factory=list)
    anonymized: bool = False
    shared_at: Optional[datetime] = None


class Metrics(BaseModel):
    view_count: int = 0
    search_count: int = 0
    application_count: int = 0
    last_accessed_at: Optional[datetime] = None


class KnowledgeArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artifact_type: ArtifactType
    title: str
    description: str = ""
    domain: Domain
    type: str
    severity: Severity
    lifecycle_stage: LifecycleStage = LifecycleStage.IDENTIFIED
    content: dict[str, Any] = Field(default_factory=dict)
    knowledge_links: KnowledgeLinks = Field(default_factory=KnowledgeLinks)
    lineage: Lineage
    governance: Governance
    sharing: Sharing = Field(default_factory=Sharing)
    metrics: Metrics = Field(default_factory=Metrics)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    updated_by: str

    def to_mongo_doc(self) -> dict:
        """Convert to MongoDB document format."""
        return self.model_dump(mode="json")

    @classmethod
    def from_mongo_doc(cls, doc: dict) -> "KnowledgeArtifact":
        """Create from MongoDB document."""
        return cls(**doc)
```

### 2.2 Capture Pipeline

```python
# pipeline/capture_pipeline.py
from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from models.knowledge_artifact import (
    ArtifactType,
    ClassificationLevel,
    Domain,
    Governance,
    KnowledgeArtifact,
    KnowledgeLinks,
    LifecycleStage,
    Lineage,
    RetentionClass,
    Severity,
)

logger = logging.getLogger(__name__)


class CaptureSource(ABC):
    """Abstract base class for knowledge capture sources."""

    @abstractmethod
    def extract(self, source_event: dict[str, Any]) -> dict[str, Any]:
        """Extract structured knowledge from source event."""
        ...

    @abstractmethod
    def validate_completeness(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate that all required fields are present."""
        ...


class IncidentCaptureSource(CaptureSource):
    """Captures knowledge from AI incident events."""

    REQUIRED_FIELDS = [
        "incident_id", "title", "severity", "category",
        "root_cause", "impact", "remediation", "lessons_learned",
    ]

    def extract(self, source_event: dict[str, Any]) -> dict[str, Any]:
        return {
            "artifact_type": ArtifactType.INCIDENT_LESSONS_LEARNED,
            "title": source_event["title"],
            "description": source_event.get("description", ""),
            "domain": Domain.INCIDENT,
            "type": source_event["category"],
            "severity": Severity(source_event["severity"]),
            "content": {
                "incident_id": source_event["incident_id"],
                "detection": source_event.get("detection", {}),
                "impact": source_event.get("impact", {}),
                "root_cause": source_event.get("root_cause", {}),
                "remediation": source_event.get("remediation", {}),
                "lessons_learned": source_event.get("lessons_learned", {}),
            },
            "knowledge_links": KnowledgeLinks(
                related_incidents=[source_event["incident_id"]],
                related_policies=source_event.get("related_policies", []),
                related_controls=source_event.get("related_controls", []),
                related_agents=source_event.get("related_agents", []),
                related_datasets=source_event.get("related_datasets", []),
            ),
        }

    def validate_completeness(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        missing = [f for f in self.REQUIRED_FIELDS if f not in data or not data[f]]
        return len(missing) == 0, missing


class AuditCaptureSource(CaptureSource):
    """Captures knowledge from audit findings."""

    REQUIRED_FIELDS = [
        "audit_id", "title", "audit_type", "framework",
        "control_id", "severity", "finding", "remediation",
    ]

    def extract(self, source_event: dict[str, Any]) -> dict[str, Any]:
        return {
            "artifact_type": ArtifactType.AUDIT_FINDING,
            "title": source_event["title"],
            "description": source_event.get("description", ""),
            "domain": Domain.AUDIT,
            "type": source_event.get("finding_type", "control_gap"),
            "severity": Severity(source_event["severity"]),
            "content": {
                "audit_id": source_event["audit_id"],
                "audit_type": source_event["audit_type"],
                "framework": source_event["framework"],
                "control_id": source_event["control_id"],
                "finding": source_event.get("finding", {}),
                "remediation": source_event.get("remediation", {}),
            },
            "knowledge_links": KnowledgeLinks(
                related_audits=[source_event["audit_id"]],
                related_controls=[source_event["control_id"]],
                related_policies=source_event.get("related_policies", []),
                related_incidents=source_event.get("related_incidents", []),
            ),
        }

    def validate_completeness(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        missing = [f for f in self.REQUIRED_FIELDS if f not in data or not data[f]]
        return len(missing) == 0, missing


class AssessmentCaptureSource(CaptureSource):
    """Captures knowledge from governance assessments."""

    REQUIRED_FIELDS = [
        "assessment_id", "title", "assessment_type",
        "methodology", "scope", "results",
    ]

    def extract(self, source_event: dict[str, Any]) -> dict[str, Any]:
        return {
            "artifact_type": ArtifactType.ASSESSMENT_RESULT,
            "title": source_event["title"],
            "description": source_event.get("description", ""),
            "domain": Domain.ASSESSMENT,
            "type": source_event["assessment_type"],
            "severity": Severity(source_event.get("risk_level", "medium")),
            "content": {
                "assessment_id": source_event["assessment_id"],
                "assessment_type": source_event["assessment_type"],
                "methodology": source_event["methodology"],
                "scope": source_event.get("scope", {}),
                "results": source_event.get("results", {}),
                "maturity_indicators": source_event.get("maturity_indicators", {}),
                "recommendations": source_event.get("recommendations", []),
            },
            "knowledge_links": KnowledgeLinks(
                related_assessments=[source_event["assessment_id"]],
                related_policies=source_event.get("related_policies", []),
                related_incidents=source_event.get("related_incidents", []),
            ),
        }

    def validate_completeness(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        missing = [f for f in self.REQUIRED_FIELDS if f not in data or not data[f]]
        return len(missing) == 0, missing


class PolicyDecisionCaptureSource(CaptureSource):
    """Captures knowledge from policy decisions."""

    REQUIRED_FIELDS = [
        "policy_id", "title", "decision_type", "decision",
    ]

    def extract(self, source_event: dict[str, Any]) -> dict[str, Any]:
        return {
            "artifact_type": ArtifactType.POLICY_DECISION,
            "title": source_event["title"],
            "description": source_event.get("description", ""),
            "domain": Domain.POLICY,
            "type": source_event["decision_type"],
            "severity": Severity(source_event.get("severity", "medium")),
            "content": {
                "policy_id": source_event["policy_id"],
                "decision_type": source_event["decision_type"],
                "decision": source_event.get("decision", {}),
                "context": source_event.get("context", {}),
            },
            "knowledge_links": KnowledgeLinks(
                related_policies=[source_event["policy_id"]],
                related_incidents=source_event.get("related_incidents", []),
                related_audits=source_event.get("related_audits", []),
                related_assessments=source_event.get("related_assessments", []),
            ),
        }

    def validate_completeness(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        missing = [f for f in self.REQUIRED_FIELDS if f not in data or not data[f]]
        return len(missing) == 0, missing


class AgentBehaviorCaptureSource(CaptureSource):
    """Captures knowledge from agent monitoring."""

    REQUIRED_FIELDS = [
        "agent_id", "title", "pattern_type", "pattern",
    ]

    def extract(self, source_event: dict[str, Any]) -> dict[str, Any]:
        return {
            "artifact_type": ArtifactType.AGENT_BEHAVIOR_PATTERN,
            "title": source_event["title"],
            "description": source_event.get("description", ""),
            "domain": Domain.AGENT_BEHAVIOR,
            "type": source_event["pattern_type"],
            "severity": Severity(source_event.get("risk_level", "medium")),
            "content": {
                "agent_id": source_event["agent_id"],
                "pattern_type": source_event["pattern_type"],
                "pattern": source_event.get("pattern", {}),
                "context": source_event.get("context", {}),
                "assessment": source_event.get("assessment", {}),
            },
            "knowledge_links": KnowledgeLinks(
                related_agents=[source_event["agent_id"]],
                related_policies=source_event.get("related_policies", []),
                related_incidents=source_event.get("related_incidents", []),
            ),
        }

    def validate_completeness(self, data: dict[str, Any]) -> tuple[bool, list[str]]:
        missing = [f for f in self.REQUIRED_FIELDS if f not in data or not data[f]]
        return len(missing) == 0, missing


# Source registry
CAPTURE_SOURCES: dict[str, type[CaptureSource]] = {
    "incident": IncidentCaptureSource,
    "audit": AuditCaptureSource,
    "assessment": AssessmentCaptureSource,
    "policy_decision": PolicyDecisionCaptureSource,
    "agent_behavior": AgentBehaviorCaptureSource,
}
```

### 2.3 Quality Gate Engine

```python
# pipeline/quality_gates.py
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from models.knowledge_artifact import KnowledgeArtifact


@dataclass
class GateResult:
    gate_id: str
    name: str
    passed: bool
    message: str
    blocking: bool = True
    details: dict[str, Any] = field(default_factory=dict)


class QualityGateEngine:
    """Validates knowledge artifacts against quality gates G1-G6."""

    PLACEHOLDER_PATTERNS = re.compile(
        r"\b(TBD|TODO|XXX|FIXME|N/?A|placeholder|lorem ipsum)\b",
        re.IGNORECASE,
    )

    def __init__(self, artifact_store, graph_client):
        self.artifact_store = artifact_store
        self.graph_client = graph_client

    def run_all_gates(self, artifact: KnowledgeArtifact) -> list[GateResult]:
        """Run all quality gates and return results."""
        return [
            self._gate_g1_completeness(artifact),
            self._gate_g2_classification(artifact),
            self._gate_g3_linkage(artifact),
            self._gate_g4_actionability(artifact),
            self._gate_g5_deduplication(artifact),
            self._gate_g6_temporal_integrity(artifact),
        ]

    def validate(self, artifact: KnowledgeArtifact) -> tuple[bool, list[GateResult]]:
        """Run all gates and return overall pass/fail."""
        results = self.run_all_gates(artifact)
        blocking_failures = [r for r in results if not r.passed and r.blocking]
        return len(blocking_failures) == 0, results

    def _gate_g1_completeness(self, artifact: KnowledgeArtifact) -> GateResult:
        """G1: All required fields populated, no placeholder text."""
        issues = []

        # Check required top-level fields
        if not artifact.title or len(artifact.title.strip()) < 5:
            issues.append("Title too short or empty")

        if not artifact.description or len(artifact.description.strip()) < 10:
            issues.append("Description too short or empty")

        # Check content fields based on artifact type
        content = artifact.content
        if not content:
            issues.append("Content is empty")

        # Check for placeholder text in all string values
        placeholder_count = self._count_placeholders(artifact.model_dump())
        if placeholder_count > 0:
            issues.append(f"Found {placeholder_count} placeholder values")

        # Check type-specific required fields
        if artifact.artifact_type.value == "INCIDENT_LESSONS_LEARNED":
            rc = content.get("root_cause", {})
            if not rc.get("description"):
                issues.append("Root cause description missing")
            rem = content.get("remediation", {})
            if not rem.get("immediate_actions"):
                issues.append("Immediate actions missing")

        passed = len(issues) == 0
        return GateResult(
            gate_id="G1",
            name="Completeness",
            passed=passed,
            message="All required fields populated" if passed else "; ".join(issues),
            blocking=True,
            details={"issues": issues, "placeholder_count": placeholder_count},
        )

    def _gate_g2_classification(self, artifact: KnowledgeArtifact) -> GateResult:
        """G2: Data classification assigned per Data Governance Spec."""
        gov = artifact.governance
        issues = []

        if not gov.classification:
            issues.append("Data classification not assigned")

        if not gov.retention_class:
            issues.append("Retention class not assigned")

        if not gov.data_owner:
            issues.append("Data owner not assigned")

        passed = len(issues) == 0
        return GateResult(
            gate_id="G2",
            name="Classification",
            passed=passed,
            message="Classification complete" if passed else "; ".join(issues),
            blocking=True,
            details={"issues": issues},
        )

    def _gate_g3_linkage(self, artifact: KnowledgeArtifact) -> GateResult:
        """G3: At least one link to a related policy, control, or artifact."""
        links = artifact.knowledge_links
        issues = []

        has_policy_link = len(links.related_policies) > 0
        has_control_link = len(links.related_controls) > 0
        has_artifact_link = (
            len(links.related_artifacts) > 0
            or len(links.related_incidents) > 0
            or len(links.related_audits) > 0
            or len(links.related_assessments) > 0
        )

        if not (has_policy_link or has_control_link or has_artifact_link):
            issues.append("No links to related policies, controls, or artifacts")

        # Source event must be linked
        if not artifact.lineage.source_event_id:
            issues.append("Source event not linked")

        passed = len(issues) == 0
        return GateResult(
            gate_id="G3",
            name="Linkage",
            passed=passed,
            message="Linkage requirements met" if passed else "; ".join(issues),
            blocking=True,
            details={
                "issues": issues,
                "has_policy_link": has_policy_link,
                "has_control_link": has_control_link,
                "has_artifact_link": has_artifact_link,
            },
        )

    def _gate_g4_actionability(self, artifact: KnowledgeArtifact) -> GateResult:
        """G4: Lessons learned and audit findings have remediation owner and due date."""
        issues = []
        content = artifact.content

        if artifact.artifact_type.value in (
            "INCIDENT_LESSONS_LEARNED",
            "AUDIT_FINDING",
        ):
            rem = content.get("remediation", {})
            if not rem.get("owner"):
                issues.append("Remediation owner not assigned")
            if not rem.get("due_date"):
                issues.append("Remediation due date not set")

        passed = len(issues) == 0
        return GateResult(
            gate_id="G4",
            name="Actionability",
            passed=passed,
            message="Actionability requirements met" if passed else "; ".join(issues),
            blocking=False,  # Flag, don't block
            details={"issues": issues},
        )

    def _gate_g5_deduplication(self, artifact: KnowledgeArtifact) -> GateResult:
        """G5: No duplicate artifact exists for same event."""
        issues = []

        # Check for existing artifact with same source event
        existing = self.artifact_store.find_by_source_event(
            artifact.lineage.source_event_id,
            artifact.artifact_type.value,
        )
        if existing and existing.artifact_id != artifact.artifact_id:
            issues.append(
                f"Duplicate artifact exists: {existing.artifact_id} "
                f"for source event {artifact.lineage.source_event_id}"
            )

        passed = len(issues) == 0
        return GateResult(
            gate_id="G5",
            name="Deduplication",
            passed=passed,
            message="No duplicates found" if passed else "; ".join(issues),
            blocking=True,
            details={"issues": issues},
        )

    def _gate_g6_temporal_integrity(self, artifact: KnowledgeArtifact) -> GateResult:
        """G6: Timestamps are consistent (capture time >= event time)."""
        issues = []
        now = datetime.now(timezone.utc)

        if artifact.lineage.captured_at > now:
            issues.append("Capture timestamp is in the future")

        if artifact.created_at > now:
            issues.append("Created timestamp is in the future")

        if artifact.lineage.validated_at and artifact.lineage.validated_at < artifact.lineage.captured_at:
            issues.append("Validation timestamp before capture timestamp")

        passed = len(issues) == 0
        return GateResult(
            gate_id="G6",
            name="Temporal Integrity",
            passed=passed,
            message="Temporal integrity verified" if passed else "; ".join(issues),
            blocking=True,
            details={"issues": issues},
        )

    def _count_placeholders(self, data: Any) -> int:
        """Recursively count placeholder values in data."""
        count = 0
        if isinstance(data, str):
            count += len(self.PLACEHOLDER_PATTERNS.findall(data))
        elif isinstance(data, dict):
            for v in data.values():
                count += self._count_placeholders(v)
        elif isinstance(data, list):
            for item in data:
                count += self._count_placeholders(item)
        return count
```

### 2.4 Capture Pipeline Orchestrator

```python
# pipeline/capture_orchestrator.py
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from models.knowledge_artifact import (
    ClassificationLevel,
    Governance,
    KnowledgeArtifact,
    LifecycleStage,
    Lineage,
    RetentionClass,
)
from pipeline.capture_pipeline import CAPTURE_SOURCES
from pipeline.quality_gates import QualityGateEngine, GateResult

logger = logging.getLogger(__name__)


class CapturePipeline:
    """Orchestrates the knowledge capture pipeline."""

    def __init__(
        self,
        artifact_store,
        graph_client,
        search_index,
        quality_engine: QualityGateEngine,
    ):
        self.artifact_store = artifact_store
        self.graph_client = graph_client
        self.search_index = search_index
        self.quality_engine = quality_engine

    def capture(
        self,
        source_type: str,
        source_event: dict[str, Any],
        captured_by: str,
        auto_classify: bool = True,
    ) -> tuple[Optional[KnowledgeArtifact], list[GateResult]]:
        """
        Execute the full capture pipeline.

        Returns:
            Tuple of (artifact, gate_results). Artifact is None if blocking gates fail.
        """
        # Step 1: Get the appropriate capture source
        source_class = CAPTURE_SOURCES.get(source_type)
        if not source_class:
            raise ValueError(f"Unknown capture source: {source_type}")

        source = source_class()

        # Step 2: Extract structured knowledge
        extracted = source.extract(source_event)

        # Step 3: Validate completeness at source level
        is_complete, missing = source.validate_completeness(source_event)
        if not is_complete:
            logger.warning(f"Source event incomplete, missing: {missing}")

        # Step 4: Build the artifact
        artifact = KnowledgeArtifact(
            artifact_type=extracted["artifact_type"],
            title=extracted["title"],
            description=extracted.get("description", ""),
            domain=extracted["domain"],
            type=extracted["type"],
            severity=extracted["severity"],
            lifecycle_stage=LifecycleStage.IDENTIFIED,
            content=extracted["content"],
            knowledge_links=extracted["knowledge_links"],
            lineage=Lineage(
                source_event_id=source_event.get("id", source_event.get("incident_id", "")),
                source_event_type=source_type.upper(),
                captured_by=captured_by,
                captured_at=datetime.now(timezone.utc),
            ),
            governance=Governance(
                classification=ClassificationLevel.L2,  # Default to internal
                data_owner=captured_by,
                data_steward=captured_by,
                retention_class=RetentionClass.STANDARD,
            ),
            created_by=captured_by,
            updated_by=captured_by,
        )

        # Step 5: Run quality gates
        passed, gate_results = self.quality_engine.validate(artifact)

        if not passed:
            blocking = [r for r in gate_results if not r.passed and r.blocking]
            logger.error(f"Artifact failed quality gates: {[r.gate_id for r in blocking]}")
            # Store as draft for manual review
            artifact.metadata["capture_status"] = "draft"
            artifact.metadata["gate_failures"] = [r.model_dump() for r in blocking]
            self.artifact_store.save_draft(artifact)
            return None, gate_results

        # Step 6: Auto-classify if enabled
        if auto_classify:
            artifact = self._auto_classify(artifact)

        # Step 7: Store artifact
        artifact.lifecycle_stage = LifecycleStage.VALIDATED
        self.artifact_store.save(artifact)

        # Step 8: Index for search
        self.search_index.index_artifact(artifact)

        # Step 9: Add to knowledge graph
        self.graph_client.add_artifact_node(artifact)
        self._create_graph_relationships(artifact)

        logger.info(f"Artifact captured successfully: {artifact.artifact_id}")
        return artifact, gate_results

    def _auto_classify(self, artifact: KnowledgeArtifact) -> KnowledgeArtifact:
        """Auto-classify artifact using rules and ML."""
        # Rule-based classification
        if artifact.severity.value == "critical":
            artifact.governance.classification = ClassificationLevel.L3
            artifact.governance.retention_class = RetentionClass.EXTENDED
        elif artifact.severity.value == "high":
            artifact.governance.classification = ClassificationLevel.L2
            artifact.governance.retention_class = RetentionClass.STANDARD

        # Set retention date based on class
        retention_years = {
            RetentionClass.EPHEMERAL: 0,
            RetentionClass.STANDARD: 7,
            RetentionClass.EXTENDED: 10,
            RetentionClass.PERMANENT: 100,
        }
        years = retention_years.get(artifact.governance.retention_class, 7)
        if years > 0:
            from datetime import timedelta
            artifact.governance.retention_until = datetime.now(timezone.utc) + timedelta(days=365 * years)

        return artifact

    def _create_graph_relationships(self, artifact: KnowledgeArtifact) -> None:
        """Create graph relationships for the artifact."""
        links = artifact.knowledge_links

        for policy_id in links.related_policies:
            self.graph_client.create_relationship(
                artifact.artifact_id, "KnowledgeArtifact",
                policy_id, "Policy",
                "RELATES_TO",
            )

        for control_id in links.related_controls:
            self.graph_client.create_relationship(
                artifact.artifact_id, "KnowledgeArtifact",
                control_id, "Control",
                "TESTS",
            )

        for agent_id in links.related_agents:
            self.graph_client.create_relationship(
                artifact.artifact_id, "KnowledgeArtifact",
                agent_id, "Agent",
                "INVOLVES",
            )

        for incident_id in links.related_incidents:
            self.graph_client.create_relationship(
                artifact.artifact_id, "KnowledgeArtifact",
                incident_id, "Incident",
                "INFORMED_BY",
            )

        for assessment_id in links.related_assessments:
            self.graph_client.create_relationship(
                artifact.artifact_id, "KnowledgeArtifact",
                assessment_id, "Assessment",
                "INFORMED_BY",
            )

        for audit_id in links.related_audits:
            self.graph_client.create_relationship(
                artifact.artifact_id, "KnowledgeArtifact",
                audit_id, "Audit",
                "INFORMED_BY",
            )
```

---

## 3. Knowledge Storage

### 3.1 MongoDB Storage Layer

```python
# storage/mongodb_store.py
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from pymongo import ASCENDING, MongoClient, IndexModel
from pymongo.collection import Collection
from pymongo.database import Database

from models.knowledge_artifact import KnowledgeArtifact

logger = logging.getLogger(__name__)


class MongoDBKnowledgeStore:
    """MongoDB-backed knowledge artifact storage."""

    def __init__(self, connection_string: str = "mongodb://localhost:27017", database: str = "grc_claw"):
        self.client = MongoClient(connectionString)
        self.db: Database = self.client[database]
        self.artifacts: Collection = self.db.knowledge_artifacts
        self.drafts: Collection = self.db.knowledge_artifacts_drafts
        self.archive: Collection = self.db.knowledge_artifacts_archive
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Create required indexes."""
        indexes = [
            IndexModel([("artifact_id", ASCENDING)], unique=True),
            IndexModel([("artifact_type", ASCENDING)]),
            IndexModel([("domain", ASCENDING)]),
            IndexModel([("severity", ASCENDING)]),
            IndexModel([("lifecycle_stage", ASCENDING)]),
            IndexModel([("lineage.source_event_id", ASCENDING)]),
            IndexModel([("lineage.captured_at", ASCENDING)]),
            IndexModel([("governance.retention_until", ASCENDING)]),
            IndexModel([("governance.legal_hold", ASCENDING)]),
            IndexModel([("knowledge_links.related_policies", ASCENDING)]),
            IndexModel([("knowledge_links.related_incidents", ASCENDING)]),
            IndexModel([("knowledge_links.related_controls", ASCENDING)]),
            IndexModel([("title", "text"), ("description", "text")]),
        ]
        self.artifacts.create_indexes(indexes)

    def save(self, artifact: KnowledgeArtifact) -> str:
        """Save a knowledge artifact."""
        doc = artifact.to_mongo_doc()
        doc["_id"] = artifact.artifact_id
        self.artifacts.replace_one(
            {"artifact_id": artifact.artifact_id},
            doc,
            upsert=True,
        )
        return artifact.artifact_id

    def save_draft(self, artifact: KnowledgeArtifact) -> str:
        """Save a draft artifact (failed quality gates)."""
        doc = artifact.to_mongo_doc()
        doc["_id"] = artifact.artifact_id
        self.drafts.replace_one(
            {"artifact_id": artifact.artifact_id},
            doc,
            upsert=True,
        )
        return artifact.artifact_id

    def get(self, artifact_id: str) -> Optional[KnowledgeArtifact]:
        """Retrieve an artifact by ID."""
        doc = self.artifacts.find_one({"artifact_id": artifact_id})
        if doc:
            return KnowledgeArtifact.from_mongo_doc(doc)
        return None

    def find_by_source_event(
        self, source_event_id: str, artifact_type: Optional[str] = None
    ) -> Optional[KnowledgeArtifact]:
        """Find artifact by source event ID."""
        query: dict[str, Any] = {"lineage.source_event_id": source_event_id}
        if artifact_type:
            query["artifact_type"] = artifact_type
        doc = self.artifacts.find_one(query)
        if doc:
            return KnowledgeArtifact.from_mongo_doc(doc)
        return None

    def search(
        self,
        query: Optional[str] = None,
        domain: Optional[str] = None,
        artifact_type: Optional[str] = None,
        severity: Optional[str] = None,
        lifecycle_stage: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 20,
        skip: int = 0,
    ) -> list[KnowledgeArtifact]:
        """Search artifacts with filters."""
        filter_query: dict[str, Any] = {}

        if domain:
            filter_query["domain"] = domain
        if artifact_type:
            filter_query["artifact_type"] = artifact_type
        if severity:
            filter_query["severity"] = severity
        if lifecycle_stage:
            filter_query["lifecycle_stage"] = lifecycle_stage
        if date_from or date_to:
            filter_query["lineage.captured_at"] = {}
            if date_from:
                filter_query["lineage.captured_at"]["$gte"] = date_from
            if date_to:
                filter_query["lineage.captured_at"]["$lte"] = date_to

        cursor = self.artifacts.find(filter_query).skip(skip).limit(limit)

        if query:
            # Text search
            text_results = self.artifacts.find(
                {"$text": {"$search": query}, **filter_query}
            ).skip(skip).limit(limit)
            return [KnowledgeArtifact.from_mongo_doc(d) for d in text_results]

        return [KnowledgeArtifact.from_mongo_doc(d) for d in cursor]

    def update_lifecycle_stage(
        self, artifact_id: str, new_stage: str, updated_by: str
    ) -> bool:
        """Update the lifecycle stage of an artifact."""
        result = self.artifacts.update_one(
            {"artifact_id": artifact_id},
            {
                "$set": {
                    "lifecycle_stage": new_stage,
                    "updated_at": datetime.now(timezone.utc),
                    "updated_by": updated_by,
                },
                "$inc": {"lineage.version": 1},
            },
        )
        return result.modified_count > 0

    def archive(self, artifact_id: str, reason: str) -> bool:
        """Move artifact to archive collection."""
        doc = self.artifacts.find_one({"artifact_id": artifact_id})
        if not doc:
            return False

        doc["archived_at"] = datetime.now(timezone.utc)
        doc["archive_reason"] = reason
        self.archive.insert_one(doc)
        self.artifacts.delete_one({"artifact_id": artifact_id})
        return True

    def find_expired(self, before_date: Optional[datetime] = None) -> list[KnowledgeArtifact]:
        """Find artifacts past their retention date."""
        if before_date is None:
            before_date = datetime.now(timezone.utc)

        cursor = self.artifacts.find(
            {
                "governance.retention_until": {"$lt": before_date},
                "lifecycle_stage": {"$nin": ["archived", "retired"]},
                "governance.legal_hold": False,
            }
        )
        return [KnowledgeArtifact.from_mongo_doc(d) for d in cursor]

    def get_version_history(self, artifact_id: str) -> list[dict]:
        """Get version history for an artifact."""
        # In production, use a separate versions collection
        doc = self.artifacts.find_one({"artifact_id": artifact_id})
        if doc:
            return [doc.get("lineage", {})]
        return []
```

### 3.2 Neo4j Graph Storage

```python
# storage/neo4j_graph.py
from __future__ import annotations

import logging
from typing import Any, Optional

from neo4j import GraphDatabase, Driver

from models.knowledge_artifact import KnowledgeArtifact

logger = logging.getLogger(__name__)


class Neo4jKnowledgeGraph:
    """Neo4j-backed knowledge graph storage."""

    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.driver: Driver = GraphDatabase.driver(uri, auth=(user, password))
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create constraints and indexes."""
        with self.driver.session() as session:
            # Constraints
            session.run(
                "CREATE CONSTRAINT artifact_id IF NOT EXISTS "
                "FOR (a:KnowledgeArtifact) REQUIRE a.artifact_id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT policy_id IF NOT EXISTS "
                "FOR (p:Policy) REQUIRE p.policy_id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT control_id IF NOT EXISTS "
                "FOR (c:Control) REQUIRE c.control_id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT agent_id IF NOT EXISTS "
                "FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT incident_id IF NOT EXISTS "
                "FOR (i:Incident) REQUIRE i.incident_id IS UNIQUE"
            )

    def close(self) -> None:
        self.driver.close()

    def add_artifact_node(self, artifact: KnowledgeArtifact) -> None:
        """Add a knowledge artifact node to the graph."""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (a:KnowledgeArtifact {artifact_id: $artifact_id})
                SET a.artifact_type = $artifact_type,
                    a.title = $title,
                    a.severity = $severity,
                    a.domain = $domain,
                    a.lifecycle_stage = $lifecycle_stage,
                    a.created_at = $created_at,
                    a.quality_score = $quality_score
                """,
                {
                    "artifact_id": artifact.artifact_id,
                    "artifact_type": artifact.artifact_type.value,
                    "title": artifact.title,
                    "severity": artifact.severity.value,
                    "domain": artifact.domain.value,
                    "lifecycle_stage": artifact.lifecycle_stage.value,
                    "created_at": artifact.created_at.isoformat(),
                    "quality_score": artifact.metadata.get("quality_score", 0),
                },
            )

    def create_relationship(
        self,
        source_id: str,
        source_label: str,
        target_id: str,
        target_label: str,
        rel_type: str,
        properties: Optional[dict] = None,
    ) -> None:
        """Create a relationship between two nodes."""
        props = properties or {}
        prop_string = ", ".join(f"{k}: ${k}" for k in props) if props else ""

        query = f"""
            MATCH (s:{source_label} {{id: $source_id}})
            MATCH (t:{target_label} {{id: $target_id}})
            MERGE (s)-[r:{rel_type}]->(t)
            {f"SET {prop_string}" if prop_string else ""}
        """

        params = {"source_id": source_id, "target_id": target_id, **props}

        with self.driver.session() as session:
            session.run(query, params)

    def find_similar_artifacts(
        self, artifact_id: str, threshold: float = 0.8, limit: int = 10
    ) -> list[dict]:
        """Find similar artifacts using graph proximity."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a:KnowledgeArtifact {artifact_id: $artifact_id})
                MATCH (a)-[:RELATES_TO|INFORMED_BY|INVOLVES*1..3]-(b:KnowledgeArtifact)
                WHERE b.artifact_id <> $artifact_id
                WITH b, count(*) AS proximity_score
                WHERE proximity_score >= $threshold
                RETURN b.artifact_id AS artifact_id,
                       b.title AS title,
                       b.artifact_type AS artifact_type,
                       proximity_score
                ORDER BY proximity_score DESC
                LIMIT $limit
                """,
                {"artifact_id": artifact_id, "threshold": threshold, "limit": limit},
            )
            return [record.data() for record in result]

    def find_orphan_artifacts(self) -> list[dict]:
        """Find artifacts with no relationships."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a:KnowledgeArtifact)
                WHERE NOT (a)--()
                RETURN a.artifact_id AS artifact_id,
                       a.title AS title,
                       a.created_at AS created_at
                ORDER BY a.created_at
                """
            )
            return [record.data() for record in result]

    def get_artifact_subgraph(
        self, artifact_id: str, depth: int = 2
    ) -> dict[str, Any]:
        """Get the subgraph around an artifact."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = (a:KnowledgeArtifact {artifact_id: $artifact_id})
                    -[*1..%d]-(b)
                RETURN [node IN nodes(path) | {
                    id: node.artifact_id ?? node.policy_id ?? node.control_id ?? node.agent_id,
                    labels: labels(node),
                    title: node.title ?? node.name
                }] AS nodes,
                [rel IN relationships(path) | {
                    type: type(rel),
                    start: startNode(rel).artifact_id ?? startNode(rel).policy_id,
                    end: endNode(rel).artifact_id ?? endNode(rel).policy_id
                }] AS relationships
                """
                % depth,
                {"artifact_id": artifact_id},
            )
            data = result.single()
            return dict(data) if data else {"nodes": [], "relationships": []}

    def get_most_influential(self, limit: int = 20) -> list[dict]:
        """Get most influential artifacts by degree centrality."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a:KnowledgeArtifact)
                RETURN a.artifact_id AS artifact_id,
                       a.title AS title,
                       a.artifact_type AS artifact_type,
                       size((a)--()) AS degree
                ORDER BY degree DESC
                LIMIT $limit
                """,
                {"limit": limit},
            )
            return [record.data() for record in result]

    def find_bridge_artifacts(self) -> list[dict]:
        """Find artifacts that bridge different domains."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a:KnowledgeArtifact)-[:RELATES_TO]-(b:KnowledgeArtifact)
                WHERE a.domain <> b.domain
                RETURN a.title AS title,
                       a.domain AS source_domain,
                       b.domain AS target_domain,
                       count(*) AS bridge_count
                ORDER BY bridge_count DESC
                """
            )
            return [record.data() for record in result]
```

---

## 4. Knowledge Graph Analytics

### 4.1 Graph Analytics Engine

```python
# analytics/graph_analytics.py
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CentralityMetrics:
    """Centrality metrics for a node."""
    node_id: str
    degree: float = 0.0
    betweenness: float = 0.0
    closeness: float = 0.0
    eigenvector: float = 0.0
    pagerank: float = 0.0


@dataclass
class CommunityResult:
    """Community detection result."""
    community_id: int
    members: list[str] = field(default_factory=list)
    size: int = 0
    density: float = 0.0


@dataclass
class GraphMetrics:
    """Overall graph metrics."""
    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    avg_degree: float = 0.0
    clustering_coefficient: float = 0.0
    diameter: int = 0
    connected_components: int = 0
    orphan_count: int = 0
    cross_domain_edges: int = 0


class KnowledgeGraphAnalytics:
    """Graph analytics engine for the knowledge graph."""

    def __init__(self, neo4j_graph):
        self.neo4j = neo4j_graph
        self._graph: Optional[nx.DiGraph] = None

    def build_networkx_graph(self) -> nx.DiGraph:
        """Build a NetworkX graph from Neo4j data."""
        G = nx.DiGraph()

        with self.neo4j.driver.session() as session:
            # Get all artifact nodes
            result = session.run(
                """
                MATCH (a:KnowledgeArtifact)
                RETURN a.artifact_id AS id, a.title AS title,
                       a.artifact_type AS type, a.domain AS domain,
                       a.severity AS severity
                """
            )
            for record in result:
                G.add_node(
                    record["id"],
                    title=record["title"],
                    type=record["type"],
                    domain=record["domain"],
                    severity=record["severity"],
                )

            # Get all relationships between artifacts
            result = session.run(
                """
                MATCH (a:KnowledgeArtifact)-[r]->(b:KnowledgeArtifact)
                RETURN a.artifact_id AS source,
                       b.artifact_id AS target,
                       type(r) AS rel_type
                """
            )
            for record in result:
                G.add_edge(
                    record["source"],
                    record["target"],
                    rel_type=record["rel_type"],
                )

        self._graph = G
        return G

    def compute_centrality_metrics(self) -> dict[str, CentralityMetrics]:
        """Compute centrality metrics for all nodes."""
        if self._graph is None:
            self.build_networkx_graph()

        G = self._graph
        metrics: dict[str, CentralityMetrics] = {}

        # Compute all centrality measures
        degree_cent = nx.degree_centrality(G)
        betweenness_cent = nx.betweenness_centrality(G, normalized=True)
        closeness_cent = nx.closeness_centrality(G)

        try:
            eigenvector_cent = nx.eigenvector_centrality(G, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            eigenvector_cent = {n: 0.0 for n in G.nodes()}

        pagerank = nx.pagerank(G)

        for node_id in G.nodes():
            metrics[node_id] = CentralityMetrics(
                node_id=node_id,
                degree=degree_cent.get(node_id, 0.0),
                betweenness=betweenness_cent.get(node_id, 0.0),
                closeness=closeness_cent.get(node_id, 0.0),
                eigenvector=eigenvector_cent.get(node_id, 0.0),
                pagerank=pagerank.get(node_id, 0.0),
            )

        return metrics

    def detect_communities(self) -> list[CommunityResult]:
        """Detect communities using Louvain method."""
        if self._graph is None:
            self.build_networkx_graph()

        # Convert to undirected for community detection
        undirected = self._graph.to_undirected()

        try:
            from networkx.algorithms.community import louvain_communities
            communities = louvain_communities(undirected, seed=42)
        except ImportError:
            # Fallback to greedy modularity
            from networkx.algorithms.community import greedy_modularity_communities
            communities = list(greedy_modularity_communities(undirected))

        results = []
        for i, community in enumerate(communities):
            subgraph = undirected.subgraph(community)
            results.append(
                CommunityResult(
                    community_id=i,
                    members=list(community),
                    size=len(community),
                    density=nx.density(subgraph),
                )
            )

        return results

    def compute_graph_metrics(self) -> GraphMetrics:
        """Compute overall graph metrics."""
        if self._graph is None:
            self.build_networkx_graph()

        G = self._graph
        undirected = G.to_undirected()

        # Basic metrics
        node_count = G.number_of_nodes()
        edge_count = G.number_of_edges()
        density = nx.density(G) if node_count > 1 else 0.0
        avg_degree = (2 * edge_count / node_count) if node_count > 0 else 0.0

        # Clustering coefficient
        clustering = nx.average_clustering(undirected) if node_count > 2 else 0.0

        # Connected components
        components = list(nx.connected_components(undirected))
        connected_components = len(components)

        # Diameter (largest component)
        diameter = 0
        if components:
            largest = undirected.subgraph(max(components, key=len))
            try:
                diameter = nx.diameter(largest)
            except nx.NetworkXError:
                diameter = 0

        # Orphan nodes
        orphan_count = sum(1 for n in G.nodes() if G.degree(n) == 0)

        # Cross-domain edges
        cross_domain = 0
        for u, v in G.edges():
            u_domain = G.nodes[u].get("domain", "")
            v_domain = G.nodes[v].get("domain", "")
            if u_domain and v_domain and u_domain != v_domain:
                cross_domain += 1

        return GraphMetrics(
            node_count=node_count,
            edge_count=edge_count,
            density=density,
            avg_degree=avg_degree,
            clustering_coefficient=clustering,
            diameter=diameter,
            connected_components=connected_components,
            orphan_count=orphan_count,
            cross_domain_edges=cross_domain,
        )

    def find_shortest_causal_path(
        self, source_id: str, target_id: str
    ) -> Optional[list[str]]:
        """Find shortest path between two artifacts."""
        if self._graph is None:
            self.build_networkx_graph()

        try:
            path = nx.shortest_path(self._graph, source_id, target_id)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def compute_impact_radius(self, artifact_id: str, max_depth: int = 3) -> dict:
        """Compute the impact radius of an artifact."""
        if self._graph is None:
            self.build_networkx_graph()

        G = self._graph
        if artifact_id not in G:
            return {"nodes_affected": 0, "depth_reached": 0, "nodes": []}

        # BFS to find all reachable nodes
        visited = {artifact_id}
        current_level = {artifact_id}
        all_affected = []

        for depth in range(1, max_depth + 1):
            next_level = set()
            for node in current_level:
                for successor in G.successors(node):
                    if successor not in visited:
                        visited.add(successor)
                        next_level.add(successor)
                        all_affected.append(successor)
            current_level = next_level
            if not current_level:
                break

        return {
            "nodes_affected": len(all_affected),
            "depth_reached": depth,
            "nodes": all_affected,
        }

    def detect_emerging_patterns(self, window_days: int = 30) -> list[dict]:
        """Detect emerging patterns in recent knowledge."""
        if self._graph is None:
            self.build_networkx_graph()

        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

        # Find recently added edges
        recent_edges = []
        for u, v, data in self._graph.edges(data=True):
            # In production, use actual edge timestamps
            recent_edges.append((u, v, data))

        # Detect new clusters forming
        new_patterns = []
        if len(recent_edges) > 5:
            # Simple heuristic: nodes with many recent connections
            node_new_degree = defaultdict(int)
            for u, v, _ in recent_edges:
                node_new_degree[u] += 1
                node_new_degree[v] += 1

            for node_id, new_degree in node_new_degree.items():
                if new_degree >= 3:
                    new_patterns.append({
                        "node_id": node_id,
                        "title": self._graph.nodes[node_id].get("title", ""),
                        "new_connections": new_degree,
                        "type": "emerging_hub",
                    })

        return sorted(new_patterns, key=lambda x: x["new_connections"], reverse=True)

    def compute_relationship_decay(self, half_life_days: int = 90) -> dict[str, float]:
        """Compute relationship strength decay over time."""
        if self._graph is None:
            self.build_networkx_graph()

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        decay_scores = {}

        for u, v, data in self._graph.edges(data=True):
            # In production, use actual edge creation/confirmation timestamps
            # For now, use a placeholder based on node creation time
            edge_key = f"{u}->{v}"
            decay_scores[edge_key] = 1.0  # Placeholder

        return decay_scores

    def generate_analytics_report(self) -> dict[str, Any]:
        """Generate a comprehensive analytics report."""
        metrics = self.compute_graph_metrics()
        centrality = self.compute_centrality_metrics()
        communities = self.detect_communities()

        # Top influential artifacts
        top_influential = sorted(
            centrality.values(),
            key=lambda x: x.betweenness,
            reverse=True,
        )[:10]

        return {
            "graph_metrics": metrics.__dict__,
            "top_influential": [
                {
                    "node_id": m.node_id,
                    "betweenness": m.betweenness,
                    "pagerank": m.pagerank,
                    "degree": m.degree,
                }
                for m in top_influential
            ],
            "communities": [
                {
                    "community_id": c.community_id,
                    "size": c.size,
                    "density": c.density,
                }
                for c in communities
            ],
            "orphan_count": metrics.orphan_count,
            "cross_domain_edge_rate": (
                metrics.cross_domain_edges / metrics.edge_count
                if metrics.edge_count > 0
                else 0.0
            ),
        }
```

---

## 5. Knowledge Quality Scoring

### 5.1 Quality Scoring Engine

```python
# quality/quality_scorer.py
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from models.knowledge_artifact import KnowledgeArtifact, RetentionClass


@dataclass
class DimensionScore:
    """Score for a single quality dimension."""
    name: str
    score: float  # 0-100
    weight: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityScoreResult:
    """Complete quality score result."""
    artifact_id: str
    overall_score: float
    tier: str
    dimensions: list[DimensionScore]
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_excellent(self) -> bool:
        return self.overall_score >= 90

    @property
    def is_good(self) -> bool:
        return 80 <= self.overall_score < 90

    @property
    def is_acceptable(self) -> bool:
        return 70 <= self.overall_score < 80

    @property
    def is_marginal(self) -> bool:
        return 60 <= self.overall_score < 70

    @property
    def is_poor(self) -> bool:
        return self.overall_score < 60


class KnowledgeQualityScorer:
    """
    Multi-dimensional quality scoring engine for knowledge artifacts.
    
    Scores artifacts on six dimensions:
    - Completeness (25%)
    - Accuracy (20%)
    - Timeliness (15%)
    - Actionability (15%)
    - Linkage (15%)
    - Clarity (10%)
    """

    # Dimension weights (must sum to 1.0)
    WEIGHTS = {
        "completeness": 0.25,
        "accuracy": 0.20,
        "timeliness": 0.15,
        "actionability": 0.15,
        "linkage": 0.15,
        "clarity": 0.10,
    }

    # Decay constants for timeliness (half-life in days)
    DECAY_LAMBDAS = {
        RetentionClass.EPHEMERAL: 0.05,
        RetentionClass.STANDARD: 0.01,
        RetentionClass.EXTENDED: 0.005,
        RetentionClass.PERMANENT: 0.001,
    }

    # Placeholder patterns
    PLACEHOLDER_PATTERN = re.compile(
        r"\b(TBD|TODO|XXX|FIXME|N/?A|placeholder|lorem ipsum|coming soon)\b",
        re.IGNORECASE,
    )

    def __init__(self, graph_client=None):
        self.graph_client = graph_client

    def score_artifact(self, artifact: KnowledgeArtifact) -> QualityScoreResult:
        """Compute the full quality score for an artifact."""
        dimensions = [
            self._score_completeness(artifact),
            self._score_accuracy(artifact),
            self._score_timeliness(artifact),
            self._score_actionability(artifact),
            self._score_linkage(artifact),
            self._score_clarity(artifact),
        ]

        overall = sum(d.score * d.weight for d in dimensions)
        overall = max(0.0, min(100.0, overall))

        return QualityScoreResult(
            artifact_id=artifact.artifact_id,
            overall_score=round(overall, 2),
            tier=self._get_tier(overall),
            dimensions=dimensions,
        )

    def _score_completeness(self, artifact: KnowledgeArtifact) -> DimensionScore:
        """Score completeness (25% weight)."""
        content = artifact.content
        issues = []

        # Check required fields based on artifact type
        required_fields = self._get_required_fields(artifact.artifact_type.value)
        populated = 0
        total = len(required_fields)

        for field_path in required_fields:
            value = self._get_nested_value(content, field_path)
            if value is not None and value != "" and value != [] and value != {}:
                populated += 1
            else:
                issues.append(f"Missing: {field_path}")

        # Check for placeholder text
        placeholder_count = self._count_placeholders(content)
        if placeholder_count > 0:
            issues.append(f"Placeholders found: {placeholder_count}")

        # Check critical fields
        critical_missing = 0
        critical_fields = self._get_critical_fields(artifact.artifact_type.value)
        for field_path in critical_fields:
            value = self._get_nested_value(content, field_path)
            if value is None or value == "" or value == []:
                critical_missing += 1
                issues.append(f"Critical missing: {field_path}")

        # Calculate score
        if total > 0:
            field_ratio = populated / total
        else:
            field_ratio = 1.0

        score = field_ratio * 100
        score -= placeholder_count * 10
        score -= critical_missing * 20
        score = max(0.0, min(100.0, score))

        return DimensionScore(
            name="completeness",
            score=round(score, 2),
            weight=self.WEIGHTS["completeness"],
            details={
                "populated_fields": populated,
                "total_fields": total,
                "placeholder_count": placeholder_count,
                "critical_missing": critical_missing,
                "issues": issues,
            },
        )

    def _score_accuracy(self, artifact: KnowledgeArtifact) -> DimensionScore:
        """Score accuracy (20% weight)."""
        score = 100.0
        details = {
            "unverified_claims": 0,
            "cross_reference_errors": 0,
            "factual_errors": 0,
            "source_verified": False,
        }

        # Check if source is verified
        if artifact.lineage.validated_by:
            details["source_verified"] = True
            score += 5  # Bonus for verification

        # Check for cross-reference consistency
        links = artifact.knowledge_links
        total_links = sum([
            len(links.related_policies),
            len(links.related_controls),
            len(links.related_agents),
            len(links.related_incidents),
        ])

        if total_links == 0:
            score -= 10  # Penalty for no cross-references
            details["cross_reference_errors"] = 1

        # Check for factual error indicators in content
        content_str = str(artifact.content).lower()
        error_indicators = ["incorrect", "error", "wrong", "false", "invalid"]
        for indicator in error_indicators:
            if indicator in content_str:
                score -= 5
                details["factual_errors"] += 1

        score = max(0.0, min(100.0, score))

        return DimensionScore(
            name="accuracy",
            score=round(score, 2),
            weight=self.WEIGHTS["accuracy"],
            details=details,
        )

    def _score_timeliness(self, artifact: KnowledgeArtifact) -> DimensionScore:
        """Score timeliness (15% weight) using exponential decay."""
        now = datetime.now(timezone.utc)

        # Days since last update
        days_since_update = (now - artifact.updated_at).days

        # Get decay constant based on retention class
        lambda_val = self.DECAY_LAMBDAS.get(
            artifact.governance.retention_class, 0.01
        )

        # Exponential decay: score = 100 * e^(-λ * days)
        decay_factor = math.exp(-lambda_val * days_since_update)
        score = 100.0 * decay_factor

        # Bonus for recent capture
        days_since_capture = (now - artifact.lineage.captured_at).days
        if days_since_capture <= 1:
            score = min(100.0, score + 5)

        return DimensionScore(
            name="timeliness",
            score=round(score, 2),
            weight=self.WEIGHTS["timeliness"],
            details={
                "days_since_update": days_since_update,
                "days_since_capture": days_since_capture,
                "decay_factor": round(decay_factor, 4),
                "lambda": lambda_val,
            },
        )

    def _score_actionability(self, artifact: KnowledgeArtifact) -> DimensionScore:
        """Score actionability (15% weight)."""
        content = artifact.content
        details = {}

        # Remediation specificity (0-1)
        rem = content.get("remediation", {})
        actions = rem.get("immediate_actions", []) + rem.get("short_term_fixes", [])
        if actions:
            # Check if actions are specific (contain measurable terms)
            specific_indicators = ["within", "by", "complete", "implement", "deploy"]
            specific_count = sum(
                1 for a in actions
                if any(ind in str(a).lower() for ind in specific_indicators)
            )
            specificity = min(1.0, specific_count / max(len(actions), 1))
        else:
            specificity = 0.0
        details["remediation_specificity"] = specificity

        # Owner assigned (0-1)
        owner = rem.get("owner", "")
        if owner and "@" in str(owner):
            owner_score = 1.0  # Named individual
        elif owner:
            owner_score = 0.5  # Team assigned
        else:
            owner_score = 0.0
        details["owner_assigned"] = owner_score

        # Due date set (0-1)
        due_date = rem.get("due_date")
        if due_date:
            try:
                due = datetime.fromisoformat(str(due_date).replace("Z", "+00:00"))
                if due > datetime.now(timezone.utc):
                    due_score = 1.0  # Future due date
                else:
                    due_score = 0.5  # Past due
            except (ValueError, TypeError):
                due_score = 0.0
        else:
            due_score = 0.0
        details["due_date_set"] = due_score

        # Outcome linked (0-1)
        outcome_linked = bool(
            rem.get("status") in ("completed", "verified")
            or content.get("outcome_evidence")
        )
        details["outcome_linked"] = 1.0 if outcome_linked else 0.0

        # Calculate weighted score
        score = (
            specificity * 0.3
            + owner_score * 0.25
            + due_score * 0.2
            + (1.0 if outcome_linked else 0.0) * 0.25
        ) * 100

        return DimensionScore(
            name="actionability",
            score=round(score, 2),
            weight=self.WEIGHTS["actionability"],
            details=details,
        )

    def _score_linkage(self, artifact: KnowledgeArtifact) -> DimensionScore:
        """Score linkage (15% weight)."""
        links = artifact.knowledge_links
        details = {}

        # Count total links
        link_counts = {
            "policies": len(links.related_policies),
            "controls": len(links.related_controls),
            "agents": len(links.related_agents),
            "datasets": len(links.related_datasets),
            "incidents": len(links.related_incidents),
            "assessments": len(links.related_assessments),
            "audits": len(links.related_audits),
            "artifacts": len(links.related_artifacts),
        }
        total_links = sum(link_counts.values())
        details["link_counts"] = link_counts
        details["total_links"] = total_links

        # Link count score (target: 5 links)
        target_links = 5
        link_score = min(100.0, (total_links / target_links) * 100)

        # Link diversity bonus
        link_types_used = sum(1 for v in link_counts.values() if v > 0)
        diversity_bonus = 10 if link_types_used >= 3 else 0
        details["link_diversity_bonus"] = diversity_bonus

        # Graph connectivity bonus
        connectivity_bonus = 0
        if self.graph_client:
            try:
                subgraph = self.graph_client.get_artifact_subgraph(
                    artifact.artifact_id, depth=1
                )
                if len(subgraph.get("nodes", [])) > 1:
                    connectivity_bonus = 10
            except Exception:
                pass
        details["graph_connectivity_bonus"] = connectivity_bonus

        # Orphan penalty
        orphan_penalty = 50 if total_links == 0 else 0
        details["orphan_penalty"] = orphan_penalty

        score = link_score + diversity_bonus + connectivity_bonus - orphan_penalty
        score = max(0.0, min(100.0, score))

        return DimensionScore(
            name="linkage",
            score=round(score, 2),
            weight=self.WEIGHTS["linkage"],
            details=details,
        )

    def _score_clarity(self, artifact: KnowledgeArtifact) -> DimensionScore:
        """Score clarity (10% weight)."""
        details = {}

        # Readability score (simplified Flesch-Kincaid)
        text = f"{artifact.title} {artifact.description}"
        content_text = str(artifact.content)
        full_text = f"{text} {content_text}"

        words = len(full_text.split())
        sentences = max(1, full_text.count(".") + full_text.count("!") + full_text.count("?"))
        syllables = self._count_syllables(full_text)

        if words > 0:
            avg_words_per_sentence = words / sentences
            avg_syllables_per_word = syllables / words
            # Simplified readability: lower is more readable
            readability_raw = 0.4 * (avg_words_per_sentence + avg_syllables_per_word * 3)
            # Map to 0-100 (lower raw = higher score)
            readability_score = max(0.0, min(100.0, 100 - readability_raw * 5))
        else:
            readability_score = 0.0
        details["readability_score"] = round(readability_score, 2)

        # Structure adherence
        required_top = ["artifact_type", "title", "domain", "type", "severity", "content"]
        structure_ok = all(hasattr(artifact, f) for f in required_top)
        structure_adherence = 1.0 if structure_ok else 0.5
        details["structure_adherence"] = structure_adherence

        # Terminology consistency
        standard_terms = {
            "incident", "audit", "assessment", "policy", "control",
            "agent", "dataset", "severity", "critical", "high", "medium", "low",
        }
        content_lower = content_text.lower()
        terms_used = sum(1 for term in standard_terms if term in content_lower)
        terminology_consistency = min(1.0, terms_used / 5)
        details["terminology_consistency"] = terminology_consistency

        score = (
            readability_score * 0.4
            + structure_adherence * 100 * 0.3
            + terminology_consistency * 100 * 0.3
        )

        return DimensionScore(
            name="clarity",
            score=round(score, 2),
            weight=self.WEIGHTS["clarity"],
            details=details,
        )

    def _get_tier(self, score: float) -> str:
        """Get quality tier from score."""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "acceptable"
        elif score >= 60:
            return "marginal"
        else:
            return "poor"

    def _get_required_fields(self, artifact_type: str) -> list[str]:
        """Get required fields for an artifact type."""
        common = ["title", "description"]
        type_specific = {
            "INCIDENT_LESSONS_LEARNED": [
                "incident_id", "root_cause", "impact", "remediation", "lessons_learned"
            ],
            "AUDIT_FINDING": [
                "audit_id", "control_id", "finding", "remediation"
            ],
            "ASSESSMENT_RESULT": [
                "assessment_id", "scope", "results", "recommendations"
            ],
            "POLICY_DECISION": [
                "policy_id", "decision_type", "decision"
            ],
            "AGENT_BEHAVIOR_PATTERN": [
                "agent_id", "pattern_type", "pattern"
            ],
        }
        return common + type_specific.get(artifact_type, [])

    def _get_critical_fields(self, artifact_type: str) -> list[str]:
        """Get critical fields for an artifact type."""
        critical = {
            "INCIDENT_LESSONS_LEARNED": ["root_cause", "remediation"],
            "AUDIT_FINDING": ["finding", "remediation"],
            "ASSESSMENT_RESULT": ["results"],
            "POLICY_DECISION": ["decision"],
            "AGENT_BEHAVIOR_PATTERN": ["pattern"],
        }
        return critical.get(artifact_type, [])

    def _get_nested_value(self, data: dict, path: str) -> Any:
        """Get a nested value from a dict using dot notation."""
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    def _count_placeholders(self, data: Any) -> int:
        """Count placeholder values in data."""
        count = 0
        if isinstance(data, str):
            count += len(self.PLACEHOLDER_PATTERN.findall(data))
        elif isinstance(data, dict):
            for v in data.values():
                count += self._count_placeholders(v)
        elif isinstance(data, list):
            for item in data:
                count += self._count_placeholders(item)
        return count

    def _count_syllables(self, text: str) -> int:
        """Rough syllable count for readability scoring."""
        text = text.lower()
        count = 0
        vowels = "aeiouy"
        prev_was_vowel = False
        for char in text:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel
        return max(1, count)
```

### 5.2 Quality Score API

```python
# quality/quality_api.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from models.knowledge_artifact import KnowledgeArtifact
from quality.quality_scorer import KnowledgeQualityScorer, QualityScoreResult


class QualityScoreService:
    """Service for managing quality scores."""

    def __init__(self, artifact_store, graph_client):
        self.scorer = KnowledgeQualityScorer(graph_client)
        self.artifact_store = artifact_store
        self._score_cache: dict[str, QualityScoreResult] = {}

    def score_and_update(self, artifact_id: str) -> Optional[QualityScoreResult]:
        """Score an artifact and update its stored quality score."""
        artifact = self.artifact_store.get(artifact_id)
        if not artifact:
            return None

        result = self.scorer.score_artifact(artifact)

        # Update artifact metadata with quality score
        artifact.metadata["quality_score"] = result.overall_score
        artifact.metadata["quality_tier"] = result.tier
        artifact.metadata["quality_dimensions"] = [
            {"name": d.name, "score": d.score, "weight": d.weight}
            for d in result.dimensions
        ]
        artifact.updated_at = datetime.now(timezone.utc)
        self.artifact_store.save(artifact)

        # Cache the result
        self._score_cache[artifact_id] = result

        return result

    def get_score(self, artifact_id: str) -> Optional[QualityScoreResult]:
        """Get cached quality score or compute new one."""
        if artifact_id in self._score_cache:
            return self._score_cache[artifact_id]

        artifact = self.artifact_store.get(artifact_id)
        if not artifact:
            return None

        return self.scorer.score_artifact(artifact)

    def get_quality_trend(
        self, artifact_id: str, days: int = 90
    ) -> list[dict]:
        """Get quality score trend over time."""
        # In production, query TimescaleDB for historical scores
        artifact = self.artifact_store.get(artifact_id)
        if not artifact:
            return []

        current_score = self.scorer.score_artifact(artifact)
        return [
            {
                "date": datetime.now(timezone.utc).isoformat(),
                "score": current_score.overall_score,
                "tier": current_score.tier,
            }
        ]

    def get_domain_quality_summary(self, domain: str) -> dict:
        """Get quality summary for a domain."""
        artifacts = self.artifact_store.search(domain=domain, limit=1000)
        scores = []
        for artifact in artifacts:
            result = self.scorer.score_artifact(artifact)
            scores.append(result.overall_score)

        if not scores:
            return {"domain": domain, "count": 0, "avg_score": 0}

        return {
            "domain": domain,
            "count": len(scores),
            "avg_score": round(sum(scores) / len(scores), 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
            "excellent_count": sum(1 for s in scores if s >= 90),
            "good_count": sum(1 for s in scores if 80 <= s < 90),
            "acceptable_count": sum(1 for s in scores if 70 <= s < 80),
            "marginal_count": sum(1 for s in scores if 60 <= s < 70),
            "poor_count": sum(1 for s in scores if s < 60),
        }
```

---

## 6. Knowledge Gap Analysis

### 6.1 Gap Analysis Engine

```python
# gaps/gap_analyzer.py
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from models.knowledge_artifact import KnowledgeArtifact, Domain

logger = logging.getLogger(__name__)


class GapType(str, Enum):
    COVERAGE = "coverage"
    DEPTH = "depth"
    CURRENCY = "currency"
    ACCURACY = "accuracy"
    LINKAGE = "linkage"
    APPLICATION = "application"
    QUALITY = "quality"
    REGULATORY = "regulatory"


@dataclass
class KnowledgeGap:
    """Represents a knowledge gap."""
    gap_id: str
    gap_type: GapType
    domain: str
    entity_id: str
    entity_type: str
    severity: float  # 0-10
    priority: str  # low | medium | high | critical | emergency
    description: str
    expected_artifacts: int
    actual_artifacts: int
    quality_threshold: float
    actual_quality: float
    regulatory_urgency: int  # 0-3
    entity_risk_weight: int  # 1-5
    identified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    remediation_owner: Optional[str] = None
    remediation_due: Optional[datetime] = None
    status: str = "open"  # open | in_progress | resolved | accepted

    @property
    def knowledge_deficit(self) -> float:
        """Calculate knowledge deficit (0-1)."""
        if self.expected_artifacts == 0:
            return 0.0
        coverage_deficit = 1.0 - (self.actual_artifacts / self.expected_artifacts)
        quality_deficit = max(0.0, 1.0 - (self.actual_quality / self.quality_threshold))
        return min(1.0, (coverage_deficit + quality_deficit) / 2)


class KnowledgeGapAnalyzer:
    """
    Systematic knowledge gap analysis engine.
    
    Identifies gaps across 8 dimensions:
    Coverage, Depth, Currency, Accuracy, Linkage, Application, Quality, Regulatory
    """

    # Expected knowledge profiles by entity type
    EXPECTED_PROFILES = {
        "critical_control": {
            "min_artifacts": 3,
            "min_quality": 80,
            "review_frequency_days": 90,
        },
        "high_risk_agent": {
            "min_artifacts": 2,
            "min_quality": 75,
            "review_frequency_days": 30,
        },
        "active_policy": {
            "min_artifacts": 2,
            "min_quality": 80,
            "review_frequency_days": 180,
        },
        "regulated_dataset": {
            "min_artifacts": 2,
            "min_quality": 85,
            "review_frequency_days": 365,
        },
        "regulatory_requirement": {
            "min_artifacts": 1,
            "min_quality": 80,
            "review_frequency_days": 60,
        },
    }

    # Gap severity thresholds
    SEVERITY_THRESHOLDS = {
        "low": (0, 2),
        "medium": (2, 4),
        "high": (4, 6),
        "critical": (6, 8),
        "emergency": (8, 10),
    }

    def __init__(self, artifact_store, graph_client, quality_service):
        self.artifact_store = artifact_store
        self.graph_client = graph_client
        self.quality_service = quality_service

    def analyze_all_gaps(self) -> list[KnowledgeGap]:
        """Run complete gap analysis."""
        gaps = []
        gaps.extend(self._detect_coverage_gaps())
        gaps.extend(self._detect_depth_gaps())
        gaps.extend(self._detect_currency_gaps())
        gaps.extend(self._detect_linkage_gaps())
        gaps.extend(self._detect_application_gaps())
        gaps.extend(self._detect_quality_gaps())
        gaps.extend(self._detect_regulatory_gaps())
        return sorted(gaps, key=lambda g: g.severity, reverse=True)

    def _detect_coverage_gaps(self) -> list[KnowledgeGap]:
        """Detect coverage gaps - missing knowledge for required entities."""
        gaps = []

        # Get all controls from graph
        controls = self._get_all_controls()
        for control in controls:
            control_id = control["control_id"]
            risk_weight = control.get("risk_weight", 3)

            # Count linked artifacts
            linked = self._count_linked_artifacts(control_id, "Control")
            expected = self.EXPECTED_PROFILES["critical_control"]["min_artifacts"]

            if linked < expected:
                severity = self._compute_severity(
                    entity_risk_weight=risk_weight,
                    knowledge_deficit=1.0 - (linked / expected),
                    regulatory_urgency=0,
                )
                gaps.append(
                    KnowledgeGap(
                        gap_id=f"gap-cov-{control_id}",
                        gap_type=GapType.COVERAGE,
                        domain="AUDIT",
                        entity_id=control_id,
                        entity_type="Control",
                        severity=severity,
                        priority=self._severity_to_priority(severity),
                        description=f"Control {control_id} has {linked} artifacts, expected {expected}",
                        expected_artifacts=expected,
                        actual_artifacts=linked,
                        quality_threshold=80,
                        actual_quality=0,
                        regulatory_urgency=0,
                        entity_risk_weight=risk_weight,
                    )
                )

        return gaps

    def _detect_depth_gaps(self) -> list[KnowledgeGap]:
        """Detect depth gaps - knowledge exists but lacks detail."""
        gaps = []
        artifacts = self.artifact_store.search(limit=1000)

        for artifact in artifacts:
            score_result = self.quality_service.get_score(artifact.artifact_id)
            if not score_result:
                continue

            # Check completeness dimension
            completeness = next(
                (d for d in score_result.dimensions if d.name == "completeness"),
                None,
            )
            if completeness and completeness.score < 60:
                severity = self._compute_severity(
                    entity_risk_weight=3,
                    knowledge_deficit=1.0 - (completeness.score / 100),
                    regulatory_urgency=0,
                )
                gaps.append(
                    KnowledgeGap(
                        gap_id=f"gap-dep-{artifact.artifact_id}",
                        gap_type=GapType.DEPTH,
                        domain=artifact.domain.value,
                        entity_id=artifact.artifact_id,
                        entity_type=artifact.artifact_type.value,
                        severity=severity,
                        priority=self._severity_to_priority(severity),
                        description=f"Artifact completeness score {completeness.score}/100",
                        expected_artifacts=1,
                        actual_artifacts=1,
                        quality_threshold=80,
                        actual_quality=completeness.score,
                        regulatory_urgency=0,
                        entity_risk_weight=3,
                    )
                )

        return gaps

    def _detect_currency_gaps(self) -> list[KnowledgeGap]:
        """Detect currency gaps - outdated knowledge."""
        gaps = []
        artifacts = self.artifact_store.search(limit=1000)
        now = datetime.now(timezone.utc)

        for artifact in artifacts:
            days_since_update = (now - artifact.updated_at).days

            # Get expected review frequency
            profile = self.EXPECTED_PROFILES.get("active_policy")
            expected_frequency = profile["review_frequency_days"] if profile else 180

            if days_since_update > expected_frequency:
                severity = min(10.0, days_since_update / expected_frequency * 3)
                gaps.append(
                    KnowledgeGap(
                        gap_id=f"gap-cur-{artifact.artifact_id}",
                        gap_type=GapType.CURRENCY,
                        domain=artifact.domain.value,
                        entity_id=artifact.artifact_id,
                        entity_type=artifact.artifact_type.value,
                        severity=severity,
                        priority=self._severity_to_priority(severity),
                        description=f"Artifact not updated in {days_since_update} days",
                        expected_artifacts=1,
                        actual_artifacts=1,
                        quality_threshold=80,
                        actual_quality=0,
                        regulatory_urgency=0,
                        entity_risk_weight=3,
                    )
                )

        return gaps

    def _detect_linkage_gaps(self) -> list[KnowledgeGap]:
        """Detect linkage gaps - knowledge not connected to graph."""
        gaps = []
        orphans = self.graph_client.find_orphan_artifacts()

        for orphan in orphans:
            severity = 5.0  # Medium severity for orphans
            gaps.append(
                KnowledgeGap(
                    gap_id=f"gap-lnk-{orphan['artifact_id']}",
                    gap_type=GapType.LINKAGE,
                    domain="UNKNOWN",
                    entity_id=orphan["artifact_id"],
                    entity_type="KnowledgeArtifact",
                    severity=severity,
                    priority=self._severity_to_priority(severity),
                    description=f"Orphan artifact: {orphan['title']}",
                    expected_artifacts=1,
                    actual_artifacts=0,
                    quality_threshold=80,
                    actual_quality=0,
                    regulatory_urgency=0,
                    entity_risk_weight=3,
                )
            )

        return gaps

    def _detect_application_gaps(self) -> list[KnowledgeGap]:
        """Detect application gaps - knowledge not applied."""
        gaps = []
        artifacts = self.artifact_store.search(limit=1000)

        for artifact in artifacts:
            if artifact.lifecycle_stage.value in ("shared", "classified"):
                # Check if artifact has been applied
                if artifact.metrics.application_count == 0:
                    days_since_capture = (
                        datetime.now(timezone.utc) - artifact.lineage.captured_at
                    ).days
                    if days_since_capture > 90:
                        severity = min(8.0, days_since_capture / 30)
                        gaps.append(
                            KnowledgeGap(
                                gap_id=f"gap-app-{artifact.artifact_id}",
                                gap_type=GapType.APPLICATION,
                                domain=artifact.domain.value,
                                entity_id=artifact.artifact_id,
                                entity_type=artifact.artifact_type.value,
                                severity=severity,
                                priority=self._severity_to_priority(severity),
                                description=f"Artifact not applied in {days_since_capture} days",
                                expected_artifacts=1,
                                actual_artifacts=1,
                                quality_threshold=80,
                                actual_quality=0,
                                regulatory_urgency=0,
                                entity_risk_weight=3,
                            )
                        )

        return gaps

    def _detect_quality_gaps(self) -> list[KnowledgeGap]:
        """Detect quality gaps - knowledge below quality thresholds."""
        gaps = []
        artifacts = self.artifact_store.search(limit=1000)

        for artifact in artifacts:
            score_result = self.quality_service.get_score(artifact.artifact_id)
            if not score_result:
                continue

            if score_result.overall_score < 70:
                severity = self._compute_severity(
                    entity_risk_weight=3,
                    knowledge_deficit=1.0 - (score_result.overall_score / 100),
                    regulatory_urgency=0,
                )
                gaps.append(
                    KnowledgeGap(
                        gap_id=f"gap-qua-{artifact.artifact_id}",
                        gap_type=GapType.QUALITY,
                        domain=artifact.domain.value,
                        entity_id=artifact.artifact_id,
                        entity_type=artifact.artifact_type.value,
                        severity=severity,
                        priority=self._severity_to_priority(severity),
                        description=f"Quality score {score_result.overall_score}/100 below threshold",
                        expected_artifacts=1,
                        actual_artifacts=1,
                        quality_threshold=70,
                        actual_quality=score_result.overall_score,
                        regulatory_urgency=0,
                        entity_risk_weight=3,
                    )
                )

        return gaps

    def _detect_regulatory_gaps(self) -> list[KnowledgeGap]:
        """Detect regulatory gaps - new regulations without linked knowledge."""
        gaps = []
        # In production, query regulatory registry for new/changed regulations
        # and check for linked compliance knowledge
        return gaps

    def compute_coverage_matrix(self) -> dict[str, dict]:
        """Compute knowledge coverage matrix by domain."""
        matrix = {}
        domains = [d.value for d in Domain]

        for domain in domains:
            artifacts = self.artifact_store.search(domain=domain, limit=1000)
            total_controls = self._get_domain_control_count(domain)
            controls_with_knowledge = self._get_controls_with_knowledge(domain)

            coverage = (
                (controls_with_knowledge / total_controls * 100)
                if total_controls > 0
                else 0.0
            )

            matrix[domain] = {
                "total_controls": total_controls,
                "controls_with_knowledge": controls_with_knowledge,
                "artifact_count": len(artifacts),
                "coverage_score": round(coverage, 1),
                "status": (
                    "critical_gap" if coverage < 50
                    else "gap" if coverage < 80
                    else "adequate"
                ),
            }

        return matrix

    def _compute_severity(
        self,
        entity_risk_weight: int,
        knowledge_deficit: float,
        regulatory_urgency: int,
    ) -> float:
        """Compute gap severity score."""
        severity = (
            entity_risk_weight * knowledge_deficit * 2
            + regulatory_urgency
        )
        return round(min(10.0, max(0.0, severity)), 2)

    def _severity_to_priority(self, severity: float) -> str:
        """Convert severity score to priority level."""
        for priority, (low, high) in self.SEVERITY_THRESHOLDS.items():
            if low <= severity < high:
                return priority
        return "emergency"

    def _get_all_controls(self) -> list[dict]:
        """Get all controls from the graph."""
        # In production, query Neo4j for all Control nodes
        return []

    def _count_linked_artifacts(self, entity_id: str, entity_type: str) -> int:
        """Count artifacts linked to an entity."""
        # In production, query Neo4j
        return 0

    def _get_domain_control_count(self, domain: str) -> int:
        """Get total controls for a domain."""
        return 0

    def _get_controls_with_knowledge(self, domain: str) -> int:
        """Get controls with linked knowledge."""
        return 0
```

---

## 7. Knowledge Recommendation Engine

### 7.1 Recommendation Engine

```python
# recommendations/recommendation_engine.py
from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from models.knowledge_artifact import KnowledgeArtifact

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """A single knowledge recommendation."""
    artifact_id: str
    title: str
    artifact_type: str
    score: float
    reasons: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """User profile for recommendations."""
    user_id: str
    role: str
    team: str
    interests: list[str] = field(default_factory=list)
    preferred_types: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    recent_artifacts: list[str] = field(default_factory=list)
    community: Optional[int] = None


class KnowledgeRecommendationEngine:
    """
    Hybrid recommendation engine combining:
    - Content-based filtering
    - Collaborative filtering
    - Graph-based recommendation
    - Quality and recency boosting
    """

    # Weights for hybrid scoring
    WEIGHTS = {
        "content": 0.30,
        "collaborative": 0.20,
        "graph": 0.25,
        "quality": 0.15,
        "recency": 0.10,
    }

    def __init__(self, artifact_store, graph_client, quality_service):
        self.artifact_store = artifact_store
        self.graph_client = graph_client
        self.quality_service = quality_service
        self._user_profiles: dict[str, UserProfile] = {}
        self._user_interactions: dict[str, list[dict]] = defaultdict(list)

    def recommend(
        self,
        user_id: str,
        context: Optional[dict] = None,
        limit: int = 10,
        diversity_factor: float = 0.3,
    ) -> list[Recommendation]:
        """
        Generate personalized recommendations for a user.

        Args:
            user_id: Target user
            context: Current context (task, view, etc.)
            limit: Maximum recommendations
            diversity_factor: 0-1, higher = more diverse recommendations
        """
        user = self._get_user_profile(user_id)
        if not user:
            return self._get_trending_recommendations(limit)

        # Get candidate artifacts
        candidates = self._get_candidate_artifacts(user, context)

        # Score candidates
        scored = []
        for artifact in candidates:
            score, reasons = self._compute_hybrid_score(artifact, user, context)
            scored.append((artifact, score, reasons))

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)

        # Apply diversity re-ranking
        if diversity_factor > 0:
            scored = self._apply_diversity(scored, limit, diversity_factor)

        # Build recommendations
        recommendations = []
        for artifact, score, reasons in scored[:limit]:
            recommendations.append(
                Recommendation(
                    artifact_id=artifact.artifact_id,
                    title=artifact.title,
                    artifact_type=artifact.artifact_type.value,
                    score=round(score, 4),
                    reasons=reasons,
                    context={
                        "domain": artifact.domain.value,
                        "severity": artifact.severity.value,
                        "lifecycle_stage": artifact.lifecycle_stage.value,
                    },
                )
            )

        return recommendations

    def _compute_hybrid_score(
        self,
        artifact: KnowledgeArtifact,
        user: UserProfile,
        context: Optional[dict],
    ) -> tuple[float, list[str]]:
        """Compute hybrid recommendation score."""
        reasons = []

        # Content-based score
        content_score = self._content_score(artifact, user)
        if content_score > 0.5:
            reasons.append("Matches your interests")

        # Collaborative score
        collab_score = self._collaborative_score(artifact, user)
        if collab_score > 0.5:
            reasons.append("Similar users found this useful")

        # Graph-based score
        graph_score = self._graph_score(artifact, user)
        if graph_score > 0.5:
            reasons.append("Related to your recent activity")

        # Quality score
        quality_result = self.quality_service.get_score(artifact.artifact_id)
        quality_score = (quality_result.overall_score / 100) if quality_result else 0.5
        if quality_score > 0.8:
            reasons.append("High quality artifact")

        # Recency score
        recency_score = self._recency_score(artifact)
        if recency_score > 0.8:
            reasons.append("Recently captured")

        # Context boost
        context_boost = 0.0
        if context:
            context_boost = self._context_boost(artifact, context)
            if context_boost > 0.3:
                reasons.append("Relevant to your current task")

        # Weighted combination
        final_score = (
            self.WEIGHTS["content"] * content_score
            + self.WEIGHTS["collaborative"] * collab_score
            + self.WEIGHTS["graph"] * graph_score
            + self.WEIGHTS["quality"] * quality_score
            + self.WEIGHTS["recency"] * recency_score
            + context_boost
        )

        return final_score, reasons

    def _content_score(self, artifact: KnowledgeArtifact, user: UserProfile) -> float:
        """Content-based filtering score."""
        scores = []

        # Domain match
        if artifact.domain.value in user.interests:
            scores.append(1.0)
        else:
            scores.append(0.0)

        # Type match
        if artifact.type in user.preferred_types:
            scores.append(1.0)
        else:
            scores.append(0.0)

        # Entity overlap (Jaccard similarity)
        artifact_entities = set()
        links = artifact.knowledge_links
        artifact_entities.update(links.related_agents)
        artifact_entities.update(links.related_policies)
        artifact_entities.update(links.related_controls)

        user_entities = set(user.entities)
        if artifact_entities or user_entities:
            intersection = len(artifact_entities & user_entities)
            union = len(artifact_entities | user_entities)
            entity_score = intersection / union if union > 0 else 0.0
        else:
            entity_score = 0.0
        scores.append(entity_score)

        # Tag overlap
        artifact_tags = set(artifact.metadata.get("tags", []))
        user_tags = set(user.tags)
        if artifact_tags or user_tags:
            intersection = len(artifact_tags & user_tags)
            union = len(artifact_tags | user_tags)
            tag_score = intersection / union if union > 0 else 0.0
        else:
            tag_score = 0.0
        scores.append(tag_score)

        return sum(scores) / len(scores) if scores else 0.0

    def _collaborative_score(self, artifact: KnowledgeArtifact, user: UserProfile) -> float:
        """Collaborative filtering score based on similar users."""
        # Get users with similar profiles
        similar_users = self._find_similar_users(user)

        if not similar_users:
            return 0.0

        # Compute weighted rating
        total_similarity = 0.0
        weighted_rating = 0.0

        for other_user, similarity in similar_users:
            # Check if other user interacted with this artifact
            interactions = self._user_interactions.get(other_user.user_id, [])
            for interaction in interactions:
                if interaction["artifact_id"] == artifact.artifact_id:
                    rating = interaction.get("rating", 0.5)
                    weighted_rating += similarity * rating
                    total_similarity += similarity
                    break

        if total_similarity == 0:
            return 0.0

        return weighted_rating / total_similarity

    def _graph_score(self, artifact: KnowledgeArtifact, user: UserProfile) -> float:
        """Graph-based recommendation score."""
        if not user.recent_artifacts:
            return 0.0

        # Proximity score: 1 / (1 + shortest_path_length)
        min_distance = float("inf")
        for recent_id in user.recent_artifacts:
            try:
                # Use graph client to find distance
                subgraph = self.graph_client.get_artifact_subgraph(recent_id, depth=3)
                for node in subgraph.get("nodes", []):
                    if node.get("id") == artifact.artifact_id:
                        # Found in subgraph, estimate distance
                        min_distance = min(min_distance, 2)
                        break
            except Exception:
                continue

        if min_distance == float("inf"):
            return 0.0

        proximity_score = 1.0 / (1.0 + min_distance)

        # Centrality score
        centrality = 0.0
        try:
            influential = self.graph_client.get_most_influential(limit=100)
            for i, inf in enumerate(influential):
                if inf["artifact_id"] == artifact.artifact_id:
                    centrality = 1.0 - (i / len(influential))
                    break
        except Exception:
            pass

        # Community score
        community_score = 0.0
        if user.community is not None:
            # Check if artifact is in same community
            community_score = 0.5  # Placeholder

        # Combined graph score
        alpha, beta, gamma = 0.5, 0.3, 0.2
        return (
            alpha * proximity_score
            + beta * centrality
            + gamma * community_score
        )

    def _recency_score(self, artifact: KnowledgeArtifact) -> float:
        """Recency score using exponential decay."""
        days_old = (datetime.now(timezone.utc) - artifact.created_at).days
        lambda_val = 0.01  # Half-life ~69 days
        return math.exp(-lambda_val * days_old)

    def _context_boost(
        self, artifact: KnowledgeArtifact, context: dict
    ) -> float:
        """Compute context-based score boost."""
        boost = 0.0

        # Current task match
        current_task = context.get("current_task", "")
        if current_task:
            task_domains = {
                "incident": ["INCIDENT"],
                "audit": ["AUDIT"],
                "assessment": ["ASSESSMENT"],
                "policy": ["POLICY"],
            }
            relevant_domains = task_domains.get(current_task, [])
            if artifact.domain.value in relevant_domains:
                boost += 0.3

        # Current artifact similarity
        current_artifact_id = context.get("current_artifact_id")
        if current_artifact_id:
            try:
                similar = self.graph_client.find_similar_artifacts(
                    current_artifact_id, threshold=0.5, limit=20
                )
                for sim in similar:
                    if sim["artifact_id"] == artifact.artifact_id:
                        boost += 0.4
                        break
            except Exception:
                pass

        # Upcoming deadline relevance
        deadlines = context.get("upcoming_deadlines", [])
        for deadline in deadlines:
            if deadline.get("domain") == artifact.domain.value:
                boost += 0.2
                break

        return min(1.0, boost)

    def _apply_diversity(
        self,
        scored: list[tuple[KnowledgeArtifact, float, list[str]]],
        limit: int,
        diversity_factor: float,
    ) -> list[tuple[KnowledgeArtifact, float, list[str]]]:
        """Apply diversity re-ranking using MMR (Maximal Marginal Relevance)."""
        if not scored:
            return scored

        selected = [scored[0]]
        remaining = scored[1:]

        while len(selected) < limit and remaining:
            best_mmr_score = -1
            best_idx = 0

            for i, (artifact, score, reasons) in enumerate(remaining):
                # Compute max similarity to already selected
                max_sim = 0
                for sel_artifact, _, _ in selected:
                    sim = self._artifact_similarity(artifact, sel_artifact)
                    max_sim = max(max_sim, sim)

                # MMR score
                mmr_score = (1 - diversity_factor) * score - diversity_factor * max_sim

                if mmr_score > best_mmr_score:
                    best_mmr_score = mmr_score
                    best_idx = i

            selected.append(remaining.pop(best_idx))

        return selected

    def _artifact_similarity(
        self, a1: KnowledgeArtifact, a2: KnowledgeArtifact
    ) -> float:
        """Compute similarity between two artifacts."""
        # Domain similarity
        domain_sim = 1.0 if a1.domain == a2.domain else 0.0

        # Type similarity
        type_sim = 1.0 if a1.type == a2.type else 0.0

        # Tag overlap
        tags1 = set(a1.metadata.get("tags", []))
        tags2 = set(a2.metadata.get("tags", []))
        tag_sim = (
            len(tags1 & tags2) / len(tags1 | tags2)
            if tags1 or tags2
            else 0.0
        )

        return (domain_sim + type_sim + tag_sim) / 3

    def _get_candidate_artifacts(
        self, user: UserProfile, context: Optional[dict]
    ) -> list[KnowledgeArtifact]:
        """Get candidate artifacts for recommendation."""
        # Get artifacts from user's domains
        candidates = []
        for interest in user.interests:
            artifacts = self.artifact_store.search(
                domain=interest, limit=50
            )
            candidates.extend(artifacts)

        # Get recently viewed artifacts
        for artifact_id in user.recent_artifacts[-5:]:
            artifact = self.artifact_store.get(artifact_id)
            if artifact:
                candidates.append(artifact)

        # Deduplicate
        seen = set()
        unique = []
        for a in candidates:
            if a.artifact_id not in seen:
                seen.add(a.artifact_id)
                unique.append(a)

        return unique

    def _get_trending_recommendations(self, limit: int) -> list[Recommendation]:
        """Get trending recommendations for new/unknown users."""
        artifacts = self.artifact_store.search(limit=limit * 2)
        scored = []

        for artifact in artifacts:
            score = (
                artifact.metrics.view_count * 0.3
                + artifact.metrics.application_count * 0.5
                + (1 if artifact.severity.value == "critical" else 0) * 0.2
            )
            scored.append((artifact, score, ["Trending in your organization"]))

        scored.sort(key=lambda x: x[1], reverse=True)

        return [
            Recommendation(
                artifact_id=a.artifact_id,
                title=a.title,
                artifact_type=a.artifact_type.value,
                score=round(s, 4),
                reasons=r,
            )
            for a, s, r in scored[:limit]
        ]

    def _get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get or create user profile."""
        return self._user_profiles.get(user_id)

    def _find_similar_users(
        self, user: UserProfile
    ) -> list[tuple[UserProfile, float]]:
        """Find users with similar profiles."""
        similar = []
        for other in self._user_profiles.values():
            if other.user_id == user.user_id:
                continue

            # Cosine similarity of interests
            interests1 = set(user.interests)
            interests2 = set(other.interests)
            if interests1 or interests2:
                intersection = len(interests1 & interests2)
                union = len(interests1 | interests2)
                similarity = intersection / union if union > 0 else 0.0
            else:
                similarity = 0.0

            if similarity > 0.3:
                similar.append((other, similarity))

        return sorted(similar, key=lambda x: x[1], reverse=True)[:10]

    def record_interaction(
        self,
        user_id: str,
        artifact_id: str,
        interaction_type: str,
        rating: Optional[float] = None,
    ) -> None:
        """Record a user interaction for collaborative filtering."""
        self._user_interactions[user_id].append(
            {
                "artifact_id": artifact_id,
                "type": interaction_type,
                "rating": rating or (1.0 if interaction_type == "view" else 0.5),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def update_user_profile(self, user_id: str, **kwargs) -> None:
        """Update user profile."""
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = UserProfile(
                user_id=user_id,
                role=kwargs.get("role", ""),
                team=kwargs.get("team", ""),
            )

        profile = self._user_profiles[user_id]
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
```

---

## 8. Knowledge Lifecycle Automation

### 8.1 Lifecycle Automation Engine

```python
# lifecycle/lifecycle_automation.py
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Optional

from models.knowledge_artifact import KnowledgeArtifact, LifecycleStage

logger = logging.getLogger(__name__)


class AutomationEventType(str, Enum):
    ARTIFACT_CAPTURED = "artifact_captured"
    ARTIFACT_CLASSIFIED = "artifact_classified"
    ARTIFACT_SHARED = "artifact_shared"
    ARTIFACT_APPLIED = "artifact_applied"
    QUALITY_THRESHOLD_BREACH = "quality_threshold_breach"
    RETENTION_EXPIRED = "retention_expired"
    REVIEW_DATE_REACHED = "review_date_reached"
    SLA_BREACHED = "sla_breached"
    LEGAL_HOLD_RELEASED = "legal_hold_released"


@dataclass
class AutomationRule:
    """Defines an automation rule."""
    rule_id: str
    name: str
    description: str
    event_type: AutomationEventType
    conditions: dict[str, Any]
    actions: list[dict[str, Any]]
    approval_required: bool = False
    approver_role: Optional[str] = None
    enabled: bool = True
    priority: int = 100


@dataclass
class LifecycleEvent:
    """A lifecycle transition event."""
    event_id: str
    artifact_id: str
    event_type: AutomationEventType
    from_stage: Optional[LifecycleStage]
    to_stage: Optional[LifecycleStage]
    triggered_by: str  # rule_id or user_id
    triggered_at: datetime
    context: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending | executed | failed | reverted


class LifecycleAutomationEngine:
    """
    Automated lifecycle transition engine.
    
    Manages transitions: identified → validated → classified → shared → applied → archived → retired
    """

    # Valid transitions
    VALID_TRANSITIONS = {
        LifecycleStage.IDENTIFIED: [LifecycleStage.VALIDATED],
        LifecycleStage.VALIDATED: [LifecycleStage.CLASSIFIED],
        LifecycleStage.CLASSIFIED: [LifecycleStage.SHARED],
        LifecycleStage.SHARED: [LifecycleStage.APPLIED],
        LifecycleStage.APPLIED: [LifecycleStage.ARCHIVED],
        LifecycleStage.ARCHIVED: [LifecycleStage.RETIRED],
    }

    def __init__(
        self,
        artifact_store,
        graph_client,
        quality_service,
        notification_service=None,
    ):
        self.artifact_store = artifact_store
        self.graph_client = graph_client
        self.quality_service = quality_service
        self.notification_service = notification_service
        self.rules: list[AutomationRule] = []
        self.event_log: list[LifecycleEvent] = []
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default automation rules."""
        self.rules = [
            AutomationRule(
                rule_id="auto-validate-on-capture",
                name="Auto-validate on capture",
                description="Automatically validate artifact when quality gates pass",
                event_type=AutomationEventType.ARTIFACT_CAPTURED,
                conditions={"quality_gates_passed": True},
                actions=[{"type": "transition", "to_stage": "validated"}],
                approval_required=False,
            ),
            AutomationRule(
                rule_id="auto-classify-on-validate",
                name="Auto-classify on validate",
                description="Automatically classify artifact after validation",
                event_type=AutomationEventType.ARTIFACT_CAPTURED,
                conditions={"lifecycle_stage": "validated"},
                actions=[{"type": "transition", "to_stage": "classified"}],
                approval_required=False,
            ),
            AutomationRule(
                rule_id="auto-share-high-quality",
                name="Auto-share high quality artifacts",
                description="Auto-share artifacts with quality score >= 70",
                event_type=AutomationEventType.ARTIFACT_CLASSIFIED,
                conditions={"quality_score_gte": 70},
                actions=[
                    {"type": "transition", "to_stage": "shared"},
                    {"type": "notify", "recipients": ["knowledge_steward"]},
                ],
                approval_required=False,
            ),
            AutomationRule(
                rule_id="auto-share-extended",
                name="Auto-share to extended audience",
                description="Auto-share to extended audience when quality >= 85",
                event_type=AutomationEventType.ARTIFACT_CLASSIFIED,
                conditions={"quality_score_gte": 85, "classification": ["L1", "L2"]},
                actions=[
                    {"type": "transition", "to_stage": "shared"},
                    {"type": "share", "audience": "all_governance_staff"},
                ],
                approval_required=True,
                approver_role="knowledge_steward",
            ),
            AutomationRule(
                rule_id="auto-archive-retention",
                name="Auto-archive on retention expiry",
                description="Automatically archive artifacts past retention period",
                event_type=AutomationEventType.RETENTION_EXPIRED,
                conditions={"retention_expired": True, "legal_hold": False},
                actions=[
                    {"type": "transition", "to_stage": "archived"},
                    {"type": "archive"},
                ],
                approval_required=False,
            ),
            AutomationRule(
                rule_id="auto-retire-archive",
                name="Auto-retire after archive period",
                description="Automatically retire artifacts after archive retention",
                event_type=AutomationEventType.RETENTION_EXPIRED,
                conditions={"lifecycle_stage": "archived", "archive_period_expired": True},
                actions=[{"type": "transition", "to_stage": "retired"}],
                approval_required=False,
            ),
            AutomationRule(
                rule_id="auto-flag-quality-drop",
                name="Auto-flag on quality drop",
                description="Flag artifact for review when quality drops below threshold",
                event_type=AutomationEventType.QUALITY_THRESHOLD_BREACH,
                conditions={"quality_score_lt": 60},
                actions=[
                    {"type": "flag", "flag_type": "review_required"},
                    {"type": "notify", "recipients": ["knowledge_steward"]},
                ],
                approval_required=False,
            ),
            AutomationRule(
                rule_id="auto-escalate-sla-breach",
                name="Auto-escalate on SLA breach",
                description="Escalate to Knowledge Owner when SLA is breached",
                event_type=AutomationEventType.SLA_BREACHED,
                conditions={"sla_breached": True},
                actions=[
                    {"type": "escalate", "to_role": "knowledge_owner"},
                    {"type": "notify", "recipients": ["knowledge_owner"]},
                ],
                approval_required=False,
            ),
        ]

    def process_event(
        self,
        event_type: AutomationEventType,
        artifact_id: str,
        context: Optional[dict] = None,
    ) -> list[LifecycleEvent]:
        """
        Process a lifecycle event and execute matching rules.
        
        Returns list of lifecycle events created.
        """
        artifact = self.artifact_store.get(artifact_id)
        if not artifact:
            logger.error(f"Artifact not found: {artifact_id}")
            return []

        triggered_events = []
        ctx = context or {}

        for rule in self.rules:
            if not rule.enabled:
                continue
            if rule.event_type != event_type:
                continue

            # Check conditions
            if self._evaluate_conditions(rule.conditions, artifact, ctx):
                event = self._execute_rule(rule, artifact, ctx)
                if event:
                    triggered_events.append(event)

        return triggered_events

    def _evaluate_conditions(
        self,
        conditions: dict[str, Any],
        artifact: KnowledgeArtifact,
        context: dict,
    ) -> bool:
        """Evaluate rule conditions against artifact and context."""
        for condition, expected in conditions.items():
            if condition == "quality_gates_passed":
                if not context.get("quality_gates_passed", False):
                    return False

            elif condition == "quality_score_gte":
                score = self.quality_service.get_score(artifact.artifact_id)
                if not score or score.overall_score < expected:
                    return False

            elif condition == "quality_score_lt":
                score = self.quality_service.get_score(artifact.artifact_id)
                if not score or score.overall_score >= expected:
                    return False

            elif condition == "lifecycle_stage":
                if artifact.lifecycle_stage.value != expected:
                    return False

            elif condition == "retention_expired":
                if not self._is_retention_expired(artifact):
                    return False

            elif condition == "legal_hold":
                if artifact.governance.legal_hold != expected:
                    return False

            elif condition == "classification":
                if artifact.governance.classification.value not in expected:
                    return False

            elif condition == "archive_period_expired":
                if not self._is_archive_period_expired(artifact):
                    return False

            elif condition == "sla_breached":
                if not context.get("sla_breached", False):
                    return False

        return True

    def _execute_rule(
        self,
        rule: AutomationRule,
        artifact: KnowledgeArtifact,
        context: dict,
    ) -> Optional[LifecycleEvent]:
        """Execute an automation rule."""
        event = LifecycleEvent(
            event_id=f"evt-{datetime.now(timezone.utc).timestamp()}",
            artifact_id=artifact.artifact_id,
            event_type=rule.event_type,
            from_stage=artifact.lifecycle_stage,
            to_stage=None,
            triggered_by=rule.rule_id,
            triggered_at=datetime.now(timezone.utc),
            context=context,
        )

        try:
            for action in rule.actions:
                self._execute_action(action, artifact, context)

            # Determine target stage from transition action
            for action in rule.actions:
                if action["type"] == "transition":
                    event.to_stage = LifecycleStage(action["to_stage"])

            event.status = "executed"
            self.event_log.append(event)

            # Update artifact if stage changed
            if event.to_stage and event.to_stage != artifact.lifecycle_stage:
                self._transition_artifact(
                    artifact.artifact_id,
                    event.to_stage,
                    rule.rule_id,
                )

            logger.info(f"Rule {rule.rule_id} executed for {artifact.artifact_id}")

        except Exception as e:
            event.status = "failed"
            logger.error(f"Rule {rule.rule_id} failed: {e}")

        return event

    def _execute_action(
        self, action: dict, artifact: KnowledgeArtifact, context: dict
    ) -> None:
        """Execute a single action."""
        action_type = action["type"]

        if action_type == "transition":
            pass  # Handled in _execute_rule

        elif action_type == "notify":
            recipients = action.get("recipients", [])
            message = action.get("message", f"Lifecycle event for {artifact.title}")
            if self.notification_service:
                self.notification_service.notify(recipients, message)

        elif action_type == "share":
            audience = action.get("audience", "team")
            visibility = action.get("visibility", "team")
            artifact.sharing.visibility = visibility
            artifact.sharing.shared_with.append(audience)
            artifact.sharing.shared_at = datetime.now(timezone.utc)

        elif action_type == "archive":
            self.artifact_store.archive(
                artifact.artifact_id,
                reason=f"Automated: {action.get('reason', 'retention_expired')}",
            )

        elif action_type == "flag":
            flag_type = action.get("flag_type", "review_required")
            artifact.metadata["review_flag"] = flag_type
            artifact.metadata["flagged_at"] = datetime.now(timezone.utc).isoformat()

        elif action_type == "escalate":
            to_role = action.get("to_role", "knowledge_owner")
            artifact.metadata["escalated_to"] = to_role
            artifact.metadata["escalated_at"] = datetime.now(timezone.utc).isoformat()

    def _transition_artifact(
        self,
        artifact_id: str,
        new_stage: LifecycleStage,
        triggered_by: str,
    ) -> bool:
        """Transition an artifact to a new lifecycle stage."""
        success = self.artifact_store.update_lifecycle_stage(
            artifact_id, new_stage.value, triggered_by
        )

        if success:
            # Update graph node
            self.graph_client.add_artifact_node(
                self.artifact_store.get(artifact_id)
            )

        return success

    def _is_retention_expired(self, artifact: KnowledgeArtifact) -> bool:
        """Check if artifact's retention period has expired."""
        if not artifact.governance.retention_until:
            return False
        return datetime.now(timezone.utc) > artifact.governance.retention_until

    def _is_archive_period_expired(self, artifact: KnowledgeArtifact) -> bool:
        """Check if archive retention period has expired."""
        # In production, check archive date + archive retention period
        return False

    def run_scheduled_transitions(self) -> list[LifecycleEvent]:
        """Run all scheduled transitions (called by cron job)."""
        events = []

        # Find artifacts past retention
        expired = self.artifact_store.find_expired()
        for artifact in expired:
            if not artifact.governance.legal_hold:
                new_events = self.process_event(
                    AutomationEventType.RETENTION_EXPIRED,
                    artifact.artifact_id,
                    {"retention_expired": True},
                )
                events.extend(new_events)

        # Check quality scores
        artifacts = self.artifact_store.search(limit=1000)
        for artifact in artifacts:
            score = self.quality_service.get_score(artifact.artifact_id)
            if score and score.overall_score < 60:
                new_events = self.process_event(
                    AutomationEventType.QUALITY_THRESHOLD_BREACH,
                    artifact.artifact_id,
                    {"quality_score": score.overall_score},
                )
                events.extend(new_events)

        return events

    def add_rule(self, rule: AutomationRule) -> None:
        """Add a custom automation rule."""
        self.rules.append(rule)

    def get_audit_trail(self, artifact_id: str) -> list[LifecycleEvent]:
        """Get audit trail for an artifact."""
        return [e for e in self.event_log if e.artifact_id == artifact_id]
```

### 8.2 Retention Manager

```python
# lifecycle/retention_manager.py
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from models.knowledge_artifact import KnowledgeArtifact, ArtifactType, RetentionClass

logger = logging.getLogger(__name__)


class RetentionManager:
    """Manages knowledge retention policies."""

    # Retention periods in days
    RETENTION_PERIODS = {
        ArtifactType.INCIDENT_LESSONS_LEARNED: {
            "active": 7 * 365,      # 7 years
            "archive": 3 * 365,     # 3 years
            "permanent": True,       # If regulatory/public
        },
        ArtifactType.AUDIT_FINDING: {
            "active": 7 * 365,
            "archive": 3 * 365,
            "permanent": True,
        },
        ArtifactType.ASSESSMENT_RESULT: {
            "active": 7 * 365,
            "archive": 3 * 365,
            "permanent": True,
        },
        ArtifactType.POLICY_DECISION: {
            "active": None,           # Indefinite while policy active
            "archive": 7 * 365,
            "permanent": True,
        },
        ArtifactType.AGENT_BEHAVIOR_PATTERN: {
            "active": 365,            # 1 year
            "archive": 365,           # 1 year
            "permanent": False,
        },
        ArtifactType.BEST_PRACTICE: {
            "active": None,           # Indefinite while current
            "archive": 3 * 365,
            "permanent": True,
        },
        ArtifactType.CROSS_ORG_INTELLIGENCE: {
            "active": 3 * 365,
            "archive": 365,
            "permanent": False,
        },
    }

    def __init__(self, artifact_store):
        self.artifact_store = artifact_store

    def set_retention(self, artifact: KnowledgeArtifact) -> KnowledgeArtifact:
        """Set retention dates for an artifact."""
        artifact_type = artifact.artifact_type
        periods = self.RETENTION_PERIODS.get(artifact_type, {})

        active_days = periods.get("active")
        if active_days:
            artifact.governance.retention_until = (
                datetime.now(timezone.utc) + timedelta(days=active_days)
            )

        return artifact

    def check_retention_compliance(self) -> dict:
        """Check retention compliance across all artifacts."""
        artifacts = self.artifact_store.search(limit=10000)
        now = datetime.now(timezone.utc)

        compliant = 0
        non_compliant = 0
        on_legal_hold = 0
        expired = 0

        for artifact in artifacts:
            if artifact.governance.legal_hold:
                on_legal_hold += 1
                continue

            if artifact.governance.retention_until:
                if artifact.governance.retention_until < now:
                    if artifact.lifecycle_stage.value not in ("archived", "retired"):
                        expired += 1
                    else:
                        compliant += 1
                else:
                    compliant += 1
            else:
                non_compliant += 1

        return {
            "total": len(artifacts),
            "compliant": compliant,
            "non_compliant": non_compliant,
            "on_legal_hold": on_legal_hold,
            "expired": expired,
            "compliance_rate": (
                round(compliant / len(artifacts) * 100, 2)
                if artifacts
                else 100.0
            ),
        }

    def apply_legal_hold(
        self, artifact_id: str, reason: str, applied_by: str
    ) -> bool:
        """Apply legal hold to an artifact."""
        artifact = self.artifact_store.get(artifact_id)
        if not artifact:
            return False

        artifact.governance.legal_hold = True
        artifact.governance.legal_hold_reason = reason
        artifact.metadata["legal_hold_applied_by"] = applied_by
        artifact.metadata["legal_hold_applied_at"] = datetime.now(timezone.utc).isoformat()
        self.artifact_store.save(artifact)
        return True

    def release_legal_hold(
        self, artifact_id: str, released_by: str
    ) -> bool:
        """Release legal hold from an artifact."""
        artifact = self.artifact_store.get(artifact_id)
        if not artifact or not artifact.governance.legal_hold:
            return False

        artifact.governance.legal_hold = False
        artifact.metadata["legal_hold_released_by"] = released_by
        artifact.metadata["legal_hold_released_at"] = datetime.now(timezone.utc).isoformat()
        self.artifact_store.save(artifact)
        return True
```

---

## 9. Integration & Deployment

### 9.1 Docker Compose Configuration

```yaml
# docker-compose.yml
version: "3.8"

services:
  # Storage Layer
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: grc_claw
      MONGO_INITDB_ROOT_PASSWORD: secure_password

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
    environment:
      NEO4J_AUTH: neo4j/secure_password
      NEO4J_PLUGINS: '["apoc", "gds"]'

  elasticsearch:
    image: elasticsearch:8
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false

  timescaledb:
    image: timescale/timescaledb:2
    ports:
      - "5433:5432"
    volumes:
      - timescaledb_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: grc_claw
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: grc_claw_metrics

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  # Application Layer
  knowledge-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - mongodb
      - neo4j
      - elasticsearch
      - timescaledb
      - redis
    environment:
      - MONGODB_URI=mongodb://grc_claw:secure_password@mongodb:27017
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=secure_password
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - TIMESCALEDB_URI=postgresql://grc_claw:secure_password@timescaledb:5433/grc_claw_metrics
      - REDIS_URL=redis://redis:6379

  knowledge-worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    depends_on:
      - mongodb
      - neo4j
      - redis
    environment:
      - MONGODB_URI=mongodb://grc_claw:secure_password@mongodb:27017
      - NEO4J_URI=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379

  # Scheduled jobs
  knowledge-scheduler:
    build:
      context: .
      dockerfile: Dockerfile.scheduler
    depends_on:
      - mongodb
      - neo4j
      - redis
    environment:
      - MONGODB_URI=mongodb://grc_claw:secure_password@mongodb:27017
      - NEO4J_URI=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379

volumes:
  mongodb_data:
  neo4j_data:
  elasticsearch_data:
  timescaledb_data:
```

### 9.2 FastAPI Application

```python
# api/main.py
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from models.knowledge_artifact import KnowledgeArtifact, ArtifactType, Domain, Severity
from storage.mongodb_store import MongoDBKnowledgeStore
from storage.neo4j_graph import Neo4jKnowledgeGraph
from pipeline.capture_orchestrator import CapturePipeline
from pipeline.quality_gates import QualityGateEngine
from quality.quality_scorer import KnowledgeQualityScorer
from quality.quality_api import QualityScoreService
from gaps.gap_analyzer import KnowledgeGapAnalyzer
from recommendations.recommendation_engine import KnowledgeRecommendationEngine, UserProfile
from lifecycle.lifecycle_automation import LifecycleAutomationEngine
from lifecycle.retention_manager import RetentionManager
from analytics.graph_analytics import KnowledgeGraphAnalytics


# Global state
store = None
graph = None
pipeline = None
quality_service = None
gap_analyzer = None
recommendation_engine = None
lifecycle_engine = None
retention_manager = None
graph_analytics = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    global store, graph, pipeline, quality_service, gap_analyzer
    global recommendation_engine, lifecycle_engine, retention_manager, graph_analytics

    store = MongoDBKnowledgeStore()
    graph = Neo4jKnowledgeGraph()

    quality_engine = QualityGateEngine(store, graph)
    pipeline = CapturePipeline(store, graph, None, quality_engine)

    quality_scorer = KnowledgeQualityScorer(graph)
    quality_service = QualityScoreService(store, graph)

    gap_analyzer = KnowledgeGapAnalyzer(store, graph, quality_service)
    recommendation_engine = KnowledgeRecommendationEngine(store, graph, quality_service)
    lifecycle_engine = LifecycleAutomationEngine(store, graph, quality_service)
    retention_manager = RetentionManager(store)
    graph_analytics = KnowledgeGraphAnalytics(graph)

    yield

    graph.close()


app = FastAPI(
    title="GRC_Claw Knowledge Management API",
    description="Knowledge capture, storage, analytics, and lifecycle management",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Knowledge Capture ---

@app.post("/api/v1/knowledge/capture/{source_type}")
async def capture_artifact(source_type: str, event: dict):
    """Capture a knowledge artifact from a source event."""
    artifact, gate_results = pipeline.capture(
        source_type=source_type,
        source_event=event,
        captured_by=event.get("captured_by", "system"),
    )

    if not artifact:
        return JSONResponse(
            status_code=422,
            content={
                "error": "Quality gates failed",
                "gate_results": [r.__dict__ for r in gate_results],
            },
        )

    return {
        "artifact_id": artifact.artifact_id,
        "lifecycle_stage": artifact.lifecycle_stage.value,
        "gate_results": [r.__dict__ for r in gate_results],
    }


# --- Knowledge Storage ---

@app.get("/api/v1/knowledge/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Get a knowledge artifact by ID."""
    artifact = store.get(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.model_dump()


@app.get("/api/v1/knowledge/search")
async def search_artifacts(
    query: str = None,
    domain: str = None,
    artifact_type: str = None,
    severity: str = None,
    lifecycle_stage: str = None,
    limit: int = Query(default=20, le=100),
    skip: int = 0,
):
    """Search knowledge artifacts."""
    results = store.search(
        query=query,
        domain=domain,
        artifact_type=artifact_type,
        severity=severity,
        lifecycle_stage=lifecycle_stage,
        limit=limit,
        skip=skip,
    )
    return {"count": len(results), "results": [r.model_dump() for r in results]}


# --- Knowledge Quality ---

@app.post("/api/v1/knowledge/{artifact_id}/score")
async def score_artifact(artifact_id: str):
    """Score a knowledge artifact."""
    result = quality_service.score_and_update(artifact_id)
    if not result:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {
        "artifact_id": result.artifact_id,
        "overall_score": result.overall_score,
        "tier": result.tier,
        "dimensions": [
            {"name": d.name, "score": d.score, "weight": d.weight}
            for d in result.dimensions
        ],
    }


@app.get("/api/v1/knowledge/quality/domain/{domain}")
async def get_domain_quality(domain: str):
    """Get quality summary for a domain."""
    return quality_service.get_domain_quality_summary(domain)


# --- Knowledge Gap Analysis ---

@app.get("/api/v1/knowledge/gaps")
async def analyze_gaps():
    """Run knowledge gap analysis."""
    gaps = gap_analyzer.analyze_all_gaps()
    return {
        "count": len(gaps),
        "gaps": [
            {
                "gap_id": g.gap_id,
                "type": g.gap_type.value,
                "domain": g.domain,
                "severity": g.severity,
                "priority": g.priority,
                "description": g.description,
            }
            for g in gaps
        ],
    }


@app.get("/api/v1/knowledge/coverage")
async def get_coverage_matrix():
    """Get knowledge coverage matrix."""
    return gap_analyzer.compute_coverage_matrix()


# --- Knowledge Recommendations ---

@app.get("/api/v1/knowledge/recommendations/{user_id}")
async def get_recommendations(
    user_id: str,
    limit: int = Query(default=10, le=50),
    context_task: str = None,
    context_artifact_id: str = None,
):
    """Get personalized knowledge recommendations."""
    context = {}
    if context_task:
        context["current_task"] = context_task
    if context_artifact_id:
        context["current_artifact_id"] = context_artifact_id

    recommendations = recommendation_engine.recommend(
        user_id=user_id,
        context=context if context else None,
        limit=limit,
    )

    return {
        "user_id": user_id,
        "count": len(recommendations),
        "recommendations": [
            {
                "artifact_id": r.artifact_id,
                "title": r.title,
                "type": r.artifact_type,
                "score": r.score,
                "reasons": r.reasons,
            }
            for r in recommendations
        ],
    }


# --- Knowledge Graph Analytics ---

@app.get("/api/v1/knowledge/analytics/report")
async def get_analytics_report():
    """Get comprehensive graph analytics report."""
    return graph_analytics.generate_analytics_report()


@app.get("/api/v1/knowledge/analytics/influential")
async def get_influential_artifacts(limit: int = 20):
    """Get most influential artifacts."""
    return graph.get_most_influential(limit)


@app.get("/api/v1/knowledge/analytics/orphans")
async def get_orphan_artifacts():
    """Get orphan artifacts."""
    return graph.find_orphan_artifacts()


# --- Knowledge Lifecycle ---

@app.post("/api/v1/knowledge/{artifact_id}/transition")
async def transition_artifact(artifact_id: str, new_stage: str, updated_by: str):
    """Transition an artifact to a new lifecycle stage."""
    success = store.update_lifecycle_stage(artifact_id, new_stage, updated_by)
    if not success:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"artifact_id": artifact_id, "new_stage": new_stage}


@app.post("/api/v1/knowledge/{artifact_id}/archive")
async def archive_artifact(artifact_id: str, reason: str):
    """Archive a knowledge artifact."""
    success = store.archive(artifact_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"artifact_id": artifact_id, "status": "archived"}


@app.get("/api/v1/knowledge/retention/compliance")
async def get_retention_compliance():
    """Get retention compliance report."""
    return retention_manager.check_retention_compliance()


# --- Scheduled Jobs ---

@app.post("/api/v1/knowledge/jobs/run-lifecycle")
async def run_lifecycle_automation():
    """Run scheduled lifecycle transitions."""
    events = lifecycle_engine.run_scheduled_transitions()
    return {
        "events_triggered": len(events),
        "events": [
            {
                "event_id": e.event_id,
                "artifact_id": e.artifact_id,
                "from_stage": e.from_stage.value if e.from_stage else None,
                "to_stage": e.to_stage.value if e.to_stage else None,
                "status": e.status,
            }
            for e in events
        ],
    }
```

### 9.3 Requirements File

```
# requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
pymongo>=4.6.0
neo4j>=5.14.0
elasticsearch>=8.11.0
networkx>=3.2.0
numpy>=1.26.0
scikit-learn>=1.3.0
celery>=5.3.0
redis>=5.0.0
python-dateutil>=2.8.2
pyyaml>=6.0.1
jinja2>=3.1.2
```

---

## Appendix: Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd grc-claw-knowledge-management
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Start infrastructure
docker-compose up -d mongodb neo4j elasticsearch timescaledb redis

# 3. Run API
uvicorn api.main:app --reload --port 8000

# 4. Run worker (for async processing)
celery -A tasks worker --loglevel=info

# 5. Run scheduler (for lifecycle automation)
python -m scheduler.run

# 6. Test
curl -X POST http://localhost:8000/api/v1/knowledge/capture/incident \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc-001",
    "title": "Prompt Injection via External API",
    "severity": "high",
    "category": "prompt_injection",
    "root_cause": {"category": "prompt", "description": "Insufficient input validation"},
    "impact": {"affected_systems": ["chatbot"], "affected_users": 150},
    "remediation": {"immediate_actions": ["Disable external API"], "owner": "security-team"},
    "lessons_learned": {"what_happened": "Attacker injected malicious prompts"}
  }'
```

---

*End of Implementation Guide*

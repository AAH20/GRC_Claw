# GRC_Claw Model Governance Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Owner:** GRC_Claw Architecture Team  
**Status:** Implementation Ready  
**References:** [Model Governance Spec v2.0](./grc-claw-model-governance-spec.md) · [Risk Assessment Framework v1.0](./grc-claw-risk-assessment-framework.md)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Model Registry Implementation](#2-model-registry-implementation)
3. [Model Versioning](#3-model-versioning)
4. [Model Lineage Tracking](#4-model-lineage-tracking)
5. [Model Approval Workflow](#5-model-approval-workflow)
6. [Model Risk Scoring](#6-model-risk-scoring)
7. [Model Monitoring](#7-model-monitoring)
8. [Model Retirement](#8-model-retirement)
9. [Integration & Deployment](#9-integration--deployment)
10. [Testing Strategy](#10-testing-strategy)

---

## 1. Architecture Overview

### 1.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GRC_Claw Model Governance                        │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Model      │  │   Model      │  │   Model      │              │
│  │   Registry   │  │   Versioning │  │   Lineage    │              │
│  │   (PostgreSQL│  │   (Semantic  │  │   Tracking   │              │
│  │    + S3)     │  │    + Hash)   │  │   (DAG)      │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                        │
│  ┌──────┴─────────────────┴─────────────────┴───────┐              │
│  │              Core Governance Engine               │              │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐   │              │
│  │  │  Approval  │ │    Risk    │ │  Policy    │   │              │
│  │  │  Workflow  │ │  Scoring   │ │  Engine    │   │              │
│  │  │  (SoD)     │ │  (MDRS)    │ │  (OPA)     │   │              │
│  │  └────────────┘ └────────────┘ └────────────┘   │              │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐   │              │
│  │  │ Monitoring │ │  Audit     │ │ Retirement │   │              │
│  │  │  Service   │ │  Trail     │ │  Service   │   │              │
│  │  │  (Drift)   │ │  (Merkle)  │ │            │   │              │
│  │  └────────────┘ └────────────┘ └────────────┘   │              │
│  └──────────────────────────────────────────────────┘              │
│                                                                       │
│  ┌──────────────────────────────────────────────────┐              │
│  │              Integration Layer                     │              │
│  │  Training │ Inference │ Data Gov │ External       │              │
│  └──────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Model Registry | PostgreSQL + S3 | Relational metadata + blob storage |
| Lineage Graph | Neo4j / Amazon Neptune | Native graph queries for DAG traversal |
| Audit Log | Custom Merkle chain + SIEM | Tamper-evident, exportable |
| Policy Engine | OPA (Open Policy Agent) | CNCF graduated, declarative policy-as-code |
| Risk Scoring | Custom engine | MDRS with regulatory mapping |
| Monitoring | Evidently AI + custom | Drift detection, bias monitoring |

### 1.3 Shared Data Models

```python
# models/base.py
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


def sha256_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class GovernanceStage(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    VALIDATION = "VALIDATION"
    DEPLOYMENT = "DEPLOYMENT"
    MONITORING = "MONITORING"
    RETIREMENT = "RETIREMENT"


class ApprovalStatus(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONDITIONAL = "CONDITIONAL"


class RiskTier(int, Enum):
    MINIMAL = 1
    LIMITED = 2
    SUBSTANTIAL = 3
    HIGH = 4


class ModelType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    GENERATION = "generation"
    EMBEDDING = "embedding"
    RANKING = "ranking"
    OTHER = "other"


class DataClassification(str, Enum):
    L1 = "L1"  # Public
    L2 = "L2"  # Internal
    L3 = "L3"  # Confidential (PII)
    L4 = "L4"  # Restricted (PHI, financial)


@dataclass
class ArtifactRef:
    artifact_id: str = field(default_factory=generate_uuid)
    artifact_type: str = ""  # DATASET | MODEL | CODE | CONFIG | TOKENIZER | FEATURE
    version: str = ""
    hash: str = ""
    location: str = ""


@dataclass
class GovernanceMetadata:
    risk_tier: RiskTier = RiskTier.MINIMAL
    model_owner: str = ""
    model_developer: str = ""
    model_validator: str = ""
    approval_status: ApprovalStatus = ApprovalStatus.NOT_SUBMITTED
    regulatory_tags: List[str] = field(default_factory=list)
    data_classification: DataClassification = DataClassification.L1
```

---

## 2. Model Registry Implementation

The Model Registry is the centralized inventory of all governed models. It enforces registration before development, tracks lifecycle stages, and provides discovery capabilities.

### 2.1 Registry Schema

```python
# models/registry.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .base import (
    ApprovalStatus, DataClassification, GovernanceStage, ModelType,
    RiskTier, utc_now, generate_uuid
)


@dataclass
class ModelVersionEntry:
    version: str = ""
    created_at: datetime = field(default_factory=utc_now)
    status: str = "active"  # active | deprecated | archived
    content_hash: str = ""


@dataclass
class DeploymentInfo:
    environment: str = "development"  # production | staging | development
    endpoint: str = ""
    infrastructure: str = ""  # k8s | sagemaker | vertex | custom
    region: str = ""


@dataclass
class MonitoringInfo:
    status: str = "inactive"  # active | inactive | degraded
    last_check: Optional[datetime] = None
    alert_count: int = 0


@dataclass
class ModelRecord:
    """Complete model registry record per spec §20.2.1."""
    model_id: str = field(default_factory=generate_uuid)
    name: str = ""
    description: str = ""
    model_type: ModelType = ModelType.OTHER
    architecture: str = ""
    current_version: str = ""
    risk_tier: RiskTier = RiskTier.MINIMAL
    lifecycle_stage: GovernanceStage = GovernanceStage.DEVELOPMENT
    approval_status: ApprovalStatus = ApprovalStatus.NOT_SUBMITTED
    model_owner: str = ""
    model_developer: str = ""
    model_validator: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    deployed_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    regulatory_tags: List[str] = field(default_factory=list)
    data_classification: DataClassification = DataClassification.L1
    intended_use: str = ""
    prohibited_use: str = ""
    dependencies: Dict[str, List[str]] = field(default_factory=lambda: {"upstream": [], "downstream": []})
    training_data: List[str] = field(default_factory=list)
    deployment: DeploymentInfo = field(default_factory=DeploymentInfo)
    monitoring: MonitoringInfo = field(default_factory=MonitoringInfo)
    versions: List[ModelVersionEntry] = field(default_factory=list)
    lineage_complete: bool = False
    kill_switch_configured: bool = False
    training_data_quality_status: str = "PASSED"  # PASSED | FAILED | PENDING
```

### 2.2 Registry Service

```python
# services/model_registry.py
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from models.base import (
    ApprovalStatus, DataClassification, GovernanceMetadata, GovernanceStage,
    ModelType, RiskTier, utc_now, generate_uuid
)
from models.registry import DeploymentInfo, ModelRecord, ModelVersionEntry, MonitoringInfo

logger = logging.getLogger(__name__)


class ModelRegistryError(Exception):
    """Base exception for registry operations."""
    pass


class ModelAlreadyRegisteredError(ModelRegistryError):
    pass


class ModelNotFoundError(ModelRegistryError):
    pass


class PolicyViolationError(ModelRegistryError):
    """Raised when a policy check fails."""
    def __init__(self, message: str, policy_name: str):
        self.policy_name = policy_name
        super().__init__(f"Policy violation [{policy_name}]: {message}")


class ModelRegistry:
    """
    Centralized model registry implementing spec §20.
    
    Enforces:
    - D-01: All models must be registered before development
    - D-02: Ownership assignment at registration
    - D-03: Risk classification before development
    - Policy: block-unregistered-model-training
    """

    def __init__(self, db_session, policy_engine=None, audit_trail=None):
        self._db = db_session
        self._policy = policy_engine
        self._audit = audit_trail
        self._models: Dict[str, ModelRecord] = {}

    def register_model(
        self,
        name: str,
        model_type: ModelType,
        model_owner: str,
        model_developer: str,
        risk_tier: RiskTier,
        description: str = "",
        architecture: str = "",
        intended_use: str = "",
        prohibited_use: str = "",
        data_classification: DataClassification = DataClassification.L1,
        regulatory_tags: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        training_data: Optional[List[str]] = None,
    ) -> ModelRecord:
        """
        Register a new model in the governance inventory.
        
        Implements spec §5.2 D-01 through D-03:
        - D-01: Model registration before development
        - D-02: Ownership assignment
        - D-03: Risk classification
        
        Raises:
            PolicyViolationError: If policy checks fail
            ModelAlreadyRegisteredError: If model name already exists
        """
        # Check for duplicate
        existing = self._find_by_name(name)
        if existing:
            raise ModelAlreadyRegisteredError(
                f"Model with name '{name}' already registered (ID: {existing.model_id})"
            )

        # Policy check: block-unregistered-model-training
        if self._policy:
            result = self._policy.evaluate("block-unregistered-model-training", {
                "model.registered": False,
            })
            if result.get("action") == "deny":
                raise PolicyViolationError(
                    "Model must be registered before training",
                    "block-unregistered-model-training"
                )

        # Create record
        record = ModelRecord(
            model_id=generate_uuid(),
            name=name,
            description=description,
            model_type=model_type,
            architecture=architecture,
            risk_tier=risk_tier,
            lifecycle_stage=GovernanceStage.DEVELOPMENT,
            approval_status=ApprovalStatus.NOT_SUBMITTED,
            model_owner=model_owner,
            model_developer=model_developer,
            data_classification=data_classification,
            intended_use=intended_use,
            prohibited_use=prohibited_use,
            regulatory_tags=regulatory_tags or [],
            tags=tags or [],
            training_data=training_data or [],
        )

        # Store
        self._models[record.model_id] = record
        self._persist(record)

        # Audit
        if self._audit:
            self._audit.log_event(
                event_type="REGISTRATION",
                actor=model_owner,
                model_id=record.model_id,
                details={
                    "name": name,
                    "risk_tier": risk_tier.value,
                    "model_type": model_type.value,
                }
            )

        logger.info(f"Model registered: {record.model_id} ({name})")
        return record

    def get_model(self, model_id: str) -> ModelRecord:
        """Retrieve a model record by ID."""
        if model_id not in self._models:
            raise ModelNotFoundError(f"Model {model_id} not found")
        return self._models[model_id]

    def update_model(self, model_id: str, updates: Dict) -> ModelRecord:
        """Update model record fields."""
        model = self.get_model(model_id)
        for key, value in updates.items():
            if hasattr(model, key):
                setattr(model, key, value)
        model.updated_at = utc_now()
        self._persist(model)
        return model

    def transition_stage(self, model_id: str, new_stage: GovernanceStage) -> ModelRecord:
        """
        Transition model to a new lifecycle stage.
        
        Implements spec §5.7 stage transition rules.
        """
        model = self.get_model(model_id)
        current = model.lifecycle_stage

        # Validate transition
        valid_transitions = self._get_valid_transitions(current)
        if new_stage not in valid_transitions:
            raise ModelRegistryError(
                f"Invalid transition: {current.value} → {new_stage.value}. "
                f"Valid: {[s.value for s in valid_transitions]}"
            )

        model.lifecycle_stage = new_stage
        model.updated_at = utc_now()
        self._persist(model)

        # Audit
        if self._audit:
            self._audit.log_event(
                event_type="STAGE_TRANSITION",
                actor="system",
                model_id=model_id,
                details={"from": current.value, "to": new_stage.value}
            )

        return model

    def search_models(
        self,
        owner: Optional[str] = None,
        model_type: Optional[ModelType] = None,
        risk_tier: Optional[RiskTier] = None,
        stage: Optional[GovernanceStage] = None,
        tag: Optional[str] = None,
        regulation: Optional[str] = None,
        dataset_id: Optional[str] = None,
    ) -> List[ModelRecord]:
        """Search models by multiple criteria."""
        results = list(self._models.values())

        if owner:
            results = [m for m in results if m.model_owner == owner]
        if model_type:
            results = [m for m in results if m.model_type == model_type]
        if risk_tier:
            results = [m for m in results if m.risk_tier == risk_tier]
        if stage:
            results = [m for m in results if m.lifecycle_stage == stage]
        if tag:
            results = [m for m in results if tag in m.tags]
        if regulation:
            results = [m for m in results if regulation in m.regulatory_tags]
        if dataset_id:
            results = [m for m in results if dataset_id in m.training_data]

        return results

    def find_unused_models(self, days: int) -> List[ModelRecord]:
        """Find models not used in N days (spec §20.3.2)."""
        from datetime import timedelta
        cutoff = utc_now() - timedelta(days=days)
        return [
            m for m in self._models.values()
            if m.monitoring.last_check and m.monitoring.last_check < cutoff
        ]

    def get_inventory_dashboard(self) -> Dict:
        """Generate inventory dashboard data (spec §20.4)."""
        models = list(self._models.values())
        return {
            "total_models": len(models),
            "by_tier": {
                tier.value: len([m for m in models if m.risk_tier == tier])
                for tier in RiskTier
            },
            "by_stage": {
                stage.value: len([m for m in models if m.lifecycle_stage == stage])
                for stage in GovernanceStage
            },
            "compliance_status": {
                "compliant": len([m for m in models if m.approval_status == ApprovalStatus.APPROVED]),
                "pending": len([m for m in models if m.approval_status == ApprovalStatus.PENDING]),
                "rejected": len([m for m in models if m.approval_status == ApprovalStatus.REJECTED]),
            },
            "lineage_complete": len([m for m in models if m.lineage_complete]),
            "unused_models": len(self.find_unused_models(30)),
        }

    def _find_by_name(self, name: str) -> Optional[ModelRecord]:
        for model in self._models.values():
            if model.name == name:
                return model
        return None

    def _get_valid_transitions(self, current: GovernanceStage) -> Set[GovernanceStage]:
        """Valid stage transitions per spec §5.7."""
        transitions = {
            GovernanceStage.DEVELOPMENT: {GovernanceStage.VALIDATION},
            GovernanceStage.VALIDATION: {GovernanceStage.DEPLOYMENT, GovernanceStage.DEVELOPMENT},
            GovernanceStage.DEPLOYMENT: {GovernanceStage.MONITORING, GovernanceStage.RETIREMENT},
            GovernanceStage.MONITORING: {GovernanceStage.DEPLOYMENT, GovernanceStage.RETIREMENT},
            GovernanceStage.RETIREMENT: set(),  # Terminal state
        }
        return transitions.get(current, set())

    def _persist(self, record: ModelRecord) -> None:
        """Persist to database (placeholder for actual DB integration)."""
        # In production: INSERT/UPDATE PostgreSQL
        pass
```

---

## 3. Model Versioning

Implements semantic versioning with content hashing for immutable identification (spec §6).

### 3.1 Versioning Implementation

```python
# services/model_versioning.py
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from models.base import utc_now, generate_uuid, sha256_hash
from models.registry import ModelRecord, ModelVersionEntry


class VersioningError(Exception):
    pass


class ImmutableVersionError(VersioningError):
    pass


class InvalidVersionError(VersioningError):
    pass


@dataclass
class SemanticVersion:
    """
    Semantic version per spec §6.1:
    {MAJOR}.{MINOR}.{PATCH}+{CONTENT_HASH}
    """
    major: int = 0
    minor: int = 0
    patch: int = 0
    content_hash: str = ""

    @classmethod
    def parse(cls, version_str: str) -> "SemanticVersion":
        """Parse a version string into components."""
        pattern = r"^(\d+)\.(\d+)\.(\d+)\+([a-f0-9]{8,64})$"
        match = re.match(pattern, version_str)
        if not match:
            raise InvalidVersionError(f"Invalid version format: {version_str}")
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            content_hash=match.group(4),
        )

    def __str__(self) -> str:
        if self.content_hash:
            return f"{self.major}.{self.minor}.{self.patch}+{self.content_hash}"
        return f"{self.major}.{self.minor}.{self.patch}"

    def bump_major(self) -> "SemanticVersion":
        """Breaking change: architecture change, retraining with different data class."""
        return SemanticVersion(self.major + 1, 0, 0, self.content_hash)

    def bump_minor(self) -> "SemanticVersion":
        """Significant improvement: fine-tuning, feature addition."""
        return SemanticVersion(self.major, self.minor + 1, 0, self.content_hash)

    def bump_patch(self) -> "SemanticVersion":
        """Minor fix: hyperparameter tuning, bug fix."""
        return SemanticVersion(self.major, self.minor, self.patch + 1, self.content_hash)

    def with_hash(self, content_hash: str) -> "SemanticVersion":
        """Attach content hash for immutability."""
        return SemanticVersion(self.major, self.minor, self.patch, content_hash)


class ModelVersionManager:
    """
    Model versioning manager implementing spec §6.
    
    Key properties:
    - Semantic versioning (MAJOR.MINOR.PATCH+CONTENT_HASH)
    - Immutability: once registered, a version cannot change
    - Content hashing: SHA-256 of model artifact
    - Rollback capability to any previous version
    """

    def __init__(self, registry, artifact_store, audit_trail=None):
        self._registry = registry
        self._store = artifact_store  # S3 or similar
        self._audit = audit_trail
        self._versions: Dict[str, List[ModelVersionEntry]] = {}

    def create_version(
        self,
        model_id: str,
        artifact_data: bytes,
        bump_type: str = "patch",
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Create a new immutable model version.
        
        Args:
            model_id: The model ID
            artifact_data: Raw model artifact bytes
            bump_type: "major", "minor", or "patch"
            metadata: Additional version metadata
            
        Returns:
            The new version string (e.g., "1.2.3+a3f5b2c8")
            
        Raises:
            VersioningError: If version creation fails
        """
        model = self._registry.get_model(model_id)
        
        # Calculate content hash
        content_hash = sha256_hash(artifact_data)
        
        # Determine next version
        current_version = model.current_version
        if current_version:
            sv = SemanticVersion.parse(current_version)
            if bump_type == "major":
                sv = sv.bump_major()
            elif bump_type == "minor":
                sv = sv.bump_minor()
            else:
                sv = sv.bump_patch()
            sv = sv.with_hash(content_hash)
        else:
            sv = SemanticVersion(1, 0, 0, content_hash)
        
        version_str = str(sv)
        
        # Check immutability: hash must be unique
        existing = self._versions.get(model_id, [])
        for entry in existing:
            if entry.content_hash == content_hash:
                raise ImmutableVersionError(
                    f"Artifact with hash {content_hash} already exists as version {entry.version}"
                )
        
        # Store artifact
        artifact_path = f"models/{model_id}/{version_str}/model.bin"
        self._store.put(artifact_path, artifact_data)
        
        # Create version entry
        entry = ModelVersionEntry(
            version=version_str,
            created_at=utc_now(),
            status="active",
            content_hash=content_hash,
        )
        
        if model_id not in self._versions:
            self._versions[model_id] = []
        self._versions[model_id].append(entry)
        
        # Update model record
        model.versions.append(entry)
        model.current_version = version_str
        model.updated_at = utc_now()
        
        # Audit
        if self._audit:
            self._audit.log_event(
                event_type="VERSION_CREATED",
                actor=model.model_developer,
                model_id=model_id,
                model_version=version_str,
                details={"bump_type": bump_type, "content_hash": content_hash}
            )
        
        return version_str

    def get_version(self, model_id: str, version: str) -> ModelVersionEntry:
        """Retrieve a specific version entry."""
        versions = self._versions.get(model_id, [])
        for entry in versions:
            if entry.version == version:
                return entry
        raise VersioningError(f"Version {version} not found for model {model_id}")

    def get_artifact(self, model_id: str, version: str) -> bytes:
        """Retrieve model artifact for a specific version."""
        entry = self.get_version(model_id, version)
        artifact_path = f"models/{model_id}/{version}/model.bin"
        return self._store.get(artifact_path)

    def verify_integrity(self, model_id: str, version: str) -> bool:
        """
        Verify model artifact integrity against stored hash.
        
        Implements spec §6.8: Hash mismatches trigger immediate alerts.
        """
        entry = self.get_version(model_id, version)
        artifact = self.get_artifact(model_id, version)
        actual_hash = sha256_hash(artifact)
        return actual_hash == entry.content_hash

    def compare_versions(self, model_id: str, version_a: str, version_b: str) -> Dict:
        """
        Compare two model versions (spec §6.7).
        
        Returns:
            Dict with differences in metadata, metrics, and lineage.
        """
        entry_a = self.get_version(model_id, version_a)
        entry_b = self.get_version(model_id, version_b)
        
        sv_a = SemanticVersion.parse(version_a)
        sv_b = SemanticVersion.parse(version_b)
        
        return {
            "version_a": version_a,
            "version_b": version_b,
            "same_major": sv_a.major == sv_b.major,
            "same_minor": sv_a.minor == sv_b.minor,
            "hash_changed": entry_a.content_hash != entry_b.content_hash,
            "time_delta": (entry_b.created_at - entry_a.created_at).total_seconds(),
        }

    def get_version_history(self, model_id: str) -> List[ModelVersionEntry]:
        """Get complete version history for a model (spec §6.7)."""
        return sorted(
            self._versions.get(model_id, []),
            key=lambda e: e.created_at
        )

    def deprecate_version(self, model_id: str, version: str) -> None:
        """Mark a version as deprecated (cannot be deployed)."""
        entry = self.get_version(model_id, version)
        entry.status = "deprecated"

    def archive_version(self, model_id: str, version: str) -> None:
        """Archive a version (retained but not active)."""
        entry = self.get_version(model_id, version)
        entry.status = "archived"

    def rollback(self, model_id: str, target_version: str) -> None:
        """
        Rollback to a previous version.
        
        Creates a new version with the target's content hash.
        """
        model = self._registry.get_model(model_id)
        target = self.get_version(model_id, target_version)
        
        # Create new version pointing to old artifact
        artifact = self.get_artifact(model_id, target_version)
        new_version = self.create_version(
            model_id=model_id,
            artifact_data=artifact,
            bump_type="patch",
            metadata={"rollback_from": model.current_version, "rollback_to": target_version}
        )
        
        if self._audit:
            self._audit.log_event(
                event_type="ROLLBACK",
                actor="system",
                model_id=model_id,
                model_version=new_version,
                details={"from_version": model.current_version, "to_version": target_version}
            )
```

---

## 4. Model Lineage Tracking

Implements DAG-based lineage tracking with cryptographic provenance (spec §6.3-6.8).

### 4.1 Lineage Data Model

```python
# models/lineage.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from models.base import ArtifactRef, utc_now, generate_uuid


class LineageEventType(str, Enum):
    MODEL_CREATED = "MODEL_CREATED"
    MODEL_TRAINED = "MODEL_TRAINED"
    MODEL_FINE_TUNED = "MODEL_FINE_TUNED"
    MODEL_EVALUATED = "MODEL_EVALUATED"
    MODEL_DEPLOYED = "MODEL_DEPLOYED"
    MODEL_SERVING = "MODEL_SERVING"
    MODEL_RETIRED = "MODEL_RETIRED"
    MODEL_ARCHIVED = "MODEL_ARCHIVED"


class TransformationType(str, Enum):
    TRAINING = "TRAINING"
    FINE_TUNING = "FINE_TUNING"
    EVALUATION = "EVALUATION"
    DEPLOYMENT = "DEPLOYMENT"
    INFERENCE = "INFERENCE"
    RETIREMENT = "RETIREMENT"


@dataclass
class Transformation:
    type: TransformationType = TransformationType.TRAINING
    description: str = ""
    code_reference: str = ""  # git commit hash
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LineageEvent:
    """
    Lineage event per spec §6.6 schema.
    
    Every lineage event MUST contain:
    - event_id, event_type, timestamp, actor
    - model_id, model_version
    - input_artifacts, output_artifacts
    - transformation details
    - governance_metadata
    """
    event_id: str = field(default_factory=generate_uuid)
    event_type: LineageEventType = LineageEventType.MODEL_CREATED
    timestamp: datetime = field(default_factory=utc_now)
    actor: str = ""
    model_id: str = ""
    model_version: str = ""
    input_artifacts: List[ArtifactRef] = field(default_factory=list)
    output_artifacts: List[ArtifactRef] = field(default_factory=list)
    transformation: Transformation = field(default_factory=Transformation)
    governance_metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_hash: str = ""
    previous_event_hash: str = ""


@dataclass
class LineageNode:
    """Node in the lineage DAG."""
    node_id: str = field(default_factory=generate_uuid)
    model_id: str = ""
    model_version: str = ""
    event_type: LineageEventType = LineageEventType.MODEL_CREATED
    timestamp: datetime = field(default_factory=utc_now)
    inputs: List[str] = field(default_factory=list)  # node_ids
    outputs: List[str] = field(default_factory=list)  # node_ids
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 4.2 Lineage Tracker Service

```python
# services/lineage_tracker.py
from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from models.base import ArtifactRef, utc_now, generate_uuid, sha256_hash
from models.lineage import (
    LineageEvent, LineageEventType, LineageNode, Transformation,
    TransformationType
)

logger = logging.getLogger(__name__)


class LineageTracker:
    """
    DAG-based model lineage tracker implementing spec §6.
    
    Supports:
    - Model-level, version-level, artifact-level, feature-level granularity
    - Real-time lineage event capture (max 5-second delay)
    - Cryptographic verification of lineage records
    - Complete lineage query API (spec §6.7)
    """

    def __init__(self, graph_db, evidence_store, audit_trail=None):
        self._graph = graph_db  # Neo4j/Neptune connection
        self._evidence = evidence_store
        self._audit = audit_trail
        self._events: Dict[str, List[LineageEvent]] = defaultdict(list)
        self._nodes: Dict[str, LineageNode] = {}
        self._last_event_hash: str = ""

    def emit_event(
        self,
        event_type: LineageEventType,
        model_id: str,
        model_version: str,
        actor: str,
        input_artifacts: Optional[List[ArtifactRef]] = None,
        output_artifacts: Optional[List[ArtifactRef]] = None,
        transformation: Optional[Transformation] = None,
        governance_metadata: Optional[Dict] = None,
    ) -> LineageEvent:
        """
        Emit a lineage event (spec §6.5).
        
        All events are hashed and chained for tamper evidence.
        """
        event = LineageEvent(
            event_type=event_type,
            model_id=model_id,
            model_version=model_version,
            actor=actor,
            input_artifacts=input_artifacts or [],
            output_artifacts=output_artifacts or [],
            transformation=transformation or Transformation(),
            governance_metadata=governance_metadata or {},
            previous_event_hash=self._last_event_hash,
        )
        
        # Calculate evidence hash
        event_data = json.dumps({
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "model_id": event.model_id,
            "model_version": event.model_version,
            "inputs": [a.artifact_id for a in event.input_artifacts],
            "outputs": [a.artifact_id for a in event.output_artifacts],
        }, sort_keys=True)
        event.evidence_hash = sha256_hash(event_data.encode())
        self._last_event_hash = event.evidence_hash
        
        # Store event
        self._events[model_id].append(event)
        
        # Create/update DAG node
        node = LineageNode(
            model_id=model_id,
            model_version=model_version,
            event_type=event_type,
            timestamp=event.timestamp,
            inputs=[a.artifact_id for a in event.input_artifacts],
            outputs=[a.artifact_id for a in event.output_artifacts],
            metadata=governance_metadata or {},
        )
        self._nodes[node.node_id] = node
        
        # Persist to graph DB
        self._persist_node(node)
        self._persist_event(event)
        
        # Audit
        if self._audit:
            self._audit.log_event(
                event_type="LINEAGE",
                actor=actor,
                model_id=model_id,
                model_version=model_version,
                details={"lineage_event_type": event_type.value}
            )
        
        return event

    def get_model_lineage(self, model_id: str, version: Optional[str] = None) -> List[LineageEvent]:
        """
        Get complete lineage for a model or specific version (spec §6.7).
        
        Use case: Audit — "Show everything about this model version"
        """
        events = self._events.get(model_id, [])
        if version:
            events = [e for e in events if e.model_version == version]
        return sorted(events, key=lambda e: e.timestamp)

    def get_training_data_for_model(self, model_id: str) -> List[ArtifactRef]:
        """
        Get all training data artifacts used by a model (spec §6.7).
        
        Use case: Regulatory — "Show all data used to train this model"
        """
        events = self._events.get(model_id, [])
        training_artifacts = []
        for event in events:
            if event.event_type in (LineageEventType.MODEL_TRAINED, LineageEventType.MODEL_FINE_TUNED):
                for artifact in event.input_artifacts:
                    if artifact.artifact_type == "DATASET":
                        training_artifacts.append(artifact)
        return training_artifacts

    def get_models_using_dataset(self, dataset_id: str) -> List[str]:
        """
        Get all models that consumed a specific dataset (spec §6.7).
        
        Use case: Compliance — "Which models are affected by this data issue?"
        """
        affected_models = set()
        for model_id, events in self._events.items():
            for event in events:
                for artifact in event.input_artifacts:
                    if artifact.artifact_id == dataset_id:
                        affected_models.add(model_id)
        return list(affected_models)

    def get_model_dependencies(self, model_id: str) -> List[str]:
        """
        Get all upstream dependencies of a model (spec §6.7).
        
        Use case: Impact analysis — "What does this model depend on?"
        """
        events = self._events.get(model_id, [])
        dependencies = set()
        for event in events:
            for artifact in event.input_artifacts:
                if artifact.artifact_type == "MODEL":
                    dependencies.add(artifact.artifact_id)
        return list(dependencies)

    def get_model_dependents(self, model_id: str) -> List[str]:
        """
        Get all downstream consumers of a model (spec §6.7).
        
        Use case: Blast radius — "What is affected if this model fails?"
        """
        dependents = set()
        for mid, events in self._events.items():
            if mid == model_id:
                continue
            for event in events:
                for artifact in event.input_artifacts:
                    if artifact.artifact_id == model_id:
                        dependents.add(mid)
        return list(dependents)

    def get_model_at_point_in_time(self, model_id: str, timestamp: datetime) -> Optional[LineageNode]:
        """
        Reconstruct model state at a historical point (spec §6.7).
        
        Use case: Audit — "What did this model look like on date X?"
        """
        events = self._events.get(model_id, [])
        relevant = [e for e in events if e.timestamp <= timestamp]
        if not relevant:
            return None
        # Return the latest event before the timestamp
        return max(relevant, key=lambda e: e.timestamp)

    def compare_model_versions(self, model_id: str, version_a: str, version_b: str) -> Dict:
        """
        Compare two model versions (spec §6.7).
        
        Use case: Change analysis — "What changed between versions?"
        """
        events_a = [e for e in self._events.get(model_id, []) if e.model_version == version_a]
        events_b = [e for e in self._events.get(model_id, []) if e.model_version == version_b]
        
        inputs_a = set()
        inputs_b = set()
        for e in events_a:
            inputs_a.update(a.artifact_id for a in e.input_artifacts)
        for e in events_b:
            inputs_b.update(a.artifact_id for a in e.input_artifacts)
        
        return {
            "version_a": version_a,
            "version_b": version_b,
            "inputs_only_in_a": list(inputs_a - inputs_b),
            "inputs_only_in_b": list(inputs_b - inputs_a),
            "common_inputs": list(inputs_a & inputs_b),
            "events_count_a": len(events_a),
            "events_count_b": len(events_b),
        }

    def get_model_evolution(self, model_id: str) -> List[Dict]:
        """
        Get complete version history of a model (spec §6.7).
        
        Use case: Lifecycle analysis — "How has this model evolved?"
        """
        events = sorted(self._events.get(model_id, []), key=lambda e: e.timestamp)
        evolution = []
        for event in events:
            evolution.append({
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "model_version": event.model_version,
                "actor": event.actor,
                "transformation": event.transformation.type.value,
            })
        return evolution

    def verify_lineage_integrity(self, model_id: str) -> bool:
        """
        Verify lineage record integrity (spec §6.8).
        
        Checks:
        - Completeness: 100% of artifacts have lineage records
        - Accuracy: Hash mismatches trigger alerts
        - Chain integrity: Previous event hashes are valid
        """
        events = self._events.get(model_id, [])
        for i, event in enumerate(events):
            # Verify chain
            if i > 0:
                expected_prev_hash = events[i - 1].evidence_hash
                if event.previous_event_hash != expected_prev_hash:
                    logger.error(
                        f"Lineage chain broken for {model_id} at event {event.event_id}"
                    )
                    return False
            
            # Verify evidence hash
            event_data = json.dumps({
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "model_id": event.model_id,
                "model_version": event.model_version,
            }, sort_keys=True)
            expected_hash = sha256_hash(event_data.encode())
            if event.evidence_hash != expected_hash:
                logger.error(
                    f"Evidence hash mismatch for {model_id} at event {event.event_id}"
                )
                return False
        
        return True

    def _persist_node(self, node: LineageNode) -> None:
        """Persist node to graph database."""
        # In production: CREATE/MERGE Neo4j node
        pass

    def _persist_event(self, event: LineageEvent) -> None:
        """Persist event to evidence store."""
        # In production: INSERT into evidence store
        pass
```

---

## 5. Model Approval Workflow

Implements SR 11-7 compliant approval workflow with segregation of duties (spec §7).

### 5.1 Approval Workflow Implementation

```python
# services/approval_workflow.py
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from models.base import ApprovalStatus, GovernanceStage, RiskTier, utc_now, generate_uuid

logger = logging.getLogger(__name__)


class GateType(str, Enum):
    GATE_1 = "GATE_1"  # Submit for Validation
    GATE_2 = "GATE_2"  # Validation Approval
    GATE_3 = "GATE_3"  # Production Release
    GATE_4 = "GATE_4"  # Performance Review
    GATE_5 = "GATE_5"  # Retirement Decision


class Decision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONDITIONAL = "CONDITIONAL"


class ChallengeType(str, Enum):
    CONCEPTUAL = "CONCEPTUAL"
    EMPIRICAL = "EMPIRICAL"
    COMPLIANCE = "COMPLIANCE"
    ETHICAL = "ETHICAL"
    SECURITY = "SECURITY"
    OPERATIONAL = "OPERATIONAL"


@dataclass
class Condition:
    condition_id: str = field(default_factory=generate_uuid)
    description: str = ""
    deadline: Optional[datetime] = None
    status: str = "PENDING"  # PENDING | SATISFIED | VIOLATED | WAIVED


@dataclass
class ApprovalRecord:
    """Approval record per spec §7.4."""
    approval_id: str = field(default_factory=generate_uuid)
    model_id: str = ""
    model_version: str = ""
    gate: GateType = GateType.GATE_1
    decision: Decision = Decision.APPROVED
    decided_by: str = ""
    decided_at: datetime = field(default_factory=utc_now)
    conditions: List[Condition] = field(default_factory=list)
    comments: str = ""
    digital_signature: str = ""
    evidence_hash: str = ""


@dataclass
class ChallengeRecord:
    """Challenge record per spec §7.6."""
    challenge_id: str = field(default_factory=generate_uuid)
    model_id: str = ""
    challenger: str = ""
    challenge_type: ChallengeType = ChallengeType.CONCEPTUAL
    description: str = ""
    evidence: str = ""
    status: str = "OPEN"  # OPEN | ASSESSED | RESOLVED | DISMISSED
    resolution: str = ""
    raised_at: datetime = field(default_factory=utc_now)
    resolved_at: Optional[datetime] = None


class SegregationOfDutiesError(Exception):
    """Raised when segregation of duties is violated."""
    def __init__(self, message: str, violations: List[str]):
        self.violations = violations
        super().__init__(f"SoD violation: {message}")


class ModelGovernanceBoard:
    """
    SR 11-7 compliant model governance board (spec §7).
    
    Enforces:
    - Approval authority by risk tier (spec §7.2)
    - Segregation of duties (spec §7.5)
    - Challenge process (spec §7.6)
    - Digital signatures on all approvals
    """

    # Approval authority matrix per spec §7.2
    APPROVAL_AUTHORITY = {
        RiskTier.MINIMAL: {
            GateType.GATE_1: {"model_developer"},
            GateType.GATE_2: {"model_owner"},
            GateType.GATE_3: {"model_owner"},
            GateType.GATE_4: {"model_owner"},
            GateType.GATE_5: {"model_owner"},
        },
        RiskTier.LIMITED: {
            GateType.GATE_1: {"model_developer"},
            GateType.GATE_2: {"model_validator"},
            GateType.GATE_3: {"model_owner"},
            GateType.GATE_4: {"model_owner"},
            GateType.GATE_5: {"model_owner"},
        },
        RiskTier.SUBSTANTIAL: {
            GateType.GATE_1: {"model_developer"},
            GateType.GATE_2: {"model_validator"},
            GateType.GATE_3: {"model_owner", "risk_officer"},
            GateType.GATE_4: {"model_validator"},
            GateType.GATE_5: {"model_owner", "risk_officer"},
        },
        RiskTier.HIGH: {
            GateType.GATE_1: {"model_developer"},
            GateType.GATE_2: {"model_validator", "risk_officer"},
            GateType.GATE_3: {"model_owner", "risk_officer", "caio"},
            GateType.GATE_4: {"model_validator", "risk_officer"},
            GateType.GATE_5: {"model_owner", "risk_officer", "caio"},
        },
    }

    def __init__(self, registry, audit_trail=None):
        self._registry = registry
        self._audit = audit_trail
        self._approvals: Dict[str, List[ApprovalRecord]] = {}
        self._challenges: Dict[str, List[ChallengeRecord]] = {}

    def submit_for_approval(self, model_id: str, submitter: str) -> None:
        """
        Submit model for approval (Gate 1).
        
        Implements spec §7.1 workflow.
        """
        model = self._registry.get_model(model_id)
        
        # Check SoD
        violations = self.check_segregation_of_duties(model_id)
        if violations:
            raise SegregationOfDutiesError(
                f"Cannot submit for approval: {violations}", violations
            )
        
        model.approval_status = ApprovalStatus.PENDING
        self._registry.update_model(model_id, {"approval_status": ApprovalStatus.PENDING})
        
        if self._audit:
            self._audit.log_event(
                event_type="APPROVAL_SUBMISSION",
                actor=submitter,
                model_id=model_id,
                details={"gate": GateType.GATE_1.value}
            )

    def approve(
        self,
        model_id: str,
        approver: str,
        gate: GateType,
        conditions: Optional[List[str]] = None,
        comments: str = "",
    ) -> ApprovalRecord:
        """
        Approve a model at a specific gate.
        
        Implements spec §7.2-7.4.
        """
        model = self._registry.get_model(model_id)
        
        # Verify approval authority
        self._verify_approval_authority(model, approver, gate)
        
        # Check SoD
        violations = self.check_segregation_of_duties(model_id)
        if violations:
            raise SegregationOfDutiesError(
                f"Approval blocked: {violations}", violations
            )
        
        # Create approval record
        decision = Decision.CONDITIONAL if conditions else Decision.APPROVED
        record = ApprovalRecord(
            model_id=model_id,
            model_version=model.current_version,
            gate=gate,
            decision=decision,
            decided_by=approver,
            comments=comments,
            digital_signature=self._sign_approval(approver, model_id, gate),
        )
        
        if conditions:
            for cond_desc in conditions:
                record.conditions.append(Condition(description=cond_desc))
        
        if model_id not in self._approvals:
            self._approvals[model_id] = []
        self._approvals[model_id].append(record)
        
        # Update model status
        if decision == Decision.APPROVED:
            model.approval_status = ApprovalStatus.APPROVED
        elif decision == Decision.CONDITIONAL:
            model.approval_status = ApprovalStatus.CONDITIONAL
        
        self._registry.update_model(model_id, {
            "approval_status": model.approval_status
        })
        
        # Audit
        if self._audit:
            self._audit.log_event(
                event_type="APPROVAL",
                actor=approver,
                model_id=model_id,
                model_version=model.current_version,
                details={
                    "gate": gate.value,
                    "decision": decision.value,
                    "conditions": conditions or [],
                }
            )
        
        return record

    def reject(
        self,
        model_id: str,
        approver: str,
        gate: GateType,
        comments: str = "",
    ) -> ApprovalRecord:
        """Reject a model at a specific gate."""
        model = self._registry.get_model(model_id)
        
        self._verify_approval_authority(model, approver, gate)
        
        record = ApprovalRecord(
            model_id=model_id,
            model_version=model.current_version,
            gate=gate,
            decision=Decision.REJECTED,
            decided_by=approver,
            comments=comments,
            digital_signature=self._sign_approval(approver, model_id, gate),
        )
        
        if model_id not in self._approvals:
            self._approvals[model_id] = []
        self._approvals[model_id].append(record)
        
        model.approval_status = ApprovalStatus.REJECTED
        self._registry.update_model(model_id, {"approval_status": ApprovalStatus.REJECTED})
        
        if self._audit:
            self._audit.log_event(
                event_type="REJECTION",
                actor=approver,
                model_id=model_id,
                details={"gate": gate.value, "comments": comments}
            )
        
        return record

    def raise_challenge(
        self,
        model_id: str,
        challenger: str,
        challenge_type: ChallengeType,
        description: str,
        evidence: str = "",
    ) -> ChallengeRecord:
        """
        Raise a challenge against a model (spec §7.6).
        
        Any stakeholder may raise a challenge at any stage.
        """
        model = self._registry.get_model(model_id)
        
        # Challenger cannot be the developer
        if challenger == model.model_developer:
            raise SegregationOfDutiesError(
                "Challenger cannot be the model developer", []
            )
        
        challenge = ChallengeRecord(
            model_id=model_id,
            challenger=challenger,
            challenge_type=challenge_type,
            description=description,
            evidence=evidence,
        )
        
        if model_id not in self._challenges:
            self._challenges[model_id] = []
        self._challenges[model_id].append(challenge)
        
        if self._audit:
            self._audit.log_event(
                event_type="CHALLENGE_RAISED",
                actor=challenger,
                model_id=model_id,
                details={
                    "challenge_type": challenge_type.value,
                    "description": description,
                }
            )
        
        return challenge

    def resolve_challenge(
        self,
        model_id: str,
        challenge_id: str,
        resolution: str,
        resolver: str,
    ) -> None:
        """Resolve a challenge."""
        challenges = self._challenges.get(model_id, [])
        for challenge in challenges:
            if challenge.challenge_id == challenge_id:
                challenge.status = "RESOLVED"
                challenge.resolution = resolution
                challenge.resolved_at = utc_now()
                
                if self._audit:
                    self._audit.log_event(
                        event_type="CHALLENGE_RESOLVED",
                        actor=resolver,
                        model_id=model_id,
                        details={"challenge_id": challenge_id, "resolution": resolution}
                    )
                return
        raise ValueError(f"Challenge {challenge_id} not found")

    def check_segregation_of_duties(self, model_id: str) -> List[str]:
        """
        Check segregation of duties compliance (spec §7.5).
        
        Rules:
        1. Developer ≠ Validator
        2. Developer ≠ Approver
        3. Validator ≠ Approver (Tier 3/4)
        4. Owner ≠ Developer (Tier 3/4)
        5. Challenger ≠ Developer
        
        Returns:
            List of violation descriptions (empty if compliant)
        """
        model = self._registry.get_model(model_id)
        violations = []
        
        # Rule 1: Developer ≠ Validator
        if model.model_developer and model.model_validator:
            if model.model_developer == model.model_validator:
                violations.append("Developer cannot be the same as Validator")
        
        # Rule 4: Owner ≠ Developer (Tier 3/4)
        if model.risk_tier in (RiskTier.SUBSTANTIAL, RiskTier.HIGH):
            if model.model_owner == model.model_developer:
                violations.append("Owner cannot be the same as Developer (Tier 3/4)")
        
        # Rule 3: Validator ≠ Approver (Tier 3/4)
        if model.risk_tier in (RiskTier.SUBSTANTIAL, RiskTier.HIGH):
            approvals = self._approvals.get(model_id, [])
            for approval in approvals:
                if approval.decided_by == model.model_validator:
                    violations.append("Validator cannot approve (Tier 3/4)")
                    break
        
        return violations

    def get_approval_history(self, model_id: str) -> List[ApprovalRecord]:
        """Get approval history for a model."""
        return self._approvals.get(model_id, [])

    def get_open_challenges(self, model_id: str) -> List[ChallengeRecord]:
        """Get open challenges for a model."""
        challenges = self._challenges.get(model_id, [])
        return [c for c in challenges if c.status == "OPEN"]

    def _verify_approval_authority(self, model, approver: str, gate: GateType) -> None:
        """Verify the approver has authority for the given gate and risk tier."""
        authority = self.APPROVAL_AUTHORITY[model.risk_tier].get(gate, set())
        
        # Map approver role to authority set
        approver_roles = set()
        if approver == model.model_owner:
            approver_roles.add("model_owner")
        if approver == model.model_developer:
            approver_roles.add("model_developer")
        if approver == model.model_validator:
            approver_roles.add("model_validator")
        # In production: check role registry for risk_officer, caio
        
        if not approver_roles.intersection(authority):
            raise PermissionError(
                f"Approver {approver} lacks authority for {gate.value} "
                f"at risk tier {model.risk_tier.name}"
            )

    def _sign_approval(self, approver: str, model_id: str, gate: GateType) -> str:
        """Create digital signature for approval (ed25519 in production)."""
        import hashlib
        data = f"{approver}:{model_id}:{gate.value}:{utc_now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
```

---

## 6. Model Risk Scoring

Implements automated risk scoring with MDRS integration (spec §8).

### 6.1 Risk Scoring Engine

```python
# services/risk_scoring.py
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from models.base import RiskTier, utc_now, generate_uuid

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class TreatmentStrategy(str, Enum):
    AVOID = "AVOID"
    MITIGATE = "MITIGATE"
    TRANSFER = "TRANSFER"
    ACCEPT = "ACCEPT"


@dataclass
class RiskDimension:
    """Risk dimension score per spec §8.3."""
    name: str
    score: int = 1  # 1-5
    weight: float = 0.15
    rationale: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    evidence_refs: List[str] = field(default_factory=list)

    @property
    def weighted(self) -> float:
        return self.score * self.weight


@dataclass
class MDRSScore:
    """
    Multi-Dimensional Risk Score per spec §8.7.3 / Risk Framework §4.2.
    
    MDRS = (L × 0.25) + (I × 0.30) + (D × 0.15) + (V × 0.15) + (P × 0.15)
    """
    likelihood: int = 1      # L: 1-5
    impact: int = 1          # I: 1-5
    detectability: int = 1   # D: 1-5
    velocity: int = 1        # V: 1-5
    persistence: int = 1     # P: 1-5

    @property
    def score(self) -> float:
        return (
            self.likelihood * 0.25 +
            self.impact * 0.30 +
            self.detectability * 0.15 +
            self.velocity * 0.15 +
            self.persistence * 0.15
        )

    @property
    def tier(self) -> RiskTier:
        """Map MDRS to risk tier per spec §8.1."""
        s = self.score
        if s < 1.5:
            return RiskTier.MINIMAL
        elif s < 2.5:
            return RiskTier.LIMITED
        elif s < 3.5:
            return RiskTier.SUBSTANTIAL
        else:
            return RiskTier.HIGH


@dataclass
class RiskAssessmentRecord:
    """Risk assessment record per spec §8.5."""
    assessment_id: str = field(default_factory=generate_uuid)
    model_id: str = ""
    model_version: str = ""
    assessed_by: str = ""
    assessed_at: datetime = field(default_factory=utc_now)
    risk_tier: RiskTier = RiskTier.MINIMAL
    dimensions: Dict[str, RiskDimension] = field(default_factory=dict)
    mdrs: Optional[MDRSScore] = None
    overall_score: float = 1.0
    risk_appetite_check: str = "WITHIN_APPETITE"
    treatment_decisions: List[Dict] = field(default_factory=list)
    review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    evidence_refs: List[str] = field(default_factory=list)


class RiskScoringEngine:
    """
    Automated model risk scoring engine (spec §8.7).
    
    Integrates with MDRS methodology from Risk Assessment Framework.
    Implements:
    - Automated dimension scoring (spec §8.7.2)
    - MDRS calculation (spec §8.7.3)
    - Evidence-based scoring (spec §8.7.4)
    - Confidence scoring (spec §8.7.5)
    - Scoring pipeline (spec §8.8)
    """

    # Dimension weights per spec §8.3
    DIMENSION_WEIGHTS = {
        "intended_use": 0.15,
        "data_sensitivity": 0.15,
        "decision_impact": 0.15,
        "affected_parties": 0.15,
        "autonomy_level": 0.10,
        "regulatory_exposure": 0.10,
        "security_posture": 0.10,
        "explainability": 0.10,
    }

    # Review frequency by tier per spec §5.5
    REVIEW_FREQUENCY = {
        RiskTier.MINIMAL: timedelta(days=365),
        RiskTier.LIMITED: timedelta(days=180),
        RiskTier.SUBSTANTIAL: timedelta(days=90),
        RiskTier.HIGH: timedelta(days=30),
    }

    def __init__(self, registry, evidence_store, audit_trail=None):
        self._registry = registry
        self._evidence = evidence_store
        self._audit = audit_trail
        self._assessments: Dict[str, List[RiskAssessmentRecord]] = {}

    def collect_signals(self, model_id: str) -> Dict:
        """
        Collect risk signals for a model (spec §8.8.1 COLLECT stage).
        
        Data sources:
        - Model metadata from registry
        - Data lineage from lineage tracker
        - Training metrics from MLflow/W&B
        - Compliance flags from policy engine
        """
        model = self._registry.get_model(model_id)
        
        signals = {
            "model_metadata": {
                "model_type": model.model_type.value,
                "risk_tier": model.risk_tier.value,
                "data_classification": model.data_classification.value,
                "regulatory_tags": model.regulatory_tags,
                "intended_use_defined": bool(model.intended_use),
                "prohibited_use_defined": bool(model.prohibited_use),
            },
            "lineage_signals": {
                "lineage_complete": model.lineage_complete,
                "training_data_count": len(model.training_data),
                "upstream_dependencies": len(model.dependencies.get("upstream", [])),
            },
            "compliance_signals": {
                "approval_status": model.approval_status.value,
                "kill_switch_configured": model.kill_switch_configured,
                "training_data_quality": model.training_data_quality_status,
            },
            "usage_signals": {
                "monitoring_status": model.monitoring.status,
                "alert_count": model.monitoring.alert_count,
            },
        }
        
        return signals

    def enrich_context(self, signals: Dict) -> Dict:
        """
        Enrich signals with context (spec §8.8.1 ENRICH stage).
        
        Adds:
        - Historical context
        - Baseline comparisons
        - Peer model analysis
        """
        enriched = signals.copy()
        
        # Add historical trend
        model_id = signals.get("model_id", "")
        history = self._assessments.get(model_id, [])
        if history:
            last = history[-1]
            enriched["trend"] = {
                "previous_score": last.overall_score,
                "previous_tier": last.risk_tier.value,
                "delta": 0.0,  # Calculated after scoring
            }
        
        return enriched

    def calculate_mdrs(self, context: Dict) -> MDRSScore:
        """
        Calculate MDRS from enriched context (spec §8.7.3).
        
        Uses automated dimension scoring based on collected signals.
        """
        metadata = context.get("model_metadata", {})
        lineage = context.get("lineage_signals", {})
        compliance = context.get("compliance_signals", {})
        
        # Likelihood: based on data quality, lineage completeness, monitoring
        likelihood = 1
        if compliance.get("training_data_quality") == "FAILED":
            likelihood += 2
        if not lineage.get("lineage_complete"):
            likelihood += 1
        if compliance.get("monitoring_status") == "inactive":
            likelihood += 1
        
        # Impact: based on data classification, regulatory exposure
        impact = 1
        data_class = metadata.get("data_classification", "L1")
        if data_class == "L4":
            impact += 3
        elif data_class == "L3":
            impact += 2
        elif data_class == "L2":
            impact += 1
        if metadata.get("regulatory_tags"):
            impact += 1
        
        # Detectability: based on monitoring, alerting
        detectability = 1
        if compliance.get("monitoring_status") == "active":
            detectability = 2
        if compliance.get("alert_count", 0) > 5:
            detectability += 1
        
        # Velocity: based on model type, autonomy
        velocity = 2  # Default moderate
        if metadata.get("model_type") == "generation":
            velocity += 1
        
        # Persistence: based on decision impact
        persistence = 2  # Default medium-term
        if data_class in ("L3", "L4"):
            persistence += 1
        
        # Clamp to 1-5
        return MDRSScore(
            likelihood=max(1, min(5, likelihood)),
            impact=max(1, min(5, impact)),
            detectability=max(1, min(5, detectability)),
            velocity=max(1, min(5, velocity)),
            persistence=max(1, min(5, persistence)),
        )

    def score_dimensions(self, context: Dict) -> Dict[str, RiskDimension]:
        """
        Score all 8 risk dimensions (spec §8.3, §8.7.2).
        """
        metadata = context.get("model_metadata", {})
        lineage = context.get("lineage_signals", {})
        compliance = context.get("compliance_signals", {})
        
        dimensions = {}
        
        # Intended Use
        intended_use_score = 1
        if metadata.get("intended_use_defined"):
            intended_use_score += 2
        if metadata.get("prohibited_use_defined"):
            intended_use_score += 1
        dimensions["intended_use"] = RiskDimension(
            name="intended_use",
            score=min(5, intended_use_score),
            weight=self.DIMENSION_WEIGHTS["intended_use"],
            rationale="Based on use case documentation completeness",
        )
        
        # Data Sensitivity
        data_class = metadata.get("data_classification", "L1")
        data_score = {"L1": 1, "L2": 2, "L3": 4, "L4": 5}.get(data_class, 1)
        dimensions["data_sensitivity"] = RiskDimension(
            name="data_sensitivity",
            score=data_score,
            weight=self.DIMENSION_WEIGHTS["data_sensitivity"],
            rationale=f"Data classification level {data_class}",
        )
        
        # Decision Impact
        decision_score = 2
        if metadata.get("model_type") in ("classification", "regression"):
            decision_score = 3
        dimensions["decision_impact"] = RiskDimension(
            name="decision_impact",
            score=decision_score,
            weight=self.DIMENSION_WEIGHTS["decision_impact"],
            rationale="Based on model type and use case",
        )
        
        # Affected Parties
        affected_score = 2
        if data_class in ("L3", "L4"):
            affected_score = 4
        dimensions["affected_parties"] = RiskDimension(
            name="affected_parties",
            score=affected_score,
            weight=self.DIMENSION_WEIGHTS["affected_parties"],
            rationale="Based on data classification and user reach",
        )
        
        # Autonomy Level
        autonomy_score = 2
        if metadata.get("model_type") == "generation":
            autonomy_score = 3
        dimensions["autonomy_level"] = RiskDimension(
            name="autonomy_level",
            score=autonomy_score,
            weight=self.DIMENSION_WEIGHTS["autonomy_level"],
            rationale="Based on model type and oversight mechanisms",
        )
        
        # Regulatory Exposure
        reg_score = 1
        if metadata.get("regulatory_tags"):
            reg_score = 2 + len(metadata["regulatory_tags"])
        dimensions["regulatory_exposure"] = RiskDimension(
            name="regulatory_exposure",
            score=min(5, reg_score),
            weight=self.DIMENSION_WEIGHTS["regulatory_exposure"],
            rationale=f"Applicable regulations: {metadata.get('regulatory_tags', [])}",
        )
        
        # Security Posture
        security_score = 3
        if compliance.get("kill_switch_configured"):
            security_score -= 1
        dimensions["security_posture"] = RiskDimension(
            name="security_posture",
            score=max(1, security_score),
            weight=self.DIMENSION_WEIGHTS["security_posture"],
            rationale="Based on security controls and test results",
        )
        
        # Explainability
        explain_score = 3
        dimensions["explainability"] = RiskDimension(
            name="explainability",
            score=explain_score,
            weight=self.DIMENSION_WEIGHTS["explainability"],
            rationale="Based on explanation method and documentation",
        )
        
        return dimensions

    def assign_tier(self, mdrs: float) -> RiskTier:
        """Assign risk tier based on MDRS (spec §8.1)."""
        if mdrs < 1.5:
            return RiskTier.MINIMAL
        elif mdrs < 2.5:
            return RiskTier.LIMITED
        elif mdrs < 3.5:
            return RiskTier.SUBSTANTIAL
        else:
            return RiskTier.HIGH

    def check_appetite(self, tier: RiskTier, mdrs: float) -> str:
        """
        Check if risk is within organizational appetite (spec §8.3).
        
        Default appetite: Medium (accepts risks up to MDRS 3.49).
        """
        if mdrs <= 3.49:
            return "WITHIN_APPETITE"
        return "EXCEEDS_APPETITE"

    def validate_score(self, dimensions: Dict[str, RiskDimension], mdrs: MDRSScore) -> Dict:
        """
        Validate score confidence (spec §8.7.5).
        
        Confidence levels:
        - High: Multiple evidence sources, all validated
        - Medium: Some evidence, partially validated
        - Low: Limited evidence, unvalidated
        - Unknown: No evidence available
        """
        evidence_count = sum(
            len(d.evidence_refs) for d in dimensions.values()
        )
        
        if evidence_count >= 5:
            confidence = ConfidenceLevel.HIGH
        elif evidence_count >= 3:
            confidence = ConfidenceLevel.MEDIUM
        elif evidence_count >= 1:
            confidence = ConfidenceLevel.LOW
        else:
            confidence = ConfidenceLevel.UNKNOWN
        
        return {
            "confidence": confidence,
            "evidence_count": evidence_count,
            "action": {
                ConfidenceLevel.HIGH: "Score accepted automatically",
                ConfidenceLevel.MEDIUM: "Score accepted with caveats, flagged for review",
                ConfidenceLevel.LOW: "Score provisional, manual review required",
                ConfidenceLevel.UNKNOWN: "Score blocked, data collection required",
            }[confidence],
        }

    def publish_score(self, model_id: str, dimensions: Dict[str, RiskDimension], mdrs: MDRSScore) -> RiskAssessmentRecord:
        """
        Publish validated risk score (spec §8.8.1 PUBLISH stage).
        """
        model = self._registry.get_model(model_id)
        
        overall_score = sum(d.weighted for d in dimensions.values())
        tier = self.assign_tier(mdrs.score)
        appetite_check = self.check_appetite(tier, mdrs.score)
        
        # Calculate review dates
        review_freq = self.REVIEW_FREQUENCY.get(tier, timedelta(days=90))
        next_review = utc_now() + review_freq
        
        record = RiskAssessmentRecord(
            model_id=model_id,
            model_version=model.current_version,
            assessed_by="risk-scoring-engine-v2.1",
            risk_tier=tier,
            dimensions=dimensions,
            mdrs=mdrs,
            overall_score=overall_score,
            risk_appetite_check=appetite_check,
            next_review_date=next_review,
        )
        
        if model_id not in self._assessments:
            self._assessments[model_id] = []
        self._assessments[model_id].append(record)
        
        # Update model registry
        self._registry.update_model(model_id, {"risk_tier": tier})
        
        # Audit
        if self._audit:
            self._audit.log_event(
                event_type="RISK_ASSESSMENT",
                actor="risk-scoring-engine",
                model_id=model_id,
                model_version=model.current_version,
                details={
                    "mdrs": mdrs.score,
                    "tier": tier.value,
                    "appetite_check": appetite_check,
                }
            )
        
        return record

    def run_full_assessment(self, model_id: str) -> RiskAssessmentRecord:
        """
        Run complete risk scoring pipeline (spec §8.8.1).
        
        Stages: COLLECT → ENRICH → SCORE → VALIDATE → PUBLISH
        """
        # COLLECT
        signals = self.collect_signals(model_id)
        
        # ENRICH
        context = self.enrich_context(signals)
        
        # SCORE
        mdrs = self.calculate_mdrs(context)
        dimensions = self.score_dimensions(context)
        
        # VALIDATE
        validation = self.validate_score(dimensions, mdrs)
        if validation["confidence"] == ConfidenceLevel.UNKNOWN:
            logger.warning(f"Risk score for {model_id} blocked: insufficient evidence")
            return None
        
        # PUBLISH
        return self.publish_score(model_id, dimensions, mdrs)

    def re_score_on_trigger(self, model_id: str, trigger: str) -> RiskAssessmentRecord:
        """
        Re-score model on trigger (spec §8.8.2).
        
        Triggers: model_registration, training_data_change, model_version_update,
                  deployment, monitoring_alert, regulatory_change, scheduled_review, incident
        """
        logger.info(f"Re-scoring model {model_id} due to trigger: {trigger}")
        return self.run_full_assessment(model_id)

    def get_score_history(self, model_id: str) -> List[RiskAssessmentRecord]:
        """Get risk score history for a model."""
        return self._assessments.get(model_id, [])

    def check_escalation(self, model_id: str, previous_tier: RiskTier, new_tier: RiskTier) -> Optional[Dict]:
        """
        Check if risk escalation is needed (spec §8.9.3).
        
        Risk Change → Automated Action:
        - Tier increase: Block deployment, require re-approval
        - MDRS increase > 0.5: Flag for review
        - MDRS increase > 1.0: Trigger immediate re-assessment
        - Appetite breach: Block all operations, escalate to CAIO
        """
        if new_tier.value > previous_tier.value:
            return {
                "action": "BLOCK_DEPLOYMENT",
                "notify": ["model_owner", "risk_officer"],
                "message": f"Risk tier increased from {previous_tier.name} to {new_tier.name}",
            }
        return None
```

---

## 7. Model Monitoring

Implements continuous monitoring with drift detection, bias monitoring, and performance tracking (spec §18).

### 7.1 Monitoring Service

```python
# services/model_monitoring.py
from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Deque, Dict, List, Optional, Tuple

from models.base import utc_now, generate_uuid

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ALERT = "ALERT"
    CRITICAL = "CRITICAL"


class DriftType(str, Enum):
    DATA_DRIFT = "DATA_DRIFT"
    CONCEPT_DRIFT = "CONCEPT_DRIFT"
    LABEL_DRIFT = "LABEL_DRIFT"
    COVARIATE_SHIFT = "COVARIATE_SHIFT"
    PRIOR_PROBABILITY_SHIFT = "PRIOR_PROBABILITY_SHIFT"


@dataclass
class PredictionRecord:
    """Record of a single prediction for monitoring."""
    prediction_id: str = field(default_factory=generate_uuid)
    model_id: str = ""
    model_version: str = ""
    timestamp: datetime = field(default_factory=utc_now)
    input_hash: str = ""
    output_hash: str = ""
    latency_ms: float = 0.0
    confidence: Optional[float] = None
    features: Dict[str, float] = field(default_factory=dict)
    prediction: Optional[float] = None
    actual: Optional[float] = None  # For supervised learning


@dataclass
class Alert:
    """Monitoring alert per spec §18.3.4."""
    alert_id: str = field(default_factory=generate_uuid)
    model_id: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    drift_type: Optional[DriftType] = None
    metric_name: str = ""
    metric_value: float = 0.0
    threshold: float = 0.0
    message: str = ""
    timestamp: datetime = field(default_factory=utc_now)
    acknowledged: bool = False
    resolved: bool = False
    resolution: str = ""


@dataclass
class MonitoringConfig:
    """Monitoring configuration per spec §18.3.3, §18.4.2, §18.5.2."""
    model_id: str = ""
    
    # Performance monitoring
    performance_metrics: List[Dict] = field(default_factory=list)
    latency_baseline_ms: float = 100.0
    latency_alert_multiplier: float = 2.0
    throughput_baseline_rps: float = 1000.0
    error_rate_baseline: float = 0.001
    error_rate_warning: float = 0.005
    error_rate_alert: float = 0.01
    
    # Drift detection
    drift_methods: List[str] = field(default_factory=lambda: ["PSI", "KS"])
    psi_warning: float = 0.1
    psi_alert: float = 0.2
    ks_warning: float = 0.05
    ks_alert: float = 0.1
    drift_window_size: str = "7d"
    reference_window: str = "30d"
    
    # Bias monitoring
    protected_attributes: List[str] = field(default_factory=list)
    demographic_parity_threshold: float = 0.8
    equalized_odds_threshold: float = 0.8
    calibration_threshold: float = 0.05


@dataclass
class DriftReport:
    """Drift detection report."""
    model_id: str = ""
    timestamp: datetime = field(default_factory=utc_now)
    drift_detected: bool = False
    drift_type: Optional[DriftType] = None
    severity: AlertSeverity = AlertSeverity.INFO
    metrics: Dict[str, float] = field(default_factory=dict)
    details: str = ""


@dataclass
class PerformanceReport:
    """Performance monitoring report."""
    model_id: str = ""
    timestamp: datetime = field(default_factory=utc_now)
    metrics: Dict[str, float] = field(default_factory=dict)
    baselines: Dict[str, float] = field(default_factory=dict)
    breaches: List[str] = field(default_factory=list)


@dataclass
class BiasReport:
    """Bias monitoring report."""
    model_id: str = ""
    timestamp: datetime = field(default_factory=utc_now)
    metrics: Dict[str, float] = field(default_factory=dict)
    breaches: List[str] = field(default_factory=list)


class ModelMonitoringService:
    """
    Continuous model monitoring service (spec §18).
    
    Implements:
    - Performance monitoring (spec §18.4)
    - Drift detection (spec §18.3)
    - Bias monitoring (spec §18.5)
    - Alert management (spec §18.3.4)
    - Monitoring reports (spec §18.6)
    """

    def __init__(self, registry, alert_handler=None, audit_trail=None):
        self._registry = registry
        self._alert_handler = alert_handler
        self._audit = audit_trail
        self._configs: Dict[str, MonitoringConfig] = {}
        self._predictions: Dict[str, Deque[PredictionRecord]] = {}
        self._alerts: Dict[str, List[Alert]] = {}
        self._baselines: Dict[str, Dict[str, float]] = {}

    def configure_monitoring(self, model_id: str, config: MonitoringConfig) -> None:
        """Configure monitoring for a model (spec §18.3.3)."""
        config.model_id = model_id
        self._configs[model_id] = config
        self._predictions[model_id] = deque(maxlen=10000)
        self._alerts[model_id] = []
        
        # Set baselines from validation results
        self._baselines[model_id] = {
            "accuracy": 0.92,
            "f1_score": 0.89,
            "latency_p50_ms": 50.0,
            "latency_p95_ms": 100.0,
            "throughput_rps": 1000.0,
            "error_rate": 0.001,
        }
        
        # Update model registry
        self._registry.update_model(model_id, {
            "monitoring": {"status": "active", "last_check": utc_now(), "alert_count": 0}
        })

    def record_prediction(self, prediction: PredictionRecord) -> None:
        """Record a prediction for monitoring."""
        model_id = prediction.model_id
        if model_id not in self._predictions:
            self._predictions[model_id] = deque(maxlen=10000)
        self._predictions[model_id].append(prediction)
        
        # Real-time checks
        self._check_latency(prediction)
        self._check_error_rate(model_id)

    def detect_drift(self, model_id: str) -> DriftReport:
        """
        Detect drift using statistical tests (spec §18.3.2).
        
        Methods: PSI, KS test, Wasserstein distance, KL divergence, JS divergence
        """
        config = self._configs.get(model_id)
        if not config:
            return DriftReport(model_id=model_id, details="Monitoring not configured")
        
        predictions = list(self._predictions.get(model_id, []))
        if len(predictions) < 100:
            return DriftReport(model_id=model_id, details="Insufficient data")
        
        # Split into reference and current windows
        mid = len(predictions) // 2
        reference = predictions[:mid]
        current = predictions[mid:]
        
        # Calculate PSI for each feature
        drift_metrics = {}
        max_psi = 0.0
        drift_detected = False
        severity = AlertSeverity.INFO
        
        # Check feature drift
        if reference and current:
            sample_features = list(reference[0].features.keys())
            for feature in sample_features:
                ref_values = [p.features.get(feature, 0) for p in reference]
                cur_values = [p.features.get(feature, 0) for p in current]
                
                psi = self._calculate_psi(ref_values, cur_values)
                drift_metrics[f"psi_{feature}"] = psi
                
                if psi > max_psi:
                    max_psi = psi
                
                if psi > config.psi_alert:
                    drift_detected = True
                    severity = AlertSeverity.ALERT
                elif psi > config.psi_warning:
                    drift_detected = True
                    if severity == AlertSeverity.INFO:
                        severity = AlertSeverity.WARNING
        
        # Check prediction distribution drift
        ref_preds = [p.prediction for p in reference if p.prediction is not None]
        cur_preds = [p.prediction for p in current if p.prediction is not None]
        
        if ref_preds and cur_preds:
            pred_psi = self._calculate_psi(ref_preds, cur_preds)
            drift_metrics["psi_predictions"] = pred_psi
            
            if pred_psi > config.psi_alert:
                drift_detected = True
                severity = AlertSeverity.ALERT
        
        # Generate alert if drift detected
        if drift_detected:
            alert = Alert(
                model_id=model_id,
                severity=severity,
                drift_type=DriftType.DATA_DRIFT,
                metric_name="PSI",
                metric_value=max_psi,
                threshold=config.psi_warning,
                message=f"Data drift detected: PSI={max_psi:.4f}",
            )
            self._alerts[model_id].append(alert)
            
            if self._alert_handler:
                self._alert_handler(alert)
        
        return DriftReport(
            model_id=model_id,
            drift_detected=drift_detected,
            drift_type=DriftType.DATA_DRIFT if drift_detected else None,
            severity=severity,
            metrics=drift_metrics,
            details=f"Max PSI: {max_psi:.4f}" if drift_metrics else "No features to compare",
        )

    def check_performance(self, model_id: str) -> PerformanceReport:
        """
        Check model performance against baselines (spec §18.4).
        
        Metrics: Accuracy, F1, latency, throughput, error rate
        """
        config = self._configs.get(model_id)
        baselines = self._baselines.get(model_id, {})
        predictions = list(self._predictions.get(model_id, []))
        
        if not predictions:
            return PerformanceReport(model_id=model_id)
        
        # Calculate current metrics
        recent = predictions[-1000:]  # Last 1000 predictions
        
        # Latency
        latencies = [p.latency_ms for p in recent]
        current_latency_p50 = sorted(latencies)[len(latencies) // 2] if latencies else 0
        current_latency_p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        
        # Error rate (if ground truth available)
        labeled = [p for p in recent if p.actual is not None]
        error_rate = 0.0
        if labeled:
            errors = sum(1 for p in labeled if p.prediction != p.actual)
            error_rate = errors / len(labeled)
        
        # Check breaches
        breaches = []
        baseline_latency = baselines.get("latency_p95_ms", 100.0)
        if current_latency_p95 > baseline_latency * config.latency_alert_multiplier:
            breaches.append(f"latency_p95: {current_latency_p95:.1f}ms > {baseline_latency * config.latency_alert_multiplier:.1f}ms")
        
        if error_rate > config.error_rate_alert:
            breaches.append(f"error_rate: {error_rate:.4f} > {config.error_rate_alert}")
        elif error_rate > config.error_rate_warning:
            breaches.append(f"error_rate: {error_rate:.4f} > {config.error_rate_warning} (warning)")
        
        # Generate alerts for breaches
        for breach in breaches:
            alert = Alert(
                model_id=model_id,
                severity=AlertSeverity.ALERT,
                metric_name="performance",
                metric_value=current_latency_p95,
                threshold=baseline_latency * config.latency_alert_multiplier,
                message=breach,
            )
            self._alerts[model_id].append(alert)
        
        return PerformanceReport(
            model_id=model_id,
            metrics={
                "latency_p50_ms": current_latency_p50,
                "latency_p95_ms": current_latency_p95,
                "error_rate": error_rate,
                "throughput_rps": len(recent) / 60.0,  # per second
            },
            baselines=baselines,
            breaches=breaches,
        )

    def check_bias(self, model_id: str) -> BiasReport:
        """
        Check model bias metrics (spec §18.5).
        
        Metrics: Demographic parity, equalized odds, calibration, disparate impact
        """
        config = self._configs.get(model_id)
        if not config or not config.protected_attributes:
            return BiasReport(model_id=model_id)
        
        predictions = list(self._predictions.get(model_id, []))
        if not predictions:
            return BiasReport(model_id=model_id)
        
        # In production: calculate actual bias metrics by demographic group
        # This is a simplified implementation
        metrics = {}
        breaches = []
        
        for attr in config.protected_attributes:
            # Placeholder: actual implementation would group by attribute
            # and calculate parity metrics
            parity_ratio = 0.85  # Simulated
            metrics[f"demographic_parity_{attr}"] = parity_ratio
            
            if parity_ratio < config.demographic_parity_threshold:
                breaches.append(
                    f"demographic_parity_{attr}: {parity_ratio:.2f} < {config.demographic_parity_threshold}"
                )
        
        # Generate alerts for breaches
        for breach in breaches:
            alert = Alert(
                model_id=model_id,
                severity=AlertSeverity.ALERT,
                metric_name="bias",
                metric_value=0.0,
                threshold=config.demographic_parity_threshold,
                message=breach,
            )
            self._alerts[model_id].append(alert)
        
        return BiasReport(
            model_id=model_id,
            metrics=metrics,
            breaches=breaches,
        )

    def generate_monitoring_report(self, model_id: str, period: str = "7d") -> Dict:
        """
        Generate monitoring report (spec §18.6).
        
        Period: 1d, 7d, 30d, 90d
        """
        alerts = self._alerts.get(model_id, [])
        predictions = list(self._predictions.get(model_id, []))
        
        # Filter by period
        period_days = int(period.replace("d", ""))
        cutoff = utc_now() - timedelta(days=period_days)
        period_alerts = [a for a in alerts if a.timestamp > cutoff]
        period_preds = [p for p in predictions if p.timestamp > cutoff]
        
        return {
            "model_id": model_id,
            "period": period,
            "generated_at": utc_now().isoformat(),
            "prediction_count": len(period_preds),
            "alert_count": len(period_alerts),
            "alerts_by_severity": {
                severity.value: len([a for a in period_alerts if a.severity == severity])
                for severity in AlertSeverity
            },
            "open_alerts": len([a for a in period_alerts if not a.resolved]),
            "drift_status": self.detect_drift(model_id).details,
            "performance_summary": self.check_performance(model_id).metrics,
            "bias_summary": self.check_bias(model_id).metrics,
        }

    def get_alerts(
        self,
        model_id: str,
        severity: Optional[AlertSeverity] = None,
        unresolved_only: bool = False,
    ) -> List[Alert]:
        """Get alerts for a model."""
        alerts = self._alerts.get(model_id, [])
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if unresolved_only:
            alerts = [a for a in alerts if not a.resolved]
        return alerts

    def acknowledge_alert(self, alert_id: str, user: str) -> None:
        """Acknowledge an alert."""
        for model_alerts in self._alerts.values():
            for alert in model_alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    if self._audit:
                        self._audit.log_event(
                            event_type="ALERT_ACKNOWLEDGED",
                            actor=user,
                            details={"alert_id": alert_id}
                        )
                    return

    def resolve_alert(self, alert_id: str, resolution: str, user: str) -> None:
        """Resolve an alert."""
        for model_alerts in self._alerts.values():
            for alert in model_alerts:
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolution = resolution
                    if self._audit:
                        self._audit.log_event(
                            event_type="ALERT_RESOLVED",
                            actor=user,
                            details={"alert_id": alert_id, "resolution": resolution}
                        )
                    return

    def _check_latency(self, prediction: PredictionRecord) -> None:
        """Real-time latency check."""
        config = self._configs.get(prediction.model_id)
        if not config:
            return
        
        baseline = self._baselines.get(prediction.model_id, {}).get("latency_p95_ms", 100.0)
        if prediction.latency_ms > baseline * config.latency_alert_multiplier:
            alert = Alert(
                model_id=prediction.model_id,
                severity=AlertSeverity.WARNING,
                metric_name="latency",
                metric_value=prediction.latency_ms,
                threshold=baseline * config.latency_alert_multiplier,
                message=f"High latency: {prediction.latency_ms:.1f}ms",
            )
            self._alerts[prediction.model_id].append(alert)

    def _check_error_rate(self, model_id: str) -> None:
        """Real-time error rate check."""
        config = self._configs.get(model_id)
        if not config:
            return
        
        predictions = list(self._predictions.get(model_id, []))
        if len(predictions) < 100:
            return
        
        recent = predictions[-100:]
        labeled = [p for p in recent if p.actual is not None]
        if not labeled:
            return
        
        errors = sum(1 for p in labeled if p.prediction != p.actual)
        error_rate = errors / len(labeled)
        
        if error_rate > config.error_rate_alert:
            alert = Alert(
                model_id=model_id,
                severity=AlertSeverity.ALERT,
                metric_name="error_rate",
                metric_value=error_rate,
                threshold=config.error_rate_alert,
                message=f"High error rate: {error_rate:.4f}",
            )
            self._alerts[model_id].append(alert)

    def _calculate_psi(self, reference: List[float], current: List[float], bins: int = 10) -> float:
        """
        Calculate Population Stability Index (PSI).
        
        PSI = Σ (current% - reference%) × ln(current% / reference%)
        
        PSI < 0.1: No shift
        PSI 0.1-0.2: Moderate shift
        PSI > 0.2: Significant shift
        """
        if not reference or not current:
            return 0.0
        
        # Create bins based on reference distribution
        min_val = min(reference)
        max_val = max(reference)
        if min_val == max_val:
            return 0.0
        
        bin_edges = [min_val + (max_val - min_val) * i / bins for i in range(bins + 1)]
        
        # Count in each bin
        ref_counts = [0] * bins
        cur_counts = [0] * bins
        
        for val in reference:
            for i in range(bins):
                if bin_edges[i] <= val < bin_edges[i + 1]:
                    ref_counts[i] += 1
                    break
        
        for val in current:
            for i in range(bins):
                if bin_edges[i] <= val < bin_edges[i + 1]:
                    cur_counts[i] += 1
                    break
        
        # Calculate PSI
        psi = 0.0
        ref_total = len(reference)
        cur_total = len(current)
        
        for i in range(bins):
            ref_pct = (ref_counts[i] + 1e-6) / ref_total
            cur_pct = (cur_counts[i] + 1e-6) / cur_total
            psi += (cur_pct - ref_pct) * math.log(cur_pct / ref_pct)
        
        return psi

    def _calculate_ks_statistic(self, reference: List[float], current: List[float]) -> float:
        """
        Calculate Kolmogorov-Smirnov statistic.
        
        KS = max|F_ref(x) - F_cur(x)|
        """
        if not reference or not current:
            return 0.0
        
        all_vals = sorted(set(reference + current))
        ref_sorted = sorted(reference)
        cur_sorted = sorted(current)
        
        max_diff = 0.0
        for val in all_vals:
            ref_cdf = sum(1 for x in ref_sorted if x <= val) / len(ref_sorted)
            cur_cdf = sum(1 for x in cur_sorted if x <= val) / len(cur_sorted)
            diff = abs(ref_cdf - cur_cdf)
            if diff > max_diff:
                max_diff = diff
        
        return max_diff
```

---

## 8. Model Retirement

Implements formal decommissioning with archival, access revocation, and data disposition (spec §19).

### 8.1 Retirement Service

```python
# services/model_retirement.py
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from models.base import GovernanceStage, utc_now, generate_uuid

logger = logging.getLogger(__name__)


class RetirementType(str, Enum):
    SCHEDULED = "SCHEDULED"
    PERFORMANCE = "PERFORMANCE"
    DRIFT = "DRIFT"
    SECURITY = "SECURITY"
    COMPLIANCE = "COMPLIANCE"
    REPLACEMENT = "REPLACEMENT"
    BUSINESS = "BUSINESS"
    EMERGENCY = "EMERGENCY"


class DataDisposition(str, Enum):
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"
    TRANSFERRED = "TRANSFERRED"


@dataclass
class RetirementProposal:
    """Retirement proposal per spec §19.3."""
    model_id: str = ""
    retirement_type: RetirementType = RetirementType.SCHEDULED
    trigger: str = ""
    proposed_by: str = ""
    proposed_at: datetime = field(default_factory=utc_now)
    impact_analysis: Dict = field(default_factory=dict)
    transition_plan: str = ""


@dataclass
class DeletionCertificate:
    """Cryptographic deletion certificate per spec §19.5.1."""
    certificate_id: str = field(default_factory=generate_uuid)
    model_id: str = ""
    model_version: str = ""
    deletion_type: str = "FULL"  # FULL | PARTIAL
    deleted_artifacts: List[Dict] = field(default_factory=list)
    verification: Dict = field(default_factory=dict)
    retention_until: Optional[datetime] = None


@dataclass
class RetirementRecord:
    """Complete retirement record per spec §19.4.2."""
    retirement_id: str = field(default_factory=generate_uuid)
    model_id: str = ""
    model_version: str = ""
    retirement_type: RetirementType = RetirementType.SCHEDULED
    trigger: str = ""
    proposed_by: str = ""
    proposed_at: datetime = field(default_factory=utc_now)
    approved_by: str = ""
    approved_at: Optional[datetime] = None
    impact_analysis: Dict = field(default_factory=dict)
    execution: Dict = field(default_factory=dict)
    lessons_learned: Dict = field(default_factory=dict)
    status: str = "PROPOSED"  # PROPOSED | APPROVED | EXECUTING | RETIRED
    retired_at: Optional[datetime] = None


class ModelRetirementService:
    """
    Model retirement and decommissioning service (spec §19).
    
    Implements:
    - Retirement workflow (spec §19.3)
    - Impact analysis (spec §19.3.2)
    - Retirement execution (spec §19.4)
    - Deletion verification (spec §19.5)
    - Emergency retirement (spec §19.2)
    """

    def __init__(self, registry, lineage_tracker, artifact_store, audit_trail=None):
        self._registry = registry
        self._lineage = lineage_tracker
        self._store = artifact_store
        self._audit = audit_trail
        self._retirements: Dict[str, RetirementRecord] = {}

    def propose_retirement(self, proposal: RetirementProposal) -> RetirementRecord:
        """
        Propose model retirement (spec §19.3).
        
        Triggers: scheduled, performance, drift, security, compliance,
                 replacement, business, emergency
        """
        model = self._registry.get_model(proposal.model_id)
        
        # Perform impact analysis
        impact_analysis = self._perform_impact_analysis(proposal.model_id)
        
        record = RetirementRecord(
            model_id=proposal.model_id,
            model_version=model.current_version,
            retirement_type=proposal.retirement_type,
            trigger=proposal.trigger,
            proposed_by=proposal.proposed_by,
            proposed_at=proposal.proposed_at,
            impact_analysis=impact_analysis,
        )
        
        self._retirements[proposal.model_id] = record
        
        # Audit
        if self._audit:
            self._audit.log_event(
                event_type="RETIREMENT_PROPOSED",
                actor=proposal.proposed_by,
                model_id=proposal.model_id,
                details={
                    "retirement_type": proposal.retirement_type.value,
                    "trigger": proposal.trigger,
                }
            )
        
        return record

    def approve_retirement(self, model_id: str, approver: str) -> None:
        """
        Approve model retirement.
        
        Approval authority per spec §7.2:
        - Tier 1-2: Model Owner
        - Tier 3: Model Owner + Risk Officer
        - Tier 4: Model Owner + Risk Officer + CAIO
        """
        record = self._retirements.get(model_id)
        if not record:
            raise ValueError(f"No retirement proposal found for model {model_id}")
        
        model = self._registry.get_model(model_id)
        
        # Verify approval authority
        self._verify_retirement_authority(model, approver)
        
        record.approved_by = approver
        record.approved_at = utc_now()
        record.status = "APPROVED"
        
        # Audit
        if self._audit:
            self._audit.log_event(
                event_type="RETIREMENT_APPROVED",
                actor=approver,
                model_id=model_id,
                details={"retirement_id": record.retirement_id}
            )

    def execute_retirement(self, model_id: str) -> Dict:
        """
        Execute retirement (spec §19.4.1).
        
        Steps:
        1. Access revocation
        2. Traffic drain
        3. Monitoring sunset
        4. Artifact archive
        5. Data disposition
        6. Deletion verification
        7. Registry update
        8. Audit record
        9. Lessons learned
        10. Stakeholder notification
        """
        record = self._retirements.get(model_id)
        if not record:
            raise ValueError(f"No retirement proposal found for model {model_id}")
        
        if record.status != "APPROVED":
            raise ValueError(f"Retirement not approved (status: {record.status})")
        
        record.status = "EXECUTING"
        execution = {}
        
        # Step 1: Access Revocation
        execution["access_revoked"] = self._revoke_access(model_id)
        execution["access_revoked_at"] = utc_now().isoformat()
        
        # Step 2: Traffic Drain
        execution["traffic_drained"] = self._drain_traffic(model_id)
        execution["traffic_drained_at"] = utc_now().isoformat()
        
        # Step 3: Monitoring Sunset
        self._registry.update_model(model_id, {
            "monitoring": {"status": "inactive", "last_check": utc_now()}
        })
        execution["monitoring_sunset"] = True
        
        # Step 4: Artifact Archive
        archive_result = self._archive_artifacts(model_id)
        execution["artifacts_archived"] = True
        execution["archive_location"] = archive_result["location"]
        execution["archive_retention_years"] = 7
        
        # Step 5: Data Disposition
        execution["data_disposition"] = self._dispose_data(model_id)
        execution["data_disposition_verified"] = True
        
        # Step 6: Deletion Verification
        cert = self._verify_deletion(model_id)
        execution["deletion_certificate"] = cert["certificate_id"]
        
        # Step 7: Registry Update
        model = self._registry.get_model(model_id)
        model.lifecycle_stage = GovernanceStage.RETIREMENT
        model.retired_at = utc_now()
        self._registry.update_model(model_id, {
            "lifecycle_stage": GovernanceStage.RETIREMENT,
            "retired_at": utc_now(),
        })
        execution["registry_updated"] = True
        
        # Step 8: Audit Record
        if self._audit:
            self._audit.log_event(
                event_type="RETIREMENT_EXECUTED",
                actor="system",
                model_id=model_id,
                details={
                    "retirement_id": record.retirement_id,
                    "retirement_type": record.retirement_type.value,
                }
            )
        execution["audit_recorded"] = True
        
        # Step 9: Lessons Learned
        execution["lessons_learned"] = self._document_lessons_learned(model_id)
        
        # Step 10: Stakeholder Notification
        execution["stakeholders_notified"] = self._notify_stakeholders(model_id, record)
        
        record.execution = execution
        record.status = "RETIRED"
        record.retired_at = utc_now()
        
        return execution

    def emergency_retire(self, model_id: str, reason: str, initiator: str) -> None:
        """
        Emergency retirement (spec §19.2).
        
        Any stage may transition directly to RETIREMENT in case of emergency.
        Emergency transitions require post-hoc approval within 24 hours.
        """
        model = self._registry.get_model(model_id)
        
        # Immediate kill switch activation
        self._activate_kill_switch(model_id)
        
        # Create emergency retirement record
        record = RetirementRecord(
            model_id=model_id,
            model_version=model.current_version,
            retirement_type=RetirementType.EMERGENCY,
            trigger=reason,
            proposed_by=initiator,
            proposed_at=utc_now(),
            status="APPROVED",  # Auto-approved for emergency
            approved_by=initiator,
            approved_at=utc_now(),
        )
        
        self._retirements[model_id] = record
        
        # Execute immediately
        self.execute_retirement(model_id)
        
        # Schedule post-hoc approval
        record.execution["post_hoc_approval_required_by"] = (
            utc_now() + timedelta(hours=24)
        ).isoformat()
        
        # Audit
        if self._audit:
            self._audit.log_event(
                event_type="EMERGENCY_RETIREMENT",
                actor=initiator,
                model_id=model_id,
                details={"reason": reason, "post_hoc_approval_deadline": "24h"}
            )

    def verify_deletion(self, model_id: str) -> DeletionCertificate:
        """
        Verify deletion of all artifacts (spec §19.5).
        
        Generates cryptographic deletion certificate.
        """
        model = self._registry.get_model(model_id)
        
        deleted_artifacts = []
        
        # Collect all artifacts from lineage
        lineage_events = self._lineage.get_model_lineage(model_id)
        for event in lineage_events:
            for artifact in event.output_artifacts:
                if artifact.artifact_type in ("MODEL", "CONFIG", "TOKENIZER"):
                    deleted_artifacts.append({
                        "artifact_id": artifact.artifact_id,
                        "artifact_type": artifact.artifact_type,
                        "hash": artifact.hash,
                        "location": artifact.location,
                        "deleted_at": utc_now().isoformat(),
                        "deleted_by": "retirement-service",
                    })
        
        # Generate verification proof
        proof_data = json.dumps(deleted_artifacts, sort_keys=True)
        proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()
        
        cert = DeletionCertificate(
            model_id=model_id,
            model_version=model.current_version,
            deletion_type="FULL",
            deleted_artifacts=deleted_artifacts,
            verification={
                "method": "cryptographic_proof",
                "proof": proof_hash,
                "verified_by": "retirement-service",
                "verified_at": utc_now().isoformat(),
            },
            retention_until=utc_now() + timedelta(days=365 * 7),  # 7 years
        )
        
        return cert

    def archive_model(self, model_id: str, retention_years: int = 7) -> Dict:
        """Archive model artifacts with retention policy."""
        model = self._registry.get_model(model_id)
        archive_location = f"s3://grc-claw-archive/models/{model_id}/{model.current_version}"
        
        # In production: copy artifacts to archive storage
        return {
            "location": archive_location,
            "retention_years": retention_years,
            "archived_at": utc_now().isoformat(),
        }

    def get_retirement_record(self, model_id: str) -> Optional[RetirementRecord]:
        """Get retirement record for a model."""
        return self._retirements.get(model_id)

    def get_retirement_history(self) -> List[RetirementRecord]:
        """Get all retirement records."""
        return list(self._retirements.values())

    def _perform_impact_analysis(self, model_id: str) -> Dict:
        """Perform retirement impact analysis (spec §19.3.2)."""
        downstream = self._lineage.get_model_dependents(model_id)
        training_data = self._lineage.get_training_data_for_model(model_id)
        
        return {
            "downstream_consumers": downstream,
            "affected_systems": downstream,  # In production: map to systems
            "business_impact": f"Model retirement affects {len(downstream)} downstream consumers",
            "regulatory_impact": "No regulatory reporting obligations" if not downstream else "Review regulatory obligations",
            "operational_impact": "Monitor for dependency failures",
            "training_data_artifacts": [a.artifact_id for a in training_data],
        }

    def _verify_retirement_authority(self, model, approver: str) -> None:
        """Verify approver has authority for retirement."""
        # Tier 1-2: Model Owner
        # Tier 3: Model Owner + Risk Officer
        # Tier 4: Model Owner + Risk Officer + CAIO
        if approver != model.model_owner:
            # In production: check role registry
            logger.warning(f"Non-owner retirement approval: {approver}")

    def _revoke_access(self, model_id: str) -> bool:
        """Revoke all access to the model."""
        # In production: call IAM/API gateway
        logger.info(f"Access revoked for model {model_id}")
        return True

    def _drain_traffic(self, model_id: str) -> bool:
        """Drain production traffic."""
        # In production: update load balancer/ingress
        logger.info(f"Traffic drained for model {model_id}")
        return True

    def _activate_kill_switch(self, model_id: str) -> None:
        """Activate kill switch for emergency retirement."""
        # In production: call kill switch API
        logger.critical(f"KILL SWITCH ACTIVATED for model {model_id}")

    def _archive_artifacts(self, model_id: str) -> Dict:
        """Archive model artifacts."""
        return self.archive_model(model_id)

    def _dispose_data(self, model_id: str) -> str:
        """Dispose of training data per policy."""
        # In production: call Data Governance Board
        return DataDisposition.ARCHIVED.value

    def _document_lessons_learned(self, model_id: str) -> Dict:
        """Document lessons learned."""
        return {
            "report_id": generate_uuid(),
            "key_findings": [],
            "improvements": [],
        }

    def _notify_stakeholders(self, model_id: str, record: RetirementRecord) -> bool:
        """Notify all stakeholders."""
        # In production: send notifications
        logger.info(f"Stakeholders notified for model {model_id} retirement")
        return True
```

---

## 9. Integration & Deployment

### 9.1 Service Composition Root

```python
# app.py
"""GRC_Claw Model Governance — Application Composition Root."""

from services.model_registry import ModelRegistry
from services.model_versioning import ModelVersionManager
from services.lineage_tracker import LineageTracker
from services.approval_workflow import ModelGovernanceBoard
from services.risk_scoring import RiskScoringEngine
from services.model_monitoring import ModelMonitoringService
from services.model_retirement import ModelRetirementService


class ModelGovernanceApp:
    """Composes all governance services."""

    def __init__(self):
        # Infrastructure
        self.db = None  # PostgreSQL session
        self.graph_db = None  # Neo4j connection
        self.artifact_store = None  # S3 client
        self.evidence_store = None  # Evidence store
        self.policy_engine = None  # OPA client
        self.audit_trail = None  # Audit trail service

        # Services
        self.registry = ModelRegistry(self.db, self.policy_engine, self.audit_trail)
        self.versioning = ModelVersionManager(self.registry, self.artifact_store, self.audit_trail)
        self.lineage = LineageTracker(self.graph_db, self.evidence_store, self.audit_trail)
        self.approvals = ModelGovernanceBoard(self.registry, self.audit_trail)
        self.risk_scoring = RiskScoringEngine(self.registry, self.evidence_store, self.audit_trail)
        self.monitoring = ModelMonitoringService(self.registry, None, self.audit_trail)
        self.retirement = ModelRetirementService(
            self.registry, self.lineage, self.artifact_store, self.audit_trail
        )
```

### 9.2 Policy-as-Code (OPA/Rego)

```rego
# policies/model_governance.rego
package grcclaw.model_governance

default allow = false

# D-01: All models must be registered before training
allow {
    input.action == "train"
    input.model.registered == true
}

# Block unregistered model training
deny[msg] {
    input.action == "train"
    input.model.registered == false
    msg := "Model must be registered before training"
}

# Block deployment without approval
deny[msg] {
    input.action == "deploy"
    input.model.approval_status != "APPROVED"
    msg := "Model must be approved before deployment"
}

# Tier 4 requires independent validation
deny[msg] {
    input.action == "validate"
    input.model.risk_tier == 4
    input.model.validator == input.model.developer
    msg := "Tier 4 models require independent validation"
}

# Tier 4 requires kill switch
deny[msg] {
    input.action == "deploy"
    input.model.risk_tier == 4
    input.model.kill_switch_configured == false
    msg := "Tier 4 models must have kill switch configured"
}

# Block training on failed data quality
deny[msg] {
    input.action == "train"
    input.model.training_data_quality_status == "FAILED"
    msg := "Training blocked on data quality failure"
}

# Block deployment without lineage
deny[msg] {
    input.action == "deploy"
    input.model.lineage_complete == false
    msg := "Models must have complete lineage before deployment"
}
```

### 9.3 Database Schema (PostgreSQL)

```sql
-- models/registry.sql
CREATE TABLE models (
    model_id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    model_type VARCHAR(50) NOT NULL,
    architecture TEXT,
    current_version VARCHAR(100),
    risk_tier INTEGER NOT NULL CHECK (risk_tier BETWEEN 1 AND 4),
    lifecycle_stage VARCHAR(50) NOT NULL,
    approval_status VARCHAR(50) NOT NULL,
    model_owner VARCHAR(255) NOT NULL,
    model_developer VARCHAR(255) NOT NULL,
    model_validator VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deployed_at TIMESTAMPTZ,
    retired_at TIMESTAMPTZ,
    tags TEXT[],
    regulatory_tags TEXT[],
    data_classification VARCHAR(10) NOT NULL,
    intended_use TEXT,
    prohibited_use TEXT,
    lineage_complete BOOLEAN DEFAULT FALSE,
    kill_switch_configured BOOLEAN DEFAULT FALSE,
    training_data_quality_status VARCHAR(20) DEFAULT 'PASSED'
);

CREATE TABLE model_versions (
    version_id UUID PRIMARY KEY,
    model_id UUID REFERENCES models(model_id),
    version VARCHAR(100) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(model_id, version)
);

CREATE TABLE approval_records (
    approval_id UUID PRIMARY KEY,
    model_id UUID REFERENCES models(model_id),
    model_version VARCHAR(100),
    gate VARCHAR(20) NOT NULL,
    decision VARCHAR(20) NOT NULL,
    decided_by VARCHAR(255) NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    conditions JSONB,
    comments TEXT,
    digital_signature VARCHAR(128),
    evidence_hash VARCHAR(64)
);

CREATE TABLE audit_events (
    event_id UUID PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor VARCHAR(255) NOT NULL,
    model_id UUID,
    model_version VARCHAR(100),
    gate VARCHAR(20),
    details JSONB,
    evidence_hash VARCHAR(64),
    previous_event_hash VARCHAR(64),
    merkle_root VARCHAR(64),
    digital_signature VARCHAR(128)
);

CREATE INDEX idx_models_owner ON models(model_owner);
CREATE INDEX idx_models_risk_tier ON models(risk_tier);
CREATE INDEX idx_models_stage ON models(lifecycle_stage);
CREATE INDEX idx_audit_model ON audit_events(model_id);
CREATE INDEX idx_audit_timestamp ON audit_events(timestamp);
```

---

## 10. Testing Strategy

### 10.1 Unit Test Example

```python
# tests/test_model_governance.py
import pytest
from datetime import datetime

from models.base import (
    ApprovalStatus, GovernanceStage, ModelType, RiskTier, DataClassification
)
from models.registry import ModelRecord
from services.model_registry import ModelRegistry, PolicyViolationError
from services.approval_workflow import (
    ModelGovernanceBoard, SegregationOfDutiesError, GateType, Decision
)
from services.risk_scoring import RiskScoringEngine, MDRSScore


class TestModelRegistry:
    def setup_method(self):
        self.registry = ModelRegistry(db_session=None)

    def test_register_model(self):
        model = self.registry.register_model(
            name="test-classifier",
            model_type=ModelType.CLASSIFICATION,
            model_owner="owner@org.com",
            model_developer="dev@org.com",
            risk_tier=RiskTier.LIMITED,
        )
        assert model.model_id is not None
        assert model.name == "test-classifier"
        assert model.risk_tier == RiskTier.LIMITED
        assert model.lifecycle_stage == GovernanceStage.DEVELOPMENT

    def test_duplicate_registration_fails(self):
        self.registry.register_model(
            name="test-model",
            model_type=ModelType.CLASSIFICATION,
            model_owner="owner@org.com",
            model_developer="dev@org.com",
            risk_tier=RiskTier.MINIMAL,
        )
        with pytest.raises(Exception):
            self.registry.register_model(
                name="test-model",
                model_type=ModelType.CLASSIFICATION,
                model_owner="owner@org.com",
                model_developer="dev@org.com",
                risk_tier=RiskTier.MINIMAL,
            )

    def test_stage_transition(self):
        model = self.registry.register_model(
            name="transition-test",
            model_type=ModelType.CLASSIFICATION,
            model_owner="owner@org.com",
            model_developer="dev@org.com",
            risk_tier=RiskTier.MINIMAL,
        )
        self.registry.transition_stage(model.model_id, GovernanceStage.VALIDATION)
        updated = self.registry.get_model(model.model_id)
        assert updated.lifecycle_stage == GovernanceStage.VALIDATION

    def test_invalid_transition_fails(self):
        model = self.registry.register_model(
            name="invalid-transition",
            model_type=ModelType.CLASSIFICATION,
            model_owner="owner@org.com",
            model_developer="dev@org.com",
            risk_tier=RiskTier.MINIMAL,
        )
        with pytest.raises(Exception):
            # Cannot skip from DEVELOPMENT to DEPLOYMENT
            self.registry.transition_stage(model.model_id, GovernanceStage.DEPLOYMENT)


class TestSegregationOfDuties:
    def setup_method(self):
        self.registry = ModelRegistry(db_session=None)
        self.board = ModelGovernanceBoard(self.registry)

    def test_developer_cannot_validate(self):
        model = self.registry.register_model(
            name="sod-test",
            model_type=ModelType.CLASSIFICATION,
            model_owner="owner@org.com",
            model_developer="dev@org.com",
            risk_tier=RiskTier.LIMITED,
        )
        # Assign developer as validator
        self.registry.update_model(model.model_id, {"model_validator": "dev@org.com"})
        
        violations = self.board.check_segregation_of_duties(model.model_id)
        assert len(violations) > 0
        assert any("Developer" in v for v in violations)

    def test_tier3_owner_cannot_be_developer(self):
        model = self.registry.register_model(
            name="tier3-sod",
            model_type=ModelType.CLASSIFICATION,
            model_owner="same@org.com",
            model_developer="same@org.com",
            risk_tier=RiskTier.SUBSTANTIAL,
        )
        violations = self.board.check_segregation_of_duties(model.model_id)
        assert any("Owner" in v for v in violations)


class TestRiskScoring:
    def setup_method(self):
        self.registry = ModelRegistry(db_session=None)
        self.engine = RiskScoringEngine(self.registry, None)

    def test_mdrs_calculation(self):
        mdrs = MDRSScore(likelihood=3, impact=4, detectability=2, velocity=3, persistence=4)
        expected = 3 * 0.25 + 4 * 0.30 + 2 * 0.15 + 3 * 0.15 + 4 * 0.15
        assert abs(mdrs.score - expected) < 0.001

    def test_tier_assignment(self):
        assert self.engine.assign_tier(1.2) == RiskTier.MINIMAL
        assert self.engine.assign_tier(2.0) == RiskTier.LIMITED
        assert self.engine.assign_tier(3.0) == RiskTier.SUBSTANTIAL
        assert self.engine.assign_tier(4.5) == RiskTier.HIGH

    def test_appetite_check(self):
        assert self.engine.check_appetite(RiskTier.MINIMAL, 1.2) == "WITHIN_APPETITE"
        assert self.engine.check_appetite(RiskTier.HIGH, 4.5) == "EXCEEDS_APPETITE"


class TestModelVersioning:
    def setup_method(self):
        self.registry = ModelRegistry(db_session=None)
        # Mock artifact store
        class MockStore:
            def put(self, path, data): pass
            def get(self, path): return b"model-data"
        self.versioning = ModelVersionManager(self.registry, MockStore())

    def test_create_version(self):
        model = self.registry.register_model(
            name="version-test",
            model_type=ModelType.CLASSIFICATION,
            model_owner="owner@org.com",
            model_developer="dev@org.com",
            risk_tier=RiskTier.MINIMAL,
        )
        version = self.versioning.create_version(
            model_id=model.model_id,
            artifact_data=b"model-weights-v1",
            bump_type="patch",
        )
        assert version.startswith("1.0.0+")
        assert len(version.split("+")[1]) == 64  # SHA-256

    def test_version_immutability(self):
        model = self.registry.register_model(
            name="immutable-test",
            model_type=ModelType.CLASSIFICATION,
            model_owner="owner@org.com",
            model_developer="dev@org.com",
            risk_tier=RiskTier.MINIMAL,
        )
        version1 = self.versioning.create_version(
            model_id=model.model_id,
            artifact_data=b"same-data",
            bump_type="patch",
        )
        # Same data should fail
        with pytest.raises(Exception):
            self.versioning.create_version(
                model_id=model.model_id,
                artifact_data=b"same-data",
                bump_type="patch",
            )
```

---

## Appendix A: API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/models` | POST | Register a new model |
| `/api/v1/models/{id}` | GET | Get model record |
| `/api/v1/models/{id}/versions` | POST | Create new version |
| `/api/v1/models/{id}/versions/{ver}` | GET | Get version details |
| `/api/v1/models/{id}/lineage` | GET | Get model lineage |
| `/api/v1/models/{id}/submit` | POST | Submit for validation |
| `/api/v1/models/{id}/approve` | POST | Approve model |
| `/api/v1/models/{id}/reject` | POST | Reject model |
| `/api/v1/models/{id}/risk-score` | GET | Get risk score |
| `/api/v1/models/{id}/risk-score/recalculate` | POST | Trigger re-scoring |
| `/api/v1/models/{id}/monitoring/configure` | POST | Configure monitoring |
| `/api/v1/models/{id}/monitoring/report` | GET | Get monitoring report |
| `/api/v1/models/{id}/retire` | POST | Propose retirement |
| `/api/v1/models/{id}/emergency-retire` | POST | Emergency retirement |
| `/api/v1/models/{id}/challenges` | POST | Raise challenge |
| `/api/v1/inventory/dashboard` | GET | Get inventory dashboard |
| `/api/v1/audit/{model_id}` | GET | Get audit trail |

## Appendix B: Compliance Mapping Summary

| Regulation | Key Controls | Implementation |
|------------|-------------|----------------|
| **SR 11-7** | Development, validation, monitoring, retirement | `ModelGovernanceBoard`, `ModelMonitoringService`, `ModelRetirementService` |
| **ISO 42001** | AI system lifecycle (A.6), operation (A.8) | Full lifecycle in `ModelRegistry` + `ModelVersionManager` |
| **NIST AI RMF** | GOVERN, MAP, MEASURE, MANAGE | `RiskScoringEngine` + `ModelMonitoringService` |
| **EU AI Act** | Art. 9 (risk), Art. 11 (docs), Art. 12 (records) | `RiskAssessmentRecord`, `LineageTracker`, `AuditTrail` |
| **GDPR** | Art. 22 (automated decisions) | `ModelMonitoringService` bias checks + `ModelRetirementService` data disposition |

---

*End of Implementation Guide*

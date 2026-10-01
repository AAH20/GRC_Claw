# GRC_Claw Training Implementation Guide

**Document ID:** GRC-TIG-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Implementation Ready  
**Parent Documents:** GRC_Claw AI Training Framework v1.0, GRC_Claw Knowledge Management Spec v2.0

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Learning Management System (LMS)](#2-learning-management-system-lms)
3. [Competency Assessment Engine](#3-competency-assessment-engine)
4. [Personalized Learning Paths](#4-personalized-learning-paths)
5. [Training Effectiveness Measurement (Kirkpatrick)](#5-training-effectiveness-measurement-kirkpatrick)
6. [Certification Preparation](#6-certification-preparation)
7. [Continuous Learning Recommendations](#7-continuous-learning-recommendations)
8. [Learning Analytics](#8-learning-analytics)
9. [Integration Architecture](#9-integration-architecture)
10. [Deployment Guide](#10-deployment-guide)

---

## 1. Architecture Overview

### 1.1 System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    GRC_Claw Training Implementation                      │
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   LMS Core   │  │  Competency  │  │   Learning   │  │  Kirkpatrick│ │
│  │   Engine     │  │  Assessment  │  │    Path      │  │  Evaluation │ │
│  │              │  │   Engine     │  │   Engine     │  │   Engine    │ │
│  │ • Enrollment │  │ • Testing    │  │ • Adaptive   │  │ • L1-L4     │ │
│  │ • Tracking   │  │ • Validation │  │ • Role-based │  │ • ROI       │ │
│  │ • Evidence   │  │ • Gap Detect │  │ • Triggers   │  │ • Reporting │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                 │                 │                 │        │
│         └────────────┬────┴────────┬────────┴────────┬────────┘        │
│                      │             │                 │                  │
│              ┌───────▼─────────────▼─────────────────▼───────┐         │
│              │         Unified Data Layer (PostgreSQL)        │         │
│              │  • Users  • Modules  • Assessments  • Evidence │         │
│              └───────────────────────┬───────────────────────┘         │
│                                      │                                  │
│              ┌───────────────────────▼───────────────────────┐         │
│              │         Analytics & Reporting Engine           │         │
│              │  • Dashboards  • Predictive  • Audit Reports   │         │
│              └───────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| API Framework | FastAPI | Async, OpenAPI docs, Pydantic validation |
| Database | PostgreSQL 16 | JSONB for flexible schemas, ACID for evidence |
| Cache | Redis | Session management, real-time progress |
| Task Queue | Celery + Redis | Async assessment scoring, notifications |
| Search | Elasticsearch | Learning content discovery |
| Analytics | Apache Superset | Self-service dashboards |
| ML/AI | scikit-learn | Learning path recommendations |
| Document Store | MongoDB | Evidence artifacts (OSCAL format) |

### 1.3 Data Model Overview

```python
# Core entities and relationships

User (id, email, name, role, tier, department, manager_id)
  ├── LearningPath (id, user_id, status, created_at, completed_at)
  │     ├── ModuleEnrollment (id, path_id, module_id, status, progress, score)
  │     └── CompetencyAssessment (id, user_id, competency_id, level, evidence)
  ├── CompetenceProfile (id, user_id, competency_levels: dict)
  ├── CertificationRecord (id, user_id, cert_type, status, expiry)
  └── EvidenceRecord (id, user_id, clause, artifact_type, content)

Module (id, code, title, tier, competencies, format, duration, evidence_type)
Competency (id, code, name, description, levels)
Assessment (id, module_id, type, questions, passing_score)
LearningContent (id, module_id, format, content, version)
```

---

## 2. Learning Management System (LMS)

### 2.1 Core LMS Models

```python
# models/lms.py
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field


class TierLevel(int, Enum):
    """Five-tier role taxonomy from the framework."""
    ALL_STAFF = 0
    AI_USER = 1
    PRACTITIONER = 2
    GOVERNANCE = 3
    LEADERSHIP = 4


class CompetencyLevel(str, Enum):
    """Three-level competence scale."""
    AWARE = "aware"           # Understands concepts
    WORKING = "working"       # Can apply independently
    EXPERT = "expert"         # Can design, lead, and evaluate others


class ModuleCode(str, Enum):
    """14 curriculum modules."""
    M01 = "M01"  # AI Awareness & Policy
    M02 = "M02"  # Responsible AI Use
    M03 = "M03"  # AI in Your Role
    M04 = "M04"  # Output Validation & Escalation
    M05 = "M05"  # Data Handling & Classification
    M06 = "M06"  # Model Governance Fundamentals
    M07 = "M07"  # Data Provenance & Bias
    M08 = "M08"  # Testing, Validation & Monitoring
    M09 = "M09"  # AI Risk Assessment
    M10 = "M10"  # AIMS Implementation
    M11 = "M11"  # AIMS Internal Audit
    M12 = "M12"  # AI Strategy & Risk Appetite
    M13 = "M13"  # AI Incident Management
    M14 = "M14"  # Policy Update Briefing


class CompetencyCode(str, Enum):
    """10 competencies from the competence matrix."""
    C1 = "C1"   # AI Foundations
    C2 = "C2"   # AI Governance & Policy
    C3 = "C3"   # AI Risk & Impact Assessment
    C4 = "C4"   # Data & Bias
    C5 = "C5"   # AI Lifecycle & Verification
    C6 = "C6"   # Transparency & Disclosure
    C7 = "C7"   # Incident Management
    C8 = "C8"   # Legal & Ethics
    C9 = "C9"   # AIMS Implementation
    C10 = "C10" # AIMS Audit


class ClauseType(str, Enum):
    """Dual-track evidence: ISO 42001 Clause 7.2 and 7.3."""
    COMPETENCE = "7.2"    # Competence
    AWARENESS = "7.3"     # Awareness


class EnrollmentStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    EXEMPT = "exempt"


class User(BaseModel):
    """System user mapped to role taxonomy."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    email: str
    name: str
    role: str
    tier: TierLevel
    department: str
    manager_id: Optional[str] = None
    is_contractor: bool = False
    hire_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Competence profile: {competency_code: level}
    competence_levels: Dict[str, CompetencyLevel] = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "analyst@company.com",
                "name": "Jane Analyst",
                "role": "Data Analyst",
                "tier": 1,
                "department": "Finance",
                "competence_levels": {"C1": "aware", "C2": "aware"}
            }
        }


class Module(BaseModel):
    """Training module definition."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    code: ModuleCode
    title: str
    description: str
    tier: TierLevel
    competencies: List[CompetencyCode]
    clause: ClauseType
    format: str  # self-paced, instructor-led, lab, workshop, briefing
    duration_minutes: int
    passing_score: int = 70
    evidence_types: List[str]  # e.g., ["completion_record", "quiz_score"]
    prerequisites: List[ModuleCode] = []
    certification_mapping: Optional[str] = None  # e.g., "GAICC_Foundation"
    version: str = "1.0"
    is_active: bool = True


class ModuleEnrollment(BaseModel):
    """User enrollment in a specific module."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    module_id: str
    status: EnrollmentStatus = EnrollmentStatus.NOT_STARTED
    progress_percent: int = 0
    score: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    evidence_artifacts: List[Dict[str, Any]] = []  # Audit-ready evidence
    assessor_notes: Optional[str] = None
    effectiveness_rating: Optional[int] = None  # Kirkpatrick L1


class CompetencyAssessment(BaseModel):
    """Competence verification record (Clause 7.2 evidence)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    competency: CompetencyCode
    required_level: CompetencyLevel
    assessed_level: CompetencyLevel
    assessment_method: str  # quiz, scenario, artifact_review, observation
    score: int
    assessor_id: str
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    evidence_ids: List[str] = []  # Links to evidence artifacts
    next_assessment_date: Optional[datetime] = None
    is_competent: bool = False


class CertificationRecord(BaseModel):
    """External certification tracking."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    certification_type: str  # GAICC_Lead_Implementer, IAPP_AIGP, etc.
    status: str  # planned, in_progress, achieved, expired, renewal_due
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    credential_id: Optional[str] = None
    verification_url: Optional[str] = None
    cpe_credits: int = 0
    internal_equivalent: Optional[str] = None  # e.g., "AIMS_Professional_Badge"


class EvidenceRecord(BaseModel):
    """Audit-ready evidence artifact (dual-track)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    clause: ClauseType  # 7.2 or 7.3
    artifact_type: str  # completion_record, quiz_score, acknowledgment, etc.
    module_code: Optional[ModuleCode] = None
    content: Dict[str, Any]  # OSCAL-compatible evidence payload
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    captured_by: str
    retention_class: str = "standard"  # standard, extended, permanent
    hash: Optional[str] = None  # SHA-256 for tamper evidence
```

### 2.2 LMS Service Layer

```python
# services/lms_service.py
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4

from models.lms import (
    User, Module, ModuleEnrollment, CompetencyAssessment,
    CertificationRecord, EvidenceRecord, TierLevel, ModuleCode,
    CompetencyCode, CompetencyLevel, ClauseType, EnrollmentStatus
)


class LMSService:
    """Core learning management operations."""
    
    def __init__(self, db, evidence_store, notification_service):
        self.db = db
        self.evidence_store = evidence_store
        self.notifications = notification_service
    
    # ── User & Role Management ──────────────────────────────────────────
    
    async def create_user(self, user_data: dict) -> User:
        """Onboard a new user and auto-assign learning path."""
        user = User(**user_data)
        await self.db.users.insert_one(user.dict())
        
        # Auto-enroll in mandatory modules based on tier
        await self._auto_enroll(user)
        
        # Create evidence record for onboarding
        await self._create_evidence(
            user_id=user.id,
            clause=ClauseType.AWARENESS,
            artifact_type="onboarding_enrollment",
            content={"tier": user.tier, "role": user.role}
        )
        
        return user
    
    async def _auto_enroll(self, user: User) -> List[ModuleEnrollment]:
        """Enroll user in mandatory modules for their tier."""
        mandatory_modules = await self._get_mandatory_modules(user.tier)
        enrollments = []
        
        for module in mandatory_modules:
            enrollment = ModuleEnrollment(
                user_id=user.id,
                module_id=module.id,
                due_date=datetime.utcnow() + timedelta(days=30)
            )
            await self.db.enrollments.insert_one(enrollment.dict())
            enrollments.append(enrollment)
        
        return enrollments
    
    async def _get_mandatory_modules(self, tier: TierLevel) -> List[Module]:
        """Get mandatory modules for a tier level."""
        tier_modules = {
            TierLevel.ALL_STAFF: [ModuleCode.M01, ModuleCode.M02, ModuleCode.M14],
            TierLevel.AI_USER: [ModuleCode.M03, ModuleCode.M04, ModuleCode.M05],
            TierLevel.PRACTITIONER: [ModuleCode.M06, ModuleCode.M07, ModuleCode.M08, ModuleCode.M09],
            TierLevel.GOVERNANCE: [ModuleCode.M10, ModuleCode.M11],
            TierLevel.LEADERSHIP: [ModuleCode.M12],
        }
        
        codes = tier_modules.get(tier, [])
        modules = []
        for code in codes:
            module = await self.db.modules.find_one({"code": code})
            if module:
                modules.append(Module(**module))
        
        # M13 is cross-tier (incident management)
        m13 = await self.db.modules.find_one({"code": ModuleCode.M13})
        if m13:
            modules.append(Module(**m13))
        
        return modules
    
    # ── Enrollment & Progress ───────────────────────────────────────────
    
    async def enroll_in_module(
        self, user_id: str, module_id: str, 
        due_date: Optional[datetime] = None
    ) -> ModuleEnrollment:
        """Enroll a user in a specific module."""
        # Check prerequisites
        module = await self.db.modules.find_one({"id": module_id})
        if not module:
            raise ValueError(f"Module {module_id} not found")
        
        module = Module(**module)
        await self._verify_prerequisites(user_id, module)
        
        enrollment = ModuleEnrollment(
            user_id=user_id,
            module_id=module_id,
            due_date=due_date or (datetime.utcnow() + timedelta(days=30))
        )
        
        await self.db.enrollments.insert_one(enrollment.dict())
        
        # Notify user
        await self.notifications.send(
            user_id=user_id,
            type="enrollment",
            message=f"Enrolled in {module.title}. Due: {enrollment.due_date}"
        )
        
        return enrollment
    
    async def update_progress(
        self, enrollment_id: str, progress_percent: int,
        score: Optional[int] = None
    ) -> ModuleEnrollment:
        """Update learning progress and trigger completion if applicable."""
        enrollment = await self.db.enrollments.find_one({"id": enrollment_id})
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        enrollment = ModuleEnrollment(**enrollment)
        enrollment.progress_percent = min(progress_percent, 100)
        
        if score is not None:
            enrollment.score = score
        
        # Check completion
        if enrollment.progress_percent >= 100:
            enrollment.status = EnrollmentStatus.COMPLETED
            enrollment.completed_at = datetime.utcnow()
            
            # Generate evidence artifacts
            await self._generate_completion_evidence(enrollment)
            
            # Check if this completes a learning path
            await self._check_path_completion(enrollment.user_id)
        
        await self.db.enrollments.update_one(
            {"id": enrollment_id},
            {"$set": enrollment.dict()}
        )
        
        return enrollment
    
    async def _generate_completion_evidence(self, enrollment: ModuleEnrollment):
        """Generate audit-ready evidence for module completion."""
        module = await self.db.modules.find_one({"id": enrollment.module_id})
        module = Module(**module)
        
        # Clause 7.2 evidence (competence)
        if module.clause == ClauseType.COMPETENCE:
            evidence = EvidenceRecord(
                user_id=enrollment.user_id,
                clause=ClauseType.COMPETENCE,
                artifact_type="training_record",
                module_code=module.code,
                content={
                    "module_title": module.title,
                    "completion_date": enrollment.completed_at.isoformat(),
                    "score": enrollment.score,
                    "competencies": [c.value for c in module.competencies],
                    "format": module.format,
                    "duration_minutes": module.duration_minutes
                },
                captured_by="system"
            )
            await self.evidence_store.store(evidence)
            enrollment.evidence_artifacts.append(evidence.dict())
        
        # Clause 7.3 evidence (awareness)
        if module.clause == ClauseType.AWARENESS:
            evidence = EvidenceRecord(
                user_id=enrollment.user_id,
                clause=ClauseType.AWARENESS,
                artifact_type="awareness_completion",
                module_code=module.code,
                content={
                    "module_title": module.title,
                    "completion_date": enrollment.completed_at.isoformat(),
                    "acknowledgment": True,
                    "quiz_score": enrollment.score
                },
                captured_by="system"
            )
            await self.evidence_store.store(evidence)
            enrollment.evidence_artifacts.append(evidence.dict())
    
    # ── Evidence & Audit ────────────────────────────────────────────────
    
    async def get_user_evidence(
        self, user_id: str, clause: Optional[ClauseType] = None
    ) -> List[EvidenceRecord]:
        """Retrieve all evidence for a user, optionally filtered by clause."""
        query = {"user_id": user_id}
        if clause:
            query["clause"] = clause
        
        cursor = self.evidence_store.find(query)
        return [EvidenceRecord(**doc) async for doc in cursor]
    
    async def generate_audit_dossier(self, user_id: str) -> Dict[str, Any]:
        """Generate a complete audit dossier for a user."""
        user = await self.db.users.find_one({"id": user_id})
        user = User(**user)
        
        competence_evidence = await self.get_user_evidence(user_id, ClauseType.COMPETENCE)
        awareness_evidence = await self.get_user_evidence(user_id, ClauseType.AWARENESS)
        
        certifications = await self.db.certifications.find({"user_id": user_id}).to_list(None)
        
        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
                "tier": user.tier,
                "department": user.department
            },
            "competence_evidence": [e.dict() for e in competence_evidence],
            "awareness_evidence": [e.dict() for e in awareness_evidence],
            "certifications": certifications,
            "generated_at": datetime.utcnow().isoformat(),
            "dossier_id": str(uuid4())
        }
    
    # ── Trigger-Based Refresh ───────────────────────────────────────────
    
    async def handle_refresh_trigger(self, trigger_type: str, context: dict):
        """Handle continuous refresh triggers from the framework."""
        handlers = {
            "new_ai_system": self._trigger_new_system,
            "policy_update": self._trigger_policy_update,
            "incident_occurred": self._trigger_incident,
            "regulation_change": self._trigger_regulation,
            "role_change": self._trigger_role_change,
            "audit_finding": self._trigger_audit_finding,
        }
        
        handler = handlers.get(trigger_type)
        if handler:
            await handler(context)
    
    async def _trigger_policy_update(self, context: dict):
        """M14: Policy Update Briefing within 30 days."""
        affected_roles = context.get("affected_roles", [])
        all_users = await self.db.users.find({
            "role": {"$in": affected_roles} if affected_roles else {}
        }).to_list(None)
        
        for user_doc in all_users:
            user = User(**user_doc)
            m14 = await self.db.modules.find_one({"code": ModuleCode.M14})
            if m14:
                await self.enroll_in_module(
                    user_id=user.id,
                    module_id=m14["id"],
                    due_date=datetime.utcnow() + timedelta(days=30)
                )
    
    async def _trigger_incident(self, context: dict):
        """M13: Incident lessons learned within 14 days."""
        incident_id = context.get("incident_id")
        severity = context.get("severity", "medium")
        
        # All staff get awareness briefing
        all_users = await self.db.users.find({}).to_list(None)
        for user_doc in all_users:
            user = User(**user_doc)
            m13 = await self.db.modules.find_one({"code": ModuleCode.M13})
            if m13:
                await self.enroll_in_module(
                    user_id=user.id,
                    module_id=m13["id"],
                    due_date=datetime.utcnow() + timedelta(days=14)
                )
        
        # Create knowledge artifact link
        await self._create_evidence(
            user_id="system",
            clause=ClauseType.AWARENESS,
            artifact_type="incident_lessons_learned",
            content={
                "incident_id": incident_id,
                "severity": severity,
                "trigger": "incident_occurred",
                "briefing_deadline": (datetime.utcnow() + timedelta(days=14)).isoformat()
            }
        )
```

### 2.3 LMS API Endpoints

```python
# api/lms_routes.py
from fastapi import FastAPI, HTTPException, Depends, Query
from typing import List, Optional

app = FastAPI(title="GRC_Claw LMS API")


@app.post("/api/v1/users", response_model=User)
async def create_user(user_data: dict, lms: LMSService = Depends(get_lms)):
    """Create a new user and auto-assign learning path."""
    return await lms.create_user(user_data)


@app.get("/api/v1/users/{user_id}/dashboard")
async def get_dashboard(user_id: str, lms: LMSService = Depends(get_lms)):
    """Get user's learning dashboard."""
    enrollments = await lms.get_user_enrollments(user_id)
    competence = await lms.get_competence_profile(user_id)
    certifications = await lms.get_certifications(user_id)
    
    return {
        "enrollments": [e.dict() for e in enrollments],
        "competence_profile": competence,
        "certifications": [c.dict() for c in certifications],
        "overall_progress": calculate_overall_progress(enrollments),
        "upcoming_deadlines": get_upcoming_deadlines(enrollments),
        "recommended_next": await lms.get_recommendations(user_id)
    }


@app.post("/api/v1/enrollments/{enrollment_id}/progress")
async def update_progress(
    enrollment_id: str,
    progress: int,
    score: Optional[int] = None,
    lms: LMSService = Depends(get_lms)
):
    """Update learning progress."""
    return await lms.update_progress(enrollment_id, progress, score)


@app.get("/api/v1/users/{user_id}/evidence")
async def get_evidence(
    user_id: str,
    clause: Optional[ClauseType] = None,
    lms: LMSService = Depends(get_lms)
):
    """Get user's audit evidence."""
    return await lms.get_user_evidence(user_id, clause)


@app.get("/api/v1/users/{user_id}/audit-dossier")
async def get_audit_dossier(user_id: str, lms: LMSService = Depends(get_lms)):
    """Generate complete audit dossier for a user."""
    return await lms.generate_audit_dossier(user_id)


@app.post("/api/v1/triggers/{trigger_type}")
async def handle_trigger(
    trigger_type: str,
    context: dict,
    lms: LMSService = Depends(get_lms)
):
    """Handle refresh triggers (policy update, incident, etc.)."""
    await lms.handle_refresh_trigger(trigger_type, context)
    return {"status": "processed", "trigger": trigger_type}
```

---

## 3. Competency Assessment Engine

### 3.1 Competence Matrix Implementation

```python
# services/competency_engine.py
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from models.lms import (
    CompetencyCode, CompetencyLevel, TierLevel, User,
    CompetencyAssessment, ModuleCode, ClauseType
)


# ── The 10×5 Competence Matrix ──────────────────────────────────────────
# Defines required competency level for each role tier
# Format: {competency_code: {tier: required_level}}

COMPETENCE_MATRIX: Dict[str, Dict[int, Optional[str]]] = {
    CompetencyCode.C1: {  # AI Foundations
        0: CompetencyLevel.AWARE,
        1: CompetencyLevel.WORKING,
        2: CompetencyLevel.EXPERT,
        3: CompetencyLevel.WORKING,
        4: CompetencyLevel.AWARE,
    },
    CompetencyCode.C2: {  # AI Governance & Policy
        0: None,
        1: CompetencyLevel.AWARE,
        2: CompetencyLevel.WORKING,
        3: CompetencyLevel.EXPERT,
        4: CompetencyLevel.WORKING,
    },
    CompetencyCode.C3: {  # AI Risk & Impact Assessment
        0: None,
        1: None,
        2: CompetencyLevel.WORKING,
        3: CompetencyLevel.EXPERT,
        4: CompetencyLevel.WORKING,
    },
    CompetencyCode.C4: {  # Data & Bias
        0: None,
        1: CompetencyLevel.AWARE,
        2: CompetencyLevel.EXPERT,
        3: CompetencyLevel.WORKING,
        4: None,
    },
    CompetencyCode.C5: {  # AI Lifecycle & Verification
        0: None,
        1: None,
        2: CompetencyLevel.EXPERT,
        3: CompetencyLevel.WORKING,
        4: None,
    },
    CompetencyCode.C6: {  # Transparency & Disclosure
        0: None,
        1: CompetencyLevel.AWARE,
        2: CompetencyLevel.WORKING,
        3: CompetencyLevel.EXPERT,
        4: CompetencyLevel.WORKING,
    },
    CompetencyCode.C7: {  # Incident Management
        0: None,
        1: CompetencyLevel.AWARE,
        2: CompetencyLevel.WORKING,
        3: CompetencyLevel.EXPERT,
        4: CompetencyLevel.WORKING,
    },
    CompetencyCode.C8: {  # Legal & Ethics
        0: None,
        1: CompetencyLevel.AWARE,
        2: CompetencyLevel.WORKING,
        3: CompetencyLevel.EXPERT,
        4: CompetencyLevel.WORKING,
    },
    CompetencyCode.C9: {  # AIMS Implementation
        0: None,
        1: None,
        2: None,
        3: CompetencyLevel.EXPERT,
        4: None,
    },
    CompetencyCode.C10: {  # AIMS Audit
        0: None,
        1: None,
        2: None,
        3: CompetencyLevel.EXPERT,
        4: None,
    },
}


# ── Module-to-Competency Mapping ───────────────────────────────────────
# Maps each module to the competencies it assesses

MODULE_COMPETENCY_MAP: Dict[str, List[str]] = {
    ModuleCode.M01: [CompetencyCode.C1],
    ModuleCode.M02: [CompetencyCode.C1, CompetencyCode.C2],
    ModuleCode.M03: [CompetencyCode.C1, CompetencyCode.C2, CompetencyCode.C6],
    ModuleCode.M04: [CompetencyCode.C5, CompetencyCode.C7],
    ModuleCode.M05: [CompetencyCode.C4, CompetencyCode.C8],
    ModuleCode.M06: [CompetencyCode.C2, CompetencyCode.C5],
    ModuleCode.M07: [CompetencyCode.C4, CompetencyCode.C5],
    ModuleCode.M08: [CompetencyCode.C5, CompetencyCode.C7],
    ModuleCode.M09: [CompetencyCode.C3, CompetencyCode.C8],
    ModuleCode.M10: [CompetencyCode.C9, CompetencyCode.C2, CompetencyCode.C3],
    ModuleCode.M11: [CompetencyCode.C10, CompetencyCode.C9],
    ModuleCode.M12: [CompetencyCode.C2, CompetencyCode.C3, CompetencyCode.C8],
    ModuleCode.M13: [CompetencyCode.C7],
    ModuleCode.M14: [CompetencyCode.C2],
}


class CompetencyAssessmentEngine:
    """Assesses and tracks competence against the matrix."""
    
    def __init__(self, db, evidence_store):
        self.db = db
        self.evidence_store = evidence_store
    
    def get_required_competencies(self, tier: TierLevel) -> Dict[str, str]:
        """Get required competency levels for a role tier."""
        required = {}
        for comp_code, tier_levels in COMPETENCE_MATRIX.items():
            level = tier_levels.get(tier)
            if level:
                required[comp_code] = level
        return required
    
    async def assess_competency(
        self,
        user_id: str,
        competency: CompetencyCode,
        assessment_method: str,
        score: int,
        assessor_id: str,
        evidence_ids: List[str] = None
    ) -> CompetencyAssessment:
        """Conduct a competency assessment."""
        user = await self.db.users.find_one({"id": user_id})
        user = User(**user)
        
        required_level = COMPETENCE_MATRIX.get(competency, {}).get(user.tier)
        if not required_level:
            raise ValueError(
                f"Competency {competency} not required for tier {user.tier}"
            )
        
        # Map score to level
        assessed_level = self._score_to_level(score)
        is_competent = self._level_meets_requirement(assessed_level, required_level)
        
        assessment = CompetencyAssessment(
            user_id=user_id,
            competency=competency,
            required_level=required_level,
            assessed_level=assessed_level,
            assessment_method=assessment_method,
            score=score,
            assessor_id=assessor_id,
            evidence_ids=evidence_ids or [],
            is_competent=is_competent,
            next_assessment_date=datetime.utcnow() + timedelta(days=180)
        )
        
        await self.db.assessments.insert_one(assessment.dict())
        
        # Update user's competence profile
        await self._update_competence_profile(user_id, competency, assessed_level)
        
        # Create evidence record
        await self._create_assessment_evidence(assessment)
        
        # If not competent, create corrective action
        if not is_competent:
            await self._create_corrective_action(assessment)
        
        return assessment
    
    def _score_to_level(self, score: int) -> CompetencyLevel:
        """Convert numeric score to competency level."""
        if score >= 90:
            return CompetencyLevel.EXPERT
        elif score >= 70:
            return CompetencyLevel.WORKING
        elif score >= 50:
            return CompetencyLevel.AWARE
        else:
            return CompetencyLevel.AWARE  # Below aware = still aware but needs work
    
    def _level_meets_requirement(
        self, assessed: CompetencyLevel, required: CompetencyLevel
    ) -> bool:
        """Check if assessed level meets or exceeds required level."""
        hierarchy = {
            CompetencyLevel.AWARE: 1,
            CompetencyLevel.WORKING: 2,
            CompetencyLevel.EXPERT: 3
        }
        return hierarchy.get(assessed, 0) >= hierarchy.get(required, 0)
    
    async def get_competence_gaps(self, user_id: str) -> List[Dict]:
        """Identify competence gaps for a user."""
        user = await self.db.users.find_one({"id": user_id})
        user = User(**user)
        
        required = self.get_required_competencies(user.tier)
        gaps = []
        
        for comp_code, required_level in required.items():
            # Get latest assessment
            assessment = await self.db.assessments.find_one(
                {"user_id": user_id, "competency": comp_code},
                sort=[("assessed_at", -1)]
            )
            
            if not assessment:
                gaps.append({
                    "competency": comp_code,
                    "required_level": required_level,
                    "current_level": None,
                    "gap": "not_assessed",
                    "priority": "high"
                })
            elif not assessment["is_competent"]:
                gaps.append({
                    "competency": comp_code,
                    "required_level": required_level,
                    "current_level": assessment["assessed_level"],
                    "gap": "below_required",
                    "priority": "high" if required_level == CompetencyLevel.EXPERT else "medium"
                })
        
        return gaps
    
    async def get_competence_profile(self, user_id: str) -> Dict:
        """Get full competence profile for a user."""
        user = await self.db.users.find_one({"id": user_id})
        user = User(**user)
        
        required = self.get_required_competencies(user.tier)
        profile = {}
        
        for comp_code, required_level in required.items():
            assessment = await self.db.assessments.find_one(
                {"user_id": user_id, "competency": comp_code},
                sort=[("assessed_at", -1)]
            )
            
            profile[comp_code] = {
                "required": required_level,
                "current": assessment["assessed_level"] if assessment else None,
                "is_competent": assessment["is_competent"] if assessment else False,
                "last_assessed": assessment["assessed_at"] if assessment else None,
                "evidence_count": len(assessment["evidence_ids"]) if assessment else 0
            }
        
        return profile
    
    async def _update_competence_profile(
        self, user_id: str, competency: CompetencyCode, level: CompetencyLevel
    ):
        """Update user's competence profile."""
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {f"competence_levels.{competency}": level}}
        )
    
    async def _create_assessment_evidence(self, assessment: CompetencyAssessment):
        """Create audit-ready evidence for assessment."""
        from models.lms import EvidenceRecord
        
        evidence = EvidenceRecord(
            user_id=assessment.user_id,
            clause=ClauseType.COMPETENCE,
            artifact_type="competence_assessment",
            content={
                "competency": assessment.competency,
                "assessment_method": assessment.assessment_method,
                "score": assessment.score,
                "assessed_level": assessment.assessed_level,
                "required_level": assessment.required_level,
                "is_competent": assessment.is_competent,
                "assessor_id": assessment.assessor_id,
                "evidence_ids": assessment.evidence_ids
            },
            captured_by=assessment.assessor_id
        )
        await self.evidence_store.store(evidence)
    
    async def _create_corrective_action(self, assessment: CompetencyAssessment):
        """Create corrective action for competence gap."""
        action = {
            "id": str(uuid4()),
            "user_id": assessment.user_id,
            "competency": assessment.competency,
            "gap_type": "competence_below_required",
            "required_level": assessment.required_level,
            "current_level": assessment.assessed_level,
            "actions": self._recommend_corrective_actions(assessment),
            "due_date": datetime.utcnow() + timedelta(days=60),
            "status": "open",
            "created_at": datetime.utcnow()
        }
        await self.db.corrective_actions.insert_one(action)
    
    def _recommend_corrective_actions(self, assessment: CompetencyAssessment) -> List[str]:
        """Recommend corrective actions based on gap."""
        actions = []
        
        if assessment.competency in MODULE_COMPETENCY_MAP:
            for module_code in MODULE_COMPETENCY_MAP[assessment.competency]:
                actions.append(f"Complete module {module_code}")
        
        actions.append(f"Schedule reassessment in 60 days")
        actions.append(f"Assign mentor with {assessment.required_level} level")
        
        return actions
```

### 3.2 Assessment Types

```python
# services/assessment_types.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Question(BaseModel):
    """Assessment question."""
    id: str
    type: str  # mcq, scenario, practical, essay
    text: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    competency: str
    difficulty: int = Field(ge=1, le=5)
    scenario_context: Optional[str] = None


class Assessment(BaseModel):
    """Complete assessment definition."""
    id: str
    module_code: str
    title: str
    description: str
    questions: List[Question]
    passing_score: int = 70
    time_limit_minutes: Optional[int] = None
    max_attempts: int = 3
    is_proctored: bool = False
    competency_weights: Dict[str, float] = {}  # Per-competency scoring weights


class AssessmentEngine:
    """Multi-type assessment engine."""
    
    def __init__(self, db):
        self.db = db
    
    async def create_quiz_assessment(
        self, module_code: str, questions: List[Question]
    ) -> Assessment:
        """Create a knowledge test (quiz)."""
        assessment = Assessment(
            id=str(uuid4()),
            module_code=module_code,
            title=f"Knowledge Check: {module_code}",
            description="Multiple choice knowledge verification",
            questions=[q for q in questions if q.type == "mcq"],
            passing_score=70,
            time_limit_minutes=30
        )
        await self.db.assessments.insert_one(assessment.dict())
        return assessment
    
    async def create_scenario_assessment(
        self, module_code: str, scenarios: List[Dict]
    ) -> Assessment:
        """Create a scenario-based assessment."""
        questions = []
        for i, scenario in enumerate(scenarios):
            questions.append(Question(
                id=f"scenario_{i}",
                type="scenario",
                text=scenario["description"],
                options=scenario["options"],
                correct_answer=scenario["correct"],
                competency=scenario["competency"],
                difficulty=scenario.get("difficulty", 3),
                scenario_context=scenario.get("context")
            ))
        
        assessment = Assessment(
            id=str(uuid4()),
            module_code=module_code,
            title=f"Scenario Assessment: {module_code}",
            description="Role-based scenario evaluation",
            questions=questions,
            passing_score=75,
            competency_weights={q.competency: 1.0 for q in questions}
        )
        await self.db.assessments.insert_one(assessment.dict())
        return assessment
    
    async def create_practical_assessment(
        self, module_code: str, tasks: List[Dict]
    ) -> Assessment:
        """Create a hands-on practical assessment."""
        questions = []
        for i, task in enumerate(tasks):
            questions.append(Question(
                id=f"practical_{i}",
                type="practical",
                text=task["instructions"],
                competency=task["competency"],
                difficulty=task.get("difficulty", 4)
            ))
        
        assessment = Assessment(
            id=str(uuid4()),
            module_code=module_code,
            title=f"Practical Assessment: {module_code}",
            description="Hands-on skills verification",
            questions=questions,
            passing_score=80,
            is_proctored=True
        )
        await self.db.assessments.insert_one(assessment.dict())
        return assessment
    
    async def grade_assessment(
        self, assessment_id: str, answers: Dict[str, str], user_id: str
    ) -> Dict[str, Any]:
        """Grade an assessment and return detailed results."""
        assessment = await self.db.assessments.find_one({"id": assessment_id})
        if not assessment:
            raise ValueError("Assessment not found")
        
        assessment = Assessment(**assessment)
        
        # Grade each question
        results = []
        competency_scores: Dict[str, List[int]] = {}
        
        for question in assessment.questions:
            user_answer = answers.get(question.id, "")
            is_correct = user_answer == question.correct_answer
            score = 100 if is_correct else 0
            
            results.append({
                "question_id": question.id,
                "is_correct": is_correct,
                "score": score,
                "competency": question.competency
            })
            
            if question.competency not in competency_scores:
                competency_scores[question.competency] = []
            competency_scores[question.competency].append(score)
        
        # Calculate overall score
        total_score = sum(r["score"] for r in results) / len(results) if results else 0
        
        # Calculate per-competency scores
        competency_results = {}
        for comp, scores in competency_scores.items():
            avg = sum(scores) / len(scores)
            competency_results[comp] = {
                "score": avg,
                "questions_answered": len(scores),
                "passed": avg >= assessment.passing_score
            }
        
        passed = total_score >= assessment.passing_score
        
        return {
            "assessment_id": assessment_id,
            "user_id": user_id,
            "total_score": total_score,
            "passed": passed,
            "passing_score": assessment.passing_score,
            "competency_results": competency_results,
            "question_results": results,
            "graded_at": datetime.utcnow().isoformat(),
            "attempt_number": await self._get_attempt_number(user_id, assessment_id)
        }
```

---

## 4. Personalized Learning Paths

### 4.1 Learning Path Engine

```python
# services/learning_path_engine.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import uuid4

from models.lms import (
    User, Module, ModuleEnrollment, CompetencyCode, CompetencyLevel,
    TierLevel, ModuleCode, EnrollmentStatus
)
from services.competency_engine import COMPETENCE_MATRIX, MODULE_COMPETENCY_MAP


class LearningPath:
    """Personalized learning path for a user."""
    
    def __init__(self, user: User, db):
        self.user = user
        self.db = db
        self.path_items: List[Dict] = []
        self.estimated_hours: float = 0.0
    
    async def generate(self) -> Dict:
        """Generate a personalized learning path."""
        # 1. Get required competencies for user's tier
        required_competencies = self._get_required_competencies()
        
        # 2. Assess current competence levels
        current_levels = await self._get_current_competence()
        
        # 3. Identify gaps
        gaps = self._identify_gaps(required_competencies, current_levels)
        
        # 4. Map gaps to modules
        modules_needed = self._map_gaps_to_modules(gaps)
        
        # 5. Add role-specific modules
        role_modules = await self._get_role_specific_modules()
        
        # 6. Sequence modules (prerequisites first)
        sequenced = self._sequence_modules(modules_needed + role_modules)
        
        # 7. Build path with metadata
        self.path_items = []
        for i, module in enumerate(sequenced):
            item = {
                "order": i + 1,
                "module_id": module.id,
                "module_code": module.code,
                "title": module.title,
                "format": module.format,
                "duration_minutes": module.duration_minutes,
                "competencies": module.competencies,
                "clause": module.clause,
                "priority": self._calculate_priority(module, gaps),
                "due_date": self._calculate_due_date(module, i),
                "prerequisites": module.prerequisites,
                "certification_mapping": module.certification_mapping
            }
            self.path_items.append(item)
            self.estimated_hours += module.duration_minutes / 60
        
        return {
            "user_id": self.user.id,
            "tier": self.user.tier,
            "role": self.user.role,
            "path_items": self.path_items,
            "total_modules": len(self.path_items),
            "estimated_hours": round(self.estimated_hours, 1),
            "competence_gaps": gaps,
            "generated_at": datetime.utcnow().isoformat(),
            "adaptive": True
        }
    
    def _get_required_competencies(self) -> Dict[str, str]:
        """Get required competencies for user's tier."""
        required = {}
        for comp_code, tier_levels in COMPETENCE_MATRIX.items():
            level = tier_levels.get(self.user.tier)
            if level:
                required[comp_code] = level
        return required
    
    async def _get_current_competence(self) -> Dict[str, str]:
        """Get user's current assessed competence levels."""
        cursor = self.db.assessments.find(
            {"user_id": self.user.id},
            sort=[("assessed_at", -1)]
        )
        
        latest = {}
        async for doc in cursor:
            comp = doc["competency"]
            if comp not in latest:
                latest[comp] = doc["assessed_level"]
        
        return latest
    
    def _identify_gaps(
        self, required: Dict[str, str], current: Dict[str, str]
    ) -> List[Dict]:
        """Identify competence gaps."""
        gaps = []
        hierarchy = {"aware": 1, "working": 2, "expert": 3}
        
        for comp, req_level in required.items():
            curr_level = current.get(comp)
            if not curr_level:
                gaps.append({
                    "competency": comp,
                    "required": req_level,
                    "current": None,
                    "gap_type": "not_assessed",
                    "severity": "high"
                })
            elif hierarchy.get(curr_level, 0) < hierarchy.get(req_level, 0):
                gaps.append({
                    "competency": comp,
                    "required": req_level,
                    "current": curr_level,
                    "gap_type": "below_required",
                    "severity": "high" if req_level == "expert" else "medium"
                })
        
        return gaps
    
    def _map_gaps_to_modules(self, gaps: List[Dict]) -> List[ModuleCode]:
        """Map competence gaps to required modules."""
        modules_needed = set()
        
        for gap in gaps:
            comp = gap["competency"]
            if comp in MODULE_COMPETENCY_MAP:
                for module_code in MODULE_COMPETENCY_MAP[comp]:
                    modules_needed.add(module_code)
        
        return list(modules_needed)
    
    async def _get_role_specific_modules(self) -> List[ModuleCode]:
        """Get role-specific modules beyond gap remediation."""
        role_modules = {
            TierLevel.ALL_STAFF: [ModuleCode.M01, ModuleCode.M02, ModuleCode.M14],
            TierLevel.AI_USER: [ModuleCode.M03, ModuleCode.M04, ModuleCode.M05],
            TierLevel.PRACTITIONER: [ModuleCode.M06, ModuleCode.M07, ModuleCode.M08, ModuleCode.M09],
            TierLevel.GOVERNANCE: [ModuleCode.M10, ModuleCode.M11],
            TierLevel.LEADERSHIP: [ModuleCode.M12],
        }
        
        return role_modules.get(self.user.tier, [])
    
    def _sequence_modules(self, module_codes: List[ModuleCode]) -> List[Module]:
        """Sequence modules respecting prerequisites."""
        # Topological sort based on prerequisites
        sequenced = []
        visited = set()
        
        # Define prerequisite graph
        prereqs = {
            ModuleCode.M01: [],
            ModuleCode.M02: [ModuleCode.M01],
            ModuleCode.M03: [ModuleCode.M01, ModuleCode.M02],
            ModuleCode.M04: [ModuleCode.M03],
            ModuleCode.M05: [ModuleCode.M02],
            ModuleCode.M06: [ModuleCode.M03, ModuleCode.M05],
            ModuleCode.M07: [ModuleCode.M06],
            ModuleCode.M08: [ModuleCode.M06, ModuleCode.M07],
            ModuleCode.M09: [ModuleCode.M06, ModuleCode.M08],
            ModuleCode.M10: [ModuleCode.M09],
            ModuleCode.M11: [ModuleCode.M10],
            ModuleCode.M12: [ModuleCode.M09],
            ModuleCode.M13: [ModuleCode.M02],
            ModuleCode.M14: [ModuleCode.M01],
        }
        
        def visit(code: ModuleCode):
            if code in visited:
                return
            visited.add(code)
            for prereq in prereqs.get(code, []):
                if prereq in module_codes:
                    visit(prereq)
            if code in module_codes:
                sequenced.append(code)
        
        for code in module_codes:
            visit(code)
        
        # Convert to Module objects (would fetch from DB in practice)
        return [Module(code=c, title=c.value, tier=0, competencies=[], 
                       clause="7.2", format="self-paced", duration_minutes=60) 
                for c in sequenced]
    
    def _calculate_priority(self, module: Module, gaps: List[Dict]) -> str:
        """Calculate module priority based on gaps."""
        gap_comps = {g["competency"] for g in gaps}
        module_comps = set(module.competencies)
        
        if gap_comps & module_comps:
            return "critical"
        elif module.code in [ModuleCode.M01, ModuleCode.M02]:
            return "high"
        else:
            return "normal"
    
    def _calculate_due_date(self, module: Module, order: int) -> str:
        """Calculate due date based on priority and order."""
        base_days = 30
        if module.code in [ModuleCode.M01, ModuleCode.M02]:
            base_days = 14  # Urgent for baseline
        elif order < 3:
            base_days = 21
        
        return (datetime.utcnow() + timedelta(days=base_days)).isoformat()


class AdaptiveLearningEngine:
    """Adapts learning paths based on performance and behavior."""
    
    def __init__(self, db, ml_model=None):
        self.db = db
        self.ml_model = ml_model
    
    async def adapt_path(self, user_id: str) -> Dict:
        """Adapt learning path based on user performance."""
        user = await self.db.users.find_one({"id": user_id})
        user = User(**user)
        
        # Get learning history
        history = await self._get_learning_history(user_id)
        
        # Analyze patterns
        patterns = self._analyze_patterns(history)
        
        # Adjust path
        adjustments = []
        
        # If user struggles with self-paced, recommend instructor-led
        if patterns["self_paced_completion_rate"] < 0.5:
            adjustments.append({
                "type": "format_change",
                "from": "self-paced",
                "to": "instructor-led",
                "reason": "Low self-paced completion rate"
            })
        
        # If user excels, accelerate
        if patterns["average_score"] > 90 and patterns["completion_rate"] > 0.9:
            adjustments.append({
                "type": "acceleration",
                "action": "reduce_remedial_modules",
                "reason": "High performance across modules"
            })
        
        # If user has knowledge gaps in specific areas
        weak_areas = patterns.get("weak_competencies", [])
        if weak_areas:
            adjustments.append({
                "type": "remediation",
                "competencies": weak_areas,
                "action": "add_reinforcement_modules",
                "reason": "Consistent low scores in specific competencies"
            })
        
        return {
            "user_id": user_id,
            "adjustments": adjustments,
            "patterns": patterns,
            "adapted_at": datetime.utcnow().isoformat()
        }
    
    async def _get_learning_history(self, user_id: str) -> List[Dict]:
        """Get user's learning history."""
        cursor = self.db.enrollments.find({"user_id": user_id})
        return [doc async for doc in cursor]
    
    def _analyze_patterns(self, history: List[Dict]) -> Dict:
        """Analyze learning patterns."""
        if not history:
            return {}
        
        completed = [h for h in history if h["status"] == "completed"]
        self_paced = [h for h in history if h.get("format") == "self-paced"]
        self_paced_completed = [h for h in self_paced if h["status"] == "completed"]
        
        scores = [h["score"] for h in completed if h.get("score") is not None]
        
        return {
            "total_modules": len(history),
            "completed_modules": len(completed),
            "completion_rate": len(completed) / len(history) if history else 0,
            "average_score": sum(scores) / len(scores) if scores else 0,
            "self_paced_completion_rate": (
                len(self_paced_completed) / len(self_paced) if self_paced else 0
            ),
            "weak_competencies": self._identify_weak_competencies(history),
            "learning_velocity": self._calculate_velocity(history)
        }
    
    def _identify_weak_competencies(self, history: List[Dict]) -> List[str]:
        """Identify competencies with consistently low scores."""
        comp_scores: Dict[str, List[int]] = {}
        
        for h in history:
            if h.get("score") is not None:
                for comp in h.get("competencies", []):
                    if comp not in comp_scores:
                        comp_scores[comp] = []
                    comp_scores[comp].append(h["score"])
        
        weak = []
        for comp, scores in comp_scores.items():
            avg = sum(scores) / len(scores)
            if avg < 70:
                weak.append(comp)
        
        return weak
    
    def _calculate_velocity(self, history: List[Dict]) -> float:
        """Calculate learning velocity (modules per week)."""
        if not history:
            return 0.0
        
        completed = [h for h in history if h.get("completed_at")]
        if len(completed) < 2:
            return 0.0
        
        dates = sorted([h["completed_at"] for h in completed])
        days = (dates[-1] - dates[0]).days
        if days == 0:
            return float(len(completed))
        
        return len(completed) / (days / 7)
```

---

## 5. Training Effectiveness Measurement (Kirkpatrick)

### 5.1 Four-Level Kirkpatrick Model

```python
# services/kirkpatrick_engine.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
from uuid import uuid4


class KirkpatrickLevel(int, Enum):
    """Kirkpatrick's four levels of evaluation."""
    REACTION = 1      # Satisfaction
    LEARNING = 2      # Knowledge/skill acquisition
    BEHAVIOR = 3      # On-the-job application
    RESULTS = 4       # Business impact


class KirkpatrickEvaluation:
    """Complete Kirkpatrick evaluation engine."""
    
    def __init__(self, db, analytics_store):
        self.db = db
        self.analytics = analytics_store
    
    # ── Level 1: Reaction ───────────────────────────────────────────────
    
    async def collect_reaction_survey(
        self, enrollment_id: str, user_id: str, responses: Dict
    ) -> Dict:
        """Collect post-training satisfaction survey (Level 1)."""
        survey = {
            "id": str(uuid4()),
            "level": KirkpatrickLevel.REACTION,
            "enrollment_id": enrollment_id,
            "user_id": user_id,
            "responses": {
                "content_quality": responses.get("content_quality"),  # 1-5
                "instructor_effectiveness": responses.get("instructor_effectiveness"),
                "material_relevance": responses.get("material_relevance"),
                "format_suitability": responses.get("format_suitability"),
                "overall_satisfaction": responses.get("overall_satisfaction"),
                "nps_score": responses.get("nps_score"),  # 0-10
                "open_feedback": responses.get("open_feedback"),
                "would_recommend": responses.get("would_recommend")
            },
            "submitted_at": datetime.utcnow()
        }
        
        await self.db.kirkpatrick_surveys.insert_one(survey)
        
        # Update enrollment with L1 rating
        await self.db.enrollments.update_one(
            {"id": enrollment_id},
            {"$set": {"effectiveness_rating": survey["responses"]["overall_satisfaction"]}}
        )
        
        return survey
    
    def calculate_l1_metrics(self, module_code: str) -> Dict:
        """Calculate Level 1 metrics for a module."""
        surveys = await self.db.kirkpatrick_surveys.find({
            "module_code": module_code
        }).to_list(None)
        
        if not surveys:
            return {"error": "No survey data available"}
        
        ratings = [s["responses"]["overall_satisfaction"] for s in surveys 
                   if s["responses"].get("overall_satisfaction")]
        nps_scores = [s["responses"]["nps_score"] for s in surveys 
                      if s["responses"].get("nps_score") is not None]
        
        return {
            "level": 1,
            "module_code": module_code,
            "response_count": len(surveys),
            "average_satisfaction": sum(ratings) / len(ratings) if ratings else 0,
            "nps": self._calculate_nps(nps_scores) if nps_scores else None,
            "response_rate": len(surveys) / self._get_enrollment_count(module_code),
            "benchmark_comparison": self._compare_to_benchmark(module_code, ratings)
        }
    
    # ── Level 2: Learning ───────────────────────────────────────────────
    
    async def evaluate_learning(
        self, user_id: str, module_code: str, 
        pre_score: Optional[int], post_score: int
    ) -> Dict:
        """Evaluate knowledge/skill acquisition (Level 2)."""
        learning_gain = post_score - (pre_score or 0)
        percent_gain = (learning_gain / (pre_score or 1)) * 100 if pre_score else 100
        
        evaluation = {
            "id": str(uuid4()),
            "level": KirkpatrickLevel.LEARNING,
            "user_id": user_id,
            "module_code": module_code,
            "pre_score": pre_score,
            "post_score": post_score,
            "learning_gain": learning_gain,
            "percent_gain": percent_gain,
            "passed": post_score >= 70,
            "evaluated_at": datetime.utcnow()
        }
        
        await self.db.kirkpatrick_evaluations.insert_one(evaluation)
        return evaluation
    
    def calculate_l2_metrics(self, module_code: str) -> Dict:
        """Calculate Level 2 metrics for a module."""
        evaluations = await self.db.kirkpatrick_evaluations.find({
            "level": KirkpatrickLevel.LEARNING,
            "module_code": module_code
        }).to_list(None)
        
        if not evaluations:
            return {"error": "No learning evaluation data"}
        
        gains = [e["learning_gain"] for e in evaluations]
        pass_rate = sum(1 for e in evaluations if e["passed"]) / len(evaluations)
        
        return {
            "level": 2,
            "module_code": module_code,
            "evaluation_count": len(evaluations),
            "average_learning_gain": sum(gains) / len(gains),
            "pass_rate": pass_rate,
            "knowledge_retention_rate": self._estimate_retention(module_code),
            "competency_improvement": self._calculate_competency_improvement(module_code)
        }
    
    # ── Level 3: Behavior ───────────────────────────────────────────────
    
    async def collect_behavior_observation(
        self, user_id: str, observer_id: str, 
        module_code: str, observations: Dict
    ) -> Dict:
        """Collect supervisor observation of behavior change (Level 3)."""
        observation = {
            "id": str(uuid4()),
            "level": KirkpatrickLevel.BEHAVIOR,
            "user_id": user_id,
            "observer_id": observer_id,
            "module_code": module_code,
            "observations": {
                "applies_knowledge": observations.get("applies_knowledge"),  # 1-5
                "uses_approved_tools": observations.get("uses_approved_tools"),
                "follows_escalation_paths": observations.get("follows_escalation_paths"),
                "validates_outputs": observations.get("validates_outputs"),
                "reports_issues": observations.get("reports_issues"),
                "behavior_change_notes": observations.get("notes"),
                "observed_incidents": observations.get("incidents", 0),
                "positive_observations": observations.get("positive", []),
                "areas_for_improvement": observations.get("improvements", [])
            },
            "observation_date": datetime.utcnow(),
            "days_since_training": self._days_since_training(user_id, module_code)
        }
        
        await self.db.kirkpatrick_behaviors.insert_one(observation)
        return observation
    
    def calculate_l3_metrics(self, module_code: str) -> Dict:
        """Calculate Level 3 behavior change metrics."""
        observations = await self.db.kirkpatrick_behaviors.find({
            "module_code": module_code
        }).to_list(None)
        
        if not observations:
            return {"error": "No behavior observation data"}
        
        behavior_scores = [o["observations"]["applies_knowledge"] for o in observations 
                          if o["observations"].get("applies_knowledge")]
        
        return {
            "level": 3,
            "module_code": module_code,
            "observation_count": len(observations),
            "average_behavior_score": sum(behavior_scores) / len(behavior_scores) if behavior_scores else 0,
            "behavior_change_rate": self._calculate_behavior_change_rate(observations),
            "incident_reduction": self._calculate_incident_reduction(module_code),
            "time_to_behavior_change": self._avg_time_to_behavior_change(observations)
        }
    
    # ── Level 4: Results ────────────────────────────────────────────────
    
    async def evaluate_business_impact(
        self, module_code: str, metrics: Dict
    ) -> Dict:
        """Evaluate business impact (Level 4)."""
        impact = {
            "id": str(uuid4()),
            "level": KirkpatrickLevel.RESULTS,
            "module_code": module_code,
            "metrics": {
                "incident_reduction_percent": metrics.get("incident_reduction"),
                "audit_finding_reduction": metrics.get("audit_finding_reduction"),
                "compliance_score_improvement": metrics.get("compliance_improvement"),
                "risk_score_improvement": metrics.get("risk_score_improvement"),
                "time_savings_hours": metrics.get("time_savings"),
                "cost_avoidance": metrics.get("cost_avoidance"),
                "productivity_gain": metrics.get("productivity_gain"),
                "employee_confidence_score": metrics.get("confidence_score")
            },
            "evaluation_period": {
                "start": metrics.get("period_start"),
                "end": metrics.get("period_end")
            },
            "roi_calculation": self._calculate_roi(module_code, metrics),
            "evaluated_at": datetime.utcnow()
        }
        
        await self.db.kirkpatrick_results.insert_one(impact)
        return impact
    
    def calculate_l4_metrics(self, module_code: str) -> Dict:
        """Calculate Level 4 business results metrics."""
        results = await self.db.kirkpatrick_results.find({
            "module_code": module_code
        }).to_list(None)
        
        if not results:
            return {"error": "No business impact data"}
        
        return {
            "level": 4,
            "module_code": module_code,
            "evaluation_count": len(results),
            "average_roi": sum(r["roi_calculation"]["roi_percent"] for r in results) / len(results),
            "total_cost_avoidance": sum(r["metrics"].get("cost_avoidance", 0) for r in results),
            "incident_reduction": self._aggregate_incident_reduction(results),
            "compliance_improvement": self._aggregate_compliance_improvement(results),
            "business_value_score": self._calculate_business_value(results)
        }
    
    # ── Comprehensive Report ─────────────────────────────────────────────
    
    async def generate_kirkpatrick_report(
        self, module_code: str, period: Optional[Dict] = None
    ) -> Dict:
        """Generate complete Kirkpatrick evaluation report."""
        return {
            "module_code": module_code,
            "report_period": period or {"start": "last_12_months"},
            "generated_at": datetime.utcnow().isoformat(),
            "level_1_reaction": self.calculate_l1_metrics(module_code),
            "level_2_learning": self.calculate_l2_metrics(module_code),
            "level_3_behavior": self.calculate_l3_metrics(module_code),
            "level_4_results": self.calculate_l4_metrics(module_code),
            "overall_effectiveness_score": self._calculate_overall_score(module_code),
            "recommendations": self._generate_recommendations(module_code)
        }
    
    def _calculate_nps(self, scores: List[int]) -> int:
        """Calculate Net Promoter Score."""
        promoters = sum(1 for s in scores if s >= 9)
        detractors = sum(1 for s in scores if s <= 6)
        return int(((promoters - detractors) / len(scores)) * 100)
    
    def _calculate_roi(self, module_code: str, metrics: Dict) -> Dict:
        """Calculate training ROI."""
        training_cost = self._get_training_cost(module_code)
        benefits = (
            metrics.get("cost_avoidance", 0) +
            metrics.get("time_savings", 0) * 50 +  # $50/hour loaded cost
            metrics.get("productivity_gain", 0)
        )
        
        roi_percent = ((benefits - training_cost) / training_cost * 100) if training_cost > 0 else 0
        
        return {
            "training_cost": training_cost,
            "total_benefits": benefits,
            "net_benefit": benefits - training_cost,
            "roi_percent": roi_percent,
            "payback_period_days": self._estimate_payback(training_cost, benefits)
        }
    
    def _calculate_overall_score(self, module_code: str) -> float:
        """Calculate overall effectiveness score across all levels."""
        # Weighted average of all four levels
        weights = {1: 0.15, 2: 0.25, 3: 0.30, 4: 0.30}
        
        scores = {}
        for level in KirkpatrickLevel:
            metrics = getattr(self, f"calculate_l{level.value}_metrics")(module_code)
            if "error" not in metrics:
                # Normalize to 0-100 scale
                scores[level.value] = self._normalize_score(level, metrics)
        
        overall = sum(scores.get(l, 0) * w for l, w in weights.items())
        return round(overall, 2)
    
    def _generate_recommendations(self, module_code: str) -> List[str]:
        """Generate improvement recommendations based on evaluation."""
        recommendations = []
        
        l1 = self.calculate_l1_metrics(module_code)
        l2 = self.calculate_l2_metrics(module_code)
        l3 = self.calculate_l3_metrics(module_code)
        l4 = self.calculate_l4_metrics(module_code)
        
        if "error" not in l1 and l1["average_satisfaction"] < 3.5:
            recommendations.append("Improve content quality and delivery format")
        
        if "error" not in l2 and l2["pass_rate"] < 0.8:
            recommendations.append("Revise assessment difficulty or add preparatory content")
        
        if "error" not in l3 and l3["behavior_change_rate"] < 0.6:
            recommendations.append("Add post-training coaching and reinforcement activities")
        
        if "error" not in l4 and l4["average_roi"] < 100:
            recommendations.append("Realign training objectives with business outcomes")
        
        return recommendations
```

---

## 6. Certification Preparation

### 6.1 Certification Pathway Engine

```python
# services/certification_engine.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

from models.lms import User, TierLevel, CertificationRecord, ModuleCode


class CertificationType(str, Enum):
    """External certifications mapped to tiers."""
    # Tier 0
    AI_AWARENESS_BADGE = "GRC_Claw_AI_Awareness_Badge"
    
    # Tier 1
    CEET = "CertNexus_CEET"
    RESPONSIBLE_AI_USER = "GRC_Claw_Responsible_AI_User_Badge"
    
    # Tier 2
    AIGP = "IAPP_AIGP"
    GAICC_FOUNDATION = "GAICC_Foundation"
    AI_PRACTITIONER = "GRC_Claw_AI_Practitioner_Badge"
    
    # Tier 3
    GAICC_LEAD_IMPLEMENTER = "GAICC_Lead_Implementer"
    GAICC_INTERNAL_AUDITOR = "GAICC_Internal_Auditor"
    AIMS_PROFESSIONAL = "GRC_Claw_AIMS_Professional_Badge"
    
    # Tier 4
    AI_LEADERSHIP = "GRC_Claw_AI_Leadership_Badge"


# Certification requirements mapping
CERTIFICATION_REQUIREMENTS: Dict[str, Dict] = {
    CertificationType.AI_AWARENESS_BADGE: {
        "tier": TierLevel.ALL_STAFF,
        "modules": [ModuleCode.M01, ModuleCode.M02],
        "min_score": 70,
        "validity_years": 1,
        "cpe_credits": 0,
        "prerequisites": []
    },
    CertificationType.CEET: {
        "tier": TierLevel.AI_USER,
        "modules": [ModuleCode.M03, ModuleCode.M04, ModuleCode.M05],
        "min_score": 70,
        "validity_years": 3,
        "cpe_credits": 90,
        "prerequisites": [],
        "external_exam": "CEET-110",
        "exam_cost": 395
    },
    CertificationType.AIGP: {
        "tier": TierLevel.PRACTITIONER,
        "modules": [ModuleCode.M06, ModuleCode.M07, ModuleCode.M08, ModuleCode.M09],
        "min_score": 75,
        "validity_years": 2,
        "cpe_credits": 40,
        "prerequisites": [],
        "external_exam": "AIGP",
        "exam_cost": 799
    },
    CertificationType.GAICC_FOUNDATION: {
        "tier": TierLevel.PRACTITIONER,
        "modules": [ModuleCode.M06, ModuleCode.M09],
        "min_score": 70,
        "validity_years": 3,
        "cpe_credits": 20,
        "prerequisites": [],
        "external_exam": "GAICC_Foundation_40_MCQ",
        "exam_cost": 795
    },
    CertificationType.GAICC_LEAD_IMPLEMENTER: {
        "tier": TierLevel.GOVERNANCE,
        "modules": [ModuleCode.M10],
        "min_score": 80,
        "validity_years": 3,
        "cpe_credits": 40,
        "prerequisites": [CertificationType.GAICC_FOUNDATION],
        "external_exam": "GAICC_Lead_Implementer",
        "exam_cost": 2495,
        "training_hours": 32
    },
    CertificationType.GAICC_INTERNAL_AUDITOR: {
        "tier": TierLevel.GOVERNANCE,
        "modules": [ModuleCode.M11],
        "min_score": 80,
        "validity_years": 3,
        "cpe_credits": 40,
        "prerequisites": [CertificationType.GAICC_LEAD_IMPLEMENTER],
        "external_exam": "GAICC_Internal_Auditor",
        "exam_cost": 2495,
        "training_hours": 32
    },
    CertificationType.AIMS_PROFESSIONAL: {
        "tier": TierLevel.GOVERNANCE,
        "modules": [ModuleCode.M10, ModuleCode.M11],
        "min_score": 85,
        "validity_years": 3,
        "cpe_credits": 80,
        "prerequisites": [CertificationType.GAICC_LEAD_IMPLEMENTER, 
                          CertificationType.GAICC_INTERNAL_AUDITOR],
        "internal_badge": True
    },
    CertificationType.AI_LEADERSHIP: {
        "tier": TierLevel.LEADERSHIP,
        "modules": [ModuleCode.M12],
        "min_score": 75,
        "validity_years": 2,
        "cpe_credits": 16,
        "prerequisites": [CertificationType.GAICC_FOUNDATION],
        "internal_badge": True
    }
}


class CertificationPreparationEngine:
    """Manages certification preparation and tracking."""
    
    def __init__(self, db, lms_service):
        self.db = db
        self.lms = lms_service
    
    async def get_certification_path(self, user_id: str) -> Dict:
        """Get recommended certification path for a user."""
        user = await self.db.users.find_one({"id": user_id})
        user = User(**user)
        
        # Get certifications for user's tier
        tier_certs = self._get_tier_certifications(user.tier)
        
        # Check current status
        path = []
        for cert_type in tier_certs:
            status = await self._get_cert_status(user_id, cert_type)
            requirements = CERTIFICATION_REQUIREMENTS[cert_type]
            
            # Check prerequisites
            prereqs_met = all(
                await self._is_cert_achieved(user_id, p)
                for p in requirements.get("prerequisites", [])
            )
            
            # Check module completion
            modules_completed = all(
                await self._is_module_completed(user_id, m)
                for m in requirements["modules"]
            )
            
            path.append({
                "certification": cert_type,
                "status": status,
                "requirements": requirements,
                "prerequisites_met": prereqs_met,
                "modules_completed": modules_completed,
                "ready_to_sit": prereqs_met and modules_completed and status == "not_started",
                "estimated_preparation_weeks": self._estimate_preparation(cert_type, user),
                "cost": requirements.get("exam_cost", 0),
                "training_hours": requirements.get("training_hours", 0)
            })
        
        return {
            "user_id": user_id,
            "tier": user.tier,
            "certification_path": path,
            "recommended_next": self._recommend_next_cert(path),
            "total_investment": sum(p["cost"] for p in path if p["ready_to_sit"])
        }
    
    async def create_study_plan(
        self, user_id: str, certification: CertificationType
    ) -> Dict:
        """Create a personalized study plan for certification."""
        requirements = CERTIFICATION_REQUIREMENTS[certification]
        
        # Get user's current knowledge gaps
        gaps = await self._identify_knowledge_gaps(user_id, requirements["modules"])
        
        # Build study plan
        study_plan = {
            "certification": certification,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "target_exam_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
            "phases": []
        }
        
        # Phase 1: Foundation (weeks 1-4)
        phase1 = {
            "phase": 1,
            "name": "Foundation Building",
            "duration_weeks": 4,
            "activities": []
        }
        
        for module_code in requirements["modules"]:
            phase1["activities"].append({
                "type": "module_completion",
                "module": module_code,
                "priority": "high",
                "estimated_hours": self._get_module_duration(module_code) / 60
            })
        
        study_plan["phases"].append(phase1)
        
        # Phase 2: Practice (weeks 5-8)
        phase2 = {
            "phase": 2,
            "name": "Practice & Assessment",
            "duration_weeks": 4,
            "activities": [
                {"type": "practice_exams", "count": 3, "target_score": 80},
                {"type": "weak_area_review", "competencies": gaps},
                {"type": "study_group", "frequency": "weekly"}
            ]
        }
        study_plan["phases"].append(phase2)
        
        # Phase 3: Final Prep (weeks 9-12)
        phase3 = {
            "phase": 3,
            "name": "Final Preparation",
            "duration_weeks": 4,
            "activities": [
                {"type": "mock_exam", "count": 2, "target_score": 85},
                {"type": "exam_strategy", "focus": "time_management"},
                {"type": "rest", "days_before_exam": 2}
            ]
        }
        study_plan["phases"].append(phase3)
        
        await self.db.study_plans.insert_one(study_plan)
        return study_plan
    
    async def track_certification_progress(
        self, user_id: str, certification: CertificationType
    ) -> Dict:
        """Track progress toward certification."""
        requirements = CERTIFICATION_REQUIREMENTS[certification]
        
        # Module progress
        module_progress = []
        for module_code in requirements["modules"]:
            enrollment = await self.db.enrollments.find_one({
                "user_id": user_id,
                "module_code": module_code
            })
            module_progress.append({
                "module": module_code,
                "status": enrollment["status"] if enrollment else "not_enrolled",
                "score": enrollment.get("score") if enrollment else None,
                "completed": enrollment["status"] == "completed" if enrollment else False
            })
        
        # Prerequisite progress
        prereq_progress = []
        for prereq in requirements.get("prerequisites", []):
            achieved = await self._is_cert_achieved(user_id, prereq)
            prereq_progress.append({
                "certification": prereq,
                "achieved": achieved
            })
        
        # Overall readiness
        all_modules_done = all(m["completed"] for m in module_progress)
        all_prereqs_met = all(p["achieved"] for p in prereq_progress)
        
        return {
            "certification": certification,
            "user_id": user_id,
            "module_progress": module_progress,
            "prerequisite_progress": prereq_progress,
            "overall_readiness": "ready" if (all_modules_done and all_prereqs_met) else "in_progress",
            "readiness_percent": self._calculate_readiness(module_progress, prereq_progress),
            "estimated_exam_ready_date": self._estimate_exam_date(module_progress),
            "next_actions": self._get_next_actions(module_progress, prereq_progress)
        }
    
    async def record_certification_result(
        self, user_id: str, certification: CertificationType,
        passed: bool, score: Optional[int] = None,
        credential_id: Optional[str] = None
    ) -> CertificationRecord:
        """Record certification exam result."""
        requirements = CERTIFICATION_REQUIREMENTS[certification]
        
        record = CertificationRecord(
            user_id=user_id,
            certification_type=certification,
            status="achieved" if passed else "failed",
            issue_date=datetime.utcnow() if passed else None,
            expiry_date=(datetime.utcnow() + timedelta(days=365 * requirements["validity_years"])) if passed else None,
            credential_id=credential_id,
            cpe_credits=requirements.get("cpe_credits", 0) if passed else 0,
            internal_equivalent=requirements.get("internal_badge")
        )
        
        await self.db.certifications.insert_one(record.dict())
        
        # If failed, create remediation plan
        if not passed:
            await self._create_cert_remediation(user_id, certification, score)
        
        return record
    
    def _get_tier_certifications(self, tier: TierLevel) -> List[CertificationType]:
        """Get certifications available for a tier."""
        tier_map = {
            TierLevel.ALL_STAFF: [CertificationType.AI_AWARENESS_BADGE],
            TierLevel.AI_USER: [CertificationType.CEET, CertificationType.RESPONSIBLE_AI_USER],
            TierLevel.PRACTITIONER: [CertificationType.AIGP, CertificationType.GAICC_FOUNDATION, 
                                      CertificationType.AI_PRACTITIONER],
            TierLevel.GOVERNANCE: [CertificationType.GAICC_LEAD_IMPLEMENTER, 
                                   CertificationType.GAICC_INTERNAL_AUDITOR,
                                   CertificationType.AIMS_PROFESSIONAL],
            TierLevel.LEADERSHIP: [CertificationType.AI_LEADERSHIP]
        }
        return tier_map.get(tier, [])
    
    def _estimate_preparation(
        self, certification: CertificationType, user: User
    ) -> int:
        """Estimate preparation time in weeks."""
        base_weeks = {
            CertificationType.AI_AWARENESS_BADGE: 1,
            CertificationType.CEET: 4,
            CertificationType.AIGP: 8,
            CertificationType.GAICC_FOUNDATION: 6,
            CertificationType.GAICC_LEAD_IMPLEMENTER: 12,
            CertificationType.GAICC_INTERNAL_AUDITOR: 12,
            CertificationType.AIMS_PROFESSIONAL: 4,
            CertificationType.AI_LEADERSHIP: 4
        }
        
        weeks = base_weeks.get(certification, 8)
        
        # Adjust for user's tier (higher tier = more experience = less prep)
        tier_adjustment = {0: 2, 1: 1, 2: 0, 3: -1, 4: -1}
        weeks += tier_adjustment.get(user.tier, 0)
        
        return max(weeks, 2)
```

---

## 7. Continuous Learning Recommendations

### 7.1 Recommendation Engine

```python
# services/recommendation_engine.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import Counter
import math

from models.lms import (
    User, Module, ModuleCode, CompetencyCode, CompetencyLevel,
    TierLevel, EnrollmentStatus
)


class ContinuousLearningRecommender:
    """AI-powered continuous learning recommendation engine."""
    
    def __init__(self, db, knowledge_graph=None):
        self.db = db
        self.knowledge_graph = knowledge_graph
    
    async def get_recommendations(
        self, user_id: str, context: Optional[Dict] = None, limit: int = 5
    ) -> List[Dict]:
        """Get personalized learning recommendations."""
        user = await self.db.users.find_one({"id": user_id})
        user = User(**user)
        
        # Gather signals
        signals = await self._gather_signals(user, context)
        
        # Score potential recommendations
        candidates = await self._get_candidate_modules(user)
        scored = []
        
        for module in candidates:
            score = self._score_recommendation(module, signals, user)
            scored.append((module, score))
        
        # Sort by score and return top N
        scored.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for module, score in scored[:limit]:
            recommendations.append({
                "module_id": module.id,
                "module_code": module.code,
                "title": module.title,
                "format": module.format,
                "duration_minutes": module.duration_minutes,
                "relevance_score": round(score, 2),
                "reasoning": self._generate_reasoning(module, signals),
                "priority": self._score_to_priority(score),
                "competencies_addressed": module.competencies,
                "estimated_completion": self._estimate_completion(user, module)
            })
        
        return recommendations
    
    async def _gather_signals(
        self, user: User, context: Optional[Dict]
    ) -> Dict:
        """Gather all signals for recommendation."""
        signals = {
            "competence_gaps": await self._get_competence_gaps(user),
            "role_requirements": self._get_role_requirements(user),
            "learning_history": await self._get_learning_history(user),
            "peer_activity": await self._get_peer_activity(user),
            "organizational_trends": await self._get_org_trends(),
            "trigger_events": await self._get_trigger_events(user),
            "context": context or {},
            "time_since_last_training": self._days_since_last_training(user)
        }
        return signals
    
    async def _get_competence_gaps(self, user: User) -> List[Dict]:
        """Identify competence gaps."""
        from services.competency_engine import COMPETENCE_MATRIX
        
        gaps = []
        for comp_code, tier_levels in COMPETENCE_MATRIX.items():
            required = tier_levels.get(user.tier)
            if not required:
                continue
            
            assessment = await self.db.assessments.find_one(
                {"user_id": user.id, "competency": comp_code},
                sort=[("assessed_at", -1)]
            )
            
            if not assessment or not assessment.get("is_competent"):
                gaps.append({
                    "competency": comp_code,
                    "required": required,
                    "current": assessment["assessed_level"] if assessment else None
                })
        
        return gaps
    
    async def _get_learning_history(self, user: User) -> Dict:
        """Analyze user's learning history."""
        enrollments = await self.db.enrollments.find(
            {"user_id": user.id}
        ).to_list(None)
        
        if not enrollments:
            return {"total": 0, "completed": 0, "average_score": 0}
        
        completed = [e for e in enrollments if e["status"] == "completed"]
        scores = [e["score"] for e in completed if e.get("score") is not None]
        
        # Identify preferred formats
        formats = Counter(e.get("format") for e in completed)
        
        # Identify strong/weak competencies
        comp_scores = {}
        for e in completed:
            for comp in e.get("competencies", []):
                if e.get("score"):
                    comp_scores.setdefault(comp, []).append(e["score"])
        
        weak_comps = [c for c, scores in comp_scores.items() 
                      if sum(scores)/len(scores) < 70]
        strong_comps = [c for c, scores in comp_scores.items() 
                        if sum(scores)/len(scores) >= 85]
        
        return {
            "total": len(enrollments),
            "completed": len(completed),
            "average_score": sum(scores)/len(scores) if scores else 0,
            "preferred_formats": formats.most_common(2),
            "weak_competencies": weak_comps,
            "strong_competencies": strong_comps,
            "completion_rate": len(completed) / len(enrollments)
        }
    
    async def _get_peer_activity(self, user: User) -> Dict:
        """Get peer learning activity for social recommendations."""
        # Find peers in same tier/department
        peers = await self.db.users.find({
            "tier": user.tier,
            "department": user.department,
            "id": {"$ne": user.id}
        }).to_list(None)
        
        peer_ids = [p["id"] for p in peers]
        
        # Get peer completions in last 30 days
        recent = await self.db.enrollments.find({
            "user_id": {"$in": peer_ids},
            "status": "completed",
            "completed_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
        }).to_list(None)
        
        # Most popular modules among peers
        module_counts = Counter(e["module_code"] for e in recent)
        
        return {
            "peer_count": len(peers),
            "popular_modules": module_counts.most_common(3),
            "peer_completion_rate": len(recent) / len(peer_ids) if peer_ids else 0
        }
    
    async def _get_org_trends(self) -> Dict:
        """Get organizational learning trends."""
        # Most completed modules org-wide
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        trending = await self.db.enrollments.aggregate([
            {"$match": {"status": "completed", "completed_at": {"$gte": thirty_days_ago}}},
            {"$group": {"_id": "$module_code", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]).to_list(None)
        
        return {
            "trending_modules": [{"module": t["_id"], "completions": t["count"]} for t in trending],
            "period": "last_30_days"
        }
    
    async def _get_trigger_events(self, user: User) -> List[Dict]:
        """Get recent trigger events relevant to user."""
        # Check for recent policy updates, incidents, etc.
        triggers = []
        
        # Recent incidents
        incidents = await self.db.incidents.find({
            "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)},
            "status": {"$in": ["open", "resolved"]}
        }).to_list(None)
        
        for inc in incidents:
            triggers.append({
                "type": "incident",
                "severity": inc.get("severity"),
                "module": ModuleCode.M13,
                "urgency": "high" if inc.get("severity") in ["critical", "high"] else "medium"
            })
        
        # Policy updates
        policy_updates = await self.db.policies.find({
            "updated_at": {"$gte": datetime.utcnow() - timedelta(days=30)},
            "status": "active"
        }).to_list(None)
        
        for policy in policy_updates:
            triggers.append({
                "type": "policy_update",
                "module": ModuleCode.M14,
                "urgency": "medium"
            })
        
        return triggers
    
    def _score_recommendation(
        self, module: Module, signals: Dict, user: User
    ) -> float:
        """Score a module recommendation (0-100)."""
        score = 0.0
        
        # Competence gap alignment (0-30 points)
        gap_comps = {g["competency"] for g in signals["competence_gaps"]}
        module_comps = set(module.competencies)
        if gap_comps & module_comps:
            score += 30 * len(gap_comps & module_comps) / len(gap_comps)
        
        # Role requirement alignment (0-25 points)
        required_comps = signals["role_requirements"]
        if any(comp in required_comps for comp in module.competencies):
            score += 25
        
        # Trigger event urgency (0-20 points)
        for trigger in signals["trigger_events"]:
            if trigger["module"] == module.code:
                score += 20 if trigger["urgency"] == "high" else 10
        
        # Peer activity (0-10 points)
        peer_modules = {m["module"] for m in signals["peer_activity"]["popular_modules"]}
        if module.code in peer_modules:
            score += 10
        
        # Organizational trend (0-10 points)
        trending = {t["module"] for t in signals["organizational_trends"]["trending_modules"]}
        if module.code in trending:
            score += 10
        
        # Time since last training (0-5 points)
        days_since = signals["time_since_last_training"]
        if days_since > 90:
            score += 5
        elif days_since > 60:
            score += 3
        
        return min(score, 100)
    
    def _generate_reasoning(self, module: Module, signals: Dict) -> str:
        """Generate human-readable reasoning for recommendation."""
        reasons = []
        
        gap_comps = {g["competency"] for g in signals["competence_gaps"]}
        if gap_comps & set(module.competencies):
            reasons.append("addresses your competence gaps")
        
        for trigger in signals["trigger_events"]:
            if trigger["module"] == module.code:
                reasons.append(f"triggered by recent {trigger['type']}")
        
        peer_modules = {m["module"] for m in signals["peer_activity"]["popular_modules"]}
        if module.code in peer_modules:
            reasons.append("popular among your peers")
        
        if not reasons:
            reasons.append("recommended for your role development")
        
        return "This module " + ", ".join(reasons)
    
    def _score_to_priority(self, score: float) -> str:
        """Convert score to priority level."""
        if score >= 70:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"
    
    def _estimate_completion(self, user: User, module: Module) -> str:
        """Estimate completion date based on user's learning velocity."""
        history = signals.get("learning_history", {})
        velocity = history.get("modules_per_week", 0.5)
        
        weeks = max(1, module.duration_minutes / 60 / velocity)
        return (datetime.utcnow() + timedelta(weeks=weeks)).isoformat()


class SpacedRepetitionEngine:
    """Spaced repetition for knowledge retention."""
    
    def __init__(self, db):
        self.db = db
    
    async def schedule_review(self, user_id: str, module_code: str) -> Dict:
        """Schedule a review session using spaced repetition."""
        # Get previous review history
        reviews = await self.db.review_schedule.find({
            "user_id": user_id,
            "module_code": module_code
        }).sort("scheduled_date", -1).to_list(None)
        
        # Calculate next review date using SM-2 algorithm
        if not reviews:
            interval = 1  # 1 day
            repetitions = 0
            ease_factor = 2.5
        else:
            last = reviews[0]
            interval = last["interval_days"]
            repetitions = last["repetitions"]
            ease_factor = last["ease_factor"]
            
            # Adjust based on performance
            if last.get("performance") == "easy":
                interval = int(interval * ease_factor * 1.3)
                repetitions += 1
            elif last.get("performance") == "good":
                interval = int(interval * ease_factor)
                repetitions += 1
            elif last.get("performance") == "hard":
                interval = max(1, int(interval * 0.8))
                ease_factor = max(1.3, ease_factor - 0.2)
            else:  # again
                interval = 1
                repetitions = 0
                ease_factor = max(1.3, ease_factor - 0.2)
        
        next_date = datetime.utcnow() + timedelta(days=interval)
        
        schedule = {
            "user_id": user_id,
            "module_code": module_code,
            "scheduled_date": next_date,
            "interval_days": interval,
            "repetitions": repetitions,
            "ease_factor": ease_factor,
            "status": "scheduled"
        }
        
        await self.db.review_schedule.insert_one(schedule)
        return schedule
    
    async def get_due_reviews(self, user_id: str) -> List[Dict]:
        """Get all due review sessions for a user."""
        now = datetime.utcnow()
        due = await self.db.review_schedule.find({
            "user_id": user_id,
            "scheduled_date": {"$lte": now},
            "status": "scheduled"
        }).to_list(None)
        
        return due
```

---

## 8. Learning Analytics

### 8.1 Analytics Engine

```python
# services/analytics_engine.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import defaultdict

from models.lms import TierLevel, ModuleCode, ClauseType, EnrollmentStatus


class LearningAnalytics:
    """Comprehensive learning analytics engine."""
    
    def __init__(self, db):
        self.db = db
    
    # ── Dashboard Metrics ───────────────────────────────────────────────
    
    async def get_executive_dashboard(self) -> Dict:
        """Executive-level training dashboard."""
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        # Overall completion rates
        total_enrollments = await self.db.enrollments.count_documents({})
        completed = await self.db.enrollments.count_documents({"status": "completed"})
        
        # Competence coverage
        total_users = await self.db.users.count_documents({})
        competent_users = await self._count_competent_users()
        
        # Certification status
        active_certs = await self.db.certifications.count_documents({
            "status": "achieved",
            "expiry_date": {"$gt": now}
        })
        
        # Clause compliance
        clause_72_coverage = await self._get_clause_coverage(ClauseType.COMPETENCE)
        clause_73_coverage = await self._get_clause_coverage(ClauseType.AWARENESS)
        
        # Training hours
        total_hours = await self._get_total_training_hours(thirty_days_ago)
        
        return {
            "report_date": now.isoformat(),
            "summary": {
                "total_learners": total_users,
                "active_learners": await self._count_active_learners(thirty_days_ago),
                "overall_completion_rate": completed / total_enrollments if total_enrollments else 0,
                "competence_coverage": competent_users / total_users if total_users else 0,
                "active_certifications": active_certs,
                "training_hours_30d": total_hours
            },
            "clause_compliance": {
                "7.2_competence": clause_72_coverage,
                "7.3_awareness": clause_73_coverage
            },
            "tier_breakdown": await self._get_tier_breakdown(),
            "trending": await self._get_trending_metrics(),
            "risk_indicators": await self._get_risk_indicators()
        }
    
    async def get_manager_dashboard(self, manager_id: str) -> Dict:
        """Manager-level team dashboard."""
        # Get team members
        team = await self.db.users.find({"manager_id": manager_id}).to_list(None)
        team_ids = [t["id"] for t in team]
        
        # Team completion rates
        team_enrollments = await self.db.enrollments.find({
            "user_id": {"$in": team_ids}
        }).to_list(None)
        
        # Competence gaps
        gaps = await self.db.assessments.find({
            "user_id": {"$in": team_ids},
            "is_competent": False
        }).to_list(None)
        
        # Upcoming deadlines
        upcoming = await self.db.enrollments.find({
            "user_id": {"$in": team_ids},
            "due_date": {"$lte": datetime.utcnow() + timedelta(days=7)},
            "status": {"$ne": "completed"}
        }).to_list(None)
        
        return {
            "manager_id": manager_id,
            "team_size": len(team),
            "team_members": [
                {
                    "id": t["id"],
                    "name": t["name"],
                    "role": t["role"],
                    "tier": t["tier"],
                    "completion_rate": await self._get_user_completion_rate(t["id"]),
                    "competence_gaps": len([g for g in gaps if g["user_id"] == t["id"]]),
                    "upcoming_deadlines": len([u for u in upcoming if u["user_id"] == t["id"]])
                }
                for t in team
            ],
            "team_completion_rate": self._calculate_team_completion(team_enrollments),
            "critical_gaps": len([g for g in gaps if g["required_level"] == "expert"]),
            "overdue_count": len([u for u in upcoming if u["due_date"] < datetime.utcnow()]),
            "recommendations": await self._get_team_recommendations(team_ids)
        }
    
    # ── Detailed Analytics ──────────────────────────────────────────────
    
    async def get_module_analytics(self, module_code: str) -> Dict:
        """Detailed analytics for a specific module."""
        # Enrollment stats
        enrollments = await self.db.enrollments.find({
            "module_code": module_code
        }).to_list(None)
        
        if not enrollments:
            return {"error": "No data for this module"}
        
        completed = [e for e in enrollments if e["status"] == "completed"]
        scores = [e["score"] for e in completed if e.get("score") is not None]
        
        # Time to completion
        completion_times = []
        for e in completed:
            if e.get("started_at") and e.get("completed_at"):
                delta = e["completed_at"] - e["started_at"]
                completion_times.append(delta.days)
        
        # Format effectiveness
        format_stats = defaultdict(lambda: {"count": 0, "avg_score": 0, "completion_rate": 0})
        for e in enrollments:
            fmt = e.get("format", "unknown")
            format_stats[fmt]["count"] += 1
            if e["status"] == "completed":
                format_stats[fmt]["completion_rate"] += 1
                if e.get("score"):
                    format_stats[fmt]["avg_score"] += e["score"]
        
        return {
            "module_code": module_code,
            "enrollment_count": len(enrollments),
            "completion_rate": len(completed) / len(enrollments),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "score_distribution": self._calculate_score_distribution(scores),
            "average_completion_days": sum(completion_times) / len(completion_times) if completion_times else 0,
            "format_effectiveness": dict(format_stats),
            "learner_satisfaction": await self._get_module_satisfaction(module_code),
            "knowledge_retention": await self._get_retention_rate(module_code),
            "improvement_trend": await self._get_improvement_trend(module_code)
        }
    
    async def get_competence_analytics(self) -> Dict:
        """Organization-wide competence analytics."""
        # Competence coverage by tier
        tier_coverage = {}
        for tier in TierLevel:
            users_in_tier = await self.db.users.count_documents({"tier": tier})
            if users_in_tier == 0:
                continue
            
            competent = await self._count_competent_in_tier(tier)
            tier_coverage[tier.name] = {
                "total_users": users_in_tier,
                "competent_users": competent,
                "coverage_rate": competent / users_in_tier
            }
        
        # Competency heatmap
        competency_heatmap = {}
        for comp in CompetencyCode:
            assessments = await self.db.assessments.find({
                "competency": comp
            }).to_list(None)
            
            if assessments:
                competent = sum(1 for a in assessments if a["is_competent"])
                competency_heatmap[comp] = {
                    "assessed": len(assessments),
                    "competent": competent,
                    "rate": competent / len(assessments)
                }
        
        # Gap analysis
        gaps = await self.db.assessments.find({"is_competent": False}).to_list(None)
        gap_by_competency = defaultdict(int)
        for g in gaps:
            gap_by_competency[g["competency"]] += 1
        
        return {
            "tier_coverage": tier_coverage,
            "competency_heatmap": competency_heatmap,
            "gap_analysis": dict(gap_by_competency),
            "critical_gaps": len([g for g in gaps if g["required_level"] == "expert"]),
            "trend": await self._get_competence_trend()
        }
    
    async def get_certification_analytics(self) -> Dict:
        """Certification program analytics."""
        certs = await self.db.certifications.find().to_list(None)
        
        by_type = defaultdict(lambda: {"achieved": 0, "expired": 0, "in_progress": 0})
        for c in certs:
            by_type[c["certification_type"]][c["status"]] += 1
        
        # Pass rates
        exam_results = await self.db.exam_results.find().to_list(None)
        pass_rates = defaultdict(lambda: {"attempts": 0, "passed": 0})
        for r in exam_results:
            pass_rates[r["certification_type"]]["attempts"] += 1
            if r["passed"]:
                pass_rates[r["certification_type"]]["passed"] += 1
        
        # Time to certification
        time_to_cert = []
        for c in certs:
            if c["status"] == "achieved" and c.get("issue_date"):
                user = await self.db.users.find_one({"id": c["user_id"]})
                if user:
                    delta = c["issue_date"] - user["hire_date"]
                    time_to_cert.append(delta.days)
        
        return {
            "total_certifications": len(certs),
            "by_type": dict(by_type),
            "pass_rates": {
                k: {"rate": v["passed"]/v["attempts"], "attempts": v["attempts"]}
                for k, v in pass_rates.items()
            },
            "average_time_to_certification_days": sum(time_to_cert)/len(time_to_cert) if time_to_cert else 0,
            "expiring_soon": len([
                c for c in certs 
                if c["status"] == "achieved" 
                and c.get("expiry_date") 
                and c["expiry_date"] < datetime.utcnow() + timedelta(days=90)
            ]),
            "roi_analysis": await self._get_certification_roi()
        }
    
    # ── Predictive Analytics ────────────────────────────────────────────
    
    async def predict_at_risk_learners(self) -> List[Dict]:
        """Predict learners at risk of falling behind."""
        # Get all active enrollments
        active = await self.db.enrollments.find({
            "status": {"$in": ["not_started", "in_progress"]}
        }).to_list(None)
        
        at_risk = []
        for enrollment in active:
            risk_score = 0
            reasons = []
            
            # Overdue
            if enrollment.get("due_date") and enrollment["due_date"] < datetime.utcnow():
                risk_score += 40
                reasons.append("overdue")
            
            # Low progress
            if enrollment.get("progress_percent", 0) < 30:
                risk_score += 30
                reasons.append("low_progress")
            
            # No activity in 14 days
            if enrollment.get("last_activity"):
                days_inactive = (datetime.utcnow() - enrollment["last_activity"]).days
                if days_inactive > 14:
                    risk_score += 20
                    reasons.append(f"inactive_{days_inactive}_days")
            
            # Past due date approaching
            if enrollment.get("due_date"):
                days_until_due = (enrollment["due_date"] - datetime.utcnow()).days
                if 0 < days_until_due < 7 and enrollment.get("progress_percent", 0) < 70:
                    risk_score += 10
                    reasons.append("deadline_approaching")
            
            if risk_score >= 50:
                user = await self.db.users.find_one({"id": enrollment["user_id"]})
                at_risk.append({
                    "user_id": enrollment["user_id"],
                    "user_name": user["name"] if user else "Unknown",
                    "module_code": enrollment["module_code"],
                    "risk_score": risk_score,
                    "reasons": reasons,
                    "recommended_action": self._get_risk_mitigation(risk_score, reasons)
                })
        
        return sorted(at_risk, key=lambda x: x["risk_score"], reverse=True)
    
    async def forecast_training_needs(self, months_ahead: int = 6) -> Dict:
        """Forecast future training needs."""
        # Based on growth plans, certification expiries, etc.
        now = datetime.utcnow()
        
        # Expiring certifications
        expiring = await self.db.certifications.find({
            "status": "achieved",
            "expiry_date": {"$lte": now + timedelta(days=30*months_ahead)}
        }).to_list(None)
        
        # New hires expected
        # (Would integrate with HR system)
        
        # Regulatory changes
        # (Would integrate with regulatory watch)
        
        return {
            "forecast_period_months": months_ahead,
            "expiring_certifications": len(expiring),
            "renewal_training_needed": len(expiring) * 8,  # 8 hours per renewal
            "new_hire_training_needed": 0,  # Would come from HR
            "regulatory_training_needed": 0,  # Would come from regulatory watch
            "total_estimated_hours": len(expiring) * 8,
            "budget_estimate": len(expiring) * 500  # $500 per renewal
        }
    
    # ── Helper Methods ──────────────────────────────────────────────────
    
    async def _count_competent_users(self) -> int:
        """Count users who are competent in all required areas."""
        users = await self.db.users.find().to_list(None)
        competent = 0
        
        for user in users:
            required = COMPETENCE_MATRIX.get(user["tier"], {})
            is_competent = True
            
            for comp, level in required.items():
                assessment = await self.db.assessments.find_one(
                    {"user_id": user["id"], "competency": comp},
                    sort=[("assessed_at", -1)]
                )
                if not assessment or not assessment.get("is_competent"):
                    is_competent = False
                    break
            
            if is_competent:
                competent += 1
        
        return competent
    
    def _calculate_score_distribution(self, scores: List[int]) -> Dict:
        """Calculate score distribution buckets."""
        buckets = {"0-49": 0, "50-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
        for s in scores:
            if s < 50:
                buckets["0-49"] += 1
            elif s < 60:
                buckets["50-59"] += 1
            elif s < 70:
                buckets["60-69"] += 1
            elif s < 80:
                buckets["70-79"] += 1
            elif s < 90:
                buckets["80-89"] += 1
            else:
                buckets["90-100"] += 1
        return buckets
    
    def _get_risk_mitigation(self, risk_score: int, reasons: List[str]) -> str:
        """Get recommended risk mitigation action."""
        if risk_score >= 70:
            return "Immediate manager intervention required"
        elif "overdue" in reasons:
            return "Reschedule with manager and set new deadline"
        elif "low_progress" in reasons:
            return "Assign learning buddy or reduce workload"
        else:
            return "Send reminder and offer support resources"
```

---

## 9. Integration Architecture

### 9.1 Knowledge Management Integration

```python
# integrations/knowledge_integration.py
from datetime import datetime
from typing import Dict, Any, Optional


class TrainingKnowledgeIntegration:
    """Integrates training system with GRC_Claw knowledge management."""
    
    def __init__(self, db, knowledge_service):
        self.db = db
        self.knowledge = knowledge_service
    
    async def capture_training_knowledge(self, event_type: str, data: Dict) -> str:
        """Capture training events as knowledge artifacts."""
        artifact = {
            "artifact_type": "TRAINING_KNOWLEDGE",
            "event_type": event_type,
            "captured_at": datetime.utcnow().isoformat(),
            "content": data,
            "knowledge_links": {
                "related_policies": [],
                "related_controls": [],
                "related_artifacts": []
            }
        }
        
        # Store in knowledge repository
        artifact_id = await self.knowledge.capture_artifact(artifact)
        return artifact_id
    
    async def link_training_to_incident(self, training_id: str, incident_id: str):
        """Link training records to incidents for lessons learned."""
        await self.db.training_incident_links.insert_one({
            "training_id": training_id,
            "incident_id": incident_id,
            "link_type": "informed_by",
            "created_at": datetime.utcnow()
        })
    
    async def get_training_lessons_learned(self, incident_category: str) -> list:
        """Retrieve training lessons learned for a specific incident type."""
        # Query knowledge repository for related training artifacts
        artifacts = await self.knowledge.search_artifacts(
            query=f"training lessons {incident_category}",
            artifact_type="TRAINING_KNOWLEDGE",
            limit=10
        )
        return artifacts
    
    async def update_training_from_incident(self, incident_id: str):
        """Update training content based on incident lessons learned."""
        # Get incident details
        incident = await self.db.incidents.find_one({"id": incident_id})
        if not incident:
            return
        
        # Identify affected training modules
        affected_modules = self._map_incident_to_modules(incident)
        
        for module_code in affected_modules:
            # Create update task
            await self.db.training_update_tasks.insert_one({
                "module_code": module_code,
                "incident_id": incident_id,
                "update_type": "content_enhancement",
                "priority": incident.get("severity", "medium"),
                "status": "pending",
                "created_at": datetime.utcnow()
            })
            
            # Trigger awareness briefing if critical
            if incident.get("severity") in ["critical", "high"]:
                await self._trigger_lessons_learned_briefing(incident, module_code)
    
    def _map_incident_to_modules(self, incident: Dict) -> list:
        """Map incident characteristics to training modules."""
        category_module_map = {
            "bias": ["M07", "M05"],
            "data_leak": ["M05", "M04"],
            "prompt_injection": ["M03", "M04"],
            "hallucination": ["M03", "M08"],
            "agent_misbehavior": ["M06", "M13"],
        }
        
        return category_module_map.get(incident.get("category"), ["M13"])
```

### 9.2 Evidence Export (OSCAL Format)

```python
# integrations/evidence_export.py
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any


class OSCALEvidenceExporter:
    """Export training evidence in OSCAL format for audit."""
    
    def __init__(self, db):
        self.db = db
    
    async def export_user_evidence_oscal(self, user_id: str) -> Dict:
        """Export user's training evidence in OSCAL format."""
        user = await self.db.users.find_one({"id": user_id})
        
        # Get all evidence
        evidence_records = await self.db.evidence_records.find({
            "user_id": user_id
        }).to_list(None)
        
        # Build OSCAL assessment results
        oscal = {
            "assessment-results": {
                "uuid": str(uuid4()),
                "metadata": {
                    "title": f"Training Competence Evidence - {user['name']}",
                    "last-modified": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "oscal-version": "1.1.2"
                },
                "import-ap": {
                    "href": "catalog://grc-claw/ai-training-framework"
                },
                "results": []
            }
        }
        
        for evidence in evidence_records:
            result = {
                "uuid": evidence["id"],
                "title": f"{evidence['artifact_type']} - {evidence.get('module_code', 'N/A')}",
                "description": f"Training evidence for clause {evidence['clause']}",
                "start": evidence["captured_at"],
                "end": evidence["captured_at"],
                "reviewed-controls": {
                    "control-selections": [
                        {
                            "include-controls": [
                                {"control-id": f"ISO42001-{evidence['clause']}"}
                            ]
                        }
                    ]
                },
                "observations": [
                    {
                        "uuid": str(uuid4()),
                        "title": evidence["artifact_type"],
                        "description": json.dumps(evidence["content"]),
                        "methods": ["EXAMINE"],
                        "subjects": [
                            {"subject-uuid": user_id, "type": "user"}
                        ]
                    }
                ],
                "risk": {
                    "uuid": str(uuid4()),
                    "title": f"Competence risk for {user['name']}",
                    "description": f"Risk associated with training evidence",
                    "statement": self._generate_risk_statement(evidence)
                }
            }
            oscal["assessment-results"]["results"].append(result)
        
        # Add integrity hash
        oscal["assessment-results"]["metadata"]["integrity_hash"] = (
            hashlib.sha256(json.dumps(oscal, sort_keys=True).encode()).hexdigest()
        )
        
        return oscal
    
    def _generate_risk_statement(self, evidence: Dict) -> str:
        """Generate risk statement for evidence."""
        if evidence["clause"] == "7.2":
            return (
                f"Competence evidence for {evidence.get('module_code', 'training')} "
                f"shows {'adequate' if evidence['content'].get('is_competent', True) else 'inadequate'} "
                f"competence verification."
            )
        else:
            return (
                f"Awareness evidence for {evidence.get('module_code', 'training')} "
                f"confirms policy acknowledgment and completion."
            )
    
    async def export_cohort_evidence(self, cohort_id: str) -> Dict:
        """Export evidence for an entire cohort."""
        cohort = await self.db.cohorts.find_one({"id": cohort_id})
        if not cohort:
            raise ValueError("Cohort not found")
        
        user_ids = cohort.get("user_ids", [])
        
        cohort_evidence = {
            "cohort_id": cohort_id,
            "cohort_name": cohort.get("name"),
            "export_date": datetime.utcnow().isoformat(),
            "user_count": len(user_ids),
            "users": []
        }
        
        for user_id in user_ids:
            user_evidence = await self.export_user_evidence_oscal(user_id)
            cohort_evidence["users"].append(user_evidence)
        
        return cohort_evidence
```

---

## 10. Deployment Guide

### 10.1 Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  # API Server
  training-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/grc_training
      - REDIS_URL=redis://redis:6379
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - MONGODB_URL=mongodb://mongo:27017/grc_evidence
    depends_on:
      - postgres
      - redis
      - elasticsearch
      - mongo
    volumes:
      - ./app:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # Background Workers
  training-worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/grc_training
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: celery -A tasks worker --loglevel=info

  # Scheduled Tasks
  training-scheduler:
    build:
      context: .
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/grc_training
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: celery -A tasks beat --loglevel=info

  # Databases
  postgres:
    image: postgres:16
    environment:
      - POSTGRES_USER=grc
      - POSTGRES_PASSWORD=grc
      - POSTGRES_DB=grc_training
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  # Analytics
  superset:
    image: apache/superset:latest
    ports:
      - "8088:8088"
    environment:
      - SUPERSET_SECRET_KEY=grc_claw_superset_secret
    volumes:
      - superset_data:/app/superset_home

volumes:
  postgres_data:
  redis_data:
  es_data:
  mongo_data:
  superset_data:
```

### 10.2 Database Schema

```sql
-- migrations/001_initial_schema.sql

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL,
    tier INTEGER NOT NULL CHECK (tier BETWEEN 0 AND 4),
    department VARCHAR(100),
    manager_id UUID REFERENCES users(id),
    is_contractor BOOLEAN DEFAULT FALSE,
    hire_date TIMESTAMP NOT NULL,
    competence_levels JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Modules table
CREATE TABLE modules (
    id UUID PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tier INTEGER NOT NULL,
    competencies TEXT[] DEFAULT '{}',
    clause VARCHAR(10) NOT NULL,
    format VARCHAR(50) NOT NULL,
    duration_minutes INTEGER NOT NULL,
    passing_score INTEGER DEFAULT 70,
    evidence_types TEXT[] DEFAULT '{}',
    prerequisites TEXT[] DEFAULT '{}',
    certification_mapping VARCHAR(100),
    version VARCHAR(10) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enrollments table
CREATE TABLE enrollments (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    module_id UUID NOT NULL REFERENCES modules(id),
    status VARCHAR(20) DEFAULT 'not_started',
    progress_percent INTEGER DEFAULT 0,
    score INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    due_date TIMESTAMP,
    evidence_artifacts JSONB DEFAULT '[]',
    assessor_notes TEXT,
    effectiveness_rating INTEGER,
    last_activity TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Competency assessments
CREATE TABLE competency_assessments (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    competency VARCHAR(10) NOT NULL,
    required_level VARCHAR(20) NOT NULL,
    assessed_level VARCHAR(20) NOT NULL,
    assessment_method VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL,
    assessor_id UUID NOT NULL,
    assessed_at TIMESTAMP DEFAULT NOW(),
    evidence_ids TEXT[] DEFAULT '{}',
    next_assessment_date TIMESTAMP,
    is_competent BOOLEAN DEFAULT FALSE
);

-- Certifications
CREATE TABLE certifications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    certification_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    issue_date TIMESTAMP,
    expiry_date TIMESTAMP,
    credential_id VARCHAR(255),
    verification_url TEXT,
    cpe_credits INTEGER DEFAULT 0,
    internal_equivalent VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Evidence records (dual-track)
CREATE TABLE evidence_records (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    clause VARCHAR(10) NOT NULL,
    artifact_type VARCHAR(50) NOT NULL,
    module_code VARCHAR(10),
    content JSONB NOT NULL,
    captured_at TIMESTAMP DEFAULT NOW(),
    captured_by VARCHAR(255) NOT NULL,
    retention_class VARCHAR(20) DEFAULT 'standard',
    integrity_hash VARCHAR(64)
);

-- Kirkpatrick evaluations
CREATE TABLE kirkpatrick_surveys (
    id UUID PRIMARY KEY,
    level INTEGER NOT NULL,
    enrollment_id UUID REFERENCES enrollments(id),
    user_id UUID NOT NULL REFERENCES users(id),
    module_code VARCHAR(10),
    responses JSONB NOT NULL,
    submitted_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE kirkpatrick_evaluations (
    id UUID PRIMARY KEY,
    level INTEGER NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    module_code VARCHAR(10) NOT NULL,
    pre_score INTEGER,
    post_score INTEGER NOT NULL,
    learning_gain INTEGER,
    percent_gain DECIMAL(5,2),
    passed BOOLEAN DEFAULT FALSE,
    evaluated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE kirkpatrick_behaviors (
    id UUID PRIMARY KEY,
    level INTEGER NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    observer_id UUID NOT NULL,
    module_code VARCHAR(10) NOT NULL,
    observations JSONB NOT NULL,
    observation_date TIMESTAMP DEFAULT NOW(),
    days_since_training INTEGER
);

CREATE TABLE kirkpatrick_results (
    id UUID PRIMARY KEY,
    level INTEGER NOT NULL,
    module_code VARCHAR(10) NOT NULL,
    metrics JSONB NOT NULL,
    evaluation_period JSONB,
    roi_calculation JSONB,
    evaluated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_enrollments_user ON enrollments(user_id);
CREATE INDEX idx_enrollments_module ON enrollments(module_id);
CREATE INDEX idx_enrollments_status ON enrollments(status);
CREATE INDEX idx_assessments_user ON competency_assessments(user_id);
CREATE INDEX idx_evidence_user ON evidence_records(user_id);
CREATE INDEX idx_evidence_clause ON evidence_records(clause);
CREATE INDEX idx_kirkpatrick_module ON kirkpatrick_surveys(module_code);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER enrollments_updated_at
    BEFORE UPDATE ON enrollments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### 10.3 Environment Configuration

```bash
# .env
# Database
DATABASE_URL=postgresql://grc:grc@localhost:5432/grc_training
REDIS_URL=redis://localhost:6379
MONGODB_URL=mongodb://localhost:27017/grc_evidence
ELASTICSEARCH_URL=http://localhost:9200

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Feature Flags
ENABLE_ML_RECOMMENDATIONS=true
ENABLE_SPACED_REPETITION=true
ENABLE_PREDICTIVE_ANALYTICS=true

# Notifications
SMTP_HOST=smtp.company.com
SMTP_PORT=583
SMTP_USER=training@company.com
SMTP_PASSWORD=app-password

# External Integrations
GAICC_API_KEY=your-gaicc-key
IAPP_API_KEY=your-iapp-key
HR_SYSTEM_API_URL=https://hr.company.com/api
```

### 10.4 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/grc-claw/training-implementation.git
cd training-implementation

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup databases
docker-compose up -d postgres redis elasticsearch mongo

# 5. Run migrations
alembic upgrade head

# 6. Seed initial data
python scripts/seed_modules.py
python scripts/seed_competence_matrix.py

# 7. Start services
docker-compose up -d

# 8. Run tests
pytest tests/ -v --cov=app

# 9. Access API docs
open http://localhost:8000/docs
```

---

## Appendix A: Module Seed Data

```python
# scripts/seed_modules.py
"""Seed the 14 training modules from the framework."""

MODULES = [
    {
        "code": "M01",
        "title": "AI Awareness & Policy",
        "description": "Foundational AI literacy and organizational policy awareness",
        "tier": 0,
        "competencies": ["C1"],
        "clause": "7.3",
        "format": "self-paced",
        "duration_minutes": 60,
        "passing_score": 70,
        "evidence_types": ["completion_record", "policy_acknowledgment"],
        "prerequisites": [],
        "certification_mapping": None
    },
    {
        "code": "M02",
        "title": "Responsible AI Use",
        "description": "Responsible use principles and practical guidelines",
        "tier": 0,
        "competencies": ["C1", "C2"],
        "clause": "7.3",
        "format": "self-paced",
        "duration_minutes": 60,
        "passing_score": 70,
        "evidence_types": ["quiz_score", "acknowledgment"],
        "prerequisites": ["M01"],
        "certification_mapping": None
    },
    {
        "code": "M03",
        "title": "AI in Your Role",
        "description": "Role-specific AI applications and scenarios",
        "tier": 1,
        "competencies": ["C1", "C2", "C6"],
        "clause": "7.2",
        "format": "scenario",
        "duration_minutes": 120,
        "passing_score": 75,
        "evidence_types": ["scenario_assessment", "completion"],
        "prerequisites": ["M01", "M02"],
        "certification_mapping": None
    },
    {
        "code": "M04",
        "title": "Output Validation & Escalation",
        "description": "Hands-on lab for validating AI outputs and escalation procedures",
        "tier": 1,
        "competencies": ["C5", "C7"],
        "clause": "7.2",
        "format": "lab",
        "duration_minutes": 120,
        "passing_score": 75,
        "evidence_types": ["lab_exercise", "assessment"],
        "prerequisites": ["M03"],
        "certification_mapping": None
    },
    {
        "code": "M05",
        "title": "Data Handling & Classification",
        "description": "Data classification, handling procedures, and case studies",
        "tier": 1,
        "competencies": ["C4", "C8"],
        "clause": "7.2",
        "format": "self-paced",
        "duration_minutes": 90,
        "passing_score": 70,
        "evidence_types": ["quiz_score", "case_study"],
        "prerequisites": ["M02"],
        "certification_mapping": None
    },
    {
        "code": "M06",
        "title": "Model Governance Fundamentals",
        "description": "Instructor-led workshop on model governance principles",
        "tier": 2,
        "competencies": ["C2", "C5"],
        "clause": "7.2",
        "format": "instructor-led",
        "duration_minutes": 240,
        "passing_score": 75,
        "evidence_types": ["workshop_assessment", "project_artifact"],
        "prerequisites": ["M03", "M05"],
        "certification_mapping": "GAICC_Foundation"
    },
    {
        "code": "M07",
        "title": "Data Provenance & Bias",
        "description": "Hands-on lab for bias detection and data provenance",
        "tier": 2,
        "competencies": ["C4", "C5"],
        "clause": "7.2",
        "format": "lab",
        "duration_minutes": 240,
        "passing_score": 80,
        "evidence_types": ["bias_assessment_report"],
        "prerequisites": ["M06"],
        "certification_mapping": None
    },
    {
        "code": "M08",
        "title": "Testing, Validation & Monitoring",
        "description": "Comprehensive testing and monitoring methodologies",
        "tier": 2,
        "competencies": ["C5", "C7"],
        "clause": "7.2",
        "format": "instructor-led",
        "duration_minutes": 360,
        "passing_score": 80,
        "evidence_types": ["evaluation_report", "monitoring_plan"],
        "prerequisites": ["M06", "M07"],
        "certification_mapping": None
    },
    {
        "code": "M09",
        "title": "AI Risk Assessment",
        "description": "Workshop on AI risk assessment methodologies",
        "tier": 2,
        "competencies": ["C3", "C8"],
        "clause": "7.2",
        "format": "workshop",
        "duration_minutes": 240,
        "passing_score": 75,
        "evidence_types": ["risk_assessment_artifact"],
        "prerequisites": ["M06", "M08"],
        "certification_mapping": None
    },
    {
        "code": "M10",
        "title": "AIMS Implementation",
        "description": "GAICC Lead Implementer certification preparation",
        "tier": 3,
        "competencies": ["C9", "C2", "C3"],
        "clause": "7.2",
        "format": "instructor-led",
        "duration_minutes": 1920,
        "passing_score": 80,
        "evidence_types": ["gaicc_certification", "implementation_project"],
        "prerequisites": ["M09"],
        "certification_mapping": "GAICC_Lead_Implementer"
    },
    {
        "code": "M11",
        "title": "AIMS Internal Audit",
        "description": "GAICC Internal Auditor certification preparation",
        "tier": 3,
        "competencies": ["C10", "C9"],
        "clause": "7.2",
        "format": "instructor-led",
        "duration_minutes": 1920,
        "passing_score": 80,
        "evidence_types": ["gaicc_certification", "audit_report"],
        "prerequisites": ["M10"],
        "certification_mapping": "GAICC_Internal_Auditor"
    },
    {
        "code": "M12",
        "title": "AI Strategy & Risk Appetite",
        "description": "Executive briefing on AI strategy and risk appetite",
        "tier": 4,
        "competencies": ["C2", "C3", "C8"],
        "clause": "7.2",
        "format": "executive-briefing",
        "duration_minutes": 240,
        "passing_score": 75,
        "evidence_types": ["board_paper", "strategy_artifact"],
        "prerequisites": ["M09"],
        "certification_mapping": None
    },
    {
        "code": "M13",
        "title": "AI Incident Management",
        "description": "Cross-tier tabletop exercise for incident response",
        "tier": 0,
        "competencies": ["C7"],
        "clause": "7.2",
        "format": "tabletop",
        "duration_minutes": 120,
        "passing_score": 70,
        "evidence_types": ["exercise_participation", "evaluation"],
        "prerequisites": ["M02"],
        "certification_mapping": None
    },
    {
        "code": "M14",
        "title": "Policy Update Briefing",
        "description": "Micro-learning for policy updates and acknowledgments",
        "tier": 0,
        "competencies": ["C2"],
        "clause": "7.3",
        "format": "micro-learning",
        "duration_minutes": 30,
        "passing_score": 100,
        "evidence_types": ["acknowledgment_record"],
        "prerequisites": ["M01"],
        "certification_mapping": None
    }
]
```

---

## Appendix B: API Reference

### B.1 Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users` | Create user & auto-assign path |
| GET | `/api/v1/users/{id}/dashboard` | User learning dashboard |
| GET | `/api/v1/users/{id}/evidence` | Get user evidence |
| GET | `/api/v1/users/{id}/audit-dossier` | Generate audit dossier |
| POST | `/api/v1/enrollments` | Enroll in module |
| PATCH | `/api/v1/enrollments/{id}/progress` | Update progress |
| POST | `/api/v1/assessments` | Submit assessment |
| GET | `/api/v1/competencies/{user_id}/gaps` | Get competence gaps |
| GET | `/api/v1/recommendations/{user_id}` | Get recommendations |
| GET | `/api/v1/analytics/executive` | Executive dashboard |
| GET | `/api/v1/analytics/manager/{id}` | Manager dashboard |
| POST | `/api/v1/triggers/{type}` | Handle refresh trigger |

### B.2 Webhook Events

| Event | Description |
|-------|-------------|
| `enrollment.created` | New enrollment created |
| `enrollment.completed` | Module completed |
| `assessment.passed` | Assessment passed |
| `assessment.failed` | Assessment failed |
| `certification.achieved` | Certification earned |
| `competence.gap_identified` | New gap identified |
| `trigger.policy_update` | Policy update triggered |
| `trigger.incident` | Incident triggered training |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial implementation guide |

---

*End of Training Implementation Guide*

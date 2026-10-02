"""Pydantic models for the onboarding automator.

This module defines all request/response schemas used by the API.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "TaskStatus",
    "TaskPriority",
    "TaskType",
    "OnboardingStatus",
    "DocumentStatus",
    "ComplianceStatus",
    "EmployeeInfo",
    "OnboardingPlan",
    "OnboardingPlanCreate",
    "OnboardingPlanUpdate",
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "Document",
    "DocumentCreate",
    "DocumentUpdate",
    "Progress",
    "ProgressUpdate",
    "ComplianceCheck",
    "ComplianceCheckCreate",
    "ComplianceCheckUpdate",
    "HealthResponse",
    "WelcomeMessage",
    "WelcomeMessageCreate",
    "AgentResponse",
    "ErrorDetail",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TaskStatus(StrEnum):
    """Possible statuses for an onboarding task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class TaskPriority(StrEnum):
    """Priority levels for tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskType(StrEnum):
    """Categories of onboarding tasks."""

    DOCUMENT_SUBMISSION = "document_submission"
    SYSTEM_ACCESS = "system_access"
    TRAINING = "training"
    ORIENTATION = "orientation"
    MEETING = "meeting"
    EQUIPMENT = "equipment"
    CUSTOM = "custom"


class OnboardingStatus(StrEnum):
    """Overall onboarding plan status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DocumentStatus(StrEnum):
    """Status of a submitted document."""

    PENDING = "pending"
    UPLOADED = "uploaded"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ComplianceStatus(StrEnum):
    """Result of a compliance check."""

    PASS = "pass"  # noqa: S105
    FAIL = "fail"
    WARNING = "warning"
    PENDING = "pending"
    NOT_APPLICABLE = "not_applicable"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------


class EmployeeInfo(BaseModel):
    """Information about the employee being onboarded."""

    model_config = ConfigDict(extra="allow")

    employee_id: str = Field(..., description="Unique employee identifier")
    full_name: str = Field(..., min_length=1, max_length=200, description="Employee full name")
    email: str = Field(..., description="Employee email address")
    department: str = Field(..., description="Department name")
    role: str = Field(..., description="Job title / role")
    start_date: datetime = Field(..., description="Expected start date")
    manager_id: str | None = Field(None, description="Manager employee ID")
    location: str | None = Field(None, description="Office location or remote")
    employment_type: str = Field(default="full_time", description="Employment type")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OnboardingPlan(BaseModel):
    """A complete onboarding plan for an employee."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique plan identifier")
    employee: EmployeeInfo = Field(..., description="Employee information")
    status: OnboardingStatus = Field(default=OnboardingStatus.NOT_STARTED)
    tasks: list[UUID] = Field(default_factory=list, description="Associated task IDs")
    documents: list[UUID] = Field(default_factory=list, description="Associated document IDs")
    compliance_checks: list[UUID] = Field(default_factory=list, description="Compliance check IDs")
    progress: UUID | None = Field(None, description="Progress tracker ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OnboardingPlanCreate(BaseModel):
    """Request body for creating an onboarding plan."""

    employee: EmployeeInfo
    template_id: str | None = Field(None, description="Onboarding template to base plan on")
    metadata: dict[str, Any] = Field(default_factory=dict)


class OnboardingPlanUpdate(BaseModel):
    """Request body for updating an onboarding plan."""

    status: OnboardingStatus | None = None
    metadata: dict[str, Any] | None = None


class Task(BaseModel):
    """An individual onboarding task."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    plan_id: UUID = Field(..., description="Parent onboarding plan ID")
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=2000)
    task_type: TaskType = Field(default=TaskType.CUSTOM)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    due_date: datetime | None = None
    assigned_to: str | None = None
    document_id: UUID | None = None
    external_refs: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskCreate(BaseModel):
    """Request body for creating a task."""

    plan_id: UUID
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=2000)
    task_type: TaskType = TaskType.CUSTOM
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None
    assigned_to: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskUpdate(BaseModel):
    """Request body for updating a task."""

    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = Field(None, max_length=2000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assigned_to: str | None = None
    metadata: dict[str, Any] | None = None


class Document(BaseModel):
    """A document submitted during onboarding."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    plan_id: UUID = Field(..., description="Parent onboarding plan ID")
    task_id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=300)
    document_type: str = Field(..., description="Document type (e.g. 'id_proof', 'contract')")
    file_type: str = Field(..., description="MIME type or file extension")
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    storage_path: str | None = None
    file_size_bytes: int | None = None
    checksum: str | None = None
    rejection_reason: str | None = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: datetime | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(BaseModel):
    """Request body for registering a document."""

    plan_id: UUID
    name: str = Field(..., min_length=1, max_length=300)
    document_type: str = Field(..., min_length=1)
    task_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentUpdate(BaseModel):
    """Request body for updating document status."""

    status: DocumentStatus | None = None
    rejection_reason: str | None = None
    metadata: dict[str, Any] | None = None


class Progress(BaseModel):
    """Progress tracking for an onboarding plan."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    plan_id: UUID = Field(..., description="Parent onboarding plan ID")
    total_tasks: int = Field(default=0)
    completed_tasks: int = Field(default=0)
    blocked_tasks: int = Field(default=0)
    pending_tasks: int = Field(default=0)
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    overall_status: OnboardingStatus = OnboardingStatus.NOT_STARTED
    milestones: list[dict[str, Any]] = Field(default_factory=list)
    risk_assessment: str | None = None
    estimated_completion: datetime | None = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProgressUpdate(BaseModel):
    """Request body for updating progress."""

    total_tasks: int | None = Field(None, ge=0)
    completed_tasks: int | None = Field(None, ge=0)
    blocked_tasks: int | None = Field(None, ge=0)
    pending_tasks: int | None = Field(None, ge=0)
    risk_assessment: str | None = None
    estimated_completion: datetime | None = None


class ComplianceCheck(BaseModel):
    """A compliance check result for an onboarding plan."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    plan_id: UUID = Field(..., description="Parent onboarding plan ID")
    name: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=2000)
    category: str = Field(..., description="Compliance category (e.g. 'data_privacy', 'labor_law')")
    status: ComplianceStatus = Field(default=ComplianceStatus.PENDING)
    severity: TaskPriority = Field(default=TaskPriority.MEDIUM)
    details: str = Field(default="")
    remediation_steps: list[str] = Field(default_factory=list)
    checked_at: datetime | None = None
    expires_at: datetime | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ComplianceCheckCreate(BaseModel):
    """Request body for creating a compliance check."""

    plan_id: UUID
    name: str = Field(..., min_length=1, max_length=300)
    description: str = Field(default="", max_length=2000)
    category: str = Field(..., min_length=1)
    severity: TaskPriority = TaskPriority.MEDIUM


class ComplianceCheckUpdate(BaseModel):
    """Request body for updating a compliance check."""

    status: ComplianceStatus | None = None
    details: str | None = None
    remediation_steps: list[str] | None = None
    severity: TaskPriority | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: str = "development"


class WelcomeMessage(BaseModel):
    """A welcome message generated for a new employee."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    plan_id: UUID = Field(..., description="Parent onboarding plan ID")
    subject: str = Field(..., min_length=1, max_length=300)
    body: str = Field(..., min_length=1)
    channel: str = Field(default="email", description="Delivery channel")
    sent: bool = False
    sent_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WelcomeMessageCreate(BaseModel):
    """Request body for generating a welcome message."""

    plan_id: UUID
    channel: str = "email"
    include_schedule: bool = True
    tone: str = Field(default="friendly", description="Tone of the message")


class AgentResponse(BaseModel):
    """Generic response from an agent operation."""

    success: bool
    message: str
    data: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)
    agent_name: str | None = None
    processing_time_ms: float | None = None


class ErrorDetail(BaseModel):
    """Detailed error response."""

    error: str
    detail: str
    code: str = "INTERNAL_ERROR"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

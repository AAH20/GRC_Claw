"""Tests for the Pydantic models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from onboarding_automator.models import (
    ComplianceCheck,
    ComplianceStatus,
    Document,
    DocumentStatus,
    EmployeeInfo,
    OnboardingPlan,
    OnboardingPlanCreate,
    OnboardingStatus,
    Progress,
    Task,
    TaskCreate,
    TaskPriority,
    TaskStatus,
    TaskType,
    WelcomeMessage,
)


def test_employee_info_creation() -> None:
    """Test EmployeeInfo model creation."""
    emp = EmployeeInfo(
        employee_id="EMP-001",
        full_name="Test User",
        email="test@example.com",
        department="Engineering",
        role="Developer",
        start_date=datetime.utcnow(),
    )
    assert emp.employee_id == "EMP-001"
    assert emp.employment_type == "full_time"


def test_onboarding_plan_creation() -> None:
    """Test OnboardingPlan model creation."""
    emp = EmployeeInfo(
        employee_id="EMP-001",
        full_name="Test User",
        email="test@example.com",
        department="Engineering",
        role="Developer",
        start_date=datetime.utcnow(),
    )
    plan = OnboardingPlan(employee=emp)
    assert plan.status == OnboardingStatus.NOT_STARTED
    assert isinstance(plan.id, UUID)


def test_task_creation() -> None:
    """Test Task model creation."""
    plan_id = UUID(int=1)
    task = Task(
        plan_id=plan_id,
        title="Test Task",
        task_type=TaskType.TRAINING,
        priority=TaskPriority.HIGH,
    )
    assert task.status == TaskStatus.PENDING
    assert task.plan_id == plan_id


def test_document_creation() -> None:
    """Test Document model creation."""
    plan_id = UUID(int=1)
    doc = Document(
        plan_id=plan_id,
        name="Test Doc",
        document_type="id_proof",
        file_type="application/pdf",
    )
    assert doc.status == DocumentStatus.PENDING


def test_progress_creation() -> None:
    """Test Progress model creation."""
    plan_id = UUID(int=1)
    progress = Progress(plan_id=plan_id, total_tasks=10, completed_tasks=5)
    assert progress.completion_percentage == 0.0


def test_compliance_check_creation() -> None:
    """Test ComplianceCheck model creation."""
    plan_id = UUID(int=1)
    check = ComplianceCheck(
        plan_id=plan_id,
        name="GDPR Check",
        category="data_privacy",
    )
    assert check.status == ComplianceStatus.PENDING


def test_welcome_message_creation() -> None:
    """Test WelcomeMessage model creation."""
    plan_id = UUID(int=1)
    msg = WelcomeMessage(
        plan_id=plan_id,
        subject="Welcome!",
        body="Welcome to the team!",
    )
    assert msg.sent is False
    assert msg.channel == "email"


def test_task_create_schema() -> None:
    """Test TaskCreate request schema."""
    plan_id = UUID(int=1)
    task_create = TaskCreate(plan_id=plan_id, title="New Task")
    assert task_create.task_type == TaskType.CUSTOM
    assert task_create.priority == TaskPriority.MEDIUM


def test_onboarding_plan_create_schema() -> None:
    """Test OnboardingPlanCreate request schema."""
    emp = EmployeeInfo(
        employee_id="EMP-001",
        full_name="Test User",
        email="test@example.com",
        department="Engineering",
        role="Developer",
        start_date=datetime.utcnow(),
    )
    plan_create = OnboardingPlanCreate(employee=emp)
    assert plan_create.template_id is None

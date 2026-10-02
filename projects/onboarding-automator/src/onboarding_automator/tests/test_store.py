"""Tests for the in-memory store."""

from __future__ import annotations

from uuid import UUID

import pytest

from onboarding_automator.integrations.store import InMemoryStore
from onboarding_automator.models import (
    ComplianceCheck,
    Document,
    EmployeeInfo,
    OnboardingPlan,
    Progress,
    Task,
    WelcomeMessage,
)


@pytest.fixture
async def store() -> InMemoryStore:
    """Create a fresh in-memory store."""
    return InMemoryStore()


@pytest.fixture
def sample_plan() -> OnboardingPlan:
    """Create a sample onboarding plan."""
    emp = EmployeeInfo(
        employee_id="EMP-001",
        full_name="Test User",
        email="test@example.com",
        department="Engineering",
        role="Developer",
        start_date="2024-01-15T00:00:00",
    )
    return OnboardingPlan(employee=emp)


@pytest.mark.asyncio
async def test_save_and_get_plan(store: InMemoryStore, sample_plan: OnboardingPlan) -> None:
    """Test saving and retrieving a plan."""
    await store.save_plan(sample_plan)
    retrieved = await store.get_plan(sample_plan.id)
    assert retrieved is not None
    assert retrieved.id == sample_plan.id


@pytest.mark.asyncio
async def test_list_plans(store: InMemoryStore, sample_plan: OnboardingPlan) -> None:
    """Test listing all plans."""
    await store.save_plan(sample_plan)
    plans = await store.list_plans()
    assert len(plans) == 1


@pytest.mark.asyncio
async def test_delete_plan(store: InMemoryStore, sample_plan: OnboardingPlan) -> None:
    """Test deleting a plan."""
    await store.save_plan(sample_plan)
    deleted = await store.delete_plan(sample_plan.id)
    assert deleted is True
    assert await store.get_plan(sample_plan.id) is None


@pytest.mark.asyncio
async def test_save_and_get_task(store: InMemoryStore, sample_plan: OnboardingPlan) -> None:
    """Test saving and retrieving a task."""
    task = Task(plan_id=sample_plan.id, title="Test Task")
    await store.save_task(task)
    retrieved = await store.get_task(task.id)
    assert retrieved is not None
    assert retrieved.title == "Test Task"


@pytest.mark.asyncio
async def test_list_tasks_by_plan(store: InMemoryStore, sample_plan: OnboardingPlan) -> None:
    """Test listing tasks filtered by plan."""
    task1 = Task(plan_id=sample_plan.id, title="Task 1")
    task2 = Task(plan_id=UUID(int=999), title="Task 2")
    await store.save_task(task1)
    await store.save_task(task2)

    tasks = await store.list_tasks(plan_id=sample_plan.id)
    assert len(tasks) == 1
    assert tasks[0].title == "Task 1"


@pytest.mark.asyncio
async def test_save_and_get_document(store: InMemoryStore, sample_plan: OnboardingPlan) -> None:
    """Test saving and retrieving a document."""
    doc = Document(
        plan_id=sample_plan.id,
        name="Test Doc",
        document_type="id_proof",
        file_type="application/pdf",
    )
    await store.save_document(doc)
    retrieved = await store.get_document(doc.id)
    assert retrieved is not None
    assert retrieved.name == "Test Doc"


@pytest.mark.asyncio
async def test_save_and_get_progress(store: InMemoryStore, sample_plan: OnboardingPlan) -> None:
    """Test saving and retrieving progress."""
    progress = Progress(plan_id=sample_plan.id, total_tasks=10, completed_tasks=5)
    await store.save_progress(progress)
    retrieved = await store.get_progress(sample_plan.id)
    assert retrieved is not None
    assert retrieved.total_tasks == 10


@pytest.mark.asyncio
async def test_save_and_get_compliance_check(
    store: InMemoryStore, sample_plan: OnboardingPlan
) -> None:
    """Test saving and retrieving a compliance check."""
    check = ComplianceCheck(
        plan_id=sample_plan.id,
        name="GDPR Check",
        category="data_privacy",
    )
    await store.save_compliance_check(check)
    retrieved = await store.get_compliance_check(check.id)
    assert retrieved is not None
    assert retrieved.name == "GDPR Check"


@pytest.mark.asyncio
async def test_save_and_get_welcome_message(
    store: InMemoryStore, sample_plan: OnboardingPlan
) -> None:
    """Test saving and retrieving a welcome message."""
    msg = WelcomeMessage(
        plan_id=sample_plan.id,
        subject="Welcome!",
        body="Welcome to the team!",
    )
    await store.save_welcome_message(msg)
    retrieved = await store.get_welcome_message(msg.id)
    assert retrieved is not None
    assert retrieved.subject == "Welcome!"

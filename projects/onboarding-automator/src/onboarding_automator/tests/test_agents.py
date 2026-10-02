"""Tests for the agent implementations."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from onboarding_automator.agents import (
    ComplianceCheckerAgent,
    DocumentCollectorAgent,
    ProgressTrackerAgent,
    TaskGeneratorAgent,
    WelcomeAgent,
)
from onboarding_automator.config.settings import Settings
from onboarding_automator.models import (
    ComplianceCheckCreate,
    Document,
    DocumentStatus,
    EmployeeInfo,
    OnboardingPlan,
    OnboardingPlanCreate,
    Task,
    TaskStatus,
    WelcomeMessageCreate,
)


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        environment="test",
        openai_api_key="test-key",
        llm_model="gpt-4o",
    )


@pytest.fixture
def employee_info() -> EmployeeInfo:
    """Create sample employee info."""
    return EmployeeInfo(
        employee_id="EMP-001",
        full_name="Jane Smith",
        email="jane@example.com",
        department="Engineering",
        role="Software Engineer",
        start_date=datetime.utcnow(),
    )


@pytest.fixture
def onboarding_plan(employee_info: EmployeeInfo) -> OnboardingPlan:
    """Create a sample onboarding plan."""
    return OnboardingPlan(employee=employee_info)


class TestTaskGeneratorAgent:
    """Tests for TaskGeneratorAgent."""

    @pytest.mark.asyncio
    async def test_execute_success(
        self, settings: Settings, employee_info: EmployeeInfo
    ) -> None:
        """Test successful task generation."""
        agent = TaskGeneratorAgent(settings)
        plan_create = OnboardingPlanCreate(employee=employee_info)

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Generated tasks response"
            response = await agent.execute(plan_create)

        assert response.success is True
        assert response.agent_name == "TaskGeneratorAgent"
        assert "tasks" in (response.data or {})

    @pytest.mark.asyncio
    async def test_execute_with_existing_tasks(
        self, settings: Settings, employee_info: EmployeeInfo, onboarding_plan: OnboardingPlan
    ) -> None:
        """Test task generation with existing tasks."""
        agent = TaskGeneratorAgent(settings)
        plan_create = OnboardingPlanCreate(employee=employee_info)
        existing = [
            Task(
                plan_id=onboarding_plan.id,
                title="Existing Task",
                status=TaskStatus.COMPLETED,
            )
        ]

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Generated tasks"
            response = await agent.execute(plan_create, existing)

        assert response.success is True


class TestDocumentCollectorAgent:
    """Tests for DocumentCollectorAgent."""

    @pytest.mark.asyncio
    async def test_execute_success(self, settings: Settings) -> None:
        """Test successful document processing."""
        agent = DocumentCollectorAgent(settings)
        from uuid import UUID

        doc_create = DocumentCreate(
            plan_id=UUID(int=1),
            name="Test Document",
            document_type="id_proof",
        )

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Document processed"
            response = await agent.execute(doc_create)

        assert response.success is True
        assert response.agent_name == "DocumentCollectorAgent"

    @pytest.mark.asyncio
    async def test_verify_document(self, settings: Settings) -> None:
        """Test document verification."""
        agent = DocumentCollectorAgent(settings)
        from uuid import UUID

        doc = Document(
            plan_id=UUID(int=1),
            name="Test Doc",
            document_type="id_proof",
            status=DocumentStatus.UPLOADED,
        )

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Document verified"
            response = await agent.verify_document(doc)

        assert response.success is True


class TestProgressTrackerAgent:
    """Tests for ProgressTrackerAgent."""

    @pytest.mark.asyncio
    async def test_execute_success(
        self, settings: Settings, onboarding_plan: OnboardingPlan
    ) -> None:
        """Test successful progress tracking."""
        agent = ProgressTrackerAgent(settings)
        tasks = [
            Task(plan_id=onboarding_plan.id, title="Task 1", status=TaskStatus.COMPLETED),
            Task(plan_id=onboarding_plan.id, title="Task 2", status=TaskStatus.PENDING),
        ]

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Progress analysis"
            response = await agent.execute(onboarding_plan, tasks)

        assert response.success is True
        assert response.data is not None
        assert response.data["total_tasks"] == 2
        assert response.data["completed_tasks"] == 1


class TestComplianceCheckerAgent:
    """Tests for ComplianceCheckerAgent."""

    @pytest.mark.asyncio
    async def test_execute_success(
        self, settings: Settings, onboarding_plan: OnboardingPlan
    ) -> None:
        """Test successful compliance check."""
        agent = ComplianceCheckerAgent(settings)
        check_create = ComplianceCheckCreate(
            plan_id=onboarding_plan.id,
            name="GDPR Check",
            category="data_privacy",
        )

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Compliance check passed"
            response = await agent.execute(check_create, onboarding_plan)

        assert response.success is True
        assert response.agent_name == "ComplianceCheckerAgent"


class TestWelcomeAgent:
    """Tests for WelcomeAgent."""

    @pytest.mark.asyncio
    async def test_execute_success(
        self, settings: Settings, onboarding_plan: OnboardingPlan
    ) -> None:
        """Test successful welcome message generation."""
        agent = WelcomeAgent(settings)
        msg_create = WelcomeMessageCreate(plan_id=onboarding_plan.id)

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Subject: Welcome!\nWelcome to the team!"
            response = await agent.execute(msg_create, onboarding_plan)

        assert response.success is True
        assert response.agent_name == "WelcomeAgent"

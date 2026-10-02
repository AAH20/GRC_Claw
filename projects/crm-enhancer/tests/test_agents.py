"""Tests for CRM Enhancer agents."""

from __future__ import annotations

import pytest

from crm_enhancer.agents.contact_enrichment import (
    ContactData,
    ContactEnrichmentAgent,
    EnrichmentResult,
)
from crm_enhancer.agents.deal_scoring import DealData, DealScoringAgent, DealScore
from crm_enhancer.agents.followup_automation import (
    FollowUpAction,
    FollowUpAutomationAgent,
    FollowUpStatus,
    FollowUpTemplate,
)
from crm_enhancer.agents.meeting_scheduling import (
    MeetingRequest,
    MeetingSchedulingAgent,
    ScheduledMeeting,
    TimeSlot,
)
from crm_enhancer.agents.performance_analytics import (
    AgentEffectiveness,
    PerformanceAnalyticsAgent,
    SalesMetrics,
)
from crm_enhancer.agents.task_automation import (
    AutomatedTask,
    TaskAutomationAgent,
    TaskPriority,
    TaskStatus,
    TaskTemplate,
)


# Contact Enrichment Agent Tests


class TestContactEnrichmentAgent:
    """Tests for ContactEnrichmentAgent."""

    @pytest.fixture
    def agent(self) -> ContactEnrichmentAgent:
        """Create a contact enrichment agent."""
        return ContactEnrichmentAgent()

    @pytest.fixture
    def sample_contact(self) -> ContactData:
        """Create a sample contact."""
        return ContactData(
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            company="Acme Inc",
            phone="+1234567890",
        )

    @pytest.mark.asyncio
    async def test_enrich_contact_success(
        self, agent: ContactEnrichmentAgent, sample_contact: ContactData
    ) -> None:
        """Test successful contact enrichment."""
        result = await agent.enrich(sample_contact)
        assert isinstance(result, EnrichmentResult)
        assert result.contact.email == sample_contact.email
        assert result.company_domain == "example.com"
        assert result.confidence_score > 0.0
        assert len(result.sources) > 0

    @pytest.mark.asyncio
    async def test_enrich_contact_invalid_email(self, agent: ContactEnrichmentAgent) -> None:
        """Test enrichment with invalid email raises error."""
        contact = ContactData(email="invalid-email")
        with pytest.raises(ValueError, match="Valid email is required"):
            await agent.enrich(contact)

    @pytest.mark.asyncio
    async def test_bulk_enrich(self, agent: ContactEnrichmentAgent) -> None:
        """Test bulk contact enrichment."""
        contacts = [
            ContactData(email=f"user{i}@example.com") for i in range(5)
        ]
        results = await agent.bulk_enrich(contacts)
        assert len(results) == 5
        assert all(isinstance(r, EnrichmentResult) for r in results)


# Deal Scoring Agent Tests


class TestDealScoringAgent:
    """Tests for DealScoringAgent."""

    @pytest.fixture
    def agent(self) -> DealScoringAgent:
        """Create a deal scoring agent."""
        return DealScoringAgent()

    @pytest.fixture
    def sample_deal(self) -> DealData:
        """Create a sample deal."""
        return DealData(
            deal_id="deal_001",
            title="Enterprise Deal",
            value=75000.0,
            stage="proposal_price_quote",
            contact_email="buyer@example.com",
            company="Big Corp",
            days_in_stage=10,
            activities_count=5,
            last_activity_days=2,
        )

    @pytest.mark.asyncio
    async def test_score_deal_success(
        self, agent: DealScoringAgent, sample_deal: DealData
    ) -> None:
        """Test successful deal scoring."""
        result = await agent.score_deal(sample_deal)
        assert isinstance(result, DealScore)
        assert result.deal_id == sample_deal.deal_id
        assert 0 <= result.total_score <= 100
        assert result.priority in ["low", "medium", "high"]
        assert 0 <= result.win_probability <= 1
        assert len(result.factors) == 5

    @pytest.mark.asyncio
    async def test_score_deal_negative_value(
        self, agent: DealScoringAgent
    ) -> None:
        """Test scoring with negative deal value raises error."""
        deal = DealData(
            deal_id="deal_002",
            title="Bad Deal",
            value=-1000.0,
            stage="prospecting",
            contact_email="test@example.com",
        )
        with pytest.raises(ValueError, match="cannot be negative"):
            await agent.score_deal(deal)

    @pytest.mark.asyncio
    async def test_score_deal_priority_high(
        self, agent: DealScoringAgent
    ) -> None:
        """Test high-value deal gets high priority."""
        deal = DealData(
            deal_id="deal_003",
            title="Huge Deal",
            value=200000.0,
            stage="negotiation_review",
            contact_email="exec@example.com",
            days_in_stage=5,
            activities_count=10,
            last_activity_days=1,
        )
        result = await agent.score_deal(deal)
        assert result.priority == "high"
        assert result.total_score > 70

    @pytest.mark.asyncio
    async def test_score_multiple_deals(
        self, agent: DealScoringAgent
    ) -> None:
        """Test scoring multiple deals returns sorted results."""
        deals = [
            DealData(
                deal_id=f"deal_{i}",
                title=f"Deal {i}",
                value=10000.0 * (i + 1),
                stage="prospecting",
                contact_email=f"user{i}@example.com",
            )
            for i in range(3)
        ]
        results = await agent.score_deals(deals)
        assert len(results) == 3
        # Results should be sorted by score descending
        assert results[0].total_score >= results[1].total_score


# Task Automation Agent Tests


class TestTaskAutomationAgent:
    """Tests for TaskAutomationAgent."""

    @pytest.fixture
    def agent(self) -> TaskAutomationAgent:
        """Create a task automation agent."""
        return TaskAutomationAgent()

    @pytest.fixture
    def sample_template(self) -> TaskTemplate:
        """Create a sample task template."""
        return TaskTemplate(
            name="Test Task",
            description="A test task",
            priority=TaskPriority.HIGH,
            due_in_days=2,
        )

    @pytest.mark.asyncio
    async def test_create_task(
        self, agent: TaskAutomationAgent, sample_template: TaskTemplate
    ) -> None:
        """Test task creation."""
        task = await agent.create_task(sample_template)
        assert isinstance(task, AutomatedTask)
        assert task.template.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.due_date is not None

    @pytest.mark.asyncio
    async def test_create_task_invalid(
        self, agent: TaskAutomationAgent
    ) -> None:
        """Test task creation with invalid template."""
        template = TaskTemplate(name="", description="Invalid")
        with pytest.raises(ValueError, match="must have a name"):
            await agent.create_task(template)

    @pytest.mark.asyncio
    async def test_create_follow_up_task(
        self, agent: TaskAutomationAgent
    ) -> None:
        """Test follow-up task creation."""
        task = await agent.create_follow_up_task(
            contact_email="test@example.com",
            deal_id="deal_001",
        )
        assert task.template.name == "Follow up with test@example.com"
        assert "follow-up" in task.template.tags

    @pytest.mark.asyncio
    async def test_complete_task(
        self, agent: TaskAutomationAgent, sample_template: TaskTemplate
    ) -> None:
        """Test task completion."""
        task = await agent.create_task(sample_template)
        completed = await agent.complete_task(task)
        assert completed.status == TaskStatus.COMPLETED
        assert completed.completed_at is not None

    @pytest.mark.asyncio
    async def test_fail_task(
        self, agent: TaskAutomationAgent, sample_template: TaskTemplate
    ) -> None:
        """Test task failure."""
        task = await agent.create_task(sample_template)
        failed = await agent.fail_task(task, "Test failure reason")
        assert failed.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_auto_assign_task(
        self, agent: TaskAutomationAgent, sample_template: TaskTemplate
    ) -> None:
        """Test task auto-assignment."""
        task = await agent.create_task(sample_template)
        assigned = await agent.auto_assign_task(task, ["user1", "user2", "user3"])
        assert assigned.assigned_to in ["user1", "user2", "user3"]

    @pytest.mark.asyncio
    async def test_auto_assign_no_members(
        self, agent: TaskAutomationAgent, sample_template: TaskTemplate
    ) -> None:
        """Test auto-assignment with no team members."""
        task = await agent.create_task(sample_template)
        with pytest.raises(ValueError, match="No team members"):
            await agent.auto_assign_task(task, [])


# Meeting Scheduling Agent Tests


class TestMeetingSchedulingAgent:
    """Tests for MeetingSchedulingAgent."""

    @pytest.fixture
    def agent(self) -> MeetingSchedulingAgent:
        """Create a meeting scheduling agent."""
        return MeetingSchedulingAgent()

    @pytest.fixture
    def sample_request(self) -> MeetingRequest:
        """Create a sample meeting request."""
        return MeetingRequest(
            title="Test Meeting",
            duration_minutes=30,
            attendees=["user1@example.com", "user2@example.com"],
        )

    @pytest.mark.asyncio
    async def test_find_available_slots(
        self, agent: MeetingSchedulingAgent, sample_request: MeetingRequest
    ) -> None:
        """Test finding available time slots."""
        slots = await agent.find_available_slots(sample_request, [])
        assert isinstance(slots, list)
        assert all(isinstance(s, TimeSlot) for s in slots)

    @pytest.mark.asyncio
    async def test_schedule_meeting(
        self, agent: MeetingSchedulingAgent, sample_request: MeetingRequest
    ) -> None:
        """Test meeting scheduling."""
        meeting = await agent.schedule_meeting(sample_request)
        assert isinstance(meeting, ScheduledMeeting)
        assert meeting.title == "Test Meeting"
        assert meeting.status == "scheduled"
        assert len(meeting.attendees) == 2

    @pytest.mark.asyncio
    async def test_schedule_meeting_no_slots(
        self, agent: MeetingSchedulingAgent
    ) -> None:
        """Test scheduling when no slots available."""
        request = MeetingRequest(
            title="Test",
            duration_minutes=30,
            attendees=["user@example.com"],
        )
        # Create meetings that block all slots
        existing = [
            ScheduledMeeting(
                meeting_id=f"mtg_{i}",
                title=f"Meeting {i}",
                start_time=meeting.start_time,
                end_time=meeting.end_time,
                attendees=["other@example.com"],
                timezone="UTC",
            )
            for i in range(100)
        ]
        with pytest.raises(ValueError, match="No available time slots"):
            await agent.schedule_meeting(request, existing)

    @pytest.mark.asyncio
    async def test_cancel_meeting(
        self, agent: MeetingSchedulingAgent, sample_request: MeetingRequest
    ) -> None:
        """Test meeting cancellation."""
        meeting = await agent.schedule_meeting(sample_request)
        cancelled = await agent.cancel_meeting(meeting)
        assert cancelled.status == "cancelled"


# Follow-up Automation Agent Tests


class TestFollowUpAutomationAgent:
    """Tests for FollowUpAutomationAgent."""

    @pytest.fixture
    def agent(self) -> FollowUpAutomationAgent:
        """Create a follow-up automation agent."""
        return FollowUpAutomationAgent()

    @pytest.mark.asyncio
    async def test_create_sequence(
        self, agent: FollowUpAutomationAgent
    ) -> None:
        """Test follow-up sequence creation."""
        actions = await agent.create_sequence(
            name="Test Sequence",
            trigger_event="deal_created",
            contact_email="test@example.com",
        )
        assert len(actions) > 0
        assert all(isinstance(a, FollowUpAction) for a in actions)
        assert all(a.status == FollowUpStatus.SCHEDULED for a in actions)

    @pytest.mark.asyncio
    async def test_create_sequence_invalid(
        self, agent: FollowUpAutomationAgent
    ) -> None:
        """Test sequence creation with invalid data."""
        with pytest.raises(ValueError, match="Sequence name is required"):
            await agent.create_sequence(
                name="",
                trigger_event="test",
                contact_email="test@example.com",
            )

    @pytest.mark.asyncio
    async def test_send_follow_up(
        self, agent: FollowUpAutomationAgent
    ) -> None:
        """Test sending a follow-up."""
        actions = await agent.create_sequence(
            name="Test",
            trigger_event="test",
            contact_email="test@example.com",
        )
        action = actions[0]
        sent = await agent.send_follow_up(action)
        assert sent.status == FollowUpStatus.SENT
        assert sent.sent_at is not None

    @pytest.mark.asyncio
    async def test_send_follow_up_invalid_status(
        self, agent: FollowUpAutomationAgent
    ) -> None:
        """Test sending a follow-up that's not scheduled."""
        actions = await agent.create_sequence(
            name="Test",
            trigger_event="test",
            contact_email="test@example.com",
        )
        action = actions[0]
        await agent.send_follow_up(action)
        with pytest.raises(ValueError, match="Cannot send"):
            await agent.send_follow_up(action)

    @pytest.mark.asyncio
    async def test_get_sequence_metrics(
        self, agent: FollowUpAutomationAgent
    ) -> None:
        """Test sequence metrics calculation."""
        actions = await agent.create_sequence(
            name="Test",
            trigger_event="test",
            contact_email="test@example.com",
        )
        metrics = await agent.get_sequence_metrics(actions)
        assert metrics["total"] == len(actions)
        assert "open_rate" in metrics
        assert "reply_rate" in metrics


# Performance Analytics Agent Tests


class TestPerformanceAnalyticsAgent:
    """Tests for PerformanceAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        """Create a performance analytics agent."""
        return PerformanceAnalyticsAgent()

    @pytest.mark.asyncio
    async def test_calculate_sales_metrics(
        self, agent: PerformanceAnalyticsAgent
    ) -> None:
        """Test sales metrics calculation."""
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        deals = [
            {"status": "closed_won", "value": 50000, "created_date": (now - timedelta(days=30)).isoformat(), "closed_date": now.isoformat()},
            {"status": "closed_won", "value": 30000, "created_date": (now - timedelta(days=20)).isoformat(), "closed_date": now.isoformat()},
            {"status": "closed_lost", "value": 20000},
            {"status": "open", "value": 40000},
        ]
        metrics = await agent.calculate_sales_metrics(
            period_start=now - timedelta(days=60),
            period_end=now,
            deals=deals,
        )
        assert isinstance(metrics, SalesMetrics)
        assert metrics.total_revenue == 80000
        assert metrics.deals_won == 2
        assert metrics.deals_lost == 1
        assert metrics.win_rate == 0.67  # 2/3 closed deals

    @pytest.mark.asyncio
    async def test_calculate_agent_effectiveness(
        self, agent: PerformanceAnalyticsAgent
    ) -> None:
        """Test agent effectiveness calculation."""
        actions = [
            {"status": "success", "processing_time_seconds": 1.5, "user_satisfaction": 4.5},
            {"status": "success", "processing_time_seconds": 2.0, "user_satisfaction": 5.0},
            {"status": "failed", "processing_time_seconds": 3.0},
        ]
        effectiveness = await agent.calculate_agent_effectiveness("test_agent", actions)
        assert isinstance(effectiveness, AgentEffectiveness)
        assert effectiveness.actions_taken == 3
        assert effectiveness.success_rate == 0.67  # 2/3

    @pytest.mark.asyncio
    async def test_generate_weekly_report(
        self, agent: PerformanceAnalyticsAgent
    ) -> None:
        """Test weekly report generation."""
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        sales_metrics = SalesMetrics(
            period_start=now - timedelta(days=7),
            period_end=now,
            total_revenue=100000,
            deals_won=5,
            deals_lost=2,
            win_rate=0.71,
        )
        agent_metrics = [
            AgentEffectiveness(
                agent_name="test_agent",
                actions_taken=100,
                success_rate=0.95,
            )
        ]
        report = await agent.generate_weekly_report(sales_metrics, agent_metrics)
        assert report["report_type"] == "weekly"
        assert "summary" in report
        assert "agent_performance" in report
        assert "insights" in report

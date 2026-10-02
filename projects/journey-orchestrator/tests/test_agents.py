"""Tests for agent implementations."""

from __future__ import annotations

import pytest

from journey_orchestrator.agents.journey_designer import JourneyDesigner, JourneyDesignRequest
from journey_orchestrator.agents.personalization import PersonalizationEngine, PersonalizationRequest, CustomerProfile
from journey_orchestrator.agents.timing_optimizer import TimingOptimizer, TimingRequest
from journey_orchestrator.agents.experimentation import ExperimentationAgent, ExperimentRequest
from journey_orchestrator.agents.critic import CriticAgent, CriticRequest
from journey_orchestrator.agents.cross_channel import CrossChannelCoordinator, ChannelExecutionRequest


class TestJourneyDesigner:
    """Tests for the Journey Designer agent."""

    @pytest.fixture
    def designer(self) -> JourneyDesigner:
        return JourneyDesigner()

    @pytest.mark.asyncio
    async def test_design_journey_success(self, designer: JourneyDesigner) -> None:
        request = JourneyDesignRequest(
            business_goal="Increase retention",
            target_audience="New users",
            channels=["email", "push"],
        )
        blueprint = await designer.design(request)
        assert blueprint.name is not None
        assert len(blueprint.steps) > 0
        assert blueprint.estimated_duration_days > 0

    @pytest.mark.asyncio
    async def test_design_journey_empty_goal_raises(self, designer: JourneyDesigner) -> None:
        request = JourneyDesignRequest(
            business_goal="",
            target_audience="Users",
        )
        with pytest.raises(ValueError, match="business_goal"):
            await designer.design(request)

    @pytest.mark.asyncio
    async def test_design_journey_empty_audience_raises(self, designer: JourneyDesigner) -> None:
        request = JourneyDesignRequest(
            business_goal="Test goal",
            target_audience="",
        )
        with pytest.raises(ValueError, match="target_audience"):
            await designer.design(request)


class TestPersonalizationEngine:
    """Tests for the Personalization Engine agent."""

    @pytest.fixture
    def engine(self) -> PersonalizationEngine:
        return PersonalizationEngine()

    @pytest.mark.asyncio
    async def test_personalize_success(self, engine: PersonalizationEngine) -> None:
        request = PersonalizationRequest(
            customer=CustomerProfile(customer_id="cust_123", first_name="Alice"),
            content_type="email",
        )
        content = await engine.personalize(request)
        assert content.subject is not None
        assert content.body is not None
        assert 0.0 <= content.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_personalize_empty_customer_id_raises(self, engine: PersonalizationEngine) -> None:
        request = PersonalizationRequest(
            customer=CustomerProfile(customer_id=""),
            content_type="email",
        )
        with pytest.raises(ValueError, match="customer_id"):
            await engine.personalize(request)


class TestTimingOptimizer:
    """Tests for the Timing Optimizer agent."""

    @pytest.fixture
    def optimizer(self) -> TimingOptimizer:
        return TimingOptimizer()

    @pytest.mark.asyncio
    async def test_optimize_success(self, optimizer: TimingOptimizer) -> None:
        request = TimingRequest(
            customer_id="cust_123",
            channel="email",
            customer_timezone="America/New_York",
        )
        result = await optimizer.optimize(request)
        assert result.optimal_send_time is not None
        assert result.timezone == "America/New_York"
        assert 0.0 <= result.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_optimize_invalid_window_raises(self, optimizer: TimingOptimizer) -> None:
        request = TimingRequest(
            customer_id="cust_123",
            channel="email",
            preferred_window_start=25,
        )
        with pytest.raises(ValueError, match="preferred_window_start"):
            await optimizer.optimize(request)


class TestExperimentationAgent:
    """Tests for the Experimentation agent."""

    @pytest.fixture
    def agent(self) -> ExperimentationAgent:
        return ExperimentationAgent()

    @pytest.mark.asyncio
    async def test_design_experiment_success(self, agent: ExperimentationAgent) -> None:
        request = ExperimentRequest(
            journey_id="journey_123",
            hypothesis="Variant B will increase conversion",
            variants=["A", "B"],
            success_metric="conversion_rate",
        )
        design = await agent.design_experiment(request)
        assert design.experiment_id is not None
        assert len(design.variants) == 2
        assert design.status == "draft"

    @pytest.mark.asyncio
    async def test_design_experiment_single_variant_raises(self, agent: ExperimentationAgent) -> None:
        request = ExperimentRequest(
            journey_id="journey_123",
            hypothesis="Test",
            variants=["A"],
            success_metric="conversion_rate",
        )
        with pytest.raises(ValueError, match="At least 2 variants"):
            await agent.design_experiment(request)


class TestCriticAgent:
    """Tests for the Critic agent."""

    @pytest.fixture
    def agent(self) -> CriticAgent:
        return CriticAgent()

    @pytest.mark.asyncio
    async def test_review_approves_valid_journey(self, agent: CriticAgent) -> None:
        request = CriticRequest(
            journey_blueprint={
                "steps": [
                    {"step_number": 1, "channel": "email", "action": "send", "exit_conditions": ["unsubscribed"]},
                ]
            },
            compliance_requirements=["gdpr"],
        )
        review = await agent.review(request)
        assert review.approved is True
        assert review.overall_score > 0.0

    @pytest.mark.asyncio
    async def test_review_rejects_empty_journey(self, agent: CriticAgent) -> None:
        request = CriticRequest(
            journey_blueprint={"steps": []},
        )
        review = await agent.review(request)
        assert review.approved is False
        assert any(f.severity == "error" for f in review.findings)

    @pytest.mark.asyncio
    async def test_review_detects_gdpr_violation(self, agent: CriticAgent) -> None:
        request = CriticRequest(
            journey_blueprint={
                "steps": [
                    {"step_number": 1, "channel": "email", "action": "send", "exit_conditions": []},
                ]
            },
            compliance_requirements=["gdpr"],
        )
        review = await agent.review(request)
        assert review.approved is False
        assert any(f.category == "compliance" for f in review.findings)


class TestCrossChannelCoordinator:
    """Tests for the Cross-Channel Coordinator agent."""

    @pytest.fixture
    def coordinator(self) -> CrossChannelCoordinator:
        return CrossChannelCoordinator()

    @pytest.mark.asyncio
    async def test_execute_success(self, coordinator: CrossChannelCoordinator) -> None:
        request = ChannelExecutionRequest(
            journey_id="journey_123",
            customer_id="cust_456",
            steps=[
                {"channel": "email", "action": "send"},
                {"channel": "push", "action": "notify"},
            ],
        )
        result = await coordinator.execute(request)
        assert result.overall_success is True
        assert len(result.completed_channels) == 2

    @pytest.mark.asyncio
    async def test_execute_empty_journey_id_raises(self, coordinator: CrossChannelCoordinator) -> None:
        request = ChannelExecutionRequest(
            journey_id="",
            customer_id="cust_456",
            steps=[],
        )
        with pytest.raises(ValueError, match="journey_id"):
            await coordinator.execute(request)

"""Tests for lead routing agent and API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from lead_scorer.agents.lead_routing import LeadRoutingAgent, RoutingContext
from lead_scorer.agents.scoring import LeadGrade, ScoringResult
from lead_scorer.agents.qualification import (
    QualificationResult,
    QualificationStatus,
    QualificationFramework,
)
from lead_scorer.models.routing import (
    BatchRoutingRequest,
    RouteDestination,
    RoutingConfig,
    RoutingDecision,
    RoutingPriority,
    RoutingRule,
    RoutingRuleCreate,
    RoutingRuleUpdate,
    RoutingStrategy,
)
from lead_scorer.main import create_app


@pytest.fixture
def routing_agent() -> LeadRoutingAgent:
    """Create a routing agent for testing."""
    return LeadRoutingAgent(timeout_seconds=10, max_retries=1)


@pytest.fixture
def routing_agent_with_rules() -> LeadRoutingAgent:
    """Create a routing agent with pre-configured rules."""
    agent = LeadRoutingAgent(timeout_seconds=10, max_retries=1)
    agent.add_rule(
        RoutingRule(
            id="rule-hot-sales",
            name="Hot leads to sales",
            destination=RouteDestination.SALES,
            priority=RoutingPriority.HIGH,
            score_threshold=80.0,
            grade_filter=["hot"],
            order=1,
        )
    )
    agent.add_rule(
        RoutingRule(
            id="rule-warm-nurture",
            name="Warm leads to nurture",
            destination=RouteDestination.NURTURE,
            priority=RoutingPriority.MEDIUM,
            score_threshold=50.0,
            grade_filter=["warm"],
            order=2,
        )
    )
    agent.add_rule(
        RoutingRule(
            id="rule-cold-marketing",
            name="Cold leads to marketing",
            destination=RouteDestination.MARKETING,
            priority=RoutingPriority.LOW,
            grade_filter=["cold"],
            order=3,
        )
    )
    return agent


@pytest.fixture
def sample_context() -> RoutingContext:
    """Create a sample routing context."""
    return RoutingContext(
        lead_id="lead-123",
        score=85.0,
        grade="hot",
        qualification_status="qualified",
        qualification_score=0.85,
        industry="Technology",
        company_size=200,
        annual_revenue=5000000.0,
        source="website",
        job_title="CTO",
    )


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = create_app()
    return TestClient(app)


class TestRoutingContext:
    """Tests for RoutingContext model."""

    def test_create_context(self) -> None:
        """Test creating a routing context."""
        ctx = RoutingContext(lead_id="lead-1", score=75.0, grade="warm")
        assert ctx.lead_id == "lead-1"
        assert ctx.score == 75.0
        assert ctx.grade == "warm"

    def test_context_defaults(self) -> None:
        """Test context default values."""
        ctx = RoutingContext(lead_id="lead-1")
        assert ctx.score == 0.0
        assert ctx.grade == ""
        assert ctx.company_size == 0


class TestRoutingRule:
    """Tests for RoutingRule model."""

    def test_create_rule(self) -> None:
        """Test creating a routing rule."""
        rule = RoutingRule(
            id="rule-1",
            name="Test Rule",
            destination=RouteDestination.SALES,
            priority=RoutingPriority.HIGH,
            score_threshold=75.0,
        )
        assert rule.id == "rule-1"
        assert rule.destination == RouteDestination.SALES
        assert rule.is_active is True

    def test_rule_with_filters(self) -> None:
        """Test rule with industry and grade filters."""
        rule = RoutingRule(
            id="rule-2",
            name="Tech hot leads",
            destination=RouteDestination.SALES,
            grade_filter=["hot"],
            industry_filter=["Technology", "Software"],
            company_size_min=50,
            company_size_max=500,
        )
        assert "hot" in rule.grade_filter
        assert "Technology" in rule.industry_filter
        assert rule.company_size_min == 50
        assert rule.company_size_max == 500


class TestLeadRoutingAgent:
    """Tests for LeadRoutingAgent."""

    @pytest.mark.asyncio
    async def test_route_hot_lead(
        self, routing_agent_with_rules: LeadRoutingAgent, sample_context: RoutingContext
    ) -> None:
        """Test routing a hot lead to sales."""
        decision = await routing_agent_with_rules.route(sample_context)
        assert isinstance(decision, RoutingDecision)
        assert decision.destination == RouteDestination.SALES
        assert decision.priority == RoutingPriority.HIGH
        assert decision.confidence > 0.0
        assert decision.rule_id == "rule-hot-sales"

    @pytest.mark.asyncio
    async def test_route_warm_lead(
        self, routing_agent_with_rules: LeadRoutingAgent
    ) -> None:
        """Test routing a warm lead to nurture."""
        ctx = RoutingContext(
            lead_id="lead-warm",
            score=60.0,
            grade="warm",
            qualification_status="pending",
        )
        decision = await routing_agent_with_rules.route(ctx)
        assert decision.destination == RouteDestination.NURTURE
        assert decision.priority == RoutingPriority.MEDIUM

    @pytest.mark.asyncio
    async def test_route_cold_lead(
        self, routing_agent_with_rules: LeadRoutingAgent
    ) -> None:
        """Test routing a cold lead to marketing."""
        ctx = RoutingContext(
            lead_id="lead-cold",
            score=20.0,
            grade="cold",
        )
        decision = await routing_agent_with_rules.route(ctx)
        assert decision.destination == RouteDestination.MARKETING
        assert decision.priority == RoutingPriority.LOW

    @pytest.mark.asyncio
    async def test_route_no_matching_rule(
        self, routing_agent: LeadRoutingAgent
    ) -> None:
        """Test routing when no rules match — uses default."""
        ctx = RoutingContext(lead_id="lead-default", score=50.0, grade="warm")
        decision = await routing_agent.route(ctx)
        assert decision.destination == RouteDestination.NURTURE
        assert decision.rule_name == "default"
        assert decision.confidence == 0.5

    @pytest.mark.asyncio
    async def test_route_with_scoring_result(
        self, routing_agent_with_rules: LeadRoutingAgent
    ) -> None:
        """Test routing with a ScoringResult."""
        scoring = ScoringResult(
            lead_id="lead-scored",
            total_score=90.0,
            grade=LeadGrade.HOT,
            components=[],
            confidence=0.9,
        )
        ctx = RoutingContext(lead_id="lead-scored")
        decision = await routing_agent_with_rules.route(ctx, scoring_result=scoring)
        assert decision.destination == RouteDestination.SALES
        assert decision.confidence > 0.5

    @pytest.mark.asyncio
    async def test_route_with_qualification_result(
        self, routing_agent_with_rules: LeadRoutingAgent
    ) -> None:
        """Test routing with a QualificationResult."""
        qual = QualificationResult(
            lead_id="lead-qual",
            framework=QualificationFramework.MEDDIC,
            status=QualificationStatus.QUALIFIED,
            total_score=0.85,
            criteria=[],
        )
        ctx = RoutingContext(
            lead_id="lead-qual",
            score=70.0,
            grade="warm",
        )
        decision = await routing_agent_with_rules.route(
            ctx, qualification_result=qual
        )
        assert decision.confidence > 0.5

    @pytest.mark.asyncio
    async def test_route_invalid_lead_id(
        self, routing_agent: LeadRoutingAgent
    ) -> None:
        """Test that routing raises on empty lead_id."""
        ctx = RoutingContext(lead_id="")
        with pytest.raises(ValueError):
            await routing_agent.route(ctx)

    @pytest.mark.asyncio
    async def test_batch_route(self, routing_agent_with_rules: LeadRoutingAgent) -> None:
        """Test batch routing."""
        request = BatchRoutingRequest(
            lead_ids=["lead-1", "lead-2", "lead-3"],
            context={"source": "api"},
        )
        contexts = {
            "lead-1": RoutingContext(lead_id="lead-1", score=90.0, grade="hot"),
            "lead-2": RoutingContext(lead_id="lead-2", score=60.0, grade="warm"),
            "lead-3": RoutingContext(lead_id="lead-3", score=20.0, grade="cold"),
        }
        response = await routing_agent_with_rules.route_batch(request, contexts)
        assert response.success is True
        assert response.total == 3
        assert len(response.results) == 3
        assert response.results[0].destination == RouteDestination.SALES
        assert response.results[1].destination == RouteDestination.NURTURE
        assert response.results[2].destination == RouteDestination.MARKETING

    @pytest.mark.asyncio
    async def test_batch_route_empty_list(
        self, routing_agent: LeadRoutingAgent
    ) -> None:
        """Test batch routing with empty list raises error."""
        request = BatchRoutingRequest(lead_ids=[])
        with pytest.raises(ValueError):
            await routing_agent.route_batch(request)

    def test_add_rule(self, routing_agent: LeadRoutingAgent) -> None:
        """Test adding a routing rule."""
        rule = RoutingRule(
            id="rule-new",
            name="New Rule",
            destination=RouteDestination.SALES,
        )
        routing_agent.add_rule(rule)
        assert len(routing_agent.rules) == 1
        assert routing_agent.rules[0].id == "rule-new"

    def test_remove_rule(self, routing_agent: LeadRoutingAgent) -> None:
        """Test removing a routing rule."""
        rule = RoutingRule(
            id="rule-remove",
            name="Remove Me",
            destination=RouteDestination.SALES,
        )
        routing_agent.add_rule(rule)
        assert routing_agent.remove_rule("rule-remove") is True
        assert len(routing_agent.rules) == 0

    def test_remove_nonexistent_rule(self, routing_agent: LeadRoutingAgent) -> None:
        """Test removing a rule that doesn't exist."""
        assert routing_agent.remove_rule("nonexistent") is False

    def test_update_rule(self, routing_agent: LeadRoutingAgent) -> None:
        """Test updating a routing rule."""
        rule = RoutingRule(
            id="rule-update",
            name="Original",
            destination=RouteDestination.SALES,
        )
        routing_agent.add_rule(rule)
        update = RoutingRuleUpdate(name="Updated", priority=RoutingPriority.LOW)
        updated = routing_agent.update_rule("rule-update", update)
        assert updated is not None
        assert updated.name == "Updated"
        assert updated.priority == RoutingPriority.LOW

    def test_update_nonexistent_rule(self, routing_agent: LeadRoutingAgent) -> None:
        """Test updating a rule that doesn't exist."""
        update = RoutingRuleUpdate(name="Updated")
        assert routing_agent.update_rule("nonexistent", update) is None

    def test_get_assignment_stats(self, routing_agent: LeadRoutingAgent) -> None:
        """Test getting assignment statistics."""
        stats = routing_agent.get_assignment_stats()
        assert isinstance(stats, dict)

    def test_reset_assignment_counters(self, routing_agent: LeadRoutingAgent) -> None:
        """Test resetting assignment counters."""
        routing_agent._assignment_counters["sales"] = 5
        routing_agent.reset_assignment_counters()
        assert len(routing_agent._assignment_counters) == 0


class TestRoutingAPI:
    """Tests for routing API endpoints."""

    def test_route_lead(self, client: TestClient) -> None:
        """Test routing a lead via API."""
        response = client.post(
            "/api/v1/routing/route",
            json={
                "lead_id": "lead-api-1",
                "score": 85.0,
                "grade": "hot",
                "industry": "Technology",
                "company_size": 200,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["lead_id"] == "lead-api-1"
        assert data["data"]["destination"] in [d.value for d in RouteDestination]

    def test_route_lead_invalid(self, client: TestClient) -> None:
        """Test routing with invalid data."""
        response = client.post(
            "/api/v1/routing/route",
            json={"lead_id": ""},
        )
        assert response.status_code == 400

    def test_batch_route_api(self, client: TestClient) -> None:
        """Test batch routing via API."""
        response = client.post(
            "/api/v1/routing/batch",
            json={
                "lead_ids": ["lead-1", "lead-2"],
                "context": {"source": "api"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2
        assert len(data["results"]) == 2

    def test_list_routing_rules(self, client: TestClient) -> None:
        """Test listing routing rules."""
        response = client.get("/api/v1/routing/rules")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["rules"], list)

    def test_create_routing_rule(self, client: TestClient) -> None:
        """Test creating a routing rule via API."""
        response = client.post(
            "/api/v1/routing/rules",
            json={
                "name": "API Test Rule",
                "destination": "sales",
                "priority": "high",
                "score_threshold": 80.0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Rule"
        assert data["destination"] == "sales"

    def test_get_routing_stats(self, client: TestClient) -> None:
        """Test getting routing statistics."""
        response = client.get("/api/v1/routing/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["stats"], dict)

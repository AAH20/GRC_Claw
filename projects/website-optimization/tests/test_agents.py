"""Tests for Website Optimization agents."""

from __future__ import annotations

import pytest

from website_optimization.agents.ab_testing import ABTestingAgent, Variant
from website_optimization.agents.personalization import (
    PersonalizationAgent,
    PersonalizationRule,
    UserProfile,
)
from website_optimization.agents.seo import SEOAgent


class TestABTestingAgent:
    """Tests for ABTestingAgent."""

    @pytest.fixture
    def agent(self) -> ABTestingAgent:
        return ABTestingAgent()

    def test_create_experiment(self, agent: ABTestingAgent) -> None:
        experiment = agent.create_experiment(
            name="Test Experiment",
            page_url="/test",
            variants=[Variant(name="A"), Variant(name="B")],
        )
        assert experiment is not None
        assert experiment.name == "Test Experiment"

    def test_get_experiment(self, agent: ABTestingAgent) -> None:
        created = agent.create_experiment(
            name="Test",
            page_url="/test",
            variants=[Variant(name="A"), Variant(name="B")],
        )
        fetched = agent.get_experiment(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    def test_start_experiment(self, agent: ABTestingAgent) -> None:
        created = agent.create_experiment(
            name="Test",
            page_url="/test",
            variants=[Variant(name="A"), Variant(name="B")],
        )
        started = agent.start_experiment(created.id)
        assert started.status == "running"

    def test_pause_experiment(self, agent: ABTestingAgent) -> None:
        created = agent.create_experiment(
            name="Test",
            page_url="/test",
            variants=[Variant(name="A"), Variant(name="B")],
        )
        agent.start_experiment(created.id)
        paused = agent.pause_experiment(created.id)
        assert paused.status == "paused"

    def test_complete_experiment(self, agent: ABTestingAgent) -> None:
        created = agent.create_experiment(
            name="Test",
            page_url="/test",
            variants=[Variant(name="A"), Variant(name="B")],
        )
        agent.start_experiment(created.id)
        completed = agent.complete_experiment(created.id)
        assert completed.status == "completed"

    def test_assign_variant(self, agent: ABTestingAgent) -> None:
        created = agent.create_experiment(
            name="Test",
            page_url="/test",
            variants=[Variant(name="A"), Variant(name="B")],
        )
        agent.start_experiment(created.id)
        variant = agent.assign_variant(created.id, "user-123")
        assert variant is not None

    def test_list_experiments(self, agent: ABTestingAgent) -> None:
        agent.create_experiment(
            name="Exp1",
            page_url="/test1",
            variants=[Variant(name="A"), Variant(name="B")],
        )
        agent.create_experiment(
            name="Exp2",
            page_url="/test2",
            variants=[Variant(name="A"), Variant(name="B")],
        )
        experiments = agent.list_experiments()
        assert len(experiments) == 2


class TestPersonalizationAgent:
    """Tests for PersonalizationAgent."""

    @pytest.fixture
    def agent(self) -> PersonalizationAgent:
        return PersonalizationAgent()

    def test_add_rule(self, agent: PersonalizationAgent) -> None:
        rule = PersonalizationRule(
            id="rule-1",
            name="US Users",
            conditions={"country": "US"},
            content={"message": "Welcome US user!"},
        )
        agent.add_rule(rule)
        assert "rule-1" in agent._rules

    def test_remove_rule(self, agent: PersonalizationAgent) -> None:
        rule = PersonalizationRule(
            id="rule-1",
            name="US Users",
            conditions={"country": "US"},
            content={"message": "Welcome US user!"},
        )
        agent.add_rule(rule)
        removed = agent.remove_rule("rule-1")
        assert removed is True
        assert "rule-1" not in agent._rules

    def test_update_user_profile(self, agent: PersonalizationAgent) -> None:
        profile = UserProfile(
            user_id="user-123",
            segments=["tech", "AI"],
            preferences={"theme": "dark"},
        )
        agent.update_user_profile(profile)
        fetched = agent.get_user_profile("user-123")
        assert fetched is not None
        assert fetched.user_id == "user-123"

    def test_get_recommendations(self, agent: PersonalizationAgent) -> None:
        recs = agent.get_recommendations(page_url="/test", user_id="user-123")
        assert isinstance(recs, list)


class TestSEOAgent:
    """Tests for SEOAgent."""

    @pytest.fixture
    def agent(self) -> SEOAgent:
        return SEOAgent()

    def test_audit_page(self, agent: SEOAgent) -> None:
        html = "<html><head><title>Test Page</title></head><body>Content</body></html>"
        result = agent.audit_page("https://example.com", html_content=html)
        assert result is not None
        assert result.url == "https://example.com"

    def test_get_optimization_suggestions(self, agent: SEOAgent) -> None:
        html = "<html><head><title>Test Page</title></head><body>Content</body></html>"
        result = agent.audit_page("https://example.com", html_content=html)
        suggestions = agent.get_optimization_suggestions(result)
        assert isinstance(suggestions, list)

"""Tests for ABM agent implementations."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from abm.agents.account_identification import (
    AccountIdentificationAgent,
    AccountScore,
)
from abm.agents.intent_scoring import (
    IntentScoringAgent,
    IntentSignalType,
)
from abm.agents.performance_analytics import (
    AttributionModel,
    PerformanceAnalyticsAgent,
)


class TestAccountIdentificationAgent:
    """Tests for AccountIdentificationAgent."""

    @pytest.fixture
    def agent(self) -> AccountIdentificationAgent:
        return AccountIdentificationAgent()

    async def test_initialize(self, agent: AccountIdentificationAgent) -> None:
        assert agent._initialized is True

    async def test_identify_accounts(self, agent: AccountIdentificationAgent) -> None:
        criteria = {"industry": "Technology", "company_size": "500-1000"}
        accounts = await agent.identify_accounts(criteria)
        assert len(accounts) > 0
        assert all(isinstance(a, AccountScore) for a in accounts)

    async def test_identify_accounts_empty_criteria(
        self, agent: AccountIdentificationAgent
    ) -> None:
        with pytest.raises(ValueError, match="ICP criteria cannot be empty"):
            await agent.identify_accounts({})

    async def test_identify_accounts_excludes_existing(
        self, agent: AccountIdentificationAgent
    ) -> None:
        criteria = {"industry": "Technology"}
        accounts = await agent.identify_accounts(
            criteria, existing_account_ids=["acc_001"]
        )
        assert all(a.account_id != "acc_001" for a in accounts)

    async def test_enrich_account(self, agent: AccountIdentificationAgent) -> None:
        data = await agent.enrich_account("acc_001")
        assert data["account_id"] == "acc_001"
        assert "industry" in data
        assert "technologies" in data

    async def test_enrich_account_empty_id(
        self, agent: AccountIdentificationAgent
    ) -> None:
        with pytest.raises(ValueError, match="account_id cannot be empty"):
            await agent.enrich_account("")


class TestIntentScoringAgent:
    """Tests for IntentScoringAgent."""

    @pytest.fixture
    def agent(self) -> IntentScoringAgent:
        return IntentScoringAgent()

    async def test_score_account(self, agent: IntentScoringAgent) -> None:
        score = await agent.score_account("acc_001")
        assert score.account_id == "acc_001"
        assert score.total_score >= 0
        assert 0 <= score.normalized_score <= 1.0
        assert len(score.signals) > 0

    async def test_score_account_empty_id(self, agent: IntentScoringAgent) -> None:
        with pytest.raises(ValueError, match="account_id cannot be empty"):
            await agent.score_account("")

    async def test_rank_accounts(self, agent: IntentScoringAgent) -> None:
        scores = await agent.rank_accounts(["acc_001", "acc_002"])
        assert len(scores) == 2
        assert scores[0].total_score >= scores[1].total_score

    async def test_rank_accounts_empty(self, agent: IntentScoringAgent) -> None:
        with pytest.raises(ValueError, match="account_ids cannot be empty"):
            await agent.rank_accounts([])


class TestPerformanceAnalyticsAgent:
    """Tests for PerformanceAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        return PerformanceAnalyticsAgent()

    async def test_get_campaign_metrics(
        self, agent: PerformanceAnalyticsAgent
    ) -> None:
        metrics = await agent.get_campaign_metrics("camp_001")
        assert metrics.campaign_id == "camp_001"
        assert metrics.impressions > 0
        assert metrics.clicks > 0

    async def test_get_campaign_metrics_empty_id(
        self, agent: PerformanceAnalyticsAgent
    ) -> None:
        with pytest.raises(ValueError, match="campaign_id cannot be empty"):
            await agent.get_campaign_metrics("")

    async def test_get_account_engagement(
        self, agent: PerformanceAnalyticsAgent
    ) -> None:
        engagement = await agent.get_account_engagement("camp_001")
        assert len(engagement) > 0

    async def test_compute_attribution(
        self, agent: PerformanceAnalyticsAgent
    ) -> None:
        result = await agent.compute_attribution("camp_001")
        assert result["campaign_id"] == "camp_001"
        assert "channel_attribution" in result

    async def test_generate_report(self, agent: PerformanceAnalyticsAgent) -> None:
        report = await agent.generate_report("camp_001")
        assert report["campaign_id"] == "camp_001"
        assert "summary" in report
        assert "attribution" in report

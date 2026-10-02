"""Tests for Market Research agents."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from market_research.agents.action import ActionAgent
from market_research.agents.analysis import AnalysisAgent
from market_research.agents.data_collection import DataCollectionAgent
from market_research.agents.performance_analytics import PerformanceAnalyticsAgent
from market_research.agents.reporting import ReportingAgent


class TestAnalysisAgent:
    """Tests for AnalysisAgent."""

    @pytest.fixture
    def agent(self) -> AnalysisAgent:
        return AnalysisAgent(config={})

    @pytest.mark.asyncio
    async def test_analyze(self, agent: AnalysisAgent) -> None:
        request = MagicMock()
        request.market = "AI"
        request.product = "Chatbot"
        result = await agent.analyze(request)
        assert result is not None


class TestDataCollectionAgent:
    """Tests for DataCollectionAgent."""

    @pytest.fixture
    def agent(self) -> DataCollectionAgent:
        return DataCollectionAgent(config={})

    @pytest.mark.asyncio
    async def test_collect(self, agent: DataCollectionAgent) -> None:
        request = MagicMock()
        request.market = "AI"
        result = await agent.collect(request)
        assert result is not None

    def test_get_source_status(self, agent: DataCollectionAgent) -> None:
        status = agent.get_source_status()
        assert isinstance(status, dict)


class TestActionAgent:
    """Tests for ActionAgent."""

    @pytest.fixture
    def agent(self) -> ActionAgent:
        return ActionAgent(config={})

    @pytest.mark.asyncio
    async def test_generate_action_plan(self, agent: ActionAgent) -> None:
        request = MagicMock()
        request.market = "AI"
        result = await agent.generate_action_plan(request)
        assert result is not None


class TestReportingAgent:
    """Tests for ReportingAgent."""

    @pytest.fixture
    def agent(self) -> ReportingAgent:
        return ReportingAgent(config={})

    @pytest.mark.asyncio
    async def test_generate_report(self, agent: ReportingAgent) -> None:
        request = MagicMock()
        request.market = "AI"
        result = await agent.generate_report(request)
        assert result is not None


class TestPerformanceAnalyticsAgent:
    """Tests for PerformanceAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        return PerformanceAnalyticsAgent(config={})

    @pytest.mark.asyncio
    async def test_analyze(self, agent: PerformanceAnalyticsAgent) -> None:
        request = MagicMock()
        request.market = "AI"
        result = await agent.analyze(request)
        assert result is not None

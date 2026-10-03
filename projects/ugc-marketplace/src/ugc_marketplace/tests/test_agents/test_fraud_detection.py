"""Tests for fraud detection agents."""

from __future__ import annotations

import pytest

from ugc_marketplace.agents.fraud_detection import (AccountAnalyzerAgent,
                                                    AnomalyDetectorAgent,
                                                    PatternDetectorAgent,
                                                    RiskScorerAgent,
                                                    TransactionMonitorAgent)


@pytest.mark.asyncio
async def test_anomaly_detector_agent() -> None:
    """Test anomaly detector agent."""
    agent = AnomalyDetectorAgent()
    status = agent.get_status()
    assert status["agent_name"] == "AnomalyDetectorAgent"


@pytest.mark.asyncio
async def test_pattern_detector_agent() -> None:
    """Test pattern detector agent."""
    agent = PatternDetectorAgent()
    status = agent.get_status()
    assert status["agent_name"] == "PatternDetectorAgent"


@pytest.mark.asyncio
async def test_risk_scorer_agent() -> None:
    """Test risk scorer agent."""
    agent = RiskScorerAgent()
    status = agent.get_status()
    assert status["agent_name"] == "RiskScorerAgent"


@pytest.mark.asyncio
async def test_account_analyzer_agent() -> None:
    """Test account analyzer agent."""
    agent = AccountAnalyzerAgent()
    status = agent.get_status()
    assert status["agent_name"] == "AccountAnalyzerAgent"


@pytest.mark.asyncio
async def test_transaction_monitor_agent() -> None:
    """Test transaction monitor agent."""
    agent = TransactionMonitorAgent()
    status = agent.get_status()
    assert status["agent_name"] == "TransactionMonitorAgent"

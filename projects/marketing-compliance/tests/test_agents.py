"""Tests for compliance agent implementations."""
from __future__ import annotations

import pytest

from compliance.agents.analytics import AnalyticsAgent
from compliance.agents.base import AgentStatus, Severity
from compliance.agents.detect import DetectAgent
from compliance.agents.monitor import MonitorAgent
from compliance.agents.orchestrator import OrchestratorAgent
from compliance.agents.report import ReportAgent
from compliance.agents.respond import RespondAgent


class TestDetectAgent:
    """Tests for DetectAgent."""

    @pytest.fixture
    def agent(self) -> DetectAgent:
        return DetectAgent()

    async def test_detect_unsubscribe_missing(self, agent: DetectAgent) -> None:
        result = await agent.execute(
            {
                "items": [
                    {
                        "id": "content_1",
                        "source": "mailchimp",
                        "content": "Buy our product now!",
                        "channel": "email",
                    }
                ]
            }
        )
        assert result.status == AgentStatus.SUCCEEDED
        assert len(result.items) == 1
        assert result.items[0]["rule"] == "unsubscribe_missing"
        assert result.items[0]["severity"] == Severity.HIGH.value

    async def test_detect_guaranteed_claims(self, agent: DetectAgent) -> None:
        result = await agent.execute(
            {
                "items": [
                    {
                        "id": "content_2",
                        "source": "salesforce",
                        "content": "Our product is guaranteed to work!",
                        "channel": "email",
                    }
                ]
            }
        )
        assert result.status == AgentStatus.SUCCEEDED
        assert any(v["rule"] == "guaranteed_claims" for v in result.items)

    async def test_detect_pii_leak(self, agent: DetectAgent) -> None:
        result = await agent.execute(
            {
                "items": [
                    {
                        "id": "content_3",
                        "source": "hubspot",
                        "content": "SSN: 123-45-6789",
                        "channel": "email",
                    }
                ]
            }
        )
        assert result.status == AgentStatus.SUCCEEDED
        assert any(v["rule"] == "pii_leak" for v in result.items)

    async def test_detect_clean_content(self, agent: DetectAgent) -> None:
        result = await agent.execute(
            {
                "items": [
                    {
                        "id": "content_4",
                        "source": "mailchimp",
                        "content": "Check out our latest updates. Unsubscribe here.",
                        "channel": "email",
                    }
                ]
            }
        )
        assert result.status == AgentStatus.SUCCEEDED
        assert len(result.items) == 0

    async def test_detect_empty_items(self, agent: DetectAgent) -> None:
        result = await agent.execute({"items": []})
        assert result.status == AgentStatus.SUCCEEDED
        assert len(result.items) == 0


class TestMonitorAgent:
    """Tests for MonitorAgent."""

    @pytest.fixture
    def agent(self) -> MonitorAgent:
        return MonitorAgent()

    async def test_monitor_normalises_campaigns(self, agent: MonitorAgent) -> None:
        result = await agent.execute(
            {
                "campaigns": [
                    {
                        "id": "camp_1",
                        "source": "salesforce",
                        "content": "Test campaign content",
                        "channel": "email",
                    }
                ]
            }
        )
        assert result.status == AgentStatus.SUCCEEDED
        assert len(result.items) == 1
        assert result.items[0]["id"] == "camp_1"

    async def test_monitor_skips_invalid(self, agent: MonitorAgent) -> None:
        result = await agent.execute(
            {
                "campaigns": [
                    {"id": "", "content": "Missing source"},
                    {"id": "camp_2", "content": "Valid content", "source": "hubspot"},
                ]
            }
        )
        assert result.status == AgentStatus.SUCCEEDED
        assert len(result.items) == 1
        assert result.items[0]["id"] == "camp_2"


class TestRespondAgent:
    """Tests for RespondAgent."""

    @pytest.fixture
    def agent(self) -> RespondAgent:
        return RespondAgent()

    async def test_respond_generates_recommendations(self, agent: RespondAgent) -> None:
        result = await agent.execute(
            {
                "violations": [
                    {
                        "content_id": "content_1",
                        "rule": "unsubscribe_missing",
                        "severity": "high",
                    }
                ]
            }
        )
        assert result.status == AgentStatus.SUCCEEDED
        assert len(result.items) == 1
        assert result.items[0]["action"] == "escalate"

    async def test_respond_empty_violations(self, agent: RespondAgent) -> None:
        result = await agent.execute({"violations": []})
        assert result.status == AgentStatus.SUCCEEDED
        assert len(result.items) == 0


class TestAnalyticsAgent:
    """Tests for AnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> AnalyticsAgent:
        return AnalyticsAgent()

    async def test_analytics_computes_metrics(self, agent: AnalyticsAgent) -> None:
        result = await agent.execute(
            {
                "violations": [
                    {"severity": "critical", "rule": "pii_leak", "source": "hubspot"},
                    {"severity": "high", "rule": "unsubscribe_missing", "source": "mailchimp"},
                ]
            }
        )
        assert result.status == AgentStatus.SUCCEEDED
        assert result.metrics["total_violations"] == 2.0
        assert result.metrics["critical_violations"] == 1.0

    async def test_analytics_empty(self, agent: AnalyticsAgent) -> None:
        result = await agent.execute({"violations": []})
        assert result.status == AgentStatus.SUCCEEDED
        assert result.metrics["total_violations"] == 0.0


class TestReportAgent:
    """Tests for ReportAgent."""

    @pytest.fixture
    def agent(self) -> ReportAgent:
        return ReportAgent()

    async def test_report_generates(self, agent: ReportAgent) -> None:
        result = await agent.execute(
            {
                "violations": [
                    {"severity": "high", "rule": "unsubscribe_missing"}
                ],
                "responses": [
                    {"action": "escalate", "rule": "unsubscribe_missing"}
                ],
            }
        )
        assert result.status == AgentStatus.SUCCEEDED
        assert len(result.items) == 1
        report = result.items[0]
        assert "summary" in report
        assert report["summary"]["total_violations"] == 1

    async def test_report_to_json(self, agent: ReportAgent) -> None:
        report = {"test": "data"}
        json_str = agent.to_json(report)
        assert '"test": "data"' in json_str


class TestOrchestratorAgent:
    """Tests for OrchestratorAgent."""

    @pytest.fixture
    def agent(self) -> OrchestratorAgent:
        return OrchestratorAgent()

    async def test_orchestrator_full_pipeline(self, agent: OrchestratorAgent) -> None:
        result = await agent.execute(
            {
                "campaigns": [
                    {
                        "id": "camp_1",
                        "source": "mailchimp",
                        "content": "Buy now! Guaranteed results!",
                        "channel": "email",
                    }
                ]
            }
        )
        assert result.status == AgentStatus.SUCCEEDED
        assert "violations_detected" in result.metrics
        assert result.metrics["violations_detected"] > 0

"""Tests for customer service agents."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from customer_service.agents import (
    CustomerSuccessAgent,
    EscalationAgent,
    ResolutionAgent,
    SentimentAnalysisAgent,
    TriageAgent,
)


class TestTriageAgent:
    """Test cases for TriageAgent."""

    @pytest.fixture
    def agent(self) -> TriageAgent:
        """Create a TriageAgent instance."""
        return TriageAgent()

    @pytest.mark.asyncio
    async def test_run_with_valid_ticket(self, agent: TriageAgent) -> None:
        """Test triage with valid ticket content."""
        mock_response = (
            '{"category": "billing", "priority": "high", "confidence": 0.92, '
            '"intent": "refund_request", "summary": "Customer wants refund", '
            '"suggested_team": "billing_team"}'
        )
        with patch.object(agent, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await agent.run("I want a refund for my last order")

        assert result.category == "billing"
        assert result.priority == "high"
        assert result.confidence == pytest.approx(0.92)
        assert result.intent == "refund_request"

    @pytest.mark.asyncio
    async def test_run_with_empty_content_raises_error(self, agent: TriageAgent) -> None:
        """Test that empty ticket content raises ValueError."""
        with pytest.raises(ValueError, match="Ticket content cannot be empty"):
            await agent.run("")

    @pytest.mark.asyncio
    async def test_run_with_whitespace_content_raises_error(self, agent: TriageAgent) -> None:
        """Test that whitespace-only ticket content raises ValueError."""
        with pytest.raises(ValueError, match="Ticket content cannot be empty"):
            await agent.run("   ")

    @pytest.mark.asyncio
    async def test_run_with_customer_context(self, agent: TriageAgent) -> None:
        """Test triage with customer context provided."""
        mock_response = (
            '{"category": "technical", "priority": "medium", "confidence": 0.85, '
            '"intent": "bug_report", "summary": "App crashes on login", '
            '"suggested_team": "engineering"}'
        )
        with patch.object(agent, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await agent.run(
                "The app crashes when I try to log in",
                customer_context={"tier": "enterprise", "mrr": 5000},
            )

        assert result.category == "technical"
        assert result.suggested_team == "engineering"


class TestResolutionAgent:
    """Test cases for ResolutionAgent."""

    @pytest.fixture
    def agent(self) -> ResolutionAgent:
        """Create a ResolutionAgent instance."""
        return ResolutionAgent()

    @pytest.mark.asyncio
    async def test_run_with_valid_ticket(self, agent: ResolutionAgent) -> None:
        """Test resolution with valid ticket content."""
        mock_response = (
            '{"suggestion": "Reset password and send confirmation email", '
            '"confidence": 0.95, "auto_reply": null, '
            '"related_articles": ["article-123"], "escalation_recommended": false}'
        )
        with patch.object(agent, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await agent.run("I cannot log into my account")

        assert "Reset password" in result.suggestion
        assert result.confidence == pytest.approx(0.95)
        assert result.escalation_recommended is False

    @pytest.mark.asyncio
    async def test_run_with_empty_content_raises_error(self, agent: ResolutionAgent) -> None:
        """Test that empty ticket content raises ValueError."""
        with pytest.raises(ValueError, match="Ticket content cannot be empty"):
            await agent.run("")

    @pytest.mark.asyncio
    async def test_run_with_triage_result(self, agent: ResolutionAgent) -> None:
        """Test resolution with triage result context."""
        mock_response = (
            '{"suggestion": "Escalate to billing team", '
            '"confidence": 0.6, "auto_reply": null, '
            '"related_articles": [], "escalation_recommended": true}'
        )
        with patch.object(agent, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await agent.run(
                "I was charged twice for my subscription",
                triage_result={"category": "billing", "priority": "high"},
            )

        assert result.escalation_recommended is True


class TestEscalationAgent:
    """Test cases for EscalationAgent."""

    @pytest.fixture
    def agent(self) -> EscalationAgent:
        """Create an EscalationAgent instance."""
        return EscalationAgent()

    @pytest.mark.asyncio
    async def test_run_with_valid_ticket(self, agent: EscalationAgent) -> None:
        """Test escalation with valid ticket content."""
        mock_response = (
            '{"should_escalate": true, "reason": "Complex billing dispute", '
            '"urgency": "high", "assigned_team": "billing_specialists", '
            '"context_summary": "Customer has duplicate charges", '
            '"customer_impact": "Financial loss, trust erosion"}'
        )
        with patch.object(agent, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await agent.run("I was charged three times and nobody is helping")

        assert result.should_escalate is True
        assert result.urgency == "high"
        assert result.assigned_team == "billing_specialists"

    @pytest.mark.asyncio
    async def test_run_with_empty_content_raises_error(self, agent: EscalationAgent) -> None:
        """Test that empty ticket content raises ValueError."""
        with pytest.raises(ValueError, match="Ticket content cannot be empty"):
            await agent.run("")


class TestSentimentAnalysisAgent:
    """Test cases for SentimentAnalysisAgent."""

    @pytest.fixture
    def agent(self) -> SentimentAnalysisAgent:
        """Create a SentimentAnalysisAgent instance."""
        return SentimentAnalysisAgent()

    @pytest.mark.asyncio
    async def test_run_with_valid_text(self, agent: SentimentAnalysisAgent) -> None:
        """Test sentiment analysis with valid text."""
        mock_response = (
            '{"overall_sentiment": "negative", "sentiment_score": -0.7, '
            '"satisfaction_level": "dissatisfied", "frustration_level": "high", '
            '"key_phrases": ["terrible service", "very disappointed"], '
            '"urgency_indicators": ["immediately", "asap"], "churn_risk": "high"}'
        )
        with patch.object(agent, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await agent.run("This is terrible service and I am very disappointed")

        assert result.overall_sentiment == "negative"
        assert result.sentiment_score == pytest.approx(-0.7)
        assert result.churn_risk == "high"

    @pytest.mark.asyncio
    async def test_run_with_empty_text_raises_error(self, agent: SentimentAnalysisAgent) -> None:
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await agent.run("")


class TestCustomerSuccessAgent:
    """Test cases for CustomerSuccessAgent."""

    @pytest.fixture
    def agent(self) -> CustomerSuccessAgent:
        """Create a CustomerSuccessAgent instance."""
        return CustomerSuccessAgent()

    @pytest.mark.asyncio
    async def test_run_with_valid_customer(self, agent: CustomerSuccessAgent) -> None:
        """Test customer success analysis with valid data."""
        mock_response = (
            '{"health_score": 45.0, "churn_risk": "high", '
            '"recommended_actions": ["Schedule executive call", "Offer discount"], '
            '"outreach_message": "We value your business", '
            '"engagement_level": "low", "satisfaction_trend": "declining", '
            '"expansion_opportunity": false}'
        )
        with patch.object(agent, "_call_llm", new_callable=AsyncMock, return_value=mock_response):
            result = await agent.run(
                customer_id="cust-123",
                customer_data={"name": "Acme Corp", "mrr": 10000, "tenure_months": 6},
            )

        assert result.health_score == pytest.approx(45.0)
        assert result.churn_risk == "high"
        assert len(result.recommended_actions) == 2

    @pytest.mark.asyncio
    async def test_run_with_empty_customer_id_raises_error(self, agent: CustomerSuccessAgent) -> None:
        """Test that empty customer ID raises ValueError."""
        with pytest.raises(ValueError, match="Customer ID cannot be empty"):
            await agent.run(customer_id="", customer_data={})

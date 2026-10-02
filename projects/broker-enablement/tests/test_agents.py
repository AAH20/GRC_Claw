"""Tests for the Broker Enablement agents."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from broker_enablement.agents.commission_tracking import (
    CommissionCalculationRequest,
    CommissionTrackingAgent,
)
from broker_enablement.agents.multi_tenant_orchestration import (
    MultiTenantOrchestrationAgent,
    TenantContext,
)
from broker_enablement.agents.partner_enablement import (
    EnablementRequest,
    PartnerEnablementAgent,
)
from broker_enablement.agents.partner_onboarding import (
    PartnerOnboardingAgent,
    PartnerRegistrationRequest,
)
from broker_enablement.agents.performance_analytics import (
    AnalyticsRequest,
    PerformanceAnalyticsAgent,
)


class TestPartnerOnboardingAgent:
    """Tests for the Partner Onboarding Agent."""

    @pytest.fixture
    def agent(self) -> PartnerOnboardingAgent:
        """Create a Partner Onboarding Agent instance."""
        return PartnerOnboardingAgent()

    @pytest.fixture
    def valid_request(self) -> PartnerRegistrationRequest:
        """Create a valid registration request."""
        return PartnerRegistrationRequest(
            business_name="Test Partner LLC",
            contact_email="test@example.com",
            contact_phone="+1234567890",
            business_type="llc",
            tax_id="123456789",
            address="123 Main St, City, ST 12345",
            country="US",
        )

    @pytest.mark.asyncio
    async def test_register_partner_success(
        self, agent: PartnerOnboardingAgent, valid_request: PartnerRegistrationRequest
    ) -> None:
        """Test successful partner registration."""
        result = await agent.register_partner(valid_request)

        assert result.partner_id.startswith("prt_")
        assert result.status == "active"
        assert result.kyc_status == "verified"
        assert "successfully onboarded" in result.message

    @pytest.mark.asyncio
    async def test_register_partner_invalid_email(self, agent: PartnerOnboardingAgent) -> None:
        """Test registration with invalid email raises error."""
        with pytest.raises(ValueError):
            PartnerRegistrationRequest(
                business_name="Test",
                contact_email="invalid-email",
                business_type="llc",
                tax_id="123456789",
                address="123 Main St",
                country="US",
            )


class TestPartnerEnablementAgent:
    """Tests for the Partner Enablement Agent."""

    @pytest.fixture
    def agent(self) -> PartnerEnablementAgent:
        """Create a Partner Enablement Agent instance."""
        return PartnerEnablementAgent()

    @pytest.mark.asyncio
    async def test_start_enablement_success(
        self, agent: PartnerEnablementAgent
    ) -> None:
        """Test successful enablement workflow."""
        request = EnablementRequest(
            partner_id="prt_test123",
            enablement_type="training",
            content_ids=["module_1", "module_2", "module_3"],
        )

        result = await agent.start_enablement(request)

        assert result.partner_id == "prt_test123"
        assert result.status == "completed"
        assert len(result.completed_modules) == 3
        assert result.certification_status == "certified"


class TestCommissionTrackingAgent:
    """Tests for the Commission Tracking Agent."""

    @pytest.fixture
    def agent(self) -> CommissionTrackingAgent:
        """Create a Commission Tracking Agent instance."""
        return CommissionTrackingAgent()

    @pytest.mark.asyncio
    async def test_calculate_commission_success(
        self, agent: CommissionTrackingAgent
    ) -> None:
        """Test successful commission calculation."""
        request = CommissionCalculationRequest(
            partner_id="prt_test123",
            transaction_amount=Decimal("10000.00"),
            product_type="standard",
            transaction_date=datetime.utcnow(),
        )

        result = await agent.calculate_commission(request)

        assert result.commission_id.startswith("com_")
        assert result.partner_id == "prt_test123"
        assert result.transaction_amount == Decimal("10000.00")
        assert result.commission_rate == Decimal("0.05")
        assert result.commission_amount == Decimal("500.00")
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_get_partner_commissions(
        self, agent: CommissionTrackingAgent
    ) -> None:
        """Test fetching partner commissions."""
        records = await agent.get_partner_commissions("prt_test123")
        assert isinstance(records, list)

    @pytest.mark.asyncio
    async def test_process_payout(self, agent: CommissionTrackingAgent) -> None:
        """Test payout processing."""
        result = await agent.process_payout("com_test123")
        assert result["commission_id"] == "com_test123"
        assert result["status"] == "paid"


class TestPerformanceAnalyticsAgent:
    """Tests for the Performance Analytics Agent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        """Create a Performance Analytics Agent instance."""
        return PerformanceAnalyticsAgent()

    @pytest.mark.asyncio
    async def test_get_performance_metrics(
        self, agent: PerformanceAnalyticsAgent
    ) -> None:
        """Test performance metrics calculation."""
        request = AnalyticsRequest(
            partner_id="prt_test123",
            metrics=["revenue", "deals", "conversion"],
        )

        result = await agent.get_performance_metrics(request)

        assert result.partner_id == "prt_test123"
        assert result.total_revenue == Decimal("100000.00")
        assert result.deal_count == 25
        assert result.conversion_rate == 0.35
        assert result.trend == "upward"

    @pytest.mark.asyncio
    async def test_get_predictive_insights(
        self, agent: PerformanceAnalyticsAgent
    ) -> None:
        """Test predictive insights generation."""
        result = await agent.get_predictive_insights("prt_test123")

        assert "forecasted_revenue_next_quarter" in result
        assert "confidence_interval" in result
        assert "recommended_actions" in result


class TestMultiTenantOrchestrationAgent:
    """Tests for the Multi-tenant Orchestration Agent."""

    @pytest.fixture
    def agent(self) -> MultiTenantOrchestrationAgent:
        """Create a Multi-tenant Orchestration Agent instance."""
        return MultiTenantOrchestrationAgent()

    @pytest.mark.asyncio
    async def test_create_tenant_success(
        self, agent: MultiTenantOrchestrationAgent
    ) -> None:
        """Test successful tenant creation."""
        result = await agent.create_tenant("tenant_123", tier="premium")

        assert result.tenant_id == "tenant_123"
        assert result.status == "active"
        assert result.metadata["tier"] == "premium"

    @pytest.mark.asyncio
    async def test_create_tenant_duplicate(
        self, agent: MultiTenantOrchestrationAgent
    ) -> None:
        """Test creating duplicate tenant raises error."""
        await agent.create_tenant("tenant_123")

        with pytest.raises(ValueError, match="already exists"):
            await agent.create_tenant("tenant_123")

    @pytest.mark.asyncio
    async def test_route_request_success(
        self, agent: MultiTenantOrchestrationAgent
    ) -> None:
        """Test successful request routing."""
        await agent.create_tenant("tenant_123", tier="premium")

        context = TenantContext(tenant_id="tenant_123", tier="premium")
        result = await agent.route_request(context, "api")

        assert result["status"] == "routed"
        assert result["tenant_id"] == "tenant_123"

    @pytest.mark.asyncio
    async def test_route_request_tenant_not_found(
        self, agent: MultiTenantOrchestrationAgent
    ) -> None:
        """Test routing with non-existent tenant raises error."""
        context = TenantContext(tenant_id="nonexistent")

        with pytest.raises(ValueError, match="not found"):
            await agent.route_request(context, "api")

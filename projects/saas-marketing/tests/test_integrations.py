"""Tests for third-party integrations."""

from __future__ import annotations

import httpx
import pytest
import respx

from saas_marketing.integrations.hubspot import HubSpotConfig, HubSpotContact, HubSpotIntegration
from saas_marketing.integrations.salesforce import (
    SalesforceConfig,
    SalesforceContact,
    SalesforceIntegration,
)
from saas_marketing.integrations.stripe import StripeConfig, StripeCustomer, StripeIntegration


class TestSalesforceIntegration:
    """Tests for Salesforce integration."""

    @pytest.fixture
    def config(self) -> SalesforceConfig:
        """Create a test Salesforce config."""
        return SalesforceConfig(
            client_id="test_client_id",
            client_secret="test_client_secret",
            username="test@example.com",
            password="test_password",
            security_token="test_token",
        )

    @pytest.fixture
    def integration(self, config: SalesforceConfig) -> SalesforceIntegration:
        """Create a Salesforce integration instance."""
        return SalesforceIntegration(config)

    @respx.mock
    @pytest.mark.asyncio
    async def test_authenticate(self, integration: SalesforceIntegration) -> None:
        """Test Salesforce authentication."""
        route = respx.post("https://login.salesforce.com/services/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_access_token",
                    "instance_url": "https://test.salesforce.com",
                },
            )
        )

        token = await integration.authenticate()
        assert token == "test_access_token"
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_upsert_contact(self, integration: SalesforceIntegration) -> None:
        """Test upserting a contact."""
        # Mock authentication
        respx.post("https://login.salesforce.com/services/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_token",
                    "instance_url": "https://test.salesforce.com",
                },
            )
        )

        # Mock contact creation
        respx.post(
            "https://test.salesforce.com/services/data/v58.0/sobjects/Contact/"
        ).mock(
            return_value=httpx.Response(
                201,
                json={"id": "003xx0000012345", "success": True},
            )
        )

        await integration.authenticate()

        contact = SalesforceContact(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            company="Acme Inc",
        )
        result = await integration.upsert_contact(contact)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_upsert_contact_not_authenticated(self, integration: SalesforceIntegration) -> None:
        """Test that upserting without auth raises RuntimeError."""
        contact = SalesforceContact(email="test@example.com", last_name="Doe")
        with pytest.raises(RuntimeError, match="not authenticated"):
            await integration.upsert_contact(contact)


class TestHubSpotIntegration:
    """Tests for HubSpot integration."""

    @pytest.fixture
    def config(self) -> HubSpotConfig:
        """Create a test HubSpot config."""
        return HubSpotConfig(api_key="test_api_key")

    @pytest.fixture
    def integration(self, config: HubSpotConfig) -> HubSpotIntegration:
        """Create a HubSpot integration instance."""
        return HubSpotIntegration(config)

    @respx.mock
    @pytest.mark.asyncio
    async def test_upsert_contact(self, integration: HubSpotIntegration) -> None:
        """Test upserting a contact."""
        respx.post("https://api.hubapi.com/crm/v3/objects/cont").mock(
            return_value=httpx.Response(
                200,
                json={"id": "12345", "properties": {"email": "test@example.com"}},
            )
        )

        contact = HubSpotContact(
            email="test@example.com",
            firstname="Jane",
            last_name="Smith",
            company="Tech Corp",
        )
        result = await integration.upsert_contact(contact)
        assert result["properties"]["email"] == "test@example.com"

    @respx.mock
    @pytest.mark.asyncio
    async def test_track_event(self, integration: HubSpotIntegration) -> None:
        """Test tracking a marketing event."""
        respx.post("https://api.hubapi.com/events/v3/send").mock(
            return_value=httpx.Response(200, json={"success": True})
        )

        result = await integration.track_event(
            "test@example.com", "page_view", {"page": "pricing"}
        )
        assert result["success"] is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_contact_by_email(self, integration: HubSpotIntegration) -> None:
        """Test retrieving a contact by email."""
        respx.post("https://api.hubapi.com/crm/v3/objects/cont/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "123", "properties": {"email": "test@example.com"}}
                    ]
                },
            )
        )

        result = await integration.get_contact_by_email("test@example.com")
        assert result is not None
        assert result["properties"]["email"] == "test@example.com"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_contact_not_found(self, integration: HubSpotIntegration) -> None:
        """Test retrieving a non-existent contact."""
        respx.post("https://api.hubapi.com/crm/v3/objects/cont/search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        result = await integration.get_contact_by_email("nonexistent@example.com")
        assert result is None


class TestStripeIntegration:
    """Tests for Stripe integration."""

    @pytest.fixture
    def config(self) -> StripeConfig:
        """Create a test Stripe config."""
        return StripeConfig(secret_key="sk_test_123")

    @pytest.fixture
    def integration(self, config: StripeConfig) -> StripeIntegration:
        """Create a Stripe integration instance."""
        return StripeIntegration(config)

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_customer(self, integration: StripeIntegration) -> None:
        """Test creating a customer."""
        respx.post("https://api.stripe.com/v1/customers").mock(
            return_value=httpx.Response(
                200,
                json={"id": "cus_123", "email": "test@example.com"},
            )
        )

        customer = StripeCustomer(email="test@example.com", name="Test User")
        result = await integration.create_customer(customer)
        assert result["id"] == "cus_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_customer(self, integration: StripeIntegration) -> None:
        """Test retrieving a customer."""
        respx.get("https://api.stripe.com/v1/customers/cus_123").mock(
            return_value=httpx.Response(
                200,
                json={"id": "cus_123", "email": "test@example.com"},
            )
        )

        result = await integration.get_customer("cus_123")
        assert result["email"] == "test@example.com"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_subscriptions(self, integration: StripeIntegration) -> None:
        """Test getting customer subscriptions."""
        respx.get("https://api.stripe.com/v1/subscriptions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"id": "sub_123", "status": "active"},
                        {"id": "sub_456", "status": "canceled"},
                    ]
                },
            )
        )

        result = await integration.get_subscriptions("cus_123")
        assert len(result) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_cancel_subscription_at_period_end(self, integration: StripeIntegration) -> None:
        """Test canceling a subscription at period end."""
        respx.post("https://api.stripe.com/v1/subscriptions/sub_123").mock(
            return_value=httpx.Response(
                200,
                json={"id": "sub_123", "cancel_at_period_end": True},
            )
        )

        result = await integration.cancel_subscription("sub_123", immediate=False)
        assert result["cancel_at_period_end"] is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_cancel_subscription_immediate(self, integration: StripeIntegration) -> None:
        """Test immediately canceling a subscription."""
        respx.delete("https://api.stripe.com/v1/subscriptions/sub_123").mock(
            return_value=httpx.Response(
                200,
                json={"id": "sub_123", "status": "canceled"},
            )
        )

        result = await integration.cancel_subscription("sub_123", immediate=True)
        assert result["status"] == "canceled"

    def test_verify_webhook(self, integration: StripeIntegration) -> None:
        """Test webhook payload verification."""
        import json

        payload = json.dumps({"type": "customer.created", "data": {"id": "cus_123"}}).encode()
        result = integration.verify_webhook(payload, "test_signature")
        assert result["type"] == "customer.created"

    def test_verify_webhook_invalid_payload(self, integration: StripeIntegration) -> None:
        """Test webhook verification with invalid payload."""
        with pytest.raises(ValueError, match="Invalid webhook payload"):
            integration.verify_webhook(b"invalid json", "test_signature")

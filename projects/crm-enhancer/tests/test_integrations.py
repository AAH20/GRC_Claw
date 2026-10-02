"""Tests for CRM Enhancer integrations."""

from __future__ import annotations

import httpx
import pytest
import respx

from crm_enhancer.integrations.hubspot import HubSpotClient
from crm_enhancer.integrations.pipedrive import PipedriveClient
from crm_enhancer.integrations.salesforce import SalesforceClient


class TestSalesforceClient:
    """Tests for Salesforce integration."""

    @pytest.fixture
    def client(self) -> SalesforceClient:
        """Create a Salesforce client."""
        return SalesforceClient(
            client_id="test_id",
            client_secret="test_secret",
            username="test@example.com",
            password="testpass",
            security_token="token123",
        )

    @respx.mock
    @pytest.mark.asyncio
    async def test_authenticate_success(self, client: SalesforceClient) -> None:
        """Test successful authentication."""
        route = respx.post("https://login.salesforce.com/services/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_token",
                    "instance_url": "https://test.salesforce.com",
                },
            )
        )
        await client.authenticate()
        assert client._access_token == "test_token"
        assert client._instance_url == "https://test.salesforce.com"
        assert route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_authenticate_failure(self, client: SalesforceClient) -> None:
        """Test authentication failure."""
        respx.post("https://login.salesforce.com/services/oauth2/token").mock(
            return_value=httpx.Response(400, json={"error": "invalid_grant"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await client.authenticate()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_contacts(self, client: SalesforceClient) -> None:
        """Test getting contacts."""
        # First mock auth
        respx.post("https://login.salesforce.com/services/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "test_token",
                    "instance_url": "https://test.salesforce.com",
                },
            )
        )
        # Then mock contacts query
        respx.get(url__startswith="https://test.salesforce.com/services/data/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "records": [
                        {"Id": "001", "FirstName": "John", "LastName": "Doe", "Email": "john@example.com"}
                    ]
                },
            )
        )
        contacts = await client.get_contacts()
        assert len(contacts) == 1
        assert contacts[0]["FirstName"] == "John"

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client: SalesforceClient) -> None:
        """Test health check returns False on failure."""
        result = await client.health_check()
        assert result is False


class TestHubSpotClient:
    """Tests for HubSpot integration."""

    @pytest.fixture
    def client(self) -> HubSpotClient:
        """Create a HubSpot client."""
        return HubSpotClient(api_key="test_key", app_id="test_app")

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_contacts(self, client: HubSpotClient) -> None:
        """Test getting contacts from HubSpot."""
        respx.get(url__startswith="https://api.hubapi.com/crm/v3/objects/cont").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "1", "properties": {"email": "test@example.com", "firstname": "Test"}}
                    ]
                },
            )
        )
        contacts = await client.get_contacts()
        assert len(contacts) == 1
        assert contacts[0]["properties"]["email"] == "test@example.com"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_deals(self, client: HubSpotClient) -> None:
        """Test getting deals from HubSpot."""
        respx.get(url__startswith="https://api.hubapi.com/crm/v3/objects/deals").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "1", "properties": {"dealname": "Test Deal", "amount": "50000"}}
                    ]
                },
            )
        )
        deals = await client.get_deals()
        assert len(deals) == 1
        assert deals[0]["properties"]["dealname"] == "Test Deal"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_contact(self, client: HubSpotClient) -> None:
        """Test creating a contact in HubSpot."""
        respx.post(url__startswith="https://api.hubapi.com/crm/v3/objects/cont").mock(
            return_value=httpx.Response(
                201,
                json={"id": "123", "properties": {"email": "new@example.com"}},
            )
        )
        result = await client.create_contact({"email": "new@example.com"})
        assert result["id"] == "123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_health_check_success(self, client: HubSpotClient) -> None:
        """Test successful health check."""
        respx.get(url__startswith="https://api.hubapi.com/integrations/v1/me").mock(
            return_value=httpx.Response(200, json={"id": 1})
        )
        result = await client.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client: HubSpotClient) -> None:
        """Test health check returns False on failure."""
        result = await client.health_check()
        assert result is False


class TestPipedriveClient:
    """Tests for Pipedrive integration."""

    @pytest.fixture
    def client(self) -> PipedriveClient:
        """Create a Pipedrive client."""
        return PipedriveClient(api_token="test_token", company_domain="testcompany")

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_persons(self, client: PipedriveClient) -> None:
        """Test getting persons from Pipedrive."""
        respx.get(url__startswith="https://testcompany.pipedrive.com/api/v1/persons").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"id": 1, "name": "John Doe", "email": "john@example.com"}
                    ]
                },
            )
        )
        persons = await client.get_persons()
        assert len(persons) == 1
        assert persons[0]["name"] == "John Doe"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_deals(self, client: PipedriveClient) -> None:
        """Test getting deals from Pipedrive."""
        respx.get(url__startswith="https://testcompany.pipedrive.com/api/v1/deals").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"id": 1, "title": "Test Deal", "value": 50000}
                    ]
                },
            )
        )
        deals = await client.get_deals()
        assert len(deals) == 1
        assert deals[0]["title"] == "Test Deal"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_person(self, client: PipedriveClient) -> None:
        """Test creating a person in Pipedrive."""
        respx.post(url__startswith="https://testcompany.pipedrive.com/api/v1/persons").mock(
            return_value=httpx.Response(
                201,
                json={"id": 123, "name": "New Person"},
            )
        )
        result = await client.create_person({"name": "New Person", "email": "new@example.com"})
        assert result["id"] == 123

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_activities(self, client: PipedriveClient) -> None:
        """Test getting activities from Pipedrive."""
        respx.get(url__startswith="https://testcompany.pipedrive.com/api/v1/activities").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"id": 1, "type": "meeting", "subject": "Test Meeting"}
                    ]
                },
            )
        )
        activities = await client.get_activities()
        assert len(activities) == 1
        assert activities[0]["type"] == "meeting"

    @respx.mock
    @pytest.mark.asyncio
    async def test_health_check_success(self, client: PipedriveClient) -> None:
        """Test successful health check."""
        respx.get(url__startswith="https://testcompany.pipedrive.com/api/v1/users").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        result = await client.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client: PipedriveClient) -> None:
        """Test health check returns False on failure."""
        result = await client.health_check()
        assert result is False

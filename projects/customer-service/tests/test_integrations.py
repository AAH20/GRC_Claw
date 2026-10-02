"""Tests for customer service integrations."""

from __future__ import annotations

import httpx
import pytest
import respx

from customer_service.integrations import IntercomClient, SalesforceClient, ZendeskClient


class TestZendeskClient:
    """Test cases for ZendeskClient."""

    @pytest.fixture
    def client(self) -> ZendeskClient:
        """Create a ZendeskClient instance."""
        return ZendeskClient(
            subdomain="test",
            email="test@example.com",
            api_token="test-token",
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_ticket(self, client: ZendeskClient) -> None:
        """Test creating a ticket in Zendesk."""
        route = respx.post("https://test.zendesk.com/api/v2/tickets.json").mock(
            return_value=httpx.Response(201, json={"ticket": {"id": 123}})
        )

        result = await client.create_ticket(
            subject="Test ticket",
            description="Test description",
            requester_email="customer@example.com",
        )

        assert route.called
        assert result["ticket"]["id"] == 123

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_ticket(self, client: ZendeskClient) -> None:
        """Test retrieving a ticket from Zendesk."""
        route = respx.get("https://test.zendesk.com/api/v2/tickets/123.json").mock(
            return_value=httpx.Response(200, json={"ticket": {"id": 123, "subject": "Test"}})
        )

        result = await client.get_ticket(123)

        assert route.called
        assert result["ticket"]["id"] == 123

    @pytest.mark.asyncio
    @respx.mock
    async def test_update_ticket(self, client: ZendeskClient) -> None:
        """Test updating a ticket in Zendesk."""
        route = respx.put("https://test.zendesk.com/api/v2/tickets/123.json").mock(
            return_value=httpx.Response(200, json={"ticket": {"id": 123, "status": "solved"}})
        )

        result = await client.update_ticket(123, status="solved")

        assert route.called
        assert result["ticket"]["status"] == "solved"

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_tickets(self, client: ZendeskClient) -> None:
        """Test searching tickets in Zendesk."""
        route = respx.get("https://test.zendesk.com/api/v2/search.json").mock(
            return_value=httpx.Response(200, json={"results": [{"id": 1}]})
        )

        result = await client.search_tickets("status:open")

        assert route.called
        assert len(result["results"]) == 1


class TestIntercomClient:
    """Test cases for IntercomClient."""

    @pytest.fixture
    def client(self) -> IntercomClient:
        """Create an IntercomClient instance."""
        return IntercomClient(access_token="test-token")

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_contact(self, client: IntercomClient) -> None:
        """Test creating a contact in Intercom."""
        route = respx.post("https://api.intercom.io/contacts").mock(
            return_value=httpx.Response(200, json={"id": "contact-123", "email": "test@example.com"})
        )

        result = await client.create_contact(email="test@example.com", name="Test User")

        assert route.called
        assert result["id"] == "contact-123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_contact(self, client: IntercomClient) -> None:
        """Test retrieving a contact from Intercom."""
        route = respx.get("https://api.intercom.io/contacts/contact-123").mock(
            return_value=httpx.Response(200, json={"id": "contact-123", "email": "test@example.com"})
        )

        result = await client.get_contact("contact-123")

        assert route.called
        assert result["id"] == "contact-123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_conversation(self, client: IntercomClient) -> None:
        """Test creating a conversation in Intercom."""
        route = respx.post("https://api.intercom.io/conversations").mock(
            return_value=httpx.Response(200, json={"id": "conv-123"})
        )

        result = await client.create_conversation(
            contact_id="contact-123",
            message="Hello, I need help",
        )

        assert route.called
        assert result["id"] == "conv-123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_reply_to_conversation(self, client: IntercomClient) -> None:
        """Test replying to an Intercom conversation."""
        route = respx.post("https://api.intercom.io/conversations/conv-123/reply").mock(
            return_value=httpx.Response(200, json={"id": "msg-456"})
        )

        result = await client.reply_to_conversation(
            conversation_id="conv-123",
            message="Here is your answer",
        )

        assert route.called
        assert result["id"] == "msg-456"


class TestSalesforceClient:
    """Test cases for SalesforceClient."""

    @pytest.fixture
    def client(self) -> SalesforceClient:
        """Create a SalesforceClient instance."""
        return SalesforceClient(
            username="test@example.com",
            password="password123",
            security_token="token123",
            client_id="client-id",
            client_secret="client-secret",
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_authenticate(self, client: SalesforceClient) -> None:
        """Test Salesforce OAuth authentication."""
        route = respx.post("https://login.salesforce.com/services/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "sf-token-123",
                    "instance_url": "https://test.salesforce.com",
                },
            )
        )

        await client._authenticate()

        assert route.called
        assert client._access_token == "sf-token-123"
        assert client._instance_url == "https://test.salesforce.com"

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_case(self, client: SalesforceClient) -> None:
        """Test creating a case in Salesforce."""
        respx.post("https://login.salesforce.com/services/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "sf-token-123",
                    "instance_url": "https://test.salesforce.com",
                },
            )
        )
        route = respx.post("https://test.salesforce.com/services/data/v58.0/sobjects/Case").mock(
            return_value=httpx.Response(201, json={"id": "case-123"})
        )

        result = await client.create_case(
            contact_id="contact-456",
            subject="Test case",
            description="Test description",
        )

        assert route.called
        assert result["id"] == "case-123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_case(self, client: SalesforceClient) -> None:
        """Test retrieving a case from Salesforce."""
        respx.post("https://login.salesforce.com/services/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "sf-token-123",
                    "instance_url": "https://test.salesforce.com",
                },
            )
        )
        route = respx.get("https://test.salesforce.com/services/data/v58.0/sobjects/Case/case-123").mock(
            return_value=httpx.Response(200, json={"Id": "case-123", "Subject": "Test"})
        )

        result = await client.get_case("case-123")

        assert route.called
        assert result["Id"] == "case-123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_query(self, client: SalesforceClient) -> None:
        """Test executing a SOQL query."""
        respx.post("https://login.salesforce.com/services/oauth2/token").mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": "sf-token-123",
                    "instance_url": "https://test.salesforce.com",
                },
            )
        )
        route = respx.get("https://test.salesforce.com/services/data/v58.0/query").mock(
            return_value=httpx.Response(200, json={"records": [{"Id": "001"}]})
        )

        result = await client.query("SELECT Id FROM Account LIMIT 1")

        assert route.called
        assert len(result["records"]) == 1

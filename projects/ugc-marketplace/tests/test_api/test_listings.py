"""
Comprehensive API tests for the Listings endpoints.

Tests cover:
    - POST   /listings        (create)
    - GET    /listings        (list)
    - GET    /listings/search (search)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_listing_payload(**overrides: object) -> dict:
    """Return a valid listing payload, with optional field overrides."""
    payload: dict = {
        "title": "Test Listing",
        "description": "A test listing description",
        "price": 29.99,
        "currency": "USD",
        "category": "digital",
        "tags": ["test", "sample"],
        "status": "active",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# 1. POST /listings  — test_create_listing
# ---------------------------------------------------------------------------

class TestCreateListing:
    """Tests for POST /listings."""

    def test_create_listing_success(self, client: TestClient) -> None:
        """Creating a listing with valid data returns 201 and the listing."""
        payload = _sample_listing_payload()
        response = client.post("/listings", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["description"] == payload["description"]
        assert data["price"] == payload["price"]
        assert data["currency"] == payload["currency"]
        assert data["category"] == payload["category"]
        assert "id" in data
        assert "created_at" in data

    def test_create_listing_minimal_fields(self, client: TestClient) -> None:
        """Creating a listing with only required fields succeeds."""
        payload = {"title": "Minimal", "price": 10.0}
        response = client.post("/listings", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal"
        assert data["price"] == 10.0

    def test_create_listing_missing_title(self, client: TestClient) -> None:
        """Missing required field 'title' returns 422."""
        payload = _sample_listing_payload()
        del payload["title"]
        response = client.post("/listings", json=payload)

        assert response.status_code == 422

    def test_create_listing_missing_price(self, client: TestClient) -> None:
        """Missing required field 'price' returns 422."""
        payload = _sample_listing_payload()
        del payload["price"]
        response = client.post("/listings", json=payload)

        assert response.status_code == 422

    def test_create_listing_invalid_price_type(self, client: TestClient) -> None:
        """Non-numeric price returns 422."""
        payload = _sample_listing_payload(price="not-a-number")
        response = client.post("/listings", json=payload)

        assert response.status_code == 422

    def test_create_listing_negative_price(self, client: TestClient) -> None:
        """Negative price returns 422."""
        payload = _sample_listing_payload(price=-5.0)
        response = client.post("/listings", json=payload)

        assert response.status_code == 422

    def test_create_listing_empty_title(self, client: TestClient) -> None:
        """Empty title string returns 422."""
        payload = _sample_listing_payload(title="")
        response = client.post("/listings", json=payload)

        assert response.status_code == 422

    def test_create_listing_extra_fields_ignored(self, client: TestClient) -> None:
        """Extra unknown fields are either ignored or rejected gracefully."""
        payload = _sample_listing_payload(unknown_field="value")
        response = client.post("/listings", json=payload)

        # Either 201 (ignored) or 422 (strict validation) is acceptable
        assert response.status_code in (201, 422)

    def test_create_listing_response_has_id(self, client: TestClient) -> None:
        """Response contains a unique id field."""
        payload = _sample_listing_payload()
        response = client.post("/listings", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert isinstance(data["id"], (str, int))

    def test_create_listing_duplicate_title_allowed(self, client: TestClient) -> None:
        """Two listings with the same title can be created (no uniqueness constraint)."""
        payload = _sample_listing_payload(title="Duplicate Title")
        r1 = client.post("/listings", json=payload)
        r2 = client.post("/listings", json=payload)

        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["id"] != r2.json()["id"]


# ---------------------------------------------------------------------------
# 2. GET /listings  — test_list_listings
# ---------------------------------------------------------------------------

class TestListListings:
    """Tests for GET /listings."""

    def test_list_listings_empty(self, client: TestClient) -> None:
        """GET /listings returns an empty list when no listings exist."""
        response = client.get("/listings")

        assert response.status_code == 200
        data = response.json()
        # Response may be a list or a paginated dict with 'items'/'results'
        if isinstance(data, list):
            assert data == []
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
            assert items == []
        else:
            pytest.fail(f"Unexpected response type: {type(data)}")

    def test_list_listings_returns_created(self, client: TestClient) -> None:
        """After creating a listing, GET /listings includes it."""
        payload = _sample_listing_payload(title="Listed Item")
        create_resp = client.post("/listings", json=payload)
        assert create_resp.status_code == 201

        response = client.get("/listings")
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            titles = [item["title"] for item in data]
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
            titles = [item["title"] for item in items]
        else:
            pytest.fail(f"Unexpected response type: {type(data)}")

        assert "Listed Item" in titles

    def test_list_listings_pagination_limit(self, client: TestClient) -> None:
        """The 'limit' query parameter restricts the number of results."""
        for i in range(5):
            client.post("/listings", json=_sample_listing_payload(title=f"Item {i}"))

        response = client.get("/listings", params={"limit": 2})
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            assert len(data) <= 2
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
            assert len(items) <= 2

    def test_list_listings_pagination_offset(self, client: TestClient) -> None:
        """The 'offset' query parameter skips the first N results."""
        for i in range(5):
            client.post("/listings", json=_sample_listing_payload(title=f"Offset Item {i}"))

        response = client.get("/listings", params={"offset": 3, "limit": 10})
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            assert len(data) <= 2  # 5 total - 3 offset = 2 remaining
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
            assert len(items) <= 2

    def test_list_listings_response_structure(self, client: TestClient) -> None:
        """Each listing in the response has expected fields."""
        client.post("/listings", json=_sample_listing_payload(title="Structure Test"))
        response = client.get("/listings")

        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
        else:
            pytest.fail(f"Unexpected response type: {type(data)}")

        assert len(items) > 0
        first = items[0]
        expected_keys = {"id", "title", "price"}
        assert expected_keys.issubset(set(first.keys()))

    def test_list_listings_filter_by_category(self, client: TestClient) -> None:
        """Filtering by category returns only matching listings."""
        client.post("/listings", json=_sample_listing_payload(title="Cat A", category="digital"))
        client.post("/listings", json=_sample_listing_payload(title="Cat B", category="physical"))

        response = client.get("/listings", params={"category": "digital"})
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
        else:
            pytest.fail(f"Unexpected response type: {type(data)}")

        for item in items:
            assert item.get("category") == "digital"

    def test_list_listings_filter_by_status(self, client: TestClient) -> None:
        """Filtering by status returns only matching listings."""
        client.post("/listings", json=_sample_listing_payload(title="Active", status="active"))
        client.post("/listings", json=_sample_listing_payload(title="Draft", status="draft"))

        response = client.get("/listings", params={"status": "active"})
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
        else:
            pytest.fail(f"Unexpected response type: {type(data)}")

        for item in items:
            assert item.get("status") == "active"


# ---------------------------------------------------------------------------
# 3. GET /listings/search  — test_search_listings
# ---------------------------------------------------------------------------

class TestSearchListings:
    """Tests for GET /listings/search."""

    def test_search_listings_basic_query(self, client: TestClient) -> None:
        """Search returns listings matching the query string."""
        client.post("/listings", json=_sample_listing_payload(
            title="Python Course", description="Learn Python programming"
        ))
        client.post("/listings", json=_sample_listing_payload(
            title="JavaScript Course", description="Learn JavaScript programming"
        ))

        response = client.get("/listings/search", params={"q": "Python"})
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
        else:
            pytest.fail(f"Unexpected response type: {type(data)}")

        assert len(items) > 0
        titles = [item["title"] for item in items]
        assert any("Python" in t for t in titles)

    def test_search_listings_no_results(self, client: TestClient) -> None:
        """Search with a non-matching query returns empty results."""
        client.post("/listings", json=_sample_listing_payload(title="Something Else"))

        response = client.get("/listings/search", params={"q": "zzzznonexistent"})
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            assert data == []
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
            assert items == []

    def test_search_listings_empty_query(self, client: TestClient) -> None:
        """Empty search query returns all listings or 422."""
        client.post("/listings", json=_sample_listing_payload(title="Test"))

        response = client.get("/listings/search", params={"q": ""})
        # Either returns all listings (200) or rejects empty query (422)
        assert response.status_code in (200, 422)

    def test_search_listings_missing_query_param(self, client: TestClient) -> None:
        """Missing 'q' parameter returns 422."""
        response = client.get("/listings/search")
        assert response.status_code == 422

    def test_search_listings_by_description(self, client: TestClient) -> None:
        """Search matches against description text."""
        client.post("/listings", json=_sample_listing_payload(
            title="Generic Title", description="Unique keyword: xyzzy"
        ))

        response = client.get("/listings/search", params={"q": "xyzzy"})
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
        else:
            pytest.fail(f"Unexpected response type: {type(data)}")

        assert len(items) > 0

    def test_search_listings_by_tag(self, client: TestClient) -> None:
        """Search matches against tags."""
        client.post("/listings", json=_sample_listing_payload(
            title="Tagged Item", tags=["raretag123"]
        ))

        response = client.get("/listings/search", params={"q": "raretag123"})
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
        else:
            pytest.fail(f"Unexpected response type: {type(data)}")

        assert len(items) > 0

    def test_search_listings_with_limit(self, client: TestClient) -> None:
        """Search respects the limit parameter."""
        for i in range(5):
            client.post("/listings", json=_sample_listing_payload(
                title=f"Searchable Item {i}", tags=["searchtest"]
            ))

        response = client.get("/listings/search", params={"q": "Searchable", "limit": 2})
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            assert len(data) <= 2
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
            assert len(items) <= 2

    def test_search_listings_response_structure(self, client: TestClient) -> None:
        """Search results have the same structure as list results."""
        client.post("/listings", json=_sample_listing_payload(title="Structure Search"))
        response = client.get("/listings/search", params={"q": "Structure"})

        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
        else:
            pytest.fail(f"Unexpected response type: {type(data)}")

        assert len(items) > 0
        first = items[0]
        expected_keys = {"id", "title", "price"}
        assert expected_keys.issubset(set(first.keys()))

    def test_search_listings_case_insensitive(self, client: TestClient) -> None:
        """Search is case-insensitive."""
        client.post("/listings", json=_sample_listing_payload(title="UPPERCASE TITLE"))

        response = client.get("/listings/search", params={"q": "uppercase"})
        assert response.status_code == 200
        data = response.json()

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("items") or data.get("results") or data.get("data") or []
        else:
            pytest.fail(f"Unexpected response type: {type(data)}")

        assert len(items) > 0

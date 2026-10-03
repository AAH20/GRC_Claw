"""
Comprehensive API tests for the Reviews endpoints.

Tests cover:
- POST /reviews  (test_create_review)
- GET /reviews   (test_get_reviews)
- GET /reviews/average  (test_get_average_rating)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_review_payload(**overrides):
    """Return a valid review payload, with optional overrides."""
    payload = {
        "product_id": "prod-001",
        "user_id": "user-001",
        "rating": 5,
        "title": "Great product",
        "body": "Exceeded my expectations in every way.",
    }
    payload.update(overrides)
    return payload


# ===========================================================================
# 1. test_create_review  —  POST /reviews
# ===========================================================================

class TestCreateReview:
    """Tests for POST /reviews."""

    def test_create_review_success(self):
        """A valid review is created and returned with an id."""
        payload = _make_review_payload()
        response = client.post("/reviews", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["product_id"] == payload["product_id"]
        assert data["user_id"] == payload["user_id"]
        assert data["rating"] == payload["rating"]
        assert data["title"] == payload["title"]
        assert data["body"] == payload["body"]

    def test_create_review_minimum_fields(self):
        """Only required fields are needed to create a review."""
        payload = {
            "product_id": "prod-002",
            "user_id": "user-002",
            "rating": 3,
        }
        response = client.post("/reviews", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 3

    def test_create_review_rating_boundary_low(self):
        """Rating of 1 (minimum) is accepted."""
        payload = _make_review_payload(rating=1)
        response = client.post("/reviews", json=payload)
        assert response.status_code == 201
        assert response.json()["rating"] == 1

    def test_create_review_rating_boundary_high(self):
        """Rating of 5 (maximum) is accepted."""
        payload = _make_review_payload(rating=5)
        response = client.post("/reviews", json=payload)
        assert response.status_code == 201
        assert response.json()["rating"] == 5

    def test_create_review_invalid_rating_zero(self):
        """Rating below 1 is rejected."""
        payload = _make_review_payload(rating=0)
        response = client.post("/reviews", json=payload)
        assert response.status_code == 422

    def test_create_review_invalid_rating_six(self):
        """Rating above 5 is rejected."""
        payload = _make_review_payload(rating=6)
        response = client.post("/reviews", json=payload)
        assert response.status_code == 422

    def test_create_review_missing_product_id(self):
        """Missing product_id returns 422."""
        payload = _make_review_payload()
        del payload["product_id"]
        response = client.post("/reviews", json=payload)
        assert response.status_code == 422

    def test_create_review_missing_user_id(self):
        """Missing user_id returns 422."""
        payload = _make_review_payload()
        del payload["user_id"]
        response = client.post("/reviews", json=payload)
        assert response.status_code == 422

    def test_create_review_missing_rating(self):
        """Missing rating returns 422."""
        payload = _make_review_payload()
        del payload["rating"]
        response = client.post("/reviews", json=payload)
        assert response.status_code == 422

    def test_create_review_empty_body(self):
        """Empty JSON body returns 422."""
        response = client.post("/reviews", json={})
        assert response.status_code == 422

    def test_create_review_invalid_rating_type(self):
        """Non-integer rating returns 422."""
        payload = _make_review_payload(rating="excellent")
        response = client.post("/reviews", json=payload)
        assert response.status_code == 422

    def test_create_review_duplicate_same_user_product(self):
        """Duplicate review from same user for same product is rejected."""
        payload = _make_review_payload()
        # First review succeeds
        response1 = client.post("/reviews", json=payload)
        assert response1.status_code == 201
        # Duplicate should fail
        response2 = client.post("/reviews", json=payload)
        assert response2.status_code in (400, 409)

    def test_create_review_response_has_created_timestamp(self):
        """Created review includes a created_at timestamp."""
        payload = _make_review_payload()
        response = client.post("/reviews", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "created_at" in data


# ===========================================================================
# 2. test_get_reviews  —  GET /reviews
# ===========================================================================

class TestGetReviews:
    """Tests for GET /reviews."""

    def test_get_reviews_empty(self):
        """Returns empty list when no reviews exist (or after cleanup)."""
        response = client.get("/reviews")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_reviews_returns_created(self):
        """A created review appears in the list."""
        payload = _make_review_payload(product_id="prod-get-001")
        create_resp = client.post("/reviews", json=payload)
        assert create_resp.status_code == 201
        created_id = create_resp.json()["id"]

        response = client.get("/reviews")
        assert response.status_code == 200
        reviews = response.json()
        ids = [r["id"] for r in reviews]
        assert created_id in ids

    def test_get_reviews_filter_by_product_id(self):
        """Filtering by product_id returns only matching reviews."""
        product_id = "prod-filter-001"
        # Create two reviews for the product
        client.post("/reviews", json=_make_review_payload(product_id=product_id, user_id="u1"))
        client.post("/reviews", json=_make_review_payload(product_id=product_id, user_id="u2"))
        # Create one review for a different product
        client.post("/reviews", json=_make_review_payload(product_id="prod-other", user_id="u3"))

        response = client.get(f"/reviews?product_id={product_id}")
        assert response.status_code == 200
        reviews = response.json()
        assert len(reviews) >= 2
        for r in reviews:
            assert r["product_id"] == product_id

    def test_get_reviews_filter_by_user_id(self):
        """Filtering by user_id returns only matching reviews."""
        user_id = "user-filter-001"
        client.post("/reviews", json=_make_review_payload(user_id=user_id, product_id="p1"))
        client.post("/reviews", json=_make_review_payload(user_id=user_id, product_id="p2"))

        response = client.get(f"/reviews?user_id={user_id}")
        assert response.status_code == 200
        reviews = response.json()
        assert len(reviews) >= 2
        for r in reviews:
            assert r["user_id"] == user_id

    def test_get_reviews_pagination_limit(self):
        """Limit parameter restricts number of results."""
        # Create several reviews
        for i in range(5):
            client.post("/reviews", json=_make_review_payload(
                product_id=f"prod-page-{i}",
                user_id=f"user-page-{i}",
            ))

        response = client.get("/reviews?limit=2")
        assert response.status_code == 200
        reviews = response.json()
        assert len(reviews) <= 2

    def test_get_reviews_pagination_skip(self):
        """Skip parameter offsets the result set."""
        # Create reviews
        for i in range(3):
            client.post("/reviews", json=_make_review_payload(
                product_id=f"prod-skip-{i}",
                user_id=f"user-skip-{i}",
            ))

        all_resp = client.get("/reviews?limit=100")
        all_reviews = all_resp.json()

        skip_resp = client.get("/reviews?limit=100&skip=1")
        skip_reviews = skip_resp.json()

        if len(all_reviews) > 1:
            assert len(skip_reviews) < len(all_reviews)

    def test_get_reviews_response_structure(self):
        """Each review in the list has expected fields."""
        client.post("/reviews", json=_make_review_payload(product_id="prod-struct"))
        response = client.get("/reviews?product_id=prod-struct")
        assert response.status_code == 200
        reviews = response.json()
        assert len(reviews) > 0
        review = reviews[0]
        expected_fields = {"id", "product_id", "user_id", "rating", "created_at"}
        assert expected_fields.issubset(set(review.keys()))

    def test_get_reviews_ordered_by_created_desc(self):
        """Reviews are returned newest-first by default."""
        import time
        client.post("/reviews", json=_make_review_payload(product_id="prod-order", user_id="u1"))
        time.sleep(0.01)
        client.post("/reviews", json=_make_review_payload(product_id="prod-order", user_id="u2"))

        response = client.get("/reviews?product_id=prod-order")
        assert response.status_code == 200
        reviews = response.json()
        if len(reviews) >= 2:
            # Newest first: second review should appear before first
            assert reviews[0]["user_id"] == "u2"


# ===========================================================================
# 3. test_get_average_rating  —  GET /reviews/average
# ===========================================================================

class TestGetAverageRating:
    """Tests for GET /reviews/average."""

    def test_get_average_rating_success(self):
        """Returns average rating for a product with reviews."""
        product_id = "prod-avg-001"
        client.post("/reviews", json=_make_review_payload(product_id=product_id, rating=4))
        client.post("/reviews", json=_make_review_payload(product_id=product_id, rating=2))

        response = client.get(f"/reviews/average?product_id={product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == product_id
        assert data["average_rating"] == 3.0
        assert data["review_count"] == 2

    def test_get_average_rating_single_review(self):
        """Average of a single review equals that review's rating."""
        product_id = "prod-avg-002"
        client.post("/reviews", json=_make_review_payload(product_id=product_id, rating=5))

        response = client.get(f"/reviews/average?product_id={product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["average_rating"] == 5.0
        assert data["review_count"] == 1

    def test_get_average_rating_no_reviews(self):
        """Returns zero/None average for product with no reviews."""
        product_id = "prod-avg-nonexistent"
        response = client.get(f"/reviews/average?product_id={product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == product_id
        assert data["average_rating"] in (0, 0.0, None)
        assert data["review_count"] == 0

    def test_get_average_rating_missing_product_id(self):
        """Missing product_id query param returns 422."""
        response = client.get("/reviews/average")
        assert response.status_code == 422

    def test_get_average_rating_decimal_precision(self):
        """Average is computed correctly with decimal values."""
        product_id = "prod-avg-003"
        client.post("/reviews", json=_make_review_payload(product_id=product_id, rating=5))
        client.post("/reviews", json=_make_review_payload(product_id=product_id, rating=4))
        client.post("/reviews", json=_make_review_payload(product_id=product_id, rating=3))

        response = client.get(f"/reviews/average?product_id={product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["average_rating"] == 4.0
        assert data["review_count"] == 3

    def test_get_average_rating_does_not_affect_other_products(self):
        """Average is scoped to the requested product only."""
        product_a = "prod-avg-a"
        product_b = "prod-avg-b"
        client.post("/reviews", json=_make_review_payload(product_id=product_a, rating=1))
        client.post("/reviews", json=_make_review_payload(product_id=product_a, rating=2))
        client.post("/reviews", json=_make_review_payload(product_id=product_b, rating=5))

        resp_a = client.get(f"/reviews/average?product_id={product_a}")
        resp_b = client.get(f"/reviews/average?product_id={product_b}")

        assert resp_a.json()["average_rating"] == 1.5
        assert resp_b.json()["average_rating"] == 5.0

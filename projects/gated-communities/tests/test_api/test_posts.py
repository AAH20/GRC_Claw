"""
Comprehensive API tests for the Posts endpoints.

Tests cover:
- POST /posts  (create post)
- GET /posts   (list posts)
- GET /posts/{id}  (get single post)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import the app and database dependencies
# Adjust these imports to match your project structure
try:
    from app.main import app
    from app.database import get_db, Base
except ImportError:
    # Fallback for common project layouts
    from main import app
    from database import get_db, Base


# ─── Test Database Setup ───────────────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_posts.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency to use the test database."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Provide a TestClient instance."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_post_data():
    """Return a valid payload for creating a post."""
    return {
        "title": "Test Post Title",
        "content": "This is the content of the test post.",
        "author_id": 1,
    }


@pytest.fixture
def created_post(client, sample_post_data):
    """Create a post and return the response JSON."""
    response = client.post("/posts", json=sample_post_data)
    assert response.status_code == 201
    return response.json()


# ─── POST /posts ───────────────────────────────────────────────────────────────


class TestCreatePost:
    """Tests for POST /posts endpoint."""

    def test_create_post_success(self, client, sample_post_data):
        """Successfully create a post with valid data."""
        response = client.post("/posts", json=sample_post_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_post_data["title"]
        assert data["content"] == sample_post_data["content"]
        assert data["author_id"] == sample_post_data["author_id"]
        assert "id" in data
        assert isinstance(data["id"], int)

    def test_create_post_missing_title(self, client):
        """Fail to create a post when title is missing."""
        payload = {
            "content": "Content without title",
            "author_id": 1,
        }
        response = client.post("/posts", json=payload)
        assert response.status_code == 422

    def test_create_post_missing_content(self, client):
        """Fail to create a post when content is missing."""
        payload = {
            "title": "Title without content",
            "author_id": 1,
        }
        response = client.post("/posts", json=payload)
        assert response.status_code == 422

    def test_create_post_missing_author_id(self, client):
        """Fail to create a post when author_id is missing."""
        payload = {
            "title": "Title",
            "content": "Content",
        }
        response = client.post("/posts", json=payload)
        assert response.status_code == 422

    def test_create_post_empty_title(self, client):
        """Fail to create a post with an empty title."""
        payload = {
            "title": "",
            "content": "Some content",
            "author_id": 1,
        }
        response = client.post("/posts", json=payload)
        assert response.status_code == 422

    def test_create_post_empty_content(self, client):
        """Fail to create a post with empty content."""
        payload = {
            "title": "Some title",
            "content": "",
            "author_id": 1,
        }
        response = client.post("/posts", json=payload)
        assert response.status_code == 422

    def test_create_post_invalid_author_id_type(self, client):
        """Fail to create a post with non-integer author_id."""
        payload = {
            "title": "Title",
            "content": "Content",
            "author_id": "not-an-integer",
        }
        response = client.post("/posts", json=payload)
        assert response.status_code == 422

    def test_create_post_negative_author_id(self, client):
        """Fail to create a post with a negative author_id."""
        payload = {
            "title": "Title",
            "content": "Content",
            "author_id": -1,
        }
        response = client.post("/posts", json=payload)
        assert response.status_code == 422

    def test_create_post_extra_fields_ignored(self, client, sample_post_data):
        """Extra fields in payload should be ignored or rejected gracefully."""
        payload = {**sample_post_data, "unknown_field": "some value"}
        response = client.post("/posts", json=payload)
        # Either 201 (ignored) or 422 (rejected) are acceptable
        assert response.status_code in (201, 422)

    def test_create_post_no_body(self, client):
        """Fail to create a post with no request body."""
        response = client.post("/posts")
        assert response.status_code == 422

    def test_create_post_content_type_not_json(self, client):
        """Fail to create a post with non-JSON content type."""
        response = client.post(
            "/posts",
            data="title=Test&content=Content&author_id=1",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 422

    def test_create_post_title_too_long(self, client):
        """Fail to create a post with an excessively long title."""
        payload = {
            "title": "A" * 1000,
            "content": "Content",
            "author_id": 1,
        }
        response = client.post("/posts", json=payload)
        # Should either reject with 422 or truncate; 201 is also acceptable if no limit
        assert response.status_code in (201, 422)

    def test_create_post_content_too_long(self, client):
        """Fail to create a post with excessively long content."""
        payload = {
            "title": "Title",
            "content": "A" * 100000,
            "author_id": 1,
        }
        response = client.post("/posts", json=payload)
        assert response.status_code in (201, 422)

    def test_create_post_returns_created_timestamp(self, client, sample_post_data):
        """Verify the response includes a created_at timestamp."""
        response = client.post("/posts", json=sample_post_data)
        assert response.status_code == 201
        data = response.json()
        # Check for common timestamp field names
        has_timestamp = any(
            key in data for key in ("created_at", "createdAt", "created")
        )
        assert has_timestamp, "Response should include a creation timestamp"

    def test_create_post_id_is_unique(self, client, sample_post_data):
        """Each created post should have a unique ID."""
        resp1 = client.post("/posts", json=sample_post_data)
        resp2 = client.post("/posts", json=sample_post_data)
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.json()["id"] != resp2.json()["id"]

    def test_create_post_unicode_content(self, client):
        """Successfully create a post with unicode characters."""
        payload = {
            "title": "Unicode 测试 🎉",
            "content": "Content with émojis 🚀 and ünïcödé",
            "author_id": 1,
        }
        response = client.post("/posts", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["content"] == payload["content"]

    def test_create_post_whitespace_title(self, client):
        """Fail to create a post with a whitespace-only title."""
        payload = {
            "title": "   ",
            "content": "Content",
            "author_id": 1,
        }
        response = client.post("/posts", json=payload)
        assert response.status_code == 422

    def test_create_post_whitespace_content(self, client):
        """Fail to create a post with whitespace-only content."""
        payload = {
            "title": "Title",
            "content": "   ",
            "author_id": 1,
        }
        response = client.post("/posts", json=payload)
        assert response.status_code == 422


# ─── GET /posts ────────────────────────────────────────────────────────────────


class TestListPosts:
    """Tests for GET /posts endpoint."""

    def test_list_posts_empty(self, client):
        """Return empty list when no posts exist."""
        response = client.get("/posts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_posts_returns_created(self, client, sample_post_data):
        """Return a list containing the created post."""
        client.post("/posts", json=sample_post_data)
        response = client.get("/posts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == sample_post_data["title"]

    def test_list_posts_multiple(self, client, sample_post_data):
        """Return all created posts."""
        for i in range(5):
            payload = {**sample_post_data, "title": f"Post {i}"}
            client.post("/posts", json=payload)

        response = client.get("/posts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_list_posts_pagination_limit(self, client, sample_post_data):
        """Respect the limit query parameter."""
        for i in range(10):
            payload = {**sample_post_data, "title": f"Post {i}"}
            client.post("/posts", json=payload)

        response = client.get("/posts?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    def test_list_posts_pagination_offset(self, client, sample_post_data):
        """Respect the offset query parameter."""
        for i in range(5):
            payload = {**sample_post_data, "title": f"Post {i}"}
            client.post("/posts", json=payload)

        response = client.get("/posts?offset=2")
        assert response.status_code == 200
        data = response.json()
        # Should return posts starting from offset 2
        assert len(data) <= 3

    def test_list_posts_pagination_skip(self, client, sample_post_data):
        """Respect the skip query parameter (alternative to offset)."""
        for i in range(5):
            payload = {**sample_post_data, "title": f"Post {i}"}
            client.post("/posts", json=payload)

        response = client.get("/posts?skip=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    def test_list_posts_response_structure(self, client, created_post):
        """Verify each post in the list has the expected fields."""
        response = client.get("/posts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        post = data[0]
        required_fields = {"id", "title", "content", "author_id"}
        assert required_fields.issubset(set(post.keys()))

    def test_list_posts_ordering(self, client, sample_post_data):
        """Posts should be returned in a consistent order (newest first by default)."""
        for i in range(3):
            payload = {**sample_post_data, "title": f"Post {i}"}
            client.post("/posts", json=payload)

        response = client.get("/posts")
        assert response.status_code == 200
        data = response.json()
        # Newest first: Post 2, Post 1, Post 0
        titles = [p["title"] for p in data]
        assert titles == ["Post 2", "Post 1", "Post 0"]

    def test_list_posts_filter_by_author(self, client, sample_post_data):
        """Filter posts by author_id."""
        # Create posts for author 1
        for i in range(3):
            payload = {**sample_post_data, "author_id": 1, "title": f"Author1 Post {i}"}
            client.post("/posts", json=payload)

        # Create posts for author 2
        for i in range(2):
            payload = {**sample_post_data, "author_id": 2, "title": f"Author2 Post {i}"}
            client.post("/posts", json=payload)

        response = client.get("/posts?author_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for post in data:
            assert post["author_id"] == 1

    def test_list_posts_search_query(self, client, sample_post_data):
        """Search posts by query parameter."""
        client.post("/posts", json={**sample_post_data, "title": "Python Tips"})
        client.post("/posts", json={**sample_post_data, "title": "JavaScript Guide"})
        client.post("/posts", json={**sample_post_data, "title": "Python Advanced"})

        response = client.get("/posts?search=Python")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_posts_limit_zero(self, client, sample_post_data):
        """Handle limit=0 gracefully."""
        client.post("/posts", json=sample_post_data)
        response = client.get("/posts?limit=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_list_posts_negative_limit(self, client, sample_post_data):
        """Handle negative limit gracefully."""
        client.post("/posts", json=sample_post_data)
        response = client.get("/posts?limit=-1")
        # Should either return 422 or treat as no limit
        assert response.status_code in (200, 422)

    def test_list_posts_negative_offset(self, client, sample_post_data):
        """Handle negative offset gracefully."""
        client.post("/posts", json=sample_post_data)
        response = client.get("/posts?offset=-1")
        assert response.status_code in (200, 422)

    def test_list_posts_content_type(self, client):
        """Response should have application/json content type."""
        response = client.get("/posts")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


# ─── GET /posts/{id} ───────────────────────────────────────────────────────────


class TestGetPost:
    """Tests for GET /posts/{id} endpoint."""

    def test_get_post_success(self, client, created_post):
        """Successfully retrieve a post by ID."""
        post_id = created_post["id"]
        response = client.get(f"/posts/{post_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == post_id
        assert data["title"] == created_post["title"]
        assert data["content"] == created_post["content"]
        assert data["author_id"] == created_post["author_id"]

    def test_get_post_not_found(self, client):
        """Return 404 for a non-existent post ID."""
        response = client.get("/posts/99999")
        assert response.status_code == 404

    def test_get_post_invalid_id_string(self, client):
        """Return 422 for a non-integer post ID."""
        response = client.get("/posts/abc")
        assert response.status_code == 422

    def test_get_post_invalid_id_float(self, client):
        """Return 422 for a float post ID."""
        response = client.get("/posts/1.5")
        assert response.status_code == 422

    def test_get_post_negative_id(self, client):
        """Return 404 or 422 for a negative post ID."""
        response = client.get("/posts/-1")
        assert response.status_code in (404, 422)

    def test_get_post_zero_id(self, client):
        """Return 404 for post ID of 0."""
        response = client.get("/posts/0")
        assert response.status_code == 404

    def test_get_post_response_structure(self, client, created_post):
        """Verify the response contains all expected fields."""
        post_id = created_post["id"]
        response = client.get(f"/posts/{post_id}")
        assert response.status_code == 200
        data = response.json()
        required_fields = {"id", "title", "content", "author_id"}
        assert required_fields.issubset(set(data.keys()))

    def test_get_post_content_type(self, client, created_post):
        """Response should have application/json content type."""
        post_id = created_post["id"]
        response = client.get(f"/posts/{post_id}")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_post_does_not_mutate(self, client, created_post):
        """Getting a post should not change its data."""
        post_id = created_post["id"]
        resp1 = client.get(f"/posts/{post_id}")
        resp2 = client.get(f"/posts/{post_id}")
        assert resp1.json() == resp2.json()

    def test_get_post_after_creation(self, client, sample_post_data):
        """A newly created post should be immediately retrievable."""
        create_resp = client.post("/posts", json=sample_post_data)
        assert create_resp.status_code == 201
        new_id = create_resp.json()["id"]

        get_resp = client.get(f"/posts/{new_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["title"] == sample_post_data["title"]

    def test_get_post_large_id(self, client):
        """Handle very large post ID gracefully."""
        response = client.get("/posts/999999999999999999")
        assert response.status_code == 404

    def test_get_post_with_special_characters_in_path(self, client):
        """Handle special characters in the path gracefully."""
        response = client.get("/posts/abc%20def")
        assert response.status_code in (404, 422)

    def test_get_post_consistency_with_list(self, client, created_post):
        """The post retrieved by ID should match the one in the list."""
        post_id = created_post["id"]

        list_resp = client.get("/posts")
        list_data = list_resp.json()
        post_in_list = next((p for p in list_data if p["id"] == post_id), None)
        assert post_in_list is not None

        get_resp = client.get(f"/posts/{post_id}")
        get_data = get_resp.json()

        assert post_in_list == get_data

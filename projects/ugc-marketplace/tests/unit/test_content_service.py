"""Unit tests for the ContentService (create_content, get_content, list_content)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

from ugc_marketplace.services.content_service import (
    Content,
    ContentFilters,
    ContentNotFoundError,
    ContentStatus,
    ContentType,
    ContentValidationError,
    PaginatedResult,
    PaginationParams,
    _content_store,
    create_content,
    get_content,
    list_content,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_content_store():
    """Ensure the in-memory content store is empty before and after each test."""
    _content_store.clear()
    yield
    _content_store.clear()


@pytest.fixture
def sample_content_data() -> Dict[str, Any]:
    """Return valid raw data for creating a content item."""
    return {
        "title": "Test Content",
        "description": "A test content item for unit testing",
        "content_type": "image",
        "creator_id": "creator-001",
        "tags": ["test", "sample"],
        "metadata": {"source": "unit_test"},
    }


@pytest.fixture
def sample_content(sample_content_data) -> Content:
    """Create and return a Content instance via the service."""
    return create_content(sample_content_data)


@pytest.fixture
def multiple_contents() -> List[Content]:
    """Create and return a list of Content instances for listing tests."""
    contents = []
    for i in range(5):
        data = {
            "title": f"Content {i}",
            "description": f"Description for content {i}",
            "content_type": "video" if i % 2 == 0 else "image",
            "creator_id": f"creator-{i % 2}",
            "tags": [f"tag-{i}"],
        }
        contents.append(create_content(data))
    return contents


# ---------------------------------------------------------------------------
# Tests: create_content
# ---------------------------------------------------------------------------


class TestCreateContent:
    """Tests for create_content."""

    def test_create_content(self, sample_content_data):
        """Test that create_content returns a Content with correct fields."""
        result = create_content(sample_content_data)

        assert isinstance(result, Content)
        assert result.id is not None
        assert isinstance(result.id, str)
        assert result.title == "Test Content"
        assert result.description == "A test content item for unit testing"
        assert result.content_type == ContentType.IMAGE
        assert result.status == ContentStatus.DRAFT
        assert result.creator_id == "creator-001"
        assert result.tags == ["test", "sample"]
        assert result.metadata == {"source": "unit_test"}
        assert result.created_at is not None
        assert result.updated_at is not None

    def test_create_content_generates_unique_ids(self, sample_content_data):
        """Test that each call to create_content generates a unique ID."""
        content1 = create_content(sample_content_data)
        content2 = create_content(sample_content_data)

        assert content1.id != content2.id

    def test_create_content_stores_in_store(self, sample_content_data):
        """Test that created content is stored in the internal store."""
        content = create_content(sample_content_data)

        assert content.id in _content_store
        assert _content_store[content.id] is content

    def test_create_content_with_minimal_data(self):
        """Test creation with only required fields (no tags or metadata)."""
        data = {
            "title": "Minimal",
            "description": "Minimal content",
            "content_type": "text",
            "creator_id": "creator-002",
        }
        result = create_content(data)

        assert result.title == "Minimal"
        assert result.content_type == ContentType.TEXT
        assert result.tags == []
        assert result.metadata == {}

    def test_create_content_strips_whitespace(self):
        """Test that title and description are stripped of leading/trailing whitespace."""
        data = {
            "title": "  Padded Title  ",
            "description": "  Padded description  ",
            "content_type": "audio",
            "creator_id": "  creator-003  ",
        }
        result = create_content(data)

        assert result.title == "Padded Title"
        assert result.description == "Padded description"
        assert result.creator_id == "creator-003"

    def test_create_content_all_content_types(self):
        """Test creation with each supported content type."""
        for ct in ContentType:
            data = {
                "title": f"Content {ct.value}",
                "description": f"Description for {ct.value}",
                "content_type": ct.value,
                "creator_id": "creator-001",
            }
            result = create_content(data)
            assert result.content_type == ct

    def test_create_content_missing_title_raises_error(self):
        """Test that missing title raises ContentValidationError."""
        data = {
            "description": "Some description",
            "content_type": "image",
            "creator_id": "creator-001",
        }
        with pytest.raises(ContentValidationError, match="title"):
            create_content(data)

    def test_create_content_empty_title_raises_error(self):
        """Test that empty title raises ContentValidationError."""
        data = {
            "title": "",
            "description": "Some description",
            "content_type": "image",
            "creator_id": "creator-001",
        }
        with pytest.raises(ContentValidationError, match="title"):
            create_content(data)

    def test_create_content_whitespace_title_raises_error(self):
        """Test that whitespace-only title raises ContentValidationError."""
        data = {
            "title": "   ",
            "description": "Some description",
            "content_type": "image",
            "creator_id": "creator-001",
        }
        with pytest.raises(ContentValidationError, match="title"):
            create_content(data)

    def test_create_content_title_too_long_raises_error(self):
        """Test that title exceeding 200 chars raises ContentValidationError."""
        data = {
            "title": "x" * 201,
            "description": "Some description",
            "content_type": "image",
            "creator_id": "creator-001",
        }
        with pytest.raises(ContentValidationError, match="title"):
            create_content(data)

    def test_create_content_missing_description_raises_error(self):
        """Test that missing description raises ContentValidationError."""
        data = {
            "title": "Some title",
            "content_type": "image",
            "creator_id": "creator-001",
        }
        with pytest.raises(ContentValidationError, match="description"):
            create_content(data)

    def test_create_content_description_too_long_raises_error(self):
        """Test that description exceeding 5000 chars raises ContentValidationError."""
        data = {
            "title": "Some title",
            "description": "x" * 5001,
            "content_type": "image",
            "creator_id": "creator-001",
        }
        with pytest.raises(ContentValidationError, match="description"):
            create_content(data)

    def test_create_content_missing_content_type_raises_error(self):
        """Test that missing content_type raises ContentValidationError."""
        data = {
            "title": "Some title",
            "description": "Some description",
            "creator_id": "creator-001",
        }
        with pytest.raises(ContentValidationError, match="content_type"):
            create_content(data)

    def test_create_content_invalid_content_type_raises_error(self):
        """Test that invalid content_type raises ContentValidationError."""
        data = {
            "title": "Some title",
            "description": "Some description",
            "content_type": "invalid_type",
            "creator_id": "creator-001",
        }
        with pytest.raises(ContentValidationError, match="content_type"):
            create_content(data)

    def test_create_content_missing_creator_id_raises_error(self):
        """Test that missing creator_id raises ContentValidationError."""
        data = {
            "title": "Some title",
            "description": "Some description",
            "content_type": "image",
        }
        with pytest.raises(ContentValidationError, match="creator_id"):
            create_content(data)

    def test_create_content_empty_creator_id_raises_error(self):
        """Test that empty creator_id raises ContentValidationError."""
        data = {
            "title": "Some title",
            "description": "Some description",
            "content_type": "image",
            "creator_id": "",
        }
        with pytest.raises(ContentValidationError, match="creator_id"):
            create_content(data)

    def test_create_content_tags_not_list_raises_error(self):
        """Test that non-list tags raises ContentValidationError."""
        data = {
            "title": "Some title",
            "description": "Some description",
            "content_type": "image",
            "creator_id": "creator-001",
            "tags": "not-a-list",
        }
        with pytest.raises(ContentValidationError, match="tags"):
            create_content(data)

    def test_create_content_non_string_tag_raises_error(self):
        """Test that non-string tag in list raises ContentValidationError."""
        data = {
            "title": "Some title",
            "description": "Some description",
            "content_type": "image",
            "creator_id": "creator-001",
            "tags": ["valid", 123],
        }
        with pytest.raises(ContentValidationError, match="each tag must be a string"):
            create_content(data)

    def test_create_content_none_field_raises_error(self):
        """Test that None value for required field raises ContentValidationError."""
        data = {
            "title": None,
            "description": "Some description",
            "content_type": "image",
            "creator_id": "creator-001",
        }
        with pytest.raises(ContentValidationError, match="title"):
            create_content(data)


# ---------------------------------------------------------------------------
# Tests: get_content
# ---------------------------------------------------------------------------


class TestGetContent:
    """Tests for get_content."""

    def test_get_content(self, sample_content):
        """Test that get_content retrieves a previously created content item."""
        result = get_content(sample_content.id)

        assert isinstance(result, Content)
        assert result.id == sample_content.id
        assert result.title == sample_content.title
        assert result.description == sample_content.description
        assert result.content_type == sample_content.content_type
        assert result.status == sample_content.status
        assert result.creator_id == sample_content.creator_id
        assert result.tags == sample_content.tags
        assert result.metadata == sample_content.metadata

    def test_get_content_not_found_raises_error(self):
        """Test that get_content raises ContentNotFoundError for unknown ID."""
        fake_id = str(uuid.uuid4())

        with pytest.raises(ContentNotFoundError) as exc_info:
            get_content(fake_id)

        assert exc_info.value.content_id == fake_id

    def test_get_content_empty_string_raises_value_error(self):
        """Test that get_content with empty string raises ValueError."""
        with pytest.raises(ValueError, match="content_id"):
            get_content("")

    def test_get_content_whitespace_string_raises_value_error(self):
        """Test that get_content with whitespace-only string raises ValueError."""
        with pytest.raises(ValueError, match="content_id"):
            get_content("   ")

    def test_get_content_non_string_raises_value_error(self):
        """Test that get_content with non-string ID raises ValueError."""
        with pytest.raises(ValueError, match="content_id"):
            get_content(123)  # type: ignore[arg-type]

    def test_get_content_none_raises_value_error(self):
        """Test that get_content with None raises ValueError."""
        with pytest.raises(ValueError, match="content_id"):
            get_content(None)  # type: ignore[arg-type]

    def test_get_content_returns_same_object(self, sample_content):
        """Test that get_content returns the exact object stored."""
        result = get_content(sample_content.id)

        assert result is sample_content


# ---------------------------------------------------------------------------
# Tests: list_content
# ---------------------------------------------------------------------------


class TestListContent:
    """Tests for list_content."""

    def test_list_content_empty_store(self):
        """Test that list_content returns empty result when store is empty."""
        result = list_content()

        assert isinstance(result, PaginatedResult)
        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_pages == 0

    def test_list_content_returns_all(self, multiple_contents):
        """Test that list_content returns all items when no filters applied."""
        result = list_content()

        assert result.total == 5
        assert len(result.items) == 5
        assert result.page == 1
        assert result.page_size == 20
        assert result.total_pages == 1

    def test_list_content_sorted_newest_first(self, multiple_contents):
        """Test that list_content returns items sorted by created_at descending."""
        result = list_content()

        for i in range(len(result.items) - 1):
            assert result.items[i].created_at >= result.items[i + 1].created_at

    def test_list_content_filter_by_content_type(self, multiple_contents):
        """Test filtering by content_type."""
        filters = ContentFilters(content_type=ContentType.VIDEO)
        result = list_content(filters=filters)

        assert result.total == 3  # indices 0, 2, 4 are video
        for item in result.items:
            assert item.content_type == ContentType.VIDEO

    def test_list_content_filter_by_status(self, multiple_contents):
        """Test filtering by status."""
        filters = ContentFilters(status=ContentStatus.DRAFT)
        result = list_content(filters=filters)

        assert result.total == 5  # all are DRAFT by default
        for item in result.items:
            assert item.status == ContentStatus.DRAFT

    def test_list_content_filter_by_creator_id(self, multiple_contents):
        """Test filtering by creator_id."""
        filters = ContentFilters(creator_id="creator-0")
        result = list_content(filters=filters)

        assert result.total == 3  # indices 0, 2, 4 have creator-0
        for item in result.items:
            assert item.creator_id == "creator-0"

    def test_list_content_filter_by_tags(self, multiple_contents):
        """Test filtering by tags."""
        filters = ContentFilters(tags=["tag-0"])
        result = list_content(filters=filters)

        assert result.total == 1
        assert result.items[0].title == "Content 0"

    def test_list_content_filter_by_search_query(self, multiple_contents):
        """Test filtering by search query matching title."""
        filters = ContentFilters(search_query="Content 1")
        result = list_content(filters=filters)

        assert result.total == 1
        assert result.items[0].title == "Content 1"

    def test_list_content_filter_by_search_query_description(self, multiple_contents):
        """Test filtering by search query matching description."""
        filters = ContentFilters(search_query="Description for content 3")
        result = list_content(filters=filters)

        assert result.total == 1
        assert result.items[0].title == "Content 3"

    def test_list_content_filter_by_search_query_case_insensitive(self, multiple_contents):
        """Test that search query is case-insensitive."""
        filters = ContentFilters(search_query="CONTENT 2")
        result = list_content(filters=filters)

        assert result.total == 1
        assert result.items[0].title == "Content 2"

    def test_list_content_filter_no_match(self, multiple_contents):
        """Test that non-matching filter returns empty result."""
        filters = ContentFilters(search_query="nonexistent")
        result = list_content(filters=filters)

        assert result.total == 0
        assert result.items == []

    def test_list_content_pagination_first_page(self, multiple_contents):
        """Test pagination returns correct first page."""
        pagination = PaginationParams(page=1, page_size=2)
        result = list_content(pagination=pagination)

        assert result.total == 5
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 2
        assert result.total_pages == 3

    def test_list_content_pagination_second_page(self, multiple_contents):
        """Test pagination returns correct second page."""
        pagination = PaginationParams(page=2, page_size=2)
        result = list_content(pagination=pagination)

        assert result.total == 5
        assert len(result.items) == 2
        assert result.page == 2
        assert result.page_size == 2
        assert result.total_pages == 3

    def test_list_content_pagination_last_page(self, multiple_contents):
        """Test pagination returns correct last page with remaining items."""
        pagination = PaginationParams(page=3, page_size=2)
        result = list_content(pagination=pagination)

        assert result.total == 5
        assert len(result.items) == 1
        assert result.page == 3
        assert result.page_size == 2
        assert result.total_pages == 3

    def test_list_content_pagination_beyond_last_page(self, multiple_contents):
        """Test pagination beyond last page returns empty items."""
        pagination = PaginationParams(page=10, page_size=2)
        result = list_content(pagination=pagination)

        assert result.total == 5
        assert len(result.items) == 0
        assert result.page == 10
        assert result.total_pages == 3

    def test_list_content_pagination_invalid_page_raises_error(self):
        """Test that invalid page number raises ValueError."""
        with pytest.raises(ValueError, match="page"):
            PaginationParams(page=0, page_size=10)

    def test_list_content_pagination_invalid_page_size_raises_error(self):
        """Test that invalid page_size raises ValueError."""
        with pytest.raises(ValueError, match="page_size"):
            PaginationParams(page=1, page_size=0)

    def test_list_content_pagination_page_size_too_large_raises_error(self):
        """Test that page_size exceeding 100 raises ValueError."""
        with pytest.raises(ValueError, match="page_size"):
            PaginationParams(page=1, page_size=101)

    def test_list_content_with_filters_and_pagination(self, multiple_contents):
        """Test combining filters with pagination."""
        filters = ContentFilters(content_type=ContentType.VIDEO)
        pagination = PaginationParams(page=1, page_size=2)
        result = list_content(filters=filters, pagination=pagination)

        assert result.total == 3
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 2
        assert result.total_pages == 2
        for item in result.items:
            assert item.content_type == ContentType.VIDEO

    def test_list_content_default_pagination_params(self, multiple_contents):
        """Test that default pagination params are applied when not specified."""
        result = list_content()

        assert result.page == 1
        assert result.page_size == 20

    def test_list_content_default_filters(self, multiple_contents):
        """Test that default (empty) filters return all items."""
        result = list_content(filters=ContentFilters())

        assert result.total == 5

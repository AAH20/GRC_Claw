"""Tests for integration clients."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_discovery.integrations import (
    AnalyticsClient,
    ContentClient,
    UserProfileClient,
    VectorStoreClient,
)


class TestVectorStoreClient:
    """Tests for VectorStoreClient."""

    @pytest.fixture
    def client(self) -> VectorStoreClient:
        """Create vector store client.

        Returns:
            VectorStoreClient: Client instance.
        """
        return VectorStoreClient(base_url="http://localhost:8080")

    @pytest.mark.asyncio
    async def test_search(self, client: VectorStoreClient) -> None:
        """Test vector store search.

        Args:
            client: Vector store client.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"id": "1", "title": "Test", "score": 0.9}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            results = await client.search(query="test", limit=5)

            assert len(results) == 1
            assert results[0]["id"] == "1"

    @pytest.mark.asyncio
    async def test_upsert(self, client: VectorStoreClient) -> None:
        """Test vector store upsert.

        Args:
            client: Vector store client.
        """
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await client.upsert(documents=[{"id": "1", "text": "test"}])

            assert result is True


class TestUserProfileClient:
    """Tests for UserProfileClient."""

    @pytest.fixture
    def client(self) -> UserProfileClient:
        """Create user profile client.

        Returns:
            UserProfileClient: Client instance.
        """
        return UserProfileClient(redis_url="redis://localhost:6379/0")

    @pytest.mark.asyncio
    async def test_get_history(self, client: UserProfileClient) -> None:
        """Test getting user history.

        Args:
            client: User profile client.
        """
        mock_redis = AsyncMock()
        mock_redis.lrange.return_value = ['{"id": "1", "title": "Test"}']

        with patch.object(client, "_get_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_redis
            history = await client.get_history(user_id="user_1")

            assert len(history) == 1
            assert history[0]["id"] == "1"

    @pytest.mark.asyncio
    async def test_add_history(self, client: UserProfileClient) -> None:
        """Test adding to user history.

        Args:
            client: User profile client.
        """
        mock_redis = AsyncMock()

        with patch.object(client, "_get_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_redis
            result = await client.add_history(
                user_id="user_1",
                item={"id": "1", "title": "Test"},
            )

            assert result is True
            mock_redis.lpush.assert_called_once()


class TestAnalyticsClient:
    """Tests for AnalyticsClient."""

    @pytest.fixture
    def client(self) -> AnalyticsClient:
        """Create analytics client.

        Returns:
            AnalyticsClient: Client instance.
        """
        return AnalyticsClient(base_url="http://localhost:9090")

    @pytest.mark.asyncio
    async def test_get_volume(self, client: AnalyticsClient) -> None:
        """Test getting volume data.

        Args:
            client: Analytics client.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"date": "2024-01-01", "count": 100}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            data = await client.get_volume(topic="AI", days=7)

            assert len(data) == 1
            assert data[0]["count"] == 100

    @pytest.mark.asyncio
    async def test_get_related_topics(self, client: AnalyticsClient) -> None:
        """Test getting related topics.

        Args:
            client: Analytics client.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {"topics": ["ML", "DL"]}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            topics = await client.get_related_topics(topic="AI")

            assert "ML" in topics
            assert "DL" in topics


class TestContentClient:
    """Tests for ContentClient."""

    @pytest.fixture
    def client(self) -> ContentClient:
        """Create content client.

        Returns:
            ContentClient: Client instance.
        """
        return ContentClient(base_url="http://localhost:7070")

    @pytest.mark.asyncio
    async def test_get_features(self, client: ContentClient) -> None:
        """Test getting content features.

        Args:
            client: Content client.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "1",
            "title": "Test",
            "tags": ["python"],
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            features = await client.get_features(content_id="1")

            assert features["id"] == "1"
            assert "python" in features["tags"]

    @pytest.mark.asyncio
    async def test_get_by_tags(self, client: ContentClient) -> None:
        """Test getting content by tags.

        Args:
            client: Content client.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"id": "1", "title": "Test"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            results = await client.get_by_tags(tags=["python"], limit=5)

            assert len(results) == 1

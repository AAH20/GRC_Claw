"""Semantic caching system.

Provides intelligent caching of model responses based on semantic
similarity, reducing costs and latency for similar queries.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached response entry.

    Attributes:
        key: Cache key (hash of the query).
        query: Original query text.
        response: Cached response content.
        embedding: Semantic embedding vector.
        timestamp: When the entry was created.
        ttl_seconds: Time-to-live in seconds.
        access_count: Number of times this entry was accessed.
        last_accessed: Timestamp of last access.
        metadata: Additional metadata.
    """

    key: str
    query: str
    response: str
    embedding: List[float]
    timestamp: float
    ttl_seconds: float
    access_count: int = 0
    last_accessed: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if the entry has expired.

        Returns:
            True if the entry has exceeded its TTL.
        """
        return (time.time() - self.timestamp) > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Get the age of the entry in seconds.

        Returns:
            Seconds since the entry was created.
        """
        return time.time() - self.timestamp


class EmbeddingProvider(Protocol):
    """Protocol for embedding generation backends."""

    def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for text.

        Args:
            text: The text to embed.

        Returns:
            Embedding vector as a list of floats.
        """
        ...


class HashEmbeddingProvider:
    """Simple hash-based embedding provider (no external dependencies).

    Uses character n-gram hashing to produce deterministic embeddings.
    Suitable for development and testing; use a neural embedding
    model for production semantic similarity.
    """

    def __init__(self, dimensions: int = 128) -> None:
        """Initialize the hash embedding provider.

        Args:
            dimensions: Number of embedding dimensions.
        """
        self._dimensions = dimensions

    def embed(self, text: str) -> List[float]:
        """Generate a hash-based embedding.

        Args:
            text: The text to embed.

        Returns:
            Embedding vector.
        """
        vector = [0.0] * self._dimensions
        text_lower = text.lower()

        # Character trigrams
        for i in range(len(text_lower) - 2):
            trigram = text_lower[i:i + 3]
            idx = hash(trigram) % self._dimensions
            vector[idx] += 1.0

        # Word unigrams
        for word in text_lower.split():
            idx = hash(word) % self._dimensions
            vector[idx] += 2.0

        # L2 normalize
        magnitude = sum(x * x for x in vector) ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector


class SemanticCache:
    """Semantic cache for model responses.

    Caches responses based on semantic similarity rather than exact
    matching, enabling cache hits for paraphrased or similar queries.

    Example:
        >>> cache = SemanticCache(similarity_threshold=0.85)
        >>> cache.put("What is AI?", "AI is...", embedding=[0.1, 0.2])
        >>> result = cache.get("What is artificial intelligence?")
        >>> print(result.response if result else "Cache miss")
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        max_entries: int = 10_000,
        default_ttl_seconds: float = 3600,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ) -> None:
        """Initialize the semantic cache.

        Args:
            similarity_threshold: Minimum cosine similarity for cache hits
                (0.0-1.0).
            max_entries: Maximum number of cache entries.
            default_ttl_seconds: Default TTL for new entries.
            embedding_provider: Custom embedding provider. Uses hash-based
                provider if None.
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._similarity_threshold = similarity_threshold
        self._max_entries = max_entries
        self._default_ttl = default_ttl_seconds
        self._embedding_provider = embedding_provider or HashEmbeddingProvider()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "inserts": 0,
        }

    @property
    def stats(self) -> Dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with hits, misses, evictions, and inserts.
        """
        return dict(self._stats)

    @property
    def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of entries in the cache.
        """
        return len(self._cache)

    def get(self, query: str) -> Optional[CacheEntry]:
        """Get a cached response for a query.

        Uses semantic similarity to find the best matching entry.

        Args:
            query: The query to look up.

        Returns:
            Best matching CacheEntry or None if no match found.
        """
        with self._lock:
            self._cleanup_expired()

            if not self._cache:
                self._stats["misses"] += 1
                return None

            query_embedding = self._embedding_provider.embed(query)
            best_match: Optional[CacheEntry] = None
            best_similarity = 0.0

            for entry in self._cache.values():
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                if similarity > best_similarity and similarity >= self._similarity_threshold:
                    best_similarity = similarity
                    best_match = entry

            if best_match:
                self._stats["hits"] += 1
                best_match.access_count += 1
                best_match.last_accessed = time.time()
                logger.debug(
                    "Cache hit: similarity=%.3f, query='%s'",
                    best_similarity,
                    query[:50],
                )
                return best_match

            self._stats["misses"] += 1
            return None

    def put(
        self,
        query: str,
        response: str,
        embedding: Optional[List[float]] = None,
        ttl_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CacheEntry:
        """Store a response in the cache.

        Args:
            query: The original query.
            response: The response to cache.
            embedding: Optional pre-computed embedding. Computed from
                query if None.
            ttl_seconds: TTL override. Uses default if None.
            metadata: Additional metadata.

        Returns:
            The created CacheEntry.
        """
        with self._lock:
            if embedding is None:
                embedding = self._embedding_provider.embed(query)

            key = self._make_key(query)
            ttl = ttl_seconds or self._default_ttl

            entry = CacheEntry(
                key=key,
                query=query,
                response=response,
                embedding=embedding,
                timestamp=time.time(),
                ttl_seconds=ttl,
                last_accessed=time.time(),
                metadata=metadata or {},
            )

            # Evict if at capacity
            if len(self._cache) >= self._max_entries:
                self._evict_lru()

            self._cache[key] = entry
            self._stats["inserts"] += 1

            logger.debug("Cached response for query: %s", query[:50])
            return entry

    def invalidate(self, query: str) -> bool:
        """Invalidate a specific cache entry.

        Args:
            query: The query to invalidate.

        Returns:
            True if an entry was removed, False otherwise.
        """
        with self._lock:
            key = self._make_key(query)
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            logger.info("Semantic cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total_requests if total_requests > 0 else 0.0
            )
            return {
                **self._stats,
                "size": len(self._cache),
                "hit_rate": hit_rate,
                "total_requests": total_requests,
                "max_entries": self._max_entries,
                "similarity_threshold": self._similarity_threshold,
            }

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            a: First vector.
            b: Second vector.

        Returns:
            Cosine similarity between -1.0 and 1.0.
        """
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def _make_key(self, query: str) -> str:
        """Generate a cache key for a query.

        Args:
            query: The query text.

        Returns:
            Hash string for the query.
        """
        return hashlib.sha256(query.lower().strip().encode()).hexdigest()

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logger.debug("Cleaned up %d expired entries", len(expired_keys))

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return

        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]
        self._stats["evictions"] += 1
        logger.debug("Evicted LRU entry: %s", lru_key[:16])

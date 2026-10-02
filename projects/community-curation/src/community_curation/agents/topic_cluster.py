"""Topic clustering agent implementation."""

from __future__ import annotations

import structlog
from collections import defaultdict
from typing import Any

from community_curation.agents.base import BaseCurationAgent
from community_curation.config.settings import get_settings
from community_curation.models import ContentItem, TopicCluster

logger = structlog.get_logger(__name__)


class TopicClusterAgent(BaseCurationAgent[list[ContentItem], list[TopicCluster]]):
    """Agent that clusters content into topic groups using keyword similarity."""

    def __init__(self) -> None:
        """Initialize the topic cluster agent."""
        super().__init__(
            name="TopicClusterAgent",
            description="Clusters community content into coherent topic groups",
        )
        self.settings = get_settings()

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize text into a set of normalized terms.

        Args:
            text: Text to tokenize.

        Returns:
            Set of normalized terms.
        """
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "and", "but", "or", "not",
            "so", "if", "when", "while", "that", "this", "these", "those", "it",
        }
        words = text.lower().split()
        return {w.strip(".,!?;:\"'()[]{}") for w in words if len(w) > 2 and w not in stop_words}

    def _compute_similarity(self, terms1: set[str], terms2: set[str]) -> float:
        """Compute Jaccard similarity between two term sets.

        Args:
            terms1: First term set.
            terms2: Second term set.

        Returns:
            Jaccard similarity score.
        """
        if not terms1 or not terms2:
            return 0.0
        intersection = len(terms1 & terms2)
        union = len(terms1 | terms2)
        return intersection / union if union > 0 else 0.0

    def _cluster_items(self, items: list[ContentItem], max_clusters: int) -> list[list[ContentItem]]:
        """Cluster content items using agglomerative clustering.

        Args:
            items: Content items to cluster.
            max_clusters: Maximum number of clusters.

        Returns:
            List of clusters, each containing content items.
        """
        if not items:
            return []

        # Tokenize all items
        item_terms: list[tuple[ContentItem, set[str]]] = []
        for item in items:
            text = f"{item.title} {item.body}"
            item_terms.append((item, self._tokenize(text)))

        # Start with each item as its own cluster
        clusters: list[list[ContentItem]] = [[item] for item, _ in item_terms]
        cluster_terms: list[set[str]] = [terms for _, terms in item_terms]

        # Agglomerative clustering
        while len(clusters) > max_clusters:
            best_sim = -1.0
            best_i, best_j = -1, -1

            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    sim = self._compute_similarity(cluster_terms[i], cluster_terms[j])
                    if sim > best_sim:
                        best_sim = sim
                        best_i, best_j = i, j

            if best_sim < 0.1:
                break  # No more similar clusters

            # Merge clusters
            clusters[best_i].extend(clusters[best_j])
            cluster_terms[best_i] = cluster_terms[best_i] | cluster_terms[best_j]
            del clusters[best_j]
            del cluster_terms[best_j]

        return clusters

    def _generate_cluster_name(self, items: list[ContentItem]) -> str:
        """Generate a name for a cluster based on common terms.

        Args:
            items: Content items in the cluster.

        Returns:
            Cluster name.
        """
        all_terms: dict[str, int] = defaultdict(int)
        for item in items:
            for term in self._tokenize(f"{item.title} {item.body}"):
                all_terms[term] += 1

        # Get most common terms
        sorted_terms = sorted(all_terms.items(), key=lambda x: x[1], reverse=True)
        top_terms = [term for term, count in sorted_terms[:3] if count > 1]

        if top_terms:
            return " / ".join(term.title() for term in top_terms)
        return "General Discussion"

    def _compute_coherence(self, items: list[ContentItem]) -> float:
        """Compute cluster coherence score.

        Args:
            items: Content items in the cluster.

        Returns:
            Coherence score between 0 and 1.
        """
        if len(items) < 2:
            return 1.0

        term_sets = [self._tokenize(f"{item.title} {item.body}") for item in items]
        total_sim = 0.0
        count = 0

        for i in range(len(term_sets)):
            for j in range(i + 1, len(term_sets)):
                total_sim += self._compute_similarity(term_sets[i], term_sets[j])
                count += 1

        return total_sim / count if count > 0 else 0.0

    async def run(self, input_data: list[ContentItem]) -> list[TopicCluster]:
        """Cluster content into topic groups.

        Args:
            input_data: List of content items to cluster.

        Returns:
            List of topic clusters.
        """
        if not self.is_available:
            logger.warning("agent_unavailable", agent=self.name)
            return self._fallback_clusters(input_data)

        if not input_data:
            return []

        max_clusters = self.settings.max_cluster_count
        clusters = self._cluster_items(input_data, max_clusters)

        result: list[TopicCluster] = []
        for idx, cluster_items in enumerate(clusters):
            if not cluster_items:
                continue

            name = self._generate_cluster_name(cluster_items)
            coherence = self._compute_coherence(cluster_items)

            # Extract keywords
            all_terms: dict[str, int] = defaultdict(int)
            for item in cluster_items:
                for term in self._tokenize(f"{item.title} {item.body}"):
                    all_terms[term] += 1
            keywords = [term for term, _ in sorted(all_terms.items(), key=lambda x: x[1], reverse=True)[:10]]

            result.append(
                TopicCluster(
                    id=f"cluster_{idx}",
                    name=name,
                    description=f"Topic cluster with {len(cluster_items)} related items",
                    keywords=keywords,
                    content_ids=[item.id for item in cluster_items],
                    coherence_score=round(coherence, 4),
                    size=len(cluster_items),
                )
            )

        logger.info("content_clustered", count=len(result))
        return result

    def _fallback_clusters(self, items: list[ContentItem]) -> list[TopicCluster]:
        """Fallback clustering when agent is unavailable.

        Args:
            items: Content items to cluster.

        Returns:
            List of topic clusters.
        """
        if not items:
            return []

        # Simple source-based clustering
        by_source: dict[str, list[ContentItem]] = defaultdict(list)
        for item in items:
            by_source[item.source.value].append(item)

        clusters = []
        for idx, (source, source_items) in enumerate(by_source.items()):
            clusters.append(
                TopicCluster(
                    id=f"cluster_{idx}",
                    name=f"{source.replace('_', ' ').title()} Content",
                    description=f"Content from {source}",
                    keywords=[source],
                    content_ids=[item.id for item in source_items],
                    coherence_score=0.5,
                    size=len(source_items),
                )
            )
        return clusters

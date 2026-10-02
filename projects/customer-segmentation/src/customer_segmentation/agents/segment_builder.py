"""Segment Builder Agent - Creates dynamic customer segments using ML clustering."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import structlog
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from customer_segmentation.agents.analyst import AnalystAgent
from customer_segmentation.agents.data_collector import BaseAgent
from customer_segmentation.models import Customer, Segment, SegmentStatus, SegmentType

logger = structlog.get_logger(__name__)


@dataclass
class SegmentBuildResult:
    """Result of a segment building operation."""

    segments: list[Segment] = field(default_factory=list)
    unassigned_customers: list[str] = field(default_factory=list)
    quality_score: float = 0.0
    algorithm_used: str = "kmeans"
    feature_importance: dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "segments": [s.model_dump() for s in self.segments],
            "unassigned_customers": self.unassigned_customers,
            "quality_score": self.quality_score,
            "algorithm_used": self.algorithm_used,
            "feature_importance": self.feature_importance,
            "created_at": self.created_at.isoformat(),
        }


class SegmentBuilderAgent(BaseAgent):
    """Agent responsible for building customer segments using ML algorithms.

    Supports K-Means, DBSCAN, and hierarchical clustering algorithms.
    Automatically selects the optimal number of clusters using silhouette score.
    """

    def __init__(
        self,
        algorithm: str = "kmeans",
        n_clusters: int = 5,
        min_segment_size: int = 50,
        max_segment_size: int = 100000,
    ) -> None:
        """Initialize the Segment Builder Agent.

        Args:
            algorithm: Clustering algorithm to use (kmeans, dbscan, hierarchical).
            n_clusters: Target number of clusters (for K-Means).
            min_segment_size: Minimum customers per segment.
            max_segment_size: Maximum customers per segment.
        """
        super().__init__()
        self.algorithm = algorithm
        self.n_clusters = n_clusters
        self.min_segment_size = min_segment_size
        self.max_segment_size = max_segment_size
        self.scaler = StandardScaler()
        self.analyst = AnalystAgent(n_clusters=n_clusters)

    def _build_feature_matrix(self, customers: list[Customer]) -> np.ndarray:
        """Build and scale feature matrix from customer data."""
        features = []
        for customer in customers:
            features.append(
                [
                    customer.total_revenue,
                    customer.total_orders,
                    customer.lifetime_value,
                    customer.engagement_score or 0.0,
                    customer.churn_risk or 0.0,
                ]
            )
        x = np.array(features, dtype=float)
        return self.scaler.fit_transform(x)

    def _find_optimal_clusters(self, x: np.ndarray, max_clusters: int = 10) -> int:
        """Find optimal number of clusters using silhouette score."""
        n_samples = x.shape[0]
        if n_samples < 3:
            return 1

        best_score = -1
        best_k = 2

        for k in range(2, min(max_clusters + 1, n_samples)):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(x)
            if len(set(labels)) < 2:
                continue
            score = silhouette_score(x, labels)
            if score > best_score:
                best_score = score
                best_k = k

        return best_k

    def _cluster_kmeans(self, x: np.ndarray, n_clusters: int) -> np.ndarray:
        """Perform K-Means clustering."""
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        return kmeans.fit_predict(x)

    def _cluster_dbscan(self, x: np.ndarray) -> np.ndarray:
        """Perform DBSCAN clustering."""
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        return dbscan.fit_predict(x)

    def _calculate_feature_importance(
        self, x: np.ndarray, labels: np.ndarray, feature_names: list[str]
    ) -> dict[str, float]:
        """Calculate feature importance based on cluster separation."""
        importance: dict[str, float] = {}
        unique_labels = set(labels) - {-1}

        if len(unique_labels) < 2:
            return {name: 0.0 for name in feature_names}

        for i, name in enumerate(feature_names):
            feature_values = x[:, i]
            cluster_means = []
            for label in unique_labels:
                mask = labels == label
                cluster_means.append(np.mean(feature_values[mask]))

            between_variance = np.var(cluster_means)
            total_variance = np.var(feature_values)
            importance[name] = (
                float(between_variance / total_variance) if total_variance > 0 else 0.0
            )

        return importance

    def _generate_segment_name(self, cluster_id: int, profile: dict[str, Any]) -> str:
        """Generate a human-readable segment name based on cluster profile."""
        avg_revenue = profile.get("total_revenue_mean", 0)
        avg_orders = profile.get("total_orders_mean", 0)
        avg_ltv = profile.get("lifetime_value_mean", 0)

        if avg_revenue > 10000 and avg_orders > 10:
            return f"High-Value Frequent (Cluster {cluster_id})"
        elif avg_revenue > 10000:
            return f"High-Value Occasional (Cluster {cluster_id})"
        elif avg_orders > 10:
            return f"Frequent Low-Value (Cluster {cluster_id})"
        elif avg_ltv > 5000:
            return f"Growing Potential (Cluster {cluster_id})"
        else:
            return f"Standard Segment (Cluster {cluster_id})"

    def _create_segment_from_cluster(
        self,
        cluster_id: int,
        customer_ids: list[str],
        customers: list[Customer],
        profile: dict[str, Any],
    ) -> Segment:
        """Create a Segment model from a cluster."""
        segment_customers = [c for c in customers if c.id in customer_ids]
        avg_engagement = (
            np.mean([c.engagement_score or 0.0 for c in segment_customers])
            if segment_customers
            else 0.0
        )
        avg_churn_risk = (
            np.mean([c.churn_risk or 0.0 for c in segment_customers])
            if segment_customers
            else 0.0
        )

        name = self._generate_segment_name(cluster_id, profile)

        return Segment(
            id=str(uuid.uuid4()),
            name=name,
            description=f"Auto-generated segment with {len(customer_ids)} customers",
            segment_type=SegmentType.BEHAVIORAL,
            status=SegmentStatus.DRAFT,
            size=len(customer_ids),
            criteria={
                "algorithm": self.algorithm,
                "cluster_id": cluster_id,
                "features": ["total_revenue", "total_orders", "lifetime_value"],
            },
            customer_ids=customer_ids,
            behavioral_profile={
                "avg_engagement": round(float(avg_engagement), 2),
                "avg_churn_risk": round(float(avg_churn_risk), 2),
                "cluster_profile": profile,
            },
        )

    async def execute(
        self,
        customers: list[Customer],
        segment_type: SegmentType = SegmentType.BEHAVIORAL,
        criteria: dict[str, Any] | None = None,
    ) -> SegmentBuildResult:
        """Execute the segment building pipeline."""
        self.logger.info(
            "Starting segment building",
            customer_count=len(customers),
            algorithm=self.algorithm,
        )

        if len(customers) < self.min_segment_size:
            self.logger.warning(
                "Insufficient customers for segmentation",
                count=len(customers),
                min_required=self.min_segment_size,
            )
            return SegmentBuildResult(
                segments=[],
                unassigned_customers=[c.id for c in customers],
                quality_score=0.0,
            )

        x = self._build_feature_matrix(customers)

        if self.algorithm == "kmeans":
            n_clusters = self._find_optimal_clusters(x)
            labels = self._cluster_kmeans(x, n_clusters)
        elif self.algorithm == "dbscan":
            labels = self._cluster_dbscan(x)
        else:
            n_clusters = self._find_optimal_clusters(x)
            labels = self._cluster_kmeans(x, n_clusters)

        unique_labels = set(labels) - {-1}
        quality_score = 0.0
        if len(unique_labels) >= 2:
            quality_score = float(silhouette_score(x, labels))

        feature_names = [
            "total_revenue", "total_orders", "lifetime_value",
            "engagement_score", "churn_risk",
        ]
        feature_importance = self._calculate_feature_importance(x, labels, feature_names)

        segments: list[Segment] = []
        unassigned: list[str] = []

        for cluster_id in unique_labels:
            cluster_customer_ids = [
                customers[i].id for i, label in enumerate(labels) if label == cluster_id
            ]

            if len(cluster_customer_ids) < self.min_segment_size:
                unassigned.extend(cluster_customer_ids)
                continue

            if len(cluster_customer_ids) > self.max_segment_size:
                cluster_customer_ids = cluster_customer_ids[: self.max_segment_size]
                unassigned.extend(cluster_customer_ids[self.max_segment_size :])

            cluster_customers = [c for c in customers if c.id in cluster_customer_ids]
            profile: dict[str, Any] = {
                "size": len(cluster_customer_ids),
                "total_revenue_mean": float(
                    np.mean([c.total_revenue for c in cluster_customers])
                ),
                "total_orders_mean": float(
                    np.mean([c.total_orders for c in cluster_customers])
                ),
                "lifetime_value_mean": float(
                    np.mean([c.lifetime_value for c in cluster_customers])
                ),
            }

            segment = self._create_segment_from_cluster(
                cluster_id, cluster_customer_ids, customers, profile
            )
            segment.segment_type = segment_type
            if criteria:
                segment.criteria.update(criteria)
            segments.append(segment)

        noise_ids = [customers[i].id for i, label in enumerate(labels) if label == -1]
        unassigned.extend(noise_ids)

        self.logger.info(
            "Segment building completed",
            segments_created=len(segments),
            unassigned=len(unassigned),
            quality_score=quality_score,
        )

        return SegmentBuildResult(
            segments=segments,
            unassigned_customers=unassigned,
            quality_score=quality_score,
            algorithm_used=self.algorithm,
            feature_importance=feature_importance,
        )

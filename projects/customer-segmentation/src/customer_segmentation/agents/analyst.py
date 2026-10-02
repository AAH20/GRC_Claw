"""Analyst Agent - Performs RFM analysis, behavioral clustering, and trend detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import structlog
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from customer_segmentation.agents.data_collector import BaseAgent
from customer_segmentation.models import Customer, RFMProfile

logger = structlog.get_logger(__name__)


@dataclass
class AnalysisReport:
    """Comprehensive analysis report for a set of customers."""

    total_customers: int
    rfm_profiles: list[RFMProfile] = field(default_factory=list)
    clusters: dict[int, list[str]] = field(default_factory=dict)
    cluster_profiles: dict[int, dict[str, Any]] = field(default_factory=dict)
    trends: dict[str, Any] = field(default_factory=dict)
    outliers: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "total_customers": self.total_customers,
            "rfm_profiles": [p.model_dump() for p in self.rfm_profiles],
            "clusters": {str(k): v for k, v in self.clusters.items()},
            "cluster_profiles": {str(k): v for k, v in self.cluster_profiles.items()},
            "trends": self.trends,
            "outliers": self.outliers,
            "generated_at": self.generated_at.isoformat(),
        }


class AnalystAgent(BaseAgent):
    """Agent responsible for customer data analysis.

    Performs RFM (Recency, Frequency, Monetary) analysis, behavioral
    clustering using K-Means, and trend detection across customer segments.
    """

    def __init__(self, n_clusters: int = 5, rfm_quantiles: int = 5) -> None:
        """Initialize the Analyst Agent.

        Args:
            n_clusters: Number of clusters for K-Means clustering.
            rfm_quantiles: Number of quantile bins for RFM scoring.
        """
        super().__init__()
        self.n_clusters = n_clusters
        self.rfm_quantiles = rfm_quantiles
        self.scaler = StandardScaler()

    def calculate_rfm_scores(self, customers: list[Customer]) -> list[RFMProfile]:
        """Calculate RFM scores for each customer.

        Args:
            customers: List of customers to analyze.

        Returns:
            List of RFM profiles with scores and segment assignments.
        """
        if not customers:
            return []

        now = datetime.utcnow()
        profiles: list[RFMProfile] = []

        recencies: list[int] = []
        frequencies: list[int] = []
        monetaries: list[float] = []

        for customer in customers:
            last_order = customer.last_order_date or customer.created_at
            recency = (now - last_order).days
            recencies.append(recency)
            frequencies.append(customer.total_orders)
            monetaries.append(customer.total_revenue)

        recency_scores = self._score_recency(recencies, self.rfm_quantiles)
        frequency_scores = self._score_frequency(frequencies, self.rfm_quantiles)
        monetary_scores = self._score_monetary(monetaries, self.rfm_quantiles)

        for i, _customer in enumerate(customers):
            r_score = recency_scores[i]
            f_score = frequency_scores[i]
            m_score = monetary_scores[i]
            rfm_segment = self._classify_rfm_segment(r_score, f_score, m_score)

            profiles.append(
                RFMProfile(
                    recency_days=recencies[i],
                    frequency=frequencies[i],
                    monetary_value=monetaries[i],
                    r_score=r_score,
                    f_score=f_score,
                    m_score=m_score,
                    rfm_segment=rfm_segment,
                )
            )

        return profiles

    def _score_recency(self, values: list[int], n_quantiles: int) -> list[int]:
        """Score recency values (lower recency = higher score)."""
        if not values:
            return []
        arr = np.array(values, dtype=float)
        scores = np.zeros(len(arr), dtype=int)
        quantiles = np.quantile(arr, np.linspace(0, 1, n_quantiles + 1)[1:-1])
        for i, val in enumerate(arr):
            scores[i] = n_quantiles - np.searchsorted(quantiles, val, side="right")
        return scores.tolist()

    def _score_frequency(self, values: list[int], n_quantiles: int) -> list[int]:
        """Score frequency values (higher frequency = higher score)."""
        if not values:
            return []
        arr = np.array(values, dtype=float)
        scores = np.zeros(len(arr), dtype=int)
        quantiles = np.quantile(arr, np.linspace(0, 1, n_quantiles + 1)[1:-1])
        for i, val in enumerate(arr):
            scores[i] = np.searchsorted(quantiles, val, side="right") + 1
        return scores.tolist()

    def _score_monetary(self, values: list[float], n_quantiles: int) -> list[int]:
        """Score monetary values (higher value = higher score)."""
        if not values:
            return []
        arr = np.array(values, dtype=float)
        scores = np.zeros(len(arr), dtype=int)
        quantiles = np.quantile(arr, np.linspace(0, 1, n_quantiles + 1)[1:-1])
        for i, val in enumerate(arr):
            scores[i] = np.searchsorted(quantiles, val, side="right") + 1
        return scores.tolist()

    def _classify_rfm_segment(self, r: int, f: int, m: int) -> str:
        """Classify customer into an RFM segment based on scores."""
        avg = (r + f + m) / 3
        if r >= 4 and f >= 4 and m >= 4:
            return "champions"
        elif r >= 3 and f >= 3 and m >= 3:
            return "loyal_customers"
        elif r >= 4 and f <= 2:
            return "new_customers"
        elif r >= 3 and f >= 3 and m <= 2:
            return "potential_loyalists"
        elif r <= 2 and f >= 3:
            return "at_risk"
        elif r <= 2 and f <= 2 and m >= 3:
            return "cannot_lose_them"
        elif r <= 2 and f <= 2:
            return "lost"
        elif avg >= 3:
            return "promising"
        else:
            return "needs_attention"

    def perform_clustering(
        self, customers: list[Customer], features: list[str] | None = None
    ) -> dict[str, Any]:
        """Perform K-Means clustering on customer data."""
        if not customers:
            return {"clusters": {}, "profiles": {}}

        features = features or ["total_revenue", "total_orders", "lifetime_value"]

        x = np.array(
            [[getattr(c, f, 0.0) for f in features] for c in customers],
            dtype=float,
        )

        x_scaled = self.scaler.fit_transform(x)

        n_clusters = min(self.n_clusters, len(customers))
        if n_clusters < 2:
            return {
                "clusters": {0: [c.id for c in customers]},
                "profiles": {0: {"size": len(customers), "features": features}},
            }

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(x_scaled)

        clusters: dict[int, list[str]] = {}
        for i, label in enumerate(labels):
            clusters.setdefault(int(label), []).append(customers[i].id)

        cluster_profiles: dict[int, dict[str, Any]] = {}
        for cluster_id, customer_ids in clusters.items():
            cluster_customers = [c for c in customers if c.id in customer_ids]
            profile: dict[str, Any] = {
                "size": len(cluster_customers),
                "features": features,
                "centroid": kmeans.cluster_centers_[cluster_id].tolist(),
            }
            for feature in features:
                values = [getattr(c, feature, 0.0) for c in cluster_customers]
                profile[f"{feature}_mean"] = float(np.mean(values))
                profile[f"{feature}_std"] = float(np.std(values))
            cluster_profiles[cluster_id] = profile

        return {"clusters": clusters, "profiles": cluster_profiles}

    def detect_trends(self, customers: list[Customer]) -> dict[str, Any]:
        """Detect trends in customer behavior."""
        if not customers:
            return {}

        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        ninety_days_ago = now - timedelta(days=90)

        recent_customers = [
            c for c in customers
            if c.last_order_date and c.last_order_date >= thirty_days_ago
        ]
        older_customers = [
            c for c in customers
            if c.last_order_date and ninety_days_ago <= c.last_order_date < thirty_days_ago
        ]

        avg_recent_revenue = (
            np.mean([c.total_revenue for c in recent_customers]) if recent_customers else 0.0
        )
        avg_older_revenue = (
            np.mean([c.total_revenue for c in older_customers]) if older_customers else 0.0
        )

        revenue_trend = (
            ((avg_recent_revenue - avg_older_revenue) / avg_older_revenue * 100)
            if avg_older_revenue > 0
            else 0.0
        )

        churn_risks = [c.churn_risk for c in customers if c.churn_risk is not None]
        high_churn_count = sum(1 for r in churn_risks if r > 0.7)

        return {
            "revenue_trend_percent": round(revenue_trend, 2),
            "recent_active_customers": len(recent_customers),
            "older_active_customers": len(older_customers),
            "high_churn_risk_count": high_churn_count,
            "high_churn_risk_percent": (
                round(high_churn_count / len(churn_risks) * 100, 2) if churn_risks else 0.0
            ),
            "avg_recent_revenue": round(float(avg_recent_revenue), 2),
            "avg_older_revenue": round(float(avg_older_revenue), 2),
        }

    def detect_outliers(
        self, customers: list[Customer], threshold: float = 3.0
    ) -> list[str]:
        """Detect outlier customers based on revenue and order patterns."""
        if len(customers) < 3:
            return []

        revenues = np.array([c.total_revenue for c in customers], dtype=float)
        mean = np.mean(revenues)
        std = np.std(revenues)

        if std == 0:
            return []

        outliers = []
        for customer in customers:
            z_score = abs(customer.total_revenue - mean) / std
            if z_score > threshold:
                outliers.append(customer.id)

        return outliers

    async def execute(self, customers: list[Customer]) -> AnalysisReport:
        """Execute the full analysis pipeline."""
        self.logger.info("Starting analysis", customer_count=len(customers))

        rfm_profiles = self.calculate_rfm_scores(customers)
        self.logger.info("RFM analysis completed", profiles_count=len(rfm_profiles))

        clustering_result = self.perform_clustering(customers)
        self.logger.info(
            "Clustering completed",
            n_clusters=len(clustering_result.get("clusters", {})),
        )

        trends = self.detect_trends(customers)
        self.logger.info("Trend detection completed")

        outliers = self.detect_outliers(customers)
        self.logger.info("Outlier detection completed", outlier_count=len(outliers))

        report = AnalysisReport(
            total_customers=len(customers),
            rfm_profiles=rfm_profiles,
            clusters=clustering_result.get("clusters", {}),
            cluster_profiles=clustering_result.get("profiles", {}),
            trends=trends,
            outliers=outliers,
        )

        self.logger.info("Analysis pipeline completed")
        return report

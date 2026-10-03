"""
Custom Prometheus business metrics for UGC Marketplace.

This module provides a comprehensive set of business-level metrics
that go beyond standard HTTP/infrastructure metrics to track
marketplace-specific KPIs.

Usage:
    from monitoring.prometheus_metrics import BusinessMetrics
    metrics = BusinessMetrics()
    metrics.record_content_upload(content_type="video", size_bytes=1024)
"""

from __future__ import annotations

from typing import Any

from prometheus_client import (CollectorRegistry, Counter, Gauge, Histogram,
                               Info, generate_latest)

# Registry for all custom metrics
REGISTRY = CollectorRegistry()


class BusinessMetrics:
    """Custom business metrics for UGC Marketplace.

    Tracks marketplace-specific KPIs:
    - Content lifecycle (upload, moderation, publish, license)
    - Creator economy (earnings, subscriptions, tips)
    - Quality signals (scores, flags, appeals)
    - Discovery & engagement (views, clicks, shares)
    - Fraud & safety (detection rate, false positives)
    """

    def __init__(self, registry: CollectorRegistry = REGISTRY) -> None:
        self._registry = registry
        self._init_metrics()

    def _init_metrics(self) -> None:
        # --- Content Lifecycle ---
        self.content_uploads_total = Counter(
            "ugc_content_uploads_total",
            "Total content uploads by type and status",
            ["content_type", "status"],
            registry=self._registry,
        )
        self.content_upload_size_bytes = Histogram(
            "ugc_content_upload_size_bytes",
            "Content upload size distribution",
            ["content_type"],
            buckets=[1024, 10240, 102400, 1048576, 10485760, 52428800, 104857600],
            registry=self._registry,
        )
        self.content_moderation_duration_seconds = Histogram(
            "ugc_content_moderation_duration_seconds",
            "Time spent in moderation pipeline",
            ["content_type", "decision"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self._registry,
        )
        self.content_publish_total = Counter(
            "ugc_content_publish_total",
            "Content published by type and visibility",
            ["content_type", "visibility"],
            registry=self._registry,
        )
        self.content_removed_total = Counter(
            "ugc_content_removed_total",
            "Content removed by reason",
            ["reason", "content_type"],
            registry=self._registry,
        )

        # --- Creator Economy ---
        self.creator_earnings_total = Counter(
            "ugc_creator_earnings_total",
            "Creator earnings by source and currency",
            ["source", "currency"],
            registry=self._registry,
        )
        self.creator_earnings_amount = Histogram(
            "ugc_creator_earnings_amount",
            "Creator earnings amount distribution",
            ["source"],
            buckets=[0.01, 0.10, 1.0, 10.0, 100.0, 1000.0],
            registry=self._registry,
        )
        self.subscriptions_active = Gauge(
            "ugc_subscriptions_active",
            "Active subscriptions by tier",
            ["tier"],
            registry=self._registry,
        )
        self.subscription_churn_total = Counter(
            "ugc_subscription_churn_total",
            "Subscription cancellations by tier and reason",
            ["tier", "reason"],
            registry=self._registry,
        )
        self.tips_total = Counter(
            "ugc_tips_total",
            "Tips sent by currency",
            ["currency"],
            registry=self._registry,
        )
        self.tips_amount = Histogram(
            "ugc_tips_amount",
            "Tip amount distribution",
            buckets=[0.5, 1.0, 5.0, 10.0, 25.0, 50.0, 100.0],
            registry=self._registry,
        )

        # --- Quality Signals ---
        self.quality_score = Histogram(
            "ugc_quality_score",
            "Content quality score distribution",
            ["content_type"],
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self._registry,
        )
        self.content_flags_total = Counter(
            "ugc_content_flags_total",
            "Content flags by type and severity",
            ["flag_type", "severity"],
            registry=self._registry,
        )
        self.content_appeals_total = Counter(
            "ugc_content_appeals_total",
            "Content appeals by outcome",
            ["outcome"],
            registry=self._registry,
        )
        self.moderation_accuracy = Gauge(
            "ugc_moderation_accuracy",
            "Moderation model accuracy score",
            ["model_version"],
            registry=self._registry,
        )

        # --- Discovery & Engagement ---
        self.content_views_total = Counter(
            "ugc_content_views_total",
            "Content views by type and source",
            ["content_type", "source"],
            registry=self._registry,
        )
        self.content_engagement_total = Counter(
            "ugc_content_engagement_total",
            "Content engagements by type",
            ["engagement_type"],
            registry=self._registry,
        )
        self.search_queries_total = Counter(
            "ugc_search_queries_total",
            "Search queries by result count bucket",
            ["result_bucket"],
            registry=self._registry,
        )
        self.search_latency_seconds = Histogram(
            "ugc_search_latency_seconds",
            "Search query latency",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self._registry,
        )
        self.recommendation_clicks_total = Counter(
            "ugc_recommendation_clicks_total",
            "Recommendation clicks by slot",
            ["slot"],
            registry=self._registry,
        )

        # --- Fraud & Safety ---
        self.fraud_detection_total = Counter(
            "ugc_fraud_detection_total",
            "Fraud detection results by type",
            ["detection_type", "action"],
            registry=self._registry,
        )
        self.fraud_score = Histogram(
            "ugc_fraud_score",
            "Fraud score distribution",
            ["content_type"],
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self._registry,
        )
        self.safety_violations_total = Counter(
            "ugc_safety_violations_total",
            "Safety violations by category",
            ["category", "severity"],
            registry=self._registry,
        )
        self.accounts_suspended_total = Counter(
            "ugc_accounts_suspended_total",
            "Account suspensions by reason",
            ["reason"],
            registry=self._registry,
        )

        # --- Licensing & Rights ---
        self.licensing_requests_total = Counter(
            "ugc_licensing_requests_total",
            "Licensing requests by action and status",
            ["action", "status"],
            registry=self._registry,
        )
        self.licensing_revenue_total = Counter(
            "ugc_licensing_revenue_total",
            "Licensing revenue by license type and currency",
            ["license_type", "currency"],
            registry=self._registry,
        )
        self.rights_claims_total = Counter(
            "ugc_rights_claims_total",
            "Rights claims by type and resolution",
            ["claim_type", "resolution"],
            registry=self._registry,
        )
        self.content_id_resolves_total = Counter(
            "ugc_content_id_resolves_total",
            "Content ID resolutions by match type",
            ["match_type"],
            registry=self._registry,
        )

        # --- Platform Health ---
        self.registered_users = Gauge(
            "ugc_registered_users",
            "Total registered users by status",
            ["status"],
            registry=self._registry,
        )
        self.active_users = Gauge(
            "ugc_active_users",
            "Active users by time window",
            ["window"],
            registry=self._registry,
        )
        self.api_rate_limit_hits_total = Counter(
            "ugc_api_rate_limit_hits_total",
            "API rate limit hits by endpoint and tier",
            ["endpoint", "tier"],
            registry=self._registry,
        )
        self.webhook_deliveries_total = Counter(
            "ugc_webhook_deliveries_total",
            "Webhook deliveries by event and status",
            ["event", "status"],
            registry=self._registry,
        )
        self.notifications_sent_total = Counter(
            "ugc_notifications_sent_total",
            "Notifications sent by channel and type",
            ["channel", "notification_type"],
            registry=self._registry,
        )

        # --- System Info ---
        self.build_info = Info(
            "ugc_build",
            "Build information",
            registry=self._registry,
        )

        # --- Content Delivery ---
        self.content_delivery_bandwidth_bytes = Histogram(
            "ugc_content_delivery_bandwidth_bytes",
            "Content delivery bandwidth by type",
            ["content_type", "cdn_provider"],
            buckets=[1048576, 10485760, 104857600, 1073741824],
            registry=self._registry,
        )
        self.content_streaming_quality_score = Gauge(
            "ugc_content_streaming_quality_score",
            "Streaming quality score by content type",
            ["content_type", "quality_tier"],
            registry=self._registry,
        )

        # --- API Endpoint Metrics ---
        self.api_endpoint_latency_seconds = Histogram(
            "ugc_api_endpoint_latency_seconds",
            "Per-endpoint API latency",
            ["endpoint", "method"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self._registry,
        )
        self.api_endpoint_requests_total = Counter(
            "ugc_api_endpoint_requests_total",
            "Per-endpoint API request count",
            ["endpoint", "method", "status"],
            registry=self._registry,
        )

        # --- Queue Depth ---
        self.queue_depth = Gauge(
            "ugc_queue_depth",
            "Queue depth by queue name",
            ["queue_name"],
            registry=self._registry,
        )

        # --- Feature Flags ---
        self.feature_flag_evaluations_total = Counter(
            "ugc_feature_flag_evaluations_total",
            "Feature flag evaluations by flag and variant",
            ["flag_name", "variant"],
            registry=self._registry,
        )

        # --- WebSocket ---
        self.websocket_connections_active = Gauge(
            "ugc_websocket_connections_active",
            "Active WebSocket connections by channel",
            ["channel"],
            registry=self._registry,
        )
        self.websocket_messages_total = Counter(
            "ugc_websocket_messages_total",
            "WebSocket messages by channel and type",
            ["channel", "message_type"],
            registry=self._registry,
        )

    # --- Recording Methods ---

    def record_content_upload(
        self, content_type: str, size_bytes: int, status: str = "success"
    ) -> None:
        self.content_uploads_total.labels(
            content_type=content_type, status=status
        ).inc()
        self.content_upload_size_bytes.labels(content_type=content_type).observe(
            size_bytes
        )

    def record_moderation(
        self, content_type: str, decision: str, duration_seconds: float
    ) -> None:
        self.content_moderation_duration_seconds.labels(
            content_type=content_type, decision=decision
        ).observe(duration_seconds)

    def record_content_publish(
        self, content_type: str, visibility: str = "public"
    ) -> None:
        self.content_publish_total.labels(
            content_type=content_type, visibility=visibility
        ).inc()

    def record_content_removal(self, reason: str, content_type: str) -> None:
        self.content_removed_total.labels(
            reason=reason, content_type=content_type
        ).inc()

    def record_creator_earnings(
        self, source: str, amount: float, currency: str = "USD"
    ) -> None:
        self.creator_earnings_total.labels(source=source, currency=currency).inc()
        self.creator_earnings_amount.labels(source=source).observe(amount)

    def record_quality_score(self, content_type: str, score: float) -> None:
        self.quality_score.labels(content_type=content_type).observe(score)

    def record_content_view(self, content_type: str, source: str = "feed") -> None:
        self.content_views_total.labels(content_type=content_type, source=source).inc()

    def record_engagement(self, engagement_type: str) -> None:
        self.content_engagement_total.labels(engagement_type=engagement_type).inc()

    def record_fraud_detection(
        self, detection_type: str, action: str, score: float, content_type: str
    ) -> None:
        self.fraud_detection_total.labels(
            detection_type=detection_type, action=action
        ).inc()
        self.fraud_score.labels(content_type=content_type).observe(score)

    def record_licensing_request(self, action: str, status: str = "success") -> None:
        self.licensing_requests_total.labels(action=action, status=status).inc()

    def record_licensing_revenue(
        self, license_type: str, amount: float, currency: str = "USD"
    ) -> None:
        self.licensing_revenue_total.labels(
            license_type=license_type, currency=currency
        ).inc(amount)

    def record_rights_claim(self, claim_type: str, resolution: str) -> None:
        self.rights_claims_total.labels(
            claim_type=claim_type, resolution=resolution
        ).inc()

    def record_content_id_resolve(self, match_type: str) -> None:
        self.content_id_resolves_total.labels(match_type=match_type).inc()

    def set_active_users(self, window: str, count: int) -> None:
        self.active_users.labels(window=window).set(count)

    def set_registered_users(self, status: str, count: int) -> None:
        self.registered_users.labels(status=status).set(count)

    def set_subscriptions_active(self, tier: str, count: int) -> None:
        self.subscriptions_active.labels(tier=tier).set(count)

    def set_moderation_accuracy(self, model_version: str, accuracy: float) -> None:
        self.moderation_accuracy.labels(model_version=model_version).set(accuracy)

    def record_api_rate_limit(self, endpoint: str, tier: str) -> None:
        self.api_rate_limit_hits_total.labels(endpoint=endpoint, tier=tier).inc()

    def record_webhook_delivery(self, event: str, status: str) -> None:
        self.webhook_deliveries_total.labels(event=event, status=status).inc()

    def record_notification(self, channel: str, notification_type: str) -> None:
        self.notifications_sent_total.labels(
            channel=channel, notification_type=notification_type
        ).inc()

    def record_safety_violation(self, category: str, severity: str) -> None:
        self.safety_violations_total.labels(category=category, severity=severity).inc()

    def record_account_suspension(self, reason: str) -> None:
        self.accounts_suspended_total.labels(reason=reason).inc()

    def record_content_flag(self, flag_type: str, severity: str) -> None:
        self.content_flags_total.labels(flag_type=flag_type, severity=severity).inc()

    def record_content_appeal(self, outcome: str) -> None:
        self.content_appeals_total.labels(outcome=outcome).inc()

    def record_search_query(self, result_count: int, latency_seconds: float) -> None:
        bucket = self._result_bucket(result_count)
        self.search_queries_total.labels(result_bucket=bucket).inc()
        self.search_latency_seconds.observe(latency_seconds)

    def record_recommendation_click(self, slot: str) -> None:
        self.recommendation_clicks_total.labels(slot=slot).inc()

    def record_subscription_churn(self, tier: str, reason: str) -> None:
        self.subscription_churn_total.labels(tier=tier, reason=reason).inc()

    def record_tip(self, amount: float, currency: str = "USD") -> None:
        self.tips_total.labels(currency=currency).inc()
        self.tips_amount.observe(amount)

    def set_build_info(self, **kwargs: Any) -> None:
        self.build_info.info(kwargs)

    @staticmethod
    def _result_bucket(count: int) -> str:
        if count == 0:
            return "0"
        elif count < 10:
            return "1-9"
        elif count < 100:
            return "10-99"
        elif count < 1000:
            return "100-999"
        else:
            return "1000+"


# Singleton instance
_business_metrics: BusinessMetrics | None = None


def get_business_metrics() -> BusinessMetrics:
    """Get or create the singleton BusinessMetrics instance."""
    global _business_metrics
    if _business_metrics is None:
        _business_metrics = BusinessMetrics()
    return _business_metrics


def get_metrics_registry() -> CollectorRegistry:
    """Get the metrics registry for integration with FastAPI /metrics endpoint."""
    return REGISTRY


def generate_metrics() -> bytes:
    """Generate Prometheus-format metrics output."""
    return generate_latest(REGISTRY)

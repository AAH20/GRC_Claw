#!/usr/bin/env python3
"""
GRC_Claw Metrics Aggregation Script
====================================
Aggregates metrics from multiple GRC_Claw services and exposes them
in Prometheus-compatible format. Runs as a sidecar or cron job.

Metrics collected:
- Request rate, error rate, latency (p50/p95/p99) per service
- Decision outcomes (allow/deny/error) from PDP
- Evidence collection throughput
- Compliance score distribution
- Resource utilization (CPU, memory) per component
- Kafka consumer lag
- Database connection pool status

Usage:
    python metrics_aggregator.py --port 9091 --interval 15
    python metrics_aggregator.py --once  # Single scrape, output to stdout
"""

import argparse
import json
import os
import sys
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import urlopen
from urllib.error import URLError


# ── Configuration ───────────────────────────────────────────────────────────

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
METRICS_PORT = int(os.getenv("METRICS_PORT", "9091"))
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "15"))
SERVICE_DISCOVERY_URL = os.getenv("SERVICE_DISCOVERY_URL", "http://kubernetes:443")

# GRC_Claw service endpoints
GRC_CLAW_SERVICES = {
    "pdp-service": os.getenv("PDP_SERVICE_URL", "http://pdp-service:8080"),
    "pep-gateway": os.getenv("PEP_GATEWAY_URL", "http://pep-gateway:8080"),
    "policy-api": os.getenv("POLICY_API_URL", "http://policy-api:8080"),
    "evidence-collector": os.getenv("EVIDENCE_COLLECTOR_URL", "http://evidence-collector:8080"),
    "audit-service": os.getenv("AUDIT_SERVICE_URL", "http://audit-service:8080"),
    "compliance-engine": os.getenv("COMPLIANCE_ENGINE_URL", "http://compliance-engine:8080"),
    "enforcement-service": os.getenv("ENFORCEMENT_SERVICE_URL", "http://enforcement-service:8080"),
    "webhook-dispatcher": os.getenv("WEBHOOK_DISPATCHER_URL", "http://webhook-dispatcher:8080"),
}


# ── Data Models ─────────────────────────────────────────────────────────────

@dataclass
class MetricValue:
    """A single metric value with labels."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class ServiceMetrics:
    """Aggregated metrics for a single service."""
    service_name: str
    request_count: int = 0
    error_count: int = 0
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    active_connections: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    custom_metrics: Dict[str, float] = field(default_factory=dict)


# ── Prometheus Query Client ─────────────────────────────────────────────────

class PrometheusClient:
    """Simple Prometheus HTTP API client."""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def query(self, promql: str) -> List[Dict[str, Any]]:
        """Execute an instant PromQL query and return results."""
        url = f"{self.base_url}/api/v1/query?query={self._encode(promql)}"
        try:
            with urlopen(url, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode())
                if data.get("status") == "success":
                    return data.get("data", {}).get("result", [])
        except (URLError, Exception) as e:
            print(f"Prometheus query failed: {e}", file=sys.stderr)
        return []

    def query_range(self, promql: str, start: float, end: float, step: str = "15s") -> List[Dict[str, Any]]:
        """Execute a range PromQL query."""
        url = (
            f"{self.base_url}/api/v1/query_range"
            f"?query={self._encode(promql)}"
            f"&start={start}&end={end}&step={step}"
        )
        try:
            with urlopen(url, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode())
                if data.get("status") == "success":
                    return data.get("data", {}).get("result", [])
        except (URLError, Exception) as e:
            print(f"Prometheus range query failed: {e}", file=sys.stderr)
        return []

    @staticmethod
    def _encode(promql: str) -> str:
        """URL-encode a PromQL query."""
        from urllib.parse import quote
        return quote(promql, safe="")


# ── Metrics Collector ───────────────────────────────────────────────────────

class MetricsCollector:
    """Collects and aggregates metrics from GRC_Claw services."""

    def __init__(self, prometheus_url: str = PROMETHEUS_URL):
        self.prometheus = PrometheusClient(prometheus_url)
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: float = 0
        self._cache_ttl: float = 10  # seconds

    def collect_all(self) -> List[MetricValue]:
        """Collect all metrics and return as a flat list."""
        metrics: List[MetricValue] = []

        # Service-level metrics
        metrics.extend(self._collect_request_metrics())
        metrics.extend(self._collect_latency_metrics())
        metrics.extend(self._collect_error_metrics())
        metrics.extend(self._collect_decision_metrics())
        metrics.extend(self._collect_evidence_metrics())
        metrics.extend(self._collect_compliance_metrics())
        metrics.extend(self._collect_resource_metrics())
        metrics.extend(self._collect_kafka_metrics())
        metrics.extend(self._collect_database_metrics())

        return metrics

    def _collect_request_metrics(self) -> List[MetricValue]:
        """Collect request rate per service."""
        results = self.prometheus.query(
            'sum by (service) (rate(http_requests_total[5m]))'
        )
        return [
            MetricValue(
                name="grc_request_rate",
                value=float(r["value"][1]),
                labels={"service": r["metric"].get("service", "unknown")},
            )
            for r in results
        ]

    def _collect_latency_metrics(self) -> List[MetricValue]:
        """Collect latency percentiles per service."""
        metrics: List[MetricValue] = []
        for percentile, label in [("50", "p50"), ("95", "p95"), ("99", "p99")]:
            results = self.prometheus.query(
                f'histogram_quantile(0.{percentile}, '
                f'sum by (service, le) (rate(http_request_duration_seconds_bucket[5m])))'
            )
            for r in results:
                metrics.append(MetricValue(
                    name="grc_request_duration_seconds",
                    value=float(r["value"][1]),
                    labels={
                        "service": r["metric"].get("service", "unknown"),
                        "quantile": label,
                    },
                ))
        return metrics

    def _collect_error_metrics(self) -> List[MetricValue]:
        """Collect error rate per service."""
        results = self.prometheus.query(
            'sum by (service) (rate(http_requests_total{status=~"5.."}[5m]))'
        )
        return [
            MetricValue(
                name="grc_error_rate",
                value=float(r["value"][1]),
                labels={"service": r["metric"].get("service", "unknown")},
            )
            for r in results
        ]

    def _collect_decision_metrics(self) -> List[MetricValue]:
        """Collect PDP decision outcomes."""
        metrics: List[MetricValue] = []

        # Total decisions
        results = self.prometheus.query('sum by (outcome) (grc_decision_total)')
        for r in results:
            metrics.append(MetricValue(
                name="grc_decision_total",
                value=float(r["value"][1]),
                labels={"outcome": r["metric"].get("outcome", "unknown")},
            ))

        # Decision rate
        results = self.prometheus.query(
            'sum by (outcome) (rate(grc_decision_total[5m]))'
        )
        for r in results:
            metrics.append(MetricValue(
                name="grc_decision_rate",
                value=float(r["value"][1]),
                labels={"outcome": r["metric"].get("outcome", "unknown")},
            ))

        return metrics

    def _collect_evidence_metrics(self) -> List[MetricValue]:
        """Collect evidence collection metrics."""
        metrics: List[MetricValue] = []

        # Evidence collection rate
        results = self.prometheus.query(
            'sum(rate(grc_evidence_collected_total[5m]))'
        )
        for r in results:
            metrics.append(MetricValue(
                name="grc_evidence_collection_rate",
                value=float(r["value"][1]),
                labels={},
            ))

        # Evidence processing latency
        results = self.prometheus.query(
            'histogram_quantile(0.99, '
            'sum by (le) (rate(grc_evidence_processing_duration_seconds_bucket[5m])))'
        )
        for r in results:
            metrics.append(MetricValue(
                name="grc_evidence_processing_duration_seconds",
                value=float(r["value"][1]),
                labels={"quantile": "p99"},
            ))

        return metrics

    def _collect_compliance_metrics(self) -> List[MetricValue]:
        """Collect compliance score metrics."""
        metrics: List[MetricValue] = []

        # Average compliance score
        results = self.prometheus.query('avg(grc_compliance_score)')
        for r in results:
            metrics.append(MetricValue(
                name="grc_compliance_score_avg",
                value=float(r["value"][1]),
                labels={},
            ))

        # Compliance score by framework
        results = self.prometheus.query(
            'avg by (framework) (grc_compliance_score)'
        )
        for r in results:
            metrics.append(MetricValue(
                name="grc_compliance_score",
                value=float(r["value"][1]),
                labels={"framework": r["metric"].get("framework", "unknown")},
            ))

        return metrics

    def _collect_resource_metrics(self) -> List[MetricValue]:
        """Collect resource utilization metrics."""
        metrics: List[MetricValue] = []

        # CPU usage
        results = self.prometheus.query(
            'sum by (pod) (rate(container_cpu_usage_seconds_total{namespace=~"grc-claw-.*"}[5m]))'
        )
        for r in results:
            metrics.append(MetricValue(
                name="grc_cpu_usage_seconds",
                value=float(r["value"][1]),
                labels={"pod": r["metric"].get("pod", "unknown")},
            ))

        # Memory usage
        results = self.prometheus.query(
            'sum by (pod) (container_memory_working_set_bytes{namespace=~"grc-claw-.*"})'
        )
        for r in results:
            metrics.append(MetricValue(
                name="grc_memory_usage_bytes",
                value=float(r["value"][1]),
                labels={"pod": r["metric"].get("pod", "unknown")},
            ))

        return metrics

    def _collect_kafka_metrics(self) -> List[MetricValue]:
        """Collect Kafka consumer metrics."""
        metrics: List[MetricValue] = []

        # Consumer lag
        results = self.prometheus.query(
            'sum by (topic, consumer_group) (kafka_consumer_group_lag)'
        )
        for r in results:
            metrics.append(MetricValue(
                name="grc_kafka_consumer_lag",
                value=float(r["value"][1]),
                labels={
                    "topic": r["metric"].get("topic", "unknown"),
                    "consumer_group": r["metric"].get("consumer_group", "unknown"),
                },
            ))

        # Under-replicated partitions
        results = self.prometheus.query(
            'sum(kafka_server_replicamanager_underreplicatedpartitions)'
        )
        for r in results:
            metrics.append(MetricValue(
                name="grc_kafka_under_replicated_partitions",
                value=float(r["value"][1]),
                labels={},
            ))

        return metrics

    def _collect_database_metrics(self) -> List[MetricValue]:
        """Collect database metrics."""
        metrics: List[MetricValue] = []

        # PostgreSQL connections
        results = self.prometheus.query(
            'sum by (database) (pg_stat_activity_count)'
        )
        for r in results:
            metrics.append(MetricValue(
                name="grc_db_connections_active",
                value=float(r["value"][1]),
                labels={"database": r["metric"].get("database", "unknown")},
            ))

        # Replication lag
        results = self.prometheus.query('pg_replication_lag_seconds')
        for r in results:
            metrics.append(MetricValue(
                name="grc_db_replication_lag_seconds",
                value=float(r["value"][1]),
                labels={"instance": r["metric"].get("instance", "unknown")},
            ))

        return metrics


# ── Prometheus Format Exporter ───────────────────────────────────────────────

def format_prometheus(metrics: List[MetricValue]) -> str:
    """Format metrics in Prometheus text exposition format."""
    # Group by metric name
    grouped: Dict[str, List[MetricValue]] = defaultdict(list)
    for m in metrics:
        grouped[m.name].append(m)

    lines: List[str] = []
    for name, values in sorted(grouped.items()):
        # HELP and TYPE lines
        lines.append(f"# HELP {name} GRC_Claw aggregated metric")
        lines.append(f"# TYPE {name} gauge")

        for v in values:
            if v.labels:
                label_str = ",".join(
                    f'{k}="{self_escape(v)}"' for k, v in sorted(v.labels.items())
                )
                lines.append(f"{name}{{{label_str}}} {v.value}")
            else:
                lines.append(f"{name} {v.value}")

        lines.append("")  # Empty line between metric groups

    return "\n".join(lines)


def self_escape(value: str) -> str:
    """Escape special characters in label values."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


# ── HTTP Server ─────────────────────────────────────────────────────────────

class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint."""

    collector: MetricsCollector = None  # Set by server

    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.end_headers()
            metrics = self.collector.collect_all()
            output = format_prometheus(metrics)
            self.wfile.write(output.encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server(port: int, prometheus_url: str):
    """Run the metrics aggregation HTTP server."""
    collector = MetricsCollector(prometheus_url)
    MetricsHandler.collector = collector

    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    print(f"Metrics aggregator listening on :{port}/metrics")
    print(f"Prometheus backend: {prometheus_url}")
    server.serve_forever()


# ── Single Scrape Mode ──────────────────────────────────────────────────────

def run_once(prometheus_url: str):
    """Run a single metrics scrape and output to stdout."""
    collector = MetricsCollector(prometheus_url)
    metrics = collector.collect_all()
    print(format_prometheus(metrics))


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GRC_Claw Metrics Aggregator")
    parser.add_argument("--port", type=int, default=METRICS_PORT, help="HTTP port")
    parser.add_argument("--interval", type=int, default=SCRAPE_INTERVAL, help="Scrape interval")
    parser.add_argument("--prometheus-url", default=PROMETHEUS_URL, help="Prometheus URL")
    parser.add_argument("--once", action="store_true", help="Single scrape to stdout")
    args = parser.parse_args()

    if args.once:
        run_once(args.prometheus_url)
    else:
        run_server(args.port, args.prometheus_url)


if __name__ == "__main__":
    main()

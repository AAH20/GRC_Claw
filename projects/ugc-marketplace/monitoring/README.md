# UGC Marketplace — Monitoring & Observability

Production-grade monitoring, logging, and distributed tracing for the UGC Marketplace platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        UGC Marketplace Stack                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │   API    │  │   DB     │  │  Redis   │  │  Kafka   │          │
│  │ (FastAPI)│  │(Postgres)│  │  (Cache) │  │(Messaging│          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │              │                 │
│       └──────────────┴──────────────┴──────────────┘                │
│                              │                                      │
│                    ┌─────────▼─────────┐                            │
│                    │   Prometheus      │                            │
│                    │   (Metrics)       │                            │
│                    └─────────┬─────────┘                            │
│                              │                                      │
│                    ┌─────────▼─────────┐                            │
│                    │     Grafana       │                            │
│                    │   (Dashboards)    │                            │
│                    └───────────────────┘                            │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Logging Pipeline                          │  │
│  │  App Logs → Fluentd → Elasticsearch → Kibana                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   Tracing Pipeline                          │  │
│  │  App Spans → Jaeger Agent → Jaeger Collector → ES → UI     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

| Component | Purpose | Port | Endpoint |
|-----------|---------|------|----------|
| Prometheus | Metrics collection & alerting | 9090 | http://localhost:9090 |
| Grafana | Visualization & dashboards | 3000 | http://localhost:3000 |
| Alertmanager | Alert routing & notification | 9093 | http://localhost:9093 |
| Fluentd | Log aggregation | 24224 | — |
| Jaeger | Distributed tracing | 16686 | http://localhost:16686 |
| Elasticsearch | Log & trace storage | 9200 | http://localhost:9200 |
| Kibana | Log exploration | 5601 | http://localhost:5601 |

## Quick Start

### 1. Start the monitoring stack

```bash
cd ~/GRC_Claw/projects/ugc-marketplace/monitoring
docker-compose up -d
```

### 2. Verify services are running

```bash
docker-compose ps
curl http://localhost:9090/-/healthy   # Prometheus
curl http://localhost:3000/api/health   # Grafana
curl http://localhost:16686/            # Jaeger
```

### 3. Access Grafana

- URL: http://localhost:3000
- Default credentials: `admin` / `admin`
- Import the dashboard from `grafana/dashboards/ugc-marketplace.json`

### 4. Configure Prometheus targets

Edit `prometheus.yml` to match your environment:

```yaml
scrape_configs:
  - job_name: ugc-marketplace-api
    static_configs:
      - targets:
          - api:8000  # Change to your API host:port
```

### 5. Load alert rules

Alert rules are in `alerts/alert-rules.yml`. Prometheus auto-loads them via:

```yaml
rule_files:
  - /etc/prometheus/alerts/*.yml
```

## File Structure

```
monitoring/
├── prometheus.yml              # Prometheus scrape configuration
├── README.md                   # This file
├── alerts/
│   └── alert-rules.yml         # Prometheus alert rules
├── grafana/
│   └── dashboards/
│       └── ugc-marketplace.json  # Grafana dashboard
├── logging/
│   └── fluentd.conf            # Fluentd log aggregation config
└── tracing/
    └── jaeger.yml              # Jaeger distributed tracing config
```

## Metrics

### Application Metrics (exposed at `/metrics`)

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by status |
| `http_request_duration_seconds` | Histogram | Request latency distribution |
| `http_request_size_bytes` | Histogram | Request payload size |
| `http_response_size_bytes` | Histogram | Response payload size |
| `active_connections` | Gauge | Current active connections |
| `db_connection_pool_size` | Gauge | Database connection pool size |
| `db_connection_pool_available` | Gauge | Available DB connections |
| `cache_hits_total` | Counter | Cache hit count |
| `cache_misses_total` | Counter | Cache miss count |
| `kafka_messages_consumed_total` | Counter | Kafka messages consumed |
| `kafka_messages_produced_total` | Counter | Kafka messages produced |
| `moderation_queue_depth` | Gauge | Pending moderation items |
| `licensing_operations_total` | Counter | Licensing operations |
| `fraud_detection_score` | Histogram | Fraud score distribution |

### Infrastructure Metrics

| Source | Metrics |
|--------|---------|
| node-exporter | CPU, memory, disk, network |
| cadvisor | Container-level resource usage |
| postgres-exporter | Connections, queries, replication |
| redis-exporter | Memory, connections, evictions |
| kafka-exporter | Consumer lag, partitions, throughput |

## Alert Rules

### Critical Alerts

| Alert | Condition | Duration |
|-------|-----------|----------|
| ServiceDown | `up == 0` | 1m |
| APIServiceDown | API unreachable | 30s |
| DatabaseDown | PostgreSQL unreachable | 30s |
| RedisDown | Redis unreachable | 30s |
| KafkaDown | Kafka unreachable | 30s |
| HighErrorRate | 5xx rate > 5% | 2m |
| HighLatencyP99 | P99 > 5s | 5m |
| DiskWillFillIn4Hours | Predicted full | 1h |
| KafkaOfflinePartitions | Offline partitions | 5m |

### Warning Alerts

| Alert | Condition | Duration |
|-------|-----------|----------|
| HighClientErrorRate | 4xx rate > 10% | 5m |
| HighLatencyP95 | P95 > 2s | 5m |
| HighCPUUsage | CPU > 85% | 5m |
| HighMemoryUsage | Memory > 85% | 5m |
| HighDiskUsage | Disk > 85% | 5m |
| PostgreSQLHighConnections | Connections > 80% | 5m |
| RedisHighMemory | Memory > 85% | 5m |
| KafkaConsumerLag | Lag > 10,000 | 5m |
| FluentdBufferQueueHigh | Queue > 1000 | 5m |

## Logging

### Log Format

All services emit structured JSON logs via `structlog`:

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "logger": "ugc_marketplace.api",
  "event": "request_completed",
  "method": "POST",
  "path": "/api/v1/content",
  "status_code": 200,
  "duration_ms": 145,
  "trace_id": "abc123",
  "span_id": "def456"
}
```

### Log Pipeline

1. **Application** → stdout (JSON)
2. **Docker** → fluentd log driver
3. **Fluentd** → parse, enrich, filter
4. **Elasticsearch** → index & store
5. **Kibana** → explore & search

### Fluentd Configuration

Key features in `logging/fluentd.conf`:
- JSON parsing with timestamp extraction
- Trace context propagation (trace_id, span_id)
- Sensitive data masking (passwords, tokens, API keys)
- Error-level routing to S3 archive
- Buffered output with retry logic
- Multi-worker parallel processing

## Tracing

### Instrumentation

All services instrument with OpenTelemetry → Jaeger:

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-agent",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)
```

### Sampling Strategy

| Service | Sampling Rate |
|---------|--------------|
| ugc-marketplace-api | 50% |
| ugc-marketplace-moderation | 30% |
| ugc-marketplace-licensing | 30% |
| ugc-marketplace-fraud-detection | 30% |
| ugc-marketplace-db | 10% |
| ugc-marketplace-redis | 10% |
| ugc-marketplace-kafka | 20% |

### Trace Context Propagation

Traces propagate via HTTP headers:
- `X-B3-TraceId` — Trace identifier
- `X-B3-SpanId` — Span identifier
- `X-B3-ParentSpanId` — Parent span
- `X-B3-Sampled` — Sampling decision

## Grafana Dashboard

The dashboard (`grafana/dashboards/ugc-marketplace.json`) includes:

### Row 1: Overview
- Request rate (req/s)
- Error rate (%)
- P50/P95/P99 latency
- Active connections

### Row 2: Resources
- CPU usage (%)
- Memory usage (%)
- Disk usage (%)
- Network I/O

### Row 3: Database
- Connection pool utilization
- Query rate
- Slow queries
- Replication lag

### Row 4: Cache & Messaging
- Redis hit rate
- Redis memory usage
- Kafka consumer lag
- Kafka throughput

### Row 5: Business Metrics
- Moderation queue depth
- Licensing operations
- Fraud detection scores
- Content discovery rate

## Configuration Reference

### Prometheus

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: ugc-marketplace
    environment: production
```

### Alertmanager

```yaml
route:
  receiver: default
  group_by: [alertname, service]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: pagerduty
      continue: true
    - match:
        severity: warning
      receiver: slack
receivers:
  - name: default
    slack_configs:
      - api_url: ${SLACK_WEBHOOK_URL}
        channel: "#alerts"
  - name: pagerduty
    pagerduty_configs:
      - service_key: ${PAGERDUTY_KEY}
```

### Grafana Provisioning

```yaml
apiVersion: 1
providers:
  - name: ugc-marketplace
    orgId: 1
    folder: UGC Marketplace
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

## Troubleshooting

### Prometheus not scraping targets

```bash
# Check target status
curl http://localhost:9090/api/v1/targets

# Check Prometheus logs
docker logs prometheus

# Verify network connectivity
docker network inspect ugc-marketplace_default
```

### Grafana dashboard not loading

```bash
# Check Grafana logs
docker logs grafana

# Verify dashboard JSON is valid
cat grafana/dashboards/ugc-marketplace.json | python -m json.tool

# Check datasource configuration
curl -u admin:admin http://localhost:3000/api/datasources
```

### Alerts not firing

```bash
# Check alert rules are loaded
curl http://localhost:9090/api/v1/rules

# Check alertmanager configuration
curl http://localhost:9093/api/v1/status

# Test alert expression
curl http://localhost:9090/api/v1/query?query=up
```

### Logs not appearing in Kibana

```bash
# Check Fluentd status
docker logs fluentd

# Verify Elasticsearch connection
curl http://localhost:9200/_cat/indices?v

# Check index pattern in Kibana
# Management → Index Patterns → ugc-marketplace-*
```

### Traces not appearing in Jaeger

```bash
# Check Jaeger collector
curl http://localhost:14269/

# Verify agent is running
kubectl logs -l app=jaeger-agent

# Check sampling configuration
curl http://localhost:14269/api/sampling
```

## Production Checklist

- [ ] Change default Grafana credentials
- [ ] Configure Alertmanager receivers (Slack, PagerDuty, email)
- [ ] Set up TLS for all endpoints
- [ ] Configure persistent volumes for Prometheus data
- [ ] Set up Grafana authentication (OAuth/LDAP)
- [ ] Configure log retention policies
- [ ] Set up backup for Elasticsearch indices
- [ ] Configure network policies / security groups
- [ ] Set up monitoring for the monitoring stack itself
- [ ] Document runbooks for each alert
- [ ] Test alert routing and escalation
- [ ] Configure SLOs and error budgets
- [ ] Set up cross-region replication for critical data

## License

MIT

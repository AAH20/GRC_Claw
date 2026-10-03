# Gated Communities - Monitoring & Observability

Production-grade monitoring, logging, and tracing setup for the Gated Communities platform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Gated Communities Platform                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ API Gateway  │  │  Community   │  │  Membership  │              │
│  │   :8080      │  │  Service     │  │  Service     │              │
│  │              │  │   :8081      │  │   :8082      │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └────────────────┬┴─────────────────┘                       │
│                          │                                          │
│  ┌──────────────┐  ┌─────┴────────┐  ┌──────────────┐              │
│  │ Notification │  │  PostgreSQL  │  │    Redis     │              │
│  │  Service     │  │   :5432      │  │   :6379      │              │
│  │   :8083      │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌───────▼──────┐ ┌─────▼──────┐ ┌──────▼───────┐
            │  Prometheus  │ │   Jaeger   │ │   Fluentd    │
            │   :9090      │ │  :16686    │ │   :24224     │
            │              │ │            │ │              │
            └───────┬──────┘ └─────┬──────┘ └──────┬───────┘
                    │               │               │
            ┌───────▼──────┐ ┌─────▼──────┐ ┌──────▼───────┐
            │   Grafana   │ │    ES      │ │     ES       │
            │   :3000      │ │  :9200     │ │   :9200      │
            │              │ │ (traces)   │ │  (logs)      │
            └──────────────┘ └────────────┘ └──────────────┘
```

## Components

### 1. Prometheus (`prometheus.yml`)

Metrics collection and alerting engine.

| Setting | Value |
|---------|-------|
| Scrape Interval | 15s |
| Evaluation Interval | 15s |
| Retention | 15 days (default) |
| Port | 9090 |

**Scraped Targets:**
- `api-gateway:8080` — API Gateway metrics
- `community-service:8081` — Community service metrics
- `membership-service:8082` — Membership service metrics
- `notification-service:8083` — Notification service metrics
- `postgres-exporter:9187` — PostgreSQL metrics
- `redis-exporter:9121` — Redis metrics
- `node-exporter:9100` — Host-level metrics
- `jaeger:14269` — Jaeger tracing metrics
- `fluentd:24231` — Fluentd logging metrics

### 2. Grafana Dashboard (`grafana/dashboards/gated-communities.json`)

Comprehensive dashboard with the following sections:

| Section | Panels |
|---------|--------|
| Service Overview | Service status, request rate, error rate, latency percentiles |
| Infrastructure | CPU, memory, disk usage per instance |
| Database & Cache | PostgreSQL connections, replication lag, Redis memory |
| Business Metrics | Community creation rate, failed logins, webhook failures |
| Tracing & Logging | Jaeger span rate, Fluentd emission rate, buffer queue |

**Dashboard Variables:**
- `datasource` — Prometheus datasource selector
- `service` — Multi-select service filter
- `instance` — Multi-select instance filter

### 3. Alert Rules (`alerts/alert-rules.yml`)

Organized into 5 groups:

| Group | Alerts | Severity |
|-------|--------|----------|
| Service Availability | ServiceDown, HighErrorRate, HighLatency | Critical/Warning |
| Resource Utilization | HighCPU, HighMemory, DiskLow, DiskFillPrediction | Warning/Critical |
| Database | PostgreSQLDown, HighConnections, ReplicationLag, RedisDown, RedisHighMemory | Critical/Warning |
| Business Logic | CommunitySpike, FailedLogins, WebhookFailures | Warning |
| Observability | PrometheusTargetMissing, AlertmanagerDown, GrafanaDown, JaegerDown, FluentdBufferHigh | Critical/Warning |

### 4. Fluentd (`logging/fluentd.conf`)

Centralized log aggregation with structured JSON output.

**Log Sources:**
- Docker container logs (forward protocol, port 24224)
- Application logs (`/var/log/gated-communities/*.log`)
- Nginx access and error logs
- PostgreSQL logs
- Redis logs

**Features:**
- TLS encryption for log forwarding
- PII/sensitive data masking (passwords, tokens, API keys)
- Automatic log enrichment (environment, cluster, hostname)
- Error/warning log separation with dedicated indices
- Buffered output with retry logic
- Prometheus metrics endpoint

**Output:** Elasticsearch with index prefixes:
- `gated-communities-*` — Application logs
- `gated-communities-errors-*` — Error logs
- `gated-communities-warnings-*` — Warning logs
- `nginx-access-*` / `nginx-error-*` — Nginx logs
- `postgresql-*` — Database logs
- `redis-*` — Cache logs

### 5. Jaeger (`tracing/jaeger.yml`)

Distributed tracing with Elasticsearch storage.

**Configuration:**
- Storage: Elasticsearch (7-day retention)
- Sampling: Probabilistic (10% default, per-service overrides)
- Protocols: HTTP (16686), gRPC (14250), Thrift (6831/6832)
- UI: Enabled at port 16686

**Sampling Rates:**

| Service | Rate |
|---------|------|
| api-gateway | 50% |
| community-service | 30% |
| membership-service | 30% |
| notification-service | 20% |
| auth-service | 80% |
| webhook-service | 50% |

**Always Traced Operations:**
- `POST /api/v1/communities`
- `POST /api/v1/memberships`
- `POST /api/v1/auth/login`
- `createCommunity`
- `joinCommunity`
- `leaveCommunity`

## Quick Start

### Docker Compose

```yaml
version: "3.8"

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts/:/etc/prometheus/rules/
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=15d"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./grafana/dashboards/:/etc/grafana/provisioning/dashboards/
      - grafana-storage:/var/lib/grafana

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14250:14250"
    environment:
      - SPAN_STORAGE_TYPE=elasticsearch
      - ES_SERVER_URLS=http://elasticsearch:9200

  fluentd:
    image: fluent/fluentd:latest
    ports:
      - "24224:24224"
      - "24231:24231"
    volumes:
      - ./logging/fluentd.conf:/fluentd/etc/fluent.conf

  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

volumes:
  grafana-storage:
```

### Starting the Stack

```bash
# Start all monitoring services
docker-compose up -d

# Verify Prometheus is scraping targets
open http://localhost:9090/targets

# Access Grafana
open http://localhost:3000

# Access Jaeger UI
open http://localhost:16686

# Check Fluentd is receiving logs
curl http://localhost:24231/metrics
```

## Application Integration

### Instrumenting Services (Python Example)

```python
from prometheus_client import Counter, Histogram, start_http_server

# Start metrics server
start_http_server(8080)

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'method', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['service', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Usage in request handler
@REQUEST_LATENCY.labels(service='api-gateway', method='GET').time()
def handle_request():
    REQUEST_COUNT.labels(service='api-gateway', method='GET', status='200').inc()
```

### Distributed Tracing (Python Example)

```python
from jaeger_client import Config

config = Config(
    config={
        'sampler': {'type': 'probabilistic', 'param': 0.5},
        'local_agent': {'reporting_host': 'jaeger', 'reporting_port': 6831},
        'logging': True,
    },
    service_name='api-gateway',
)
tracer = config.initialize_tracer()

with tracer.start_span('create_community') as span:
    span.set_tag('user_id', user_id)
    span.set_tag('community_id', community_id)
    # ... business logic ...
```

### Structured Logging (Python Example)

```python
import json
import logging

logger = logging.getLogger('api-gateway')

def log_event(level, message, **extra):
    log_entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'level': level,
        'service': 'api-gateway',
        'message': message,
        **extra
    }
    print(json.dumps(log_entry))

# Usage
log_event('info', 'Community created', user_id='123', community_id='456', trace_id='abc')
```

## Alert Routing

Configure Alertmanager to route alerts to appropriate channels:

```yaml
# alertmanager.yml
route:
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      group_wait: 0s
    - match:
        severity: warning
      receiver: 'slack'
      group_wait: 1m

receivers:
  - name: 'default'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_KEY}'
```

## Maintenance

### Backup

```bash
# Backup Prometheus data
docker exec prometheus tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz /prometheus

# Backup Grafana dashboards
cp -r grafana/dashboards/ /backup/grafana-dashboards-$(date +%Y%m%d)/
```

### Log Rotation

```bash
# Elasticsearch index lifecycle policy
curl -X PUT "localhost:9200/_ilm/policy/gated-communities-policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": { "actions": {} },
      "delete": { "min_age": "30d", "actions": { "delete": {} } }
    }
  }
}'
```

### Scaling

- **Prometheus**: Use Thanos or Cortex for horizontal scaling and long-term storage
- **Jaeger**: Use Kafka-based ingestion pipeline for high-throughput scenarios
- **Fluentd**: Increase workers and buffer sizes; consider Fluent Bit for edge collection
- **Elasticsearch**: Use index templates and ILM policies for automatic data lifecycle management

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Prometheus targets down | Check network connectivity and service health endpoints |
| High Prometheus memory | Reduce scrape interval or add recording rules |
| Fluentd buffer overflow | Increase `queue_limit_length` and `total_limit_size` |
| Jaeger traces missing | Verify sampling rate and agent connectivity |
| Grafana dashboard empty | Check datasource configuration and Prometheus connectivity |
| Alert not firing | Verify rule syntax with `promtool check rules` |

## Security Considerations

- Enable TLS for all inter-service communication
- Use authentication for Grafana, Jaeger, and Elasticsearch
- Rotate API keys and credentials regularly
- Mask sensitive data in logs (passwords, tokens, PII)
- Network isolation: monitoring services on dedicated VPC/subnet
- Audit logging for all monitoring access

## License

Internal use only — Gated Communities Platform

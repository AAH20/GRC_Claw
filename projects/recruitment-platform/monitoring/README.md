# Recruitment Platform Monitoring Setup

This directory contains the complete monitoring, observability, and alerting setup for the Recruitment Platform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Recruitment Platform                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   API    │  │  Worker  │  │   DB     │  │  Redis   │       │
│  │  :8000   │  │  :8000   │  │  :5432   │  │  :6379   │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │             │
│       └──────────────┴──────────────┴──────────────┘             │
│                              │                                    │
│                    ┌─────────┴─────────┐                         │
│                    │   Prometheus      │                         │
│                    │     :9090         │                         │
│                    └─────────┬─────────┘                         │
│                              │                                    │
│              ┌───────────────┼───────────────┐                   │
│              │               │               │                    │
│        ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐             │
│        │  Grafana  │  │ Alertmanager│ │  Jaeger   │             │
│        │   :3000   │  │   :9093    │  │  :16686   │             │
│        └───────────┘  └───────────┘  └───────────┘             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Fluentd (Log Aggregation)                    │  │
│  │                      :24224                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Prometheus (`prometheus.yml`)

Metrics collection and alerting engine.

**Scraped Targets:**
| Target | Port | Metrics Path | Interval |
|--------|------|--------------|----------|
| recruitment API | 8000 | /metrics | 15s |
| Celery Worker | 8000 | /metrics | 15s |
| PostgreSQL Exporter | 9187 | /metrics | 30s |
| Redis Exporter | 9121 | /metrics | 30s |
| Node Exporter | 9100 | /metrics | 30s |
| Prometheus | 9090 | /metrics | 15s |

**Quick Start:**
```bash
# Run Prometheus with this config
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $(pwd)/alerts/:/etc/prometheus/rules/ \
  prom/prometheus:latest
```

### 2. Grafana Dashboard (`grafana/dashboards/recruitment.json`)

Pre-configured dashboard with the following panels:

| Panel | Description | Metrics |
|-------|-------------|---------|
| API Request Rate | Requests per second by endpoint | `rate(http_requests_total[5m])` |
| API Response Time | p95/p99 latency | `histogram_quantile(0.95/0.99, ...)` |
| API Error Rate | 5xx error percentage | `rate(5xx) / rate(total)` |
| Memory Usage | Process memory consumption | `process_resident_memory_bytes` |
| CPU Usage | Host CPU utilization | `100 - idle_cpu` |
| Celery Task Rate | Background task throughput | `rate(celery_tasks_total[5m])` |

**Quick Start:**
```bash
# Run Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -v $(pwd)/grafana/dashboards/:/var/lib/grafana/dashboards/ \
  grafana/grafana:latest
```

### 3. Alert Rules (`alerts/alert-rules.yml`)

Production-ready alert rules:

| Alert | Condition | Severity |
|-------|-----------|----------|
| HighErrorRate | Error rate > 5% for 5m | critical |
| HighResponseTime | p95 > 2s for 5m | warning |
| ServiceDown | API down for 1m | critical |
| HighMemoryUsage | Memory > 500MB for 5m | warning |
| HighCPUUsage | CPU > 80% for 5m | warning |
| DatabaseConnectionsHigh | Connections > 80 for 5m | warning |
| CeleryWorkerDown | Worker down for 1m | critical |
| CeleryTaskBacklog | Pending tasks > 100 for 10m | warning |
| DiskSpaceLow | Disk < 10% for 5m | critical |
| RedisDown | Redis down for 1m | critical |

**Quick Start:**
```bash
# Run Alertmanager
docker run -d \
  --name alertmanager \
  -p 9093:9093 \
  -v $(pwd)/alerts/alertmanager.yml:/etc/alertmanager/config.yml \
  prom/alertmanager:latest
```

### 4. Fluentd Logging (`logging/fluentd.conf`)

Centralized log aggregation with Elasticsearch and S3 archival.

**Log Flow:**
```
Application → Fluentd → Elasticsearch (hot storage)
                    → S3 (cold archival)
                    → Stdout (debugging)
```

**Quick Start:**
```bash
# Run Fluentd
docker run -d \
  --name fluentd \
  -p 24224:24224 \
  -p 24224:24224/udp \
  -v $(pwd)/logging/fluentd.conf:/fluentd/etc/fluent.conf \
  -v /var/log:/var/log \
  fluent/fluentd:latest
```

### 5. Jaeger Tracing (`tracing/jaeger.yml`)

Distributed tracing for request flow analysis.

**Sampling Rates:**
| Service | Rate |
|---------|------|
| recruitment-api | 50% |
| recruitment-worker | 30% |
| default | 10% |

**Quick Start:**
```bash
# Run Jaeger
docker run -d \
  --name jaeger \
  -p 16686:16686 \
  -p 14250:14250 \
  -p 14268:14268 \
  -p 9411:9411 \
  -v $(pwd)/tracing/jaeger.yml:/etc/jaeger/config.yml \
  jaegertracing/all-in-one:latest
```

## Docker Compose (All-in-One)

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts/:/etc/prometheus/rules/
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./grafana/dashboards/:/var/lib/grafana/dashboards/
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alerts/alertmanager.yml:/etc/alertmanager/config.yml
    networks:
      - monitoring

  fluentd:
    image: fluent/fluentd:latest
    ports:
      - "24224:24224"
      - "24224:24224/udp"
    volumes:
      - ./logging/fluentd.conf:/fluentd/etc/fluent.conf
    networks:
      - monitoring

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14250:14250"
      - "14268:14268"
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
```

## Application Integration

### Python (Prometheus Client)

```python
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency', ['endpoint'])

# Start metrics server
start_http_server(8000)

# In your routes
@REQUEST_LATENCY.time()
async def handle_request():
    REQUEST_COUNT.labels(method='GET', endpoint='/api/v1/jobs', status='200').inc()
    ...
```

### Python (Jaeger Tracing)

```python
from jaeger_client import Config

config = Config(
    config={
        'sampler': {'type': 'probabilistic', 'param': 0.5},
        'logging': True,
    },
    service_name='recruitment-api',
)
tracer = config.initialize_tracer()

with tracer.start_span('process_job') as span:
    span.set_tag('job_id', job_id)
    ...
```

### Python (Structured Logging)

```python
import json
import logging

logger = logging.getLogger('recruitment-platform')

def log_event(level, message, **kwargs):
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': level,
        'message': message,
        **kwargs
    }
    logger.info(json.dumps(log_entry))

log_event('INFO', 'Job processed', job_id=123, duration=1.5)
```

## Directory Structure

```
monitoring/
├── prometheus.yml              # Prometheus configuration
├── grafana/
│   └── dashboards/
│       └── recruitment.json    # Grafana dashboard
├── alerts/
│   └── alert-rules.yml         # Prometheus alert rules
├── logging/
│   └── fluentd.conf            # Fluentd log aggregation
├── tracing/
│   └── jaeger.yml              # Jaeger tracing config
└── README.md                   # This file
```

## Production Checklist

- [ ] Configure Alertmanager notification channels (Slack, PagerDuty, email)
- [ ] Set up Grafana authentication (LDAP/OAuth)
- [ ] Configure Elasticsearch retention policies
- [ ] Set up S3 bucket for log archival
- [ ] Configure Jaeger storage backend
- [ ] Set up TLS for all monitoring endpoints
- [ ] Configure backup for Prometheus data
- [ ] Set up Grafana alert notifications
- [ ] Configure log rotation for Fluentd buffers
- [ ] Test all alert rules in staging environment

## Troubleshooting

### Prometheus not scraping targets
```bash
# Check target status
curl http://localhost:9090/api/v1/targets

# Check Prometheus logs
docker logs prometheus
```

### Grafana dashboard not loading
```bash
# Check Grafana logs
docker logs grafana

# Verify dashboard JSON
cat grafana/dashboards/recruitment.json | python -m json.tool
```

### Alerts not firing
```bash
# Check Alertmanager status
curl http://localhost:9093/api/v2/alerts

# Verify rule syntax
promtool check rules alerts/alert-rules.yml
```

### Logs not appearing in Elasticsearch
```bash
# Check Fluentd logs
docker logs fluentd

# Verify Elasticsearch connection
curl http://localhost:9200/_cat/indices?v
```

## License

Internal use only.

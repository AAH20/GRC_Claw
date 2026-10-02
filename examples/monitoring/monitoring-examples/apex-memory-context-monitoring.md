# Monitoring Examples: apex-memory-context

## Overview
This document provides comprehensive monitoring examples for the **apex-memory-context** project.

## 1. Health Check Monitoring

### Basic Health Endpoint
```python
import requests
import time

def check_health(url="http://localhost:8000/health"):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

# Run every 30 seconds
while True:
    if not check_health():
        print("ALERT: apex-memory-context is unhealthy!")
    time.sleep(30)
```

### Docker Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

## 2. Metrics Collection

### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_duration_seconds', 'Request latency')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')
ERROR_COUNT = Counter('errors_total', 'Total errors', ['type'])

# Start metrics server
start_http_server(9090)
```

### StatsD Metrics
```python
import statsd

client = statsd.StatsDClient('localhost', 8125)

# Increment counter
client.incr('requests')

# Record timing
client.timing('response_time', 150)

# Gauge value
client.gauge('active_users', 42)
```

## 3. Log Monitoring

### Structured Logging
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'project': 'apex-memory-context'
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger('apex-memory-context')
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Log Aggregation with Fluentd
```yaml
# fluentd.conf
<source>
  @type tail
  path /var/log/apex-memory-context/*.log
  pos_file /var/log/td-agent/apex-memory-context.log.pos
  tag apex-memory-context.*
  <parse>
    @type json
  </parse>
</source>

<match apex-memory-context.*>
  @type elasticsearch
  host localhost
  port 9200
  logstash_format true
</match>
```

## 4. Alerting Rules

### Prometheus Alert Rules
```yaml
groups:
  - name: apex-memory-context_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in apex-memory-context"
          
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High latency in apex-memory-context"
          
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "apex-memory-context is down"
```

## 5. Dashboard Examples

### Grafana Dashboard JSON
```json
{
  "dashboard": {
    "title": "apex-memory-context Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(errors_total[5m])"
          }
        ]
      },
      {
        "title": "Latency (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

## 6. Uptime Monitoring

### External Uptime Check
```python
import requests
import smtplib
from email.mime.text import MIMEText

def monitor_uptime(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            send_alert("apex-memory-context returned status {}".format(response.status_code))
    except Exception as e:
        send_alert("apex-memory-context is unreachable: {}".format(str(e)))

def send_alert(message):
    msg = MIMEText(message)
    msg['Subject'] = "ALERT: apex-memory-context"
    msg['From'] = "monitor@example.com"
    msg['To'] = "admin@example.com"
    
    with smtplib.SMTP('localhost') as server:
        server.send_message(msg)
```

## 7. Resource Monitoring

### System Resource Monitoring
```python
import psutil
import time

def monitor_resources():
    while True:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        if cpu > 90:
            print("WARNING: CPU usage is {}%".format(cpu))
        if memory > 90:
            print("WARNING: Memory usage is {}%".format(memory))
        if disk > 90:
            print("WARNING: Disk usage is {}%".format(disk))
        
        time.sleep(60)
```

## 8. CI/CD Pipeline Monitoring

### GitHub Actions Monitoring
```yaml
name: Monitor apex-memory-context
on:
  schedule:
    - cron: '*/15 * * * *'
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - name: Check service health
        run: |
          curl -f http://localhost:8000/health || exit 1
          
      - name: Check error rate
        run: |
          ERROR_RATE=$(curl -s http://localhost:9090/metrics | grep errors_total | awk '{print $2}')
          if (( $(echo "$ERROR_RATE > 100" | bc -l) )); then
            echo "Error rate too high: $ERROR_RATE"
            exit 1
          fi
```

## 9. Database Monitoring

### Connection Pool Monitoring
```python
import psycopg2
from psycopg2 import pool

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    host='localhost',
    database='apex-memory-context',
    user='user',
    password='password'
)

def check_connection_pool():
    try:
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM pg_stat_activity")
        active_connections = cursor.fetchone()[0]
        print("Active connections: {}".format(active_connections))
        connection_pool.putconn(conn)
    except Exception as e:
        print("Database error: {}".format(e))
```

## 10. Distributed Tracing

### OpenTelemetry Tracing
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("apex-memory-context")

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Usage
with tracer.start_as_current_span("process_data") as span:
    span.set_attribute("project", "apex-memory-context")
    # Your code here
```

## Summary

This monitoring setup provides:
- **Health checks** for service availability
- **Metrics collection** with Prometheus/StatsD
- **Structured logging** with JSON format
- **Alerting rules** for critical issues
- **Dashboards** for visualization
- **Uptime monitoring** with external checks
- **Resource monitoring** for system health
- **CI/CD integration** for automated checks
- **Database monitoring** for connection pools
- **Distributed tracing** for request flow analysis

---
*Generated for apex-memory-context*

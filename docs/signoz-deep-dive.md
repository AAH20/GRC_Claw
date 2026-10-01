# SigNoz Deep-Dive: Agent Monitoring & Alerting for Hermes Agent

> **For:** Ahmed Hassan — production agent monitoring with Nerve telemetry  
> **Stack:** Hermes Agent + Nerve + SigNoz (OTel-native observability)  
> **Date:** 2026-10-01

---

## 1. Architecture Overview — OTel-Native Observability

SigNoz is an open-source, OpenTelemetry-native observability platform built on ClickHouse. It unifies **traces, metrics, and logs** in a single datastore with one query and dashboard surface.

### Core Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIGNOZ ARCHITECTURE                          │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ OTel SDK /   │    │ OTel         │    │ ClickHouse   │      │
│  │ Auto-        │───▶│ Collector    │───▶│ (Unified     │      │
│  │ Instrument   │    │ (signoz-     │    │  Storage)    │      │
│  │              │    │  otel-       │    │              │      │
│  │ Hermes Agent │    │  collector)  │    │ • Traces     │      │
│  │ + Nerve      │    │              │    │ • Metrics    │      │
│  └──────────────┘    └──────────────┘    │ • Logs       │      │
│                                          └──────┬───────┘      │
│                                                 │              │
│                                          ┌──────▼───────┐      │
│                                          │ Query        │      │
│                                          │ Service      │      │
│                                          │ (Go)         │      │
│                                          └──────┬───────┘      │
│                                                 │              │
│                                          ┌──────▼───────┐      │
│                                          │ Frontend     │      │
│                                          │ (React SPA)  │      │
│                                          │              │      │
│                                          │ • Explorer   │      │
│                                          │ • Dashboards │      │
│                                          │ • Alerts     │      │
│                                          │ • Service Map│      │
│                                          └──────────────┘      │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Ruler        │───▶│ Alertmanager │───▶│ Notification │      │
│  │ (evaluates   │    │ (dedup,      │    │ Channels     │      │
│  │  alert rules)│    │  grouping)   │    │ (Slack, PD,  │      │
│  └──────────────┘    └──────────────┘    │  Email, etc) │      │
│                                          └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Role | Technology |
|---|---|---|
| **OTel Collector** | Receives OTLP, processes, writes to ClickHouse | Go (signoz-otel-collector fork) |
| **ClickHouse** | Columnar storage for all signals | ClickHouse |
| **Query Service** | Translates queries to ClickHouse SQL, evaluates alerts | Go |
| **Frontend** | Explorer, dashboards, alerts, service map | React/TypeScript |
| **Ruler** | Evaluates alert rules on schedule | Go |
| **Alertmanager** | Dedup, grouping, notification routing | Go (Prometheus Alertmanager fork) |
| **OpAMP** | Dynamic log pipeline configuration | Protocol |

### Why ClickHouse?

- **10x compression** vs Elasticsearch for trace data
- **Sub-second queries** on billions of spans
- **High-cardinality** tag filtering (user_id, request_path, status_code)
- **Single datastore** — no separate Prometheus + Jaeger + Loki to operate
- **TTL + S3 tiering** for cost-effective retention

### Deployment Options

| Mode | Best For | Command |
|---|---|---|
| **Docker Compose** | Evaluation, small workloads | `git clone https://github.com/SigNoz/signoz.git && cd deploy && ./install.sh` |
| **Kubernetes/Helm** | Production scale | `helm install signoz signoz/signoz` |
| **SigNoz Cloud** | Zero-ops, managed | Sign up at signoz.io |

---

## 2. Key Features for Ahmed's Stack

### 2.1 Unified Logs + Metrics + Traces + Alerts

| Signal | SigNoz Support | Ahmed Use Case |
|---|---|---|
| **Traces** | Full OTel trace ingestion, flamegraphs, Gantt charts | Agent execution traces, tool call chains, LLM call latency |
| **Metrics** | OTLP + Prometheus remote-write, PromQL support | Nerve telemetry metrics, agent performance counters |
| **Logs** | OTel logs, structured + unstructured, query builder | Agent logs, error logs, tool execution logs |
| **Alerts** | Metric, log, trace, anomaly, exception-based | Agent health alerts, cost alerts, error rate alerts |
| **Exceptions** | First-class exception tracking from trace data | Agent failure detection |

### 2.2 Agent-Native MCP Server

SigNoz ships an official **MCP server** that gives AI agents natural-language access to observability data:

**Key MCP Tools (41+):**

| Category | Tools | Use Case |
|---|---|---|
| **Traces** | `search_traces`, `get_trace_details`, `aggregate_traces` | Find failing agent runs, drill into span breakdown |
| **Logs** | `search_logs`, `aggregate_logs` | Find ERROR logs, correlate with traces |
| **Metrics** | `query_metrics`, `list_metrics`, `get_top_metrics` | Check agent latency, token usage, cost |
| **Alerts** | `list_alerts`, `create_alert`, `update_alert`, `delete_alert` | Manage alert rules from chat |
| **Dashboards** | `create_dashboard`, `import_dashboard`, `list_dashboards` | Build monitoring dashboards programmatically |
| **Discovery** | `get_field_keys`, `get_field_values`, `check_metric_cardinality` | Learn telemetry shape before querying |

**MCP Server Install (Self-Hosted):**

```json
{
  "mcpServers": {
    "signoz": {
      "command": "/path/to/signoz-mcp-server",
      "env": {
        "SIGNOZ_URL": "http://localhost:8080",
        "SIGNOZ_API_KEY": "<your-api-key>",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

**MCP Server Install (SigNoz Cloud):**

```json
{
  "mcpServers": {
    "signoz": {
      "type": "http",
      "url": "https://mcp.us.signoz.cloud/mcp"
    }
  }
}
```

### 2.3 GenAI Semantic Conventions Support

SigNoz supports the **OpenTelemetry GenAI Semantic Conventions** (`gen_ai.*` namespace):

| Span Type | Operation | Key Attributes |
|---|---|---|
| LLM Call | `chat {provider}` | `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens` |
| Agent Invocation | `invoke_agent {name}` | `gen_ai.agent.name`, `gen_ai.agent.outcome` |
| Tool Execution | `execute_tool {tool}` | `gen_ai.tool.name`, arguments, return value |
| Workflow | `invoke_workflow` | Multi-agent orchestration |

This means Hermes Agent can emit standardized GenAI spans that SigNoz understands natively.

---

## 3. Integration Guide — Monitoring Hermes Agent with SigNoz

### 3.1 Architecture for Ahmed's Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    HERMES AGENT + SIGNOZ                         │
│                                                                 │
│  ┌──────────────┐                                               │
│  │ Hermes Agent │                                               │
│  │              │                                               │
│  │ ┌──────────┐ │  OTel GenAI Spans                             │
│  │ │ Nerve    │ │  (invoke_agent, chat, execute_tool)            │
│  │ │ Telemetry│ │                                               │
│  │ └────┬─────┘ │                                               │
│  │      │       │                                               │
│  │ ┌────▼─────┐ │  OTLP Export                                  │
│  │ │ OTel SDK │ │                                               │
│  │ └────┬─────┘ │                                               │
│  └──────┼───────┘                                               │
│         │ OTLP/gRPC (port 4317)                                  │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ OTel         │                                               │
│  │ Collector    │  ←── Also receives Prometheus remote-write    │
│  │ (signoz)     │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ ClickHouse   │                                               │
│  │ (traces +    │                                               │
│  │  metrics +   │                                               │
│  │  logs)       │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Query        │    │ Ruler        │    │ Alertmanager │      │
│  │ Service      │    │ (alerts)     │───▶│ → Slack/PD   │      │
│  └──────┬───────┘    └──────────────┘    └──────────────┘      │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ SigNoz UI    │                                               │
│  │ :8080        │                                               │
│  └──────────────┘                                               │
│                                                                 │
│  ┌──────────────┐                                               │
│  │ SigNoz MCP   │  ←── Hermes Agent queries SigNoz via MCP     │
│  │ Server       │      (self-monitoring loop)                   │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Step-by-Step Integration

#### Step 1: Deploy SigNoz

```bash
# Clone and deploy with Docker Compose
git clone -b main https://github.com/SigNoz/signoz.git
cd signoz/deploy
./install.sh

# UI available at http://localhost:8080
# OTLP endpoint: localhost:4317 (gRPC), localhost:4318 (HTTP)
```

#### Step 2: Instrument Hermes Agent with OTel

```python
# hermes_otel.py — OTel instrumentation for Hermes Agent
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource

# Configure resource
resource = Resource.create({
    "service.name": "hermes-agent",
    "service.version": "1.0.0",
    "deployment.environment": "production",
    "agent.type": "hermes",
})

# Traces
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            insecure=True,
        )
    )
)
trace.set_tracer_provider(trace_provider)

# Metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True,
    ),
    export_interval_millis=60000,
)
metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metrics_provider)

tracer = trace.get_tracer("hermes-agent")
meter = metrics.get_meter("hermes-agent")
```

#### Step 3: Emit GenAI Semantic Convention Spans

```python
# hermes_genai_spans.py — GenAI semconv spans for agent operations
from opentelemetry import trace
import time

tracer = trace.get_tracer("hermes-agent")

def instrument_agent_run(agent_name: str, task: str):
    """Wrap agent execution with invoke_agent span."""
    with tracer.start_as_current_span(
        f"invoke_agent {agent_name}",
        kind=trace.SpanKind.INTERNAL,
    ) as span:
        span.set_attribute("gen_ai.operation.name", "invoke_agent")
        span.set_attribute("gen_ai.agent.name", agent_name)
        span.set_attribute("gen_ai.agent.id", f"hermes-{agent_name}")
        span.set_attribute("gen_ai.system", "hermes")
        return span

def instrument_llm_call(model: str, input_tokens: int, output_tokens: int, latency_ms: float):
    """Emit chat span for each LLM call."""
    with tracer.start_as_current_span(
        f"chat {model}",
        kind=trace.SpanKind.CLIENT,
    ) as span:
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("gen_ai.response.model", model)
        span.set_attribute("gen_ai.usage.input_tokens", input_tokens)
        span.set_attribute("gen_ai.usage.output_tokens", output_tokens)
        span.set_attribute("gen_ai.response.finish_reasons", "stop")
        span.set_attribute("server.address", "api.anthropic.com")
        return span

def instrument_tool_call(tool_name: str, arguments: dict, result: dict, latency_ms: float):
    """Emit execute_tool span for each tool invocation."""
    with tracer.start_as_current_span(
        f"execute_tool {tool_name}",
        kind=trace.SpanKind.INTERNAL,
    ) as span:
        span.set_attribute("gen_ai.operation.name", "execute_tool")
        span.set_attribute("gen_ai.tool.name", tool_name)
        span.set_attribute("gen_ai.agent.name", "hermes")
        # Add tool arguments as events (not attributes — can be large)
        span.add_event("gen_ai.tool.arguments", {"arguments": str(arguments)[:1000]})
        span.add_event("gen_ai.tool.result", {"result": str(result)[:1000]})
        return span
```

#### Step 4: Export Nerve Metrics via Prometheus Remote Write

```yaml
# otel-collector-config.yaml — Add Prometheus remote-write receiver
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: 'hermes-nerve'
          scrape_interval: 15s
          static_configs:
            - targets: ['localhost:9090']  # Nerve Prometheus exporter

processors:
  batch:
    timeout: 10s
    send_batch_size: 10000

exporters:
  otlp:
    endpoint: localhost:4317
    tls:
      insecure: true

service:
  pipelines:
    metrics:
      receivers: [prometheus]
      processors: [batch]
      exporters: [otlp]
```

#### Step 5: Configure SigNoz MCP Server for Self-Monitoring

```json
// .hermes/mcp.json — Hermes Agent queries SigNoz via MCP
{
  "mcpServers": {
    "signoz": {
      "command": "/usr/local/bin/signoz-mcp-server",
      "env": {
        "SIGNOZ_URL": "http://localhost:8080",
        "SIGNOZ_API_KEY": "${SIGNOZ_API_KEY}",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

This creates a **self-monitoring loop**: Hermes Agent uses the SigNoz MCP server to query its own telemetry, investigate anomalies, and even create dashboards — all from chat.

---

## 4. Configuration Examples

### 4.1 Alert Rules

#### Metric-Based Alert: High Agent Error Rate

```yaml
# alert-rules/agent-error-rate.yaml
# SigNoz alert rule (v5 / v2alpha1 schema, SigNoz >= 0.125)
name: "hermes-agent-high-error-rate"
alert_type: METRIC_BASED_ALERT
description: "Agent error rate exceeds 5% over 5 minutes"
condition:
  query: |
    {
      "aggregateAttribute": {
        "key": "gen_ai.agent.outcome",
        "type": "tag",
        "dataType": "string"
      },
      "aggregateOperator": "count",
      "dataSource": "traces",
      "filters": {
        "items": [
          {
            "key": {"key": "gen_ai.agent.outcome", "type": "tag"},
            "op": "=",
            "value": "error"
          }
        ],
        "op": "AND"
      },
      "groupBy": [],
      "legend": "error_count",
      "queryName": "A",
      "timeAggregation": "rate"
    }
  threshold: "5"
  comparison: ">"
  evaluation_window: "5m"
  frequency: "1m"
severity: critical
notification_channels:
  - slack-alerts
  - pagerduty-critical
```

#### Log-Based Alert: Agent Tool Failures

```yaml
# alert-rules/tool-failure-alert.yaml
name: "hermes-tool-failures"
alert_type: LOGS_BASED_ALERT
description: "More than 10 tool execution failures in 5 minutes"
condition:
  query: |
    {
      "aggregateAttribute": {
        "key": "level",
        "type": "tag",
        "dataType": "string"
      },
      "aggregateOperator": "count",
      "dataSource": "logs",
      "filters": {
        "items": [
          {
            "key": {"key": "level", "type": "tag"},
            "op": "=",
            "value": "ERROR"
          },
          {
            "key": {"key": "event", "type": "tag"},
            "op": "=",
            "value": "tool_call"
          }
        ],
        "op": "AND"
      },
      "groupBy": [],
      "legend": "error_count",
      "queryName": "A",
      "timeAggregation": "rate"
    }
  threshold: "10"
  comparison: ">"
  evaluation_window: "5m"
  frequency: "1m"
severity: warning
notification_channels:
  - slack-alerts
```

#### Trace-Based Alert: High Agent Latency

```yaml
# alert-rules/agent-latency-alert.yaml
name: "hermes-agent-high-latency"
alert_type: TRACES_BASED_ALERT
description: "P99 agent execution latency exceeds 30 seconds"
condition:
  query: |
    {
      "aggregateAttribute": {
        "key": "duration_nano",
        "type": "float64"
      },
      "aggregateOperator": "p99",
      "dataSource": "traces",
      "filters": {
        "items": [
          {
            "key": {"key": "gen_ai.operation.name", "type": "tag"},
            "op": "=",
            "value": "invoke_agent"
          }
        ],
        "op": "AND"
      },
      "groupBy": [],
      "legend": "p99_latency",
      "queryName": "A"
    }
  threshold: "30000000000"
  comparison: ">"
  evaluation_window: "5m"
  frequency: "1m"
severity: warning
notification_channels:
  - slack-alerts
```

#### Anomaly-Based Alert: Token Cost Spike

```yaml
# alert-rules/token-cost-anomaly.yaml
name: "hermes-token-cost-anomaly"
alert_type: ANOMALY_BASED_ALERT
description: "Token usage deviates from historical baseline"
condition:
  query: |
    {
      "aggregateAttribute": {
        "key": "gen_ai.usage.output_tokens",
        "type": "float64"
      },
      "aggregateOperator": "sum",
      "dataSource": "traces",
      "filters": {
        "items": [],
        "op": "AND"
      },
      "groupBy": [],
      "legend": "total_tokens",
      "queryName": "A",
      "timeAggregation": "rate"
    }
  threshold: "2.0"
  comparison: ">"
  evaluation_window: "15m"
  frequency: "5m"
severity: warning
notification_channels:
  - slack-alerts
```

### 4.2 Notification Channel Configuration

```yaml
# notification-channels.yaml
channels:
  - name: slack-alerts
    type: slack
    webhook_url: "${SLACK_WEBHOOK_URL}"
    title: "SigNoz Alert: {{ .CommonLabels.alertname }}"
    text: "{{ .CommonAnnotations.description }}"

  - name: pagerduty-critical
    type: pagerduty
    routing_key: "${PAGERDUTY_ROUTING_KEY}"
    severity: critical

  - name: email-team
    type: email
    to: "team@example.com"
    from: "signoz@example.com"
    smarthost: "smtp.example.com:587"
    auth_username: "${SMTP_USER}"
    auth_password: "${SMTP_PASS}"
```

### 4.3 Dashboard Setup

#### Agent Observability Dashboard (JSON Import)

```json
{
  "title": "Hermes Agent Observability",
  "description": "Agent health, performance, cost, and error tracking",
  "tags": ["hermes", "agent", "observability"],
  "layout": [
    {"id": "panel-1", "x": 0, "y": 0, "w": 3, "h": 2, "panelTypes": "value"},
    {"id": "panel-2", "x": 3, "y": 0, "w": 3, "h": 2, "panelTypes": "value"},
    {"id": "panel-3", "x": 6, "y": 0, "w": 3, "h": 2, "panelTypes": "value"},
    {"id": "panel-4", "x": 9, "y": 0, "w": 3, "h": 2, "panelTypes": "value"},
    {"id": "panel-5", "x": 0, "y": 2, "w": 6, "h": 4, "panelTypes": "graph"},
    {"id": "panel-6", "x": 6, "y": 2, "w": 6, "h": 4, "panelTypes": "graph"},
    {"id": "panel-7", "x": 0, "y": 6, "w": 6, "h": 4, "panelTypes": "graph"},
    {"id": "panel-8", "x": 6, "y": 6, "w": 6, "h": 4, "panelTypes": "graph"},
    {"id": "panel-9", "x": 0, "y": 10, "w": 12, "h": 4, "panelTypes": "table"}
  ],
  "widgets": [
    {
      "id": "panel-1",
      "title": "Agent Success Rate",
      "panelTypes": "value",
      "queryData": {
        "queryType": "builder",
        "builder": {
          "queryData": [
            {
              "aggregateAttribute": {"key": "gen_ai.agent.outcome", "type": "tag", "dataType": "string"},
              "aggregateOperator": "count",
              "dataSource": "traces",
              "filters": {"items": [{"key": {"key": "gen_ai.agent.outcome", "type": "tag"}, "op": "=", "value": "success"}], "op": "AND"},
              "queryName": "A"
            },
            {
              "aggregateAttribute": {"key": "gen_ai.agent.outcome", "type": "tag", "dataType": "string"},
              "aggregateOperator": "count",
              "dataSource": "traces",
              "filters": {"items": [], "op": "AND"},
              "queryName": "B"
            }
          ],
          "queryFormulas": [{"expression": "A / B * 100", "queryName": "F1"}]
        }
      },
      "yAxisUnit": "percent"
    },
    {
      "id": "panel-2",
      "title": "Avg Agent Latency",
      "panelTypes": "value",
      "queryData": {
        "queryType": "builder",
        "builder": {
          "queryData": [
            {
              "aggregateAttribute": {"key": "duration_nano", "type": "float64"},
              "aggregateOperator": "avg",
              "dataSource": "traces",
              "filters": {"items": [{"key": {"key": "gen_ai.operation.name", "type": "tag"}, "op": "=", "value": "invoke_agent"}], "op": "AND"},
              "queryName": "A"
            }
          ]
        }
      },
      "yAxisUnit": "ms"
    },
    {
      "id": "panel-3",
      "title": "Total Tokens (24h)",
      "panelTypes": "value",
      "queryData": {
        "queryType": "builder",
        "builder": {
          "queryData": [
            {
              "aggregateAttribute": {"key": "gen_ai.usage.output_tokens", "type": "float64"},
              "aggregateOperator": "sum",
              "dataSource": "traces",
              "filters": {"items": [], "op": "AND"},
              "queryName": "A"
            }
          ]
        }
      },
      "yAxisUnit": "none"
    },
    {
      "id": "panel-4",
      "title": "Error Rate",
      "panelTypes": "value",
      "queryData": {
        "queryType": "builder",
        "builder": {
          "queryData": [
            {
              "aggregateAttribute": {"key": "gen_ai.agent.outcome", "type": "tag", "dataType": "string"},
              "aggregateOperator": "count",
              "dataSource": "traces",
              "filters": {"items": [{"key": {"key": "gen_ai.agent.outcome", "type": "tag"}, "op": "=", "value": "error"}], "op": "AND"},
              "queryName": "A"
            },
            {
              "aggregateAttribute": {"key": "gen_ai.agent.outcome", "type": "tag", "dataType": "string"},
              "aggregateOperator": "count",
              "dataSource": "traces",
              "filters": {"items": [], "op": "AND"},
              "queryName": "B"
            }
          ],
          "queryFormulas": [{"expression": "A / B * 100", "queryName": "F1"}]
        }
      },
      "yAxisUnit": "percent"
    },
    {
      "id": "panel-5",
      "title": "Agent Latency Over Time (P50/P90/P99)",
      "panelTypes": "graph",
      "queryData": {
        "queryType": "builder",
        "builder": {
          "queryData": [
            {
              "aggregateAttribute": {"key": "duration_nano", "type": "float64"},
              "aggregateOperator": "p50",
              "dataSource": "traces",
              "filters": {"items": [{"key": {"key": "gen_ai.operation.name", "type": "tag"}, "op": "=", "value": "invoke_agent"}], "op": "AND"},
              "legend": "P50",
              "queryName": "A"
            },
            {
              "aggregateAttribute": {"key": "duration_nano", "type": "float64"},
              "aggregateOperator": "p90",
              "dataSource": "traces",
              "filters": {"items": [{"key": {"key": "gen_ai.operation.name", "type": "tag"}, "op": "=", "value": "invoke_agent"}], "op": "AND"},
              "legend": "P90",
              "queryName": "B"
            },
            {
              "aggregateAttribute": {"key": "duration_nano", "type": "float64"},
              "aggregateOperator": "p99",
              "dataSource": "traces",
              "filters": {"items": [{"key": {"key": "gen_ai.operation.name", "type": "tag"}, "op": "=", "value": "invoke_agent"}], "op": "AND"},
              "legend": "P99",
              "queryName": "C"
            }
          ]
        }
      },
      "yAxisUnit": "ms"
    },
    {
      "id": "panel-6",
      "title": "Token Usage by Model",
      "panelTypes": "graph",
      "queryData": {
        "queryType": "builder",
        "builder": {
          "queryData": [
            {
              "aggregateAttribute": {"key": "gen_ai.usage.output_tokens", "type": "float64"},
              "aggregateOperator": "sum",
              "dataSource": "traces",
              "filters": {"items": [], "op": "AND"},
              "groupBy": [{"key": "gen_ai.request.model", "type": "tag", "dataType": "string"}],
              "legend": "{{gen_ai.request.model}}",
              "queryName": "A",
              "timeAggregation": "rate"
            }
          ]
        }
      },
      "yAxisUnit": "none"
    },
    {
      "id": "panel-7",
      "title": "Tool Call Frequency",
      "panelTypes": "graph",
      "queryData": {
        "queryType": "builder",
        "builder": {
          "queryData": [
            {
              "aggregateAttribute": {"key": "gen_ai.tool.name", "type": "tag", "dataType": "string"},
              "aggregateOperator": "count",
              "dataSource": "traces",
              "filters": {"items": [{"key": {"key": "gen_ai.operation.name", "type": "tag"}, "op": "=", "value": "execute_tool"}], "op": "AND"},
              "groupBy": [{"key": "gen_ai.tool.name", "type": "tag", "dataType": "string"}],
              "legend": "{{gen_ai.tool.name}}",
              "queryName": "A",
              "timeAggregation": "rate"
            }
          ]
        }
      },
      "yAxisUnit": "ops"
    },
    {
      "id": "panel-8",
      "title": "Agent Outcome Distribution",
      "panelTypes": "graph",
      "queryData": {
        "queryType": "builder",
        "builder": {
          "queryData": [
            {
              "aggregateAttribute": {"key": "gen_ai.agent.outcome", "type": "tag", "dataType": "string"},
              "aggregateOperator": "count",
              "dataSource": "traces",
              "filters": {"items": [], "op": "AND"},
              "groupBy": [{"key": "gen_ai.agent.outcome", "type": "tag", "dataType": "string"}],
              "legend": "{{gen_ai.agent.outcome}}",
              "queryName": "A",
              "timeAggregation": "rate"
            }
          ]
        }
      },
      "yAxisUnit": "ops"
    },
    {
      "id": "panel-9",
      "title": "Top Slowest Agent Runs",
      "panelTypes": "table",
      "queryData": {
        "queryType": "builder",
        "builder": {
          "queryData": [
            {
              "aggregateAttribute": {"key": "duration_nano", "type": "float64"},
              "aggregateOperator": "p99",
              "dataSource": "traces",
              "filters": {"items": [{"key": {"key": "gen_ai.operation.name", "type": "tag"}, "op": "=", "value": "invoke_agent"}], "op": "AND"},
              "groupBy": [
                {"key": "gen_ai.agent.name", "type": "tag", "dataType": "string"},
                {"key": "gen_ai.request.model", "type": "tag", "dataType": "string"}
              ],
              "legend": "P99 Latency",
              "queryName": "A"
            }
          ]
        }
      }
    }
  ]
}
```

### 4.4 ClickHouse SQL Queries for Custom Panels

```sql
-- Agent runs per minute with error rate
WITH __resource_filter AS (
  SELECT fingerprint
  FROM signoz_traces.distributed_traces_v3_resource
  WHERE simpleJSONExtractString(labels, 'service.name') = 'hermes-agent'
    AND seen_at_ts_bucket_start BETWEEN $start_timestamp - 1800 AND $end_timestamp
)
SELECT
  fromUnixTimestamp64Milli(intDiv(toUnixTimestamp64Milli(timestamp), 60000) * 60000) AS interval,
  count() AS total_runs,
  countIf(attributes_string['gen_ai.agent.outcome'] = 'error') AS error_runs,
  round(error_runs / total_runs * 100, 2) AS error_rate_pct
FROM signoz_traces.distributed_signoz_index_v3
WHERE resource_fingerprint GLOBAL IN __resource_filter
  AND attributes_string['gen_ai.operation.name'] = 'invoke_agent'
  AND timestamp BETWEEN $start_datetime AND $end_datetime
  AND ts_bucket_start BETWEEN $start_timestamp - 1800 AND $end_timestamp
GROUP BY interval
ORDER BY interval ASC;

-- Token cost by model over time
WITH __resource_filter AS (
  SELECT fingerprint
  FROM signoz_traces.distributed_traces_v3_resource
  WHERE simpleJSONExtractString(labels, 'service.name') = 'hermes-agent'
    AND seen_at_ts_bucket_start BETWEEN $start_timestamp - 1800 AND $end_timestamp
)
SELECT
  fromUnixTimestamp64Milli(intDiv(toUnixTimestamp64Milli(timestamp), 300000) * 300000) AS interval,
  attributes_string['gen_ai.request.model'] AS model,
  sum(toFloat64(attributes_number['gen_ai.usage.output_tokens'])) AS output_tokens,
  sum(toFloat64(attributes_number['gen_ai.usage.input_tokens'])) AS input_tokens
FROM signoz_traces.distributed_signoz_index_v3
WHERE resource_fingerprint GLOBAL IN __resource_filter
  AND attributes_string['gen_ai.operation.name'] = 'chat'
  AND timestamp BETWEEN $start_datetime AND $end_datetime
  AND ts_bucket_start BETWEEN $start_timestamp - 1800 AND $end_timestamp
GROUP BY interval, model
ORDER BY interval ASC, output_tokens DESC;

-- Tool call latency percentiles
WITH __resource_filter AS (
  SELECT fingerprint
  FROM signoz_traces.distributed_traces_v3_resource
  WHERE simpleJSONExtractString(labels, 'service.name') = 'hermes-agent'
    AND seen_at_ts_bucket_start BETWEEN $start_timestamp - 1800 AND $end_timestamp
)
SELECT
  attributes_string['gen_ai.tool.name'] AS tool_name,
  count() AS call_count,
  round(quantile(0.5)(duration_nano) / 1000000, 2) AS p50_ms,
  round(quantile(0.95)(duration_nano) / 1000000, 2) AS p95_ms,
  round(quantile(0.99)(duration_nano) / 1000000, 2) AS p99_ms
FROM signoz_traces.distributed_signoz_index_v3
WHERE resource_fingerprint GLOBAL IN __resource_filter
  AND attributes_string['gen_ai.operation.name'] = 'execute_tool'
  AND timestamp BETWEEN $start_datetime AND $end_datetime
  AND ts_bucket_start BETWEEN $start_timestamp - 1800 AND $end_timestamp
GROUP BY tool_name
ORDER BY p99_ms DESC;
```

---

## 5. Comparison: SigNoz vs Prometheus/Grafana

| Dimension | SigNoz | Prometheus + Grafana |
|---|---|---|
| **Architecture** | Unified platform (traces + metrics + logs in one store) | Best-of-breed assembly (Prometheus + Loki + Tempo + Grafana) |
| **Storage** | ClickHouse (single columnar store) | Prometheus TSDB + Loki chunks + Tempo traces |
| **OTel Native** | Yes — primary ingestion contract | Partial — via OTel Collector sidecar |
| **Query Language** | ClickHouse SQL + PromQL + Query Builder | PromQL + LogQL + TraceQL |
| **Correlation** | Native — same schema, click from metric to trace to log | Manual — label alignment across tools |
| **Alerting** | Built-in Ruler + Alertmanager | Prometheus Alertmanager |
| **Dashboards** | Built-in, JSON import/export | Grafana (industry standard, more mature) |
| **MCP Server** | Official agent-native MCP server | No official MCP server |
| **GenAI Semconv** | Native support for `gen_ai.*` spans | Via OTel Collector, no native UI support |
| **Self-Host Cost** | $0 (MIT license) | $0 (AGPL for some components) |
| **Operational Complexity** | Medium — operate ClickHouse | High — operate 4+ components |
| **Scalability** | ClickHouse cluster + Keeper | Prometheus federation + Mimir/Cortex |
| **RUM (Real User Monitoring)** | Not yet (roadmap H2 2026) | Via Grafana Faro |
| **Community** | 31.8K stars, YC W21, Series A | Grafana 60K+ stars, massive ecosystem |
| **Agent Self-Monitoring** | MCP server enables agent to query own telemetry | No equivalent |

### When to Choose SigNoz

- You want **one platform** instead of assembling LGTM stack
- You're **OTel-native** or planning to migrate to OTel
- You need **agent-native observability** with MCP server
- You want **built-in correlation** across signals
- You prefer **ClickHouse performance** over Elasticsearch

### When to Choose Prometheus/Grafana

- You have **existing Prometheus investment** and expertise
- You need **mature ecosystem** (thousands of exporters, dashboards)
- You want **best-of-breed** for each signal
- You need **RUM** or extensive plugin ecosystem
- You have **dedicated SRE team** to operate multiple components

### Migration Path: Prometheus → SigNoz

SigNoz supports **Prometheus remote-write** and **PromQL**, so you can migrate incrementally:

```yaml
# prometheus.yml — remote write to SigNoz
remote_write:
  - url: "http://signoz-otel-collector:13133/api/v1/write"
    tls_config:
      insecure_skip_verify: true
```

---

## 6. Pitfalls and Best Practices

### 6.1 Pitfalls

| Pitfall | Impact | Mitigation |
|---|---|---|
| **ClickHouse operational burden** | Background merges, part explosions, disk pressure at scale | Use ClickHouse Keeper, monitor `system.parts`, set `max_memory_usage` |
| **No RUM support** | Can't monitor frontend performance | Use separate tool (Grafana Faro) until SigNoz ships RUM |
| **GenAI semconv is Development status** | Attribute names can change between releases | Pin instrumentation library version, record semconv version |
| **High cardinality explosion** | ClickHouse storage and query performance degrades | Use `signoz_check_metric_cardinality`, limit label values |
| **Single-node ClickHouse** | Not production-ready | Use ClickHouse cluster with replication for production |
| **MCP server version requirements** | Dashboard tools need v0.135.0+, alert tools need v0.120.0+ | Keep SigNoz updated, check version compatibility |
| **Content capture PII risk** | Prompt/compliance exposure | Set `capture_message_content = false`, add collector redaction processor |
| **Alert fatigue** | Too many alerts → ignored alerts | Use anomaly-based alerts, proper thresholds, maintenance windows |
| **No built-in log pipeline** | Logs need explicit configuration | Use OpAMP for dynamic log pipeline management |
| **Compose → K8s migration** | Not a flag — real migration effort | Plan for Helm chart deployment from the start |

### 6.2 Best Practices

#### Deployment

```yaml
# production-deployment.yaml
# 1. Use separate cluster for SigNoz
# 2. Enable TLS ingress
# 3. Configure ClickHouse replication
# 4. Set up S3-backed cold storage
# 5. Use Kubernetes Helm chart

# values.yaml for Helm
clickhouse:
  enabled: true
  replicas: 3
  keeper:
    enabled: true
  storage:
    size: 500Gi
  resources:
    requests:
      memory: "8Gi"
      cpu: "4"
    limits:
      memory: "16Gi"
      cpu: "8"

otelCollector:
  replicas: 3
  resources:
    requests:
      memory: "4Gi"
      cpu: "2"

retention:
  traces: "30d"
  metrics: "90d"
  logs: "30d"
  coldStorage:
    enabled: true
    bucket: "signoz-telemetry-cold"
    region: "us-east-1"
```

#### Sampling Strategy

```yaml
# otel-collector-sampling.yaml
processors:
  # Tail-based sampling: keep all errors, sample successes
  tail_sampling:
    decision_wait: 10s
    num_traces: 100000
    expected_new_traces_per_sec: 10000
    policies:
      - name: error-traces
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-traces
        type: latency
        latency: {threshold_ms: 5000}
      - name: success-sampling
        type: probabilistic
        probabilistic: {sampling_percentage: 10}
```

#### Cardinality Management

```python
# Good: Low-cardinality labels
span.set_attribute("gen_ai.agent.name", "hermes")  # Few distinct values
span.set_attribute("gen_ai.request.model", "claude-sonnet-4")  # Few models

# Bad: High-cardinality labels
span.set_attribute("gen_ai.agent.id", f"hermes-{uuid.uuid4()}")  # Unique per run
span.set_attribute("session.id", session_id)  # Unique per session
span.set_attribute("user.id", user_id)  # Unique per user

# Instead: Use events for high-cardinality data
span.add_event("gen_ai.session", {"session.id": session_id})
```

#### Alert Design

```yaml
# Good alert design principles:
# 1. Use anomaly-based alerts for dynamic thresholds
# 2. Set appropriate evaluation windows (not too short)
# 3. Use severity levels consistently
# 4. Include runbook links in annotations
# 5. Test alerts before relying on them

alerts:
  - name: "hermes-agent-error-rate"
    severity: critical
    evaluation_window: "5m"
    frequency: "1m"
    annotations:
      runbook: "https://wiki.internal/hermes-agent-runbook"
      dashboard: "http://signoz:8080/d/hermes-agent"
    labels:
      team: "ai-platform"
      service: "hermes-agent"
```

#### Security

```yaml
# security-best-practices.yaml
# 1. Enable TLS on all endpoints
# 2. Use API keys with minimal permissions
# 3. Enable RBAC
# 4. Redact PII in collector
# 5. Network policies to restrict collector access

processors:
  # Redact sensitive data before it leaves your network
  redact:
    allowed_keys: ["gen_ai.operation.name", "gen_ai.tool.name", "gen_ai.request.model"]
    blocked_values:
      - "(?i)password"
      - "(?i)secret"
      - "(?i)token"
      - "(?i)api.key"
```

#### Self-Monitoring with MCP

```python
# hermes_self_monitor.py — Hermes Agent monitors itself via SigNoz MCP
# This creates a "third observability layer" — SigNoz watches the agent that watches SigNoz

# The MCP server emits its own telemetry:
# - mcp.tool.calls (counter by tool name)
# - mcp.tool.call.duration.* (histogram)
# - Tagged with gen_ai.tool.name

# Enable by setting OTEL_EXPORTER_OTLP_ENDPOINT on the MCP server:
# OTEL_EXPORTER_OTLP_ENDPOINT=http://signoz-otel-collector:4317
# OTEL_SERVICE_NAME=signoz-mcp-server
```

---

## 7. Quick Start Checklist

- [ ] Deploy SigNoz (Docker Compose for eval, Helm for prod)
- [ ] Instrument Hermes Agent with OTel SDK + GenAI semconv spans
- [ ] Configure Nerve Prometheus exporter → OTel Collector → SigNoz
- [ ] Set up notification channels (Slack, PagerDuty)
- [ ] Import agent observability dashboard JSON
- [ ] Create alert rules (error rate, latency, token cost)
- [ ] Configure tail-based sampling
- [ ] Set up ClickHouse retention policies + S3 cold storage
- [ ] Deploy SigNoz MCP server for agent self-monitoring
- [ ] Test end-to-end: trigger alert → receive notification → investigate in UI
- [ ] Set up TLS ingress for production
- [ ] Configure RBAC and API key management

---

## 8. Key Takeaways

1. **SigNoz is the right fit for Ahmed's stack** — OTel-native, unified storage, agent MCP server, and GenAI semconv support make it ideal for monitoring Hermes Agent + Nerve telemetry.

2. **The MCP server is the differentiator** — No other observability platform gives AI agents native access to query their own telemetry. This enables self-monitoring, autonomous investigation, and programmatic dashboard management.

3. **ClickHouse is the operational reality** — SigNoz works great on a single node for evaluation, but production requires ClickHouse cluster management. This is the main operational investment.

4. **GenAI semconv is the future** — The `gen_ai.*` span taxonomy is the standard for agent observability. SigNoz supports it natively, and instrumenting with it now future-proofs the monitoring stack.

5. **Start simple, scale gradually** — Begin with Docker Compose, basic traces and metrics, then add logs, alerts, and the MCP server as maturity grows.

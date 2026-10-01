# Arize Phoenix — Deep-Dive Integration Guide for Ahmed Hassan's Stack

> **Target stack:** Hermes Agent + Prometheus/Grafana + vendor-neutral OTel tracing
> **Phoenix version referenced:** 11.x (current main, 11.3K GitHub stars)
> **License:** Apache 2.0 (OSS); managed equivalent is Arize AX

---

## 1. Architecture Overview

### What Phoenix Is

Arize Phoenix is an **open-source AI observability and evaluation platform** built on two CNCF standards:

| Layer | Standard | Role |
|-------|----------|------|
| Transport | **OpenTelemetry (OTLP)** | Vendor-neutral trace/metrics/logs collection |
| Semantics | **OpenInference** | AI-specific span conventions (LLM, RETRIEVER, TOOL, AGENT, etc.) |

Phoenix is **local-first**: it runs as a single process (or Docker container) on your machine, stores traces in SQLite (default) or PostgreSQL, and exposes a web UI at `http://localhost:6006`. No cloud account, no data leaves your infrastructure.

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│  Hermes Agent (Python)                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ hermes-otel │  │ OpenInference│  │ OTel SDK      │  │
│  │ plugin      │──│ instrumentors│──│ (OTLP exporter)│ │
│  └─────────────┘  └──────────────┘  └───────┬───────┘  │
└─────────────────────────────────────────────┼──────────┘
                                              │ OTLP (gRPC/HTTP)
                                              ▼
┌─────────────────────────────────────────────────────────┐
│  Phoenix Server (localhost:6006)                        │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Web UI     │  │ Trace Store  │  │ Eval Engine    │  │
│  │ (React)    │  │ (SQLite/PG)  │  │ (LLM-as-judge) │  │
│  └────────────┘  └──────────────┘  └────────────────┘  │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ OTLP       │  │ Prometheus   │  │ Prompt         │  │
│  │ Collector  │  │ /v1/metrics  │  │ Management     │  │
│  │ :4317/:6006│  │ :9090        │  │ + Playground   │  │
│  └────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Port Map

| Port | Protocol | Purpose | Env Var |
|------|----------|---------|---------|
| 6006 | HTTP | Web UI + OTLP HTTP trace ingestion (`/v1/traces`) | `PHOENIX_PORT` |
| 4317 | gRPC | OTLP gRPC trace ingestion | `PHOENIX_GRPC_PORT` |
| 9090 | HTTP | Prometheus metrics (optional, disabled by default) | `PHOENIX_ENABLE_PROMETHEUS` |

### OpenInference Semantic Conventions

OpenInference defines **10 span kinds** that Phoenix uses to render AI-aware visualizations:

| Span Kind | Description | Key Attributes |
|-----------|-------------|----------------|
| `LLM` | Model API call | `llm.model_name`, `llm.input_messages`, `llm.output_messages`, `llm.token_count.*`, `llm.invocation_parameters` |
| `AGENT` | Autonomous reasoning step | `agent.name`, `graph.node.*` |
| `CHAIN` | Logical grouping / orchestration | `input.value`, `output.value` |
| `TOOL` | Function/tool execution | `tool.name`, `tool.parameters`, `tool.json_schema` |
| `RETRIEVER` | Vector store / search query | `retrieval.documents.*` (flattened: `retrieval.documents.0.document.content`) |
| `RERANKER` | Document reranking | `reranker.query`, `reranker.input_documents`, `reranker.top_k` |
| `EMBEDDING` | Vector generation | `embedding.model_name`, `embedding.embeddings.*` |
| `GUARDRAIL` | Safety/moderation check | `input.value`, `output.value` |
| `EVALUATOR` | LLM-as-judge scoring | `output.value` (label + explanation) |
| `PROMPT` | Template rendering | `llm.prompt_template.*` |

**Critical convention:** List-valued attributes use **zero-based indexed dot notation** (e.g., `llm.input_messages.0.message.role`). This is mandatory — Phoenix's UI queries these flattened keys.

---

## 2. Key Features for Ahmed's Stack

### 2.1 LLM Tracing

- **Auto-instrumentation** via `openinference-instrumentation-*` packages for 30+ frameworks (OpenAI, Anthropic, LangChain, LlamaIndex, DSPy, CrewAI, OpenAI Agents SDK, Claude Agent SDK, etc.)
- **One-line setup**: `register(project_name="hermes-agent", endpoint="http://localhost:6006/v1/traces")` + `OpenAIInstrumentor().instrument()`
- **Token-level waterfall**: Per-span latency breakdown showing prompt processing vs. token generation vs. network overhead
- **Session tracking**: `session.id` / `user.id` attributes roll multi-turn conversations into evaluable units
- **Cost tracking**: `llm.cost.*` attributes + token counts enable per-request and aggregate cost analysis

### 2.2 Evaluation

- **LLM-as-judge**: Built-in evaluators (`HallucinationEvaluator`, `QAEvaluator`, `RelevanceEvaluator`) using any LLM as judge
- **Code-based evals**: Python functions for deterministic checks
- **Human annotations**: UI-based labeling with ground-truth attachment
- **Dataset evaluators**: Attach evaluators to datasets for automatic scoring during experiments
- **Third-party integrations**: Ragas, Deepeval, Cleanlab
- **Result logging**: `client.log_evaluations(SpanEvaluations(...))` writes scores back onto spans — visible inline in the trace UI

### 2.3 Debugging

- **Trace waterfall**: Hierarchical span tree with timing, token counts, and status per span
- **Span replay**: Re-run any LLM span with modified inputs to test prompt changes
- **Prompt playground**: Side-by-side model/prompt comparison
- **Prompt management**: Version control for prompts with tagging and deployment
- **Experiments**: A/B test prompts, models, or retrieval configs on versioned datasets
- **PXI (Phoenix Intelligence)**: Built-in AI agent (beta in 17.0+) for debugging traces and iterating prompts
- **Remote MCP Server**: Connect Claude Code, Cursor, or other MCP clients to query traces via `/mcp` endpoint

### 2.4 Datasets & Experiments

- Create versioned datasets from traces or uploaded files
- Run experiments comparing prompt/model/retrieval changes
- Track metrics across experiment runs
- Export datasets for fine-tuning

---

## 3. Integration Guide: Instrumenting Hermes Agent with Phoenix

### 3.1 Architecture Decision

Hermes Agent has an official OTel plugin (`briancaffey/hermes-otel`) that exports traces via OTLP to **any** compatible backend — Phoenix included. This is the recommended path because:

1. The plugin already handles span creation for LLM calls, tool calls, and agent sessions
2. Phoenix accepts OTLP natively — no adapter needed
3. The same traces can simultaneously go to Phoenix (for LLM debugging) and Grafana Tempo (for infrastructure correlation)

### 3.2 Installation

```bash
# 1. Install the hermes-otel plugin
hermes plugins install briancaffey/hermes-otel --enable

# 2. Install OTel runtime dependencies into the Hermes Agent venv
~/.hermes/hermes-agent/venv/bin/pip install \
  opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-exporter-otlp-proto-http

# 3. Install the plugin's own dependencies
~/.hermes/hermes-agent/venv/bin/pip install -e ~/.hermes/plugins/hermes_otel

# 4. Verify
hermes plugins list --plain --no-bundled | grep hermes_otel
```

### 3.3 Configuration

Edit `~/.hermes/plugins/hermes_otel/config.yaml`:

```yaml
# ── Core ──────────────────────────────────────────────
enabled: true

# Capture input/output previews on spans (prompts, tool args, responses)
# Set false if you don't want sensitive data in Phoenix
capture_previews: true

# Preview truncation cap (characters)
preview_max_chars: 1200

# Global privacy kill switch — suppresses ALL previews but keeps metadata
# (tool names, durations, token counts)
# capture_previews: false

# ── Logs (opt-in) ─────────────────────────────────────
capture_logs: true
log_level: INFO
log_attach_logger: null  # null = root logger; "hermes" = hermes-agent only

# ── Metrics ───────────────────────────────────────────
flush_interval_ms: 60000

# ── Backend: Phoenix ──────────────────────────────────
backends:
  - type: otlp
    endpoint: http://localhost:6006/v1/traces
    traces: true
    metrics: true
    logs: true
    # If Phoenix auth is enabled:
    # headers:
    #   Authorization: Bearer <PHOENIX_ADMIN_SECRET>
```

### 3.4 Environment Variables (alternative to config.yaml)

Add to `~/.hermes/.env`:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006/v1/traces
OTEL_PROJECT_NAME=hermes-agent
OTEL_RESOURCE_ATTRIBUTES=service.name=hermes-agent,environment=production
```

### 3.5 Verifying the Integration

```bash
# 1. Start Phoenix (if not running)
docker run -d --name phoenix -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest

# 2. Run a Hermes interaction
hermes chat -q "Say hello and list the current working directory using a tool."

# 3. Check plugin logs
grep -Ei 'hermes-otel|phoenix|backend' ~/.hermes/logs/*.log | tail -20

# 4. Open Phoenix UI
open http://localhost:6006
# You should see: agent root span → LLM spans → tool spans
```

### 3.6 What You'll See in Phoenix

Each Hermes execution produces a trace with:

| Span | Kind | Content |
|------|------|---------|
| Agent root | `AGENT` | Total tokens, final output, total latency |
| LLM call | `LLM` | Model, prompt, completion, token counts, TTFT |
| Tool call | `TOOL` | Tool name, arguments, result |
| (Optional) Chain | `CHAIN` | Prompt formatting, post-processing |

The plugin also emits **GenAI semantic-convention metrics**:
- `gen_ai.client.token.usage` (histogram, input/output)
- `gen_ai.client.operation.duration` (histogram, seconds)
- `gen_ai.agent.token.usage` (histogram, per-turn rollup)

---

## 4. Configuration Examples

### 4.1 Docker Compose — Full Stack

```yaml
# docker-compose.yml
services:
  phoenix:
    image: arizephoenix/phoenix:latest
    container_name: phoenix
    restart: unless-stopped
    ports:
      - "6006:6006"   # UI + OTLP HTTP
      - "4317:4317"   # OTLP gRPC
      - "9090:9090"   # Prometheus metrics (optional)
    environment:
      - PHOENIX_PORT=6006
      - PHOENIX_GRPC_PORT=4317
      - PHOENIX_HOST=0.0.0.0
      - PHOENIX_WORKING_DIR=/mnt/data
      - PHOENIX_ENABLE_PROMETHEUS=true
      # For production with Postgres:
      # - PHOENIX_SQL_DATABASE_URL=postgresql://phoenix:${DB_PASSWORD}@postgres:5432/phoenix
      # - PHOENIX_SQL_ALCHEMY_POOL_SIZE=20
      # - PHOENIX_SQL_ALCHEMY_POOL_RECYCLE=3600
    volumes:
      - phoenix_data:/mnt/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6006/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  # Optional: PostgreSQL for persistent trace storage
  postgres:
    image: postgres:16
    restart: unless-stopped
    environment:
      - POSTGRES_USER=phoenix
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=phoenix
    volumes:
      - phoenix_db:/var/lib/postgresql/data

  # Your Hermes Agent (example)
  hermes-agent:
    build: ./hermes-agent
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://phoenix:6006/v1/traces
      - OTEL_PROJECT_NAME=hermes-agent
      - OTEL_RESOURCE_ATTRIBUTES=service.name=hermes-agent,environment=production
    depends_on:
      phoenix:
        condition: service_healthy

volumes:
  phoenix_data:
  phoenix_db:
```

### 4.2 OTel Collector Config (Fan-Out to Multiple Backends)

If you want traces to go to **both Phoenix and Grafana Tempo** (or any other backend), insert an OTel Collector:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  resource:
    attributes:
      - key: service.name
        value: hermes-agent
        action: upsert

exporters:
  # Phoenix (LLM debugging)
  otlp/phoenix:
    endpoint: phoenix:4317
    tls:
      insecure: true

  # Grafana Tempo (infrastructure correlation)
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

  # Prometheus (metrics)
  prometheus:
    endpoint: "0.0.0.0:8888"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [otlp/phoenix, otlp/tempo]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

### 4.3 Phoenix with PostgreSQL (Production)

```bash
docker run -d \
  --name phoenix \
  -p 6006:6006 \
  -p 4317:4317 \
  -p 9090:9090 \
  -e PHOENIX_SQL_DATABASE_URL=postgresql://phoenix:password@postgres:5432/phoenix \
  -e PHOENIX_SQL_ALCHEMY_POOL_SIZE=20 \
  -e PHOENIX_SQL_ALCHEMY_POOL_RECYCLE=3600 \
  -e PHOENIX_ENABLE_PROMETHEUS=true \
  -e PHOENIX_WORKING_DIR=/mnt/data \
  -v phoenix_data:/mnt/data \
  arizephoenix/phoenix:latest
```

### 4.4 Kubernetes (Helm)

```bash
helm repo add arize-ai https://arize-ai.github.io/phoenix-helm
helm install phoenix arize-ai/phoenix \
  --set phoenix.serverConfig.phoenixSqlDatabaseUrl="postgresql://..." \
  --set phoenix.serverConfig.phoenixEnablePrometheus=true \
  --set phoenix.serverConfig.phoenixPort=6006 \
  --set phoenix.serverConfig.phoenixGrpcPort=4317
```

---

## 5. Exporting to Prometheus/Grafana

### 5.1 Phoenix's Built-in Prometheus Endpoint

Phoenix can expose Prometheus-formatted metrics directly:

```bash
# Enable via environment variable
-e PHOENIX_ENABLE_PROMETHEUS=true
# Metrics available at http://localhost:9090/metrics
```

**Important:** Phoenix metrics are derived from **span attributes**, not raw span data. If `llm.token_count.prompt` is set as a span attribute, it appears in metrics. If tokens are only in the trace payload but not set as attributes, they won't appear in Prometheus.

### 5.2 Prometheus Scrape Config

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'phoenix'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### 5.3 Grafana Data Source

```yaml
# Grafana datasource provisioning
apiVersion: 1
datasources:
  - name: Phoenix Metrics
    type: prometheus
    access: proxy
    url: http://localhost:9090
    jsonData:
      timeInterval: 5s
    editable: true
```

### 5.4 Example PromQL Queries

```promql
# P95 LLM span latency
histogram_quantile(0.95, rate(px_span_latency_ms_bucket{span_kind="LLM"}[5m]))

# Total tokens consumed by model
sum by (llm_model_name) (rate(px_span_tokens_total[5m]))

# Error rate by span kind
sum by (span_kind) (rate(px_span_errors_total[5m]))

# Hallucination rate (if eval results are logged as metrics)
rate(px_eval_total{eval_name="Hallucination", label="hallucination"}[5m])
  / rate(px_eval_total{eval_name="Hallucination"}[5m])
```

### 5.5 Recommended Grafana Dashboard Panels

| Panel | Query | Purpose |
|-------|-------|---------|
| P95 LLM Latency | `histogram_quantile(0.95, ...)` | Track model latency SLOs |
| Token Consumption | `sum(rate(px_span_tokens_total[5m]))` | Cost tracking |
| Error Rate | `sum(rate(px_span_errors_total[5m]))` | Reliability monitoring |
| Hallucination Rate | Eval-based metric | Quality regression detection |
| Spans by Kind | `sum by (span_kind) (px_span_total)` | Workload composition |

### 5.6 Alternative: OTel Collector as Prometheus Source

If you're already running an OTel Collector (Section 4.2), you can use its Prometheus exporter instead of Phoenix's built-in endpoint:

```yaml
# In otel-collector-config.yaml
exporters:
  prometheus:
    endpoint: "0.0.0.0:8888"

service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

Then point Prometheus at `localhost:8888`.

---

## 6. Pitfalls and Best Practices

### 6.1 Critical Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| **Instrumentation after LLM import** | First LLM call not traced; missing spans | Always call `Instrumentor().instrument()` at the top of entrypoint, **before** any LLM library imports |
| **Wrong OTLP endpoint path** | Traces silently dropped, no errors | HTTP exporter must use `/v1/traces` (not `/`); gRPC uses `:4317` with no path |
| **localhost in Docker** | Traces work locally but not in containers | Use service names (`http://phoenix:6006/v1/traces`) in Docker Compose |
| **Missing `openinference.span.kind`** | Spans appear as `UNKNOWN` in Phoenix UI | Ensure instrumentor sets this attribute; manual spans must set it explicitly |
| **Unflattened list attributes** | Phoenix UI shows empty retriever/tool spans | Use indexed dot notation: `llm.input_messages.0.message.role` |
| **Phoenix not running before app starts** | Traces lost, no error | Start Phoenix first; verify with `curl http://localhost:6006/health` |
| **Default pool_size too low** | `QueuePool limit exceeded` under load | Set `PHOENIX_SQL_ALCHEMY_POOL_SIZE=20` |
| **Metrics endpoint not enabled** | Prometheus shows "no data" | Set `PHOENIX_ENABLE_PROMETHEUS=true` |
| **Auth not configured** | 401 errors when sending traces | Set `PHOENIX_CLIENT_HEADERS` or `PHOENIX_API_KEY` |
| **Instrumentation version mismatch** | Traces stop working after library upgrade | Pin `openinference-instrumentation-*` versions to match client library versions |

### 6.2 Best Practices

1. **Use `BatchSpanProcessor`** — Never use `SimpleSpanProcessor` in production. Batch export prevents network I/O from blocking the agent's hot path.

2. **Sample wisely** — For high-volume agents, use parent-based sampling:
   ```python
   from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
   sampler = ParentBasedTraceIdRatio(0.1)  # 10% sampling
   ```

3. **Set resource attributes** — Tag traces with metadata for filtering:
   ```python
   OTEL_RESOURCE_ATTRIBUTES=service.name=hermes-agent,environment=production,version=1.2.0
   ```

4. **Use `capture_previews: false` for sensitive workloads** — Suppresses all prompt/tool/response content but keeps metadata (durations, token counts, tool names).

5. **Pin Phoenix image version** — Use `arizephoenix/phoenix:11.3.0` instead of `:latest` in production.

6. **Separate dev/staging/production Phoenix instances** — Use `PHOENIX_PROJECT_NAME` to isolate traces by environment.

7. **Log evaluations back to spans** — Run LLM-as-judge evals on traces and use `client.log_evaluations()` so quality scores appear inline in the UI.

8. **Use the `hermes-otel` plugin's GenAI metrics** — The plugin emits `gen_ai.client.*` spec-named instruments that work with generic OTel GenAI dashboards out of the box.

9. **Monitor Phoenix itself** — Set up alerts on Phoenix's health endpoint and Prometheus metrics. If Phoenix goes down, you lose observability.

10. **Plan for retention** — Default SQLite storage is ephemeral. For production, use PostgreSQL with persistent volumes and define a retention policy (export old traces to S3/ClickHouse).

### 6.3 Security Considerations

- **Phoenix has no authentication by default** — anyone with port access can view traces. Enable auth (`PHOENIX_ENABLE_AUTH=true`) before exposing beyond localhost.
- **Traces contain prompts and responses** — potentially sensitive. Use `capture_previews: false` or deploy Phoenix on a private network.
- **Use TLS in production** — Set `insecure=False` on OTLP exporters and configure certificates.
- **Phoenix telemetry** — Set `PHOENIX_TELEMETRY_ENABLED=false` to disable FullStory/Scarf.sh tracking.

### 6.4 Migration Path

Phoenix is OTel-native, so you're never locked in:

- **To Arize AX (managed):** Change `OTEL_EXPORTER_OTLP_ENDPOINT` to Arize's endpoint + add API key. No code changes.
- **To Grafana Tempo:** Point the same OTLP exporter at Tempo. Traces are standard OTLP.
- **To Datadog/Honeycomb:** Same pattern — change the exporter endpoint.
- **From Phoenix to pure OTel Collector:** Remove Phoenix-specific config; the `openinference-instrumentation-*` packages work with any OTLP backend.

---

## Quick Reference: Minimal Working Setup

```bash
# 1. Start Phoenix
docker run -d --name phoenix -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest

# 2. Install hermes-otel plugin
hermes plugins install briancaffey/hermes-otel --enable
~/.hermes/hermes-agent/venv/bin/pip install -e ~/.hermes/plugins/hermes_otel

# 3. Configure backend (edit ~/.hermes/plugins/hermes_otel/config.yaml)
# Set endpoint: http://localhost:6006/v1/traces

# 4. Run Hermes
hermes chat -q "Hello"

# 5. View traces
open http://localhost:6006
```

---

*Sources: Arize Phoenix GitHub (Arize-ai/phoenix), OpenInference spec, hermes-otel plugin docs, Phoenix documentation (arize.com/docs/phoenix)*

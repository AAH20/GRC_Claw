# Langfuse Integration Guide for Ahmed Hassan's Agent Systems

## 1. Architecture Overview

### 1.1 Langfuse Platform Architecture

Langfuse is an open-source LLM observability platform (35K+ GitHub stars, MIT license) built on a **dual-service, multi-store architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                     SDK / OTLP / API                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │   Langfuse Web :3000    │  (Next.js UI + REST API)
          │   - Serves UI           │
          │   - Ingestion API       │
          │   - tRPC internal API  │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   Langfuse Worker :3030 │  (Express async worker)
          │   - Event processing    │
          │   - Eval execution      │
          │   - Batch exports       │
          └────────────┬────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
┌────▼─────┐   ┌──────▼──────┐   ┌──────▼──────┐
│ Postgres  │   │ ClickHouse  │   │    Redis    │
│ (OLTP)    │   │ (OLAP)      │   │ (Queue)     │
│ users,    │   │ traces,     │   │ BullMQ      │
│ projects, │   │ observations│   │ events      │
│ prompts,  │   │ scores      │   │ cache       │
│ datasets  │   │ sessions    │   │             │
└──────────┘   └─────────────┘   └─────────────┘
                       │
                ┌──────▼──────┐
                │  S3 / Blob  │
                │ raw events  │
                │ media       │
                └─────────────┘
```

**Key architectural decisions:**
- **ClickHouse for analytics**: Columnar OLAP storage for traces, observations, scores — enables fast aggregations (cost over time, latency percentiles)
- **Postgres for metadata**: Users, projects, API keys, prompts, datasets — transactional consistency
- **Redis for queue + cache**: BullMQ event queue decouples ingestion from processing; API key and prompt caching
- **S3 for durability**: Raw event batches persisted before processing — enables replay and disaster recovery
- **Async ingestion**: SDK batches events → Web enqueues to Redis → Worker processes → ClickHouse. Traces appear with slight lag (seconds)

### 1.2 Data Model

```
Organization
  └── Project (isolated environment)
       ├── Trace (one unit of work)
       │    ├── Observation (span/generation/event/tool/retriever/agent/chain/embedding/evaluator/guardrail)
       │    │    ├── input, output, metadata
       │    │    ├── model, usage (tokens), cost
       │    │    └── scores (quality metrics)
       │    └── user_id, session_id, tags, metadata
       ├── Session (groups multiple traces)
       ├── Prompt (versioned, deployable)
       ├── Dataset (test cases)
       └── Score (numeric/categorical/boolean)
```

### 1.3 Tracing Architecture

Langfuse SDKs are built on **OpenTelemetry** under the hood:
- Python SDK v4.x — OTel-based, `@observe` decorator, `start_as_current_observation()` context manager
- JS/TS SDK v5.x — OTel-based, `LangfuseSpanProcessor`, modular packages
- Any language with OTel SDK can send traces to Langfuse's OTLP endpoint (`/api/public/otel`)

**Observation types**: `generation`, `span`, `agent`, `tool`, `chain`, `retriever`, `embedding`, `evaluator`, `guardrail`, `event`

### 1.4 Evaluation Architecture

```
Production Traces ──► Online Evaluation (LLM-as-a-Judge, code evaluators)
                           │
                           ▼
                      Scores attached to observations
                           │
                           ▼
Datasets (curated from production) ──► Offline Experiments ──► Compare runs
```

**Evaluation methods:**
- **LLM-as-a-Judge**: Managed evaluators (hallucination, helpfulness, toxicity) or custom prompts with `{{variables}}`
- **Code evaluators**: Python/TypeScript functions for deterministic checks
- **Human annotation**: Collaborative review queues
- **User feedback**: Thumbs up/down, star ratings

### 1.5 Prompt Management Architecture

```
Prompt (text/chat) ──► Versioned ──► Labels (production/staging/dev)
                                    │
                                    ▼
                              SDK fetches (cached client-side)
                                    │
                                    ▼
                              Linked to traces (prompt version visible in UI)
```

- Prompts cached client-side by SDK — no latency impact
- Labels control deployment (production, staging) without code changes
- Every generation linked to its prompt version — enables per-version metrics

---

## 2. Key Features for Ahmed's Stack

### 2.1 Agent Tracing

**What you get:**
- Hierarchical trace trees showing every LLM call, tool invocation, retrieval step
- Agent graphs visualizing multi-step execution flows
- Session replay — group traces by `session_id` to see full conversations
- Per-observation latency, token usage, and cost

**For Hermes Agent specifically:**
- The `hermes-otel` plugin already emits OTel spans for LLM calls, tool calls, API requests
- Spans follow the hierarchy: `session.{platform}` → `llm.{model}` → `api.{model}` → `tool.{name}`
- Dual-convention attributes: `gen_ai.*` (Langfuse-native) + `llm.token_count.*` (Phoenix/OpenInference)

### 2.2 Cost Tracking

**Automatic cost computation:**
- Langfuse multiplies token counts by built-in model pricing tables
- Cost aggregated per trace, per user, per session, per model, per time period
- Custom model pricing supported

**For agent systems:**
- Per-turn cost visible in trace dashboard
- Cost spikes detectable via alerts (threshold-based)
- Output tokens typically 3-4x more expensive than input — check output distribution first

### 2.3 Session Replay

**What it is:**
- Structured trace viewer (not video replay) — hierarchical, timestamped record of everything an agent did
- Navigate step-by-step through agent execution
- See exact inputs/outputs at each node
- Diff two runs to surface behavioral regressions

**For debugging:**
- Reconstruct failed sessions from trace timeline
- See which tool ran with what arguments after which model output
- Identify exact divergence points in multi-agent workflows

### 2.4 Prompt Management

- Version prompts in Langfuse UI — no code changes needed for prompt iteration
- Non-technical team members can edit prompts
- One-click rollback to previous versions
- Link prompts to traces — see which prompt version produced which output
- A/B testing via dataset experiments

### 2.5 Evaluation & Quality

- LLM-as-a-Judge for automated quality scoring
- Build datasets from production failures → regression test suite
- Online evaluation scores production traces in real-time
- Human annotation queues for collaborative review

---

## 3. Integration Guide — Instrumenting Hermes Agent with Langfuse

### 3.1 Architecture: Hermes Agent → Langfuse

```
┌──────────────────────────────────────────────────────────┐
│                     Hermes Agent                          │
│                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │ Agent Loop  │───►│ hermes-otel  │───►│ OTel SDK   │  │
│  │ (LLM calls, │    │ plugin       │    │ (spans)    │  │
│  │  tools)     │    │ (hooks)      │    │            │  │
│  └─────────────┘    └──────────────┘    └─────┬──────┘  │
│                                               │         │
│  ┌─────────────┐                              │         │
│  │ Nerve       │                              │         │
│  │ telemetry   │                              │         │
│  │ (events,    │                              │         │
│  │  challenges,│                              │         │
│  │  controls,  │                              │         │
│  │  receipts)  │                              │         │
│  └─────────────┘                              │         │
└───────────────────────────────────────────────┼─────────┘
                                                │
                              OTLP/HTTP (port 4318)
                                                │
                                   ┌────────────▼────────┐
                                   │   Langfuse Web      │
                                   │   /api/public/otel  │
                                   └─────────────────────┘
```

### 3.2 Method 1: hermes-otel Plugin (Recommended)

The `hermes-otel` plugin is the fastest path — it converts Hermes lifecycle events into OTel spans and exports to any OTLP-compatible backend including Langfuse.

**Step 1: Install the plugin**
```bash
hermes plugins install briancaffey/hermes-otel/hermes_otel
```

**Step 2: Install OTel dependencies into Hermes venv**
```bash
# Find the Hermes venv
HERMES_PYTHON="$(dirname "$(command -v hermes)")/python"
uv pip install --python "$HERMES_PYTHON" \
  opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-exporter-otlp-proto-http
```

**Step 3: Configure Langfuse backend**

Edit `~/.hermes/plugins/hermes_otel/config.yaml`:
```yaml
enabled: true
project_name: hermes-agent
resource_attributes:
  service.name: hermes-agent
  deployment.environment.name: production
capture_previews: true          # Set false to strip input/output previews
capture_conversation_history: false
capture_sender_id: false
capture_logs: true
log_level: INFO
emit_genai_metrics: true
force_flush_on_session_end: true
span_batch_export_timeout_ms: 30000

backends:
  - type: langfuse
    public_key_env: LANGFUSE_PUBLIC_KEY
    secret_key_env: LANGFUSE_SECRET_KEY
    base_url: http://localhost:3000   # or https://cloud.langfuse.com
```

**Step 4: Set environment variables**

Add to `~/.hermes/.env`:
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxx
LANGFUSE_HOST=http://localhost:3000
```

**Step 5: Verify**
```bash
hermes chat -q "Say hello and list the current working directory using a tool."
# Check Langfuse UI at http://localhost:3000 — traces should appear within seconds
```

### 3.3 Method 2: Direct Langfuse Python SDK

For custom instrumentation within Hermes skills or tools:

```python
from langfuse import observe, get_client, propagate_attributes

langfuse = get_client()

@observe()
def my_agent_tool(user_input: str, session_id: str):
    with propagate_attributes(
        user_id="ahmed",
        session_id=session_id,
        metadata={"tool": "custom-agent", "env": "production"},
        tags=["agent", "production"],
    ):
        # LLM call here — automatically traced as generation
        result = call_llm(user_input)
        return result
```

### 3.4 Method 3: OpenTelemetry Direct (No Plugin)

If you want to bypass the plugin and use OTel directly:

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import base64

# Configure Langfuse OTLP endpoint
public_key = "pk-lf-xxx"
secret_key = "sk-lf-xxx"
auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint="http://localhost:3000/api/public/otel",
            headers={
                "Authorization": f"Basic {auth}",
                "x-langfuse-ingestion-version": "4",
            },
        )
    )
)
trace.set_tracer_provider(provider)
```

### 3.5 Span Hierarchy in Hermes Agent

The hermes-otel plugin produces this trace structure:
```
session.{platform} / cron [root, GENERAL]
  └── llm.{model} [LLM — input, output, total tokens]
       ├── api.{model} [LLM — prompt/completion tokens, duration]
       │    └── tool.{name} [TOOL — args, result, outcome]
       └── api.{model} [LLM — second round-trip, final response]
```

**Per-turn summary attributes** (on root span):
- `hermes.turn.tool_count` — distinct tools invoked
- `hermes.turn.tools` — sorted CSV of tool names
- `hermes.turn.skill_count` — distinct skills used
- `hermes.turn.api_call_count` — API request count
- `hermes.turn.final_status` — completed/interrupted/incomplete/timed_out

---

## 4. Configuration Examples — Self-Hosted Docker Setup

### 4.1 Quick Start (Local Development)

```bash
git clone --depth=1 https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up
# Langfuse UI at http://localhost:3000
```

### 4.2 Production Docker Compose

Create `docker-compose.yml`:
```yaml
services:
  langfuse-web:
    image: docker.langfuse.com/langfuse/langfuse:4
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy
      redis:
        condition: service_healthy
      clickhouse:
        condition: service_healthy
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse@postgres:5432/langfuse
      NEXTAUTH_URL: http://localhost:3000
      NEXTAUTH_SECRET: ${NEXTAUTH_SECRET}         # CHANGEME: openssl rand -base64 32
      SALT: ${SALT}                               # CHANGEME
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}           # CHANGEME: openssl rand -hex 32
      LANGFUSE_S3_EVENT_UPLOAD_BUCKET: langfuse
      LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT: http://minio:9000
      LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID: ${MINIO_ROOT_USER}
      LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY: ${MINIO_ROOT_PASSWORD}
      LANGFUSE_S3_MEDIA_UPLOAD_ENDPOINT: http://localhost:9090
      REDIS_HOST: redis
      REDIS_PORT: 6379
      CLICKHOUSE_HOST: clickhouse
      CLICKHOUSE_PORT: 8123
      CLICKHOUSE_USER: clickhouse
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD}
      NODE_OPTIONS: "--max-old-space-size=2048"

  langfuse-worker:
    image: docker.langfuse.com/langfuse/langfuse-worker:4
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy
      redis:
        condition: service_healthy
      clickhouse:
        condition: service_healthy
    ports:
      - "127.0.0.1:3030:3030"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse@postgres:5432/langfuse
      NEXTAUTH_URL: http://localhost:3000
      NEXTAUTH_SECRET: ${NEXTAUTH_SECRET}
      SALT: ${SALT}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      LANGFUSE_S3_EVENT_UPLOAD_BUCKET: langfuse
      LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT: http://minio:9000
      LANGFUSE_S3_EVENT_UPLOAD_ACCESS_KEY_ID: ${MINIO_ROOT_USER}
      LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY: ${MINIO_ROOT_PASSWORD}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      CLICKHOUSE_HOST: clickhouse
      CLICKHOUSE_PORT: 8123
      CLICKHOUSE_USER: clickhouse
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD}
      NODE_OPTIONS: "--max-old-space-size=2048"

  postgres:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse
      POSTGRES_DB: langfuse
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langfuse"]
      interval: 5s
      timeout: 5s
      retries: 5

  clickhouse:
    image: clickhouse/clickhouse-server:25.12
    restart: always
    environment:
      CLICKHOUSE_DB: default
      CLICKHOUSE_USER: clickhouse
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD}
    volumes:
      - clickhouse_data:/var/lib/clickhouse
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8123/ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --maxmemory-policy noeviction
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio
    restart: always
    entrypoint: sh
    command: -c 'mkdir -p /data/langfuse && minio server --address ":9000" --console-address ":9001" /data'
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  clickhouse_data:
  redis_data:
  minio_data:
```

Create `.env`:
```bash
# Generate secrets
NEXTAUTH_SECRET=$(openssl rand -base64 32)
SALT=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
CLICKHOUSE_PASSWORD=$(openssl rand -base64 32)
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)
```

### 4.3 Production Recommendations

- **Kubernetes (Helm)**: Preferred for production — HA, scaling, backup
- **Resource sizing**: 2 CPU + 3 GB RAM minimum per container
- **Storage**: 100+ GiB for observability data
- **Redis**: Set `maxmemory-policy: noeviction` — critical to prevent queue loss
- **ClickHouse**: v4 requires 25.12+ (lightweight updates, JSON type, full-text search)
- **Backups**: S3 events provide replay capability; ClickHouse data needs separate backup strategy
- **Monitoring**: Monitor worker queue depth, ClickHouse disk usage, API latency

---

## 5. Exporting Nerve Telemetry to Langfuse

### 5.1 Understanding the Nerve → Langfuse Bridge

Nerve telemetry (events, challenges, controls, receipts) is Hermes Agent's built-in observability system. To bridge it to Langfuse:

**Option A: Via hermes-otel Plugin (Recommended)**

The plugin already captures Nerve lifecycle events as OTel spans. Configure the Langfuse backend as shown in Section 3.2. Nerve events automatically flow to Langfuse as traces with:
- Session/turn spans
- LLM call spans with token usage
- Tool call spans with args/results
- Per-turn summary attributes

**Option B: Custom Nerve-to-Langfuse Exporter**

For direct Nerve event export, create a custom exporter:

```python
from langfuse import get_client
import json

langfuse = get_client()

def export_nerve_event(event: dict):
    """Export a Nerve telemetry event to Langfuse as a trace."""
    event_type = event.get("type")
    session_id = event.get("session_id", "unknown")
    trace_id = event.get("trace_id")
    
    if event_type == "llm_call":
        with langfuse.start_as_current_observation(
            as_type="generation",
            name=f"llm.{event.get('model', 'unknown')}",
            model=event.get("model"),
            input=event.get("input"),
            usage_details={
                "input": event.get("prompt_tokens", 0),
                "output": event.get("completion_tokens", 0),
                "total": event.get("total_tokens", 0),
            },
        ) as gen:
            gen.update(output=event.get("output"))
            
    elif event_type == "tool_call":
        with langfuse.start_as_current_observation(
            as_type="span",
            name=f"tool.{event.get('tool_name', 'unknown')}",
            input=event.get("args"),
        ) as span:
            span.update(output=event.get("result"))
            
    elif event_type == "challenge":
        # Log challenges as trace metadata
        langfuse.update_current_trace(
            metadata={"challenge": event.get("description")},
        )
        
    elif event_type == "control":
        # Log controls as events within the trace
        langfuse.update_current_trace(
            metadata={"control_action": event.get("action")},
        )
        
    elif event_type == "receipt":
        # Log receipts as trace scores
        langfuse.score(
            trace_id=trace_id,
            name="receipt",
            value=event.get("status") == "success",
            data_type="BOOLEAN",
        )
```

**Option C: Batch Export from Nerve Event Log**

```python
import json
from langfuse import get_client

langfuse = get_client()

def batch_export_nerve_events(nerve_log_path: str):
    """Batch export Nerve events from JSONL log to Langfuse."""
    with open(nerve_log_path) as f:
        for line in f:
            event = json.loads(line)
            export_nerve_event(event)
    langfuse.flush()
```

### 5.2 Mapping Nerve Concepts to Langfuse

| Nerve Concept | Langfuse Mapping |
|---|---|
| Event | Trace or Observation |
| Challenge | Trace metadata / Score |
| Control | Trace metadata / Event |
| Receipt | Score (boolean) |
| Session | Session ID |
| Agent turn | Trace |
| LLM call | Generation observation |
| Tool call | Span observation |
| Token usage | Usage details on generation |
| Cost | Computed from usage × model pricing |

---

## 6. Pitfalls and Best Practices

### 6.1 Common Pitfalls

| Pitfall | Problem | Fix |
|---|---|---|
| **No `flush()` in scripts** | Traces never sent | Call `langfuse.flush()` before exit |
| **Flat traces** | Can't see which step failed | Use nested spans for distinct steps |
| **Generic trace names** | Hard to filter | Use descriptive verb-first names: `classify-intent`, `retrieve-context` |
| **Logging sensitive data** | Data leakage risk | Mask PII before tracing; use `capture_input=False` |
| **Not setting input explicitly** | All function args become trace input (including API keys) | Use `langfuse.update_current_span(input=...)` with only relevant data |
| **Manual instrumentation when integration exists** | More code, less context | Use framework integrations (OpenAI drop-in, LangChain callback) |
| **Langfuse import before env vars** | Initializes with wrong credentials | Import Langfuse AFTER loading `.env` |
| **Redis maxmemory-policy not noeviction** | Queue events silently lost under memory pressure | Set `maxmemory-policy: noeviction` |
| **Worker not monitored** | Silent queue backup | Monitor worker container and Redis queue depth |
| **Cost attribution without tagging** | Useless cost reports | Tag every trace with feature, repo, objective in metadata |
| **Observations vs traces confusion** | Billing surprises | Langfuse bills on observations (10-20 per agent trace), not traces |
| **v3 → v4 SDK migration** | Broken code | `start_span` → `start_as_current_observation`, `update_current_trace` → `propagate_attributes` |

### 6.2 Best Practices

**Trace Structure:**
1. **One trace per agent turn** — keeps traces small and navigable
2. **One session per conversation** — group related traces
3. **Use correct observation types** — `generation` for LLM calls, `span` for tools, `agent` for subagents
4. **Name observations verb-first** — `retrieve-context`, `generate-response`, `classify-intent`
5. **Set environment attribute** — `production`, `staging`, `development` to prevent test data pollution

**Cost Management:**
1. **Tag traces with metadata** — `feature`, `repo`, `user_id`, `objective` for cost attribution
2. **Set up cost alerts** — threshold-based alerts on daily spend
3. **Monitor output tokens** — typically 3-4x more expensive than input
4. **Use sampling for high-volume evals** — 2-3% sampling provides 80%+ confidence for regression detection
5. **Tiered evaluation** — cheap fast judge first, expensive deep eval only on failures

**Evaluation:**
1. **Start with tracing, not scoring** — manually review traces first to understand failure patterns
2. **Build datasets from real failures** — production traces with low scores → golden dataset
3. **Calibrate LLM-as-a-Judge** — validate against human-annotated sample before trusting trend lines
4. **Run evals in CI/CD** — block deployments that cause score regressions
5. **Use all three evaluation levels** — final response (what), trajectory (where), single step (why)

**Production Operations:**
1. **Monitor the worker** — queue depth, processing latency, error rate
2. **Set up ClickHouse backups** — S3 events provide replay but not full restore
3. **Use separate projects for staging/prod** — prevent data cross-contamination
4. **Rotate API keys periodically** — never expose secret key in client-side code
5. **Enable `force_flush_on_session_end`** — traces appear immediately, not after next batch cycle

**Privacy:**
1. **Use `capture_previews: false`** in production if prompts contain sensitive data
2. **Mask PII before tracing** — the SDK captures raw function arguments
3. **Use `capture_input=False`** on decorators handling sensitive data
4. **Content-free monitoring plane** — Hermes's gateway monitoring exports only metadata, never prompts/messages

### 6.3 Langfuse v4 SDK Migration Checklist

If upgrading from v3 to v4:
- [ ] `langfuse.trace()` → `langfuse.start_as_current_observation()`
- [ ] `start_span()` / `start_generation()` → `start_as_current_observation(as_type=...)`
- [ ] `update_current_trace()` → `propagate_attributes()` context manager
- [ ] `langfuse.flush()` still required in short-lived scripts
- [ ] `get_client()` is the intended entry point (not `Langfuse()`)
- [ ] Smart span filtering is default — use `should_export_span` to customize
- [ ] `langfuse.anthropic` never existed — use `@observe` or OTel instrumentor

---

## 7. Quick Reference

### Environment Variables
```bash
# Langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=http://localhost:3000

# Hermes OTel Plugin
HERMES_OTEL_DEBUG=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:3000/api/public/otel
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <base64(pk:sk)>,x-langfuse-ingestion-version=4
```

### Key URLs
- Langfuse UI: http://localhost:3000
- Langfuse API: http://localhost:3000/api/public
- OTLP endpoint: http://localhost:3000/api/public/otel
- Docs: https://langfuse.com/docs

### SDK Install
```bash
# Python
pip install langfuse

# JS/TS
npm install @langfuse/tracing @langfuse/otel @opentelemetry/sdk-node
```

---

*Guide compiled from Langfuse official documentation, hermes-otel plugin docs, and production deployment patterns. Last updated: October 2026.*

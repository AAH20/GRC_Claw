# LiteLLM + Hermes Agent Integration Guide
## Central LLM Gateway for 330 Agent Slots Across 12 Squads

---

## 1. Architecture Overview

### What LiteLLM Is

LiteLLM (BerriAI, ~59K GitHub stars, YC W23) is an open-source AI gateway that provides a **single OpenAI-compatible interface** to 100+ LLM providers. It ships in two forms:

- **Python SDK** (`litellm.completion()`) — in-process library for direct integration
- **AI Gateway / Proxy Server** — standalone FastAPI service that wraps the SDK with auth, rate limiting, budgets, routing, and observability

For Ahmed's 330-agent-slot stack, the **Proxy Server** is the right deployment model.

### How It Works as a AI Gateway

```
Hermes Agent (330 slots)  ──▶  LiteLLM Proxy (:4000)  ──▶  LiteLLM SDK  ──▶  Provider APIs
                                    │
                                    ├── PostgreSQL (keys, teams, spend logs)
                                    ├── Redis (rate limits, cooldowns, caching)
                                    └── Admin UI (:3000)
```

**Request flow through the proxy:**

1. **HTTP ingestion** — FastAPI receives OpenAI-compatible requests at `/v1/chat/completions`
2. **Authentication** — Virtual key validated against Redis cache → PostgreSQL on miss
3. **Rate limiting** — Parallel request limiter checks RPM/TPM for key, user, team, and server
4. **Router** — Selects model deployment using configured strategy (simple-shuffle, latency-based, usage-based, cost-based)
5. **Translation** — Provider-specific transformation converts OpenAI format → native provider format
6. **LLM call** — httpx async client calls the provider API
7. **Response normalization** — Provider response → OpenAI ChatCompletion format
8. **Post-processing** — Async logging, spend tracking, cache updates

### Three Planes

| Plane | Responsibility | Key Components |
|-------|---------------|----------------|
| **Control** | Config, routing rules, budget management | `proxy_server.py`, `router.py`, `ProxyConfig` |
| **Data** | Request/response streaming, caching, retries | `main.py`, `BaseLLMHTTPHandler`, `Cache` |
| **Observability** | Logging, cost tracking, guardrails | `proxy_track_cost_callback.py`, Prometheus metrics, Langfuse/Datadog integrations |

### Core Abstractions

- **ModelGroup** — Multiple deployments sharing one `model_name`, load-balanced
- **VirtualKey** — Ephemeral API key with per-key budget limits, rate limits, model allowlists
- **StreamingChunk** — Normalized async generator homogenizing SSE across providers
- **CooldownCache** — Redis-backed health tracking for failed deployments

### Performance Characteristics

| Metric | Value | Context |
|--------|-------|---------|
| Proxy overhead (P50) | 8-12ms | JSON serialization + routing on localhost |
| Proxy overhead (P95) | 25-40ms | Under 1000 concurrent connections |
| Max throughput | 10,000 req/s | With 8 vCPU instances |
| Memory footprint | 150-300MB | Base proxy without caching |
| Redis latency impact | +2-5ms | Semantic cache lookup |
| Streaming first chunk | +15ms | Header normalization |

---

## 2. Key Features for Ahmed's Stack

### 2.1 Cost Tracking

LiteLLM automatically tracks spend for all known models using a hand-maintained pricing map (`model_prices_and_context_window.json`).

**What's tracked per request:**
- `end_user` — customer identifier
- `model_group` — the model name passed to LiteLLM
- `api_base` — the actual provider endpoint
- Token counts (input/output/total)
- Computed cost in USD
- Custom tags (via `metadata.tags` or `x-litellm-tags` header)
- User-Agent (auto-tracked for tools like Claude Code, Gemini CLI)

**Spend hierarchy:**
- **Per-key spend** — tracked in `LiteLLM_VerificationTokenTable`
- **Per-user spend** — aggregated across all keys owned by a user
- **Per-team spend** — aggregated across all keys in a team
- **Per-model spend** — tracked per model group
- **Per-provider spend** — via `provider_budget_config`
- **Per-tag spend** — cost center / project attribution

**Cost optimization features:**
- `cost_discount_config` — provider-specific discounts (e.g., Vertex AI 5% off)
- `cost_margin_config` — markup on provider costs
- Response caching — 40-60% cost reduction for repetitive RAG workflows
- Cost-based routing — route to cheapest available provider

### 2.2 Rate Limiting

**Multi-level rate limits:**

| Level | Scope | Use Case |
|-------|-------|----------|
| Global server | Entire proxy | Protect upstream providers |
| Virtual key | Per API key | Per-agent or per-squad limits |
| User | Per user_id | Individual engineer caps |
| Team | Per team_id | Squad-level shared limits |
| Model | Per model group | Prevent single model exhaustion |

**Rate limit types:**
- **RPM** (requests per minute)
- **TPM** (tokens per minute) — input, output, or total
- **Max parallel requests** — concurrency cap
- **ITPM/OTPM** — separate input/output token limits

**Rate limit tiers** (Enterprise): Define reusable tiers with rate limits, assign to keys.

### 2.3 Model Routing

**Routing strategies:**

| Strategy | Description | Best For |
|----------|-------------|----------|
| `simple-shuffle` (default) | Weighted random pick | High-traffic, minimal overhead |
| `least-busy` | Fewest active requests | Balanced load |
| `latency-based` | Lowest rolling latency | Latency-sensitive apps |
| `usage-based-routing-v2` | Factors latency + remaining rate limit | Production recommended |
| `cost-based` | Cheapest provider with capacity | Cost optimization |
| `lowest-cost` (async) | Lowest cost per token | Batch processing |
| Custom | Pluggable strategy | Special needs |

**Routing groups** — Different strategies for different model sets:
```yaml
routing_groups:
  - group_name: latency-sensitive
    models: [gpt-4o]
    routing_strategy: latency-based-routing
    routing_strategy_args:
      ttl: 3600
  - group_name: batch
    models: [gpt-4o-mini, llama-70b]
    routing_strategy: usage-based-routing-v2
    routing_strategy_args:
      rpm: 10000
```

### 2.4 Fallback Chains

**Three fallback families:**

1. **Standard fallbacks** — General errors (rate limits, timeouts, 5xx)
2. **Content-policy fallbacks** — Provider content-policy violations
3. **Context-window fallbacks** — Route to larger-context model when request exceeds window

**Fallback behavior:**
- Retries stay **within** the model group (same `model_name`, different deployment)
- Fallbacks move to a **different** model group
- Cooldown: Failed deployments are cooled down (default: 3 failures/min, 5s cooldown)
- Budget fallbacks (v1.92+): Reroute to fallback model when key's `model_max_budget` exceeded

**Fallback chain example:**
```
gpt-4o (OpenAI) → gpt-4o (Azure) → claude-sonnet (Anthropic) → gpt-4o-mini (OpenAI)
```

### 2.5 Additional Features

- **Semantic caching** — Qdrant/Redis embedding similarity matching (40-60% cost reduction)
- **Guardrails** — PII detection, prompt injection defense, content moderation
- **80+ logging integrations** — Langfuse, Datadog, MLflow, S3, etc.
- **MCP gateway** — Expose MCP tool servers through the proxy
- **A2A agent gateway** — Agent-to-agent invocation
- **Admin UI** — React dashboard for key management, spend viewing, model config

---

## 3. Integration Guide: Deploying Alongside Hermes Agent

### 3.1 Architecture for 330 Agent Slots

```
┌─────────────────────────────────────────────────────────┐
│                    Ahmed's Infrastructure                │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Hermes Agent │  │  Hermes Agent │  │  Hermes Agent │  │
│  │  Squad 1     │  │  Squad 2     │  │  ... Squad 12 │  │
│  │  (28 slots)  │  │  (28 slots)  │  │  (28 slots)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │           │
│         └──────────────────┼──────────────────┘           │
│                            │                              │
│                   ┌────────▼────────┐                     │
│                   │  Load Balancer  │                     │
│                   │  (nginx/ALB)    │                     │
│                   └────────┬────────┘                     │
│                            │                              │
│              ┌─────────────┼─────────────┐                │
│              │             │             │                │
│         ┌────▼────┐  ┌────▼────┐  ┌────▼────┐           │
│         │LiteLLM  │  │LiteLLM  │  │LiteLLM  │           │
│         │Proxy 1  │  │Proxy 2  │  │Proxy 3  │           │
│         │:4000    │  │:4000    │  │:4000    │           │
│         └────┬────┘  └────┬────┘  └────┬────┘           │
│              │             │             │                │
│              └─────────────┼─────────────┘                │
│                            │                              │
│                   ┌────────▼────────┐                     │
│                   │   PostgreSQL    │                     │
│                   │   (spend logs,  │                     │
│                   │    keys, teams) │                     │
│                   └─────────────────┘                     │
│                                                          │
│                   ┌─────────────────┐                     │
│                   │     Redis       │                     │
│                   │ (rate limits,   │                     │
│                   │  cooldowns,     │                     │
│                   │  caching)       │                     │
│                   └─────────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Step-by-Step Deployment

#### Step 1: Install LiteLLM

```bash
# Pin to a specific version — NEVER use :latest in production
pip install 'litellm[proxy]==1.84.0'

# Or use Docker (recommended for production)
docker pull ghcr.io/berriai/litellm-database:1.84.0
```

#### Step 2: Create config.yaml

See Section 4 for full configuration.

#### Step 3: Start PostgreSQL and Redis

```bash
# Docker Compose for infrastructure
docker-compose up -d postgres redis
```

#### Step 4: Run Prisma Migrations

```bash
# One-time setup
prisma migrate deploy
```

#### Step 5: Start LiteLLM Proxy

```bash
litellm --config /path/to/config.yaml --port 4000 --num_workers 1
```

#### Step 6: Configure Hermes Agent

For each of the 330 agent slots, configure Hermes to use LiteLLM as a custom provider:

**Option A: Per-agent config.yaml**
```yaml
# ~/.hermes/config.yaml (per agent)
model:
  default: gpt-4o
  provider: custom
  base_url: http://litellm-proxy:4000/v1
  api_key: sk-litellm-virtual-key-for-squad-1
```

**Option B: Environment variable (recommended for 330 slots)**
```bash
# In each agent's .env file
LITELLM_API_KEY=sk-litellm-virtual-key-for-squad-1
HERMES_BASE_URL=http://litellm-proxy:4000/v1
HERMES_MODEL=gpt-4o
```

**Option C: Hermes custom_providers block**
```yaml
# ~/.hermes/config.yaml
custom_providers:
  - name: litellm
    base_url: http://litellm-proxy:4000/v1
    api_key: ${LITELLM_API_KEY}
    key_env: LITELLM_API_KEY
    model: gpt-4o
    api_mode: chat_completions
```

#### Step 7: Create Virtual Keys per Squad

```bash
# Create a key for Squad 1 (28 agent slots)
curl -X POST http://litellm-proxy:4000/key/generate \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "key_alias": "squad-1-production",
    "team_id": "squad-1",
    "models": ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4", "claude-haiku-4-5"],
    "max_budget": 500.00,
    "budget_duration": "30d",
    "rpm_limit": 280,
    "tpm_limit": 500000,
    "metadata": {
      "squad": "squad-1",
      "owner": "ahmed",
      "cost_center": "engineering"
    }
  }'
```

#### Step 8: Verify Integration

```bash
# Test through LiteLLM proxy
curl -X POST http://litellm-proxy:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-litellm-virtual-key-for-squad-1" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello from Squad 1"}]
  }'

# Check spend tracking
curl http://litellm-proxy:4000/global/spend/report?start_date=2026-10-01&end_date=2026-10-01 \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

### 3.3 Scaling for 330 Slots

**Capacity planning:**

| Metric | Per Agent | 330 Agents | LiteLLM Capacity |
|--------|-----------|-------------|------------------|
| Concurrent requests | ~1-2 | 330-660 | 10,000+ req/s |
| Tokens/minute | ~50K-100K | 16M-33M | Redis-backed TPM tracking |
| Monthly spend | ~$50-200 | $16K-66K | Full cost visibility |

**Recommended setup:**
- **3-5 LiteLLM proxy replicas** behind a load balancer
- **PostgreSQL** with connection pooling (PgBouncer)
- **Redis** for distributed rate limiting and caching
- **1 vCPU + 4Gi RAM per worker**, one worker per pod
- **HPA** with CPU target 60%, memory target 80%

---

## 4. Configuration Examples

### 4.1 Full Multi-Provider config.yaml

```yaml
# LiteLLM Proxy Configuration for Ahmed's 330-Agent Stack
# Version: 1.84.0

# ============================================================
# MODEL LIST — All providers and model groups
# ============================================================
model_list:

  # ---- Primary: GPT-4o via OpenAI ----
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
      rpm: 500
      tpm: 150000
    model_info:
      mode: chat
      input_cost_per_token: 0.0000025
      output_cost_per_token: 0.00001

  # ---- Primary: GPT-4o via Azure OpenAI (fallback) ----
  - model_name: gpt-4o
    litellm_params:
      model: azure/gpt-4o
      api_base: os.environ/AZURE_OPENAI_ENDPOINT
      api_key: os.environ/AZURE_OPENAI_API_KEY
      api_version: "2024-02-01"
      rpm: 300
      tpm: 100000
    model_info:
      mode: chat

  # ---- Claude Sonnet 4 via Anthropic ----
  - model_name: claude-sonnet-4
    litellm_params:
      model: anthropic/claude-sonnet-4-20250514
      api_key: os.environ/ANTHROPIC_API_KEY
      rpm: 200
      tpm: 100000
    model_info:
      mode: chat
      input_cost_per_token: 0.000003
      output_cost_per_token: 0.000015

  # ---- Claude Haiku 4.5 (cost-effective) ----
  - model_name: claude-haiku-4-5
    litellm_params:
      model: anthropic/claude-haiku-4-5-20251001
      api_key: os.environ/ANTHROPIC_API_KEY
      rpm: 500
      tpm: 200000
    model_info:
      mode: chat
      input_cost_per_token: 0.000001
      output_cost_per_token: 000005

  # ---- GPT-4o-mini (high-volume, low-cost) ----
  - model_name: gpt-4o-mini
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY
      rpm: 1000
      tpm: 500000
    model_info:
      mode: chat
      input_cost_per_token: 0.00000015
      output_cost_per_token: 0.0000006

  # ---- Gemini 2.5 Pro (Google AI Studio) ----
  - model_name: gemini-2.5-pro
    litellm_params:
      model: gemini/gemini-2.5-pro
      api_key: os.environ/GEMINI_API_KEY
      rpm: 300
      tpm: 100000
    model_info:
      mode: chat

  # ---- Self-hosted Llama (free fallback) ----
  - model_name: llama-self-hosted
    litellm_params:
      model: openai/meta-llama/Llama-3.1-70B-Instruct
      api_base: http://vllm-cluster:8000/v1
      api_key: os.environ/VLLM_API_KEY
      rpm: 100
      tpm: 50000
    model_info:
      mode: chat
      input_cost_per_token: 0
      output_cost_per_token: 0

  # ---- Embedding model ----
  - model_name: text-embedding
    litellm_params:
      model: openai/text-embedding-3-small
      api_key: os.environ/OPENAI_API_KEY
    model_info:
      mode: embedding

# ============================================================
# ROUTER SETTINGS — Load balancing, fallbacks, retries
# ============================================================
router_settings:
  routing_strategy: usage-based-routing-v2
  routing_strategy_args:
    rpm: 10000
  num_retries: 3
  request_timeout: 600
  cooldown_time: 30
  allowed_fails: 3

  # Fallback chains
  fallbacks:
    - gpt-4o: ["claude-sonnet-4", "gpt-4o-mini"]
    - claude-sonnet-4: ["gpt-4o", "claude-haiku-4-5"]
    - gpt-4o-mini: ["claude-haiku-4-5", "llama-self-hosted"]
    - gemini-2.5-pro: ["gpt-4o", "claude-sonnet-4"]

  # Context window fallbacks
  context_window_fallbacks:
    - gpt-4o: ["claude-sonnet-4", "gemini-2.5-pro"]

  # Content policy fallbacks
  content_policy_fallbacks:
    - gpt-4o: ["claude-sonnet-4"]
    - claude-sonnet-4: ["gpt-4o"]

  # Default fallbacks for misconfigured model groups
  default_fallbacks: ["gpt-4o-mini", "claude-haiku-4-5"]

  # Provider budget routing
  provider_budget_config:
    openai:
      budget_limit: 5000.0
      time_period: "30d"
    anthropic:
      budget_limit: 3000.0
      time_period: "30d"
    azure:
      budget_limit: 2000.0
      time_period: "30d"
    gemini:
      budget_limit: 1000.0
      time_period: "30d"

  # Redis for multi-instance coordination
  redis_host: os.environ/REDIS_HOST
  redis_port: os.environ/REDIS_PORT
  redis_password: os.environ/REDIS_PASSWORD

# ============================================================
# LITELLM SETTINGS — Caching, callbacks, timeouts
# ============================================================
litellm_settings:
  drop_params: true
  set_verbose: false
  json_logs: true

  # Response caching
  cache: true
  cache_params:
    type: redis
    host: os.environ/REDIS_HOST
    port: os.environ/REDIS_PORT
    password: os.environ/REDIS_PASSWORD
    ttl: 600
    namespace: "litellm.caching"

  # Callbacks for observability
  success_callback: ["langfuse", "datadog"]
  failure_callback: ["langfuse", "slack"]

  # Cost tracking
  cost_discount_config:
    vertex_ai: 0.05
    gemini: 0.05
  cost_margin_config:
    global: 0.05

# ============================================================
# GENERAL SETTINGS — Auth, database, alerting
# ============================================================
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
  store_model_in_db: true

  # Performance
  user_api_key_cache_ttl: 600
  database_connection_pool_limit: 20
  database_connection_timeout: 60
  proxy_batch_write_at: 30
  use_redis_transaction_buffer: true

  # Health checks
  background_health_checks: true
  health_check_interval: 300

  # Spend log retention
  maximum_spend_logs_retention_period: "60d"
  maximum_spend_logs_retention_interval: "1d"
  maximum_spend_logs_cleanup_cron: "0 4 * * *"

  # Security
  block_robots: true
  allow_requests_on_db_unavailable: true

  # Alerting
  alerting: ["slack"]
  alerting_threshold: 100
  alerting_args:
    slack_webhook_url: os.environ/SLACK_WEBHOOK_URL
    alert_types:
      - budget_exceeded
      - rate_limit_hit
      - provider_fallback
      - db_connection_error

  # Key generation upperbounds
  upperbound_key_generate_params:
    max_budget: 1000
    tpm_limit: 1000000
    rpm_limit: 10000
```

### 4.2 Docker Compose for Full Stack

```yaml
version: "3.9"

services:
  litellm:
    image: ghcr.io/berriai/litellm-database:1.84.0
    ports:
      - "4000:4000"
    volumes:
      - ./config.yaml:/app/config.yaml
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - VLLM_API_KEY=${VLLM_API_KEY}
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
      - DATABASE_URL=postgresql://litellm:${DB_PASSWORD}@postgres:5432/litellm
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
    command: --config /app/config.yaml --port 4000 --num_workers 1 --max_requests_before_restart 10000
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health/liveliness"]
      interval: 30s
      timeout: 10s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 4Gi
          cpu: "1"
        reservations:
          memory: 2Gi
          cpu: "500m"

  postgres:
    image: postgres:16
    environment:
      - POSTGRES_USER=litellm
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=litellm
    volumes:
      - litellm_db:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U litellm"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - litellm_redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Optional: Nginx load balancer for multiple LiteLLM replicas
  nginx:
    image: nginx:1.27
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - litellm

volumes:
  litellm_db:
  litellm_redis:
```

### 4.3 Kubernetes Deployment (Helm)

```yaml
# values.yaml for litellm-helm chart
replicaCount: 3

image:
  repository: ghcr.io/berriai/litellm-database
  tag: "1.84.0"
  pullPolicy: IfNotPresent

resources:
  requests:
    cpu: "1"
    memory: "4Gi"
  limits:
    cpu: "1"
    memory: "4Gi"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 60
  targetMemoryUtilizationPercentage: 80

config:
  model_list:
    - model_name: gpt-4o
      litellm_params:
        model: openai/gpt-4o
        api_key: os.environ/OPENAI_API_KEY
    - model_name: claude-sonnet-4
      litellm_params:
        model: anthropic/claude-sonnet-4-20250514
        api_key: os.environ/ANTHROPIC_API_KEY
  router_settings:
    routing_strategy: usage-based-routing-v2
    num_retries: 3
    fallbacks:
      - gpt-4o: ["claude-sonnet-4", "gpt-4o-mini"]
  general_settings:
    master_key: os.environ/LITELLM_MASTER_KEY
    database_url: os.environ/DATABASE_URL

env:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: litellm-secrets
        key: openai-api-key
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: litellm-secrets
        key: anthropic-api-key
  - name: LITELLM_MASTER_KEY
    valueFrom:
      secretKeyRef:
        name: litellm-secrets
        key: litellm-master-key
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: litellm-secrets
        key: database-url

livenessProbe:
  httpGet:
    path: /health/liveliness
    port: 4000
  initialDelaySeconds: 60
  periodSeconds: 30
  timeoutSeconds: 10
  failureThreshold: 5

readinessProbe:
  httpGet:
    path: /health/readiness
    port: 4000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 10
  failureThreshold: 3
```

### 4.4 Per-Squad Virtual Key Creation Script

```bash
#!/bin/bash
# create-squad-keys.sh — Create virtual keys for all 12 squads

MASTER_KEY=$LITELLM_MASTER_KEY
PROXY_URL=${PROXY_URL:-http://localhost:4000}

# Squad configurations: name|budget|rpm|tpm|models
SQUADS=(
  "squad-1|500|280|500000|gpt-4o,gpt-4o-mini,claude-sonnet-4,claude-haiku-4-5"
  "squad-2|500|280|500000|gpt-4o,gpt-4o-mini,claude-sonnet-4,claude-haiku-4-5"
  "squad-3|400|200|400000|gpt-4o,gpt-4o-mini,claude-haiku-4-5"
  "squad-4|400|200|400000|gpt-4o,gpt-4o-mini,claude-haiku-4-5"
  "squad-5|300|150|300000|gpt-4o-mini,claude-haiku-4-5"
  "squad-6|300|150|300000|gpt-4o-mini,claude-haiku-4-5"
  "squad-7|600|350|600000|gpt-4o,gpt-4o-mini,claude-sonnet-4,claude-haiku-4-5,gemini-2.5-pro"
  "squad-8|600|350|600000|gpt-4o,gpt-4o-mini,claude-sonnet-4,claude-haiku-4-5,gemini-2.5-pro"
  "squad-9|200|100|200000|gpt-4o-mini,claude-haiku-4-5"
  "squad-10|200|100|200000|gpt-4o-mini,claude-haiku-4-5"
  "squad-11|450|250|450000|gpt-4o,gpt-4o-mini,claude-sonnet-4,claude-haiku-4-5"
  "squad-12|450|250|450000|gpt-4o,gpt-4o-mini,claude-sonnet-4,claude-haiku-4-5"
)

for squad_config in "${SQUADS[@]}"; do
  IFS='|' read -r name budget rpm tpm models <<< "$squad_config"
  
  echo "Creating key for $name (budget: $$budget, rpm: $rpm, tpm: $tpm)..."
  
  curl -s -X POST "$PROXY_URL/key/generate" \
    -H "Authorization: Bearer $MASTER_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"key_alias\": \"$name-production\",
      \"team_id\": \"$name\",
      \"models\": [$(echo $models | sed 's/,/","/g' | sed 's/^/"/;s/$/"/')],
      \"max_budget\": $budget,
      \"budget_duration\": \"30d\",
      \"rpm_limit\": $rpm,
      \"tpm_limit\": $tpm,
      \"metadata\": {
        \"squad\": \"$name\",
        \"owner\": \"ahmed\",
        \"cost_center\": \"engineering\"
      }
    }" | jq .
  
  echo ""
done
```

---

## 5. Pitfalls and Best Practices

### 5.1 Critical Pitfalls

#### 1. Supply Chain Attack (March 2026)
**Versions 1.82.7 and 1.82.8 were compromised** — contained a credential harvester and Kubernetes lateral-movement toolkit. Pulled from PyPI after ~3 hours.

**Mitigation:** Pin exact version hashes, never use floating versions. Safe: ≤1.82.6 or ≥1.84.0.

#### 2. Connection Pool Exhaustion
Default `MAX_CONNECTIONS=10` causes request drops at 300+ concurrent requests. With 330 agent slots, this will bite immediately.

**Mitigation:** Set `MAX_CONNECTIONS=200` per replica. Scale horizontally to 3+ replicas.

#### 3. Memory Leaks Under Sustained Load
Python's object retention causes RAM growth over days. At 120+ req/s sustained, OOM kills occur.

**Mitigation:** Use `--max_requests_before_restart 10000`. Set memory limits to 4Gi minimum.

#### 4. Spend Tracking Database Bottleneck
At 1000+ req/s or 10+ instances, every instance issues UPDATE/UPSERT against the same rows → deadlocks → `FATAL: sorry, too many clients already`.

**Mitigation:** Enable `use_redis_transaction_buffer: true`. Route spend writes through Redis.

#### 5. Config Changes Don't Hot-Reload
Mounting config.yaml as a ConfigMap and changing it does NOT hot-reload. Must send SIGHUP.

**Mitigation:** `kubectl exec <pod> -- kill -HUP 1` or restart pods.

#### 6. Liveness Probe False Positives
`/health/readiness` pings upstream. If upstream is slow (OpenAI rate limit), probe fails → Kubernetes kills pod.

**Mitigation:** Set `timeoutSeconds: 10`, `failureThreshold: 3` on probes.

#### 7. Cache Staleness Across Model Versions
Switching model versions mid-deploy serves stale cached responses until TTL expires.

**Mitigation:** Set `cache: false` during model migrations, flush Redis with `FLUSHDB`.

#### 8. Prisma Not Auto-Installed
`pip install 'litellm[proxy]'` does NOT pull Prisma. Proxy crashes on startup with `ModuleNotFoundError: No module named 'prisma'`.

**Mitigation:** `pip install prisma psycopg2-binary` then `prisma generate`.

#### 9. MCP Authentication Bypass (CVE-2026-59822)
v1.84.0 fixed a high-severity MCP auth bypass. If using MCP gateway, upgrade immediately.

#### 10. ARM64 Image Issues
Official Docker image ships linux/amd64 only. On Apple M-series or Graviton, container fails with `exec format error`.

**Mitigation:** Add `platform: linux/amd64` in docker-compose (QEMU) or build from source with `docker buildx build --platform linux/arm64`.

### 5.2 Best Practices

#### Security
- [ ] Pin exact LiteLLM version (never `:latest`)
- [ ] Use environment variables for ALL API keys (never in config.yaml)
- [ ] Enable JWT authentication for production
- [ ] Run on private network, expose only needed routes
- [ ] Enable TLS for client-to-gateway and gateway-to-provider
- [ ] Rotate master key regularly
- [ ] Set `upperbound_key_generate_params` to prevent key generation abuse
- [ ] Enable `block_robots: true`
- [ ] Monitor CVE advisories and upgrade promptly

#### Performance
- [ ] One Uvicorn worker per pod, scale horizontally
- [ ] 1 vCPU + 4Gi RAM per worker (minimum)
- [ ] Use `simple-shuffle` routing for high-traffic (lowest overhead)
- [ ] Enable Redis caching (40-60% cost reduction for repetitive prompts)
- [ ] Set `request_timeout: 600` (default 6000s is too long)
- [ ] Use `drop_params: true` to avoid provider errors on unsupported params
- [ ] Enable `use_redis_transaction_buffer: true` for spend tracking
- [ ] Set `--max_requests_before_restart 10000` for memory management

#### Cost Control
- [ ] Set per-squad budgets via virtual keys
- [ ] Set `provider_budget_config` for upstream provider caps
- [ ] Use `cost_discount_config` and `cost_margin_config` for accurate tracking
- [ ] Configure fallback chains to prefer cheaper models
- [ ] Use `budget_fallbacks` (v1.92+) to reroute instead of blocking on budget exceeded
- [ ] Set up Slack alerts for `budget_exceeded`, `provider_fallback`, `rate_limit_hit`
- [ ] Review `/global/spend/report` weekly
- [ ] Use tags for cost center attribution

#### Reliability
- [ ] Deploy 3+ replicas behind load balancer
- [ ] Configure health checks with appropriate thresholds
- [ ] Set up `default_fallbacks` for misconfigured model groups
- [ ] Configure `context_window_fallbacks` for long-context requests
- [ ] Test failover by manually disabling a provider key
- [ ] Keep an emergency static model in fallback chain
- [ ] Set `cooldown_time: 30` (tune for your providers)
- [ ] Use `allowed_fails: 3` before cooldown

#### Observability
- [ ] Enable Prometheus metrics at `/metrics`
- [ ] Set up Grafana dashboards for: provider latency, cost, cache hit ratio, error rate
- [ ] Configure Langfuse or Datadog for LLM-specific tracing
- [ ] Enable `json_logs: true` for structured logging
- [ ] Set up alertmanager rules for: cache miss rate < 30%, provider 5xx > 1%
- [ ] Monitor `litellm_proxy_total_requests` and `litellm_proxy_latency` metrics

#### Hermes Agent Specific
- [ ] Use `custom_providers` block in config.yaml for clean integration
- [ ] Set `api_mode: chat_completions` for Hermes compatibility
- [ ] Create one virtual key per squad (not per agent) to simplify management
- [ ] Set squad-level RPM/TPM limits based on slot count (e.g., 10 RPM per slot)
- [ ] Use `metadata.tags` for cost attribution per squad
- [ ] Monitor per-squad spend via `/global/spend/report?group_by=team`

### 5.3 Monitoring Checklist

| Metric | Source | Alert Threshold |
|--------|--------|-----------------|
| Proxy latency P95 | Prometheus | > 200ms |
| Error rate | Prometheus | > 1% |
| Cache hit ratio | Prometheus | < 30% |
| Daily spend | LiteLLM API | > 2x baseline |
| Budget utilization | Slack alert | > 80% |
| Provider 5xx rate | Prometheus | > 1% |
| Connection pool | Logs | "connection pool exhausted" |
| Memory usage | Kubernetes | > 3.5Gi |
| Redis memory | Redis INFO | > 80% |
| Postgres connections | pg_stat_activity | > 80% of max |

---

## 6. Quick Reference

### Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Main LLM call endpoint |
| `/v1/embeddings` | POST | Embedding generation |
| `/key/generate` | POST | Create virtual key |
| `/key/update` | POST | Update key (budget, models) |
| `/key/info` | GET | Get key info and spend |
| `/global/spend/report` | GET | Spend reports |
| `/global/spend/reset` | POST | Reset all spend (master key only) |
| `/health/liveliness` | GET | Liveness probe |
| `/health/readiness` | GET | Readiness probe |
| `/metrics` | GET | Prometheus metrics |
| `/ui` | GET | Admin dashboard |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `LITELLM_MASTER_KEY` | Admin master key |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_HOST` | Redis hostname |
| `REDIS_PORT` | Redis port |
| `REDIS_PASSWORD` | Redis password |
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint |
| `GEMINI_API_KEY` | Google AI Studio key |
| `SLACK_WEBHOOK_URL` | Slack alerting webhook |
| `MAX_CONNECTIONS` | HTTP connection pool size (default: 10) |

---

## Summary

LiteLLM is the right gateway for Ahmed's 330-agent-slot stack. It provides:

1. **Unified API** — One OpenAI-compatible endpoint for all providers
2. **Cost tracking** — Per-key, per-user, per-team, per-model, per-provider spend visibility
3. **Rate limiting** — Multi-level RPM/TPM controls at key, user, team, and server level
4. **Model routing** — Multiple strategies (latency, cost, usage-based) with fallback chains
5. **Fallback chains** — Automatic failover across providers with cooldown management
6. **Virtual keys** — Per-squad key management with budgets and model allowlists
7. **Observability** — Prometheus metrics, Langfuse/Datadog integration, spend reports

**Key deployment decisions:**
- 3-5 proxy replicas behind a load balancer
- PostgreSQL for persistence, Redis for rate limiting/caching
- One virtual key per squad (12 keys total)
- Pin to LiteLLM v1.84.0 (post supply-chain attack fix)
- Enable Redis transaction buffer for spend tracking
- Set `--max_requests_before_restart 10000` for memory management

# Campaign Optimizer — Configuration Guide

> AI-powered campaign optimization platform that automates budget allocation, A/B testing, and performance optimization across Meta, Google, and LinkedIn ad platforms.

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Options](#configuration-options)
3. [Environment Variables](#environment-variables)
4. [Full Configuration File](#full-configuration-file)
5. [Example .env File](#example-env-file)
6. [Agent Configuration](#agent-configuration)
7. [Integration Settings](#integration-settings)
8. [Security Configuration](#security-configuration)
9. [Monitoring & Observability](#monitoring--observability)
10. [Rate Limiting & Caching](#rate-limiting--caching)

---

## Overview

The **campaign-optimizer** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/campaign-optimizer/
├── config/
│   ├── config.yaml          # Main configuration
│   └── .env.example        # Environment variable template
├── .env                   # Local environment (git-ignored)
└── config.yaml            # Alternative config location
```

---

## Configuration Options

All available configuration options with their default values:

| Option | Default Value |
|--------|---------------|
| `app.name` | `campaign-optimizer` |
| `app.version` | `0.1.0` |
| `app.env` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `app.workers` | `4` |
| `agents.strategy.model` | `gpt-4` |
| `agents.strategy.temperature` | `0.3` |
| `agents.strategy.max_tokens` | `2000` |
| `agents.strategy.timeout_seconds` | `60` |
| `agents.research.model` | `gpt-4` |
| `agents.research.temperature` | `0.5` |
| `agents.research.max_tokens` | `3000` |
| `agents.research.timeout_seconds` | `90` |
| `agents.creative.model` | `gpt-4` |
| `agents.creative.temperature` | `0.7` |
| `agents.creative.max_tokens` | `2000` |
| `agents.creative.timeout_seconds` | `60` |
| `agents.bidding.model` | `gpt-4` |
| `agents.bidding.temperature` | `0.2` |
| `agents.bidding.max_tokens` | `1500` |
| `agents.bidding.timeout_seconds` | `45` |
| `agents.audience.model` | `gpt-4` |
| `agents.audience.temperature` | `0.4` |
| `agents.audience.max_tokens` | `2000` |
| `agents.audience.timeout_seconds` | `60` |
| `agents.critic.model` | `gpt-4` |
| `agents.critic.temperature` | `0.1` |
| `agents.critic.max_tokens` | `2500` |
| `agents.critic.timeout_seconds` | `60` |
| `integrations.meta.api_version` | `v19.0` |
| `integrations.meta.base_url` | `https://graph.facebook.com` |
| `integrations.meta.rate_limit_per_hour` | `200` |
| `integrations.meta.timeout_seconds` | `30` |
| `integrations.meta.retry_attempts` | `3` |
| `integrations.google.api_version` | `v17` |
| `integrations.google.base_url` | `https://googleads.googleapis.com` |
| `integrations.google.rate_limit_per_minute` | `100` |
| `integrations.google.timeout_seconds` | `30` |
| `integrations.google.retry_attempts` | `3` |
| `integrations.linkedin.api_version` | `v2` |
| `integrations.linkedin.base_url` | `https://api.linkedin.com` |
| `integrations.linkedin.rate_limit_per_day` | `500` |
| `integrations.linkedin.timeout_seconds` | `30` |
| `integrations.linkedin.retry_attempts` | `3` |
| `optimization.min_budget_usd` | `100` |
| `optimization.max_budget_usd` | `100000` |
| `optimization.budget_allocation.meta` | `0.4` |
| `optimization.budget_allocation.google` | `0.35` |
| `optimization.budget_allocation.linkedin` | `0.25` |
| `optimization.performance_thresholds.roas_min` | `2.0` |
| `optimization.performance_thresholds.ctr_min` | `0.01` |
| `optimization.performance_thresholds.cpc_max` | `5.0` |
| `optimization.optimization_interval_minutes` | `60` |
| `optimization.ab_test.min_sample_size` | `1000` |
| `optimization.ab_test.confidence_level` | `0.95` |
| `optimization.ab_test.max_variants` | `5` |
| `cache.ttl_seconds` | `300` |
| `cache.max_entries` | `10000` |
| `database.pool_size` | `10` |
| `database.max_overflow` | `20` |
| `database.pool_timeout` | `30` |
| `database.echo` | `False` |
| `security.api_key_header` | `X-API-Key` |
| `security.rate_limit_requests_per_minute` | `60` |
| `security.cors_origins` | `http://localhost:3000, https://app.campaign-optimizer.example.com` |
| `monitoring.metrics_port` | `9090` |
| `monitoring.enable_tracing` | `True` |
| `monitoring.tracing_sample_rate` | `0.1` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Copy this file to .env and fill in your values |
| `LOG_LEVEL` | `DEBUG` | Copy this file to .env and fill in your values |
| `DEBUG` | `true` | Copy this file to .env and fill in your values |
| `API_HOST` | `0.0.0.0` | Copy this file to .env and fill in your values |
| `API_PORT` | `8000` | Copy this file to .env and fill in your values |
| `API_WORKERS` | `4` | Copy this file to .env and fill in your values |
| `DATABASE_URL` | `postgresql://campaign:campaign@localhost:5432/campaign_optimizer` | Copy this file to .env and fill in your values |
| `DB_POOL_SIZE` | `10` | Copy this file to .env and fill in your values |
| `DB_MAX_OVERFLOW` | `20` | Copy this file to .env and fill in your values |
| `REDIS_URL` | `redis://localhost:6379/0` | Copy this file to .env and fill in your values |
| `OPENAI_API_KEY` | `sk-your-key-here` | Copy this file to .env and fill in your values |
| `DEFAULT_MODEL` | `gpt-4o` | Copy this file to .env and fill in your values |
| `FALLBACK_MODEL` | `gpt-4o-mini` | Copy this file to .env and fill in your values |
| `LLM_TEMPERATURE` | `0.7` | Copy this file to .env and fill in your values |
| `LLM_MAX_TOKENS` | `4096` | Copy this file to .env and fill in your values |
| `GRC_CLAW_ENABLED` | `true` | Copy this file to .env and fill in your values |
| `GRC_CLAW_POLICY_ENGINE` | `default` | Copy this file to .env and fill in your values |
| `GRC_CLAW_APPROVAL_THRESHOLD` | `0.8` | Copy this file to .env and fill in your values |
| `GRC_CLAW_AUDIT_LOG` | `true` | Copy this file to .env and fill in your values |
| `GRC_CLAW_MAX_BUDGET_CHANGE_PCT` | `20` | Copy this file to .env and fill in your values |
| `GRC_CLAW_REQUIRE_APPROVAL_ABOVE` | `1000` | Copy this file to .env and fill in your values |
| `OPTIMIZATION_INTERVAL` | `300` | Copy this file to .env and fill in your values |
| `MIN_IMPROVEMENT_THRESHOLD` | `0.05` | Copy this file to .env and fill in your values |
| `MAX_BUDGET_ADJUSTMENT` | `0.15` | Copy this file to .env and fill in your values |
| `LOOKBACK_WINDOW` | `7` | Copy this file to .env and fill in your values |
| `AB_TEST_DURATION` | `3` | Copy this file to .env and fill in your values |
| `CONFIDENCE_LEVEL` | `0.95` | Copy this file to .env and fill in your values |
| `PROMETHEUS_ENABLED` | `true` | Copy this file to .env and fill in your values |
| `PROMETHEUS_PORT` | `9090` | Copy this file to .env and fill in your values |
| `GRAFANA_ENABLED` | `true` | Copy this file to .env and fill in your values |
| `SENTRY_DSN` | `` | Copy this file to .env and fill in your values |
| `GOOGLE_ADS_API_KEY` | `` | Copy this file to .env and fill in your values |
| `META_ADS_API_KEY` | `` | Copy this file to .env and fill in your values |
| `TIKTOK_ADS_API_KEY` | `` | Copy this file to .env and fill in your values |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: campaign-optimizer
  version: 0.1.0
  env: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
  workers: 4
agents:
  strategy:
    model: gpt-4
    temperature: 0.3
    max_tokens: 2000
    timeout_seconds: 60
  research:
    model: gpt-4
    temperature: 0.5
    max_tokens: 3000
    timeout_seconds: 90
  creative:
    model: gpt-4
    temperature: 0.7
    max_tokens: 2000
    timeout_seconds: 60
  bidding:
    model: gpt-4
    temperature: 0.2
    max_tokens: 1500
    timeout_seconds: 45
  audience:
    model: gpt-4
    temperature: 0.4
    max_tokens: 2000
    timeout_seconds: 60
  critic:
    model: gpt-4
    temperature: 0.1
    max_tokens: 2500
    timeout_seconds: 60
integrations:
  meta:
    api_version: v19.0
    base_url: https://graph.facebook.com
    rate_limit_per_hour: 200
    timeout_seconds: 30
    retry_attempts: 3
  google:
    api_version: v17
    base_url: https://googleads.googleapis.com
    rate_limit_per_minute: 100
    timeout_seconds: 30
    retry_attempts: 3
  linkedin:
    api_version: v2
    base_url: https://api.linkedin.com
    rate_limit_per_day: 500
    timeout_seconds: 30
    retry_attempts: 3
optimization:
  min_budget_usd: 100
  max_budget_usd: 100000
  budget_allocation:
    meta: 0.4
    google: 0.35
    linkedin: 0.25
  performance_thresholds:
    roas_min: 2.0
    ctr_min: 0.01
    cpc_max: 5.0
  optimization_interval_minutes: 60
  ab_test:
    min_sample_size: 1000
    confidence_level: 0.95
    max_variants: 5
cache:
  ttl_seconds: 300
  max_entries: 10000
database:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  echo: False
security:
  api_key_header: X-API-Key
  rate_limit_requests_per_minute: 60
  cors_origins:
    - http://localhost:3000
    - https://app.campaign-optimizer.example.com
monitoring:
  metrics_port: 9090
  enable_tracing: True
  tracing_sample_rate: 0.1
```

---

## Example .env File

```bash
# Campaign Optimizer Environment Configuration
# Copy this file to .env and fill in your values

# ─── Application ───────────────────────────────────────────────
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true

# ─── API ──────────────────────────────────────────────────────
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# ─── Database ─────────────────────────────────────────────────
DATABASE_URL=postgresql://campaign:campaign@localhost:5432/campaign_optimizer
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# ─── Redis ────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ─── LLM / OpenAI ─────────────────────────────────────────────
OPENAI_API_KEY=sk-your-key-here
DEFAULT_MODEL=gpt-4o
FALLBACK_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# ─── Governance / GRC_Claw ────────────────────────────────────
GRC_CLAW_ENABLED=true
GRC_CLAW_POLICY_ENGINE=default
GRC_CLAW_APPROVAL_THRESHOLD=0.8
GRC_CLAW_AUDIT_LOG=true
GRC_CLAW_MAX_BUDGET_CHANGE_PCT=20
GRC_CLAW_REQUIRE_APPROVAL_ABOVE=1000

# ─── Optimization ─────────────────────────────────────────────
OPTIMIZATION_INTERVAL=300
MIN_IMPROVEMENT_THRESHOLD=0.05
MAX_BUDGET_ADJUSTMENT=0.15
LOOKBACK_WINDOW=7
AB_TEST_DURATION=3
CONFIDENCE_LEVEL=0.95

# ─── Monitoring ───────────────────────────────────────────────
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
GRAFANA_ENABLED=true
SENTRY_DSN=

# ─── External APIs ────────────────────────────────────────────
GOOGLE_ADS_API_KEY=
META_ADS_API_KEY=
TIKTOK_ADS_API_KEY=

```

---

## Agent Configuration

```yaml
agents:
  audience:
    max_tokens: 2000
    model: gpt-4
    temperature: 0.4
    timeout_seconds: 60
  bidding:
    max_tokens: 1500
    model: gpt-4
    temperature: 0.2
    timeout_seconds: 45
  creative:
    max_tokens: 2000
    model: gpt-4
    temperature: 0.7
    timeout_seconds: 60
  critic:
    max_tokens: 2500
    model: gpt-4
    temperature: 0.1
    timeout_seconds: 60
  research:
    max_tokens: 3000
    model: gpt-4
    temperature: 0.5
    timeout_seconds: 90
  strategy:
    max_tokens: 2000
    model: gpt-4
    temperature: 0.3
    timeout_seconds: 60
```

---

## Integration Settings

```yaml
integrations:
  google:
    api_version: v17
    base_url: https://googleads.googleapis.com
    rate_limit_per_minute: 100
    retry_attempts: 3
    timeout_seconds: 30
  linkedin:
    api_version: v2
    base_url: https://api.linkedin.com
    rate_limit_per_day: 500
    retry_attempts: 3
    timeout_seconds: 30
  meta:
    api_version: v19.0
    base_url: https://graph.facebook.com
    rate_limit_per_hour: 200
    retry_attempts: 3
    timeout_seconds: 30
```

---

## Security Configuration

### security

```yaml
security:
  api_key_header: X-API-Key
  cors_origins:
  - http://localhost:3000
  - https://app.campaign-optimizer.example.com
  rate_limit_requests_per_minute: 60
```

---

## Monitoring & Observability

### monitoring

```yaml
monitoring:
  enable_tracing: true
  metrics_port: 9090
  tracing_sample_rate: 0.1
```

---

## Rate Limiting & Caching

### cache

```yaml
cache:
  max_entries: 10000
  ttl_seconds: 300
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/campaign-optimizer
cp .env.example .env  # or: cp config/.env.example .env
```

### 2. Edit `.env` with your values:

```bash
nano .env  # or your preferred editor
```

### 3. Validate configuration:

```bash
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
```

### 4. Start the service:

```bash
python -m src.main  # or: uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

*Generated for `campaign-optimizer` — GRC_Claw Configuration Guide*

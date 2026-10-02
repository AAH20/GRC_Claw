# Lead Scorer — Configuration Guide

> Intelligent lead scoring platform using firmographic, technographic, engagement, intent, and timing signals to rank and qualify leads.

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

The **lead-scorer** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/lead-scorer/
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
| `app.name` | `lead-scorer` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `info` |
| `scoring.weights.firmographic` | `0.25` |
| `scoring.weights.technographic` | `0.15` |
| `scoring.weights.engagement` | `0.3` |
| `scoring.weights.intent` | `0.2` |
| `scoring.weights.timing` | `0.1` |
| `scoring.thresholds.hot` | `80` |
| `scoring.thresholds.warm` | `50` |
| `scoring.thresholds.cold` | `0` |
| `scoring.decay.half_life_days` | `30` |
| `scoring.decay.engagement_window_days` | `90` |
| `qualification.framework` | `MEDDIC` |
| `qualification.required_fields` | `budget, authority, need, timeline` |
| `qualification.scoring.budget.min` | `10000` |
| `qualification.scoring.budget.optimal` | `50000` |
| `qualification.scoring.timeline.urgent_days` | `14` |
| `qualification.scoring.timeline.standard_days` | `90` |
| `integrations.salesforce.enabled` | `False` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.timeout_seconds` | `30` |
| `integrations.salesforce.retry_attempts` | `3` |
| `integrations.hubspot.enabled` | `False` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.timeout_seconds` | `30` |
| `integrations.hubspot.retry_attempts` | `3` |
| `agents.research.timeout_seconds` | `60` |
| `agents.research.max_retries` | `2` |
| `agents.evidence.timeout_seconds` | `45` |
| `agents.evidence.max_retries` | `2` |
| `agents.scoring.timeout_seconds` | `30` |
| `agents.scoring.max_retries` | `1` |
| `agents.qualification.timeout_seconds` | `30` |
| `agents.qualification.max_retries` | `1` |
| `agents.churn_prediction.timeout_seconds` | `45` |
| `agents.churn_prediction.max_retries` | `2` |
| `agents.next_best_action.timeout_seconds` | `30` |
| `agents.next_best_action.max_retries` | `1` |
| `agents.insight_synthesis.timeout_seconds` | `60` |
| `agents.insight_synthesis.max_retries` | `2` |
| `api.host` | `0.0.0.0` |
| `api.port` | `8000` |
| `api.workers` | `4` |
| `api.cors_origins` | `http://localhost:3000, https://app.example.com` |
| `api.rate_limit.requests_per_minute` | `100` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `OPENAI_API_KEY` | `sk-your-openai-api-key-here` | Copy this file to .env and fill in your values |
| `DATABASE_URL` | `postgresql+asyncpg://leadscorer:leadscorer@localhost:5432/leadscorer` | Copy this file to .env and fill in your values |
| `REDIS_URL` | `redis://localhost:6379/0` | Copy this file to .env and fill in your values |
| `API_HOST` | `0.0.0.0` | Copy this file to .env and fill in your values |
| `API_PORT` | `8000` | Copy this file to .env and fill in your values |
| `API_WORKERS` | `4` | Copy this file to .env and fill in your values |
| `LOG_LEVEL` | `INFO` | Copy this file to .env and fill in your values |
| `ENVIRONMENT` | `development` | Copy this file to .env and fill in your values |
| `SCORING_MODEL` | `gpt-4o` | Copy this file to .env and fill in your values |
| `SCORING_TEMPERATURE` | `0.1` | Copy this file to .env and fill in your values |
| `ENABLE_GOVERNANCE` | `true` | Copy this file to .env and fill in your values |
| `AUDIT_LOG` | `true` | Copy this file to .env and fill in your values |
| `PII_REDACTION` | `true` | Copy this file to .env and fill in your values |
| `PROMETHEUS_ENABLED` | `true` | Copy this file to .env and fill in your values |
| `OTEL_ENABLED` | `true` | Copy this file to .env and fill in your values |
| `OTEL_ENDPOINT` | `http://localhost:4318` | Copy this file to .env and fill in your values |
| `TRACING_SAMPLE_RATE` | `0.1` | Copy this file to .env and fill in your values |
| `JWT_SECRET` | `change-me-in-production` | Copy this file to .env and fill in your values |
| `JWT_ALGORITHM` | `HS256` | Copy this file to .env and fill in your values |
| `JWT_EXPIRATION_HOURS` | `24` | Copy this file to .env and fill in your values |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Copy this file to .env and fill in your values |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: lead-scorer
  version: 0.1.0
  environment: development
  log_level: info
scoring:
  weights:
    firmographic: 0.25
    technographic: 0.15
    engagement: 0.3
    intent: 0.2
    timing: 0.1
  thresholds:
    hot: 80
    warm: 50
    cold: 0
  decay:
    half_life_days: 30
    engagement_window_days: 90
qualification:
  framework: MEDDIC
  required_fields:
    - budget
    - authority
    - need
    - timeline
  scoring:
    budget:
      min: 10000
      optimal: 50000
    timeline:
      urgent_days: 14
      standard_days: 90
integrations:
  salesforce:
    enabled: False
    api_version: v58.0
    timeout_seconds: 30
    retry_attempts: 3
  hubspot:
    enabled: False
    api_version: v3
    timeout_seconds: 30
    retry_attempts: 3
agents:
  research:
    timeout_seconds: 60
    max_retries: 2
  evidence:
    timeout_seconds: 45
    max_retries: 2
  scoring:
    timeout_seconds: 30
    max_retries: 1
  qualification:
    timeout_seconds: 30
    max_retries: 1
  churn_prediction:
    timeout_seconds: 45
    max_retries: 2
  next_best_action:
    timeout_seconds: 30
    max_retries: 1
  insight_synthesis:
    timeout_seconds: 60
    max_retries: 2
api:
  host: 0.0.0.0
  port: 8000
  workers: 4
  cors_origins:
    - http://localhost:3000
    - https://app.example.com
  rate_limit:
    requests_per_minute: 100
```

---

## Example .env File

```bash
# AI-Powered Lead Scoring & Qualification — Environment Variables
# Copy this file to .env and fill in your values

# ─── Required ───────────────────────────────────────────────
OPENAI_API_KEY=sk-your-openai-api-key-here

# ─── Database ───────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://leadscorer:leadscorer@localhost:5432/leadscorer

# ─── Redis ─────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ─── API ───────────────────────────────────────────────────
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
LOG_LEVEL=INFO
ENVIRONMENT=development

# ─── Scoring ───────────────────────────────────────────────
SCORING_MODEL=gpt-4o
SCORING_TEMPERATURE=0.1

# ─── Governance ────────────────────────────────────────────
ENABLE_GOVERNANCE=true
AUDIT_LOG=true
PII_REDACTION=true

# ─── Observability ──────────────────────────────────────────
PROMETHEUS_ENABLED=true
OTEL_ENABLED=true
OTEL_ENDPOINT=http://localhost:4318
TRACING_SAMPLE_RATE=0.1

# ─── Security ──────────────────────────────────────────────
JWT_SECRET=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ─── Docker Compose ─────────────────────────────────────────
GRAFANA_ADMIN_PASSWORD=admin

```

---

## Agent Configuration

```yaml
agents:
  churn_prediction:
    max_retries: 2
    timeout_seconds: 45
  evidence:
    max_retries: 2
    timeout_seconds: 45
  insight_synthesis:
    max_retries: 2
    timeout_seconds: 60
  next_best_action:
    max_retries: 1
    timeout_seconds: 30
  qualification:
    max_retries: 1
    timeout_seconds: 30
  research:
    max_retries: 2
    timeout_seconds: 60
  scoring:
    max_retries: 1
    timeout_seconds: 30
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    api_version: v3
    enabled: false
    retry_attempts: 3
    timeout_seconds: 30
  salesforce:
    api_version: v58.0
    enabled: false
    retry_attempts: 3
    timeout_seconds: 30
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

No explicit monitoring configuration found.

---

## Rate Limiting & Caching

No explicit rate limiting or caching configuration found.

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/lead-scorer
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

*Generated for `lead-scorer` — GRC_Claw Configuration Guide*

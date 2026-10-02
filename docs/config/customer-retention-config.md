# Customer Retention — Configuration Guide

> Customer retention platform with churn prediction, intervention automation, and performance analytics.

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

The **customer-retention** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/customer-retention/
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
| `app.name` | `customer-retention` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.prediction.model` | `gpt-4` |
| `agents.prediction.temperature` | `0.1` |
| `agents.prediction.max_tokens` | `2048` |
| `agents.prediction.cache_ttl` | `3600` |
| `agents.intervention.model` | `gpt-4` |
| `agents.intervention.temperature` | `0.3` |
| `agents.intervention.max_tokens` | `4096` |
| `agents.intervention.max_interventions_per_day` | `100` |
| `agents.optimization.model` | `gpt-4` |
| `agents.optimization.temperature` | `0.2` |
| `agents.optimization.max_tokens` | `2048` |
| `agents.optimization.ab_test_duration_days` | `14` |
| `agents.performance_analytics.model` | `gpt-4` |
| `agents.performance_analytics.temperature` | `0.1` |
| `agents.performance_analytics.max_tokens` | `2048` |
| `agents.performance_analytics.metrics_retention_days` | `365` |
| `integrations.salesforce.api_version` | `v59.0` |
| `integrations.salesforce.timeout` | `30` |
| `integrations.salesforce.max_retries` | `3` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.timeout` | `30` |
| `integrations.hubspot.max_retries` | `3` |
| `integrations.stripe.api_version` | `2024-06-20` |
| `integrations.stripe.timeout` | `30` |
| `integrations.stripe.max_retries` | `3` |
| `crm.default_provider` | `salesforce` |
| `crm.sync_interval_minutes` | `15` |
| `crm.batch_size` | `100` |
| `analytics.default_date_range_days` | `30` |
| `analytics.cohort_granularity` | `weekly` |
| `analytics.retention_windows` | `7, 30, 90, 180, 365` |
| `rate_limiting.requests_per_minute` | `100` |
| `rate_limiting.burst_size` | `20` |
| `caching.backend` | `redis` |
| `caching.ttl_seconds` | `300` |
| `caching.max_entries` | `10000` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `HOST` | `0.0.0.0` | API |
| `PORT` | `8000` | API |
| `OPENAI_API_KEY` | `sk-...` | OpenAI (required for LLM agents) |
| `OPENAI_MODEL` | `gpt-4` | OpenAI (required for LLM agents) |
| `SALESFORCE_CLIENT_ID` | `your-client-id` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `your-client-secret` | Salesforce |
| `SALESFORCE_USERNAME` | `your-username` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-security-token` | Salesforce |
| `SALESFORCE_DOMAIN` | `login` | Salesforce |
| `SALESFORCE_API_VERSION` | `v59.0` | Salesforce |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | HubSpot |
| `HUBSPOT_PORTAL_ID` | `your-portal-id` | HubSpot |
| `STRIPE_SECRET_KEY` | `sk_test_...` | Stripe |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Stripe |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (for caching) |
| `PROMETHEUS_PORT` | `9090` | Monitoring |
| `SENTRY_DSN` | `` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: customer-retention
  version: 0.1.0
  environment: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  prediction:
    model: gpt-4
    temperature: 0.1
    max_tokens: 2048
    cache_ttl: 3600
  intervention:
    model: gpt-4
    temperature: 0.3
    max_tokens: 4096
    max_interventions_per_day: 100
  optimization:
    model: gpt-4
    temperature: 0.2
    max_tokens: 2048
    ab_test_duration_days: 14
  performance_analytics:
    model: gpt-4
    temperature: 0.1
    max_tokens: 2048
    metrics_retention_days: 365
integrations:
  salesforce:
    api_version: v59.0
    timeout: 30
    max_retries: 3
    sandbox: False
  hubspot:
    api_version: v3
    timeout: 30
    max_retries: 3
  stripe:
    api_version: 2024-06-20
    timeout: 30
    max_retries: 3
crm:
  default_provider: salesforce
  sync_interval_minutes: 15
  batch_size: 100
analytics:
  default_date_range_days: 30
  cohort_granularity: weekly
  retention_windows:
    - 7
    - 30
    - 90
    - 180
    - 365
rate_limiting:
  requests_per_minute: 100
  burst_size: 20
caching:
  backend: redis
  ttl_seconds: 300
  max_entries: 10000
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-in-production

# API
HOST=0.0.0.0
PORT=8000

# OpenAI (required for LLM agents)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Salesforce
SALESFORCE_CLIENT_ID=your-client-id
SALESFORCE_CLIENT_SECRET=your-client-secret
SALESFORCE_USERNAME=your-username
SALESFORCE_PASSWORD=your-password
SALESFORCE_SECURITY_TOKEN=your-security-token
SALESFORCE_DOMAIN=login
SALESFORCE_API_VERSION=v59.0

# HubSpot
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_PORTAL_ID=your-portal-id

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# Monitoring
PROMETHEUS_PORT=9090
SENTRY_DSN=

```

---

## Agent Configuration

```yaml
agents:
  intervention:
    max_interventions_per_day: 100
    max_tokens: 4096
    model: gpt-4
    temperature: 0.3
  optimization:
    ab_test_duration_days: 14
    max_tokens: 2048
    model: gpt-4
    temperature: 0.2
  performance_analytics:
    max_tokens: 2048
    metrics_retention_days: 365
    model: gpt-4
    temperature: 0.1
  prediction:
    cache_ttl: 3600
    max_tokens: 2048
    model: gpt-4
    temperature: 0.1
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    api_version: v3
    max_retries: 3
    timeout: 30
  salesforce:
    api_version: v59.0
    max_retries: 3
    sandbox: false
    timeout: 30
  stripe:
    api_version: '2024-06-20'
    max_retries: 3
    timeout: 30
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

No explicit monitoring configuration found.

---

## Rate Limiting & Caching

### rate_limiting

```yaml
rate_limiting:
  burst_size: 20
  requests_per_minute: 100
```

### caching

```yaml
caching:
  backend: redis
  max_entries: 10000
  ttl_seconds: 300
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/customer-retention
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

*Generated for `customer-retention` — GRC_Claw Configuration Guide*

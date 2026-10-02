# Saas Marketing — Configuration Guide

> SaaS marketing platform with PQL scoring, churn prevention, content generation, and product-led growth analytics.

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

The **saas-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/saas-marketing/
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
| `app.name` | `saas-marketing` |
| `app.version` | `0.1.0` |
| `app.env` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.content.model` | `gpt-4` |
| `agents.content.temperature` | `0.7` |
| `agents.content.max_tokens` | `2000` |
| `agents.content.retry_attempts` | `3` |
| `agents.pql_scoring.model` | `gpt-4` |
| `agents.pql_scoring.temperature` | `0.3` |
| `agents.pql_scoring.max_tokens` | `1000` |
| `agents.pql_scoring.scoring_threshold` | `70` |
| `agents.pql_scoring.weights.feature_usage` | `0.35` |
| `agents.pql_scoring.weights.engagement` | `0.25` |
| `agents.pql_scoring.weights.profile_fit` | `0.2` |
| `agents.pql_scoring.weights.intent_signals` | `0.2` |
| `agents.churn_prevention.model` | `gpt-4` |
| `agents.churn_prevention.temperature` | `0.3` |
| `agents.churn_prevention.max_tokens` | `1500` |
| `agents.churn_prevention.risk_thresholds.low` | `0.3` |
| `agents.churn_prevention.risk_thresholds.medium` | `0.6` |
| `agents.churn_prevention.risk_thresholds.high` | `0.8` |
| `agents.analytics.model` | `gpt-4` |
| `agents.analytics.temperature` | `0.2` |
| `agents.analytics.max_tokens` | `1500` |
| `agents.analytics.default_lookback_days` | `30` |
| `agents.reporting.model` | `gpt-4` |
| `agents.reporting.temperature` | `0.3` |
| `agents.reporting.max_tokens` | `3000` |
| `agents.reporting.default_format` | `markdown` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.timeout_seconds` | `30` |
| `integrations.salesforce.retry_attempts` | `3` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.timeout_seconds` | `30` |
| `integrations.hubspot.retry_attempts` | `3` |
| `integrations.stripe.api_version` | `2024-06-20` |
| `integrations.stripe.timeout_seconds` | `30` |
| `integrations.stripe.retry_attempts` | `3` |
| `database.url` | `sqlite:///./saas_marketing.db` |
| `database.echo` | `False` |
| `database.pool_size` | `5` |
| `database.max_overflow` | `10` |
| `cache.backend` | `memory` |
| `cache.ttl_seconds` | `300` |
| `rate_limiting.enabled` | `True` |
| `rate_limiting.requests_per_minute` | `100` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `DATABASE_URL` | `sqlite:///./saas_marketing.db` | Database |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (optional) |
| `SALESFORCE_CLIENT_ID` | `` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `` | Salesforce |
| `SALESFORCE_USERNAME` | `` | Salesforce |
| `SALESFORCE_PASSWORD` | `` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `` | Salesforce |
| `SALESFORCE_DOMAIN` | `login` | Salesforce |
| `HUBSPOT_API_KEY` | `` | HubSpot |
| `HUBSPOT_PORTAL_ID` | `` | HubSpot |
| `STRIPE_SECRET_KEY` | `` | Stripe |
| `STRIPE_WEBHOOK_SECRET` | `` | Stripe |
| `OPENAI_API_KEY` | `` | LangChain / LLM |
| `LANGCHAIN_API_KEY` | `` | LangChain / LLM |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain / LLM |
| `LANGCHAIN_PROJECT` | `saas-marketing` | LangChain / LLM |
| `SENTRY_DSN` | `` | Monitoring |
| `PROMETHEUS_PORT` | `9090` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: saas-marketing
  version: 0.1.0
  env: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  content:
    model: gpt-4
    temperature: 0.7
    max_tokens: 2000
    retry_attempts: 3
  pql_scoring:
    model: gpt-4
    temperature: 0.3
    max_tokens: 1000
    scoring_threshold: 70
    weights:
      feature_usage: 0.35
      engagement: 0.25
      profile_fit: 0.2
      intent_signals: 0.2
  churn_prevention:
    model: gpt-4
    temperature: 0.3
    max_tokens: 1500
    risk_thresholds:
      low: 0.3
      medium: 0.6
      high: 0.8
  analytics:
    model: gpt-4
    temperature: 0.2
    max_tokens: 1500
    default_lookback_days: 30
  reporting:
    model: gpt-4
    temperature: 0.3
    max_tokens: 3000
    default_format: markdown
integrations:
  salesforce:
    api_version: v58.0
    timeout_seconds: 30
    retry_attempts: 3
  hubspot:
    api_version: v3
    timeout_seconds: 30
    retry_attempts: 3
  stripe:
    api_version: 2024-06-20
    timeout_seconds: 30
    retry_attempts: 3
database:
  url: sqlite:///./saas_marketing.db
  echo: False
  pool_size: 5
  max_overflow: 10
cache:
  backend: memory
  ttl_seconds: 300
rate_limiting:
  enabled: True
  requests_per_minute: 100
```

---

## Example .env File

```bash
# Application
APP_ENV=development
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-in-production

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./saas_marketing.db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Salesforce
SALESFORCE_CLIENT_ID=
SALESFORCE_CLIENT_SECRET=
SALESFORCE_USERNAME=
SALESFORCE_PASSWORD=
SALESFORCE_SECURITY_TOKEN=
SALESFORCE_DOMAIN=login

# HubSpot
HUBSPOT_API_KEY=
HUBSPOT_PORTAL_ID=

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# LangChain / LLM
OPENAI_API_KEY=
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=saas-marketing

# Monitoring
SENTRY_DSN=
PROMETHEUS_PORT=9090

```

---

## Agent Configuration

```yaml
agents:
  analytics:
    default_lookback_days: 30
    max_tokens: 1500
    model: gpt-4
    temperature: 0.2
  churn_prevention:
    max_tokens: 1500
    model: gpt-4
    risk_thresholds:
      high: 0.8
      low: 0.3
      medium: 0.6
    temperature: 0.3
  content:
    max_tokens: 2000
    model: gpt-4
    retry_attempts: 3
    temperature: 0.7
  pql_scoring:
    max_tokens: 1000
    model: gpt-4
    scoring_threshold: 70
    temperature: 0.3
    weights:
      engagement: 0.25
      feature_usage: 0.35
      intent_signals: 0.2
      profile_fit: 0.2
  reporting:
    default_format: markdown
    max_tokens: 3000
    model: gpt-4
    temperature: 0.3
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    api_version: v3
    retry_attempts: 3
    timeout_seconds: 30
  salesforce:
    api_version: v58.0
    retry_attempts: 3
    timeout_seconds: 30
  stripe:
    api_version: '2024-06-20'
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

### cache

```yaml
cache:
  backend: memory
  ttl_seconds: 300
```

### rate_limiting

```yaml
rate_limiting:
  enabled: true
  requests_per_minute: 100
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/saas-marketing
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

*Generated for `saas-marketing` — GRC_Claw Configuration Guide*

# Affiliate Marketing — Configuration Guide

> Affiliate marketing platform for recruitment, tracking, optimization, payout management, and analytics.

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

The **affiliate-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/affiliate-marketing/
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
| `app.name` | `affiliate-marketing` |
| `app.version` | `0.1.0` |
| `app.debug` | `False` |
| `app.log_level` | `INFO` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `database.url` | `postgresql://postgres:postgres@localhost:5432/affiliate_marketing` |
| `database.pool_size` | `10` |
| `database.max_overflow` | `20` |
| `database.echo` | `False` |
| `redis.url` | `redis://localhost:6379/0` |
| `redis.max_connections` | `50` |
| `agents.recruitment.model` | `gpt-4` |
| `agents.recruitment.temperature` | `0.7` |
| `agents.recruitment.max_tokens` | `2048` |
| `agents.tracking.model` | `gpt-4` |
| `agents.tracking.temperature` | `0.3` |
| `agents.tracking.max_tokens` | `1024` |
| `agents.optimization.model` | `gpt-4` |
| `agents.optimization.temperature` | `0.5` |
| `agents.optimization.max_tokens` | `2048` |
| `agents.payout.model` | `gpt-4` |
| `agents.payout.temperature` | `0.1` |
| `agents.payout.max_tokens` | `1024` |
| `agents.analytics.model` | `gpt-4` |
| `agents.analytics.temperature` | `0.3` |
| `agents.analytics.max_tokens` | `2048` |
| `integrations.rakuten.enabled` | `True` |
| `integrations.rakuten.api_endpoint` | `https://api.rakutenmarketing.com` |
| `integrations.rakuten.timeout` | `30` |
| `integrations.impact.enabled` | `True` |
| `integrations.impact.api_endpoint` | `https://api.impact.com` |
| `integrations.impact.timeout` | `30` |
| `integrations.shareasale.enabled` | `True` |
| `integrations.shareasale.api_endpoint` | `https://api.shareasale.com` |
| `integrations.shareasale.timeout` | `30` |
| `monitoring.prometheus_enabled` | `True` |
| `monitoring.sentry_enabled` | `False` |
| `monitoring.sentry_dsn` | `` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_NAME` | `affiliate-marketing` | Application |
| `APP_VERSION` | `0.1.0` | Application |
| `DEBUG` | `false` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `WORKERS` | `4` | Server |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/affiliate_marketing` | Database |
| `DB_POOL_SIZE` | `10` | Database |
| `DB_MAX_OVERFLOW` | `20` | Database |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `REDIS_MAX_CONNECTIONS` | `50` | Redis |
| `OPENAI_API_KEY` | `` | LangChain / LLM |
| `LANGCHAIN_API_KEY` | `` | LangChain / LLM |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain / LLM |
| `LANGCHAIN_PROJECT` | `affiliate-marketing` | LangChain / LLM |
| `RECRUITMENT_MODEL` | `gpt-4` | Agent Models |
| `TRACKING_MODEL` | `gpt-4` | Agent Models |
| `OPTIMIZATION_MODEL` | `gpt-4` | Agent Models |
| `PAYOUT_MODEL` | `gpt-4` | Agent Models |
| `ANALYTICS_MODEL` | `gpt-4` | Agent Models |
| `RAKUTEN_API_KEY` | `` | Integrations |
| `RAKUTEN_API_SECRET` | `` | Integrations |
| `RAKUTEN_API_ENDPOINT` | `https://api.rakutenmarketing.com` | Integrations |
| `IMPACT_ACCOUNT_SID` | `` | Integrations |
| `IMPACT_AUTH_TOKEN` | `` | Integrations |
| `IMPACT_API_ENDPOINT` | `https://api.impact.com` | Integrations |
| `SHAREASALE_API_TOKEN` | `` | Integrations |
| `SHAREASALE_API_SECRET` | `` | Integrations |
| `SHAREASALE_AFFILIATE_ID` | `` | Integrations |
| `SHAREASALE_API_ENDPOINT` | `https://api.shareasale.com` | Integrations |
| `PROMETHEUS_ENABLED` | `true` | Monitoring |
| `SENTRY_ENABLED` | `false` | Monitoring |
| `SENTRY_DSN` | `` | Monitoring |
| `SECRET_KEY` | `change-me-in-production` | Security |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Security |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: affiliate-marketing
  version: 0.1.0
  debug: False
  log_level: INFO
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
database:
  url: postgresql://postgres:postgres@localhost:5432/affiliate_marketing
  pool_size: 10
  max_overflow: 20
  echo: False
redis:
  url: redis://localhost:6379/0
  max_connections: 50
agents:
  recruitment:
    model: gpt-4
    temperature: 0.7
    max_tokens: 2048
  tracking:
    model: gpt-4
    temperature: 0.3
    max_tokens: 1024
  optimization:
    model: gpt-4
    temperature: 0.5
    max_tokens: 2048
  payout:
    model: gpt-4
    temperature: 0.1
    max_tokens: 1024
  analytics:
    model: gpt-4
    temperature: 0.3
    max_tokens: 2048
integrations:
  rakuten:
    enabled: True
    api_endpoint: https://api.rakutenmarketing.com
    timeout: 30
  impact:
    enabled: True
    api_endpoint: https://api.impact.com
    timeout: 30
  shareasale:
    enabled: True
    api_endpoint: https://api.shareasale.com
    timeout: 30
monitoring:
  prometheus_enabled: True
  sentry_enabled: False
  sentry_dsn: 
```

---

## Example .env File

```bash
# Application
APP_NAME=affiliate-marketing
APP_VERSION=0.1.0
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/affiliate_marketing
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# LangChain / LLM
OPENAI_API_KEY=
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=affiliate-marketing

# Agent Models
RECRUITMENT_MODEL=gpt-4
TRACKING_MODEL=gpt-4
OPTIMIZATION_MODEL=gpt-4
PAYOUT_MODEL=gpt-4
ANALYTICS_MODEL=gpt-4

# Integrations
RAKUTEN_API_KEY=
RAKUTEN_API_SECRET=
RAKUTEN_API_ENDPOINT=https://api.rakutenmarketing.com

IMPACT_ACCOUNT_SID=
IMPACT_AUTH_TOKEN=
IMPACT_API_ENDPOINT=https://api.impact.com

SHAREASALE_API_TOKEN=
SHAREASALE_API_SECRET=
SHAREASALE_AFFILIATE_ID=
SHAREASALE_API_ENDPOINT=https://api.shareasale.com

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_ENABLED=false
SENTRY_DSN=

# Security
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

```

---

## Agent Configuration

```yaml
agents:
  analytics:
    max_tokens: 2048
    model: gpt-4
    temperature: 0.3
  optimization:
    max_tokens: 2048
    model: gpt-4
    temperature: 0.5
  payout:
    max_tokens: 1024
    model: gpt-4
    temperature: 0.1
  recruitment:
    max_tokens: 2048
    model: gpt-4
    temperature: 0.7
  tracking:
    max_tokens: 1024
    model: gpt-4
    temperature: 0.3
```

---

## Integration Settings

```yaml
integrations:
  impact:
    api_endpoint: https://api.impact.com
    enabled: true
    timeout: 30
  rakuten:
    api_endpoint: https://api.rakutenmarketing.com
    enabled: true
    timeout: 30
  shareasale:
    api_endpoint: https://api.shareasale.com
    enabled: true
    timeout: 30
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

### monitoring

```yaml
monitoring:
  prometheus_enabled: true
  sentry_dsn: ''
  sentry_enabled: false
```

---

## Rate Limiting & Caching

### redis

```yaml
redis:
  max_connections: 50
  url: redis://localhost:6379/0
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/affiliate-marketing
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

*Generated for `affiliate-marketing` — GRC_Claw Configuration Guide*

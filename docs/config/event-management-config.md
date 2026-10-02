# Event Management — Configuration Guide

> Event management platform for planning, promotion, execution, follow-up, and performance analytics.

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

The **event-management** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/event-management/
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
| `app.name` | `Event Management` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `debug` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.planning.model` | `gpt-4` |
| `agents.planning.max_tokens` | `4096` |
| `agents.planning.temperature` | `0.7` |
| `agents.planning.timeout_seconds` | `120` |
| `agents.promotion.model` | `gpt-4` |
| `agents.promotion.max_tokens` | `4096` |
| `agents.promotion.temperature` | `0.8` |
| `agents.promotion.timeout_seconds` | `120` |
| `agents.execution.model` | `gpt-4` |
| `agents.execution.max_tokens` | `4096` |
| `agents.execution.temperature` | `0.5` |
| `agents.execution.timeout_seconds` | `120` |
| `agents.followup.model` | `gpt-4` |
| `agents.followup.max_tokens` | `4096` |
| `agents.followup.temperature` | `0.6` |
| `agents.followup.timeout_seconds` | `120` |
| `agents.performance_analytics.model` | `gpt-4` |
| `agents.performance_analytics.max_tokens` | `4096` |
| `agents.performance_analytics.temperature` | `0.3` |
| `agents.performance_analytics.timeout_seconds` | `120` |
| `integrations.eventbrite.base_url` | `https://www.eventbriteapi.com/v3` |
| `integrations.eventbrite.timeout_seconds` | `30` |
| `integrations.eventbrite.retry_attempts` | `3` |
| `integrations.meetup.base_url` | `https://api.meetup.com` |
| `integrations.meetup.timeout_seconds` | `30` |
| `integrations.meetup.retry_attempts` | `3` |
| `integrations.luma.base_url` | `https://api.lu.ma` |
| `integrations.luma.timeout_seconds` | `30` |
| `integrations.luma.retry_attempts` | `3` |
| `database.url` | `sqlite:///./events.db` |
| `database.echo` | `False` |
| `database.pool_size` | `5` |
| `database.max_overflow` | `10` |
| `cache.backend` | `redis` |
| `cache.url` | `redis://localhost:6379/0` |
| `cache.ttl_seconds` | `3600` |
| `rate_limiting.enabled` | `True` |
| `rate_limiting.requests_per_minute` | `60` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `debug` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `DEBUG` | `true` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `DATABASE_URL` | `sqlite:///./events.db` | Database |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LLM Configuration |
| `OPENAI_MODEL` | `gpt-4` | LLM Configuration |
| `OPENAI_MAX_TOKENS` | `4096` | LLM Configuration |
| `OPENAI_TEMPERATURE` | `0.7` | LLM Configuration |
| `EVENTBRITE_API_KEY` | `your-eventbrite-api-key` | Eventbrite Integration |
| `EVENTBRITE_OAUTH_TOKEN` | `your-eventbrite-oauth-token` | Eventbrite Integration |
| `MEETUP_API_KEY` | `your-meetup-api-key` | Meetup Integration |
| `MEETUP_CLIENT_ID` | `your-meetup-client-id` | Meetup Integration |
| `MEETUP_CLIENT_SECRET` | `your-meetup-client-secret` | Meetup Integration |
| `LUMA_API_KEY` | `your-luma-api-key` | Luma Integration |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain / LangGraph |
| `LANGCHAIN_API_KEY` | `your-langsmith-api-key` | LangChain / LangGraph |
| `LANGCHAIN_PROJECT` | `event-management` | LangChain / LangGraph |
| `GRC_MARKETING_API_KEY` | `your-grc-marketing-api-key` | grc-marketing-core |
| `GRC_MARKETING_BASE_URL` | `https://api.grc-marketing.example.com` | grc-marketing-core |
| `RATE_LIMIT_ENABLED` | `true` | Rate Limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Rate Limiting |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:8080"]` | CORS |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: Event Management
  version: 0.1.0
  environment: development
  log_level: debug
  host: 0.0.0.0
  port: 8000
agents:
  planning:
    model: gpt-4
    max_tokens: 4096
    temperature: 0.7
    timeout_seconds: 120
  promotion:
    model: gpt-4
    max_tokens: 4096
    temperature: 0.8
    timeout_seconds: 120
  execution:
    model: gpt-4
    max_tokens: 4096
    temperature: 0.5
    timeout_seconds: 120
  followup:
    model: gpt-4
    max_tokens: 4096
    temperature: 0.6
    timeout_seconds: 120
  performance_analytics:
    model: gpt-4
    max_tokens: 4096
    temperature: 0.3
    timeout_seconds: 120
integrations:
  eventbrite:
    base_url: https://www.eventbriteapi.com/v3
    timeout_seconds: 30
    retry_attempts: 3
  meetup:
    base_url: https://api.meetup.com
    timeout_seconds: 30
    retry_attempts: 3
  luma:
    base_url: https://api.lu.ma
    timeout_seconds: 30
    retry_attempts: 3
database:
  url: sqlite:///./events.db
  echo: False
  pool_size: 5
  max_overflow: 10
cache:
  backend: redis
  url: redis://localhost:6379/0
  ttl_seconds: 3600
rate_limiting:
  enabled: True
  requests_per_minute: 60
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=debug
SECRET_KEY=change-me-in-production
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./events.db

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM Configuration
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7

# Eventbrite Integration
EVENTBRITE_API_KEY=your-eventbrite-api-key
EVENTBRITE_OAUTH_TOKEN=your-eventbrite-oauth-token

# Meetup Integration
MEETUP_API_KEY=your-meetup-api-key
MEETUP_CLIENT_ID=your-meetup-client-id
MEETUP_CLIENT_SECRET=your-meetup-client-secret

# Luma Integration
LUMA_API_KEY=your-luma-api-key

# LangChain / LangGraph
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=event-management

# grc-marketing-core
GRC_MARKETING_API_KEY=your-grc-marketing-api-key
GRC_MARKETING_BASE_URL=https://api.grc-marketing.example.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

```

---

## Agent Configuration

```yaml
agents:
  execution:
    max_tokens: 4096
    model: gpt-4
    temperature: 0.5
    timeout_seconds: 120
  followup:
    max_tokens: 4096
    model: gpt-4
    temperature: 0.6
    timeout_seconds: 120
  performance_analytics:
    max_tokens: 4096
    model: gpt-4
    temperature: 0.3
    timeout_seconds: 120
  planning:
    max_tokens: 4096
    model: gpt-4
    temperature: 0.7
    timeout_seconds: 120
  promotion:
    max_tokens: 4096
    model: gpt-4
    temperature: 0.8
    timeout_seconds: 120
```

---

## Integration Settings

```yaml
integrations:
  eventbrite:
    base_url: https://www.eventbriteapi.com/v3
    retry_attempts: 3
    timeout_seconds: 30
  luma:
    base_url: https://api.lu.ma
    retry_attempts: 3
    timeout_seconds: 30
  meetup:
    base_url: https://api.meetup.com
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
  backend: redis
  ttl_seconds: 3600
  url: redis://localhost:6379/0
```

### rate_limiting

```yaml
rate_limiting:
  enabled: true
  requests_per_minute: 60
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/event-management
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

*Generated for `event-management` — GRC_Claw Configuration Guide*

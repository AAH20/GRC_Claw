# Email Marketing — Configuration Guide

> AI-driven email marketing platform with segmentation, personalization, send-time optimization, and performance analytics.

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

The **email-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/email-marketing/
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
| `app.name` | `email-marketing` |
| `app.version` | `0.1.0` |
| `app.env` | `dev` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.segmentation.model` | `gpt-4` |
| `agents.segmentation.temperature` | `0.3` |
| `agents.segmentation.max_tokens` | `2048` |
| `agents.segmentation.cache_ttl` | `3600` |
| `agents.content_personalization.model` | `gpt-4` |
| `agents.content_personalization.temperature` | `0.7` |
| `agents.content_personalization.max_tokens` | `4096` |
| `agents.content_personalization.cache_ttl` | `1800` |
| `agents.send_time_optimization.model` | `gpt-4` |
| `agents.send_time_optimization.temperature` | `0.2` |
| `agents.send_time_optimization.max_tokens` | `1024` |
| `agents.send_time_optimization.cache_ttl` | `7200` |
| `agents.subject_line_optimization.model` | `gpt-4` |
| `agents.subject_line_optimization.temperature` | `0.8` |
| `agents.subject_line_optimization.max_tokens` | `512` |
| `agents.subject_line_optimization.cache_ttl` | `900` |
| `agents.list_hygiene.model` | `gpt-4` |
| `agents.list_hygiene.temperature` | `0.1` |
| `agents.list_hygiene.max_tokens` | `2048` |
| `agents.list_hygiene.cache_ttl` | `86400` |
| `agents.performance_analytics.model` | `gpt-4` |
| `agents.performance_analytics.temperature` | `0.3` |
| `agents.performance_analytics.max_tokens` | `4096` |
| `agents.performance_analytics.cache_ttl` | `3600` |
| `integrations.sendgrid.timeout` | `30` |
| `integrations.sendgrid.max_retries` | `3` |
| `integrations.sendgrid.retry_delay` | `1.0` |
| `integrations.mailchimp.timeout` | `30` |
| `integrations.mailchimp.max_retries` | `3` |
| `integrations.mailchimp.retry_delay` | `1.0` |
| `integrations.klaviyo.timeout` | `30` |
| `integrations.klaviyo.max_retries` | `3` |
| `integrations.klaviyo.retry_delay` | `1.0` |
| `rate_limiting.enabled` | `True` |
| `rate_limiting.requests_per_minute` | `60` |
| `rate_limiting.burst_size` | `10` |
| `caching.backend` | `redis` |
| `caching.ttl` | `3600` |
| `caching.max_size` | `10000` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `dev` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | OpenAI (required for LLM agents) |
| `OPENAI_MODEL` | `gpt-4` | OpenAI (required for LLM agents) |
| `SENDGRID_API_KEY` | `SG.your-sendgrid-api-key` | SendGrid |
| `SENDGRID_FROM_EMAIL` | `noreply@yourdomain.com` | SendGrid |
| `SENDGRID_FROM_NAME` | `"Your Company"` | SendGrid |
| `MAILCHIMP_API_KEY` | `your-mailchimp-api-key` | Mailchimp |
| `MAILCHIMP_SERVER_PREFIX` | `us1` | Mailchimp |
| `MAILCHIMP_LIST_ID` | `your-audience-list-id` | Mailchimp |
| `KLAVIYO_API_KEY` | `your-klaviyo-api-key` | Klaviyo |
| `KLAVIYO_LIST_ID` | `your-klaviyo-list-id` | Klaviyo |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (for caching) |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain / LangSmith (optional, for tracing) |
| `LANGCHAIN_API_KEY` | `your-langsmith-api-key` | LangChain / LangSmith (optional, for tracing) |
| `LANGCHAIN_PROJECT` | `email-marketing` | LangChain / LangSmith (optional, for tracing) |
| `RATE_LIMIT_ENABLED` | `true` | Rate Limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Rate Limiting |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: email-marketing
  version: 0.1.0
  env: dev
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  segmentation:
    model: gpt-4
    temperature: 0.3
    max_tokens: 2048
    cache_ttl: 3600
  content_personalization:
    model: gpt-4
    temperature: 0.7
    max_tokens: 4096
    cache_ttl: 1800
  send_time_optimization:
    model: gpt-4
    temperature: 0.2
    max_tokens: 1024
    cache_ttl: 7200
  subject_line_optimization:
    model: gpt-4
    temperature: 0.8
    max_tokens: 512
    cache_ttl: 900
  list_hygiene:
    model: gpt-4
    temperature: 0.1
    max_tokens: 2048
    cache_ttl: 86400
  performance_analytics:
    model: gpt-4
    temperature: 0.3
    max_tokens: 4096
    cache_ttl: 3600
integrations:
  sendgrid:
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
  mailchimp:
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
  klaviyo:
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
rate_limiting:
  enabled: True
  requests_per_minute: 60
  burst_size: 10
caching:
  backend: redis
  ttl: 3600
  max_size: 10000
```

---

## Example .env File

```bash
# Application
APP_ENV=dev
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-in-production

# Server
HOST=0.0.0.0
PORT=8000

# OpenAI (required for LLM agents)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4

# SendGrid
SENDGRID_API_KEY=SG.your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME="Your Company"

# Mailchimp
MAILCHIMP_API_KEY=your-mailchimp-api-key
MAILCHIMP_SERVER_PREFIX=us1
MAILCHIMP_LIST_ID=your-audience-list-id

# Klaviyo
KLAVIYO_API_KEY=your-klaviyo-api-key
KLAVIYO_LIST_ID=your-klaviyo-list-id

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# LangChain / LangSmith (optional, for tracing)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=email-marketing

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

```

---

## Agent Configuration

```yaml
agents:
  content_personalization:
    cache_ttl: 1800
    max_tokens: 4096
    model: gpt-4
    temperature: 0.7
  list_hygiene:
    cache_ttl: 86400
    max_tokens: 2048
    model: gpt-4
    temperature: 0.1
  performance_analytics:
    cache_ttl: 3600
    max_tokens: 4096
    model: gpt-4
    temperature: 0.3
  segmentation:
    cache_ttl: 3600
    max_tokens: 2048
    model: gpt-4
    temperature: 0.3
  send_time_optimization:
    cache_ttl: 7200
    max_tokens: 1024
    model: gpt-4
    temperature: 0.2
  subject_line_optimization:
    cache_ttl: 900
    max_tokens: 512
    model: gpt-4
    temperature: 0.8
```

---

## Integration Settings

```yaml
integrations:
  klaviyo:
    max_retries: 3
    retry_delay: 1.0
    timeout: 30
  mailchimp:
    max_retries: 3
    retry_delay: 1.0
    timeout: 30
  sendgrid:
    max_retries: 3
    retry_delay: 1.0
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
  burst_size: 10
  enabled: true
  requests_per_minute: 60
```

### caching

```yaml
caching:
  backend: redis
  max_size: 10000
  ttl: 3600
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/email-marketing
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

*Generated for `email-marketing` — GRC_Claw Configuration Guide*

# Feedback Management — Configuration Guide

> Customer feedback management platform with collection, sentiment analysis, response generation, and action tracking.

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

The **feedback-management** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/feedback-management/
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
| `app.name` | `feedback-management` |
| `app.version` | `0.1.0` |
| `app.env` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.collection.enabled` | `True` |
| `agents.collection.platforms` | `surveymonkey, typeform, google_forms` |
| `agents.collection.poll_interval_minutes` | `15` |
| `agents.collection.max_feedback_per_batch` | `100` |
| `agents.analysis.enabled` | `True` |
| `agents.analysis.sentiment_model` | `distilbert-base-uncased-finetuned-sst-2-english` |
| `agents.analysis.topic_model` | `all-MiniLM-L6-v2` |
| `agents.analysis.batch_size` | `32` |
| `agents.analysis.confidence_threshold` | `0.7` |
| `agents.response.enabled` | `True` |
| `agents.response.model` | `gpt-4` |
| `agents.response.max_tokens` | `500` |
| `agents.response.temperature` | `0.7` |
| `agents.response.tone` | `professional` |
| `agents.response.language` | `en` |
| `agents.action.enabled` | `True` |
| `agents.action.auto_escalate_threshold` | `-0.5` |
| `agents.action.auto_respond_threshold` | `0.8` |
| `agents.action.webhook_url` | `None` |
| `agents.performance_analytics.enabled` | `True` |
| `agents.performance_analytics.metrics` | `response_time, satisfaction_score, resolution_rate` |
| `agents.performance_analytics.report_interval_hours` | `24` |
| `integrations.surveymonkey.enabled` | `True` |
| `integrations.surveymonkey.api_version` | `v3` |
| `integrations.surveymonkey.base_url` | `https://api.surveymonkey.com` |
| `integrations.surveymonkey.rate_limit_per_minute` | `120` |
| `integrations.typeform.enabled` | `True` |
| `integrations.typeform.base_url` | `https://api.typeform.com` |
| `integrations.typeform.rate_limit_per_minute` | `60` |
| `integrations.google_forms.enabled` | `True` |
| `integrations.google_forms.base_url` | `https://forms.googleapis.com/v1` |
| `integrations.google_forms.rate_limit_per_minute` | `100` |
| `database.url` | `sqlite:///./feedback.db` |
| `database.echo` | `False` |
| `database.pool_size` | `5` |
| `database.max_overflow` | `10` |
| `cache.backend` | `redis` |
| `cache.url` | `redis://localhost:6379/0` |
| `cache.ttl_seconds` | `3600` |
| `logging.format` | `json` |
| `logging.timestamp_format` | `ISO8601` |
| `logging.include_trace_id` | `True` |

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
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LLM / AI |
| `OPENAI_MODEL` | `gpt-4` | LLM / AI |
| `OPENAI_MAX_TOKENS` | `500` | LLM / AI |
| `OPENAI_TEMPERATURE` | `0.7` | LLM / AI |
| `LANGCHAIN_API_KEY` | `lsv2-your-langchain-api-key` | LangChain |
| `LANGCHAIN_TRACING_V2` | `true` | LangChain |
| `LANGCHAIN_PROJECT` | `feedback-management` | LangChain |
| `SURVEYMONKEY_API_KEY` | `your-surveymonkey-api-key` | SurveyMonkey |
| `SURVEYMONKEY_CLIENT_ID` | `your-client-id` | SurveyMonkey |
| `SURVEYMONKEY_CLIENT_SECRET` | `your-client-secret` | SurveyMonkey |
| `TYPEFORM_API_KEY` | `your-typeform-api-key` | Typeform |
| `TYPEFORM_WORKSPACE_ID` | `your-workspace-id` | Typeform |
| `GOOGLE_FORMS_CREDENTIALS_PATH` | `./config/google-credentials.json` | Google Forms |
| `GOOGLE_FORMS_TOKEN_PATH` | `./config/google-token.json` | Google Forms |
| `DATABASE_URL` | `sqlite:///./feedback.db` | Database |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis / Cache |
| `CACHE_TTL_SECONDS` | `3600` | Redis / Cache |
| `SENTRY_DSN` | `` | Monitoring |
| `PROMETHEUS_PORT` | `9090` | Monitoring |
| `WEBHOOK_SECRET` | `your-webhook-secret` | Webhooks |
| `SLACK_WEBHOOK_URL` | `` | Webhooks |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: feedback-management
  version: 0.1.0
  env: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  collection:
    enabled: True
    platforms:
      - surveymonkey
      - typeform
      - google_forms
    poll_interval_minutes: 15
    max_feedback_per_batch: 100
  analysis:
    enabled: True
    sentiment_model: distilbert-base-uncased-finetuned-sst-2-english
    topic_model: all-MiniLM-L6-v2
    batch_size: 32
    confidence_threshold: 0.7
  response:
    enabled: True
    model: gpt-4
    max_tokens: 500
    temperature: 0.7
    tone: professional
    language: en
  action:
    enabled: True
    auto_escalate_threshold: -0.5
    auto_respond_threshold: 0.8
    webhook_url: None
  performance_analytics:
    enabled: True
    metrics:
      - response_time
      - satisfaction_score
      - resolution_rate
    report_interval_hours: 24
integrations:
  surveymonkey:
    enabled: True
    api_version: v3
    base_url: https://api.surveymonkey.com
    rate_limit_per_minute: 120
  typeform:
    enabled: True
    base_url: https://api.typeform.com
    rate_limit_per_minute: 60
  google_forms:
    enabled: True
    base_url: https://forms.googleapis.com/v1
    rate_limit_per_minute: 100
database:
  url: sqlite:///./feedback.db
  echo: False
  pool_size: 5
  max_overflow: 10
cache:
  backend: redis
  url: redis://localhost:6379/0
  ttl_seconds: 3600
logging:
  format: json
  timestamp_format: ISO8601
  include_trace_id: True
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

# LLM / AI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.7

# LangChain
LANGCHAIN_API_KEY=lsv2-your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=feedback-management

# SurveyMonkey
SURVEYMONKEY_API_KEY=your-surveymonkey-api-key
SURVEYMONKEY_CLIENT_ID=your-client-id
SURVEYMONKEY_CLIENT_SECRET=your-client-secret

# Typeform
TYPEFORM_API_KEY=your-typeform-api-key
TYPEFORM_WORKSPACE_ID=your-workspace-id

# Google Forms
GOOGLE_FORMS_CREDENTIALS_PATH=./config/google-credentials.json
GOOGLE_FORMS_TOKEN_PATH=./config/google-token.json

# Database
DATABASE_URL=sqlite:///./feedback.db
# DATABASE_URL=postgresql://feedback:feedback_pass@localhost:5432/feedback_db

# Redis / Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=3600

# Monitoring
SENTRY_DSN=
PROMETHEUS_PORT=9090

# Webhooks
WEBHOOK_SECRET=your-webhook-secret
SLACK_WEBHOOK_URL=

```

---

## Agent Configuration

```yaml
agents:
  action:
    auto_escalate_threshold: -0.5
    auto_respond_threshold: 0.8
    enabled: true
    webhook_url: null
  analysis:
    batch_size: 32
    confidence_threshold: 0.7
    enabled: true
    sentiment_model: distilbert-base-uncased-finetuned-sst-2-english
    topic_model: all-MiniLM-L6-v2
  collection:
    enabled: true
    max_feedback_per_batch: 100
    platforms:
    - surveymonkey
    - typeform
    - google_forms
    poll_interval_minutes: 15
  performance_analytics:
    enabled: true
    metrics:
    - response_time
    - satisfaction_score
    - resolution_rate
    report_interval_hours: 24
  response:
    enabled: true
    language: en
    max_tokens: 500
    model: gpt-4
    temperature: 0.7
    tone: professional
```

---

## Integration Settings

```yaml
integrations:
  google_forms:
    base_url: https://forms.googleapis.com/v1
    enabled: true
    rate_limit_per_minute: 100
  surveymonkey:
    api_version: v3
    base_url: https://api.surveymonkey.com
    enabled: true
    rate_limit_per_minute: 120
  typeform:
    base_url: https://api.typeform.com
    enabled: true
    rate_limit_per_minute: 60
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

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/feedback-management
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

*Generated for `feedback-management` — GRC_Claw Configuration Guide*

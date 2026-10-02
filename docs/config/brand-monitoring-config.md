# Brand Monitoring — Configuration Guide

> Brand monitoring platform for social listening, sentiment analysis, response management, and reporting.

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

The **brand-monitoring** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/brand-monitoring/
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
| `app.name` | `brand-monitoring` |
| `app.version` | `0.1.0` |
| `app.env` | `dev` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.listening.enabled` | `True` |
| `agents.listening.poll_interval_seconds` | `60` |
| `agents.listening.max_mentions_per_poll` | `100` |
| `agents.listening.platforms` | `twitter, reddit, newsapi` |
| `agents.analysis.enabled` | `True` |
| `agents.analysis.sentiment_model` | `openai` |
| `agents.analysis.batch_size` | `50` |
| `agents.analysis.topics` | `product, service, pricing, support, competition` |
| `agents.response.enabled` | `True` |
| `agents.response.auto_respond` | `False` |
| `agents.response.response_templates_dir` | `config/templates` |
| `agents.response.max_response_length` | `280` |
| `agents.response.approval_required` | `True` |
| `agents.reporting.enabled` | `True` |
| `agents.reporting.schedule` | `0 9 * * 1` |
| `agents.reporting.formats` | `json, pdf` |
| `agents.reporting.retention_days` | `90` |
| `agents.performance_analytics.enabled` | `True` |
| `agents.performance_analytics.metrics` | `mention_volume, sentiment_score, response_time, resolution_rate, roi` |
| `integrations.twitter.enabled` | `True` |
| `integrations.twitter.rate_limit_per_minute` | `300` |
| `integrations.twitter.search_query` | `@YourBrand OR #YourBrand` |
| `integrations.twitter.include_retweets` | `False` |
| `integrations.reddit.enabled` | `True` |
| `integrations.reddit.rate_limit_per_minute` | `60` |
| `integrations.reddit.subreddits` | `technology, business, marketing` |
| `integrations.newsapi.enabled` | `True` |
| `integrations.newsapi.rate_limit_per_minute` | `100` |
| `integrations.newsapi.query` | `YourBrand` |
| `integrations.newsapi.language` | `en` |
| `integrations.newsapi.sort_by` | `publishedAt` |
| `database.url` | `postgresql://brandmon:brandmon@localhost:5432/brand_monitoring` |
| `database.pool_size` | `10` |
| `database.max_overflow` | `20` |
| `database.pool_timeout` | `30` |
| `redis.url` | `redis://localhost:6379/0` |
| `redis.ttl_seconds` | `3600` |
| `monitoring.prometheus_enabled` | `True` |
| `monitoring.sentry_enabled` | `False` |
| `monitoring.sentry_dsn` | `` |
| `monitoring.sentry_traces_sample_rate` | `0.1` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `dev` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | OpenAI (for LangChain agents) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI (for LangChain agents) |
| `TWITTER_BEARER_TOKEN` | `your-twitter-bearer-token` | Twitter API |
| `TWITTER_API_KEY` | `your-twitter-api-key` | Twitter API |
| `TWITTER_API_SECRET` | `your-twitter-api-secret` | Twitter API |
| `REDDIT_CLIENT_ID` | `your-reddit-client-id` | Reddit API |
| `REDDIT_CLIENT_SECRET` | `your-reddit-client-secret` | Reddit API |
| `REDDIT_USER_AGENT` | `brand-monitoring/0.1.0` | Reddit API |
| `NEWSAPI_KEY` | `your-newsapi-key` | NewsAPI |
| `DATABASE_URL` | `postgresql://brandmon:brandmon@localhost:5432/brand_monitoring` | Database |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `SENTRY_DSN` | `` | Monitoring |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.1` | Monitoring |
| `BRAND_NAME` | `YourBrand` | Brand Configuration |
| `BRAND_KEYWORDS` | `YourBrand,YourProduct,YourCompany` | Brand Configuration |
| `BRAND_EXCLUDED_KEYWORDS` | `spam,competitor1,competitor2` | Brand Configuration |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: brand-monitoring
  version: 0.1.0
  env: dev
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  listening:
    enabled: True
    poll_interval_seconds: 60
    max_mentions_per_poll: 100
    platforms:
      - twitter
      - reddit
      - newsapi
  analysis:
    enabled: True
    sentiment_model: openai
    batch_size: 50
    topics:
      - product
      - service
      - pricing
      - support
      - competition
  response:
    enabled: True
    auto_respond: False
    response_templates_dir: config/templates
    max_response_length: 280
    approval_required: True
  reporting:
    enabled: True
    schedule: 0 9 * * 1
    formats:
      - json
      - pdf
    retention_days: 90
  performance_analytics:
    enabled: True
    metrics:
      - mention_volume
      - sentiment_score
      - response_time
      - resolution_rate
      - roi
integrations:
  twitter:
    enabled: True
    rate_limit_per_minute: 300
    search_query: @YourBrand OR #YourBrand
    include_retweets: False
  reddit:
    enabled: True
    rate_limit_per_minute: 60
    subreddits:
      - technology
      - business
      - marketing
  newsapi:
    enabled: True
    rate_limit_per_minute: 100
    query: YourBrand
    language: en
    sort_by: publishedAt
database:
  url: postgresql://brandmon:brandmon@localhost:5432/brand_monitoring
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
redis:
  url: redis://localhost:6379/0
  ttl_seconds: 3600
monitoring:
  prometheus_enabled: True
  sentry_enabled: False
  sentry_dsn: 
  sentry_traces_sample_rate: 0.1
```

---

## Example .env File

```bash
# Application
APP_ENV=dev
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-in-production

# OpenAI (for LangChain agents)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# Twitter API
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret

# Reddit API
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=brand-monitoring/0.1.0

# NewsAPI
NEWSAPI_KEY=your-newsapi-key

# Database
DATABASE_URL=postgresql://brandmon:brandmon@localhost:5432/brand_monitoring

# Redis
REDIS_URL=redis://localhost:6379/0

# Monitoring
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=0.1

# Brand Configuration
BRAND_NAME=YourBrand
BRAND_KEYWORDS=YourBrand,YourProduct,YourCompany
BRAND_EXCLUDED_KEYWORDS=spam,competitor1,competitor2

```

---

## Agent Configuration

```yaml
agents:
  analysis:
    batch_size: 50
    enabled: true
    sentiment_model: openai
    topics:
    - product
    - service
    - pricing
    - support
    - competition
  listening:
    enabled: true
    max_mentions_per_poll: 100
    platforms:
    - twitter
    - reddit
    - newsapi
    poll_interval_seconds: 60
  performance_analytics:
    enabled: true
    metrics:
    - mention_volume
    - sentiment_score
    - response_time
    - resolution_rate
    - roi
  reporting:
    enabled: true
    formats:
    - json
    - pdf
    retention_days: 90
    schedule: 0 9 * * 1
  response:
    approval_required: true
    auto_respond: false
    enabled: true
    max_response_length: 280
    response_templates_dir: config/templates
```

---

## Integration Settings

```yaml
integrations:
  newsapi:
    enabled: true
    language: en
    query: YourBrand
    rate_limit_per_minute: 100
    sort_by: publishedAt
  reddit:
    enabled: true
    rate_limit_per_minute: 60
    subreddits:
    - technology
    - business
    - marketing
  twitter:
    enabled: true
    include_retweets: false
    rate_limit_per_minute: 300
    search_query: '@YourBrand OR #YourBrand'
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
  sentry_traces_sample_rate: 0.1
```

---

## Rate Limiting & Caching

### redis

```yaml
redis:
  ttl_seconds: 3600
  url: redis://localhost:6379/0
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/brand-monitoring
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

*Generated for `brand-monitoring` — GRC_Claw Configuration Guide*

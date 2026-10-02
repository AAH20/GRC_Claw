# Smb Marketing — Configuration Guide

> SMB marketing platform for small businesses with content, campaigns, social, email, and analytics agents.

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

The **smb-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/smb-marketing/
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
| `app.name` | `SMB Marketing` |
| `app.version` | `0.1.0` |
| `app.description` | `Standalone modularized agentic AI marketing platform for small businesses` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `app.workers` | `4` |
| `llm.provider` | `openai` |
| `llm.model` | `gpt-4o` |
| `llm.temperature` | `0.7` |
| `llm.max_tokens` | `4096` |
| `llm.timeout` | `60` |
| `llm.max_retries` | `3` |
| `agents.content.enabled` | `True` |
| `agents.content.default_tone` | `professional` |
| `agents.content.max_length` | `2000` |
| `agents.content.supported_formats` | `blog_post, ad_copy, product_description, social_caption, email_body` |
| `agents.campaigns.enabled` | `True` |
| `agents.campaigns.default_duration_days` | `30` |
| `agents.campaigns.max_budget` | `10000` |
| `agents.campaigns.channels` | `meta, google_ads, mailchimp` |
| `agents.social.enabled` | `True` |
| `agents.social.platforms` | `facebook, instagram` |
| `agents.social.max_posts_per_day` | `5` |
| `agents.social.best_time_window.start` | `09:00` |
| `agents.social.best_time_window.end` | `17:00` |
| `agents.email.enabled` | `True` |
| `agents.email.max_recipients` | `5000` |
| `agents.email.ab_test_enabled` | `True` |
| `agents.email.default_from_name` | `SMB Marketing` |
| `agents.email.default_from_email` | `marketing@example.com` |
| `agents.analytics.enabled` | `True` |
| `agents.analytics.metrics` | `impressions, clicks, conversions, ctr, roas, engagement_rate` |
| `agents.analytics.report_frequency` | `weekly` |
| `agents.analytics.data_retention_days` | `365` |
| `integrations.meta.enabled` | `True` |
| `integrations.meta.api_version` | `v18.0` |
| `integrations.meta.base_url` | `https://graph.facebook.com` |
| `integrations.meta.timeout` | `30` |
| `integrations.meta.rate_limit_per_hour` | `200` |
| `integrations.google_ads.enabled` | `True` |
| `integrations.google_ads.api_version` | `v14` |
| `integrations.google_ads.base_url` | `https://googleads.googleapis.com` |
| `integrations.google_ads.timeout` | `30` |
| `integrations.google_ads.rate_limit_per_hour` | `1000` |
| `integrations.mailchimp.enabled` | `True` |
| `integrations.mailchimp.api_version` | `3.0` |
| `integrations.mailchimp.base_url` | `https://{server_prefix}.api.mailchimp.com` |
| `integrations.mailchimp.timeout` | `30` |
| `integrations.mailchimp.rate_limit_per_hour` | `500` |
| `api.prefix` | `/api/v1` |
| `api.cors_origins` | `http://localhost:3000, http://localhost:8080` |
| `api.rate_limit` | `100/minute` |
| `api.max_request_size` | `10MB` |
| `monitoring.enabled` | `True` |
| `monitoring.metrics_endpoint` | `/metrics` |
| `monitoring.health_endpoint` | `/health` |
| `monitoring.tracing_enabled` | `True` |
| `monitoring.sentry_dsn` | `None` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | NEVER commit .env to version control. |
| `LOG_LEVEL` | `DEBUG` | NEVER commit .env to version control. |
| `SECRET_KEY` | `change-me-in-production` | NEVER commit .env to version control. |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | NEVER commit .env to version control. |
| `OPENAI_MODEL` | `gpt-4o` | NEVER commit .env to version control. |
| `OPENAI_TEMPERATURE` | `0.7` | NEVER commit .env to version control. |
| `OPENAI_MAX_TOKENS` | `4096` | NEVER commit .env to version control. |
| `META_ACCESS_TOKEN` | `your-meta-access-token` | NEVER commit .env to version control. |
| `META_PAGE_ID` | `your-facebook-page-id` | NEVER commit .env to version control. |
| `META_APP_ID` | `your-meta-app-id` | NEVER commit .env to version control. |
| `META_APP_SECRET` | `your-meta-app-secret` | NEVER commit .env to version control. |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | `your-google-ads-developer-token` | NEVER commit .env to version control. |
| `GOOGLE_ADS_CLIENT_ID` | `your-google-client-id` | NEVER commit .env to version control. |
| `GOOGLE_ADS_CLIENT_SECRET` | `your-google-client-secret` | NEVER commit .env to version control. |
| `GOOGLE_ADS_REFRESH_TOKEN` | `your-google-refresh-token` | NEVER commit .env to version control. |
| `GOOGLE_ADS_CUSTOMER_ID` | `your-google-customer-id` | NEVER commit .env to version control. |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | `your-mcc-customer-id` | NEVER commit .env to version control. |
| `MAILCHIMP_API_KEY` | `your-mailchimp-api-key` | NEVER commit .env to version control. |
| `MAILCHIMP_SERVER_PREFIX` | `us1` | NEVER commit .env to version control. |
| `MAILCHIMP_LIST_ID` | `your-audience-list-id` | NEVER commit .env to version control. |
| `DATABASE_URL` | `postgresql+asyncpg://user:password@localhost:5432/smb_marketing` | NEVER commit .env to version control. |
| `REDIS_URL` | `redis://localhost:6379/0` | NEVER commit .env to version control. |
| `SENTRY_DSN` | `` | NEVER commit .env to version control. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `` | NEVER commit .env to version control. |
| `OTEL_SERVICE_NAME` | `smb-marketing` | NEVER commit .env to version control. |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: SMB Marketing
  version: 0.1.0
  description: Standalone modularized agentic AI marketing platform for small businesses
  environment: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
  workers: 4
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  max_tokens: 4096
  timeout: 60
  max_retries: 3
agents:
  content:
    enabled: True
    default_tone: professional
    max_length: 2000
    supported_formats:
      - blog_post
      - ad_copy
      - product_description
      - social_caption
      - email_body
  campaigns:
    enabled: True
    default_duration_days: 30
    max_budget: 10000
    channels:
      - meta
      - google_ads
      - mailchimp
  social:
    enabled: True
    platforms:
      - facebook
      - instagram
    max_posts_per_day: 5
    best_time_window:
      start: 09:00
      end: 17:00
  email:
    enabled: True
    max_recipients: 5000
    ab_test_enabled: True
    default_from_name: SMB Marketing
    default_from_email: marketing@example.com
  analytics:
    enabled: True
    metrics:
      - impressions
      - clicks
      - conversions
      - ctr
      - roas
      - engagement_rate
    report_frequency: weekly
    data_retention_days: 365
integrations:
  meta:
    enabled: True
    api_version: v18.0
    base_url: https://graph.facebook.com
    timeout: 30
    rate_limit_per_hour: 200
  google_ads:
    enabled: True
    api_version: v14
    base_url: https://googleads.googleapis.com
    timeout: 30
    rate_limit_per_hour: 1000
  mailchimp:
    enabled: True
    api_version: 3.0
    base_url: https://{server_prefix}.api.mailchimp.com
    timeout: 30
    rate_limit_per_hour: 500
api:
  prefix: /api/v1
  cors_origins:
    - http://localhost:3000
    - http://localhost:8080
  rate_limit: 100/minute
  max_request_size: 10MB
monitoring:
  enabled: True
  metrics_endpoint: /metrics
  health_endpoint: /health
  tracing_enabled: True
  sentry_dsn: None
```

---

## Example .env File

```bash
# SMB Marketing Environment Variables
# Copy this file to .env and fill in your actual values.
# NEVER commit .env to version control.

# ─── Application ───────────────────────────────────────────────
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-in-production

# ─── LLM / OpenAI ─────────────────────────────────────────────
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=4096

# ─── Meta (Facebook / Instagram) ──────────────────────────────
META_ACCESS_TOKEN=your-meta-access-token
META_PAGE_ID=your-facebook-page-id
META_APP_ID=your-meta-app-id
META_APP_SECRET=your-meta-app-secret

# ─── Google Ads ───────────────────────────────────────────────
GOOGLE_ADS_DEVELOPER_TOKEN=your-google-ads-developer-token
GOOGLE_ADS_CLIENT_ID=your-google-client-id
GOOGLE_ADS_CLIENT_SECRET=your-google-client-secret
GOOGLE_ADS_REFRESH_TOKEN=your-google-refresh-token
GOOGLE_ADS_CUSTOMER_ID=your-google-customer-id
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your-mcc-customer-id

# ─── Mailchimp ───────────────────────────────────────────────
MAILCHIMP_API_KEY=your-mailchimp-api-key
MAILCHIMP_SERVER_PREFIX=us1
MAILCHIMP_LIST_ID=your-audience-list-id

# ─── Database (optional) ──────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/smb_marketing
REDIS_URL=redis://localhost:6379/0

# ─── Monitoring ───────────────────────────────────────────────
SENTRY_DSN=
OTEL_EXPORTER_OTLP_ENDPOINT=
OTEL_SERVICE_NAME=smb-marketing

```

---

## Agent Configuration

```yaml
agents:
  analytics:
    data_retention_days: 365
    enabled: true
    metrics:
    - impressions
    - clicks
    - conversions
    - ctr
    - roas
    - engagement_rate
    report_frequency: weekly
  campaigns:
    channels:
    - meta
    - google_ads
    - mailchimp
    default_duration_days: 30
    enabled: true
    max_budget: 10000
  content:
    default_tone: professional
    enabled: true
    max_length: 2000
    supported_formats:
    - blog_post
    - ad_copy
    - product_description
    - social_caption
    - email_body
  email:
    ab_test_enabled: true
    default_from_email: marketing@example.com
    default_from_name: SMB Marketing
    enabled: true
    max_recipients: 5000
  social:
    best_time_window:
      end: '17:00'
      start: 09:00
    enabled: true
    max_posts_per_day: 5
    platforms:
    - facebook
    - instagram
```

---

## Integration Settings

```yaml
integrations:
  google_ads:
    api_version: v14
    base_url: https://googleads.googleapis.com
    enabled: true
    rate_limit_per_hour: 1000
    timeout: 30
  mailchimp:
    api_version: '3.0'
    base_url: https://{server_prefix}.api.mailchimp.com
    enabled: true
    rate_limit_per_hour: 500
    timeout: 30
  meta:
    api_version: v18.0
    base_url: https://graph.facebook.com
    enabled: true
    rate_limit_per_hour: 200
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
  enabled: true
  health_endpoint: /health
  metrics_endpoint: /metrics
  sentry_dsn: null
  tracing_enabled: true
```

---

## Rate Limiting & Caching

No explicit rate limiting or caching configuration found.

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/smb-marketing
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

*Generated for `smb-marketing` — GRC_Claw Configuration Guide*

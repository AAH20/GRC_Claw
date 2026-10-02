# Real Estate Marketing — Configuration Guide

> Real estate marketing platform for listings, lead nurture, virtual tours, and market analytics.

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

The **real-estate-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/real-estate-marketing/
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
| `app.name` | `Real Estate Marketing Platform` |
| `app.version` | `0.1.0` |
| `app.description` | `AI-powered real estate marketing automation` |
| `app.environment` | `development` |
| `app.debug` | `True` |
| `app.log_level` | `INFO` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `server.reload` | `True` |
| `server.timeout_keep_alive` | `30` |
| `database.url` | `postgresql://postgres:postgres@localhost:5432/real_estate` |
| `database.pool_size` | `20` |
| `database.max_overflow` | `10` |
| `database.pool_timeout` | `30` |
| `database.echo` | `False` |
| `redis.url` | `redis://localhost:6379/0` |
| `redis.max_connections` | `50` |
| `agents.listings.model` | `gpt-4` |
| `agents.listings.temperature` | `0.7` |
| `agents.listings.max_tokens` | `2000` |
| `agents.listings.retry_attempts` | `3` |
| `agents.listings.retry_delay` | `1.0` |
| `agents.lead_nurture.model` | `gpt-4` |
| `agents.lead_nurture.temperature` | `0.5` |
| `agents.lead_nurture.max_tokens` | `1500` |
| `agents.lead_nurture.retry_attempts` | `3` |
| `agents.lead_nurture.retry_delay` | `1.0` |
| `agents.virtual_tours.model` | `gpt-4` |
| `agents.virtual_tours.temperature` | `0.6` |
| `agents.virtual_tours.max_tokens` | `1800` |
| `agents.virtual_tours.retry_attempts` | `3` |
| `agents.virtual_tours.retry_delay` | `1.0` |
| `agents.analytics.model` | `gpt-4` |
| `agents.analytics.temperature` | `0.3` |
| `agents.analytics.max_tokens` | `2500` |
| `agents.analytics.retry_attempts` | `3` |
| `agents.analytics.retry_delay` | `1.0` |
| `agents.reporting.model` | `gpt-4` |
| `agents.reporting.temperature` | `0.4` |
| `agents.reporting.max_tokens` | `3000` |
| `agents.reporting.retry_attempts` | `3` |
| `agents.reporting.retry_delay` | `1.0` |
| `integrations.zillow.base_url` | `https://api.zillow.com/v2` |
| `integrations.zillow.timeout` | `30` |
| `integrations.zillow.rate_limit` | `100` |
| `integrations.realtor.base_url` | `https://api.realtor.com/v1` |
| `integrations.realtor.timeout` | `30` |
| `integrations.realtor.rate_limit` | `100` |
| `integrations.salesforce.base_url` | `https://login.salesforce.com` |
| `integrations.salesforce.timeout` | `30` |
| `integrations.salesforce.api_version` | `v58.0` |
| `marketing.email_templates_dir` | `templates/email` |
| `marketing.report_templates_dir` | `templates/reports` |
| `marketing.default_from_email` | `marketing@realestate.com` |
| `marketing.nurture_sequence` | `{'delay_days': 0, 'template': 'welcome'}, {'delay_days': 3, 'template': 'property_recommendations'}, {'delay_days': 7, 'template': 'market_update'}, {'delay_days': 14, 'template': 'follow_up'}, {'delay_days': 30, 'template': 'check_in'}` |
| `analytics.tracking_enabled` | `True` |
| `analytics.attribution_window_days` | `30` |
| `analytics.session_timeout_minutes` | `30` |
| `analytics.metrics` | `impressions, clicks, leads, conversions, revenue` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `development` | Application |
| `DEBUG` | `true` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `SECRET_KEY` | `your-secret-key-here` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/real_estate` | Database |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LLM Providers |
| `ANTHROPIC_API_KEY` | `sk-ant-your-anthropic-api-key` | LLM Providers |
| `ZILLOW_API_KEY` | `your-zillow-api-key` | Zillow API |
| `ZILLOW_API_SECRET` | `your-zillow-api-secret` | Zillow API |
| `REALTOR_API_KEY` | `your-realtor-api-key` | Realtor.com API |
| `REALTOR_API_SECRET` | `your-realtor-api-secret` | Realtor.com API |
| `SALESFORCE_USERNAME` | `your-salesforce-username` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | Salesforce |
| `SALESFORCE_DOMAIN` | `login` | Salesforce |
| `SENDGRID_API_KEY` | `your-sendgrid-api-key` | Email (SendGrid / SES) |
| `DEFAULT_FROM_EMAIL` | `marketing@realestate.com` | Email (SendGrid / SES) |
| `GOOGLE_ANALYTICS_ID` | `your-ga-id` | Analytics |
| `MIXPANEL_TOKEN` | `your-mixpanel-token` | Analytics |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Celery |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: Real Estate Marketing Platform
  version: 0.1.0
  description: AI-powered real estate marketing automation
  environment: development
  debug: True
  log_level: INFO
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: True
  timeout_keep_alive: 30
database:
  url: postgresql://postgres:postgres@localhost:5432/real_estate
  pool_size: 20
  max_overflow: 10
  pool_timeout: 30
  echo: False
redis:
  url: redis://localhost:6379/0
  max_connections: 50
agents:
  listings:
    model: gpt-4
    temperature: 0.7
    max_tokens: 2000
    retry_attempts: 3
    retry_delay: 1.0
  lead_nurture:
    model: gpt-4
    temperature: 0.5
    max_tokens: 1500
    retry_attempts: 3
    retry_delay: 1.0
  virtual_tours:
    model: gpt-4
    temperature: 0.6
    max_tokens: 1800
    retry_attempts: 3
    retry_delay: 1.0
  analytics:
    model: gpt-4
    temperature: 0.3
    max_tokens: 2500
    retry_attempts: 3
    retry_delay: 1.0
  reporting:
    model: gpt-4
    temperature: 0.4
    max_tokens: 3000
    retry_attempts: 3
    retry_delay: 1.0
integrations:
  zillow:
    base_url: https://api.zillow.com/v2
    timeout: 30
    rate_limit: 100
  realtor:
    base_url: https://api.realtor.com/v1
    timeout: 30
    rate_limit: 100
  salesforce:
    base_url: https://login.salesforce.com
    timeout: 30
    api_version: v58.0
marketing:
  email_templates_dir: templates/email
  report_templates_dir: templates/reports
  default_from_email: marketing@realestate.com
  nurture_sequence:
    -
      delay_days: 0
      template: welcome
    -
      delay_days: 3
      template: property_recommendations
    -
      delay_days: 7
      template: market_update
    -
      delay_days: 14
      template: follow_up
    -
      delay_days: 30
      template: check_in
analytics:
  tracking_enabled: True
  attribution_window_days: 30
  session_timeout_minutes: 30
  metrics:
    - impressions
    - clicks
    - leads
    - conversions
    - revenue
```

---

## Example .env File

```bash
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/real_estate

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM Providers
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# Zillow API
ZILLOW_API_KEY=your-zillow-api-key
ZILLOW_API_SECRET=your-zillow-api-secret

# Realtor.com API
REALTOR_API_KEY=your-realtor-api-key
REALTOR_API_SECRET=your-realtor-api-secret

# Salesforce
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_DOMAIN=login

# Email (SendGrid / SES)
SENDGRID_API_KEY=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=marketing@realestate.com

# Analytics
GOOGLE_ANALYTICS_ID=your-ga-id
MIXPANEL_TOKEN=your-mixpanel-token

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

```

---

## Agent Configuration

```yaml
agents:
  analytics:
    max_tokens: 2500
    model: gpt-4
    retry_attempts: 3
    retry_delay: 1.0
    temperature: 0.3
  lead_nurture:
    max_tokens: 1500
    model: gpt-4
    retry_attempts: 3
    retry_delay: 1.0
    temperature: 0.5
  listings:
    max_tokens: 2000
    model: gpt-4
    retry_attempts: 3
    retry_delay: 1.0
    temperature: 0.7
  reporting:
    max_tokens: 3000
    model: gpt-4
    retry_attempts: 3
    retry_delay: 1.0
    temperature: 0.4
  virtual_tours:
    max_tokens: 1800
    model: gpt-4
    retry_attempts: 3
    retry_delay: 1.0
    temperature: 0.6
```

---

## Integration Settings

```yaml
integrations:
  realtor:
    base_url: https://api.realtor.com/v1
    rate_limit: 100
    timeout: 30
  salesforce:
    api_version: v58.0
    base_url: https://login.salesforce.com
    timeout: 30
  zillow:
    base_url: https://api.zillow.com/v2
    rate_limit: 100
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
cd ~/GRC_Claw/projects/real-estate-marketing
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

*Generated for `real-estate-marketing` — GRC_Claw Configuration Guide*

# Marketing Attribution — Configuration Guide

> Multi-touch attribution platform supporting first-touch, last-touch, linear, time-decay, and data-driven models.

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

The **marketing-attribution** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/marketing-attribution/
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
| `app.name` | `marketing-attribution` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.data_collection.enabled` | `True` |
| `agents.data_collection.schedule` | `0 */6 * * *` |
| `agents.data_collection.batch_size` | `1000` |
| `agents.data_collection.timeout_seconds` | `300` |
| `agents.data_collection.retry_attempts` | `3` |
| `agents.data_collection.sources` | `google_ads, meta_ads, google_analytics` |
| `agents.attribution_engine.enabled` | `True` |
| `agents.attribution_engine.default_model` | `data_driven` |
| `agents.attribution_engine.available_models` | `first_touch, last_touch, linear, time_decay, data_driven` |
| `agents.attribution_engine.time_decay_half_life_days` | `7` |
| `agents.attribution_engine.min_touchpoints` | `1` |
| `agents.predictive_analytics.enabled` | `True` |
| `agents.predictive_analytics.forecast_horizon_days` | `30` |
| `agents.predictive_analytics.confidence_level` | `0.95` |
| `agents.predictive_analytics.model_retrain_interval_hours` | `24` |
| `agents.predictive_analytics.features` | `spend, impressions, clicks, conversions, day_of_week, hour_of_day` |
| `agents.reporting.enabled` | `True` |
| `agents.reporting.default_format` | `pdf` |
| `agents.reporting.available_formats` | `pdf, csv, json` |
| `agents.reporting.schedule` | `0 8 * * *` |
| `agents.reporting.retention_days` | `90` |
| `agents.realtime_dashboards.enabled` | `True` |
| `agents.realtime_dashboards.websocket_path` | `/api/v1/dashboards/stream` |
| `agents.realtime_dashboards.update_interval_seconds` | `30` |
| `agents.realtime_dashboards.max_connections` | `100` |
| `integrations.google_ads.enabled` | `True` |
| `integrations.google_ads.api_version` | `v14` |
| `integrations.google_ads.developer_token` | `${GOOGLE_ADS_DEVELOPER_TOKEN}` |
| `integrations.google_ads.client_id` | `${GOOGLE_ADS_CLIENT_ID}` |
| `integrations.google_ads.client_secret` | `${GOOGLE_ADS_CLIENT_SECRET}` |
| `integrations.google_ads.refresh_token` | `${GOOGLE_ADS_REFRESH_TOKEN}` |
| `integrations.google_ads.login_customer_id` | `${GOOGLE_ADS_LOGIN_CUSTOMER_ID}` |
| `integrations.meta_ads.enabled` | `True` |
| `integrations.meta_ads.api_version` | `v18.0` |
| `integrations.meta_ads.access_token` | `${META_ACCESS_TOKEN}` |
| `integrations.meta_ads.app_id` | `${META_APP_ID}` |
| `integrations.meta_ads.app_secret` | `${META_APP_SECRET}` |
| `integrations.meta_ads.ad_account_id` | `${META_AD_ACCOUNT_ID}` |
| `integrations.google_analytics.enabled` | `True` |
| `integrations.google_analytics.api_version` | `v1beta` |
| `integrations.google_analytics.property_id` | `${GA_PROPERTY_ID}` |
| `integrations.google_analytics.credentials_path` | `${GOOGLE_APPLICATION_CREDENTIALS}` |
| `cache.redis_url` | `${REDIS_URL}` |
| `cache.ttl_seconds` | `3600` |
| `database.url` | `${DATABASE_URL}` |
| `database.pool_size` | `10` |
| `database.max_overflow` | `20` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `DATABASE_URL` | `postgresql://user:password@localhost:5432/marketing_attribution` | Database |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | `your-developer-token` | Google Ads API |
| `GOOGLE_ADS_CLIENT_ID` | `your-client-id` | Google Ads API |
| `GOOGLE_ADS_CLIENT_SECRET` | `your-client-secret` | Google Ads API |
| `GOOGLE_ADS_REFRESH_TOKEN` | `your-refresh-token` | Google Ads API |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | `your-login-customer-id` | Google Ads API |
| `META_ACCESS_TOKEN` | `your-access-token` | Meta Ads API |
| `META_APP_ID` | `your-app-id` | Meta Ads API |
| `META_APP_SECRET` | `your-app-secret` | Meta Ads API |
| `META_AD_ACCOUNT_ID` | `your-ad-account-id` | Meta Ads API |
| `GA_PROPERTY_ID` | `your-property-id` | Google Analytics API |
| `GOOGLE_APPLICATION_CREDENTIALS` | `/path/to/service-account.json` | Google Analytics API |
| `OPENAI_API_KEY` | `your-openai-api-key` | LangChain / LLM |
| `LANGCHAIN_API_KEY` | `your-langchain-api-key` | LangChain / LLM |
| `LANGCHAIN_TRACING_V2` | `true` | LangChain / LLM |
| `LANGCHAIN_PROJECT` | `marketing-attribution` | LangChain / LLM |
| `PROMETHEUS_PORT` | `9090` | Monitoring |
| `SENTRY_DSN` | `your-sentry-dsn` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: marketing-attribution
  version: 0.1.0
  environment: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  data_collection:
    enabled: True
    schedule: 0 */6 * * *
    batch_size: 1000
    timeout_seconds: 300
    retry_attempts: 3
    sources:
      - google_ads
      - meta_ads
      - google_analytics
  attribution_engine:
    enabled: True
    default_model: data_driven
    available_models:
      - first_touch
      - last_touch
      - linear
      - time_decay
      - data_driven
    time_decay_half_life_days: 7
    min_touchpoints: 1
  predictive_analytics:
    enabled: True
    forecast_horizon_days: 30
    confidence_level: 0.95
    model_retrain_interval_hours: 24
    features:
      - spend
      - impressions
      - clicks
      - conversions
      - day_of_week
      - hour_of_day
  reporting:
    enabled: True
    default_format: pdf
    available_formats:
      - pdf
      - csv
      - json
    schedule: 0 8 * * *
    retention_days: 90
  realtime_dashboards:
    enabled: True
    websocket_path: /api/v1/dashboards/stream
    update_interval_seconds: 30
    max_connections: 100
integrations:
  google_ads:
    enabled: True
    api_version: v14
    developer_token: ${GOOGLE_ADS_DEVELOPER_TOKEN}
    client_id: ${GOOGLE_ADS_CLIENT_ID}
    client_secret: ${GOOGLE_ADS_CLIENT_SECRET}
    refresh_token: ${GOOGLE_ADS_REFRESH_TOKEN}
    login_customer_id: ${GOOGLE_ADS_LOGIN_CUSTOMER_ID}
  meta_ads:
    enabled: True
    api_version: v18.0
    access_token: ${META_ACCESS_TOKEN}
    app_id: ${META_APP_ID}
    app_secret: ${META_APP_SECRET}
    ad_account_id: ${META_AD_ACCOUNT_ID}
  google_analytics:
    enabled: True
    api_version: v1beta
    property_id: ${GA_PROPERTY_ID}
    credentials_path: ${GOOGLE_APPLICATION_CREDENTIALS}
cache:
  redis_url: ${REDIS_URL}
  ttl_seconds: 3600
database:
  url: ${DATABASE_URL}
  pool_size: 10
  max_overflow: 20
```

---

## Example .env File

```bash
# Marketing Attribution Environment Variables
# Copy this file to .env and fill in your values

# Application
APP_ENVIRONMENT=development
LOG_LEVEL=INFO
SECRET_KEY=change-me-in-production

# Redis
REDIS_URL=redis://localhost:6379/0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/marketing_attribution

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=your-developer-token
GOOGLE_ADS_CLIENT_ID=your-client-id
GOOGLE_ADS_CLIENT_SECRET=your-client-secret
GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your-login-customer-id

# Meta Ads API
META_ACCESS_TOKEN=your-access-token
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret
META_AD_ACCOUNT_ID=your-ad-account-id

# Google Analytics API
GA_PROPERTY_ID=your-property-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# LangChain / LLM
OPENAI_API_KEY=your-openai-api-key
LANGCHAIN_API_KEY=your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=marketing-attribution

# Monitoring
PROMETHEUS_PORT=9090
SENTRY_DSN=your-sentry-dsn

```

---

## Agent Configuration

```yaml
agents:
  attribution_engine:
    available_models:
    - first_touch
    - last_touch
    - linear
    - time_decay
    - data_driven
    default_model: data_driven
    enabled: true
    min_touchpoints: 1
    time_decay_half_life_days: 7
  data_collection:
    batch_size: 1000
    enabled: true
    retry_attempts: 3
    schedule: 0 */6 * * *
    sources:
    - google_ads
    - meta_ads
    - google_analytics
    timeout_seconds: 300
  predictive_analytics:
    confidence_level: 0.95
    enabled: true
    features:
    - spend
    - impressions
    - clicks
    - conversions
    - day_of_week
    - hour_of_day
    forecast_horizon_days: 30
    model_retrain_interval_hours: 24
  realtime_dashboards:
    enabled: true
    max_connections: 100
    update_interval_seconds: 30
    websocket_path: /api/v1/dashboards/stream
  reporting:
    available_formats:
    - pdf
    - csv
    - json
    default_format: pdf
    enabled: true
    retention_days: 90
    schedule: 0 8 * * *
```

---

## Integration Settings

```yaml
integrations:
  google_ads:
    api_version: v14
    client_id: ${GOOGLE_ADS_CLIENT_ID}
    client_secret: ${GOOGLE_ADS_CLIENT_SECRET}
    developer_token: ${GOOGLE_ADS_DEVELOPER_TOKEN}
    enabled: true
    login_customer_id: ${GOOGLE_ADS_LOGIN_CUSTOMER_ID}
    refresh_token: ${GOOGLE_ADS_REFRESH_TOKEN}
  google_analytics:
    api_version: v1beta
    credentials_path: ${GOOGLE_APPLICATION_CREDENTIALS}
    enabled: true
    property_id: ${GA_PROPERTY_ID}
  meta_ads:
    access_token: ${META_ACCESS_TOKEN}
    ad_account_id: ${META_AD_ACCOUNT_ID}
    api_version: v18.0
    app_id: ${META_APP_ID}
    app_secret: ${META_APP_SECRET}
    enabled: true
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
  redis_url: ${REDIS_URL}
  ttl_seconds: 3600
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/marketing-attribution
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

*Generated for `marketing-attribution` — GRC_Claw Configuration Guide*

# Customer Segmentation — Configuration Guide

> AI-powered customer segmentation platform using RFM analysis, K-means/DBSCAN clustering, and behavioral segmentation.

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

The **customer-segmentation** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/customer-segmentation/
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
| `app.name` | `customer-segmentation` |
| `app.version` | `0.1.0` |
| `app.description` | `AI-powered customer segmentation platform` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `app.workers` | `4` |
| `agents.default_provider` | `openai` |
| `agents.openai.model` | `gpt-4-turbo-preview` |
| `agents.openai.temperature` | `0.1` |
| `agents.openai.max_tokens` | `4096` |
| `agents.openai.timeout` | `60` |
| `agents.anthropic.model` | `claude-3-5-sonnet-20241022` |
| `agents.anthropic.temperature` | `0.1` |
| `agents.anthropic.max_tokens` | `4096` |
| `agents.anthropic.timeout` | `60` |
| `agents.data_collector.batch_size` | `500` |
| `agents.data_collector.max_retries` | `3` |
| `agents.data_collector.retry_delay` | `1.0` |
| `agents.data_collector.cache_ttl` | `3600` |
| `agents.analyst.rfm_quantiles` | `5` |
| `agents.analyst.min_cluster_size` | `10` |
| `agents.analyst.max_clusters` | `10` |
| `agents.analyst.outlier_threshold` | `3.0` |
| `agents.segment_builder.algorithm` | `kmeans` |
| `agents.segment_builder.n_clusters` | `5` |
| `agents.segment_builder.random_state` | `42` |
| `agents.segment_builder.feature_scaling` | `standard` |
| `agents.strategist.max_recommendations` | `5` |
| `agents.strategist.strategy_templates` | `email_campaign, retargeting, loyalty_program, upsell, win_back` |
| `agents.reviewer.min_segment_size` | `50` |
| `agents.reviewer.max_segment_size` | `100000` |
| `agents.reviewer.bias_threshold` | `0.15` |
| `agents.reviewer.quality_threshold` | `0.7` |
| `agents.performance_analytics.metrics_window_days` | `30` |
| `agents.performance_analytics.attribution_model` | `last_touch` |
| `agents.performance_analytics.kpi_thresholds.conversion_rate` | `0.05` |
| `agents.performance_analytics.kpi_thresholds.churn_rate` | `0.1` |
| `agents.performance_analytics.kpi_thresholds.roi` | `2.0` |
| `integrations.salesforce.api_version` | `v59.0` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.salesforce.timeout` | `30` |
| `integrations.salesforce.rate_limit` | `100` |
| `integrations.salesforce.objects` | `Account, Contact, Opportunity, Lead, Campaign, CampaignMember` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.timeout` | `30` |
| `integrations.hubspot.rate_limit` | `100` |
| `integrations.hubspot.objects` | `contacts, companies, deals, engagements` |
| `integrations.google_analytics.api_version` | `v1beta` |
| `integrations.google_analytics.timeout` | `30` |
| `integrations.google_analytics.rate_limit` | `100` |
| `integrations.google_analytics.dimensions` | `date, deviceCategory, channelGrouping, country` |
| `integrations.google_analytics.metrics` | `activeUsers, newUsers, sessions, conversions, totalRevenue` |
| `cache.backend` | `redis` |
| `cache.redis.host` | `localhost` |
| `cache.redis.port` | `6379` |
| `cache.redis.db` | `0` |
| `cache.redis.password` | `None` |
| `cache.redis.ttl` | `3600` |
| `monitoring.enabled` | `True` |
| `monitoring.prometheus.port` | `9090` |
| `monitoring.prometheus.path` | `/metrics` |
| `monitoring.health_check.interval` | `30` |
| `monitoring.health_check.timeout` | `10` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | NEVER commit .env to version control. |
| `LOG_LEVEL` | `DEBUG` | NEVER commit .env to version control. |
| `SECRET_KEY` | `change-me-to-a-random-secret-key-in-production` | NEVER commit .env to version control. |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | NEVER commit .env to version control. |
| `ANTHROPIC_API_KEY` | `sk-ant-your-anthropic-api-key` | NEVER commit .env to version control. |
| `SALESFORCE_USERNAME` | `your-salesforce-username@example.com` | NEVER commit .env to version control. |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | NEVER commit .env to version control. |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | NEVER commit .env to version control. |
| `SALESFORCE_DOMAIN` | `login` | NEVER commit .env to version control. |
| `SALESFORCE_API_VERSION` | `v59.0` | NEVER commit .env to version control. |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | NEVER commit .env to version control. |
| `HUBSPOT_PORTAL_ID` | `your-portal-id` | NEVER commit .env to version control. |
| `GOOGLE_ANALYTICS_PROPERTY_ID` | `123456789` | NEVER commit .env to version control. |
| `GOOGLE_APPLICATION_CREDENTIALS` | `/path/to/service-account-key.json` | NEVER commit .env to version control. |
| `REDIS_URL` | `redis://localhost:6379/0` | NEVER commit .env to version control. |
| `REDIS_PASSWORD` | `` | NEVER commit .env to version control. |
| `PROMETHEUS_PORT` | `9090` | NEVER commit .env to version control. |
| `SENTRY_DSN` | `` | NEVER commit .env to version control. |
| `DATADOG_API_KEY` | `` | NEVER commit .env to version control. |
| `ENABLE_REAL_TIME_SEGMENTATION` | `true` | NEVER commit .env to version control. |
| `ENABLE_PERFORMANCE_TRACKING` | `true` | NEVER commit .env to version control. |
| `ENABLE_BIAS_DETECTION` | `true` | NEVER commit .env to version control. |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: customer-segmentation
  version: 0.1.0
  description: AI-powered customer segmentation platform
  environment: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
  workers: 4
agents:
  default_provider: openai
  openai:
    model: gpt-4-turbo-preview
    temperature: 0.1
    max_tokens: 4096
    timeout: 60
  anthropic:
    model: claude-3-5-sonnet-20241022
    temperature: 0.1
    max_tokens: 4096
    timeout: 60
  data_collector:
    batch_size: 500
    max_retries: 3
    retry_delay: 1.0
    cache_ttl: 3600
  analyst:
    rfm_quantiles: 5
    min_cluster_size: 10
    max_clusters: 10
    outlier_threshold: 3.0
  segment_builder:
    algorithm: kmeans
    n_clusters: 5
    random_state: 42
    feature_scaling: standard
  strategist:
    max_recommendations: 5
    strategy_templates:
      - email_campaign
      - retargeting
      - loyalty_program
      - upsell
      - win_back
  reviewer:
    min_segment_size: 50
    max_segment_size: 100000
    bias_threshold: 0.15
    quality_threshold: 0.7
  performance_analytics:
    metrics_window_days: 30
    attribution_model: last_touch
    kpi_thresholds:
      conversion_rate: 0.05
      churn_rate: 0.1
      roi: 2.0
integrations:
  salesforce:
    api_version: v59.0
    sandbox: False
    timeout: 30
    rate_limit: 100
    objects:
      - Account
      - Contact
      - Opportunity
      - Lead
      - Campaign
      - CampaignMember
  hubspot:
    api_version: v3
    timeout: 30
    rate_limit: 100
    objects:
      - contacts
      - companies
      - deals
      - engagements
  google_analytics:
    api_version: v1beta
    timeout: 30
    rate_limit: 100
    dimensions:
      - date
      - deviceCategory
      - channelGrouping
      - country
    metrics:
      - activeUsers
      - newUsers
      - sessions
      - conversions
      - totalRevenue
cache:
  backend: redis
  redis:
    host: localhost
    port: 6379
    db: 0
    password: None
    ttl: 3600
monitoring:
  enabled: True
  prometheus:
    port: 9090
    path: /metrics
  health_check:
    interval: 30
    timeout: 10
```

---

## Example .env File

```bash
# Customer Segmentation Platform - Environment Variables
# Copy this file to .env and fill in your values.
# NEVER commit .env to version control.

# ─── Application ───────────────────────────────────────────────
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-to-a-random-secret-key-in-production

# ─── LLM Providers ─────────────────────────────────────────────
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# ─── Salesforce CRM ────────────────────────────────────────────
SALESFORCE_USERNAME=your-salesforce-username@example.com
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_DOMAIN=login  # Use 'test' for sandbox
SALESFORCE_API_VERSION=v59.0

# ─── HubSpot CRM ───────────────────────────────────────────────
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_PORTAL_ID=your-portal-id

# ─── Google Analytics ──────────────────────────────────────────
GOOGLE_ANALYTICS_PROPERTY_ID=123456789
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# ─── Redis Cache ───────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# ─── Monitoring ────────────────────────────────────────────────
PROMETHEUS_PORT=9090
SENTRY_DSN=
DATADOG_API_KEY=

# ─── Feature Flags ─────────────────────────────────────────────
ENABLE_REAL_TIME_SEGMENTATION=true
ENABLE_PERFORMANCE_TRACKING=true
ENABLE_BIAS_DETECTION=true

```

---

## Agent Configuration

```yaml
agents:
  analyst:
    max_clusters: 10
    min_cluster_size: 10
    outlier_threshold: 3.0
    rfm_quantiles: 5
  anthropic:
    max_tokens: 4096
    model: claude-3-5-sonnet-20241022
    temperature: 0.1
    timeout: 60
  data_collector:
    batch_size: 500
    cache_ttl: 3600
    max_retries: 3
    retry_delay: 1.0
  default_provider: openai
  openai:
    max_tokens: 4096
    model: gpt-4-turbo-preview
    temperature: 0.1
    timeout: 60
  performance_analytics:
    attribution_model: last_touch
    kpi_thresholds:
      churn_rate: 0.1
      conversion_rate: 0.05
      roi: 2.0
    metrics_window_days: 30
  reviewer:
    bias_threshold: 0.15
    max_segment_size: 100000
    min_segment_size: 50
    quality_threshold: 0.7
  segment_builder:
    algorithm: kmeans
    feature_scaling: standard
    n_clusters: 5
    random_state: 42
  strategist:
    max_recommendations: 5
    strategy_templates:
    - email_campaign
    - retargeting
    - loyalty_program
    - upsell
    - win_back
```

---

## Integration Settings

```yaml
integrations:
  google_analytics:
    api_version: v1beta
    dimensions:
    - date
    - deviceCategory
    - channelGrouping
    - country
    metrics:
    - activeUsers
    - newUsers
    - sessions
    - conversions
    - totalRevenue
    rate_limit: 100
    timeout: 30
  hubspot:
    api_version: v3
    objects:
    - contacts
    - companies
    - deals
    - engagements
    rate_limit: 100
    timeout: 30
  salesforce:
    api_version: v59.0
    objects:
    - Account
    - Contact
    - Opportunity
    - Lead
    - Campaign
    - CampaignMember
    rate_limit: 100
    sandbox: false
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
  health_check:
    interval: 30
    timeout: 10
  prometheus:
    path: /metrics
    port: 9090
```

---

## Rate Limiting & Caching

### cache

```yaml
cache:
  backend: redis
  redis:
    db: 0
    host: localhost
    password: null
    port: 6379
    ttl: 3600
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/customer-segmentation
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

*Generated for `customer-segmentation` — GRC_Claw Configuration Guide*

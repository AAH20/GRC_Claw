# Website Optimization — Configuration Guide

> Website optimization platform for A/B testing, personalization, SEO auditing, and performance monitoring.

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

The **website-optimization** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/website-optimization/
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
| `app.name` | `website-optimization` |
| `app.version` | `0.1.0` |
| `app.env` | `${APP_ENV:-development}` |
| `app.log_level` | `${LOG_LEVEL:-INFO}` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `agents.ab_testing.enabled` | `True` |
| `agents.ab_testing.default_confidence_level` | `0.95` |
| `agents.ab_testing.min_sample_size` | `100` |
| `agents.ab_testing.max_experiments_per_page` | `5` |
| `agents.personalization.enabled` | `True` |
| `agents.personalization.max_recommendations` | `10` |
| `agents.personalization.cache_ttl_seconds` | `300` |
| `agents.seo.enabled` | `True` |
| `agents.seo.max_audit_depth` | `3` |
| `agents.seo.check_mobile_friendly` | `True` |
| `agents.performance.enabled` | `True` |
| `agents.performance.metrics_retention_days` | `30` |
| `agents.performance.alert_threshold_ms` | `3000` |
| `agents.analytics.enabled` | `True` |
| `agents.analytics.batch_size` | `100` |
| `agents.analytics.flush_interval_seconds` | `60` |
| `integrations.google_analytics.enabled` | `True` |
| `integrations.google_analytics.measurement_id` | `${GA_MEASUREMENT_ID:-}` |
| `integrations.google_analytics.api_secret` | `${GA_API_SECRET:-}` |
| `integrations.google_analytics.base_url` | `https://www.google-analytics.com/mp/collect` |
| `integrations.hotjar.enabled` | `True` |
| `integrations.hotjar.site_id` | `${HOTJAR_SITE_ID:-}` |
| `integrations.hotjar.base_url` | `https://script.hotjar.com` |
| `integrations.optimizely.enabled` | `True` |
| `integrations.optimizely.sdk_key` | `${OPTIMIZELY_SDK_KEY:-}` |
| `integrations.optimizely.base_url` | `https://cdn.optimizely.com` |
| `cache.backend` | `redis` |
| `cache.url` | `${REDIS_URL:-redis://localhost:6379/0}` |
| `cache.ttl_seconds` | `300` |
| `rate_limiting.enabled` | `True` |
| `rate_limiting.requests_per_minute` | `60` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `PORT` | `8000` | Server |
| `GA_MEASUREMENT_ID` | `G-XXXXXXXXXX` | Google Analytics 4 |
| `GA_API_SECRET` | `your_ga_api_secret` | Google Analytics 4 |
| `HOTJAR_SITE_ID` | `your_hotjar_site_id` | Hotjar |
| `OPTIMIZELY_SDK_KEY` | `your_optimizely_sdk_key` | Optimizely |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (for caching) |
| `RATE_LIMIT_ENABLED` | `true` | Rate Limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Rate Limiting |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: website-optimization
  version: 0.1.0
  env: ${APP_ENV:-development}
  log_level: ${LOG_LEVEL:-INFO}
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
agents:
  ab_testing:
    enabled: True
    default_confidence_level: 0.95
    min_sample_size: 100
    max_experiments_per_page: 5
  personalization:
    enabled: True
    max_recommendations: 10
    cache_ttl_seconds: 300
  seo:
    enabled: True
    max_audit_depth: 3
    check_mobile_friendly: True
  performance:
    enabled: True
    metrics_retention_days: 30
    alert_threshold_ms: 3000
  analytics:
    enabled: True
    batch_size: 100
    flush_interval_seconds: 60
integrations:
  google_analytics:
    enabled: True
    measurement_id: ${GA_MEASUREMENT_ID:-}
    api_secret: ${GA_API_SECRET:-}
    base_url: https://www.google-analytics.com/mp/collect
  hotjar:
    enabled: True
    site_id: ${HOTJAR_SITE_ID:-}
    base_url: https://script.hotjar.com
  optimizely:
    enabled: True
    sdk_key: ${OPTIMIZELY_SDK_KEY:-}
    base_url: https://cdn.optimizely.com
cache:
  backend: redis
  url: ${REDIS_URL:-redis://localhost:6379/0}
  ttl_seconds: 300
rate_limiting:
  enabled: True
  requests_per_minute: 60
```

---

## Example .env File

```bash
# Application
APP_ENV=development
LOG_LEVEL=DEBUG

# Server
PORT=8000

# Google Analytics 4
GA_MEASUREMENT_ID=G-XXXXXXXXXX
GA_API_SECRET=your_ga_api_secret

# Hotjar
HOTJAR_SITE_ID=your_hotjar_site_id

# Optimizely
OPTIMIZELY_SDK_KEY=your_optimizely_sdk_key

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

```

---

## Agent Configuration

```yaml
agents:
  ab_testing:
    default_confidence_level: 0.95
    enabled: true
    max_experiments_per_page: 5
    min_sample_size: 100
  analytics:
    batch_size: 100
    enabled: true
    flush_interval_seconds: 60
  performance:
    alert_threshold_ms: 3000
    enabled: true
    metrics_retention_days: 30
  personalization:
    cache_ttl_seconds: 300
    enabled: true
    max_recommendations: 10
  seo:
    check_mobile_friendly: true
    enabled: true
    max_audit_depth: 3
```

---

## Integration Settings

```yaml
integrations:
  google_analytics:
    api_secret: ${GA_API_SECRET:-}
    base_url: https://www.google-analytics.com/mp/collect
    enabled: true
    measurement_id: ${GA_MEASUREMENT_ID:-}
  hotjar:
    base_url: https://script.hotjar.com
    enabled: true
    site_id: ${HOTJAR_SITE_ID:-}
  optimizely:
    base_url: https://cdn.optimizely.com
    enabled: true
    sdk_key: ${OPTIMIZELY_SDK_KEY:-}
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
  ttl_seconds: 300
  url: ${REDIS_URL:-redis://localhost:6379/0}
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
cd ~/GRC_Claw/projects/website-optimization
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

*Generated for `website-optimization` — GRC_Claw Configuration Guide*

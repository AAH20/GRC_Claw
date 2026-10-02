# Analytics — Configuration Guide

> Marketing analytics and attribution platform with data collection, multi-touch attribution, predictive analytics, and real-time dashboards.

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

The **analytics** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/analytics/
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
| `app.name` | `analytics-attribution` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `redis.url` | `redis://localhost:6379/0` |
| `redis.ttl` | `3600` |
| `agents.data_collection.batch_size` | `1000` |
| `agents.data_collection.lookback_days` | `30` |
| `agents.data_collection.timeout_seconds` | `60` |
| `agents.data_collection.retry_attempts` | `3` |
| `agents.data_collection.sources` | `google_analytics, mixpanel, amplitude` |
| `agents.attribution_engine.models` | `first_touch, last_touch, linear, time_decay, data_driven` |
| `agents.attribution_engine.default_model` | `data_driven` |
| `agents.attribution_engine.time_decay_half_life_days` | `7` |
| `agents.attribution_engine.min_touchpoints` | `1` |
| `agents.predictive_analytics.forecast_horizon_days` | `30` |
| `agents.predictive_analytics.confidence_level` | `0.95` |
| `agents.predictive_analytics.model_types` | `linear_regression, random_forest, gradient_boosting` |
| `agents.predictive_analytics.retrain_interval_hours` | `24` |
| `agents.predictive_analytics.feature_window_days` | `90` |
| `agents.reporting.formats` | `json, csv, pdf` |
| `agents.reporting.schedule` | `0 6 * * *` |
| `agents.reporting.retention_days` | `90` |
| `agents.reporting.max_reports` | `100` |
| `agents.realtime_dashboards.websocket_ping_interval` | `30` |
| `agents.realtime_dashboards.max_connections` | `100` |
| `agents.realtime_dashboards.metrics_refresh_seconds` | `5` |
| `agents.realtime_dashboards.buffer_size` | `1000` |
| `integrations.google_analytics.property_id` | `` |
| `integrations.google_analytics.credentials_path` | `` |
| `integrations.google_analytics.api_version` | `v1beta` |
| `integrations.google_analytics.batch_size` | `10000` |
| `integrations.mixpanel.project_id` | `` |
| `integrations.mixpanel.api_secret` | `` |
| `integrations.mixpanel.api_host` | `https://api.mixpanel.com` |
| `integrations.mixpanel.batch_size` | `5000` |
| `integrations.amplitude.api_key` | `` |
| `integrations.amplitude.api_host` | `https://api2.amplitude.com` |
| `integrations.amplitude.batch_size` | `1000` |
| `monitoring.prometheus_enabled` | `True` |
| `monitoring.metrics_port` | `9090` |
| `monitoring.health_check_interval` | `30` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `SERVER_HOST` | `0.0.0.0` | Server |
| `SERVER_PORT` | `8000` | Server |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `GA_PROPERTY_ID` | `123456789` | Google Analytics |
| `GA_CREDENTIALS_PATH` | `config/ga-credentials.json` | Google Analytics |
| `MIXPANEL_PROJECT_ID` | `your-project-id` | Mixpanel |
| `MIXPANEL_API_SECRET` | `your-api-secret` | Mixpanel |
| `AMPLITUDE_API_KEY` | `your-api-key` | Amplitude |
| `LANGCHAIN_API_KEY` | `your-langchain-api-key` | LangChain / DeepAgents |
| `LANGCHAIN_TRACING_V2` | `true` | LangChain / DeepAgents |
| `LANGCHAIN_PROJECT` | `analytics-attribution` | LangChain / DeepAgents |
| `GRC_MARKETING_CORE_API_KEY` | `your-grc-api-key` | grc-marketing-core |
| `PROMETHEUS_ENABLED` | `true` | Monitoring |
| `METRICS_PORT` | `9090` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: analytics-attribution
  version: 0.1.0
  environment: development
  log_level: INFO
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
redis:
  url: redis://localhost:6379/0
  ttl: 3600
agents:
  data_collection:
    batch_size: 1000
    lookback_days: 30
    timeout_seconds: 60
    retry_attempts: 3
    sources:
      - google_analytics
      - mixpanel
      - amplitude
  attribution_engine:
    models:
      - first_touch
      - last_touch
      - linear
      - time_decay
      - data_driven
    default_model: data_driven
    time_decay_half_life_days: 7
    min_touchpoints: 1
  predictive_analytics:
    forecast_horizon_days: 30
    confidence_level: 0.95
    model_types:
      - linear_regression
      - random_forest
      - gradient_boosting
    retrain_interval_hours: 24
    feature_window_days: 90
  reporting:
    formats:
      - json
      - csv
      - pdf
    schedule: 0 6 * * *
    retention_days: 90
    max_reports: 100
  realtime_dashboards:
    websocket_ping_interval: 30
    max_connections: 100
    metrics_refresh_seconds: 5
    buffer_size: 1000
integrations:
  google_analytics:
    property_id: 
    credentials_path: 
    api_version: v1beta
    batch_size: 10000
  mixpanel:
    project_id: 
    api_secret: 
    api_host: https://api.mixpanel.com
    batch_size: 5000
  amplitude:
    api_key: 
    api_host: https://api2.amplitude.com
    batch_size: 1000
monitoring:
  prometheus_enabled: True
  metrics_port: 9090
  health_check_interval: 30
```

---

## Example .env File

```bash
# Application
APP_ENVIRONMENT=development
LOG_LEVEL=INFO

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Redis
REDIS_URL=redis://localhost:6379/0

# Google Analytics
GA_PROPERTY_ID=123456789
GA_CREDENTIALS_PATH=config/ga-credentials.json

# Mixpanel
MIXPANEL_PROJECT_ID=your-project-id
MIXPANEL_API_SECRET=your-api-secret

# Amplitude
AMPLITUDE_API_KEY=your-api-key

# LangChain / DeepAgents
LANGCHAIN_API_KEY=your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=analytics-attribution

# grc-marketing-core
GRC_MARKETING_CORE_API_KEY=your-grc-api-key

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

```

---

## Agent Configuration

```yaml
agents:
  attribution_engine:
    default_model: data_driven
    min_touchpoints: 1
    models:
    - first_touch
    - last_touch
    - linear
    - time_decay
    - data_driven
    time_decay_half_life_days: 7
  data_collection:
    batch_size: 1000
    lookback_days: 30
    retry_attempts: 3
    sources:
    - google_analytics
    - mixpanel
    - amplitude
    timeout_seconds: 60
  predictive_analytics:
    confidence_level: 0.95
    feature_window_days: 90
    forecast_horizon_days: 30
    model_types:
    - linear_regression
    - random_forest
    - gradient_boosting
    retrain_interval_hours: 24
  realtime_dashboards:
    buffer_size: 1000
    max_connections: 100
    metrics_refresh_seconds: 5
    websocket_ping_interval: 30
  reporting:
    formats:
    - json
    - csv
    - pdf
    max_reports: 100
    retention_days: 90
    schedule: 0 6 * * *
```

---

## Integration Settings

```yaml
integrations:
  amplitude:
    api_host: https://api2.amplitude.com
    api_key: ''
    batch_size: 1000
  google_analytics:
    api_version: v1beta
    batch_size: 10000
    credentials_path: ''
    property_id: ''
  mixpanel:
    api_host: https://api.mixpanel.com
    api_secret: ''
    batch_size: 5000
    project_id: ''
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

### monitoring

```yaml
monitoring:
  health_check_interval: 30
  metrics_port: 9090
  prometheus_enabled: true
```

---

## Rate Limiting & Caching

### redis

```yaml
redis:
  ttl: 3600
  url: redis://localhost:6379/0
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/analytics
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

*Generated for `analytics` — GRC_Claw Configuration Guide*

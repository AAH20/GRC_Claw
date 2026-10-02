# Sales Forecaster — Configuration Guide

> Sales forecasting platform with Prophet/ARIMA/ensemble models, seasonality detection, and actionable recommendations.

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

The **sales-forecaster** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/sales-forecaster/
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
| `app.name` | `sales-forecaster` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.debug` | `False` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `server.timeout_keep_alive` | `30` |
| `redis.url` | `redis://localhost:6379/0` |
| `redis.max_connections` | `20` |
| `redis.socket_timeout` | `5` |
| `agents.data_collection.timeout_seconds` | `120` |
| `agents.data_collection.retry_attempts` | `3` |
| `agents.data_collection.batch_size` | `500` |
| `agents.data_collection.sources` | `salesforce, hubspot, sap` |
| `agents.analysis.seasonality_mode` | `multiplicative` |
| `agents.analysis.changepoint_prior_scale` | `0.05` |
| `agents.analysis.interval_width` | `0.95` |
| `agents.analysis.anomaly_threshold` | `2.5` |
| `agents.prediction.forecast_horizon_days` | `90` |
| `agents.prediction.confidence_level` | `0.95` |
| `agents.prediction.models` | `prophet, arima, ensemble` |
| `agents.prediction.retrain_threshold_days` | `30` |
| `agents.action.max_recommendations` | `10` |
| `agents.action.priority_threshold` | `0.7` |
| `agents.action.auto_approve` | `False` |
| `agents.performance_analytics.kpi_window_days` | `30` |
| `agents.performance_analytics.drift_threshold` | `0.15` |
| `agents.performance_analytics.alert_channels` | `email, slack` |
| `integrations.salesforce.api_version` | `v59.0` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.salesforce.timeout_seconds` | `30` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.timeout_seconds` | `30` |
| `integrations.sap.base_url` | `` |
| `integrations.sap.timeout_seconds` | `60` |
| `pipeline.max_concurrent_runs` | `5` |
| `pipeline.run_timeout_seconds` | `600` |
| `pipeline.checkpoint_interval_seconds` | `60` |
| `observability.metrics_enabled` | `True` |
| `observability.tracing_enabled` | `True` |
| `observability.profiling_enabled` | `False` |
| `observability.jaeger_endpoint` | `http://localhost:14268/api/traces` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `DEBUG` | `true` | Application |
| `SERVER_HOST` | `0.0.0.0` | Server |
| `SERVER_PORT` | `8000` | Server |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LangChain / LLM |
| `LANGCHAIN_API_KEY` | `lsv2-your-langchain-api-key` | LangChain / LLM |
| `LANGCHAIN_TRACING_V2` | `true` | LangChain / LLM |
| `LANGCHAIN_PROJECT` | `sales-forecaster` | LangChain / LLM |
| `SALESFORCE_CLIENT_ID` | `your-salesforce-client-id` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `your-salesforce-client-secret` | Salesforce |
| `SALESFORCE_USERNAME` | `your-salesforce-username` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | Salesforce |
| `SALESFORCE_SANDBOX` | `false` | Salesforce |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | HubSpot |
| `HUBSPOT_PORTAL_ID` | `your-portal-id` | HubSpot |
| `SAP_BASE_URL` | `https://your-sap-instance.example.com` | SAP |
| `SAP_USERNAME` | `your-sap-username` | SAP |
| `SAP_PASSWORD` | `your-sap-password` | SAP |
| `SAP_CLIENT` | `100` | SAP |
| `DATABASE_URL` | `postgresql+asyncpg://user:password@localhost:5432/sales_forecaster` | Database (optional - for persistent storage) |
| `JAEGER_ENDPOINT` | `http://localhost:14268/api/traces` | Observability |
| `PROMETHEUS_PORT` | `9090` | Observability |
| `API_KEY_HEADER` | `X-API-Key` | Security |
| `API_KEY` | `your-api-key-here` | Security |
| `CORS_ORIGINS` | `["http://localhost:3000","https://yourdomain.com"]` | Security |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: sales-forecaster
  version: 0.1.0
  environment: development
  log_level: INFO
  debug: False
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  timeout_keep_alive: 30
redis:
  url: redis://localhost:6379/0
  max_connections: 20
  socket_timeout: 5
agents:
  data_collection:
    timeout_seconds: 120
    retry_attempts: 3
    batch_size: 500
    sources:
      - salesforce
      - hubspot
      - sap
  analysis:
    seasonality_mode: multiplicative
    changepoint_prior_scale: 0.05
    interval_width: 0.95
    anomaly_threshold: 2.5
  prediction:
    forecast_horizon_days: 90
    confidence_level: 0.95
    models:
      - prophet
      - arima
      - ensemble
    retrain_threshold_days: 30
  action:
    max_recommendations: 10
    priority_threshold: 0.7
    auto_approve: False
  performance_analytics:
    kpi_window_days: 30
    drift_threshold: 0.15
    alert_channels:
      - email
      - slack
integrations:
  salesforce:
    api_version: v59.0
    sandbox: False
    timeout_seconds: 30
  hubspot:
    api_version: v3
    timeout_seconds: 30
  sap:
    base_url: 
    timeout_seconds: 60
pipeline:
  max_concurrent_runs: 5
  run_timeout_seconds: 600
  checkpoint_interval_seconds: 60
observability:
  metrics_enabled: True
  tracing_enabled: True
  profiling_enabled: False
  jaeger_endpoint: http://localhost:14268/api/traces
```

---

## Example .env File

```bash
# Application
APP_ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Redis
REDIS_URL=redis://localhost:6379/0

# LangChain / LLM
OPENAI_API_KEY=sk-your-openai-api-key
LANGCHAIN_API_KEY=lsv2-your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=sales-forecaster

# Salesforce
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_SANDBOX=false

# HubSpot
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_PORTAL_ID=your-portal-id

# SAP
SAP_BASE_URL=https://your-sap-instance.example.com
SAP_USERNAME=your-sap-username
SAP_PASSWORD=your-sap-password
SAP_CLIENT=100

# Database (optional - for persistent storage)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/sales_forecaster

# Observability
JAEGER_ENDPOINT=http://localhost:14268/api/traces
PROMETHEUS_PORT=9090

# Security
API_KEY_HEADER=X-API-Key
API_KEY=your-api-key-here
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

```

---

## Agent Configuration

```yaml
agents:
  action:
    auto_approve: false
    max_recommendations: 10
    priority_threshold: 0.7
  analysis:
    anomaly_threshold: 2.5
    changepoint_prior_scale: 0.05
    interval_width: 0.95
    seasonality_mode: multiplicative
  data_collection:
    batch_size: 500
    retry_attempts: 3
    sources:
    - salesforce
    - hubspot
    - sap
    timeout_seconds: 120
  performance_analytics:
    alert_channels:
    - email
    - slack
    drift_threshold: 0.15
    kpi_window_days: 30
  prediction:
    confidence_level: 0.95
    forecast_horizon_days: 90
    models:
    - prophet
    - arima
    - ensemble
    retrain_threshold_days: 30
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    api_version: v3
    timeout_seconds: 30
  salesforce:
    api_version: v59.0
    sandbox: false
    timeout_seconds: 30
  sap:
    base_url: ''
    timeout_seconds: 60
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

### observability

```yaml
observability:
  jaeger_endpoint: http://localhost:14268/api/traces
  metrics_enabled: true
  profiling_enabled: false
  tracing_enabled: true
```

---

## Rate Limiting & Caching

### redis

```yaml
redis:
  max_connections: 20
  socket_timeout: 5
  url: redis://localhost:6379/0
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/sales-forecaster
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

*Generated for `sales-forecaster` — GRC_Claw Configuration Guide*

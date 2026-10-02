# Marketing Personalization — Configuration Guide

> Real-time marketing personalization platform with data collection, analysis, and optimization agents.

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

The **marketing-personalization** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/marketing-personalization/
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
| `app.name` | `marketing-personalization` |
| `app.version` | `1.0.0` |
| `app.env` | `development` |
| `app.log_level` | `INFO` |
| `app.debug` | `False` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `server.timeout` | `30` |
| `redis.url` | `redis://localhost:6379/0` |
| `redis.max_connections` | `10` |
| `redis.socket_timeout` | `5` |
| `agents.data_collection.timeout` | `60` |
| `agents.data_collection.max_retries` | `3` |
| `agents.data_collection.batch_size` | `100` |
| `agents.analysis.timeout` | `120` |
| `agents.analysis.max_retries` | `2` |
| `agents.personalization.timeout` | `90` |
| `agents.personalization.max_retries` | `2` |
| `agents.optimization.timeout` | `120` |
| `agents.optimization.max_retries` | `2` |
| `agents.governance.timeout` | `30` |
| `agents.governance.max_retries` | `1` |
| `agents.performance_analytics.timeout` | `60` |
| `agents.performance_analytics.max_retries` | `2` |
| `agents.orchestrator.timeout` | `300` |
| `agents.orchestrator.max_retries` | `1` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.timeout` | `30` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.hubspot.timeout` | `30` |
| `integrations.hubspot.max_results` | `100` |
| `integrations.mailchimp.timeout` | `30` |
| `integrations.mailchimp.max_results` | `1000` |
| `prometheus.enabled` | `True` |
| `prometheus.port` | `9090` |
| `prometheus.path` | `/metrics` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `DEBUG` | `true` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `LANGCHAIN_API_KEY` | `your-langchain-api-key` | LangChain |
| `LANGCHAIN_TRACING_V2` | `true` | LangChain |
| `LANGCHAIN_PROJECT` | `marketing-personalization` | LangChain |
| `SALESFORCE_USERNAME` | `your-salesforce-username` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | Salesforce |
| `SALESFORCE_DOMAIN` | `login` | Salesforce |
| `SALESFORCE_API_VERSION` | `v58.0` | Salesforce |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | HubSpot |
| `MAILCHIMP_API_KEY` | `your-mailchimp-api-key` | Mailchimp |
| `MAILCHIMP_SERVER_PREFIX` | `us1` | Mailchimp |
| `OPENAI_API_KEY` | `your-openai-api-key` | OpenAI (for LangChain agents) |
| `PROMETHEUS_ENABLED` | `true` | Prometheus |
| `PROMETHEUS_PORT` | `9090` | Prometheus |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: marketing-personalization
  version: 1.0.0
  env: development
  log_level: INFO
  debug: False
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  timeout: 30
redis:
  url: redis://localhost:6379/0
  max_connections: 10
  socket_timeout: 5
agents:
  data_collection:
    timeout: 60
    max_retries: 3
    batch_size: 100
  analysis:
    timeout: 120
    max_retries: 2
  personalization:
    timeout: 90
    max_retries: 2
  optimization:
    timeout: 120
    max_retries: 2
  governance:
    timeout: 30
    max_retries: 1
  performance_analytics:
    timeout: 60
    max_retries: 2
  orchestrator:
    timeout: 300
    max_retries: 1
integrations:
  salesforce:
    api_version: v58.0
    timeout: 30
    sandbox: False
  hubspot:
    timeout: 30
    max_results: 100
  mailchimp:
    timeout: 30
    max_results: 1000
prometheus:
  enabled: True
  port: 9090
  path: /metrics
```

---

## Example .env File

```bash
# Application
APP_ENV=development
LOG_LEVEL=DEBUG
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Redis
REDIS_URL=redis://localhost:6379/0

# LangChain
LANGCHAIN_API_KEY=your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=marketing-personalization

# Salesforce
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_DOMAIN=login
SALESFORCE_API_VERSION=v58.0

# HubSpot
HUBSPOT_API_KEY=your-hubspot-api-key

# Mailchimp
MAILCHIMP_API_KEY=your-mailchimp-api-key
MAILCHIMP_SERVER_PREFIX=us1

# OpenAI (for LangChain agents)
OPENAI_API_KEY=your-openai-api-key

# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

```

---

## Agent Configuration

```yaml
agents:
  analysis:
    max_retries: 2
    timeout: 120
  data_collection:
    batch_size: 100
    max_retries: 3
    timeout: 60
  governance:
    max_retries: 1
    timeout: 30
  optimization:
    max_retries: 2
    timeout: 120
  orchestrator:
    max_retries: 1
    timeout: 300
  performance_analytics:
    max_retries: 2
    timeout: 60
  personalization:
    max_retries: 2
    timeout: 90
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    max_results: 100
    timeout: 30
  mailchimp:
    max_results: 1000
    timeout: 30
  salesforce:
    api_version: v58.0
    sandbox: false
    timeout: 30
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

### prometheus

```yaml
prometheus:
  enabled: true
  path: /metrics
  port: 9090
```

---

## Rate Limiting & Caching

### redis

```yaml
redis:
  max_connections: 10
  socket_timeout: 5
  url: redis://localhost:6379/0
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/marketing-personalization
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

*Generated for `marketing-personalization` — GRC_Claw Configuration Guide*

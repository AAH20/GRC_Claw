# Workflow Automation — Configuration Guide

> Workflow automation platform integrating n8n, Zapier, and Make for process automation and integration management.

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

The **workflow-automation** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/workflow-automation/
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
| `app.name` | `workflow-automation` |
| `app.version` | `0.1.0` |
| `app.env` | `dev` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.workflow_discovery.enabled` | `True` |
| `agents.workflow_discovery.max_concurrent_discoveries` | `5` |
| `agents.workflow_discovery.timeout_seconds` | `300` |
| `agents.workflow_discovery.cache_ttl_seconds` | `3600` |
| `agents.workflow_optimization.enabled` | `True` |
| `agents.workflow_optimization.max_concurrent_optimizations` | `3` |
| `agents.workflow_optimization.timeout_seconds` | `600` |
| `agents.workflow_optimization.suggestion_limit` | `10` |
| `agents.process_automation.enabled` | `True` |
| `agents.process_automation.max_concurrent_executions` | `10` |
| `agents.process_automation.timeout_seconds` | `1800` |
| `agents.process_automation.retry_attempts` | `3` |
| `agents.process_automation.retry_delay_seconds` | `5` |
| `agents.integration_automation.enabled` | `True` |
| `agents.integration_automation.sync_interval_seconds` | `300` |
| `agents.integration_automation.timeout_seconds` | `120` |
| `agents.integration_automation.max_retries` | `3` |
| `agents.performance_analytics.enabled` | `True` |
| `agents.performance_analytics.metrics_retention_days` | `90` |
| `agents.performance_analytics.report_interval_seconds` | `3600` |
| `agents.performance_analytics.dashboard_refresh_seconds` | `60` |
| `integrations.n8n.enabled` | `True` |
| `integrations.n8n.base_url` | `http://localhost:5678` |
| `integrations.n8n.api_key` | `` |
| `integrations.n8n.webhook_path` | `/webhook` |
| `integrations.n8n.timeout_seconds` | `30` |
| `integrations.zapier.enabled` | `True` |
| `integrations.zapier.webhook_url` | `` |
| `integrations.zapier.timeout_seconds` | `30` |
| `integrations.make.enabled` | `True` |
| `integrations.make.base_url` | `https://www.make.com` |
| `integrations.make.api_key` | `` |
| `integrations.make.team_id` | `` |
| `integrations.make.timeout_seconds` | `30` |
| `langchain.api_key` | `` |
| `langchain.project` | `workflow-automation` |
| `langchain.tracing` | `False` |
| `langchain.model` | `gpt-4` |
| `langchain.temperature` | `0.1` |
| `langchain.max_tokens` | `4096` |
| `grc_marketing_core.enabled` | `True` |
| `grc_marketing_core.api_endpoint` | `` |
| `grc_marketing_core.api_key` | `` |
| `prometheus.enabled` | `True` |
| `prometheus.port` | `9090` |
| `prometheus.path` | `/metrics` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `dev` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `N8N_BASE_URL` | `http://localhost:5678` | n8n Integration |
| `N8N_API_KEY` | `` | n8n Integration |
| `ZAPIER_WEBHOOK_URL` | `` | Zapier Integration |
| `MAKE_BASE_URL` | `https://www.make.com` | Make Integration |
| `MAKE_API_KEY` | `` | Make Integration |
| `MAKE_TEAM_ID` | `` | Make Integration |
| `LANGCHAIN_API_KEY` | `` | LangChain |
| `LANGCHAIN_PROJECT` | `workflow-automation` | LangChain |
| `LANGCHAIN_TRACING` | `false` | LangChain |
| `GRC_MARKETING_CORE_ENABLED` | `true` | grc-marketing-core |
| `GRC_MARKETING_CORE_API_ENDPOINT` | `` | grc-marketing-core |
| `GRC_MARKETING_CORE_API_KEY` | `` | grc-marketing-core |
| `PROMETHEUS_ENABLED` | `true` | Prometheus |
| `PROMETHEUS_PORT` | `9090` | Prometheus |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: workflow-automation
  version: 0.1.0
  env: dev
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  workflow_discovery:
    enabled: True
    max_concurrent_discoveries: 5
    timeout_seconds: 300
    cache_ttl_seconds: 3600
  workflow_optimization:
    enabled: True
    max_concurrent_optimizations: 3
    timeout_seconds: 600
    suggestion_limit: 10
  process_automation:
    enabled: True
    max_concurrent_executions: 10
    timeout_seconds: 1800
    retry_attempts: 3
    retry_delay_seconds: 5
  integration_automation:
    enabled: True
    sync_interval_seconds: 300
    timeout_seconds: 120
    max_retries: 3
  performance_analytics:
    enabled: True
    metrics_retention_days: 90
    report_interval_seconds: 3600
    dashboard_refresh_seconds: 60
integrations:
  n8n:
    enabled: True
    base_url: http://localhost:5678
    api_key: 
    webhook_path: /webhook
    timeout_seconds: 30
  zapier:
    enabled: True
    webhook_url: 
    timeout_seconds: 30
  make:
    enabled: True
    base_url: https://www.make.com
    api_key: 
    team_id: 
    timeout_seconds: 30
langchain:
  api_key: 
  project: workflow-automation
  tracing: False
  model: gpt-4
  temperature: 0.1
  max_tokens: 4096
grc_marketing_core:
  enabled: True
  api_endpoint: 
  api_key: 
prometheus:
  enabled: True
  port: 9090
  path: /metrics
```

---

## Example .env File

```bash
# Application
APP_ENV=dev
LOG_LEVEL=INFO
SECRET_KEY=change-me-in-production

# Server
HOST=0.0.0.0
PORT=8000

# n8n Integration
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=

# Zapier Integration
ZAPIER_WEBHOOK_URL=

# Make Integration
MAKE_BASE_URL=https://www.make.com
MAKE_API_KEY=
MAKE_TEAM_ID=

# LangChain
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=workflow-automation
LANGCHAIN_TRACING=false

# grc-marketing-core
GRC_MARKETING_CORE_ENABLED=true
GRC_MARKETING_CORE_API_ENDPOINT=
GRC_MARKETING_CORE_API_KEY=

# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

```

---

## Agent Configuration

```yaml
agents:
  integration_automation:
    enabled: true
    max_retries: 3
    sync_interval_seconds: 300
    timeout_seconds: 120
  performance_analytics:
    dashboard_refresh_seconds: 60
    enabled: true
    metrics_retention_days: 90
    report_interval_seconds: 3600
  process_automation:
    enabled: true
    max_concurrent_executions: 10
    retry_attempts: 3
    retry_delay_seconds: 5
    timeout_seconds: 1800
  workflow_discovery:
    cache_ttl_seconds: 3600
    enabled: true
    max_concurrent_discoveries: 5
    timeout_seconds: 300
  workflow_optimization:
    enabled: true
    max_concurrent_optimizations: 3
    suggestion_limit: 10
    timeout_seconds: 600
```

---

## Integration Settings

```yaml
integrations:
  make:
    api_key: ''
    base_url: https://www.make.com
    enabled: true
    team_id: ''
    timeout_seconds: 30
  n8n:
    api_key: ''
    base_url: http://localhost:5678
    enabled: true
    timeout_seconds: 30
    webhook_path: /webhook
  zapier:
    enabled: true
    timeout_seconds: 30
    webhook_url: ''
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

No explicit rate limiting or caching configuration found.

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/workflow-automation
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

*Generated for `workflow-automation` — GRC_Claw Configuration Guide*

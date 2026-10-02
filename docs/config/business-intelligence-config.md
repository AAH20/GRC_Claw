# Business Intelligence — Configuration Guide

> Business intelligence platform with data collection, analysis, visualization, and predictive analytics agents.

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

The **business-intelligence** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/business-intelligence/
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
| `app.name` | `business-intelligence` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `debug` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `agents.data_collection.timeout_seconds` | `300` |
| `agents.data_collection.max_retries` | `3` |
| `agents.data_collection.batch_size` | `1000` |
| `agents.analysis.timeout_seconds` | `600` |
| `agents.analysis.confidence_threshold` | `0.95` |
| `agents.visualization.timeout_seconds` | `120` |
| `agents.visualization.default_format` | `png` |
| `agents.visualization.dpi` | `150` |
| `agents.reporting.timeout_seconds` | `300` |
| `agents.reporting.formats` | `pdf, html, markdown` |
| `agents.predictive_analytics.timeout_seconds` | `900` |
| `agents.predictive_analytics.model_cache_ttl` | `3600` |
| `integrations.tableau.server_url` | `https://tableau.example.com` |
| `integrations.tableau.site_id` | `` |
| `integrations.tableau.api_version` | `3.19` |
| `integrations.tableau.token_name` | `` |
| `integrations.tableau.token_secret` | `` |
| `integrations.powerbi.tenant_id` | `` |
| `integrations.powerbi.client_id` | `` |
| `integrations.powerbi.client_secret` | `` |
| `integrations.powerbi.workspace_id` | `` |
| `integrations.powerbi.api_base` | `https://api.powerbi.com/v1.0/myorg` |
| `integrations.looker.base_url` | `https://looker.example.com` |
| `integrations.looker.client_id` | `` |
| `integrations.looker.client_secret` | `` |
| `integrations.looker.api_version` | `4.0` |
| `database.url` | `sqlite:///./bi.db` |
| `database.echo` | `False` |
| `cache.backend` | `redis` |
| `cache.url` | `redis://localhost:6379/0` |
| `cache.ttl` | `3600` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `debug` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `DATABASE_URL` | `sqlite:///./bi.db` | Database |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache |
| `TABLEAU_SERVER_URL` | `https://tableau.example.com` | Tableau |
| `TABLEAU_SITE_ID` | `` | Tableau |
| `TABLEAU_TOKEN_NAME` | `` | Tableau |
| `TABLEAU_TOKEN_SECRET` | `` | Tableau |
| `POWER_BI_TENANT_ID` | `` | Power BI |
| `POWER_BI_CLIENT_ID` | `` | Power BI |
| `POWER_BI_CLIENT_SECRET` | `` | Power BI |
| `POWER_BI_WORKSPACE_ID` | `` | Power BI |
| `LOOKER_BASE_URL` | `https://looker.example.com` | Looker |
| `LOOKER_CLIENT_ID` | `` | Looker |
| `LOOKER_CLIENT_SECRET` | `` | Looker |
| `LANGCHAIN_API_KEY` | `` | LangChain / DeepAgents |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain / DeepAgents |
| `LANGCHAIN_PROJECT` | `business-intelligence` | LangChain / DeepAgents |
| `GRC_MARKETING_CORE_API_KEY` | `` | grc-marketing-core |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: business-intelligence
  version: 0.1.0
  environment: development
  log_level: debug
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
agents:
  data_collection:
    timeout_seconds: 300
    max_retries: 3
    batch_size: 1000
  analysis:
    timeout_seconds: 600
    confidence_threshold: 0.95
  visualization:
    timeout_seconds: 120
    default_format: png
    dpi: 150
  reporting:
    timeout_seconds: 300
    formats:
      - pdf
      - html
      - markdown
  predictive_analytics:
    timeout_seconds: 900
    model_cache_ttl: 3600
integrations:
  tableau:
    server_url: https://tableau.example.com
    site_id: 
    api_version: 3.19
    token_name: 
    token_secret: 
  powerbi:
    tenant_id: 
    client_id: 
    client_secret: 
    workspace_id: 
    api_base: https://api.powerbi.com/v1.0/myorg
  looker:
    base_url: https://looker.example.com
    client_id: 
    client_secret: 
    api_version: 4.0
database:
  url: sqlite:///./bi.db
  echo: False
cache:
  backend: redis
  url: redis://localhost:6379/0
  ttl: 3600
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=debug
SECRET_KEY=change-me-in-production

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./bi.db

# Cache
REDIS_URL=redis://localhost:6379/0

# Tableau
TABLEAU_SERVER_URL=https://tableau.example.com
TABLEAU_SITE_ID=
TABLEAU_TOKEN_NAME=
TABLEAU_TOKEN_SECRET=

# Power BI
POWER_BI_TENANT_ID=
POWER_BI_CLIENT_ID=
POWER_BI_CLIENT_SECRET=
POWER_BI_WORKSPACE_ID=

# Looker
LOOKER_BASE_URL=https://looker.example.com
LOOKER_CLIENT_ID=
LOOKER_CLIENT_SECRET=

# LangChain / DeepAgents
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=business-intelligence

# grc-marketing-core
GRC_MARKETING_CORE_API_KEY=

```

---

## Agent Configuration

```yaml
agents:
  analysis:
    confidence_threshold: 0.95
    timeout_seconds: 600
  data_collection:
    batch_size: 1000
    max_retries: 3
    timeout_seconds: 300
  predictive_analytics:
    model_cache_ttl: 3600
    timeout_seconds: 900
  reporting:
    formats:
    - pdf
    - html
    - markdown
    timeout_seconds: 300
  visualization:
    default_format: png
    dpi: 150
    timeout_seconds: 120
```

---

## Integration Settings

```yaml
integrations:
  looker:
    api_version: '4.0'
    base_url: https://looker.example.com
    client_id: ''
    client_secret: ''
  powerbi:
    api_base: https://api.powerbi.com/v1.0/myorg
    client_id: ''
    client_secret: ''
    tenant_id: ''
    workspace_id: ''
  tableau:
    api_version: '3.19'
    server_url: https://tableau.example.com
    site_id: ''
    token_name: ''
    token_secret: ''
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
  ttl: 3600
  url: redis://localhost:6379/0
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/business-intelligence
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

*Generated for `business-intelligence` — GRC_Claw Configuration Guide*

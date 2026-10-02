# Market Research — Configuration Guide

> Market research platform with data collection, SWOT/PESTEL analysis, competitive benchmarking, and reporting.

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

The **market-research** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/market-research/
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
| `app.name` | `market-research` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.debug` | `False` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `server.timeout` | `300` |
| `server.max_request_size` | `10485760` |
| `agents.max_concurrent` | `3` |
| `agents.timeout_seconds` | `600` |
| `agents.retry_attempts` | `3` |
| `agents.retry_delay_seconds` | `5` |
| `agents.model` | `gpt-4o` |
| `agents.temperature` | `0.1` |
| `agents.max_tokens` | `4096` |
| `data_collection.sources` | `statista, ibisworld, semrush` |
| `data_collection.cache_ttl_seconds` | `3600` |
| `data_collection.rate_limit_per_minute` | `60` |
| `data_collection.batch_size` | `100` |
| `analysis.methods` | `swot, porter_five_forces, pestel, competitive_benchmarking` |
| `analysis.confidence_threshold` | `0.7` |
| `analysis.min_data_points` | `10` |
| `reporting.formats` | `json, markdown, pdf` |
| `reporting.template_dir` | `templates` |
| `reporting.output_dir` | `outputs` |
| `reporting.include_visualizations` | `True` |
| `action.max_recommendations` | `10` |
| `action.priority_levels` | `critical, high, medium, low` |
| `action.validation_required` | `True` |
| `performance_analytics.metrics` | `roi, conversion_rate, customer_acquisition_cost, lifetime_value, market_share` |
| `performance_analytics.aggregation_period` | `monthly` |
| `performance_analytics.comparison_baseline` | `previous_period` |
| `integrations.statista.base_url` | `https://api.statista.com` |
| `integrations.statista.timeout_seconds` | `30` |
| `integrations.statista.rate_limit_per_minute` | `30` |
| `integrations.ibisworld.base_url` | `https://api.ibisworld.com` |
| `integrations.ibisworld.timeout_seconds` | `30` |
| `integrations.ibisworld.rate_limit_per_minute` | `20` |
| `integrations.semrush.base_url` | `https://api.semrush.com` |
| `integrations.semrush.timeout_seconds` | `30` |
| `integrations.semrush.rate_limit_per_minute` | `60` |
| `cache.backend` | `redis` |
| `cache.ttl_seconds` | `3600` |
| `cache.max_entries` | `10000` |
| `monitoring.enabled` | `True` |
| `monitoring.metrics_port` | `9090` |
| `monitoring.health_check_interval_seconds` | `30` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_NAME` | `market-research` | Application |
| `APP_ENVIRONMENT` | `development` | Application |
| `APP_DEBUG` | `false` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `SERVER_HOST` | `0.0.0.0` | Server |
| `SERVER_PORT` | `8000` | Server |
| `SERVER_WORKERS` | `4` | Server |
| `OPENAI_API_KEY` | `your-openai-api-key-here` | LLM Configuration |
| `OPENAI_MODEL` | `gpt-4o` | LLM Configuration |
| `OPENAI_TEMPERATURE` | `0.1` | LLM Configuration |
| `OPENAI_MAX_TOKENS` | `4096` | LLM Configuration |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain |
| `LANGCHAIN_API_KEY` | `your-langsmith-api-key-here` | LangChain |
| `LANGCHAIN_PROJECT` | `market-research` | LangChain |
| `MAX_CONCURRENT_AGENTS` | `3` | Agent Settings |
| `AGENT_TIMEOUT_SECONDS` | `600` | Agent Settings |
| `AGENT_RETRY_ATTEMPTS` | `3` | Agent Settings |
| `STATISTA_API_KEY` | `your-statista-api-key-here` | Research Platform API Keys |
| `IBISWORLD_API_KEY` | `your-ibisworld-api-key-here` | Research Platform API Keys |
| `SEMRUSH_API_KEY` | `your-semrush-api-key-here` | Research Platform API Keys |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache |
| `CACHE_TTL_SECONDS` | `3600` | Cache |
| `METRICS_ENABLED` | `true` | Monitoring |
| `METRICS_PORT` | `9090` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: market-research
  version: 0.1.0
  environment: development
  log_level: INFO
  debug: False
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  timeout: 300
  max_request_size: 10485760
agents:
  max_concurrent: 3
  timeout_seconds: 600
  retry_attempts: 3
  retry_delay_seconds: 5
  model: gpt-4o
  temperature: 0.1
  max_tokens: 4096
data_collection:
  sources:
    - statista
    - ibisworld
    - semrush
  cache_ttl_seconds: 3600
  rate_limit_per_minute: 60
  batch_size: 100
analysis:
  methods:
    - swot
    - porter_five_forces
    - pestel
    - competitive_benchmarking
  confidence_threshold: 0.7
  min_data_points: 10
reporting:
  formats:
    - json
    - markdown
    - pdf
  template_dir: templates
  output_dir: outputs
  include_visualizations: True
action:
  max_recommendations: 10
  priority_levels:
    - critical
    - high
    - medium
    - low
  validation_required: True
performance_analytics:
  metrics:
    - roi
    - conversion_rate
    - customer_acquisition_cost
    - lifetime_value
    - market_share
  aggregation_period: monthly
  comparison_baseline: previous_period
integrations:
  statista:
    base_url: https://api.statista.com
    timeout_seconds: 30
    rate_limit_per_minute: 30
  ibisworld:
    base_url: https://api.ibisworld.com
    timeout_seconds: 30
    rate_limit_per_minute: 20
  semrush:
    base_url: https://api.semrush.com
    timeout_seconds: 30
    rate_limit_per_minute: 60
cache:
  backend: redis
  ttl_seconds: 3600
  max_entries: 10000
monitoring:
  enabled: True
  metrics_port: 9090
  health_check_interval_seconds: 30
```

---

## Example .env File

```bash
# Application
APP_NAME=market-research
APP_ENVIRONMENT=development
APP_DEBUG=false
LOG_LEVEL=INFO

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SERVER_WORKERS=4

# LLM Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4096

# LangChain
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=market-research

# Agent Settings
MAX_CONCURRENT_AGENTS=3
AGENT_TIMEOUT_SECONDS=600
AGENT_RETRY_ATTEMPTS=3

# Research Platform API Keys
STATISTA_API_KEY=your-statista-api-key-here
IBISWORLD_API_KEY=your-ibisworld-api-key-here
SEMRUSH_API_KEY=your-semrush-api-key-here

# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=3600

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090

```

---

## Agent Configuration

```yaml
agents:
  max_concurrent: 3
  max_tokens: 4096
  model: gpt-4o
  retry_attempts: 3
  retry_delay_seconds: 5
  temperature: 0.1
  timeout_seconds: 600
```

---

## Integration Settings

```yaml
integrations:
  ibisworld:
    base_url: https://api.ibisworld.com
    rate_limit_per_minute: 20
    timeout_seconds: 30
  semrush:
    base_url: https://api.semrush.com
    rate_limit_per_minute: 60
    timeout_seconds: 30
  statista:
    base_url: https://api.statista.com
    rate_limit_per_minute: 30
    timeout_seconds: 30
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
  health_check_interval_seconds: 30
  metrics_port: 9090
```

---

## Rate Limiting & Caching

### cache

```yaml
cache:
  backend: redis
  max_entries: 10000
  ttl_seconds: 3600
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/market-research
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

*Generated for `market-research` — GRC_Claw Configuration Guide*

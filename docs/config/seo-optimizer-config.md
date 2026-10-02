# Seo Optimizer — Configuration Guide

> AI-powered SEO optimization platform for keyword research, content optimization, technical SEO, link building, and rank monitoring.

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

The **seo-optimizer** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/seo-optimizer/
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
| `app.name` | `SEO Optimizer` |
| `app.version` | `0.1.0` |
| `app.description` | `AI-powered SEO optimization platform` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `server.reload` | `False` |
| `agents.max_concurrent` | `3` |
| `agents.timeout_seconds` | `300` |
| `agents.retry_attempts` | `3` |
| `agents.retry_delay_seconds` | `5` |
| `agents.keyword_research.max_keywords` | `50` |
| `agents.keyword_research.min_search_volume` | `100` |
| `agents.keyword_research.max_difficulty` | `70` |
| `agents.keyword_research.default_country` | `us` |
| `agents.content_optimization.max_content_length` | `50000` |
| `agents.content_optimization.readability_target` | `grade_8` |
| `agents.content_optimization.keyword_density_min` | `0.5` |
| `agents.content_optimization.keyword_density_max` | `2.5` |
| `agents.technical_seo.max_pages_per_crawl` | `1000` |
| `agents.technical_seo.crawl_timeout_seconds` | `300` |
| `agents.technical_seo.check_core_web_vitals` | `True` |
| `agents.link_building.max_backlinks_per_domain` | `100` |
| `agents.link_building.min_domain_authority` | `20` |
| `agents.link_building.outreach_email_template` | `default` |
| `agents.seo_monitoring.check_interval_hours` | `24` |
| `agents.seo_monitoring.ranking_alert_threshold` | `5` |
| `agents.seo_monitoring.competitor_tracking` | `True` |
| `agents.performance_analytics.metrics_retention_days` | `365` |
| `agents.performance_analytics.dashboard_refresh_minutes` | `60` |
| `integrations.google_search_console.enabled` | `False` |
| `integrations.google_search_console.credentials_path` | `None` |
| `integrations.google_search_console.site_url` | `None` |
| `integrations.google_search_console.api_version` | `v1` |
| `integrations.semrush.enabled` | `False` |
| `integrations.semrush.api_key` | `None` |
| `integrations.semrush.base_url` | `https://api.semrush.com` |
| `integrations.semrush.rate_limit_per_second` | `1` |
| `integrations.ahrefs.enabled` | `False` |
| `integrations.ahrefs.api_key` | `None` |
| `integrations.ahrefs.base_url` | `https://apiv2.ahrefs.com` |
| `integrations.ahrefs.rate_limit_per_second` | `1` |
| `integrations.screaming_frog.enabled` | `False` |
| `integrations.screaming_frog.spider_path` | `None` |
| `integrations.screaming_frog.max_crawl_pages` | `500` |
| `cache.backend` | `memory` |
| `cache.ttl_seconds` | `3600` |
| `cache.max_size` | `1000` |
| `rate_limiting.enabled` | `True` |
| `rate_limiting.requests_per_minute` | `60` |
| `rate_limiting.burst_size` | `10` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `WORKERS` | `4` | Server |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LLM |
| `OPENAI_MODEL` | `gpt-4o` | LLM |
| `OPENAI_TEMPERATURE` | `0.1` | LLM |
| `OPENAI_MAX_TOKENS` | `4096` | LLM |
| `GOOGLE_SEARCH_CONSOLE_ENABLED` | `false` | Google Search Console |
| `GOOGLE_SEARCH_CONSOLE_CREDENTIALS_PATH` | `/path/to/credentials.json` | Google Search Console |
| `GOOGLE_SEARCH_CONSOLE_SITE_URL` | `https://example.com` | Google Search Console |
| `SEMRUSH_ENABLED` | `false` | SEMrush |
| `SEMRUSH_API_KEY` | `your-semrush-api-key` | SEMrush |
| `AHREFS_ENABLED` | `false` | Ahrefs |
| `AHREFS_API_KEY` | `your-ahrefs-api-key` | Ahrefs |
| `SCREAMING_FROG_ENABLED` | `false` | Screaming Frog |
| `SCREAMING_FROG_SPIDER_PATH` | `/path/to/ScreamingFrogSEOSpider` | Screaming Frog |
| `CACHE_BACKEND` | `memory` | Cache |
| `CACHE_TTL_SECONDS` | `3600` | Cache |
| `CACHE_MAX_SIZE` | `1000` | Cache |
| `RATE_LIMITING_ENABLED` | `true` | Rate Limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Rate Limiting |
| `RATE_LIMIT_BURST_SIZE` | `10` | Rate Limiting |
| `PROMETHEUS_ENABLED` | `true` | Monitoring |
| `PROMETHEUS_PORT` | `9090` | Monitoring |
| `MAX_CONCURRENT_AGENTS` | `3` | Agents |
| `AGENT_TIMEOUT_SECONDS` | `300` | Agents |
| `AGENT_RETRY_ATTEMPTS` | `3` | Agents |
| `AGENT_RETRY_DELAY_SECONDS` | `5` | Agents |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: SEO Optimizer
  version: 0.1.0
  description: AI-powered SEO optimization platform
  environment: development
  log_level: INFO
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: False
agents:
  max_concurrent: 3
  timeout_seconds: 300
  retry_attempts: 3
  retry_delay_seconds: 5
  keyword_research:
    max_keywords: 50
    min_search_volume: 100
    max_difficulty: 70
    default_country: us
  content_optimization:
    max_content_length: 50000
    readability_target: grade_8
    keyword_density_min: 0.5
    keyword_density_max: 2.5
  technical_seo:
    max_pages_per_crawl: 1000
    crawl_timeout_seconds: 300
    check_core_web_vitals: True
  link_building:
    max_backlinks_per_domain: 100
    min_domain_authority: 20
    outreach_email_template: default
  seo_monitoring:
    check_interval_hours: 24
    ranking_alert_threshold: 5
    competitor_tracking: True
  performance_analytics:
    metrics_retention_days: 365
    dashboard_refresh_minutes: 60
integrations:
  google_search_console:
    enabled: False
    credentials_path: None
    site_url: None
    api_version: v1
  semrush:
    enabled: False
    api_key: None
    base_url: https://api.semrush.com
    rate_limit_per_second: 1
  ahrefs:
    enabled: False
    api_key: None
    base_url: https://apiv2.ahrefs.com
    rate_limit_per_second: 1
  screaming_frog:
    enabled: False
    spider_path: None
    max_crawl_pages: 500
cache:
  backend: memory
  ttl_seconds: 3600
  max_size: 1000
rate_limiting:
  enabled: True
  requests_per_minute: 60
  burst_size: 10
```

---

## Example .env File

```bash
# Application
APP_ENVIRONMENT=development
LOG_LEVEL=INFO
SECRET_KEY=change-me-in-production

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# LLM
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4096

# Google Search Console
GOOGLE_SEARCH_CONSOLE_ENABLED=false
GOOGLE_SEARCH_CONSOLE_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_SEARCH_CONSOLE_SITE_URL=https://example.com

# SEMrush
SEMRUSH_ENABLED=false
SEMRUSH_API_KEY=your-semrush-api-key

# Ahrefs
AHREFS_ENABLED=false
AHREFS_API_KEY=your-ahrefs-api-key

# Screaming Frog
SCREAMING_FROG_ENABLED=false
SCREAMING_FROG_SPIDER_PATH=/path/to/ScreamingFrogSEOSpider

# Cache
CACHE_BACKEND=memory
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000

# Rate Limiting
RATE_LIMITING_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Agents
MAX_CONCURRENT_AGENTS=3
AGENT_TIMEOUT_SECONDS=300
AGENT_RETRY_ATTEMPTS=3
AGENT_RETRY_DELAY_SECONDS=5

```

---

## Agent Configuration

```yaml
agents:
  content_optimization:
    keyword_density_max: 2.5
    keyword_density_min: 0.5
    max_content_length: 50000
    readability_target: grade_8
  keyword_research:
    default_country: us
    max_difficulty: 70
    max_keywords: 50
    min_search_volume: 100
  link_building:
    max_backlinks_per_domain: 100
    min_domain_authority: 20
    outreach_email_template: default
  max_concurrent: 3
  performance_analytics:
    dashboard_refresh_minutes: 60
    metrics_retention_days: 365
  retry_attempts: 3
  retry_delay_seconds: 5
  seo_monitoring:
    check_interval_hours: 24
    competitor_tracking: true
    ranking_alert_threshold: 5
  technical_seo:
    check_core_web_vitals: true
    crawl_timeout_seconds: 300
    max_pages_per_crawl: 1000
  timeout_seconds: 300
```

---

## Integration Settings

```yaml
integrations:
  ahrefs:
    api_key: null
    base_url: https://apiv2.ahrefs.com
    enabled: false
    rate_limit_per_second: 1
  google_search_console:
    api_version: v1
    credentials_path: null
    enabled: false
    site_url: null
  screaming_frog:
    enabled: false
    max_crawl_pages: 500
    spider_path: null
  semrush:
    api_key: null
    base_url: https://api.semrush.com
    enabled: false
    rate_limit_per_second: 1
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
  backend: memory
  max_size: 1000
  ttl_seconds: 3600
```

### rate_limiting

```yaml
rate_limiting:
  burst_size: 10
  enabled: true
  requests_per_minute: 60
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/seo-optimizer
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

*Generated for `seo-optimizer` — GRC_Claw Configuration Guide*

# Content Generator — Configuration Guide

> Multi-agent AI content generation pipeline supporting blog posts, social media, ad copy, and more with multi-language support.

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

The **content-generator** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/content-generator/
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
| `app.name` | `content-generator` |
| `app.version` | `0.1.0` |
| `app.description` | `Multi-agent AI content generation pipeline` |
| `app.log_level` | `info` |
| `app.workers` | `4` |
| `models.openai.default` | `gpt-4-turbo-preview` |
| `models.openai.fallback` | `gpt-3.5-turbo` |
| `models.openai.max_tokens` | `4096` |
| `models.openai.temperature` | `0.7` |
| `models.anthropic.default` | `claude-sonnet-4-20250514` |
| `models.anthropic.fallback` | `claude-haiku-4-20250514` |
| `models.anthropic.max_tokens` | `4096` |
| `models.anthropic.temperature` | `0.7` |
| `agents.researcher.model` | `claude-sonnet-4-20250514` |
| `agents.researcher.max_results` | `10` |
| `agents.researcher.search_depth` | `deep` |
| `agents.strategist.model` | `claude-sonnet-4-20250514` |
| `agents.strategist.max_tokens` | `2048` |
| `agents.writer.model` | `gpt-4-turbo-preview` |
| `agents.writer.max_tokens` | `4096` |
| `agents.writer.temperature` | `0.7` |
| `agents.seo_editor.model` | `gpt-4-turbo-preview` |
| `agents.seo_editor.max_tokens` | `2048` |
| `agents.seo_editor.temperature` | `0.3` |
| `agents.atomizer.model` | `claude-sonnet-4-20250514` |
| `agents.atomizer.max_tokens` | `2048` |
| `languages.supported` | `{'code': 'en', 'name': 'English', 'direction': 'ltr'}, {'code': 'ar', 'name': 'Arabic (MSA)', 'direction': 'rtl'}, {'code': 'ar-EG', 'name': 'Arabic (Egyptian)', 'direction': 'rtl'}, {'code': 'ar-SA', 'name': 'Arabic (Gulf)', 'direction': 'rtl'}, {'code': 'ar-LB', 'name': 'Arabic (Levantine)', 'direction': 'rtl'}` |
| `rate_limiting.requests_per_minute` | `60` |
| `rate_limiting.burst_size` | `10` |
| `caching.enabled` | `True` |
| `caching.ttl_seconds` | `3600` |
| `caching.backend` | `redis` |
| `monitoring.metrics_enabled` | `True` |
| `monitoring.tracing_enabled` | `False` |
| `monitoring.health_check_interval` | `30` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_NAME` | `content-generator` | General |
| `APP_ENV` | `development` | General |
| `LOG_LEVEL` | `info` | General |
| `WORKERS` | `4` | General |
| `OPENAI_API_KEY` | `sk-your-openai-key` | General |
| `OPENAI_MODEL` | `gpt-4-turbo-preview` | General |
| `OPENAI_MAX_TOKENS` | `4096` | General |
| `OPENAI_TEMPERATURE` | `0.7` | General |
| `ANTHROPIC_API_KEY` | `sk-ant-your-anthropic-key` | General |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | General |
| `ANTHROPIC_MAX_TOKENS` | `4096` | General |
| `ANTHROPIC_TEMPERATURE` | `0.7` | General |
| `SERPAPI_API_KEY` | `your-serpapi-key` | General |
| `REDIS_URL` | `redis://localhost:6379/0` | General |
| `CACHE_TTL` | `3600` | General |
| `METRICS_ENABLED` | `true` | General |
| `TRACING_ENABLED` | `false` | General |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: content-generator
  version: 0.1.0
  description: Multi-agent AI content generation pipeline
  log_level: info
  workers: 4
models:
  openai:
    default: gpt-4-turbo-preview
    fallback: gpt-3.5-turbo
    max_tokens: 4096
    temperature: 0.7
  anthropic:
    default: claude-sonnet-4-20250514
    fallback: claude-haiku-4-20250514
    max_tokens: 4096
    temperature: 0.7
agents:
  researcher:
    model: claude-sonnet-4-20250514
    max_results: 10
    search_depth: deep
  strategist:
    model: claude-sonnet-4-20250514
    max_tokens: 2048
  writer:
    model: gpt-4-turbo-preview
    max_tokens: 4096
    temperature: 0.7
  seo_editor:
    model: gpt-4-turbo-preview
    max_tokens: 2048
    temperature: 0.3
  atomizer:
    model: claude-sonnet-4-20250514
    max_tokens: 2048
languages:
  supported:
    -
      code: en
      name: English
      direction: ltr
    -
      code: ar
      name: Arabic (MSA)
      direction: rtl
    -
      code: ar-EG
      name: Arabic (Egyptian)
      direction: rtl
    -
      code: ar-SA
      name: Arabic (Gulf)
      direction: rtl
    -
      code: ar-LB
      name: Arabic (Levantine)
      direction: rtl
rate_limiting:
  requests_per_minute: 60
  burst_size: 10
caching:
  enabled: True
  ttl_seconds: 3600
  backend: redis
monitoring:
  metrics_enabled: True
  tracing_enabled: False
  health_check_interval: 30
```

---

## Example .env File

```bash
# ── App ──────────────────────────────────────────────
APP_NAME=content-generator
APP_ENV=development
LOG_LEVEL=info
WORKERS=4

# ── OpenAI ───────────────────────────────────────────
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7

# ── Anthropic ────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ANTHROPIC_MODEL=claude-sonnet-4-20250514
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TEMPERATURE=0.7

# ── SerpAPI ──────────────────────────────────────────
SERPAPI_API_KEY=your-serpapi-key

# ── Redis (optional) ─────────────────────────────────
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# ── Monitoring ───────────────────────────────────────
METRICS_ENABLED=true
TRACING_ENABLED=false

```

---

## Agent Configuration

```yaml
agents:
  atomizer:
    max_tokens: 2048
    model: claude-sonnet-4-20250514
  researcher:
    max_results: 10
    model: claude-sonnet-4-20250514
    search_depth: deep
  seo_editor:
    max_tokens: 2048
    model: gpt-4-turbo-preview
    temperature: 0.3
  strategist:
    max_tokens: 2048
    model: claude-sonnet-4-20250514
  writer:
    max_tokens: 4096
    model: gpt-4-turbo-preview
    temperature: 0.7
```

---

## Integration Settings

No integration configuration found.

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

### monitoring

```yaml
monitoring:
  health_check_interval: 30
  metrics_enabled: true
  tracing_enabled: false
```

---

## Rate Limiting & Caching

### rate_limiting

```yaml
rate_limiting:
  burst_size: 10
  requests_per_minute: 60
```

### caching

```yaml
caching:
  backend: redis
  enabled: true
  ttl_seconds: 3600
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/content-generator
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

*Generated for `content-generator` — GRC_Claw Configuration Guide*

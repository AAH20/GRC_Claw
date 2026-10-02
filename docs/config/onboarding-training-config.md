# Onboarding Training — Configuration Guide

> Onboarding and training platform with content creation, LMS delivery, assessment, and performance tracking.

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

The **onboarding-training** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/onboarding-training/
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
| `app_env` | `production` |
| `log_level` | `info` |
| `debug` | `False` |
| `host` | `0.0.0.0` |
| `port` | `8000` |
| `workers` | `2` |
| `request_timeout_seconds` | `60` |
| `cors_origins` | `https://grc.local, https://onboarding.grc.local` |
| `openai_api_key` | `${OPENAI_API_KEY}` |
| `openai_model` | `gpt-4o-mini` |
| `model_temperature` | `0.2` |
| `model_max_tokens` | `4096` |
| `deepagents_max_iterations` | `25` |
| `content_creation.enabled` | `True` |
| `content_creation.default_language` | `en` |
| `content_creation.max_lessons_per_course` | `30` |
| `content_creation.max_quiz_questions_per_lesson` | `10` |
| `delivery.enabled` | `True` |
| `delivery.default_lms` | `canvas` |
| `delivery.publish_draft` | `False` |
| `delivery.retry_attempts` | `3` |
| `assessment.enabled` | `True` |
| `assessment.mastery_threshold` | `0.75` |
| `assessment.passing_score` | `0.7` |
| `assessment.max_grading_retries` | `3` |
| `optimization.enabled` | `True` |
| `optimization.min_feedback_samples` | `20` |
| `optimization.auto_apply` | `False` |
| `performance_analytics.enabled` | `True` |
| `performance_analytics.default_lookback_days` | `30` |
| `performance_analytics.alert_completion_threshold` | `0.4` |
| `canvas.enabled` | `True` |
| `canvas.base_url` | `https://canvas.instructure.com/api/v1` |
| `canvas.timeout_seconds` | `30` |
| `canvas.page_size` | `100` |
| `moodle.enabled` | `True` |
| `moodle.base_url` | `https://moodle.example.com` |
| `moodle.webservice_endpoint` | `/webservice/rest/server.php` |
| `moodle.timeout_seconds` | `30` |
| `scorm.enabled` | `True` |
| `scorm.version` | `2004` |
| `scorm.strict_mode` | `False` |
| `prometheus_enabled` | `True` |
| `metrics_path` | `/metrics` |
| `health_path` | `/health` |
| `structured_logging` | `True` |
| `sentry_dsn` | `${SENTRY_DSN:-null}` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `production` | --- Application --- |
| `LOG_LEVEL` | `info` | --- Application --- |
| `DEBUG` | `false` | --- Application --- |
| `HOST` | `0.0.0.0` | --- Server --- |
| `PORT` | `8000` | --- Server --- |
| `WORKERS` | `2` | --- Server --- |
| `REQUEST_TIMEOUT_SECONDS` | `60` | --- Server --- |
| `OPENAI_API_KEY` | `sk-...` | --- Models --- |
| `OPENAI_MODEL` | `gpt-4o-mini` | --- Models --- |
| `MODEL_TEMPERATURE` | `0.2` | --- Models --- |
| `MODEL_MAX_TOKENS` | `4096` | --- Models --- |
| `DEEPAGENTS_MAX_ITERATIONS` | `25` | --- Models --- |
| `CONTENT_CREATION_ENABLED` | `true` | --- Agents --- |
| `DELIVERY_ENABLED` | `true` | --- Agents --- |
| `ASSESSMENT_ENABLED` | `true` | --- Agents --- |
| `OPTIMIZATION_ENABLED` | `true` | --- Agents --- |
| `PERFORMANCE_ANALYTICS_ENABLED` | `true` | --- Agents --- |
| `MASTERY_THRESHOLD` | `0.75` | --- Assessment thresholds --- |
| `PASSING_SCORE` | `0.70` | --- Assessment thresholds --- |
| `MIN_FEEDBACK_SAMPLES` | `20` | --- Optimization --- |
| `OPTIMIZATION_AUTO_APPLY` | `false` | --- Optimization --- |
| `DEFAULT_LOOKBACK_DAYS` | `30` | --- Performance Analytics --- |
| `ALERT_COMPLETION_THRESHOLD` | `0.40` | --- Performance Analytics --- |
| `CANVAS_ENABLED` | `true` | --- Canvas --- |
| `CANVAS_BASE_URL` | `https://canvas.instructure.com/api/v1` | --- Canvas --- |
| `CANVAS_API_TOKEN` | `replace-with-real-token` | --- Canvas --- |
| `MOODLE_ENABLED` | `true` | --- Moodle --- |
| `MOODLE_BASE_URL` | `https://moodle.example.com` | --- Moodle --- |
| `MOODLE_WS_TOKEN` | `replace-with-real-token` | --- Moodle --- |
| `SCORM_ENABLED` | `true` | --- SCORM --- |
| `SCORM_VERSION` | `2004` | --- SCORM --- |
| `SCORM_STRICT_MODE` | `false` | --- SCORM --- |
| `SCORM_PUBLISHER` | `GRC Marketing` | --- SCORM --- |
| `PROMETHEUS_ENABLED` | `true` | --- Observability --- |
| `SENTRY_DSN` | `` | --- Observability --- |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app_env: production
log_level: info
debug: False
host: 0.0.0.0
port: 8000
workers: 2
request_timeout_seconds: 60
cors_origins:
  - https://grc.local
  - https://onboarding.grc.local
openai_api_key: ${OPENAI_API_KEY}
openai_model: gpt-4o-mini
model_temperature: 0.2
model_max_tokens: 4096
deepagents_max_iterations: 25
content_creation:
  enabled: True
  default_language: en
  max_lessons_per_course: 30
  max_quiz_questions_per_lesson: 10
delivery:
  enabled: True
  default_lms: canvas
  publish_draft: False
  retry_attempts: 3
assessment:
  enabled: True
  mastery_threshold: 0.75
  passing_score: 0.7
  max_grading_retries: 3
optimization:
  enabled: True
  min_feedback_samples: 20
  auto_apply: False
performance_analytics:
  enabled: True
  default_lookback_days: 30
  alert_completion_threshold: 0.4
canvas:
  enabled: True
  base_url: https://canvas.instructure.com/api/v1
  timeout_seconds: 30
  page_size: 100
moodle:
  enabled: True
  base_url: https://moodle.example.com
  webservice_endpoint: /webservice/rest/server.php
  timeout_seconds: 30
scorm:
  enabled: True
  version: 2004
  strict_mode: False
prometheus_enabled: True
metrics_path: /metrics
health_path: /health
structured_logging: True
sentry_dsn: ${SENTRY_DSN:-null}
```

---

## Example .env File

```bash
# Copy to .env and fill in values. All values are read by pydantic-settings.

# --- Application ---
APP_ENV=production
LOG_LEVEL=info
DEBUG=false

# --- Server ---
HOST=0.0.0.0
PORT=8000
WORKERS=2
REQUEST_TIMEOUT_SECONDS=60

# --- Models ---
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
MODEL_TEMPERATURE=0.2
MODEL_MAX_TOKENS=4096
DEEPAGENTS_MAX_ITERATIONS=25

# --- Agents ---
CONTENT_CREATION_ENABLED=true
DELIVERY_ENABLED=true
ASSESSMENT_ENABLED=true
OPTIMIZATION_ENABLED=true
PERFORMANCE_ANALYTICS_ENABLED=true

# --- Assessment thresholds ---
MASTERY_THRESHOLD=0.75
PASSING_SCORE=0.70

# --- Optimization ---
MIN_FEEDBACK_SAMPLES=20
OPTIMIZATION_AUTO_APPLY=false

# --- Performance Analytics ---
DEFAULT_LOOKBACK_DAYS=30
ALERT_COMPLETION_THRESHOLD=0.40

# --- Canvas ---
CANVAS_ENABLED=true
CANVAS_BASE_URL=https://canvas.instructure.com/api/v1
CANVAS_API_TOKEN=replace-with-real-token

# --- Moodle ---
MOODLE_ENABLED=true
MOODLE_BASE_URL=https://moodle.example.com
MOODLE_WS_TOKEN=replace-with-real-token

# --- SCORM ---
SCORM_ENABLED=true
SCORM_VERSION=2004
SCORM_STRICT_MODE=false
SCORM_PUBLISHER=GRC Marketing

# --- Observability ---
PROMETHEUS_ENABLED=true
SENTRY_DSN=

```

---

## Agent Configuration

No agent-specific configuration found.

---

## Integration Settings

No integration configuration found.

---

## Security Configuration

### openai_api_key

```yaml
openai_api_key: ${OPENAI_API_KEY}
```

### model_max_tokens

```yaml
model_max_tokens: 4096
```

---

## Monitoring & Observability

### prometheus_enabled

```yaml
prometheus_enabled: true
```

### metrics_path

```yaml
metrics_path: /metrics
```

### health_path

```yaml
health_path: /health
```

### sentry_dsn

```yaml
sentry_dsn: ${SENTRY_DSN:-null}
```

---

## Rate Limiting & Caching

No explicit rate limiting or caching configuration found.

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/onboarding-training
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

*Generated for `onboarding-training` — GRC_Claw Configuration Guide*

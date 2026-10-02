# Conversational Marketing — Configuration Guide

> Conversational marketing platform for WhatsApp, Facebook Messenger, and Slack with intent detection and response generation.

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

The **conversational-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/conversational-marketing/
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
| `app.name` | `conversational-marketing` |
| `app.version` | `0.1.0` |
| `app.env` | `dev` |
| `app.log_level` | `INFO` |
| `app.debug` | `False` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `1` |
| `server.reload` | `False` |
| `llm.provider` | `openai` |
| `llm.model` | `gpt-4o-mini` |
| `llm.temperature` | `0.7` |
| `llm.max_tokens` | `1024` |
| `llm.timeout` | `30` |
| `agents.intent_detection.confidence_threshold` | `0.7` |
| `agents.intent_detection.fallback_intent` | `general_inquiry` |
| `agents.intent_detection.supported_intents` | `purchase_intent, product_inquiry, support_request, complaint, pricing_question, demo_request, general_inquiry, greeting, farewell` |
| `agents.response_generation.max_response_length` | `500` |
| `agents.response_generation.tone` | `professional_friendly` |
| `agents.response_generation.include_cta` | `True` |
| `agents.response_generation.language` | `en` |
| `agents.handoff.enabled` | `True` |
| `agents.handoff.confidence_threshold` | `0.6` |
| `agents.handoff.max_agent_turns` | `10` |
| `agents.handoff.human_handoff_timeout` | `300` |
| `agents.handoff.escalation_rules` | `{'intent': 'complaint', 'priority': 'high', 'auto_handoff': True}, {'intent': 'purchase_intent', 'priority': 'medium', 'auto_handoff': False}` |
| `agents.optimization.enabled` | `True` |
| `agents.optimization.analysis_interval` | `3600` |
| `agents.optimization.min_conversations_for_analysis` | `10` |
| `agents.optimization.suggestion_threshold` | `0.8` |
| `agents.analytics.enabled` | `True` |
| `agents.analytics.retention_days` | `90` |
| `agents.analytics.realtime_metrics` | `True` |
| `agents.analytics.export_format` | `json` |
| `integrations.whatsapp.enabled` | `False` |
| `integrations.whatsapp.verify_token` | `` |
| `integrations.whatsapp.phone_number_id` | `` |
| `integrations.whatsapp.webhook_path` | `/webhooks/whatsapp` |
| `integrations.facebook_messenger.enabled` | `False` |
| `integrations.facebook_messenger.page_id` | `` |
| `integrations.facebook_messenger.app_secret` | `` |
| `integrations.facebook_messenger.webhook_path` | `/webhooks/facebook` |
| `integrations.slack.enabled` | `False` |
| `integrations.slack.signing_secret` | `` |
| `integrations.slack.webhook_path` | `/webhooks/slack` |
| `conversation.max_history` | `20` |
| `conversation.session_timeout` | `1800` |
| `conversation.context_window` | `4000` |
| `rate_limiting.enabled` | `True` |
| `rate_limiting.requests_per_minute` | `60` |
| `rate_limiting.burst_size` | `10` |
| `monitoring.prometheus_enabled` | `True` |
| `monitoring.metrics_port` | `9090` |
| `monitoring.health_check_interval` | `30` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `dev` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `DEBUG` | `true` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LLM Configuration |
| `LLM_PROVIDER` | `openai` | LLM Configuration |
| `LLM_MODEL` | `gpt-4o-mini` | LLM Configuration |
| `LLM_TEMPERATURE` | `0.7` | LLM Configuration |
| `LLM_MAX_TOKENS` | `1024` | LLM Configuration |
| `WHATSAPP_TOKEN` | `your-whatsapp-token` | WhatsApp Business API |
| `WHATSAPP_PHONE_NUMBER_ID` | `your-phone-number-id` | WhatsApp Business API |
| `WHATSAPP_VERIFY_TOKEN` | `your-verify-token` | WhatsApp Business API |
| `FACEBOOK_PAGE_TOKEN` | `your-facebook-page-token` | Facebook Messenger |
| `FACEBOOK_APP_SECRET` | `your-facebook-app-secret` | Facebook Messenger |
| `FACEBOOK_VERIFY_TOKEN` | `your-facebook-verify-token` | Facebook Messenger |
| `SLACK_BOT_TOKEN` | `xoxb-your-slack-bot-token` | Slack |
| `SLACK_SIGNING_SECRET` | `your-slack-signing-secret` | Slack |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (for session storage) |
| `PROMETHEUS_ENABLED` | `true` | Monitoring |
| `METRICS_PORT` | `9090` | Monitoring |
| `SECRET_KEY` | `your-secret-key-change-in-production` | Security |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8080` | Security |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: conversational-marketing
  version: 0.1.0
  env: dev
  log_level: INFO
  debug: False
server:
  host: 0.0.0.0
  port: 8000
  workers: 1
  reload: False
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 1024
  timeout: 30
agents:
  intent_detection:
    confidence_threshold: 0.7
    fallback_intent: general_inquiry
    supported_intents:
      - purchase_intent
      - product_inquiry
      - support_request
      - complaint
      - pricing_question
      - demo_request
      - general_inquiry
      - greeting
      - farewell
  response_generation:
    max_response_length: 500
    tone: professional_friendly
    include_cta: True
    language: en
  handoff:
    enabled: True
    confidence_threshold: 0.6
    max_agent_turns: 10
    human_handoff_timeout: 300
    escalation_rules:
      -
        intent: complaint
        priority: high
        auto_handoff: True
      -
        intent: purchase_intent
        priority: medium
        auto_handoff: False
  optimization:
    enabled: True
    analysis_interval: 3600
    min_conversations_for_analysis: 10
    suggestion_threshold: 0.8
  analytics:
    enabled: True
    retention_days: 90
    realtime_metrics: True
    export_format: json
integrations:
  whatsapp:
    enabled: False
    verify_token: 
    phone_number_id: 
    webhook_path: /webhooks/whatsapp
  facebook_messenger:
    enabled: False
    page_id: 
    app_secret: 
    webhook_path: /webhooks/facebook
  slack:
    enabled: False
    signing_secret: 
    webhook_path: /webhooks/slack
conversation:
  max_history: 20
  session_timeout: 1800
  context_window: 4000
rate_limiting:
  enabled: True
  requests_per_minute: 60
  burst_size: 10
monitoring:
  prometheus_enabled: True
  metrics_port: 9090
  health_check_interval: 30
```

---

## Example .env File

```bash
# Application
APP_ENV=dev
LOG_LEVEL=INFO
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# LLM Configuration
OPENAI_API_KEY=sk-your-openai-api-key
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1024

# WhatsApp Business API
WHATSAPP_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_VERIFY_TOKEN=your-verify-token

# Facebook Messenger
FACEBOOK_PAGE_TOKEN=your-facebook-page-token
FACEBOOK_APP_SECRET=your-facebook-app-secret
FACEBOOK_VERIFY_TOKEN=your-facebook-verify-token

# Slack
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# Redis (for session storage)
REDIS_URL=redis://localhost:6379/0

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

# Security
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

```

---

## Agent Configuration

```yaml
agents:
  analytics:
    enabled: true
    export_format: json
    realtime_metrics: true
    retention_days: 90
  handoff:
    confidence_threshold: 0.6
    enabled: true
    escalation_rules:
    - auto_handoff: true
      intent: complaint
      priority: high
    - auto_handoff: false
      intent: purchase_intent
      priority: medium
    human_handoff_timeout: 300
    max_agent_turns: 10
  intent_detection:
    confidence_threshold: 0.7
    fallback_intent: general_inquiry
    supported_intents:
    - purchase_intent
    - product_inquiry
    - support_request
    - complaint
    - pricing_question
    - demo_request
    - general_inquiry
    - greeting
    - farewell
  optimization:
    analysis_interval: 3600
    enabled: true
    min_conversations_for_analysis: 10
    suggestion_threshold: 0.8
  response_generation:
    include_cta: true
    language: en
    max_response_length: 500
    tone: professional_friendly
```

---

## Integration Settings

```yaml
integrations:
  facebook_messenger:
    app_secret: ''
    enabled: false
    page_id: ''
    webhook_path: /webhooks/facebook
  slack:
    enabled: false
    signing_secret: ''
    webhook_path: /webhooks/slack
  whatsapp:
    enabled: false
    phone_number_id: ''
    verify_token: ''
    webhook_path: /webhooks/whatsapp
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
cd ~/GRC_Claw/projects/conversational-marketing
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

*Generated for `conversational-marketing` — GRC_Claw Configuration Guide*

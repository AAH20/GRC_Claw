# Cross Project Orchestrator — Configuration Guide

> Cross-project orchestration platform for managing dependencies, resources, and health across all GRC_Claw projects.

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

The **cross-project-orchestrator** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/cross-project-orchestrator/
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
| `orchestrator.environment` | `development` |
| `orchestrator.port` | `8080` |
| `orchestrator.log_level` | `INFO` |
| `orchestrator.workers` | `4` |
| `agents.project_discovery.enabled` | `True` |
| `agents.project_discovery.scan_interval_seconds` | `300` |
| `agents.project_discovery.project_roots` | `/projects` |
| `agents.project_discovery.exclude_patterns` | `*.tmp, *.cache, __pycache__` |
| `agents.dependency_resolution.enabled` | `True` |
| `agents.dependency_resolution.max_depth` | `10` |
| `agents.dependency_resolution.cache_ttl_seconds` | `3600` |
| `agents.dependency_resolution.conflict_strategy` | `highest_version` |
| `agents.resource_allocation.enabled` | `True` |
| `agents.resource_allocation.allocation_strategy` | `weighted_fair` |
| `agents.resource_allocation.rebalance_interval_seconds` | `600` |
| `agents.resource_allocation.overcommit_ratio` | `1.2` |
| `agents.health_monitoring.enabled` | `True` |
| `agents.health_monitoring.check_interval_seconds` | `60` |
| `agents.health_monitoring.alert_threshold.cpu_percent` | `80` |
| `agents.health_monitoring.alert_threshold.memory_percent` | `85` |
| `agents.health_monitoring.alert_threshold.error_rate` | `0.05` |
| `agents.health_monitoring.retention_days` | `30` |
| `agents.cost_optimization.enabled` | `True` |
| `agents.cost_optimization.analysis_interval_seconds` | `3600` |
| `agents.cost_optimization.budget_alert_threshold` | `0.8` |
| `agents.cost_optimization.recommendations` | `rightsizing, spot_instances, reserved_capacity` |
| `integrations.kubernetes.enabled` | `True` |
| `integrations.kubernetes.namespace` | `default` |
| `integrations.kubernetes.in_cluster` | `True` |
| `integrations.kubernetes.kubeconfig_path` | `None` |
| `integrations.terraform.enabled` | `True` |
| `integrations.terraform.state_path` | `./tfstate` |
| `integrations.terraform.workspace` | `default` |
| `integrations.terraform.auto_approve` | `False` |
| `integrations.prometheus.enabled` | `True` |
| `integrations.prometheus.url` | `http://localhost:9090` |
| `integrations.prometheus.scrape_interval` | `15` |
| `integrations.prometheus.timeout` | `10` |
| `api.rate_limit.enabled` | `True` |
| `api.rate_limit.requests_per_minute` | `100` |
| `api.cors.enabled` | `True` |
| `api.cors.allow_origins` | `*` |
| `api.auth.enabled` | `False` |
| `api.auth.type` | `api_key` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ORCHESTRATOR_ENV` | `development` | Copy this file to .env and fill in your values |
| `ORCHESTRATOR_PORT` | `8080` | Copy this file to .env and fill in your values |
| `ORCHESTRATOR_LOG_LEVEL` | `INFO` | Copy this file to .env and fill in your values |
| `ORCHESTRATOR_WORKERS` | `4` | Copy this file to .env and fill in your values |
| `KUBERNETES_ENABLED` | `true` | Copy this file to .env and fill in your values |
| `KUBERNETES_NAMESPACE` | `default` | Copy this file to .env and fill in your values |
| `KUBERNETES_IN_CLUSTER` | `true` | Copy this file to .env and fill in your values |
| `KUBERNETES_KUBECONFIG_PATH` | `` | Copy this file to .env and fill in your values |
| `TERRAFORM_ENABLED` | `true` | Copy this file to .env and fill in your values |
| `TERRAFORM_STATE_PATH` | `./tfstate` | Copy this file to .env and fill in your values |
| `TERRAFORM_WORKSPACE` | `default` | Copy this file to .env and fill in your values |
| `TERRAFORM_AUTO_APPROVE` | `false` | Copy this file to .env and fill in your values |
| `PROMETHEUS_ENABLED` | `true` | Copy this file to .env and fill in your values |
| `PROMETHEUS_URL` | `http://localhost:9090` | Copy this file to .env and fill in your values |
| `PROMETHEUS_SCRAPE_INTERVAL` | `15` | Copy this file to .env and fill in your values |
| `PROMETHEUS_TIMEOUT` | `10` | Copy this file to .env and fill in your values |
| `API_RATE_LIMIT_ENABLED` | `true` | Copy this file to .env and fill in your values |
| `API_RATE_LIMIT_RPM` | `100` | Copy this file to .env and fill in your values |
| `API_CORS_ENABLED` | `true` | Copy this file to .env and fill in your values |
| `API_CORS_ORIGINS` | `*` | Copy this file to .env and fill in your values |
| `API_AUTH_ENABLED` | `false` | Copy this file to .env and fill in your values |
| `API_AUTH_TYPE` | `api_key` | Copy this file to .env and fill in your values |
| `API_AUTH_KEY` | `` | Copy this file to .env and fill in your values |
| `AGENT_DISCOVERY_SCAN_INTERVAL` | `300` | Copy this file to .env and fill in your values |
| `AGENT_DISCOVERY_PROJECT_ROOTS` | `/projects` | Copy this file to .env and fill in your values |
| `AGENT_DEPENDENCY_MAX_DEPTH` | `10` | Copy this file to .env and fill in your values |
| `AGENT_DEPENDENCY_CACHE_TTL` | `3600` | Copy this file to .env and fill in your values |
| `AGENT_RESOURCE_REBALANCE_INTERVAL` | `600` | Copy this file to .env and fill in your values |
| `AGENT_HEALTH_CHECK_INTERVAL` | `60` | Copy this file to .env and fill in your values |
| `AGENT_COST_ANALYSIS_INTERVAL` | `3600` | Copy this file to .env and fill in your values |
| `OTEL_ENABLED` | `false` | Copy this file to .env and fill in your values |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | Copy this file to .env and fill in your values |
| `OTEL_SERVICE_NAME` | `cross-project-orchestrator` | Copy this file to .env and fill in your values |
| `STRUCTLOG_PRETTY` | `false` | Copy this file to .env and fill in your values |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
orchestrator:
  environment: development
  port: 8080
  log_level: INFO
  workers: 4
agents:
  project_discovery:
    enabled: True
    scan_interval_seconds: 300
    project_roots:
      - /projects
    exclude_patterns:
      - *.tmp
      - *.cache
      - __pycache__
  dependency_resolution:
    enabled: True
    max_depth: 10
    cache_ttl_seconds: 3600
    conflict_strategy: highest_version
  resource_allocation:
    enabled: True
    allocation_strategy: weighted_fair
    rebalance_interval_seconds: 600
    overcommit_ratio: 1.2
  health_monitoring:
    enabled: True
    check_interval_seconds: 60
    alert_threshold:
      cpu_percent: 80
      memory_percent: 85
      error_rate: 0.05
    retention_days: 30
  cost_optimization:
    enabled: True
    analysis_interval_seconds: 3600
    budget_alert_threshold: 0.8
    recommendations:
      - rightsizing
      - spot_instances
      - reserved_capacity
integrations:
  kubernetes:
    enabled: True
    namespace: default
    in_cluster: True
    kubeconfig_path: None
  terraform:
    enabled: True
    state_path: ./tfstate
    workspace: default
    auto_approve: False
  prometheus:
    enabled: True
    url: http://localhost:9090
    scrape_interval: 15
    timeout: 10
api:
  rate_limit:
    enabled: True
    requests_per_minute: 100
  cors:
    enabled: True
    allow_origins:
      - *
  auth:
    enabled: False
    type: api_key
```

---

## Example .env File

```bash
# Cross-Project Orchestrator Environment Configuration
# Copy this file to .env and fill in your values

# ─── Core ───────────────────────────────────────────────
ORCHESTRATOR_ENV=development
ORCHESTRATOR_PORT=8080
ORCHESTRATOR_LOG_LEVEL=INFO
ORCHESTRATOR_WORKERS=4

# ─── Kubernetes ─────────────────────────────────────────
KUBERNETES_ENABLED=true
KUBERNETES_NAMESPACE=default
KUBERNETES_IN_CLUSTER=true
KUBERNETES_KUBECONFIG_PATH=

# ─── Terraform ──────────────────────────────────────────
TERRAFORM_ENABLED=true
TERRAFORM_STATE_PATH=./tfstate
TERRAFORM_WORKSPACE=default
TERRAFORM_AUTO_APPROVE=false

# ─── Prometheus ─────────────────────────────────────────
PROMETHEUS_ENABLED=true
PROMETHEUS_URL=http://localhost:9090
PROMETHEUS_SCRAPE_INTERVAL=15
PROMETHEUS_TIMEOUT=10

# ─── API Security ───────────────────────────────────────
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_RPM=100
API_CORS_ENABLED=true
API_CORS_ORIGINS=*
API_AUTH_ENABLED=false
API_AUTH_TYPE=api_key
API_AUTH_KEY=

# ─── Agent Tuning ───────────────────────────────────────
AGENT_DISCOVERY_SCAN_INTERVAL=300
AGENT_DISCOVERY_PROJECT_ROOTS=/projects
AGENT_DEPENDENCY_MAX_DEPTH=10
AGENT_DEPENDENCY_CACHE_TTL=3600
AGENT_RESOURCE_REBALANCE_INTERVAL=600
AGENT_HEALTH_CHECK_INTERVAL=60
AGENT_COST_ANALYSIS_INTERVAL=3600

# ─── Observability ──────────────────────────────────────
OTEL_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=cross-project-orchestrator
STRUCTLOG_PRETTY=false

```

---

## Agent Configuration

```yaml
agents:
  cost_optimization:
    analysis_interval_seconds: 3600
    budget_alert_threshold: 0.8
    enabled: true
    recommendations:
    - rightsizing
    - spot_instances
    - reserved_capacity
  dependency_resolution:
    cache_ttl_seconds: 3600
    conflict_strategy: highest_version
    enabled: true
    max_depth: 10
  health_monitoring:
    alert_threshold:
      cpu_percent: 80
      error_rate: 0.05
      memory_percent: 85
    check_interval_seconds: 60
    enabled: true
    retention_days: 30
  project_discovery:
    enabled: true
    exclude_patterns:
    - '*.tmp'
    - '*.cache'
    - __pycache__
    project_roots:
    - /projects
    scan_interval_seconds: 300
  resource_allocation:
    allocation_strategy: weighted_fair
    enabled: true
    overcommit_ratio: 1.2
    rebalance_interval_seconds: 600
```

---

## Integration Settings

```yaml
integrations:
  kubernetes:
    enabled: true
    in_cluster: true
    kubeconfig_path: null
    namespace: default
  prometheus:
    enabled: true
    scrape_interval: 15
    timeout: 10
    url: http://localhost:9090
  terraform:
    auto_approve: false
    enabled: true
    state_path: ./tfstate
    workspace: default
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

No explicit monitoring configuration found.

---

## Rate Limiting & Caching

No explicit rate limiting or caching configuration found.

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/cross-project-orchestrator
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

*Generated for `cross-project-orchestrator` — GRC_Claw Configuration Guide*

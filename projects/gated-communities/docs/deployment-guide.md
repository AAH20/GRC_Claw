# Deployment Guide

## Gated Communities — Deployment Guide

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Docker Compose (Development)](#docker-compose-development)
- [Docker Compose (Production)](#docker-compose-production)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Migrations](#database-migrations)
- [Health Checks](#health-checks)
- [Monitoring](#monitoring)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

---

## Overview

Gated Communities can be deployed using Docker, Docker Compose, or Kubernetes. Choose the deployment method that best fits your infrastructure.

```mermaid
graph LR
    A[Source Code] --> B[Docker Image]
    B --> C[Docker Compose<br/>Development]
    B --> D[Kubernetes<br/>Production]
    B --> E[Cloud Run<br/>Serverless]
```

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.0+ | Multi-container orchestration |
| kubectl | 1.28+ | Kubernetes CLI |
| Helm | 3.0+ | Kubernetes package manager (optional) |

### Required Services

| Service | Version | Purpose |
|---------|---------|---------|
| PostgreSQL | 15+ | Primary database |
| Redis | 7+ | Cache and session store |
| OpenAI API | — | LLM integration |

---

## Docker Deployment

### Building the Image

```bash
# Build the Docker image
docker build -t gated-communities:latest .

# Build with specific version tag
docker build -t gated-communities:1.0.0 .
```

### Running the Container

```bash
# Run with environment variables
docker run -d \
  --name gated-communities \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/gated_communities \
  -e REDIS_URL=redis://host:6379/0 \
  -e LLM_API_KEY=sk-... \
  -e LOG_LEVEL=INFO \
  -e ENVIRONMENT=production \
  gated-communities:latest
```

### Docker Run Options

| Option | Description |
|--------|-------------|
| `-d` | Run in detached mode |
| `-p 8000:8000` | Map container port to host |
| `--restart unless-stopped` | Auto-restart on failure |
| `--memory 512m` | Memory limit |
| `--cpus 0.5` | CPU limit |

---

## Docker Compose (Development)

### Quick Start

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your values
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `app` | 8000 | FastAPI application |
| `db` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis cache |
| `worker` | — | Background worker |

### Development Commands

```bash
# Run migrations
docker-compose exec app python -m gated_communities.migrate

# Run tests
docker-compose exec app pytest

# Shell into container
docker-compose exec app bash

# View database
docker-compose exec db psql -U postgres -d gated_communities

# View Redis
docker-compose exec redis redis-cli
```

---

## Docker Compose (Production)

### Production Configuration

```bash
# Use production compose file
docker-compose -f docker/docker-compose.prod.yml up -d

# With custom environment
docker-compose -f docker/docker-compose.prod.yml --env-file .env.prod up -d
```

### Production Features

- **Read-only containers** — All services run with `read_only: true`
- **Security** — `no-new-privileges: true` on all services
- **Log rotation** — JSON file logging with 10MB max size, 3 files
- **Restart policy** — `always` for all services
- **Resource limits** — Configured per service

### Production Services

| Service | Description |
|---------|-------------|
| `postgres` | PostgreSQL with persistent volume |
| `redis` | Redis with persistent volume |
| `backend` | FastAPI application |
| `frontend` | Next.js frontend |
| `nginx` | Reverse proxy with SSL termination |

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.28+)
- kubectl configured
- cert-manager installed (for TLS)
- NGINX Ingress Controller installed

### Deployment Steps

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create secrets (edit with real values first!)
kubectl apply -f k8s/secret.yaml

# 3. Create configmap
kubectl apply -f k8s/configmap.yaml

# 4. Create service
kubectl apply -f k8s/service.yaml

# 5. Create deployment
kubectl apply -f k8s/deployment.yaml

# 6. Create ingress
kubectl apply -f k8s/ingress.yaml

# 7. Create HPA
kubectl apply -f k8s/hpa.yaml

# 8. Create PDB
kubectl apply -f k8s/pdb.yaml
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n gated-communities

# Check services
kubectl get svc -n gated-communities

# Check ingress
kubectl get ingress -n gated-communities

# Check HPA
kubectl get hpa -n gated-communities

# View logs
kubectl logs -n gated-communities -l app=gated-communities --tail=100

# Port forward for local access
kubectl port-forward -n gated-communities svc/gated-communities 8080:80
```

### Updating the Deployment

```bash
# Update image
kubectl set image deployment/gated-communities \
  app=gated-communities:new-version \
  -n gated-communities

# Watch rollout
kubectl rollout status deployment/gated-communities -n gated-communities

# Rollback if needed
kubectl rollout undo deployment/gated-communities -n gated-communities
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment/gated-communities --replicas=5 -n gated-communities

# Edit HPA
kubectl edit hpa gated-communities -n gated-communities
```

---

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |
| `LLM_API_KEY` | OpenAI API key | `sk-...` |
| `SECRET_KEY` | Application secret key | `random-string-32-chars` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENVIRONMENT` | `production` | Deployment environment |
| `DEBUG` | `false` | Debug mode |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `DATABASE_POOL_SIZE` | `20` | Database connection pool size |
| `MODERATION_THRESHOLD` | `0.8` | Auto-moderation threshold |
| `ESCALATION_TIMEOUT_MINUTES` | `30` | Escalation timeout |
| `REPUTATION_DECAY_DAYS` | `90` | Reputation decay period |
| `COMPLIANCE_AUDIT_RETENTION_DAYS` | `365` | Audit log retention |
| `METRICS_ENABLED` | `true` | Enable Prometheus metrics |
| `TRACING_ENABLED` | `false` | Enable distributed tracing |

### Kubernetes Secrets

Create secrets before deploying:

```bash
# Create secret manually
kubectl create secret generic gated-communities-secrets \
  --from-literal=database-url='postgresql://user:pass@host:5432/db' \
  --from-literal=redis-url='redis://host:6379/0' \
  --from-literal=llm-api-key='sk-...' \
  --from-literal=secret-key='random-string' \
  -n gated-communities
```

---

## Database Migrations

### Running Migrations

```bash
# Docker Compose
docker-compose exec app python -m gated_communities.migrate

# Kubernetes
kubectl exec -n gated-communities deploy/gated-communities -- python -m gated_communities.migrate
```

### Migration Commands

| Command | Description |
|---------|-------------|
| `migrate` | Run pending migrations |
| `migrate --dry-run` | Preview migrations without applying |
| `migrate --rollback` | Rollback last migration |
| `migrate --status` | Show migration status |

---

## Health Checks

### Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health` | Overall health | `{"status": "healthy", ...}` |
| `GET /ready` | Readiness probe | `{"ready": true, ...}` |
| `GET /live` | Liveness probe | `{"alive": true}` |

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

---

## Monitoring

### Prometheus Metrics

Metrics are available at `GET /metrics`:

```
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health"} 1523

# TYPE http_request_duration_seconds gauge
http_request_duration_seconds{endpoint="/api/v1/tiers"} 0.045

# TYPE agent_executions_total counter
agent_executions_total{agent="TierEvaluatorAgent"} 456

# TYPE agent_execution_duration_seconds gauge
agent_execution_duration_seconds{agent="TierEvaluatorAgent"} 0.123
```

### Prometheus Configuration

```yaml
# k8s/prometheus.yml
scrape_configs:
  - job_name: 'gated-communities'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - gated-communities
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: gated-communities
        action: keep
```

### Grafana Dashboard

Import the provided Grafana dashboard JSON for:
- Request rate and latency
- Agent execution metrics
- Error rates
- Resource utilization

---

## Backup and Recovery

### Database Backup

```bash
# Docker Compose
docker-compose exec db pg_dump -U postgres gated_communities > backup.sql

# Kubernetes
kubectl exec -n gated-communities deploy/postgres -- pg_dump -U postgres gated_communities > backup.sql
```

### Database Restore

```bash
# Docker Compose
docker-compose exec -T db psql -U postgres gated_communities < backup.sql

# Kubernetes
cat backup.sql | kubectl exec -i -n gated-communities deploy/postgres -- psql -U postgres gated_communities
```

### Redis Backup

```bash
# Docker Compose
docker-compose exec redis redis-cli SAVE
docker cp gated-communities_redis_1:/data/dump.rdb ./dump.rdb

# Kubernetes
kubectl exec -n gated-communities deploy/redis -- redis-cli SAVE
kubectl cp gated-communities/deploy/redis:/data/dump.rdb ./dump.rdb
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **Container won't start** | Missing env vars | Check all required env vars are set |
| **Database connection failed** | Wrong DATABASE_URL | Verify connection string format |
| **Redis connection failed** | Wrong REDIS_URL | Verify Redis is running and accessible |
| **LLM calls failing** | Invalid API key | Verify LLM_API_KEY is correct |
| **High memory usage** | Too many replicas | Adjust HPA limits or reduce replicas |
| **Pod evicted** | Resource limits | Increase memory/CPU limits |

### Debugging Commands

```bash
# View pod details
kubectl describe pod -n gated-communities -l app=gated-communities

# View pod logs
kubectl logs -n gated-communities -l app=gated-communities --previous

# Execute into pod
kubectl exec -it -n gated-communities deploy/gated-communities -- bash

# Check events
kubectl get events -n gated-communities --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n gated-communities
```

### Log Levels

Set `LOG_LEVEL` to control verbosity:

| Level | Use Case |
|-------|----------|
| `DEBUG` | Development troubleshooting |
| `INFO` | Normal operations |
| `WARNING` | Production with reduced noise |
| `ERROR` | Production errors only |
| `CRITICAL` | Critical failures only |

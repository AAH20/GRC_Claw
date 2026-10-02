# GRC_Claw Deployment Guide

> Last updated: 2026-10-01

This guide covers deploying GRC_Claw across development, staging, and production environments using Docker Compose, Kubernetes, and sovereign (air-gap) configurations.

---

## Table of Contents

- [Overview](#overview)
- [Deployment Options](#deployment-options)
- [Docker Compose (Development)](#docker-compose-development)
- [Kubernetes (Production)](#kubernetes-production)
- [Sovereign / Air-Gap Deployment](#sovereign--air-gap-deployment)
- [Helm Chart Deployment](#helm-chart-deployment)
- [Terraform Deployment](#terraform-deployment)
- [Environment Variables](#environment-variables)
- [Health Checks](#health-checks)
- [Scaling](#scaling)
- [Backup and Recovery](#backup-and-recovery)

---

## Overview

```mermaid
flowchart TB
    A[Development] --> B[Docker Compose]
    C[Staging] --> D[Kubernetes]
    E[Production] --> D
    F[Air-Gap] --> G[Sovereign Stack]
    B --> H[Single Process]
    D --> I[Multi-Pod]
    G --> J[Ollama + Local]
```

---

## Deployment Options

| Environment | Method | Use Case |
|-------------|--------|----------|
| Development | Docker Compose | Local development, quick start |
| Staging | Kubernetes (Kind/Minikube) | Pre-production testing |
| Production | Kubernetes (EKS/GKE/AKS) | Production workloads |
| Air-Gap | Sovereign Stack | Classified, disconnected environments |
| On-Prem | Helm + Terraform | Enterprise data centers |

---

## Docker Compose (Development)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/AAH20/GRC_Claw.git
cd GRC_Claw

# Start the stack
docker compose -f deployment/docker-compose.yml up -d

# Verify health
curl http://localhost:3000/health
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `grc-claw-gateway` | 3000 | API Gateway |
| `supabase-db` | 5432 | PostgreSQL database |
| `redis` | 6379 | Cache and idempotency |
| `ollama` | 11434 | Local LLM (sovereign mode) |
| `nginx` | 8080 | Reverse proxy |

### Docker Compose Configuration

```yaml
version: "3.8"
services:
  gateway:
    build:
      context: .
      dockerfile: deploy/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:postgres@supabase-db:5432/grc_claw
      - REDIS_URL=redis://redis:6379
      - SOVEREIGN_MODE=false
    depends_on:
      - supabase-db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  supabase-db:
    image: supabase/postgres:latest
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=grc_claw
    volumes:
      - supabase-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    profiles:
      - sovereign

volumes:
  supabase-data:
  ollama-data:
```

---

## Kubernetes (Production)

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or on-prem)
- Helm 3.x
- kubectl configured
- cert-manager (for TLS)
- ingress-nginx (for ingress)

### Namespace Setup

```bash
kubectl create namespace grc-claw
kubectl config set-context --current --namespace=grc-claw
```

### Deploy with Helm

```bash
# Add the GRC_Claw Helm repository
helm repo add grc-claw https://charts.grc-claw.com
helm repo update

# Install the chart
helm install grc-claw grc-claw/grc-claw \
  --namespace grc-claw \
  --set gateway.replicas=2 \
  --set gateway.env.DATABASE_URL=postgresql://... \
  --set gateway.env.REDIS_URL=redis://... \
  --set gateway.env.SOVEREIGN_MODE=false
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n grc-claw

# Check services
kubectl get svc -n grc-claw

# Check logs
kubectl logs -n grc-claw -l app.kubernetes.io/component=gateway

# Port-forward for local access
kubectl port-forward -n grc-claw svc/grc-claw-gateway 3000:3000
```

---

## Sovereign / Air-Gap Deployment

### Overview

For air-gapped or sovereign deployments, set `SOVEREIGN_MODE=true` to route all LLM traffic through a local Ollama instance. No data leaves your network.

### Quick Start

```bash
export SOVEREIGN_MODE=true
grc sovereign init
docker compose -f docker-compose.sovereign.yml up
```

### Sovereign Stack

| Service | Description |
|---------|-------------|
| `ollama` | Local LLM backend |
| `grc-claw-gateway` | GRC_Claw gateway daemon |
| `supabase` | PostgreSQL persistence |
| `nginx` | Reverse proxy |

### Sovereign Configuration

```yaml
# docker-compose.sovereign.yml
version: "3.8"
services:
  gateway:
    build:
      context: .
      dockerfile: deploy/Dockerfile
    environment:
      - SOVEREIGN_MODE=true
      - GRC_LLM_PROVIDER=ollama
      - GRC_LLM_MODEL=llama3
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
      - supabase-db

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"

  supabase-db:
    image: supabase/postgres:latest
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=grc_claw
    volumes:
      - supabase-data:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - gateway

volumes:
  ollama-data:
  supabase-data:
```

### Air-Gap Installation

```bash
# 1. On connected machine, pull all images
docker pull ollama/ollama:latest
docker pull supabase/postgres:latest
docker pull nginx:alpine
docker save -o grc-claw-images.tar ollama/ollama:latest supabase/postgres:latest nginx:alpine

# 2. Transfer to air-gapped machine
scp grc-claw-images.tar airgap:/tmp/

# 3. On air-gapped machine, load images
docker load -i /tmp/grc-claw-images.tar

# 4. Deploy
docker compose -f docker-compose.sovereign.yml up -d
```

---

## Helm Chart Deployment

### Chart Values

```yaml
# values.yaml
gateway:
  replicas: 2
  image:
    repository: ghcr.io/grc-claw/gateway
    tag: latest
    pullPolicy: IfNotPresent
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "1000m"
  env:
    NODE_ENV: production
    SOVEREIGN_MODE: "false"
    GATEWAY_MODULAR_V15: "route-registry,policy-firewall"
  service:
    type: ClusterIP
    port: 3000
  ingress:
    enabled: true
    className: nginx
    hosts:
      - host: grc-claw.example.com
        paths:
          - path: /
            pathType: Prefix

postgresql:
  enabled: true
  auth:
    database: grc_claw
    username: grc_claw
  primary:
    persistence:
      size: 10Gi

redis:
  enabled: true
  architecture: standalone
  master:
    persistence:
      size: 1Gi

ollama:
  enabled: false
  models:
    - llama3
```

### Upgrade

```bash
helm upgrade grc-claw grc-claw/grc-claw \
  --namespace grc-claw \
  -f values.yaml
```

### Rollback

```bash
helm rollback grc-claw 1 --namespace grc-claw
```

---

## Terraform Deployment

### AWS EKS

```hcl
# main.tf
module "grc_claw" {
  source = "grc-claw/deployment/terraform/aws"

  cluster_name    = "grc-claw-production"
  cluster_version = "1.28"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  gateway_replicas = 3
  database_instance_class = "db.t3.medium"
  redis_node_type = "cache.t3.medium"
  
  sovereign_mode = false
  
  tags = {
    Environment = "production"
    Project     = "grc-claw"
  }
}
```

### Deploy

```bash
cd deployment/terraform/aws
terraform init
terraform plan
terraform apply
```

---

## Environment Variables

### Core Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Environment mode | `production` |
| `SOVEREIGN_MODE` | Route LLM through local Ollama | `false` |
| `GRC_LLM_PROVIDER` | LLM provider: `openai`, `anthropic`, `ollama` | `openai` |
| `GRC_LLM_MODEL` | Model override | — |
| `GRC_LOG_LEVEL` | Log level: `debug`, `info`, `warn`, `error` | `info` |
| `GRC_EVIDENCE_DIR` | Local evidence storage directory | `.grc/evidence` |

### Database Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `REDIS_URL` | Redis connection string | — |
| `SUPABASE_URL` | Supabase project URL | — |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | — |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | — |

### A2Z SOC Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `A2Z_SOC_BASE_URL` | A2Z SOC platform base URL | `https://a2zsoc.com` |
| `GRC_CLAW_API_KEY` | API key for A2Z SOC authentication | — |
| `GRC_CLAW_TENANT` | Default tenant ID | — |

### Security Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET` | JWT signing secret | — |
| `ENCRYPTION_KEY` | AES-256 encryption key | — |
| `VAULT_ADDR` | HashiCorp Vault address | — |
| `VAULT_TOKEN` | HashiCorp Vault token | — |

---

## Health Checks

### Gateway Health

```bash
curl http://localhost:3000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "checks": {
    "database": "connected",
    "redis": "connected",
    "llm": "connected"
  }
}
```

### Readiness Probe

```bash
curl http://localhost:3000/ready
```

### Liveness Probe

```bash
curl http://localhost:3000/live
```

---

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: grc-claw-gateway
  namespace: grc-claw
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: grc-claw-gateway
  minReplicas: 2
  maxReplicas: 32
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Worker Pool Scaling

Worker pods autoscale based on queue depth:

| Queue Depth | Worker Pods |
|-------------|-------------|
| 0-100 | 2 |
| 101-500 | 4 |
| 501-2000 | 8 |
| 2001-10000 | 16 |
| 10000+ | 32 |

---

## Backup and Recovery

### Database Backup

```bash
# Automated daily backup
kubectl create cronjob grc-claw-db-backup \
  --schedule="0 2 * * *" \
  --image=postgres:16-alpine \
  -- pg_dump $DATABASE_URL > /backup/grc-claw-$(date +%F).sql
```

### Evidence Backup

```bash
# Backup evidence directory
tar -czf evidence-backup-$(date +%F).tar.gz .grc/evidence/

# Upload to S3
aws s3 cp evidence-backup-$(date +%F).tar.gz s3://grc-claw-backups/
```

### Disaster Recovery

```bash
# Restore from backup
psql $DATABASE_URL < backup/grc-claw-2026-10-01.sql

# Restore evidence
tar -xzf evidence-backup-2026-10-01.tar.gz -C .grc/evidence/

# Verify integrity
grc evidence verify --all
```

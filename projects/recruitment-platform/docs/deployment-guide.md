# Recruitment Platform Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring](#monitoring)
7. [Backup and Recovery](#backup-and-recovery)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Recruitment Platform can be deployed using Docker Compose for development and small-scale deployments, or Kubernetes for production workloads.

## Prerequisites

### For Docker Deployment

- Docker 24.0+
- Docker Compose 2.20+
- 4GB RAM minimum
- 10GB disk space

### For Kubernetes Deployment

- Kubernetes 1.28+
- kubectl 1.28+
- Helm 3.12+ (optional)
- cert-manager 1.13+ (for TLS)
- NGINX Ingress Controller
- 8GB RAM minimum per node
- 50GB disk space

---

## Docker Deployment

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd recruitment-platform

# Copy environment configuration
cp .env.example .env

# Edit .env with your settings
nano .env

# Build and start all services
docker-compose up --build -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f api
```

### Docker Compose Services

The `docker-compose.yml` defines the following services:

| Service | Image | Ports | Description |
|---------|-------|-------|-------------|
| api | recruitment-platform:latest | 8000:8000 | Main API server |
| db | postgres:16-alpine | 5432:5432 | PostgreSQL database |
| redis | redis:7-alpine | 6379:6379 | Redis cache |
| worker | recruitment-platform:latest | - | Celery worker |

### Production Docker Deployment

For production, use the production Docker Compose file:

```bash
# Use production configuration
docker-compose -f docker/docker-compose.prod.yml up --build -d
```

The production configuration includes:
- NGINX reverse proxy with SSL termination
- Multiple API replicas
- Persistent volume backups
- Health checks and auto-restart

### Docker Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | Recruitment Platform | Application name |
| `APP_VERSION` | 1.0.0 | Application version |
| `DEBUG` | false | Enable debug mode |
| `HOST` | 0.0.0.0 | Server bind address |
| `PORT` | 8000 | Server port |
| `WORKERS` | 1 | Number of Uvicorn workers |
| `SECRET_KEY` | change-me-in-production | Application secret key |
| `DATABASE_URL` | sqlite:///./recruitment.db | Database connection string |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection string |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `OPENAI_MODEL` | gpt-4 | OpenAI model name |
| `LOG_LEVEL` | INFO | Logging level |
| `LOG_FORMAT` | json | Log format (json or console) |

---

## Kubernetes Deployment

### Architecture

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Namespace: recruitment-platform"
            ING[NGINX Ingress] --> SVC[Service]
            SVC --> P1[Pod 1]
            SVC --> P2[Pod 2]
            SVC --> P3[Pod 3]
            
            HPA[HPA 3-10 replicas] -.-> P1 & P2 & P3
            PDB[PDB min 2] -.-> P1 & P2 & P3
        end
        
        subgraph "Data Services"
            PG[(PostgreSQL)]
            RD[(Redis)]
        end
    end
    
    P1 & P2 & P3 --> PG
    P1 & P2 & P3 --> RD
```

### Deployment Steps

#### 1. Create the Namespace

```bash
kubectl apply -f k8s/base/namespace.yaml
```

#### 2. Apply Base Resources

```bash
# Apply all base resources
kubectl apply -k k8s/base/

# Verify deployment
kubectl get all -n recruitment-platform
```

#### 3. Configure Secrets

```bash
# Create secrets (replace with actual values)
kubectl create secret generic recruitment-platform-secrets \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=DATABASE_URL='postgresql://user:pass@postgres:5432/recruitment' \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  --from-literal=OPENAI_API_KEY='your-openai-key' \
  -n recruitment-platform
```

#### 4. Deploy to Staging

```bash
# Apply staging overlay
kubectl apply -k k8s/overlays/staging/

# Verify staging deployment
kubectl get all -n recruitment-platform-staging
```

#### 5. Deploy to Production

```bash
# Apply production overlay
kubectl apply -k k8s/overlays/production/

# Verify production deployment
kubectl get all -n recruitment-platform-production
```

### Kustomize Overlays

The project uses Kustomize for environment-specific configurations:

| Overlay | Namespace | Replicas | Memory Limit |
|---------|-----------|----------|--------------|
| development | recruitment-platform-development | 1 | 1Gi |
| staging | recruitment-platform-staging | 2 | 2Gi |
| production | recruitment-platform-production | 3 | 2Gi |

### Scaling

The HorizontalPodAutoscaler (HPA) automatically scales based on:

- **CPU**: Target 70% utilization
- **Memory**: Target 80% utilization
- **Min replicas**: 3
- **Max replicas**: 10

Manual scaling:

```bash
# Scale to 5 replicas
kubectl scale deployment recruitment-platform --replicas=5 -n recruitment-platform-production

# Check HPA status
kubectl get hpa -n recruitment-platform-production
```

### Rolling Updates

```bash
# Update the image
kubectl set image deployment/recruitment-platform \
  api=ghcr.io/your-org/recruitment-platform:v1.1.0 \
  -n recruitment-platform-production

# Watch the rollout
kubectl rollout status deployment/recruitment-platform -n recruitment-platform-production

# Rollback if needed
kubectl rollout undo deployment/recruitment-platform -n recruitment-platform-production
```

### Ingress and TLS

The ingress is configured with:
- NGINX ingress controller
- cert-manager for automatic TLS via Let's Encrypt
- Rate limiting: 100 requests/minute

```bash
# Check ingress
kubectl get ingress -n recruitment-platform-production

# Check certificate
kubectl get certificate -n recruitment-platform-production
```

---

## Environment Configuration

### Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `ENABLE_BIAS_DETECTION` | true | Enable bias detection agents |
| `ENABLE_ANALYTICS` | true | Enable analytics agents |
| `ENABLE_NOTIFICATIONS` | true | Enable notification system |

### Database Configuration

#### SQLite (Development)

```env
DATABASE_URL=sqlite:///./recruitment.db
```

#### PostgreSQL (Production)

```env
DATABASE_URL=postgresql://user:password@postgres:5432/recruitment
```

### Redis Configuration

```env
REDIS_URL=redis://redis:6379/0
```

### OpenAI Configuration

```env
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4
```

---

## Monitoring

### Health Checks

```bash
# Liveness probe
curl http://localhost:8000/api/v1/health

# Readiness probe
curl http://localhost:8000/api/v1/ready
```

### Prometheus Metrics

Metrics are available at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

### Prometheus Configuration

The `monitoring/prometheus.yml` configures scraping:

```yaml
scrape_configs:
  - job_name: recruitment-platform
    static_configs:
      - targets:
          - api:8000
    metrics_path: /metrics
    scrape_interval: 15s
```

### Grafana Dashboard

Import the provided Grafana dashboard JSON to visualize:

- Request rate and latency
- Error rates
- Agent execution times
- Resource utilization

### Log Aggregation

Logs are output in JSON format (configurable via `LOG_FORMAT`). Use your preferred log aggregation solution:

- **ELK Stack**: Filebeat → Logstash → Elasticsearch → Kibana
- **Loki**: Promtail → Loki → Grafana
- **Cloud**: AWS CloudWatch, GCP Cloud Logging, Azure Monitor

---

## Backup and Recovery

### Database Backups

```bash
# PostgreSQL backup
kubectl exec -it postgres-0 -n recruitment-platform \
  pg_dump -U postgres recruitment > backup.sql

# Restore from backup
kubectl exec -i postgres-0 -n recruitment-platform \
  psql -U postgres recruitment < backup.sql
```

### Redis Backups

Redis persistence is enabled with AOF (Append Only File):

```bash
# Trigger manual save
kubectl exec -it redis-0 -n recruitment-platform redis-cli BGSAVE
```

### Volume Backups

Use your cloud provider's snapshot mechanism or Velero for Kubernetes backup:

```bash
# Install Velero
velero install --provider aws --bucket your-backup-bucket

# Create backup
velero backup create recruitment-platform-backup \
  --include-namespaces recruitment-platform
```

---

## Troubleshooting

### Pod CrashLoopBackOff

```bash
# Check pod status
kubectl describe pod <pod-name> -n recruitment-platform

# Check logs
kubectl logs <pod-name> -n recruitment-platform

# Common causes:
# - Missing secrets
# - Database connection failure
# - Insufficient resources
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl run -it --rm postgres-test --image=postgres:16-alpine \
  -- psql $DATABASE_URL -c "SELECT 1"

# Check database logs
kubectl logs deployment/postgres -n recruitment-platform
```

### High Memory Usage

```bash
# Check resource usage
kubectl top pods -n recruitment-platform

# Increase memory limit
kubectl patch deployment recruitment-platform -n recruitment-platform \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress recruitment-platform-ingress -n recruitment-platform

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

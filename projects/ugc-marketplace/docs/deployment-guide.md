# UGC Marketplace Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Production Deployment](#production-deployment)
5. [Monitoring](#monitoring)
6. [Backup and Recovery](#backup-and-recovery)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Multi-container orchestration |
| kubectl | 1.28+ | Kubernetes CLI |
| kustomize | 5.0+ | Kubernetes manifest management |
| Helm | 3.12+ | Kubernetes package manager (optional) |
| Terraform | 1.5+ | Infrastructure as Code (optional) |

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| Memory | 4 GB | 8+ GB |
| Disk | 20 GB | 50+ GB |
| Network | 100 Mbps | 1 Gbps |

### Environment Variables

Create a `.env` file from the example:

```bash
cp docker/.env.example .env
```

Edit `.env` with your values:

```env
# PostgreSQL
POSTGRES_DB=ugc_marketplace
POSTGRES_USER=ugc_user
POSTGRES_PASSWORD=your-strong-password-here

# Redis
REDIS_PASSWORD=your-strong-redis-password

# Backend
SECRET_KEY=your-32-character-minimum-secret-key
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com
LOG_LEVEL=INFO
BACKEND_WORKERS=4

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
API_URL=http://backend:8000

# SSL/TLS
SSL_CERT_PATH=./certs/fullchain.pem
SSL_KEY_PATH=./certs/privkey.pem

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

---

## Docker Deployment

### Quick Start

1. **Clone the repository:**

```bash
git clone https://github.com/your-org/ugc-marketplace.git
cd ugc-marketplace
```

2. **Configure environment:**

```bash
cp docker/.env.example .env
# Edit .env with your values
```

3. **Start all services:**

```bash
docker-compose up -d
```

4. **Verify deployment:**

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8000/api/v1/health
```

### Docker Compose Configuration

The `docker-compose.yml` defines the following services:

| Service | Image | Ports | Description |
|---------|-------|-------|-------------|
| postgres | postgres:16-alpine | 5432 | Primary database |
| redis | redis:7-alpine | 6379 | Cache and session store |
| backend | ugc-marketplace:latest | 8000 | FastAPI backend |
| frontend | ugc-marketplace-frontend:latest | 3000 | Next.js frontend |
| nginx | nginx:1.27-alpine | 80, 443 | Reverse proxy |

### Managing Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Scale backend workers
docker-compose up -d --scale backend=3

# Rebuild and restart
docker-compose up -d --build

# Remove volumes (WARNING: deletes data)
docker-compose down -v
```

---

## Kubernetes Deployment

### Prerequisites

- A running Kubernetes cluster (EKS, GKE, AKS, or on-prem)
- `kubectl` configured with cluster access
- `kustomize` installed

### Deployment Steps

1. **Create the namespace:**

```bash
kubectl create namespace ugc-marketplace
```

2. **Deploy base resources:**

```bash
kubectl apply -k k8s/overlays/development/
```

3. **Verify deployment:**

```bash
# Check pods
kubectl get pods -n ugc-marketplace

# Check services
kubectl get svc -n ugc-marketplace

# Check logs
kubectl logs -n ugc-marketplace -l app=ugc-marketplace
```

### Environment Overlays

The project uses Kustomize overlays for environment-specific configurations:

| Overlay | Namespace | Purpose |
|---------|-----------|---------|
| `k8s/overlays/development/` | ugc-marketplace | Development environment |
| `k8s/overlays/production/` | ugc-marketplace | Production environment |

### Deploying to Production

```bash
# Apply production configuration
kubectl apply -k k8s/overlays/production/

# Verify production deployment
kubectl get pods -n ugc-marketplace
kubectl get svc -n ugc-marketplace
kubectl get ingress -n ugc-marketplace
```

### Scaling

```bash
# Scale API replicas
kubectl scale deployment ugc-marketplace-api --replicas=5 -n ugc-marketplace

# Check HPA status
kubectl get hpa -n ugc-marketplace
```

### Rolling Updates

```bash
# Update image
kubectl set image deployment/ugc-marketplace-api api=ugc-marketplace:v1.1.0 -n ugc-marketplace

# Check rollout status
kubectl rollout status deployment/ugc-marketplace-api -n ugc-marketplace

# Rollback if needed
kubectl rollout undo deployment/ugc-marketplace-api -n ugc-marketplace
```

---

## Production Deployment

### Production Checklist

- [ ] Change all default passwords and secrets
- [ ] Configure SSL/TLS certificates
- [ ] Set up CORS with specific origins
- [ ] Enable rate limiting
- [ ] Configure monitoring and alerting
- [ ] Set up log aggregation
- [ ] Configure backup strategy
- [ ] Test disaster recovery
- [ ] Review security policies
- [ ] Load test the application

### Production Docker Compose

Use the production-specific compose file:

```bash
docker-compose -f docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

### SSL/TLS Configuration

1. **Obtain certificates** (Let's Encrypt recommended):

```bash
certbot certonly --standalone -d yourdomain.com
```

2. **Copy certificates:**

```bash
mkdir -p docker/certs
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem docker/certs/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem docker/certs/
```

3. **Update nginx.conf** with your domain name.

4. **Restart nginx:**

```bash
docker-compose restart nginx
```

### Resource Limits

Production resource configuration:

| Service | CPU Limit | Memory Limit | CPU Request | Memory Request |
|---------|-----------|--------------|-------------|----------------|
| backend | 2.0 | 1G | 0.5 | 256M |
| frontend | 2.0 | 1G | 0.5 | 256M |
| nginx | 1.0 | 256M | 0.25 | 64M |
| postgres | 2.0 | 1G | 0.5 | 256M |
| redis | 1.0 | 512M | 0.25 | 128M |

### Security Hardening

1. **Read-only containers:**

```yaml
read_only: true
tmpfs:
  - /tmp
```

2. **Non-root user:**

```dockerfile
USER appuser
```

3. **Security headers** (configured in nginx.conf):

```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
```

4. **Network policies:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ugc-marketplace-network-policy
spec:
  podSelector:
    matchLabels:
      app: ugc-marketplace
  policyTypes:
    - Ingress
    - Egress
```

---

## Monitoring

### Prometheus Metrics

The application exposes Prometheus metrics at:

```
GET /api/v1/quality/metrics
```

### Prometheus Configuration

The `monitoring/prometheus.yml` defines alert rules:

| Alert | Condition | Severity |
|-------|-----------|----------|
| HighErrorRate | Error rate > 5% for 5m | critical |
| HighLatency | P95 latency > 2s for 5m | warning |
| PodCrashLooping | Pod restarts in 15m | critical |
| HighMemoryUsage | Memory > 85% for 5m | warning |

### Setting Up Monitoring

1. **Deploy Prometheus:**

```bash
kubectl apply -f monitoring/prometheus.yml
```

2. **Access Prometheus:**

```bash
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
```

3. **Access Grafana:**

```bash
kubectl port-forward svc/grafana 3000:3000 -n monitoring
```

### Key Metrics to Watch

| Metric | Description | Threshold |
|--------|-------------|-----------|
| `http_requests_total` | Total HTTP requests | - |
| `http_request_duration_seconds` | Request latency | P95 < 2s |
| `http_requests_total{status="5.."}` | Error rate | < 5% |
| `container_memory_usage_bytes` | Memory usage | < 85% |
| `kube_pod_container_status_restarts_total` | Pod restarts | 0 |

---

## Backup and Recovery

### Database Backups

```bash
# Create backup
docker-compose exec postgres pg_dump -U ugc_user ugc_marketplace > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U ugc_user ugc_marketplace < backup.sql
```

### Automated Backups

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/ugc-marketplace && docker-compose exec -T postgres pg_dump -U ugc_user ugc_marketplace > /backups/ugc_$(date +\%Y\%m\%d).sql
```

### Redis Backups

```bash
# Force save
docker-compose exec redis redis-cli -a $REDIS_PASSWORD BGSAVE

# Copy dump file
docker cp ugc-redis:/data/dump.rdb /backups/
```

---

## Troubleshooting

### Common Deployment Issues

#### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n ugc-marketplace

# Check events
kubectl get events -n ugc-marketplace --sort-by='.lastTimestamp'
```

#### Database Connection Failures

```bash
# Test database connection
kubectl exec -it <pod-name> -n ugc-marketplace -- python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
engine = create_async_engine('postgresql+asyncpg://...')
async def test():
    async with engine.connect() as conn:
        print('Connected!')
asyncio.run(test())
"
```

#### High Memory Usage

```bash
# Check memory usage
kubectl top pods -n ugc-marketplace

# Check memory limits
kubectl describe pod <pod-name> -n ugc-marketplace | grep -A 5 "Limits"
```

#### SSL Certificate Issues

```bash
# Test SSL configuration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check certificate expiry
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Getting Help

- **Logs:** `kubectl logs -n ugc-marketplace -l app=ugc-marketplace`
- **Events:** `kubectl get events -n ugc-marketplace`
- **Metrics:** `kubectl top pods -n ugc-marketplace`
- **Documentation:** See [architecture.md](architecture.md) for system design

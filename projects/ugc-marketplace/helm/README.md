# UGC Marketplace Helm Chart

A production-grade Helm chart for deploying the UGC Marketplace Platform on Kubernetes.

## Overview

The UGC Marketplace is a unified agentic AI system for content moderation, creator monetization, rights management, and marketplace operations. This Helm chart provides a complete, production-ready deployment configuration with:

- **High Availability**: Pod anti-affinity, topology spread constraints, and Pod Disruption Budget
- **Auto-scaling**: Horizontal Pod Autoscaler with CPU/memory metrics and custom scaling behavior
- **Health Checks**: Liveness, readiness, and startup probes
- **Security**: Non-root containers, read-only root filesystem, dropped capabilities, and network policies
- **Monitoring**: Prometheus ServiceMonitor and metrics endpoint
- **Ingress**: NGINX ingress with TLS termination via cert-manager

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- NGINX Ingress Controller
- cert-manager (for TLS)
- Prometheus Operator (for ServiceMonitor, optional)

## Installation

### Add the chart locally

```bash
cd ~/GRC_Claw/projects/ugc-marketplace/helm
helm install ugc-marketplace . --namespace ugc-marketplace --create-namespace
```

### With custom values

```bash
helm install ugc-marketplace . \
  --namespace ugc-marketplace \
  --create-namespace \
  --set image.repository=myregistry/ugc-marketplace \
  --set image.tag=v1.2.3 \
  --set ingress.hosts[0].host=ugc-marketplace.mycompany.com
```

### With a values file

```bash
helm install ugc-marketplace . \
  --namespace ugc-marketplace \
  --create-namespace \
  -f values-production.yaml
```

## Configuration

### Key Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas (when HPA disabled) | `3` |
| `image.repository` | Container image repository | `ugc-marketplace` |
| `image.tag` | Container image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8000` |
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class | `nginx` |
| `ingress.hosts[0].host` | Ingress hostname | `ugc-marketplace.example.com` |
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Minimum replicas | `3` |
| `autoscaling.maxReplicas` | Maximum replicas | `20` |
| `autoscaling.targetCPUUtilizationPercentage` | CPU target | `70` |
| `autoscaling.targetMemoryUtilizationPercentage` | Memory target | `80` |
| `resources.limits.cpu` | CPU limit | `1000m` |
| `resources.limits.memory` | Memory limit | `2Gi` |
| `resources.requests.cpu` | CPU request | `250m` |
| `resources.requests.memory` | Memory request | `512Mi` |
| `podDisruptionBudget.enabled` | Enable PDB | `true` |
| `podDisruptionBudget.minAvailable` | Min available pods | `2` |
| `monitoring.enabled` | Enable monitoring | `true` |
| `monitoring.serviceMonitor.enabled` | Enable ServiceMonitor | `true` |
| `networkPolicy.enabled` | Enable network policy | `false` |

### Secrets

The following secrets are configured in `values.yaml`:

| Secret | Description |
|--------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka bootstrap servers |
| `SECRET_KEY` | Application secret key |
| `OPENAI_API_KEY` | OpenAI API key |

**Important**: Override all secrets in production using a separate values file or `--set` flags.

### Environment Variables

The following environment variables are configured via ConfigMap:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Application environment | `production` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `API_PREFIX` | API route prefix | `/api/v1` |
| `LLM_MODEL` | LLM model name | `gpt-4o` |
| `LLM_TEMPERATURE` | LLM temperature | `0.1` |
| `DEFAULT_CONFIDENCE_THRESHOLD` | Confidence threshold | `0.7` |
| `ENABLE_METRICS` | Enable metrics endpoint | `true` |
| `METRICS_PORT` | Metrics port | `9090` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://ugc-marketplace.example.com` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Rate limit per minute | `100` |
| `RATE_LIMIT_BURST` | Rate limit burst | `20` |

## Upgrading

```bash
helm upgrade ugc-marketplace . \
  --namespace ugc-marketplace \
  -f values-production.yaml
```

## Uninstalling

```bash
helm uninstall ugc-marketplace --namespace ugc-marketplace
```

## Production Checklist

Before deploying to production:

- [ ] Override all secrets with real values
- [ ] Set proper ingress hostname
- [ ] Configure TLS certificates (cert-manager)
- [ ] Set appropriate resource limits based on load testing
- [ ] Configure HPA thresholds based on traffic patterns
- [ ] Enable network policies
- [ ] Set up monitoring and alerting
- [ ] Configure pod disruption budget
- [ ] Set up backup strategy for persistent data
- [ ] Review security context settings
- [ ] Configure pod anti-affinity for multi-zone deployment

## Chart Structure

```
helm/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default values
├── README.md               # This file
└── templates/
    ├── _helpers.tpl        # Template helpers
    ├── deployment.yaml     # Backend deployment
    ├── service.yaml        # Backend service
    ├── ingress.yaml        # Ingress configuration
    ├── configmap.yaml      # ConfigMap
    ├── secret.yaml         # Secret template
    ├── hpa.yaml            # Horizontal Pod Autoscaler
    ├── serviceaccount.yaml # Service account
    ├── pdb.yaml            # Pod Disruption Budget
    ├── servicemonitor.yaml # Prometheus ServiceMonitor
    ├── networkpolicy.yaml  # Network policy
    └── NOTES.txt           # Post-install notes
```

## License

MIT

# Recruitment Platform Helm Chart

A production-grade Helm chart for deploying the Recruitment Platform on Kubernetes.

## Overview

This chart deploys the Recruitment Platform, a unified recruitment system with AI agents, on Kubernetes. It includes:

- **Deployment** with rolling updates, health checks, and security contexts
- **Service** for internal communication
- **Ingress** with TLS and rate limiting
- **ConfigMap** for non-sensitive configuration
- **Secret** for sensitive configuration
- **HPA** (Horizontal Pod Autoscaler) for automatic scaling
- **PDB** (Pod Disruption Budget) for availability guarantees
- **ServiceAccount** with minimal permissions
- **ServiceMonitor** for Prometheus monitoring (optional)

## Prerequisites

- Kubernetes 1.25+
- Helm 3.12+
- cert-manager (for TLS certificates)
- nginx-ingress controller
- Prometheus Operator (optional, for monitoring)

## Installation

### Add the chart repository (if published)

```bash
helm repo add recruitment-platform https://your-repo.com/charts
helm repo update
```

### Install the chart

```bash
# Install with default values
helm install recruitment-platform ./helm

# Install with custom values
helm install recruitment-platform ./helm -f custom-values.yaml

# Install in a specific namespace
helm install recruitment-platform ./helm --namespace recruitment-platform --create-namespace

# Dry run to preview
helm install recruitment-platform ./helm --dry-run --debug
```

### Upgrade

```bash
helm upgrade recruitment-platform ./helm -f custom-values.yaml
```

### Uninstall

```bash
helm uninstall recruitment-platform
```

## Configuration

### Key Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `3` |
| `image.repository` | Image repository | `recruitment-platform` |
| `image.tag` | Image tag | `""` (uses appVersion) |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `resources.requests.cpu` | CPU request | `250m` |
| `resources.requests.memory` | Memory request | `512Mi` |
| `resources.limits.cpu` | CPU limit | `1000m` |
| `resources.limits.memory` | Memory limit | `2Gi` |
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Minimum replicas | `3` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.hosts[0].host` | Ingress host | `recruitment.example.com` |

### Secrets

**IMPORTANT**: Change the default secrets before deploying to production!

```yaml
secrets:
  SECRET_KEY: "your-secure-secret-key-here"
  DATABASE_URL: "postgresql://user:password@host:5432/dbname"
  REDIS_URL: "redis://host:6379/0"
  OPENAI_API_KEY: "sk-your-openai-api-key"
```

### Custom Values Example

```yaml
replicaCount: 5

image:
  repository: ghcr.io/yourorg/recruitment-platform
  tag: "v1.2.3"

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60
  targetMemoryUtilizationPercentage: 70

ingress:
  enabled: true
  hosts:
    - host: recruitment.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: recruitment-platform-tls
      hosts:
        - recruitment.yourdomain.com

config:
  LOG_LEVEL: "DEBUG"
  WORKERS: "4"
  OPENAI_MODEL: "gpt-4-turbo"
```

## Health Checks

The chart configures three types of health checks:

- **Liveness Probe**: `/api/v1/health` - Restarts container if failing
- **Readiness Probe**: `/api/v1/ready` - Removes pod from service if failing
- **Startup Probe**: `/api/v1/health` - Delays other probes until app is ready

## Monitoring

Enable Prometheus monitoring:

```yaml
monitoring:
  enabled: true
  interval: 30s
  scrapeTimeout: 10s
```

## Security

The chart follows security best practices:

- Non-root container execution
- Read-only root filesystem
- Dropped Linux capabilities
- Security contexts at pod and container level
- Resource limits to prevent DoS
- Network policies (recommended to add separately)

## Troubleshooting

### Check pod status

```bash
kubectl get pods -n recruitment-platform
kubectl describe pod -n recruitment-platform <pod-name>
kubectl logs -n recruitment-platform <pod-name>
```

### Check HPA status

```bash
kubectl get hpa -n recruitment-platform
kubectl describe hpa -n recruitment-platform
```

### Check ingress

```bash
kubectl get ingress -n recruitment-platform
kubectl describe ingress -n recruitment-platform
```

### Port forward for local testing

```bash
kubectl port-forward -n recruitment-platform svc/recruitment-platform 8080:80
```

## License

MIT

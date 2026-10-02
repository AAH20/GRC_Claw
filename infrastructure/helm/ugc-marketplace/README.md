# UGC Marketplace Helm Chart

## Overview

This Helm chart deploys 10 UGC marketplace microservices for GRC_Claw. It provides a complete, production-grade deployment solution for user-generated content platforms with configurable scaling, security, monitoring, and high availability.

## Projects Included

| # | Project | Description |
|---|---------|-------------|
| 1 | content-platform | User-generated content publishing and discovery |
| 2 | review-system | Product and service review management |
| 3 | creator-monetization | Creator earnings, payouts, and subscription management |
| 4 | marketplace-analytics | Marketplace metrics, insights, and reporting |
| 5 | media-processor | Image, video, and audio processing pipeline |
| 6 | content-moderation | AI-powered content moderation and compliance |
| 7 | creator-dashboard | Creator analytics, content management, and earnings |
| 8 | subscription-manager | Subscription plans, billing, and access control |
| 9 | notification-hub | Multi-channel notification delivery system |
| 10 | search-discovery | Content search, recommendations, and discovery |

## Prerequisites

- Kubernetes 1.24+
- Helm 3.12+
- cert-manager (for TLS certificates)
- nginx-ingress controller
- Prometheus Operator (for metrics)

## Installation

```bash
# Install the chart
helm install ugc-marketplace ./infrastructure/helm/ugc-marketplace \
  --namespace ugc \
  --create-namespace

# Or with custom values
helm install ugc-marketplace ./infrastructure/helm/ugc-marketplace \
  --namespace ugc \
  --create-namespace \
  -f custom-values.yaml
```

## Upgrading

```bash
helm upgrade ugc-marketplace ./infrastructure/helm/ugc-marketplace \
  --namespace ugc
```

## Uninstallation

```bash
helm uninstall ugc-marketplace --namespace ugc
```

## Configuration

### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.imageRegistry` | Docker image registry | `ghcr.io/ahmedhassan/grc-claw` |
| `global.imagePullSecrets` | Image pull secrets | `[]` |
| `global.storageClass` | Storage class for PVs | `standard` |
| `global.environment` | Deployment environment | `production` |
| `global.domain` | Base domain for ingress | `ugc.grc-claw.local` |

### Default Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `defaults.replicaCount` | Default replica count | `2` |
| `defaults.service.type` | Service type | `ClusterIP` |
| `defaults.service.port` | Service port | `8080` |
| `defaults.ingress.enabled` | Enable ingress | `true` |
| `defaults.ingress.className` | Ingress class | `nginx` |
| `defaults.autoscaling.enabled` | Enable HPA | `true` |
| `defaults.autoscaling.minReplicas` | Min replicas | `2` |
| `defaults.autoscaling.maxReplicas` | Max replicas | `10` |

### Per-Project Overrides

Each project in the `projects` array can override any default value. See `values.yaml` for examples.

## Security

- All containers run as non-root (UID 1000)
- Read-only root filesystem
- Dropped Linux capabilities
- Network policies restrict traffic
- Pod security standards enforced
- Secrets stored in Kubernetes Secrets

## Monitoring

- Prometheus metrics endpoint on port 9090
- Health check endpoints: `/health`, `/ready`
- Configurable liveness, readiness, and startup probes

## Scaling

- Horizontal Pod Autoscaler (HPA) for all services
- Pod Disruption Budgets for availability
- Rolling update strategy with zero downtime
- Topology spread constraints for zone distribution

## License

Apache 2.0

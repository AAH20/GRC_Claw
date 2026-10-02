# Gated Communities Helm Chart

## Overview

This Helm chart deploys 10 gated community microservices for GRC_Claw. It provides a complete, production-grade deployment solution for exclusive community platforms with configurable access control, membership management, security, monitoring, and high availability.

## Projects Included

| # | Project | Description |
|---|---------|-------------|
| 1 | access-control | Role-based access control and permissions management |
| 2 | membership-manager | Community membership lifecycle and tier management |
| 3 | community-forums | Discussion forums with moderation and threading |
| 4 | exclusive-content | Gated content delivery and digital rights management |
| 5 | community-analytics | Community engagement metrics and insights |
| 6 | invite-system | Invitation management and referral tracking |
| 7 | payment-gateway | Subscription payments and billing management |
| 8 | moderation-tools | Community moderation and content flagging |
| 9 | event-manager | Community events, webinars, and meetups |
| 10 | notification-service | Community notifications and announcements |

## Prerequisites

- Kubernetes 1.24+
- Helm 3.12+
- cert-manager (for TLS certificates)
- nginx-ingress controller
- Prometheus Operator (for metrics)

## Installation

```bash
# Install the chart
helm install gated-communities ./infrastructure/helm/gated-communities \
  --namespace communities \
  --create-namespace

# Or with custom values
helm install gated-communities ./infrastructure/helm/gated-communities \
  --namespace communities \
  --create-namespace \
  -f custom-values.yaml
```

## Upgrading

```bash
helm upgrade gated-communities ./infrastructure/helm/gated-communities \
  --namespace communities
```

## Uninstallation

```bash
helm uninstall gated-communities --namespace communities
```

## Configuration

### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.imageRegistry` | Docker image registry | `ghcr.io/ahmedhassan/grc-claw` |
| `global.imagePullSecrets` | Image pull secrets | `[]` |
| `global.storageClass` | Storage class for PVs | `standard` |
| `global.environment` | Deployment environment | `production` |
| `global.domain` | Base domain for ingress | `communities.grc-claw.local` |

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
- RBAC access control
- Content protection and DRM

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

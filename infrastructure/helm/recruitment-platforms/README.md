# Recruitment Platforms Helm Chart

## Overview

This Helm chart deploys 10 recruitment platform microservices for GRC_Claw. It provides a complete, production-grade deployment solution with configurable scaling, security, monitoring, and high availability.

## Projects Included

| # | Project | Description |
|---|---------|-------------|
| 1 | job-board | Public job listing and search platform |
| 2 | applicant-tracker | End-to-end applicant tracking and pipeline management |
| 3 | candidate-sourcing | AI-powered candidate discovery and outreach |
| 4 | interview-scheduler | Automated interview scheduling and calendar sync |
| 5 | recruitment-analytics | Recruitment metrics, dashboards, and reporting |
| 6 | resume-parser | AI resume parsing and skill extraction |
| 7 | offer-management | Offer letter generation and approval workflow |
| 8 | onboarding-portal | New hire onboarding and document management |
| 9 | referral-engine | Employee referral tracking and rewards |
| 10 | compliance-checker | Background checks and compliance verification |

## Prerequisites

- Kubernetes 1.24+
- Helm 3.12+
- cert-manager (for TLS certificates)
- nginx-ingress controller
- Prometheus Operator (for metrics)

## Installation

```bash
# Install the chart
helm install recruitment-platforms ./infrastructure/helm/recruitment-platforms \
  --namespace recruitment \
  --create-namespace

# Or with custom values
helm install recruitment-platforms ./infrastructure/helm/recruitment-platforms \
  --namespace recruitment \
  --create-namespace \
  -f custom-values.yaml
```

## Upgrading

```bash
helm upgrade recruitment-platforms ./infrastructure/helm/recruitment-platforms \
  --namespace recruitment
```

## Uninstallation

```bash
helm uninstall recruitment-platforms --namespace recruitment
```

## Configuration

### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.imageRegistry` | Docker image registry | `ghcr.io/ahmedhassan/grc-claw` |
| `global.imagePullSecrets` | Image pull secrets | `[]` |
| `global.storageClass` | Storage class for PVs | `standard` |
| `global.environment` | Deployment environment | `production` |
| `global.domain` | Base domain for ingress | `recruitment.grc-claw.local` |

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

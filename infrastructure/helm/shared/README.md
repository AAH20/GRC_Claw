# Shared Infrastructure Helm Chart

## Overview

This Helm chart deploys shared infrastructure services for GRC_Claw. It provides common services used across all domains including ingress control, certificate management, monitoring, service mesh, databases, caching, object storage, and log aggregation.

## Components

| Component | Description |
|-----------|-------------|
| Ingress Controller | NGINX ingress for external traffic |
| Cert Manager | Automatic TLS certificate management |
| Prometheus | Metrics collection and alerting |
| Grafana | Visualization and dashboards |
| Alertmanager | Alert routing and notification |
| PostgreSQL | Shared relational database |
| Redis | Shared caching layer |
| MinIO | S3-compatible object storage |
| Loki | Log aggregation |

## Prerequisites

- Kubernetes 1.24+
- Helm 3.12+

## Installation

```bash
# Install the chart
helm install shared ./infrastructure/helm/shared \
  --namespace infrastructure \
  --create-namespace

# Or with custom values
helm install shared ./infrastructure/helm/shared \
  --namespace infrastructure \
  --create-namespace \
  -f custom-values.yaml
```

## Upgrading

```bash
helm upgrade shared ./infrastructure/helm/shared \
  --namespace infrastructure
```

## Uninstallation

```bash
helm uninstall shared --namespace infrastructure
```

## Configuration

### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.environment` | Deployment environment | `production` |
| `global.domain` | Base domain | `grc-claw.local` |
| `global.imageRegistry` | Docker image registry | `ghcr.io/ahmedhassan/grc-claw` |
| `global.storageClass` | Storage class for PVs | `standard` |

### Monitoring

| Parameter | Description | Default |
|-----------|-------------|---------|
| `monitoring.prometheus.retention` | Metrics retention period | `15d` |
| `monitoring.prometheus.storage` | Prometheus storage size | `10Gi` |
| `monitoring.grafana.adminPassword` | Grafana admin password | `admin` |
| `monitoring.grafana.storage` | Grafana storage size | `5Gi` |

### Database

| Parameter | Description | Default |
|-----------|-------------|---------|
| `database.type` | Database type | `postgresql` |
| `database.version` | PostgreSQL version | `15` |
| `database.storage` | Database storage size | `20Gi` |
| `database.config.maxConnections` | Max connections | `100` |

## Security

- Network policies restrict traffic
- Pod security standards enforced
- Secrets stored in Kubernetes Secrets
- TLS via cert-manager
- Non-root container execution

## License

Apache 2.0

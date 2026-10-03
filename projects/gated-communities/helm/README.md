# Gated Communities Helm Chart

Production-grade Helm chart for deploying the Gated Communities unified platform on Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- cert-manager (for TLS certificates)
- nginx-ingress controller
- Metrics server (for HPA)

## Installation

### Add the chart directory

```bash
cd ~/GRC_Claw/projects/gated-communities/helm
```

### Install with default values

```bash
helm install gated-communities . -n gated-communities --create-namespace
```

### Install with custom values

```bash
helm install gated-communities . -n gated-communities --create-namespace -f values-production.yaml
```

### Install with specific overrides

```bash
helm install gated-communities . -n gated-communities --create-namespace \
  --set image.tag=v1.2.3 \
  --set replicaCount=5 \
  --set secrets.database-url="postgresql://user:pass@db-host:5432/gated_communities" \
  --set secrets.llm-api-key="sk-..." \
  --set ingress.hosts[0].host="api.yourdomain.com"
```

## Upgrading

```bash
helm upgrade gated-communities . -n gated-communities -f values-production.yaml
```

## Uninstalling

```bash
helm uninstall gated-communities -n gated-communities
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas (when HPA disabled) | `3` |
| `image.repository` | Container image repository | `gated-communities` |
| `image.tag` | Container image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `80` |
| `service.targetPort` | Container target port | `8000` |
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts[0].host` | Ingress hostname | `api.gated-communities.example.com` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `250m` |
| `resources.requests.memory` | Memory request | `256Mi` |
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Minimum replicas | `2` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `autoscaling.targetCPUUtilizationPercentage` | CPU target | `70` |
| `autoscaling.targetMemoryUtilizationPercentage` | Memory target | `80` |
| `pdb.enabled` | Enable Pod Disruption Budget | `true` |
| `pdb.minAvailable` | Minimum available pods | `1` |
| `config.LOG_LEVEL` | Logging level | `INFO` |
| `config.ENVIRONMENT` | Environment name | `production` |
| `secrets.database-url` | PostgreSQL connection string | (see values.yaml) |
| `secrets.redis-url` | Redis connection string | (see values.yaml) |
| `secrets.llm-api-key` | LLM API key | (empty) |
| `secrets.secret-key` | Application secret key | (see values.yaml) |

## Production Checklist

- [ ] Override all secrets with real values
- [ ] Set proper ingress hostname
- [ ] Configure cert-manager ClusterIssuer
- [ ] Set appropriate resource limits for your workload
- [ ] Configure HPA thresholds based on load testing
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy for PostgreSQL
- [ ] Enable network policies
- [ ] Set up log aggregation
- [ ] Configure PodDisruptionBudget
- [ ] Test rolling updates and rollbacks

## Building and Pushing the Image

```bash
docker build -t your-registry/gated-communities:v1.0.0 .
docker push your-registry/gated-communities:v1.0.0
```

Then update `image.repository` and `image.tag` in values.yaml or via `--set`.

## Chart Structure

```
helm/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Default values
├── README.md           # This file
└── templates/
    ├── _helpers.tpl    # Named templates
    ├── deployment.yaml # Backend deployment
    ├── service.yaml    # Backend service
    ├── ingress.yaml    # Ingress configuration
    ├── configmap.yaml  # Application config
    ├── secret.yaml     # Secrets template
    ├── hpa.yaml        # Horizontal Pod Autoscaler
    ├── serviceaccount.yaml # Service account
    └── pdb.yaml        # Pod Disruption Budget
```

# GRC_Claw Deployment Implementation Guide

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Production Ready  
**References:** grc-claw-deployment-spec.md v2.0, grc-claw-scalability-spec.md v2.0

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start
5. [Component Deployment](#component-deployment)
6. [Service Mesh (Istio)](#service-mesh-istio)
7. [Monitoring Stack](#monitoring-stack)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Disaster Recovery](#disaster-recovery)
10. [Security](#security)
11. [Operations](#operations)
12. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides complete implementation details for deploying GRC_Claw — an AI Governance, Risk, and Compliance enforcement platform — in production Kubernetes environments.

### What's Included

| Section | Contents |
|---------|----------|
| Dockerfiles | 12 component Dockerfiles (distroless, non-root, multi-stage) |
| Kubernetes Manifests | Deployments, Services, ConfigMaps, Secrets, PDBs, HPAs, NetworkPolicies |
| Helm Chart | Complete chart with values for dev/staging/production |
| Istio Config | mTLS, traffic management, rate limiting, authorization |
| Monitoring | Prometheus, Grafana, Loki, Alertmanager, OTel Collector |
| CI/CD | GitHub Actions workflows, ArgoCD ApplicationSets, Rollouts |
| DR | Failover runbooks, backup CronJobs, cross-region replication |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ingress (Istio Gateway)                   │
│                    TLS termination, WAF, rate limiting            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     API Gateway (Kong/Envoy)                     │
│              AuthN (OAuth 2.1/OIDC), AuthZ, routing              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      Service Mesh (Istio)                        │
│           mTLS, traffic management, observability                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                    Microservices Layer                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Policy   │ │ PDP      │ │ PEP      │ │ Agent    │          │
│  │ API      │ │ Service  │ │ Gateway  │ │ Identity │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Evidence │ │Compliance│ │Analytics │ │Reporting │          │
│  │Collector │ │ Mapping  │ │ Engine   │ │ Engine   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      Data Layer (StatefulSets)                   │
│  PostgreSQL │ Redis │ Kafka │ MinIO │ Neo4j │ immudb │ Vault    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Required Tools

```bash
# Kubernetes CLI
kubectl version --client  # >= 1.28

# Helm
helm version  # >= 3.13

# Istio
istioctl version  # >= 1.20

# ArgoCD
argocd version  # >= 2.9

# Additional tools
kubeval --version
conftest --version
cosign version
```

### Cluster Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Nodes | 10 | 30-50 |
| vCPU | 40 | 200 |
| Memory | 160 GB | 800 GB |
| Storage | 1 TB | 50 TB |
| Kubernetes | 1.28 | 1.29+ |
| CNI | Calico/Cilium | Cilium |

### Supported Platforms

- **AWS**: EKS 1.28+
- **GCP**: GKE 1.28+
- **Azure**: AKS 1.28+
- **On-premises**: Rancher, OpenShift

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/grc-claw/grc-claw-deployment.git
cd grc-claw-deployment
```

### 2. Install Helm Dependencies

```bash
cd helm/grc-claw
helm dependency update
```

### 3. Deploy to Development

```bash
helm install grc-claw . \
  --namespace grc-claw \
  --create-namespace \
  --values values-development.yaml
```

### 4. Deploy to Staging

```bash
helm install grc-claw . \
  --namespace grc-claw \
  --create-namespace \
  --values values-staging.yaml
```

### 5. Deploy to Production

```bash
helm install grc-claw . \
  --namespace grc-claw \
  --create-namespace \
  --values values-production.yaml
```

### 6. Verify Deployment

```bash
kubectl get pods -n grc-claw-control-plane
kubectl get pods -n grc-claw-evidence
kubectl get pods -n grc-claw-analytics
kubectl get pods -n grc-claw-data
kubectl get svc -n grc-claw-control-plane
```

---

## Component Deployment

### Docker Images

All components use distroless base images with non-root user (UID 65534):

| Component | Dockerfile | Base Image | Port |
|-----------|-----------|------------|------|
| Policy API | `dockerfiles/policy-api/Dockerfile` | distroless/python3-debian12 | 8080 |
| PDP Service | `dockerfiles/pdp-service/Dockerfile` | distroless/static-debian12 | 8080, 9090 |
| PEP Gateway | `dockerfiles/pep-gateway/Dockerfile` | distroless/static-debian12 | 8080, 9090 |
| Agent Identity | `dockerfiles/agent-identity/Dockerfile` | distroless/static-debian12 | 8080 |
| Evidence Collector | `dockerfiles/evidence-collector/Dockerfile` | distroless/python3-debian12 | 8080 |
| Compliance Mapping | `dockerfiles/compliance-mapping/Dockerfile` | distroless/python3-debian12 | 8080 |
| Analytics Engine | `dockerfiles/analytics-engine/Dockerfile` | distroless/python3-debian12 | 8080 |
| Reporting Engine | `dockerfiles/reporting-engine/Dockerfile` | distroless/python3-debian12 | 8080 |
| Discovery Engine | `dockerfiles/discovery-engine/Dockerfile` | distroless/static-debian12 | 8080 |
| Risk Assessment | `dockerfiles/risk-assessment/Dockerfile` | distroless/python3-debian12 | 8080 |
| Approval Workflow | `dockerfiles/approval-workflow/Dockerfile` | distroless/static-debian12 | 8080 |
| OTel Collector | `dockerfiles/otel-collector/Dockerfile` | otel/opentelemetry-collector-contrib | 4317, 4318, 8888 |

### Build and Push

```bash
# Build all images
for dir in docker/*/; do
  component=$(basename "$dir")
  docker build -t ghcr.io/grc-claw/$component:latest -f "$dir/Dockerfile" "$dir"
  docker push ghcr.io/grc-claw/$component:latest
done
```

### Kubernetes Manifests

Apply manifests directly (without Helm):

```bash
# Namespaces
kubectl apply -f kubernetes/namespaces.yaml

# ConfigMaps and Secrets
kubectl apply -f kubernetes/configmaps.yaml
kubectl apply -f kubernetes/secrets.yaml

# Network Policies
kubectl apply -f kubernetes/network-policies.yaml

# Resource Quotas
kubectl apply -f kubernetes/resource-quotas.yaml

# Control Plane
kubectl apply -f kubernetes/control-plane/

# Evidence
kubectl apply -f kubernetes/evidence/

# Analytics
kubectl apply -f kubernetes/analytics/

# Data Layer
kubectl apply -f kubernetes/data/
```

### Helm Chart Structure

```
helm/grc-claw/
├── Chart.yaml
├── values.yaml                 # Default values
├── values-production.yaml      # Production overrides
├── values-staging.yaml         # Staging overrides
├── values-development.yaml     # Development overrides
└── templates/
    ├── _helpers.tpl            # Common templates
    ├── control-plane/
    │   ├── policy-api/
    │   ├── pdp-service/
    │   ├── pep-gateway/
    │   └── agent-identity/
    ├── evidence/
    │   ├── collector/
    │   └── compliance-mapping/
    ├── analytics/
    │   ├── engine/
    │   └── reporting/
    ├── observability/
    │   ├── otel-collector/
    │   ├── prometheus/
    │   ├── grafana/
    │   └── loki/
    └── data/
        ├── postgresql/
        ├── redis/
        ├── kafka/
        ├── minio/
        ├── neo4j/
        ├── immudb/
        └── vault/
```

---

## Service Mesh (Istio)

### Installation

```bash
# Install Istio with IstioOperator
istioctl install --set profile=default -y

# Enable sidecar injection for all GRC_Claw namespaces
kubectl label namespace grc-claw-control-plane istio-injection=enabled
kubectl label namespace grc-claw-evidence istio-injection=enabled
kubectl label namespace grc-claw-analytics istio-injection=enabled
kubectl label namespace grc-claw-data istio-injection=enabled
```

### mTLS Configuration

All service-to-service communication uses STRICT mTLS:

```bash
# Apply PeerAuthentication
kubectl apply -f istio/peer-authentication.yaml

# Apply DestinationRules
kubectl apply -f istio/destination-rules.yaml
```

### Traffic Management

Canary deployments with automatic rollback:

```bash
# Apply VirtualServices
kubectl apply -f istio/virtual-services.yaml

# Apply Ingress Gateway
kubectl apply -f istio/ingress-gateway.yaml
```

### Authorization

Fine-grained access control between services:

```bash
kubectl apply -f istio/authorization-policies.yaml
```

### Rate Limiting

Per-tenant rate limiting at the mesh level:

```bash
kubectl apply -f istio/rate-limiting.yaml
```

### Observability

Distributed tracing and metrics collection:

```bash
kubectl apply -f istio/telemetry.yaml
```

---

## Monitoring Stack

### Prometheus

```bash
# Apply Prometheus configuration
kubectl apply -f monitoring/prometheus/prometheus-config.yaml
kubectl apply -f monitoring/prometheus/alert-rules.yaml
kubectl apply -f monitoring/prometheus/alertmanager-config.yaml
```

### Grafana

```bash
# Apply Grafana dashboards
kubectl apply -f monitoring/grafana/dashboards/
kubectl apply -f monitoring/grafana/provisioning.yaml
```

### Loki

```bash
# Apply Loki configuration
kubectl apply -f monitoring/loki/loki-config.yaml
kubectl apply -f monitoring/loki/promtail-config.yaml
```

### Key Dashboards

| Dashboard | File | Purpose |
|----------|------|---------|
| Enforcement | `monitoring/grafana/dashboards/enforcement.json` | Real-time decisions, latency, errors |
| Data Pipeline | `monitoring/grafana/dashboards/data-pipeline.json` | Evidence ingestion, consumer lag |
| Capacity | `monitoring/grafana/dashboards/capacity.json` | Resource utilization, scaling events |

### Alerting

| Severity | Condition | Response |
|----------|-----------|----------|
| P1 Critical | Enforcement down, data loss risk | Page on-call immediately |
| P2 High | p99 > 50ms, error rate > 1% | Page on-call within 15 min |
| P3 Medium | p99 > 20ms, disk > 80% | Slack alert, next business day |
| P4 Low | Disk > 70%, cert expiry < 30 days | Slack alert, weekly review |

---

## CI/CD Pipeline

### GitHub Actions Workflows

| Workflow | File | Trigger |
|----------|------|---------|
| Docker Build | `cicd/github-actions/docker-build.yml` | Push to main/develop, tags |
| PR Validation | `cicd/github-actions/pr-validation.yml` | Pull requests |
| Security Scan | `cicd/github-actions/security-scan.yml` | Daily schedule |

### ArgoCD Configuration

```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Apply AppProject
kubectl apply -f cicd/argocd/appproject.yaml

# Apply ApplicationSets
kubectl apply -f cicd/argocd/applicationset-control-plane.yaml
kubectl apply -f cicd/argocd/applicationset-evidence.yaml
kubectl apply -f cicd/argocd/applicationset-analytics.yaml
kubectl apply -f cicd/argocd/applicationset-data.yaml
kubectl apply -f cicd/argocd/applicationset-observability.yaml
```

### Progressive Delivery

#### Canary Deployment (PDP Service)

```bash
kubectl apply -f cicd/argocd/rollout-pdp.yaml
```

Steps: 5% → 20% → 50% → 100% with automated analysis

#### Canary Deployment (PEP Gateway)

```bash
kubectl apply -f cicd/argocd/rollout-pep.yaml
```

Steps: 10% → 50% → 100% with automated analysis

#### Blue-Green Deployment (Policy API)

```bash
kubectl apply -f cicd/argocd/rollout-policy-api.yaml
```

### External Secrets

```bash
kubectl apply -f cicd/argocd/external-secrets.yaml
```

---

## Disaster Recovery

### DR Architecture

- **Primary Region**: us-east-1 (active)
- **DR Region**: us-west-2 (standby)
- **Replication**: Cross-region for all data stores
- **RTO**: < 4 hours
- **RPO**: < 5 minutes (critical data)

### Failover Procedures

See `dr/runbook-failover.md` for detailed procedures.

### Backup Schedule

| Data Store | Frequency | Retention | CronJob |
|-----------|-----------|-----------|---------|
| PostgreSQL | Daily | 30 days | `postgresql-backup` |
| Redis | Every 6 hours | 7 days | `redis-backup` |
| immudb | Daily | 90 days | `immudb-backup` |
| Vault | Daily | 30 days | `vault-snapshot` |
| etcd | Every 6 hours | 30 days | `etcd-snapshot` |

```bash
kubectl apply -f dr/backup-cronjobs.yaml
```

### Cross-Region Replication

```bash
kubectl apply -f dr/cross-region-replication.yaml
```

### DR Health Checks

```bash
kubectl apply -f dr/health-checks.yaml
```

---

## Security

### Image Security

- All images built with distroless base images
- Non-root user (UID 65534)
- Read-only root filesystem
- No privilege escalation
- All capabilities dropped
- Cosign signing at build time
- Trivy vulnerability scanning in CI

### Network Security

- Istio mTLS (STRICT mode) for all service-to-service communication
- Kubernetes NetworkPolicies for micro-segmentation
- Egress filtering via Istio Egress Gateway
- Private subnets for data layer (no public IPs)

### Secret Management

- HashiCorp Vault for all secrets
- External Secrets Operator for K8s integration
- Automatic rotation:
  - mTLS certificates: 24 hours
  - API tokens: 7 days
  - Database credentials: 30 days
  - Encryption keys: 90 days

### Pod Security

- Pod Security Standards: restricted
- SecurityContext on all containers
- Resource quotas per namespace
- LimitRanges for default resource limits

---

## Operations

### Scaling

#### Horizontal Pod Autoscaling

| Component | Min | Max | Metric |
|-----------|-----|-----|--------|
| PDP Service | 3 | 20 | CPU > 70% or p99 > 15ms |
| PEP Gateway | 3 | 20 | CPU > 70% or p99 > 20ms |
| Policy API | 3 | 10 | CPU > 70% |
| Evidence Collector | 3 | 15 | Queue > 10K |
| Analytics Engine | 2 | 8 | CPU > 70% |

#### Vertical Pod Autoscaling

Used for stateful services (PostgreSQL, Redis, Kafka).

#### Cluster Autoscaling

Karpenter NodePool for automatic node provisioning.

### Health Checks

| Check | Endpoint | Interval | Timeout | Failure Threshold |
|-------|----------|----------|---------|-------------------|
| Liveness | `/healthz` | 10s | 5s | 3 |
| Readiness | `/readyz` | 5s | 3s | 3 |
| Startup | `/startz` | 5s | 30s | 6 |
| Deep health | `/deepz` | 60s | 10s | 3 |

### SLOs

| Service | SLO | Error Budget |
|---------|-----|-------------|
| PDP Service | 99.95% | 21.9 min/month |
| PEP Gateway | 99.95% | 21.9 min/month |
| Policy API | 99.9% | 43.8 min/month |
| Evidence Collection | 99.9% | 43.8 min/month |
| Overall Platform | 99.9% | 43.8 min/month |

---

## Troubleshooting

### Common Issues

#### Pod Stuck in Pending

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

#### Service Unavailable

```bash
kubectl get endpoints -n <namespace> <service-name>
istioctl proxy-config endpoints <pod-name> -n <namespace>
```

#### High Latency

```bash
# Check Istio metrics
istioctl dashboard envoy <pod-name> -n <namespace>

# Check distributed traces
istioctl dashboard jaeger
```

#### Certificate Issues

```bash
kubectl get certificates -A
kubectl describe certificate <cert-name> -n <namespace>
```

### Useful Commands

```bash
# View all GRC_Claw resources
kubectl get all -n grc-claw-control-plane
kubectl get all -n grc-claw-evidence
kubectl get all -n grc-claw-analytics
kubectl get all -n grc-claw-data

# View Istio configuration
istioctl analyze -n grc-claw-control-plane
istioctl proxy-config routes deploy/pdp-service -n grc-claw-control-plane

# View ArgoCD applications
argocd app list
argocd app get grc-claw-control-plane-prod-us-east-1

# View logs
kubectl logs -f deployment/pdp-service -n grc-claw-control-plane
kubectl logs -f deployment/pep-gateway -n grc-claw-control-plane

# Port-forward for local access
kubectl port-forward svc/grafana 3000:3000 -n grc-claw-observability
kubectl port-forward svc/prometheus 9090:9090 -n grc-claw-observability
```

---

## File Reference

### Dockerfiles

- `docker/policy-api/Dockerfile`
- `docker/pdp-service/Dockerfile`
- `docker/pep-gateway/Dockerfile`
- `docker/agent-identity/Dockerfile`
- `docker/evidence-collector/Dockerfile`
- `docker/compliance-mapping/Dockerfile`
- `docker/analytics-engine/Dockerfile`
- `docker/reporting-engine/Dockerfile`
- `docker/discovery-engine/Dockerfile`
- `docker/risk-assessment/Dockerfile`
- `docker/approval-workflow/Dockerfile`
- `docker/otel-collector/Dockerfile`

### Kubernetes Manifests

- `kubernetes/namespaces.yaml`
- `kubernetes/configmaps.yaml`
- `kubernetes/secrets.yaml`
- `kubernetes/network-policies.yaml`
- `kubernetes/resource-quotas.yaml`
- `kubernetes/control-plane/pdp-deployment.yaml`
- `kubernetes/control-plane/pep-gateway.yaml`
- `kubernetes/control-plane/policy-api.yaml`
- `kubernetes/control-plane/agent-identity.yaml`
- `kubernetes/evidence/collector.yaml`
- `kubernetes/evidence/compliance-mapping.yaml`
- `kubernetes/analytics/engine.yaml`
- `kubernetes/analytics/reporting.yaml`
- `kubernetes/data/postgresql.yaml`
- `kubernetes/data/redis.yaml`
- `kubernetes/data/kafka.yaml`
- `kubernetes/data/minio.yaml`
- `kubernetes/data/immudb.yaml`
- `kubernetes/data/vault.yaml`

### Helm Chart

- `helm/grc-claw/Chart.yaml`
- `helm/grc-claw/values.yaml`
- `helm/grc-claw/values-production.yaml`
- `helm/grc-claw/values-staging.yaml`
- `helm/grc-claw/values-development.yaml`
- `helm/grc-claw/templates/_helpers.tpl`
- `helm/grc-claw/templates/control-plane/policy-api/deployment.yaml`
- `helm/grc-claw/templates/control-plane/pdp-service/deployment.yaml`
- `helm/grc-claw/templates/control-plane/pep-gateway/deployment.yaml`
- `helm/grc-claw/templates/control-plane/agent-identity/deployment.yaml`
- `helm/grc-claw/templates/evidence/collector/deployment.yaml`
- `helm/grc-claw/templates/evidence/compliance-mapping/deployment.yaml`
- `helm/grc-claw/templates/analytics/engine/deployment.yaml`
- `helm/grc-claw/templates/analytics/reporting/deployment.yaml`
- `helm/grc-claw/templates/observability/otel-collector/deployment.yaml`
- `helm/grc-claw/templates/observability/prometheus/deployment.yaml`
- `helm/grc-claw/templates/observability/grafana/deployment.yaml`
- `helm/grc-claw/templates/observability/loki/deployment.yaml`

### Istio Configuration

- `istio/peer-authentication.yaml`
- `istio/destination-rules.yaml`
- `istio/virtual-services.yaml`
- `istio/ingress-gateway.yaml`
- `istio/egress-gateway.yaml`
- `istio/authorization-policies.yaml`
- `istio/rate-limiting.yaml`
- `istio/telemetry.yaml`

### Monitoring

- `monitoring/prometheus/prometheus-config.yaml`
- `monitoring/prometheus/alert-rules.yaml`
- `monitoring/prometheus/alertmanager-config.yaml`
- `monitoring/grafana/dashboards/enforcement.json`
- `monitoring/grafana/dashboards/data-pipeline.json`
- `monitoring/grafana/dashboards/capacity.json`
- `monitoring/grafana/provisioning.yaml`
- `monitoring/loki/loki-config.yaml`
- `monitoring/loki/promtail-config.yaml`

### CI/CD

- `cicd/github-actions/docker-build.yml`
- `cicd/github-actions/pr-validation.yml`
- `cicd/github-actions/security-scan.yml`
- `cicd/argocd/appproject.yaml`
- `cicd/argocd/applicationset-control-plane.yaml`
- `cicd/argocd/applicationset-evidence.yaml`
- `cicd/argocd/applicationset-analytics.yaml`
- `cicd/argocd/applicationset-data.yaml`
- `cicd/argocd/applicationset-observability.yaml`
- `cicd/argocd/external-secrets.yaml`
- `cicd/argocd/rollout-pdp.yaml`
- `cicd/argocd/rollout-pep.yaml`
- `cicd/argocd/rollout-policy-api.yaml`

### Disaster Recovery

- `dr/runbook-failover.md`
- `dr/backup-cronjobs.yaml`
- `dr/cross-region-replication.yaml`
- `dr/health-checks.yaml`

---

## License

Proprietary — GRC_Claw Project

# GRC_Claw — Local Development Guide

## Overview

This guide covers three ways to run GRC_Claw locally for development:

| Method | Best For | Live Reload | K8s Native |
|--------|----------|-------------|------------|
| **Docker Compose** | Quick start, data layer | No | No |
| **Tilt** | Fastest inner loop | Yes | Yes |
| **Skaffold** | CI-like dev, multi-service | Yes | Yes |

---

## Prerequisites

### Required

- **Docker** 24+ with Compose v2
- **kubectl** 1.28+
- **Helm** 3.14+ (for chart-based dev)

### For Tilt/Skaffold (K8s dev)

- **kind** or **minikube** (local K8s cluster)
- **Tilt** v0.30+ (`brew install tilt`)
- **Skaffold** v2+ (`brew install skaffold`)

### For Go services

- **Go** 1.22+
- **Delve** (for debug mode)

### For Python services

- **Python** 3.11+
- **uvicorn** (for live reload)

### For Node.js gateway

- **Node.js** 20+
- **npm** 10+

---

## Quick Start — Docker Compose

The fastest way to get running. Starts all services with a single command.

```bash
cd ~/GRC_Claw/deployment

# Copy environment template
cp .env.example .env.local

# Start everything
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop
docker compose down

# Stop and wipe all data
docker compose down -v
```

### Access Points (Docker Compose)

| Service | URL | Credentials |
|---------|-----|-------------|
| Gateway | http://localhost:18791 | Token: `dev-gateway-token` |
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | — |
| Jaeger | http://localhost:16686 | — |
| MinIO | http://localhost:9000 | minioadmin/minioadmin |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin |
| Vault | http://localhost:8200 | Token: `dev-root-token` |
| PostgreSQL | localhost:5432 | grc_claw/grc_claw_dev_password |
| Redis | localhost:6379 | — |
| Kafka | localhost:9092 | — |

---

## Quick Start — Tilt (Recommended for Development)

Tilt provides the fastest inner loop: edit code → auto-rebuild → auto-deploy to K8s.

```bash
# 1. Create a kind cluster
kind create cluster --name grc-claw --config kind-config.yaml

# 2. Verify context
kubectl config current-context
# Should output: kind-grc-claw

# 3. Copy environment template
cp .env.example .env.local

# 4. Start Tilt
cd ~/GRC_Claw/deployment
tilt up

# 5. Open Tilt UI
# Press 's' in terminal or open http://localhost:10350
```

### Tilt UI

The Tilt UI shows all resources grouped by tier:

- **Data Layer**: PostgreSQL, Redis, Kafka, MinIO, Vault
- **Control Plane**: Policy API, PDP, PEP Gateway, Agent Identity
- **Analytics**: Analytics Engine, Reporting Engine
- **Evidence**: Collector, Validator, Compliance Mapping
- **Observability**: Prometheus, Grafana, Jaeger, Loki, OTel

### Live Reload

Tilt automatically detects file changes and rebuilds:

- **Python services**: Sync → `pip install` → restart container
- **Go services**: Sync → `go build` → restart container
- **Gateway (Node.js)**: Sync → `npm run build` → restart container

### Tilt Commands

```bash
tilt up              # Start Tilt UI + live-reload
tilt up policy-api   # Only start specific resource
tilt down            # Tear down
tilt ci              # CI mode (no UI, fail on error)
tilt doctor          # Diagnose issues
```

---

## Quick Start — Skaffold

Skaffold provides a CI-like dev loop with port-forwarding.

```bash
# 1. Create a kind cluster
kind create cluster --name grc-claw

# 2. Copy environment template
cp .env.example .env.local

# 3. Start Skaffold dev loop
cd ~/GRC_Claw/deployment
skaffold dev

# 4. Or deploy once
skaffold run

# 5. Debug mode (with delve for Go services)
skaffold debug

# 6. Clean up
skaffold delete
```

### Skaffold Profiles

```bash
# Minimal — only data layer + gateway
skaffold dev -p minimal

# Control plane only
skaffold dev -p control-plane

# Debug mode — with delve for Go services
skaffold dev -p debug
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ingress / Gateway                         │
│                    grc-claw-gateway :18791                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                    Control Plane Services                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Policy   │ │ PDP      │ │ PEP      │ │ Agent    │          │
│  │ API :8081│ │ :8082    │ │ :8083    │ │ :8084    │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                    Analytics Services                            │
│  ┌──────────┐ ┌──────────┐                                      │
│  │Analytics │ │Reporting │                                      │
│  │ :8085    │ │ :8086    │                                      │
│  └──────────┘ └──────────┘                                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                    Evidence Services                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │Collector │ │Validator │ │Compliance│                        │
│  │ :8087    │ │ :8088    │ │ :8089    │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      Data Layer                                  │
│  PostgreSQL :5432 │ Redis :6379 │ Kafka :9092 │ MinIO :9000    │
│  Vault :8200                                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Environment Variables

Copy `.env.example` to `.env.local` and customize:

```bash
cp .env.example .env.local
```

Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GRC_CLAW_GATEWAY_TOKEN` | `dev-gateway-token` | Gateway auth token |
| `A2Z_SOC_MODE` | `demo` | SOC mode (demo/prod) |
| `A2Z_SOC_BASE_URL` | `http://host.docker.internal:3000` | SOC API URL |
| `DATABASE_URL` | `postgresql+asyncpg://grc_claw:...@postgres:5432/grc_claw` | PostgreSQL |
| `REDIS_URL` | `redis://redis:6379/0` | Redis |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | Kafka |
| `VAULT_ADDR` | `http://vault:8200` | Vault |
| `VAULT_TOKEN` | `dev-root-token` | Vault dev token |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4318` | OTel |

See `.env.example` for the full list.

---

## Development Workflows

### Adding a New Python Service

1. Create `deployment/docker/my-service/Dockerfile`
2. Add to `docker-compose.yml` under `services:`
3. Add to `skaffold.yaml` under `build.artifacts`
4. Add to `Tiltfile` with `custom_build`
5. Create K8s manifests in `deployment/grc-claw-deployment/kubernetes/`

### Adding a New Go Service

1. Create `deployment/docker/my-service/Dockerfile`
2. Add to `docker-compose.yml` under `services:`
3. Add to `skaffold.yaml` under `build.artifacts`
4. Add to `Tiltfile` with `custom_build`
5. Create K8s manifests in `deployment/grc-claw-deployment/kubernetes/`

### Adding a New K8s Manifest

1. Create YAML in the appropriate `kubernetes/` subdirectory
2. Add the path to `skaffold.yaml` under `deploy.kubectl.manifests`
3. Add the path to `Tiltfile` under `k8s_yaml`

---

## Debugging

### Python Services

```bash
# Attach to running container
docker compose exec policy-api python -m pdb

# Or with debugpy
docker compose exec policy-api python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app
```

### Go Services

```bash
# With Skaffold debug mode
skaffold debug

# Or attach delve manually
kubectl port-forward deployment/pdp-service 2345:2345
dlv connect localhost:2345
```

### Gateway (Node.js)

```bash
# Node inspector
docker compose exec grc-claw-gateway node --inspect=0.0.0.0:9229 packages/gateway/dist/cli.js
```

---

## Testing

```bash
# Run all tests
cd ~/GRC_Claw
npm run test:all

# Run specific package tests
npm run test -w @grc-claw/policy-api

# Run integration tests
docker compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit
```

---

## Troubleshooting

### Port Conflicts

If ports are already in use, edit `docker-compose.yml` or `.env.local`:

```bash
# Change host port mapping
ports:
  - "18792:18791"  # Gateway on 18792 instead of 18791
```

### Kind Cluster Issues

```bash
# Delete and recreate
kind delete cluster --name grc-claw
kind create cluster --name grc-claw --config kind-config.yaml

# Check cluster
kubectl cluster-info --context kind-grc-claw
```

### Tilt Not Detecting Changes

```bash
# Restart Tilt
tilt down
tilt up

# Check file sync
tilt get filewatch
```

### Skaffold Build Failures

```bash
# Clean build cache
skaffold delete
docker system prune -f

# Verbose output
skaffold dev -v debug
```

### Database Migrations

```bash
# Run migrations manually
docker compose exec policy-api alembic upgrade head

# Reset database
docker compose down -v
docker compose up -d
```

---

## Production Parity

The local dev environment mirrors production in these ways:

| Aspect | Production | Local Dev |
|--------|------------|-----------|
| Images | `ghcr.io/grc-claw/*` | Built locally |
| Secrets | Vault / ExternalSecrets | `.env.local` / dev tokens |
| Storage | `premium-rwo` | `standard` (kind) |
| Replicas | 3+ | 1 |
| Istio | mTLS, traffic management | Not installed |
| Monitoring | Full stack | Prometheus + Grafana + Jaeger |
| Ingress | Istio Gateway | NodePort / port-forward |

---

## Next Steps

- [Deployment Guide](./grc-claw-deployment/DEPLOYMENT-GUIDE.md)
- [Architecture](../ARCHITECTURE.md)
- [API Spec](./grc-claw-api-spec.md)
- [Helm Chart](../deploy/helm/grc-claw/)
